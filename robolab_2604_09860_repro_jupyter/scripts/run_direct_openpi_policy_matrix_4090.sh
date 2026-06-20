#!/usr/bin/env bash
set -euo pipefail

# Run the same axis5 task matrix for direct RoboLab/OpenPI policy variants.
# This is for variants already supported by policies/pi0_family/run.py:
#   pi05, paligemma, paligemma_fast, pi0, pi0_fast
#
# Important: each policy still needs its corresponding OpenPI server/checkpoint
# to be available. This script does not download checkpoints by itself.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACK_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

ROBO_ROOT="${ROBO_ROOT:-/home/yjl/codex_robolab_4090_20260619/RoboLab}"
UV_BIN="${UV_BIN:-/home/yjl/.local/bin/uv}"
REMOTE_HOST="${REMOTE_HOST:-localhost}"
REMOTE_PORT="${REMOTE_PORT:-8000}"
NUM_ENVS="${NUM_ENVS:-1}"
NUM_RUNS="${NUM_RUNS:-3}"
DEVICE="${DEVICE:-cuda:0}"
VIDEO_MODE="${VIDEO_MODE:-all}"
STAMP="${STAMP:-$(date +%Y%m%d_%H%M%S)}"
DIRECT_POLICIES="${DIRECT_POLICIES:-pi05 paligemma paligemma_fast}"
MATRIX_PATH="${MATRIX_PATH:-${PACK_ROOT}/robolab_repro_artifacts/pi05_axis5_task_matrix.json}"
REPORT_DIR="${PACK_ROOT}/robolab_repro_artifacts"

export OMNI_KIT_ACCEPT_EULA="${OMNI_KIT_ACCEPT_EULA:-Y}"

if [[ ! -d "${ROBO_ROOT}" ]]; then
  echo "[policy-matrix] RoboLab root not found: ${ROBO_ROOT}" >&2
  exit 2
fi

cd "${PACK_ROOT}"
if [[ ! -f "${MATRIX_PATH}" ]]; then
  python scripts/generate_axis5_task_matrix.py --out "${MATRIX_PATH}"
fi

python scripts/generate_policy_baseline_model_matrix.py \
  --out "${REPORT_DIR}/policy_baseline_model_matrix.json"

TASKS="$(python - "${MATRIX_PATH}" <<'PY'
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
print(" ".join(row["task_name"] for row in data["tasks"]))
PY
)"

read -r -a TASK_ARRAY <<< "${TASKS}"
mkdir -p "${REPORT_DIR}"

echo "[policy-matrix] Host: $(hostname)"
echo "[policy-matrix] Policies: ${DIRECT_POLICIES}"
echo "[policy-matrix] Tasks: ${TASKS}"
nvidia-smi || true

OUTPUT_FOLDERS=()
cd "${ROBO_ROOT}"
for policy in ${DIRECT_POLICIES}; do
  output_folder="axis5_${policy}_${STAMP}"
  OUTPUT_FOLDERS+=("${ROBO_ROOT}/output/${output_folder}")
  echo "[policy-matrix] Running ${policy} -> ${output_folder}"
  "${UV_BIN}" run python policies/pi0_family/run.py \
    --policy "${policy}" \
    --remote-host "${REMOTE_HOST}" \
    --remote-port "${REMOTE_PORT}" \
    --task "${TASK_ARRAY[@]}" \
    --num-envs "${NUM_ENVS}" \
    --num-runs "${NUM_RUNS}" \
    --video-mode "${VIDEO_MODE}" \
    --output-folder-name "${output_folder}" \
    --enable-subtask \
    --headless \
    --device "${DEVICE}"

  python "${PACK_ROOT}/scripts/verify_robolab_artifacts.py" \
    --output-root "${ROBO_ROOT}/output/${output_folder}" \
    --matrix "${MATRIX_PATH}" \
    --out "${REPORT_DIR}/${output_folder}_artifact_check.json"

  "${UV_BIN}" run python analysis/read_results.py "${output_folder}" \
    --by-attributes \
    --output-csv "${output_folder}_by_attributes.csv"

  "${UV_BIN}" run python analysis/read_results.py "${output_folder}" \
    --by-difficulty \
    --output-csv "${output_folder}_by_difficulty.csv"

  "${UV_BIN}" run python analysis/read_results.py "${output_folder}" \
    --by-task-length \
    --output-csv "${output_folder}_by_task_length.csv"
done

python "${PACK_ROOT}/scripts/compare_policy_matrix_results.py" \
  --matrix "${MATRIX_PATH}" \
  --roots "${OUTPUT_FOLDERS[@]}" \
  --out-json "${REPORT_DIR}/axis5_direct_policy_compare_${STAMP}.json" \
  --out-csv "${REPORT_DIR}/axis5_direct_policy_compare_${STAMP}.csv"

echo "[policy-matrix] Done. Reports under ${REPORT_DIR}"
