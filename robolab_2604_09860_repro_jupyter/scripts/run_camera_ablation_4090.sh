#!/usr/bin/env bash
set -euo pipefail

# One-command entrypoint for the RoboLab camera ablation pack on the RTX 4090 host.
# It uses the official RoboLab Pi0-family runners when possible:
#   - policies/pi0_family/run.py for baseline
#   - policies/pi0_family/run_camera_pose_variation.py for camera-pose sweeps
# Optional wrist-camera soft ablation requires scripts/create_pi05_wrist_blackout_runner.py.

ROBO_ROOT="${ROBO_ROOT:-/home/yjl/codex_robolab_4090_20260619/RoboLab}"
UV_BIN="${UV_BIN:-/home/yjl/.local/bin/uv}"
POLICY="${POLICY:-pi05}"
REMOTE_HOST="${REMOTE_HOST:-localhost}"
REMOTE_PORT="${REMOTE_PORT:-8000}"
TASKS="${TASKS:-BananaInBowlTask}"
NUM_ENVS="${NUM_ENVS:-1}"
NUM_RUNS="${NUM_RUNS:-3}"
DEVICE="${DEVICE:-cuda:0}"
VIDEO_MODE="${VIDEO_MODE:-all}"
STAMP="${STAMP:-$(date +%Y%m%d_%H%M%S)}"
OUTPUT_PREFIX="${OUTPUT_PREFIX:-pi05_camera_robot_ablation_${STAMP}}"

RUN_BASELINE="${RUN_BASELINE:-1}"
RUN_CAMERA_VARIATION="${RUN_CAMERA_VARIATION:-1}"
RUN_WRIST_BLACKOUT="${RUN_WRIST_BLACKOUT:-0}"
WRIST_BLACKOUT_INSTALLER="${WRIST_BLACKOUT_INSTALLER:-}"

export OMNI_KIT_ACCEPT_EULA="${OMNI_KIT_ACCEPT_EULA:-Y}"

if [[ ! -d "${ROBO_ROOT}" ]]; then
  echo "[ablation] RoboLab root not found: ${ROBO_ROOT}" >&2
  exit 2
fi

if [[ ! -x "${UV_BIN}" ]]; then
  echo "[ablation] uv not executable: ${UV_BIN}" >&2
  exit 2
fi

cd "${ROBO_ROOT}"

echo "[ablation] Host: $(hostname)"
echo "[ablation] Root: ${ROBO_ROOT}"
echo "[ablation] Policy: ${POLICY}"
echo "[ablation] Tasks: ${TASKS}"
echo "[ablation] Output prefix: ${OUTPUT_PREFIX}"
nvidia-smi || true

read -r -a TASK_ARRAY <<< "${TASKS}"

COMMON_ARGS=(
  --policy "${POLICY}"
  --remote-host "${REMOTE_HOST}"
  --remote-port "${REMOTE_PORT}"
  --task "${TASK_ARRAY[@]}"
  --num-envs "${NUM_ENVS}"
  --num-runs "${NUM_RUNS}"
  --video-mode "${VIDEO_MODE}"
  --headless
  --device "${DEVICE}"
)

if [[ "${RUN_BASELINE}" == "1" ]]; then
  echo "[ablation] Running baseline..."
  "${UV_BIN}" run python policies/pi0_family/run.py \
    "${COMMON_ARGS[@]}" \
    --output-folder-name "${OUTPUT_PREFIX}_baseline"
fi

if [[ "${RUN_CAMERA_VARIATION}" == "1" ]]; then
  if [[ ! -f policies/pi0_family/run_camera_pose_variation.py ]]; then
    echo "[ablation] Missing official camera variation runner: policies/pi0_family/run_camera_pose_variation.py" >&2
    exit 3
  fi

  echo "[ablation] Running official camera pose variation sweep..."
  "${UV_BIN}" run python policies/pi0_family/run_camera_pose_variation.py \
    "${COMMON_ARGS[@]}" \
    --output-folder-name "${OUTPUT_PREFIX}_camera_pose_variation"
fi

if [[ "${RUN_WRIST_BLACKOUT}" == "1" ]]; then
  if [[ ! -f policies/pi0_family/run_wrist_blackout.py ]]; then
    if [[ -n "${WRIST_BLACKOUT_INSTALLER}" && -f "${WRIST_BLACKOUT_INSTALLER}" ]]; then
      echo "[ablation] Installing wrist blackout runner..."
      python "${WRIST_BLACKOUT_INSTALLER}" --robolab-root "${ROBO_ROOT}" --force
    fi
  fi

  if [[ ! -f policies/pi0_family/run_wrist_blackout.py ]]; then
    echo "[ablation] Wrist blackout runner missing. Set WRIST_BLACKOUT_INSTALLER=/path/to/create_pi05_wrist_blackout_runner.py or run the installer first." >&2
    exit 4
  fi

  echo "[ablation] Running wrist-camera soft blackout..."
  "${UV_BIN}" run python policies/pi0_family/run_wrist_blackout.py \
    "${COMMON_ARGS[@]}" \
    --output-folder-name "${OUTPUT_PREFIX}_wrist_blackout"
fi

echo "[ablation] Done. Outputs are under ${ROBO_ROOT}/output/${OUTPUT_PREFIX}_*"
