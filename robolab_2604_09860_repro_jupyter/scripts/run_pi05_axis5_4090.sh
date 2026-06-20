#!/usr/bin/env bash
set -euo pipefail

# Fixed-Pi05 evaluation pack:
#   1. ability-axis matrix with >=5 tasks per axis
#   2. one RoboLab run.py execution with videos/HDF5/event logs/subtask progress
#   3. artifact verification
#   4. analysis/read_results.py tables by axis(attributes), difficulty, and task length

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACK_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

ROBO_ROOT="${ROBO_ROOT:-/home/yjl/codex_robolab_4090_20260619/RoboLab}"
UV_BIN="${UV_BIN:-/home/yjl/.local/bin/uv}"
POLICY="${POLICY:-pi05}"
REMOTE_HOST="${REMOTE_HOST:-localhost}"
REMOTE_PORT="${REMOTE_PORT:-8000}"
NUM_ENVS="${NUM_ENVS:-1}"
NUM_RUNS="${NUM_RUNS:-3}"
DEVICE="${DEVICE:-cuda:0}"
VIDEO_MODE="${VIDEO_MODE:-all}"
STAMP="${STAMP:-$(date +%Y%m%d_%H%M%S)}"
OUTPUT_FOLDER="${OUTPUT_FOLDER:-pi05_axis5_${STAMP}}"
RECORD_IMAGE_DATA="${RECORD_IMAGE_DATA:-0}"
MATRIX_PATH="${MATRIX_PATH:-${PACK_ROOT}/robolab_repro_artifacts/pi05_axis5_task_matrix.json}"

export OMNI_KIT_ACCEPT_EULA="${OMNI_KIT_ACCEPT_EULA:-Y}"

if [[ ! -d "${ROBO_ROOT}" ]]; then
  echo "[axis5] RoboLab root not found: ${ROBO_ROOT}" >&2
  exit 2
fi

cd "${PACK_ROOT}"
python scripts/generate_axis5_task_matrix.py --out "${MATRIX_PATH}"

TASKS="$(python - "${MATRIX_PATH}" <<'PY'
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
print(" ".join(row["task_name"] for row in data["tasks"]))
PY
)"

echo "[axis5] Host: $(hostname)"
echo "[axis5] RoboLab root: ${ROBO_ROOT}"
echo "[axis5] Matrix: ${MATRIX_PATH}"
echo "[axis5] Tasks: ${TASKS}"
echo "[axis5] Output folder: ${OUTPUT_FOLDER}"
nvidia-smi || true

cd "${ROBO_ROOT}"
read -r -a TASK_ARRAY <<< "${TASKS}"

RUN_ARGS=(
  --policy "${POLICY}"
  --remote-host "${REMOTE_HOST}"
  --remote-port "${REMOTE_PORT}"
  --task "${TASK_ARRAY[@]}"
  --num-envs "${NUM_ENVS}"
  --num-runs "${NUM_RUNS}"
  --video-mode "${VIDEO_MODE}"
  --output-folder-name "${OUTPUT_FOLDER}"
  --enable-subtask
  --headless
  --device "${DEVICE}"
)

if [[ "${RECORD_IMAGE_DATA}" == "1" ]]; then
  RUN_ARGS+=(--record-image-data)
fi

echo "[axis5] Running fixed Pi05 matrix..."
"${UV_BIN}" run python policies/pi0_family/run.py "${RUN_ARGS[@]}"

OUTPUT_ROOT="${ROBO_ROOT}/output/${OUTPUT_FOLDER}"
REPORT_DIR="${PACK_ROOT}/robolab_repro_artifacts"
mkdir -p "${REPORT_DIR}"

echo "[axis5] Verifying required artifacts..."
python "${PACK_ROOT}/scripts/verify_robolab_artifacts.py" \
  --output-root "${OUTPUT_ROOT}" \
  --matrix "${MATRIX_PATH}" \
  --out "${REPORT_DIR}/${OUTPUT_FOLDER}_artifact_check.json"

echo "[axis5] Running analysis/read_results.py tables..."
"${UV_BIN}" run python analysis/read_results.py "${OUTPUT_FOLDER}" \
  --by-attributes \
  --output-csv "${OUTPUT_FOLDER}_by_attributes.csv"

"${UV_BIN}" run python analysis/read_results.py "${OUTPUT_FOLDER}" \
  --by-difficulty \
  --output-csv "${OUTPUT_FOLDER}_by_difficulty.csv"

"${UV_BIN}" run python analysis/read_results.py "${OUTPUT_FOLDER}" \
  --by-task-length \
  --output-csv "${OUTPUT_FOLDER}_by_task_length.csv"

python "${PACK_ROOT}/scripts/summarize_ablation_outputs.py" \
  --roots "${OUTPUT_ROOT}" \
  --out-json "${REPORT_DIR}/${OUTPUT_FOLDER}_episode_summary.json" \
  --out-csv "${REPORT_DIR}/${OUTPUT_FOLDER}_episode_summary.csv"

python "${PACK_ROOT}/scripts/select_medium_success_task.py" \
  --output-root "${OUTPUT_ROOT}" \
  --matrix "${MATRIX_PATH}" \
  --out "${REPORT_DIR}/${OUTPUT_FOLDER}_selected_medium_task.json"

echo "[axis5] Done."
echo "[axis5] Output root: ${OUTPUT_ROOT}"
echo "[axis5] Reports: ${REPORT_DIR}/${OUTPUT_FOLDER}_*.json / *.csv"
