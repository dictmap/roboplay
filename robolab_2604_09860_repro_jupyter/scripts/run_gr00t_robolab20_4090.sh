#!/usr/bin/env bash
set -euo pipefail

# Run the fixed RoboLab-20 task matrix against a running GR00T policy server.
# This runner mirrors the Pi05 artifact discipline: one task at a time, per-task
# output folders, artifact verification, merged episode JSONL, and summary CSVs.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACK_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

ROBO_ROOT="${ROBO_ROOT:-/home/yjl/codex_robolab_4090_20260619/RoboLab}"
UV_BIN="${UV_BIN:-/home/yjl/.local/bin/uv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
REMOTE_HOST="${REMOTE_HOST:-localhost}"
REMOTE_PORT="${REMOTE_PORT:-5555}"
NUM_ENVS="${NUM_ENVS:-1}"
NUM_RUNS="${NUM_RUNS:-1}"
DEVICE="${DEVICE:-cuda:0}"
VIDEO_MODE="${VIDEO_MODE:-all}"
RECORD_IMAGE_DATA="${RECORD_IMAGE_DATA:-0}"
STOP_ON_FAILURE="${STOP_ON_FAILURE:-0}"
TASK_LIMIT="${TASK_LIMIT:-0}"
STAMP="${STAMP:-$(date +%Y%m%d_%H%M%S)}"
RUN_PREFIX="${RUN_PREFIX:-roboplay_companion_gr00t20_${STAMP}}"
MATRIX_PATH="${MATRIX_PATH:-${PACK_ROOT}/robolab_repro_artifacts/roboplay_companion_20260621_074050_robolab20_task_matrix.json}"
REPORT_DIR="${PACK_ROOT}/robolab_repro_artifacts"
FALLBACK_LABEL="${FALLBACK_LABEL:-gr00t_eager_noflash_fallback}"

export OMNI_KIT_ACCEPT_EULA="${OMNI_KIT_ACCEPT_EULA:-Y}"

if [[ ! -d "${ROBO_ROOT}" ]]; then
  echo "[gr00t20] RoboLab root not found: ${ROBO_ROOT}" >&2
  exit 2
fi
if [[ ! -f "${MATRIX_PATH}" ]]; then
  echo "[gr00t20] MATRIX_PATH not found: ${MATRIX_PATH}" >&2
  exit 2
fi
mkdir -p "${REPORT_DIR}"

mapfile -t TASKS < <("${PYTHON_BIN}" - "${MATRIX_PATH}" "${TASK_LIMIT}" <<'PY_TASKS'
import json
import sys
matrix = json.load(open(sys.argv[1], encoding='utf-8'))
limit = int(sys.argv[2])
tasks = [row['task_name'] for row in matrix['tasks']]
if limit > 0:
    tasks = tasks[:limit]
print('\n'.join(tasks))
PY_TASKS
)

TOTAL="${#TASKS[@]}"
RUN_MANIFEST="${REPORT_DIR}/${RUN_PREFIX}_task_run_manifest.jsonl"
MERGED_FOLDER="${RUN_PREFIX}_merged"
MERGED_OUTPUT_ROOT="${ROBO_ROOT}/output/${MERGED_FOLDER}"
rm -f "${RUN_MANIFEST}"

echo "[gr00t20] Host: $(hostname)"
echo "[gr00t20] RoboLab root: ${ROBO_ROOT}"
echo "[gr00t20] Matrix: ${MATRIX_PATH}"
echo "[gr00t20] Tasks: ${TOTAL}"
echo "[gr00t20] Server: ${REMOTE_HOST}:${REMOTE_PORT}"
echo "[gr00t20] NUM_ENVS=${NUM_ENVS} NUM_RUNS=${NUM_RUNS} VIDEO_MODE=${VIDEO_MODE} label=${FALLBACK_LABEL}"
nvidia-smi || true

