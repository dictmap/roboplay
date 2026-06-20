#!/usr/bin/env bash
set -euo pipefail

# Start a five-task RoboLab-120 Pi05 smoke run on the 4090 host.
# This wrapper avoids fragile SSH/tmux nested quoting by writing a concrete
# per-run script and then asking tmux to execute that file.

BASE="${BASE:-/home/yjl/codex_robolab_4090_20260619}"
PACK_ROOT="${PACK_ROOT:-/home/yjl/roboplay/robolab_2604_09860_repro_jupyter}"
ROBO_ROOT="${ROBO_ROOT:-${BASE}/RoboLab}"
UV_BIN="${UV_BIN:-/home/yjl/.local/bin/uv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
REMOTE_HOST="${REMOTE_HOST:-localhost}"
REMOTE_PORT="${REMOTE_PORT:-8000}"
NUM_ENVS="${NUM_ENVS:-1}"
NUM_RUNS="${NUM_RUNS:-1}"
VIDEO_MODE="${VIDEO_MODE:-all}"
TASK_LIMIT="${TASK_LIMIT:-5}"
STOP_ON_FAILURE="${STOP_ON_FAILURE:-0}"
SESSION="${SESSION:-robolab_monitor}"
WINDOW="${WINDOW:-robolab120_smoke5}"
STAMP="${STAMP:-$(date +%Y%m%d_%H%M%S)}"
RUN_PREFIX="${RUN_PREFIX:-robolab120_pi05_smoke5_${STAMP}}"
LOG="${LOG:-${BASE}/${RUN_PREFIX}.log}"
STATUS="${STATUS:-${BASE}/${RUN_PREFIX}.status}"
RUN_SCRIPT="${RUN_SCRIPT:-${BASE}/${RUN_PREFIX}_runner.sh}"

if [[ ! -d "${PACK_ROOT}" ]]; then
  echo "[smoke5] pack root not found: ${PACK_ROOT}" >&2
  exit 2
fi

if [[ ! -d "${ROBO_ROOT}" ]]; then
  echo "[smoke5] RoboLab root not found: ${ROBO_ROOT}" >&2
  exit 2
fi

if ! ss -ltn 2>/dev/null | grep -q ":${REMOTE_PORT} "; then
  echo "[smoke5] policy server is not listening on ${REMOTE_HOST}:${REMOTE_PORT}" >&2
  exit 3
fi

if ! tmux has-session -t "${SESSION}" 2>/dev/null; then
  tmux new-session -d -s "${SESSION}" -n main
fi

cat > "${RUN_SCRIPT}" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "${PACK_ROOT}"
export ROBO_ROOT="${ROBO_ROOT}"
export UV_BIN="${UV_BIN}"
export PYTHON_BIN="${PYTHON_BIN}"
export POLICY="pi05"
export REMOTE_HOST="${REMOTE_HOST}"
export REMOTE_PORT="${REMOTE_PORT}"
export NUM_ENVS="${NUM_ENVS}"
export NUM_RUNS="${NUM_RUNS}"
export VIDEO_MODE="${VIDEO_MODE}"
export TASK_LIMIT="${TASK_LIMIT}"
export STOP_ON_FAILURE="${STOP_ON_FAILURE}"
export RUN_PREFIX="${RUN_PREFIX}"
echo ROBOLAB120_SMOKE5_START \$(date -Is) | tee "${LOG}"
bash scripts/run_pi05_robolab120_4090.sh 2>&1 | tee -a "${LOG}"
rc=\${PIPESTATUS[0]}
"${PYTHON_BIN}" scripts/diagnose_robolab120_smoke_log.py \
  --log "${LOG}" \
  --manifest "${PACK_ROOT}/robolab_repro_artifacts/${RUN_PREFIX}_task_run_manifest.jsonl" \
  --artifact-check-glob "${PACK_ROOT}/robolab_repro_artifacts/${RUN_PREFIX}_*Task_artifact_check.json" \
  --out "${PACK_ROOT}/robolab_repro_artifacts/${RUN_PREFIX}_failure_diagnosis.json" \
  2>&1 | tee -a "${LOG}" || true
echo ROBOLAB120_SMOKE5_EXIT \${rc} \$(date -Is) | tee -a "${LOG}"
echo "\${rc}" > "${STATUS}"
exit "\${rc}"
EOF
chmod +x "${RUN_SCRIPT}"

tmux kill-window -t "${SESSION}:${WINDOW}" 2>/dev/null || true
tmux new-window -t "${SESSION}" -n "${WINDOW}" "bash ${RUN_SCRIPT}; exec bash"
echo "${RUN_PREFIX}" > "${BASE}/robolab120_smoke5_latest.txt"

echo "[smoke5] started ${RUN_PREFIX}"
echo "[smoke5] log ${LOG}"
echo "[smoke5] status ${STATUS}"
echo "[smoke5] runner ${RUN_SCRIPT}"
tmux list-windows -t "${SESSION}"
