#!/usr/bin/env bash
set -euo pipefail

# Run RoboLab-120 for direct RoboLab/OpenPI policies and add explicit
# adapter-pending rows for RoboChallenge/ReKep until their adapters are real.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACK_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

ROBO_ROOT="${ROBO_ROOT:-/home/yjl/codex_robolab_4090_20260619/RoboLab}"
UV_BIN="${UV_BIN:-/home/yjl/.local/bin/uv}"
REMOTE_HOST="${REMOTE_HOST:-localhost}"
REMOTE_PORT="${REMOTE_PORT:-8000}"
NUM_ENVS="${NUM_ENVS:-1}"
NUM_RUNS="${NUM_RUNS:-1}"
DEVICE="${DEVICE:-cuda:0}"
VIDEO_MODE="${VIDEO_MODE:-all}"
TASK_LIMIT="${TASK_LIMIT:-0}"
STOP_ON_FAILURE="${STOP_ON_FAILURE:-0}"
DIRECT_POLICIES="${DIRECT_POLICIES:-pi05}"
INCLUDE_ADAPTER_PENDING="${INCLUDE_ADAPTER_PENDING:-1}"
STAMP="${STAMP:-$(date +%Y%m%d_%H%M%S)}"
MATRIX_PATH="${MATRIX_PATH:-${PACK_ROOT}/robolab_repro_artifacts/robolab120_task_matrix.json}"
REPORT_DIR="${PACK_ROOT}/robolab_repro_artifacts"

export OMNI_KIT_ACCEPT_EULA="${OMNI_KIT_ACCEPT_EULA:-Y}"

if [[ ! -d "${ROBO_ROOT}" ]]; then
  echo "[robolab120-compare] RoboLab root not found: ${ROBO_ROOT}" >&2
  exit 2
fi

cd "${PACK_ROOT}"
mkdir -p "${REPORT_DIR}"
python scripts/generate_robolab120_task_matrix.py --out "${MATRIX_PATH}"
python scripts/generate_adapter_baseline_plan.py \
  --out "${REPORT_DIR}/adapter_baseline_plan.json"
python scripts/create_robochallenge_robolab_adapter_stub.py
python scripts/create_rekep_robolab_adapter_stub.py

OUTPUT_ROOTS=()
for policy in ${DIRECT_POLICIES}; do
  run_prefix="robolab120_${policy}_${STAMP}"
  echo "[robolab120-compare] Running direct policy: ${policy}"
  POLICY="${policy}" \
  RUN_PREFIX="${run_prefix}" \
  MATRIX_PATH="${MATRIX_PATH}" \
  ROBO_ROOT="${ROBO_ROOT}" \
  UV_BIN="${UV_BIN}" \
  REMOTE_HOST="${REMOTE_HOST}" \
  REMOTE_PORT="${REMOTE_PORT}" \
  NUM_ENVS="${NUM_ENVS}" \
  NUM_RUNS="${NUM_RUNS}" \
  DEVICE="${DEVICE}" \
  VIDEO_MODE="${VIDEO_MODE}" \
  TASK_LIMIT="${TASK_LIMIT}" \
  STOP_ON_FAILURE="${STOP_ON_FAILURE}" \
  bash "${PACK_ROOT}/scripts/run_pi05_robolab120_4090.sh"
  OUTPUT_ROOTS+=("${ROBO_ROOT}/output/${run_prefix}_merged")
done

if [[ "${INCLUDE_ADAPTER_PENDING}" == "1" ]]; then
  robochallenge_root="${REPORT_DIR}/robolab120_robochallenge_pi_adapter_pending_${STAMP}"
  rekep_root="${REPORT_DIR}/robolab120_rekep_adapter_pending_${STAMP}"
  python scripts/write_adapter_pending_results.py \
    --matrix "${MATRIX_PATH}" \
    --out-root "${robochallenge_root}" \
    --policy "robochallenge_pi" \
    --status "adapter_required" \
    --reason "RoboChallenge checkpoint exists as a local candidate, but RoboLab observation/action adapter has not been implemented."
  python scripts/write_adapter_pending_results.py \
    --matrix "${MATRIX_PATH}" \
    --out-root "${rekep_root}" \
    --policy "rekep" \
    --status "planner_adapter_required" \
    --reason "ReKep needs keypoint extraction, constraint planning, and RoboLab low-level controller adapter before Isaac rollouts."
  OUTPUT_ROOTS+=("${robochallenge_root}" "${rekep_root}")
fi

python scripts/compare_policy_matrix_results.py \
  --matrix "${MATRIX_PATH}" \
  --roots "${OUTPUT_ROOTS[@]}" \
  --out-json "${REPORT_DIR}/robolab120_policy_compare_${STAMP}.json" \
  --out-csv "${REPORT_DIR}/robolab120_policy_compare_by_axis_${STAMP}.csv"

echo "[robolab120-compare] Done."
echo "[robolab120-compare] Compared roots:"
printf '  %s\n' "${OUTPUT_ROOTS[@]}"
echo "[robolab120-compare] Report: ${REPORT_DIR}/robolab120_policy_compare_${STAMP}.json"
