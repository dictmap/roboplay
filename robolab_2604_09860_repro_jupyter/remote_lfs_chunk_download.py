from __future__ import annotations

"""使用 HTTP range 分块下载单个大型 RoboLab Git LFS 对象。

当某个大型资产用普通 LFS 或单线程 curl 反复超时时使用这个脚本：
1. 从 Git 中读取 LFS pointer；
2. 向 GitHub LFS API 申请临时下载 URL；
3. 按固定字节范围并发下载 chunk；
4. 按顺序拼装；
5. 完整 sha256 校验通过后才替换目标文件。
"""

import argparse
import concurrent.futures
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
DEFAULT_PROXY_URL = "http://127.0.0.1:7897"


def run(cmd: list[str]) -> str:
    # git 元数据命令应该稳定可靠；失败时立即抛错。
    return subprocess.run(cmd, check=True, text=True, capture_output=True).stdout


def read_lfs_pointer(path: str) -> tuple[str, int]:
    # LFS pointer 文件里包含标准 sha256 oid 和精确字节大小。
    pointer = run(["git", "cat-file", "-p", f"HEAD:{path}"])
    oid = ""
    size = 0
    for line in pointer.splitlines():
        if line.startswith("oid sha256:"):
            oid = line.split("sha256:", 1)[1].strip()
        elif line.startswith("size "):
            size = int(line.split()[1])
    if not oid or not size:
        raise ValueError(f"No LFS pointer metadata found for {path}")
    return oid, size


def lfs_href(oid: str, size: int, proxy_url: str) -> str:
    # 把一个 LFS 对象 oid 解析成临时 signed download URL。
    payload = {
        "operation": "download",
        "transfers": ["basic"],
        "objects": [{"oid": oid, "size": size}],
    }
    opener = build_opener(ProxyHandler({"https": proxy_url, "http": proxy_url}))
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
    obj = data["objects"][0]
    if "error" in obj:
        # 对象级错误通常意味着认证、限流或网络问题；这里直接暴露出来。
        raise RuntimeError(f"LFS batch error for {oid}: {obj['error']}")
    return obj["actions"]["download"]["href"]


def sha256_file(path: Path) -> str:
    # 流式读取文件，支持大型 USDZ/背景资产且不占用太多内存。
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_chunk_name(path: str, start: int, end: int) -> str:
    # 生成安全的 chunk 文件名，同时保留来源路径和字节范围信息。
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", path)
    return f"{stem}.{start}-{end}.part"


def download_range(
    *,
    href: str,
    proxy_url: str,
    chunk_dir: Path,
    source_path: str,
    start: int,
    end: int,
) -> Path:
    # 下载一个闭区间字节范围；已完成 chunk 可在重试时复用。
    expected = end - start + 1
    out = chunk_dir / safe_chunk_name(source_path, start, end)
    if out.exists() and out.stat().st_size == expected:
        print(f"CHUNK_SKIP start={start} end={end} bytes={expected}", flush=True)
        return out

    tmp = out.with_suffix(out.suffix + ".download")
    for attempt in range(1, 8):
        # 单个 chunk 足够小，失败后重下整个 chunk 比继续断点更简单可靠。
        if tmp.exists():
            tmp.unlink()
        print(f"CHUNK_DOWNLOAD attempt={attempt} start={start} end={end} bytes={expected}", flush=True)
        cmd = [
            "curl",
            "-x",
            proxy_url,
            "-L",
            "--fail",
            "--retry",
            "6",
            "--retry-delay",
            "3",
            "--connect-timeout",
            "30",
            "--speed-limit",
            "1024",
            "--speed-time",
            "120",
            "--max-time",
            "1800",
            "--range",
            f"{start}-{end}",
            "--silent",
            "--show-error",
            href,
            "-o",
            str(tmp),
        ]
        proc = subprocess.run(cmd, text=True, capture_output=True)
        if proc.returncode != 0:
            # 只打印 stderr 尾部，让并发失败日志仍然可读。
            print(proc.stderr[-2000:], file=sys.stderr, flush=True)
            time.sleep(5)
            continue
        got = tmp.stat().st_size if tmp.exists() else 0
        if got != expected:
            # 有些代理会返回截断的 range body；拼装前必须拒绝。
            print(f"CHUNK_SIZE_MISMATCH start={start} got={got} expected={expected}", file=sys.stderr, flush=True)
            time.sleep(5)
            continue
        os.replace(tmp, out)
        print(f"CHUNK_DONE start={start} end={end} bytes={expected}", flush=True)
        return out
    raise RuntimeError(f"Failed chunk {start}-{end}")


def main() -> int:
    # 这个脚本一次处理一个问题资产，例如大型 scene 或 background 文件。
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True)
    parser.add_argument("--proxy", default=DEFAULT_PROXY_URL)
    parser.add_argument("--chunk-size-mib", type=int, default=16)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()

    source_path = args.path
    target = Path(source_path)
    oid, size = read_lfs_pointer(source_path)
    if target.exists() and target.stat().st_size == size and sha256_file(target) == oid:
        # 目标文件已存在且校验通过时直接退出，便于安全重复运行。
        print(f"TARGET_SKIP_OK path={source_path} bytes={size}", flush=True)
        return 0

    href = lfs_href(oid, size, args.proxy)
    chunk_size = args.chunk_size_mib * 1024 * 1024
    # curl --range 使用 HTTP 字节区间语义，起止位置都是闭区间。
    ranges = [(start, min(start + chunk_size - 1, size - 1)) for start in range(0, size, chunk_size)]
    target.parent.mkdir(parents=True, exist_ok=True)
    chunk_dir = target.parent / f".{target.name}.chunks"
    chunk_dir.mkdir(parents=True, exist_ok=True)
    print(f"PLAN path={source_path} bytes={size} chunks={len(ranges)} workers={args.workers}", flush=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        # 一次提交所有 range；每个 chunk 独立重试并做大小校验。
        futures = [
            executor.submit(
                download_range,
                href=href,
                proxy_url=args.proxy,
                chunk_dir=chunk_dir,
                source_path=source_path,
                start=start,
                end=end,
            )
            for start, end in ranges
        ]
        for future in concurrent.futures.as_completed(futures):
            # 任何 chunk 失败都向外抛出，让调用者看到非零退出。
            future.result()

    assembled = target.with_suffix(target.suffix + ".assembled")
    with assembled.open("wb") as out_f:
        # 无论 chunk 谁先下载完，最终都严格按字节范围顺序拼装。
        for start, end in ranges:
            part = chunk_dir / safe_chunk_name(source_path, start, end)
            with part.open("rb") as in_f:
                for block in iter(lambda: in_f.read(1024 * 1024), b""):
                    out_f.write(block)

    digest = sha256_file(assembled)
    if digest != oid:
        # 最终对象 digest 是证明并发 chunk 正确重建 LFS blob 的唯一依据。
        raise RuntimeError(f"SHA mismatch for {source_path}: got={digest} expected={oid}")
    os.replace(assembled, target)
    print(f"TARGET_DONE path={source_path} bytes={size}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
