from __future__ import annotations

"""通过 GitHub LFS batch API 下载 RoboLab 的 Git LFS 对象。

远端 4090 上普通 `git lfs pull` 容易因为网络中断失败，所以用这个脚本直接：
1. 从 Git LFS pointer 解析对象 oid 和大小；
2. 调 GitHub LFS batch API 换取临时下载 URL；
3. 用 curl 断点续传下载真实文件；
4. 用 sha256 校验通过后再替换 pointer 文件。
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import ProxyHandler, Request, build_opener


BATCH_URL = "https://github.com/NVlabs/RoboLab.git/info/lfs/objects/batch"
PROXY_URL = "http://127.0.0.1:7897"


def run(cmd: list[str], *, text: bool = True) -> subprocess.CompletedProcess:
    # 小封装：用于必须快速失败的 git 命令，stdout 会被调用方继续解析。
    return subprocess.run(cmd, check=True, text=text, capture_output=True)


def parse_size(size_s: str) -> int:
    # `git lfs ls-files --size` 输出类似 "342 KB" 的人类可读大小；这里转成字节便于排序。
    match = re.match(r"([0-9.]+)\s*([KMG]?B)", size_s)
    if not match:
        raise ValueError(f"Cannot parse size: {size_s}")
    value = float(match.group(1))
    unit = match.group(2)
    factor = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}[unit]
    return int(value * factor)


def get_lfs_entries(prefix: str) -> list[dict]:
    # 枚举仓库中所有 LFS 文件，只保留当前 smoke run 需要的路径前缀。
    output = run(["git", "lfs", "ls-files", "--long", "--size"]).stdout
    entries: list[dict] = []
    for line in output.splitlines():
        match = re.match(r"([0-9a-f]{64}) ([-*]) (.+?) \(([^)]+)\)$", line)
        if not match:
            continue
        oid, state, path, approx_size = match.groups()
        if not path.startswith(prefix):
            continue
        entries.append(
            {
                "oid": oid,
                "state": state,
                "path": path,
                "approx_size": approx_size,
                "approx_bytes": parse_size(approx_size),
                "exists": Path(path).exists(),
            }
        )
    return entries


def exact_size(path: str) -> int:
    # 上面的可读大小只是近似值；LFS pointer 里有精确字节数。
    pointer = run(["git", "cat-file", "-p", f"HEAD:{path}"]).stdout
    for line in pointer.splitlines():
        if line.startswith("size "):
            return int(line.split()[1])
    raise ValueError(f"No LFS size in pointer for {path}")


def batch_download_info(objects: list[dict]) -> dict[str, str]:
    # 向 GitHub LFS API 批量申请临时 signed URL。
    payload = {
        "operation": "download",
        "transfers": ["basic"],
        "objects": [{"oid": obj["oid"], "size": obj["size"]} for obj in objects],
    }
    opener = build_opener(ProxyHandler({"https": PROXY_URL, "http": PROXY_URL}))
    req = Request(
        BATCH_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": "application/vnd.git-lfs+json",
            "Content-Type": "application/vnd.git-lfs+json",
        },
        method="POST",
    )
    with opener.open(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    hrefs: dict[str, str] = {}
    for obj in data.get("objects", []):
        # 如果 API 对某个对象返回错误，立即失败；部分成功的批次很难审计。
        if "error" in obj:
            raise RuntimeError(f"LFS batch error for {obj.get('oid')}: {obj['error']}")
        hrefs[obj["oid"]] = obj["actions"]["download"]["href"]
    return hrefs


def sha256_file(path: Path) -> str:
    # 流式计算 sha256，避免多 GB USD/背景资产一次性读入内存。
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download_one(obj: dict, href: str) -> None:
    # 先下载到同目录临时文件；中断时不会留下损坏的目标文件。
    path = Path(obj["path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".download")
    if path.exists() and path.stat().st_size == obj["size"]:
        current = sha256_file(path)
        if current == obj["oid"]:
            # 已存在且校验通过的文件直接跳过，因此脚本可以安全重复运行。
            print(f"SKIP_OK {obj['path']} {obj['approx_size']}", flush=True)
            return
    for attempt in range(1, 6):
        # 如果之前已有 .download 临时文件，curl 会从已有进度继续下载。
        resume = tmp.exists() and tmp.stat().st_size > 0
        print(
            f"DOWNLOAD attempt={attempt} resume={resume} tmp_bytes={tmp.stat().st_size if tmp.exists() else 0} "
            f"path={obj['path']} size={obj['size']}",
            flush=True,
        )
        cmd = [
            "curl",
            "-x",
            PROXY_URL,
            "-L",
            "--fail",
            "--continue-at",
            "-",
            "--retry",
            "5",
            "--retry-delay",
            "3",
            "--connect-timeout",
            "30",
            "--speed-limit",
            "2048",
            "--speed-time",
            "90",
            "--max-time",
            "1200",
            "--silent",
            "--show-error",
            href,
            "-o",
            str(tmp),
        ]
        proc = subprocess.run(cmd, text=True, capture_output=True)
        if proc.returncode != 0:
            # 只打印 stderr 尾部，避免长时间远端下载日志过于噪音。
            print(proc.stderr[-2000:], file=sys.stderr, flush=True)
            time.sleep(5)
            continue
        if tmp.stat().st_size != obj["size"]:
            # 先检查大小；大小不对时 sha 校验必然失败。
            print(
                f"SIZE_INCOMPLETE {obj['path']} got={tmp.stat().st_size} expected={obj['size']}",
                file=sys.stderr,
                flush=True,
            )
            time.sleep(5)
            continue
        digest = sha256_file(tmp)
        if digest != obj["oid"]:
            # Git LFS 的 oid 本身就是 sha256，因此这是最终完整性检查。
            print(f"SHA_MISMATCH {obj['path']} got={digest} expected={obj['oid']}", file=sys.stderr, flush=True)
            time.sleep(5)
            continue
        os.replace(tmp, path)
        print(f"DONE {obj['path']} bytes={obj['size']}", flush=True)
        return
    raise RuntimeError(f"Failed to download {obj['path']}")


def main() -> int:
    # prefix 允许只下载某个子树的资产，而不是一次性拉完整 RoboLab LFS 数据。
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--only-missing", action="store_true")
    args = parser.parse_args()

    entries = get_lfs_entries(args.prefix)
    if args.only_missing:
        # 失败重跑时只补缺失文件，避免重复下载已落盘资产。
        entries = [entry for entry in entries if not Path(entry["path"]).exists()]
    for entry in entries:
        entry["size"] = exact_size(entry["path"])
    # 小文件优先能更快证明网络路径/API/校验链路是否可用。
    entries.sort(key=lambda x: (x["size"], x["path"]))
    if args.limit:
        entries = entries[: args.limit]

    total = sum(entry["size"] for entry in entries)
    print(f"PLAN count={len(entries)} bytes={total} prefix={args.prefix}", flush=True)
    if not entries:
        return 0

    for start in range(0, len(entries), 20):
        # 每 20 个对象申请一批 URL，减少 API 调用，同时控制失败影响范围。
        chunk = entries[start : start + 20]
        hrefs = batch_download_info(chunk)
        for obj in chunk:
            download_one(obj, hrefs[obj["oid"]])
    print("ALL_DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