OUTPUT_ROOTS=()
cd "${ROBO_ROOT}"
for idx in "${!TASKS[@]}"; do
  task="${TASKS[$idx]}"
  output_folder="${RUN_PREFIX}_${task}"
  output_root="${ROBO_ROOT}/output/${output_folder}"
  OUTPUT_ROOTS+=("${output_root}")
  echo "[gr00t20] [$((idx + 1))/${TOTAL}] ${task} -> ${output_folder}"

  RUN_ARGS=(
    --remote-host "${REMOTE_HOST}"
    --remote-port "${REMOTE_PORT}"
    --task "${task}"
    --num-envs "${NUM_ENVS}"
    --num-runs "${NUM_RUNS}"
    --video-mode "${VIDEO_MODE}"
    --output-folder-name "${output_folder}"
    --enable-subtask
    --headless
    --device "${DEVICE}"
  )
  if [[ "${RECORD_IMAGE_DATA}" == "1" ]]; then
    RUN_ARGS+=(--record-image-data)
  fi

  set +e
  "${UV_BIN}" run python policies/gr00t/run.py "${RUN_ARGS[@]}"
  run_rc="$?"
  verify_rc="NA"
  if [[ "${run_rc}" == "0" ]]; then
    "${PYTHON_BIN}" "${PACK_ROOT}/scripts/verify_robolab_artifacts.py" \
      --output-root "${output_root}" \
      --matrix "${MATRIX_PATH}" \
      --tasks "${task}" \
      --out "${REPORT_DIR}/${output_folder}_artifact_check.json"
    verify_rc="$?"
  fi
  set -e

  "${PYTHON_BIN}" - "${RUN_MANIFEST}" "${task}" "${output_root}" "${run_rc}" "${verify_rc}" "${FALLBACK_LABEL}" <<'PY_MANIFEST'
import json
import sys
from datetime import datetime, timezone
path, task, output_root, run_rc, verify_rc, label = sys.argv[1:7]
row = {
    'created_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    'task_name': task,
    'output_root': output_root,
    'run_returncode': int(run_rc),
    'verify_returncode': verify_rc if verify_rc == 'NA' else int(verify_rc),
    'policy': 'gr00t',
    'label': label,
}
with open(path, 'a', encoding='utf-8') as f:
    f.write(json.dumps(row, ensure_ascii=False) + '\n')
PY_MANIFEST

  if [[ "${STOP_ON_FAILURE}" == "1" && ( "${run_rc}" != "0" || "${verify_rc}" != "0" ) ]]; then
    echo "[gr00t20] stop on failure: task=${task} run_rc=${run_rc} verify_rc=${verify_rc}" >&2
    exit 1
  fi
done

"${PYTHON_BIN}" - "${MERGED_OUTPUT_ROOT}" "${OUTPUT_ROOTS[@]}" <<'PY_MERGE'
import json
import sys
from pathlib import Path
merged = Path(sys.argv[1])
roots = [Path(item) for item in sys.argv[2:]]
merged.mkdir(parents=True, exist_ok=True)
episode_out = merged / 'episode_results.jsonl'
rows = 0
with episode_out.open('w', encoding='utf-8') as out:
    for root in roots:
        for path in sorted(root.rglob('episode_results.jsonl')):
            for line in path.read_text(encoding='utf-8').splitlines():
                if line.strip():
                    out.write(line.rstrip() + '\n')
                    rows += 1
manifest = {'merged_output_root': str(merged), 'source_roots': [str(root) for root in roots], 'episode_rows': rows}
(merged / 'merged_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(manifest, ensure_ascii=False))
PY_MERGE

cd "${PACK_ROOT}"
"${PYTHON_BIN}" scripts/summarize_ablation_outputs.py \
  --roots "${OUTPUT_ROOTS[@]}" \
  --out-json "${REPORT_DIR}/${RUN_PREFIX}_episode_summary.json" \
  --out-csv "${REPORT_DIR}/${RUN_PREFIX}_episode_summary.csv"

"${PYTHON_BIN}" scripts/compare_policy_matrix_results.py \
  --matrix "${MATRIX_PATH}" \
  --roots "${OUTPUT_ROOTS[@]}" \
  --out-json "${REPORT_DIR}/${RUN_PREFIX}_policy_compare.json" \
  --out-csv "${REPORT_DIR}/${RUN_PREFIX}_policy_compare_by_axis.csv"

cd "${ROBO_ROOT}"
if [[ -s "${MERGED_OUTPUT_ROOT}/episode_results.jsonl" ]]; then
  echo "[gr00t20] Running official analysis/read_results.py on merged JSONL folder..."
  "${UV_BIN}" run python analysis/read_results.py "${MERGED_FOLDER}" \
    --by-attributes \
    --output-csv "${RUN_PREFIX}_by_attributes.csv" || true
  "${UV_BIN}" run python analysis/read_results.py "${MERGED_FOLDER}" \
    --by-difficulty \
    --output-csv "${RUN_PREFIX}_by_difficulty.csv" || true
  "${UV_BIN}" run python analysis/read_results.py "${MERGED_FOLDER}" \
    --by-task-length \
    --output-csv "${RUN_PREFIX}_by_task_length.csv" || true
fi

echo "[gr00t20] Done."
echo "[gr00t20] Merged output: ${MERGED_OUTPUT_ROOT}"
echo "[gr00t20] Task manifest: ${RUN_MANIFEST}"
echo "[gr00t20] Reports: ${REPORT_DIR}/${RUN_PREFIX}_*.json / *.csv"
