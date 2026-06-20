#!/usr/bin/env bash
set -euo pipefail

# Run lighting/background/object-position perturbations for one medium-success task.
# The task is selected from a finished Pi05 axis5 run unless SELECTED_TASK is set.

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
BASE_OUTPUT_FOLDER="${BASE_OUTPUT_FOLDER:?Set BASE_OUTPUT_FOLDER to the finished pi05_axis5 output folder name}"
STAMP="${STAMP:-$(date +%Y%m%d_%H%M%S)}"
MATRIX_PATH="${MATRIX_PATH:-${PACK_ROOT}/robolab_repro_artifacts/pi05_axis5_task_matrix.json}"
REPORT_DIR="${PACK_ROOT}/robolab_repro_artifacts"
SELECTED_JSON="${SELECTED_JSON:-${REPORT_DIR}/${BASE_OUTPUT_FOLDER}_selected_medium_task.json}"

RUN_LIGHTING="${RUN_LIGHTING:-1}"
RUN_BACKGROUND="${RUN_BACKGROUND:-1}"
RUN_OBJECT_POSITION="${RUN_OBJECT_POSITION:-1}"
BACKGROUND_SEEDS="${BACKGROUND_SEEDS:-0 1 2}"
OBJECT_XY_RANGE="${OBJECT_XY_RANGE:-0.03}"
OBJECT_YAW_RANGE="${OBJECT_YAW_RANGE:-0.20}"

export OMNI_KIT_ACCEPT_EULA="${OMNI_KIT_ACCEPT_EULA:-Y}"

if [[ ! -d "${ROBO_ROOT}" ]]; then
  echo "[perturb] RoboLab root not found: ${ROBO_ROOT}" >&2
  exit 2
fi

mkdir -p "${REPORT_DIR}"
cd "${PACK_ROOT}"
if [[ ! -f "${MATRIX_PATH}" ]]; then
  python scripts/generate_axis5_task_matrix.py --out "${MATRIX_PATH}"
fi

if [[ -z "${SELECTED_TASK:-}" ]]; then
  if [[ ! -f "${SELECTED_JSON}" ]]; then
    python scripts/select_medium_success_task.py \
      --output-root "${ROBO_ROOT}/output/${BASE_OUTPUT_FOLDER}" \
      --matrix "${MATRIX_PATH}" \
      --out "${SELECTED_JSON}"
  fi
  SELECTED_TASK="$(python - "${SELECTED_JSON}" <<'PY'
import json, sys
data=json.load(open(sys.argv[1], encoding="utf-8"))
print(data["selected"]["task_name"])
PY
)"
fi

OBJECT_NAMES="${OBJECT_NAMES:-$(python - "${MATRIX_PATH}" "${SELECTED_TASK}" <<'PY'
import json, sys
matrix=json.load(open(sys.argv[1], encoding="utf-8"))
task=sys.argv[2]
for row in matrix["tasks"]:
    if row["task_name"] == task:
        print(" ".join(row.get("primary_objects_for_object_pose_variation") or []))
        break
PY
)}"

if [[ -z "${OBJECT_NAMES}" ]]; then
  echo "[perturb] No object names available for ${SELECTED_TASK}; set OBJECT_NAMES manually." >&2
  exit 3
fi

OUTPUT_PREFIX="${OUTPUT_PREFIX:-pi05_perturb_${SELECTED_TASK}_${STAMP}}"

echo "[perturb] Selected task: ${SELECTED_TASK}"
echo "[perturb] Object names: ${OBJECT_NAMES}"
echo "[perturb] Output prefix: ${OUTPUT_PREFIX}"
nvidia-smi || true

cd "${ROBO_ROOT}"

COMMON_ARGS=(
  --policy "${POLICY}"
  --remote-host "${REMOTE_HOST}"
  --remote-port "${REMOTE_PORT}"
  --task "${SELECTED_TASK}"
  --num-envs "${NUM_ENVS}"
  --num-runs "${NUM_RUNS}"
  --video-mode "${VIDEO_MODE}"
  --enable-subtask
  --headless
  --device "${DEVICE}"
)

if [[ "${RUN_LIGHTING}" == "1" ]]; then
  if [[ ! -f policies/pi0_family/run_lighting.py ]]; then
    echo "[perturb] Missing official lighting runner." >&2
    exit 4
  fi
  echo "[perturb] Running lighting variation..."
  "${UV_BIN}" run python policies/pi0_family/run_lighting.py \
    --policy "${POLICY}" \
    --remote-host "${REMOTE_HOST}" \
    --remote-port "${REMOTE_PORT}" \
    --task "${SELECTED_TASK}" \
    --num-envs "${NUM_ENVS}" \
    --num-runs "${NUM_RUNS}" \
    --headless \
    --device "${DEVICE}" \
    --output-folder-name "${OUTPUT_PREFIX}_lighting"
fi

if [[ "${RUN_BACKGROUND}" == "1" ]]; then
  for seed in ${BACKGROUND_SEEDS}; do
    echo "[perturb] Running background seed ${seed}..."
    "${UV_BIN}" run python policies/pi0_family/run.py \
      "${COMMON_ARGS[@]}" \
      --randomize-background \
      --background-seed "${seed}" \
      --output-folder-name "${OUTPUT_PREFIX}_background_seed${seed}"
  done
fi

if [[ "${RUN_OBJECT_POSITION}" == "1" ]]; then
  echo "[perturb] Installing object position variation runner..."
  python "${PACK_ROOT}/scripts/create_object_position_variation_runner.py" --robolab-root "${ROBO_ROOT}" --force
  read -r -a OBJECT_ARRAY <<< "${OBJECT_NAMES}"
  echo "[perturb] Running object position variation..."
  "${UV_BIN}" run python policies/pi0_family/run_object_position_variation.py \
    --policy "${POLICY}" \
    --remote-host "${REMOTE_HOST}" \
    --remote-port "${REMOTE_PORT}" \
    --task "${SELECTED_TASK}" \
    --object-name "${OBJECT_ARRAY[@]}" \
    --xy-range "${OBJECT_XY_RANGE}" \
    --yaw-range "${OBJECT_YAW_RANGE}" \
    --num-envs "${NUM_ENVS}" \
    --num-runs "${NUM_RUNS}" \
    --video-mode "${VIDEO_MODE}" \
    --enable-subtask \
    --headless \
    --device "${DEVICE}" \
    --output-folder-name "${OUTPUT_PREFIX}_object_position"
fi

echo "[perturb] Summarizing perturbation outputs..."
ROOTS=()
for path in "${ROBO_ROOT}/output/${OUTPUT_PREFIX}"_*; do
  [[ -d "$path" ]] && ROOTS+=("$path")
done

if [[ ${#ROOTS[@]} -gt 0 ]]; then
  python "${PACK_ROOT}/scripts/summarize_ablation_outputs.py" \
    --roots "${ROOTS[@]}" \
    --out-json "${REPORT_DIR}/${OUTPUT_PREFIX}_summary.json" \
    --out-csv "${REPORT_DIR}/${OUTPUT_PREFIX}_summary.csv"
fi

echo "[perturb] Done."
