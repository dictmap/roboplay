#!/usr/bin/env bash
set -uo pipefail

PACK_ROOT="${PACK_ROOT:-/home/yjl/roboplay/robolab_2604_09860_repro_jupyter}"
ROBO_ROOT="${ROBO_ROOT:-/home/yjl/codex_robolab_4090_20260619/RoboLab}"
UV_BIN="${UV_BIN:-/home/yjl/.local/bin/uv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
REMOTE_HOST="${REMOTE_HOST:-localhost}"
REMOTE_PORT="${REMOTE_PORT:-8000}"
NUM_ENVS="${NUM_ENVS:-1}"
NUM_RUNS="${NUM_RUNS:-1}"
DEVICE="${DEVICE:-cuda:0}"
VIDEO_MODE="${VIDEO_MODE:-all}"
QUEUE_ID="${QUEUE_ID:-roboplay_companion_$(date +%Y%m%d_%H%M%S)}"
STAMP="${STAMP:-$(date +%Y%m%d_%H%M%S)}"
REPORT_DIR="${PACK_ROOT}/robolab_repro_artifacts"
LOG_DIR="${PACK_ROOT}/remote_logs/${QUEUE_ID}"
STATUS_JSONL="${REPORT_DIR}/${QUEUE_ID}_status.jsonl"
QUEUE_MD="${PACK_ROOT}/EXPERIMENT_21_companion_experiment_queue.md"
QUEUE_NB="${PACK_ROOT}/RoboLab_4090_companion_experiments_20260621.ipynb"
LIVE_LOG="${LOG_DIR}/live.log"
MATRIX120="${REPORT_DIR}/robolab120_task_matrix.json"
MATRIX20="${REPORT_DIR}/${QUEUE_ID}_robolab20_task_matrix.json"
TASKS20_TXT="${REPORT_DIR}/${QUEUE_ID}_tasks20.txt"

mkdir -p "${REPORT_DIR}" "${LOG_DIR}"
cd "${PACK_ROOT}" || exit 2
exec > >(tee -a "${LIVE_LOG}") 2>&1

json_event() {
  local phase="$1" status="$2" rc="$3" message="$4" extra_json="${5:-{}}"
  "${PYTHON_BIN}" - "${STATUS_JSONL}" "$phase" "$status" "$rc" "$message" "$extra_json" <<'PYJSON'
import json, sys
from datetime import datetime, timezone
path, phase, status, rc, message, extra = sys.argv[1:7]
try:
    extra_obj = json.loads(extra)
except Exception:
    extra_obj = {"raw_extra": extra}
row = {
    "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "phase": phase,
    "status": status,
    "returncode": None if rc == "NA" else int(rc),
    "message": message,
    **extra_obj,
}
with open(path, "a", encoding="utf-8") as f:
    f.write(json.dumps(row, ensure_ascii=False) + "\n")
print(json.dumps(row, ensure_ascii=False))
PYJSON
}

append_md() {
  local text="$1"
  printf '%b\n' "$text" >> "${QUEUE_MD}"
}

refresh_notebook() {
  "${PYTHON_BIN}" scripts/update_companion_notebook.py \
    --md "${QUEUE_MD}" \
    --status-jsonl "${STATUS_JSONL}" \
    --out "${QUEUE_NB}" || true
}

phase_begin() {
  local phase="$1" title="$2"
  append_md "\n## $(date '+%Y-%m-%d %H:%M:%S') - ${title}\n\n- 阶段 ID：\`${phase}\`\n- 状态：running\n- 日志：\`${LOG_DIR}/${phase}.log\`\n"
  json_event "$phase" "running" "NA" "$title" "{\"log\":\"${LOG_DIR}/${phase}.log\"}"
  refresh_notebook
}

phase_end() {
  local phase="$1" title="$2" rc="$3" note="$4"
  local status="completed"
  if [[ "$rc" != "0" ]]; then status="failed_or_blocked"; fi
  append_md "\n### 阶段结果：${title}\n\n- 状态：\`${status}\`\n- returncode：\`${rc}\`\n- 说明：${note}\n"
  json_event "$phase" "$status" "$rc" "$note" "{}"
  refresh_notebook
}

run_phase() {
  local phase="$1" title="$2" func="$3"
  local log="${LOG_DIR}/${phase}.log"
  phase_begin "$phase" "$title"
  set +e
  "$func" 2>&1 | tee -a "$log"
  local rc=${PIPESTATUS[0]}
  set -e
  phase_end "$phase" "$title" "$rc" "see ${log}"
  return 0
}

load_tasks20() {
  mapfile -t TASKS20 < "${TASKS20_TXT}"
}

phase_00_full120_checkpoint() {
  "${PYTHON_BIN}" - "${REPORT_DIR}" <<'PYFULL'
import json
from pathlib import Path
import sys
report_dir = Path(sys.argv[1])
prefix = 'robolab120_pi05_full_assetsfixed_20260620_170411'
manifest = report_dir / f'{prefix}_task_run_manifest.jsonl'
status = report_dir / 'current_robolab120_status.json'
rows = [json.loads(line) for line in manifest.read_text(encoding='utf-8').splitlines() if line.strip()]
print(json.dumps({
    'prefix': prefix,
    'manifest_rows': len(rows),
    'run_ok': sum(1 for r in rows if r.get('run_returncode') == 0),
    'verify_ok': sum(1 for r in rows if r.get('verify_returncode') == 0),
    'status_file_exists': status.exists(),
}, ensure_ascii=False, indent=2))
assert len(rows) == 120
assert all(r.get('run_returncode') == 0 for r in rows)
assert all(r.get('verify_returncode') == 0 for r in rows)
PYFULL
}

phase_01_select20_and_pi05_baseline() {
  "${PYTHON_BIN}" scripts/generate_robolab120_task_matrix.py --out "${MATRIX120}"
  "${PYTHON_BIN}" scripts/generate_robolab20_task_matrix.py --source "${MATRIX120}" --out "${MATRIX20}" --count 20
  "${PYTHON_BIN}" - "${MATRIX20}" "${TASKS20_TXT}" <<'PYTASKS'
import json, sys
matrix=json.load(open(sys.argv[1], encoding='utf-8'))
with open(sys.argv[2], 'w', encoding='utf-8') as f:
    for row in matrix['tasks']:
        f.write(row['task_name'] + '\n')
print(json.dumps({'tasks_file': sys.argv[2], 'tasks': [r['task_name'] for r in matrix['tasks']]}, ensure_ascii=False, indent=2))
PYTASKS
  RUN_PREFIX="${QUEUE_ID}_robolab20_pi05_baseline" \
  MATRIX_PATH="${MATRIX20}" GENERATE_MATRIX=0 TASK_LIMIT=0 \
  POLICY=pi05 REMOTE_HOST="${REMOTE_HOST}" REMOTE_PORT="${REMOTE_PORT}" \
  NUM_ENVS="${NUM_ENVS}" NUM_RUNS="${NUM_RUNS}" VIDEO_MODE="${VIDEO_MODE}" DEVICE="${DEVICE}" \
  bash scripts/run_pi05_robolab120_4090.sh
}

phase_02_robochallenge_probe() {
  out_root="${REPORT_DIR}/${QUEUE_ID}_robochallenge_pi_adapter_required"
  "${PYTHON_BIN}" scripts/write_adapter_pending_results.py \
    --matrix "${MATRIX20}" \
    --out-root "${out_root}" \
    --policy "robochallenge_pi" \
    --status "adapter_required" \
    --reason "Local RoboChallenge pi05/Table30v2 ALOHA checkpoint exists, but it is not a RoboLab Franka+Robotiq joint-position websocket policy. A real RoboLab observation/action adapter is required before the 20-task rollout is meaningful."
  "${PYTHON_BIN}" - "${out_root}" <<'PYROBOCHALLENGE'
import json, sys
from pathlib import Path
root=Path(sys.argv[1])
probe={
  'candidate_roots': ['/home/yjl/robochallenge/repo', '/home/yjl/robochallenge/openpi', '/home/yjl/yjl/RoboChallenge/checkpoints/table30v2_multitask_baseline_aloha'],
  'local_checkpoint_exists': Path('/home/yjl/yjl/RoboChallenge/checkpoints/table30v2_multitask_baseline_aloha').exists(),
  'robolab_rollout_started': False,
  'blocking_reason': 'Aloha/Table30v2 action and observation schema do not match RoboLab Pi0DroidJointposClient keys/actions.',
}
(root/'adapter_probe.json').write_text(json.dumps(probe, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(probe, ensure_ascii=False, indent=2))
PYROBOCHALLENGE
}

phase_03_rekep_probe() {
  out_root="${REPORT_DIR}/${QUEUE_ID}_rekep_adapter_required"
  "${PYTHON_BIN}" scripts/write_adapter_pending_results.py \
    --matrix "${MATRIX20}" \
    --out-root "${out_root}" \
    --policy "rekep" \
    --status "planner_adapter_required" \
    --reason "ReKep local demos exist, but RoboLab needs a perception/keypoint extraction adapter plus a Franka+Robotiq execution controller before a 20-task RoboLab rollout can be scored."
  "${PYTHON_BIN}" - "${out_root}" <<'PYREKEP'
import json, sys
from pathlib import Path
root=Path(sys.argv[1])
probe={
  'candidate_root': '/home/yjl/light/Rekep',
  'local_rekep_exists': Path('/home/yjl/light/Rekep').exists(),
  'robolab_rollout_started': False,
  'blocking_reason': 'ReKep is a planner/perception method, not a drop-in RoboLab policy server.',
}
(root/'adapter_probe.json').write_text(json.dumps(probe, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(probe, ensure_ascii=False, indent=2))
PYREKEP
}

phase_04_camera_angle_20() {
  load_tasks20
  TASKS="${TASKS20[*]}" RUN_BASELINE=0 RUN_CAMERA_VARIATION=1 RUN_WRIST_BLACKOUT=0 \
  POLICY=pi05 REMOTE_HOST="${REMOTE_HOST}" REMOTE_PORT="${REMOTE_PORT}" \
  NUM_ENVS="${NUM_ENVS}" NUM_RUNS="${NUM_RUNS}" VIDEO_MODE="${VIDEO_MODE}" DEVICE="${DEVICE}" \
  OUTPUT_PREFIX="${QUEUE_ID}_camera_angle" bash scripts/run_camera_ablation_4090.sh
  roots=("${ROBO_ROOT}/output/${QUEUE_ID}_camera_angle"_*)
  "${PYTHON_BIN}" scripts/summarize_ablation_outputs.py --roots "${roots[@]}" \
    --out-json "${REPORT_DIR}/${QUEUE_ID}_camera_angle_summary.json" \
    --out-csv "${REPORT_DIR}/${QUEUE_ID}_camera_angle_summary.csv" || true
}

phase_05_wrist_blackout_20() {
  load_tasks20
  TASKS="${TASKS20[*]}" RUN_BASELINE=0 RUN_CAMERA_VARIATION=0 RUN_WRIST_BLACKOUT=1 \
  WRIST_BLACKOUT_INSTALLER="${PACK_ROOT}/scripts/create_pi05_wrist_blackout_runner.py" \
  POLICY=pi05 REMOTE_HOST="${REMOTE_HOST}" REMOTE_PORT="${REMOTE_PORT}" \
  NUM_ENVS="${NUM_ENVS}" NUM_RUNS="${NUM_RUNS}" VIDEO_MODE="${VIDEO_MODE}" DEVICE="${DEVICE}" \
  OUTPUT_PREFIX="${QUEUE_ID}_wrist_blackout" bash scripts/run_camera_ablation_4090.sh
  roots=("${ROBO_ROOT}/output/${QUEUE_ID}_wrist_blackout"_*)
  "${PYTHON_BIN}" scripts/summarize_ablation_outputs.py --roots "${roots[@]}" \
    --out-json "${REPORT_DIR}/${QUEUE_ID}_wrist_blackout_summary.json" \
    --out-csv "${REPORT_DIR}/${QUEUE_ID}_wrist_blackout_summary.csv" || true
}

phase_06_robot_base_shift_20() {
  load_tasks20
  "${PYTHON_BIN}" scripts/create_robot_base_shift_runner.py --robolab-root "${ROBO_ROOT}" --force
  cd "${ROBO_ROOT}" || return 2
  "${UV_BIN}" run python policies/pi0_family/run_robot_base_shift.py \
    --policy pi05 --remote-host "${REMOTE_HOST}" --remote-port "${REMOTE_PORT}" \
    --task "${TASKS20[@]}" --num-envs "${NUM_ENVS}" --num-runs "${NUM_RUNS}" \
    --video-mode "${VIDEO_MODE}" --output-folder-name "${QUEUE_ID}_robot_base_shift" \
    --enable-subtask --headless --device "${DEVICE}" --robot-x-offset 0.03 --robot-y-offset 0.00
  cd "${PACK_ROOT}" || return 2
  "${PYTHON_BIN}" scripts/summarize_ablation_outputs.py --roots "${ROBO_ROOT}/output/${QUEUE_ID}_robot_base_shift" \
    --out-json "${REPORT_DIR}/${QUEUE_ID}_robot_base_shift_summary.json" \
    --out-csv "${REPORT_DIR}/${QUEUE_ID}_robot_base_shift_summary.csv" || true
}

phase_07_other_models_probe() {
  "${PYTHON_BIN}" scripts/generate_policy_baseline_model_matrix.py --out "${REPORT_DIR}/${QUEUE_ID}_policy_baseline_model_matrix.json"
  "${PYTHON_BIN}" - "${REPORT_DIR}" "${QUEUE_ID}" "${MATRIX20}" <<'PYMODELS'
import json, sys
from pathlib import Path
report_dir=Path(sys.argv[1]); qid=sys.argv[2]; matrix=Path(sys.argv[3])
models = [
  ('pi05', 'completed_in_phase_01', 'Pi05 is the direct baseline and has a 20-task rollout in this queue.'),
  ('paligemma', 'checkpoint_missing', 'RoboLab runner supports paligemma, but local openpi-assets-simeval paligemma_binning_droid_jointpos checkpoint is not present.'),
  ('groot_n1_5_3b', 'adapter_required', 'GR00T checkpoint is downloaded, but RoboLab observation/action adapter is not implemented.'),
  ('cosmos_policy', 'adapter_required', 'Cosmos policy checkpoints are downloaded for other embodiments/tasks, not a RoboLab Franka+Robotiq policy server yet.'),
  ('qwen_vl_alibaba', 'not_action_policy', 'Qwen2.5-VL local model is a VLM, not an action policy; Qwen-VLA/RobotManip interface must be confirmed before RoboLab scoring.'),
]
summary=[]
tasks=json.loads(matrix.read_text(encoding='utf-8'))['tasks']
for policy,status,reason in models:
    out_root=report_dir/f'{qid}_{policy}_model_probe'
    out_root.mkdir(parents=True, exist_ok=True)
    with (out_root/'episode_results.jsonl').open('w', encoding='utf-8') as f:
        for t in tasks:
            row={'task_name':t['task_name'],'env_name':t['task_name'],'policy':policy,'status':status,'adapter_required':status not in {'completed_in_phase_01'},'success':None,'score':None,'episode_step':None,'reason':reason}
            f.write(json.dumps(row, ensure_ascii=False)+'\n')
    (out_root/'model_probe_manifest.json').write_text(json.dumps({'policy':policy,'status':status,'reason':reason,'rows':len(tasks)}, ensure_ascii=False, indent=2), encoding='utf-8')
    summary.append({'policy':policy,'status':status,'reason':reason,'out_root':str(out_root)})
(report_dir/f'{qid}_other_models_probe_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
PYMODELS
}

main() {
  cat > "${QUEUE_MD}" <<EOF
# RoboLab 4090 陪伴式实验队列

- 队列 ID：\`${QUEUE_ID}\`
- 启动时间：$(date '+%Y-%m-%d %H:%M:%S %Z')
- 4090 运行目录：\`${ROBO_ROOT}\`
- 文档目录：\`${PACK_ROOT}\`
- 进度日志：\`${LIVE_LOG}\`

## 执行原则

1. 第 0 项 full RoboLab-120 以已完成的 clean run 为事实来源，不重复浪费 GPU。
2. 后续统一选择 20 个任务作为横向对照矩阵。
3. 能直接用 RoboLab/OpenPI runner 跑的实验会真实跑 episode、HDF5、视频和子任务日志。
4. 不能直接作为 RoboLab action policy 的模型，先生成 adapter/probe 记录，不把 adapter 缺失伪装成 0 分。
EOF
  refresh_notebook
  echo "QUEUE_ID=${QUEUE_ID}"
  echo "LIVE_LOG=${LIVE_LOG}"
  nvidia-smi || true
  run_phase "00_full120_checkpoint" "确认 Pi05 RoboLab-120 已完整复现" phase_00_full120_checkpoint
  run_phase "01_select20_pi05_baseline" "选择 20 个任务并运行 Pi05 基线" phase_01_select20_and_pi05_baseline
  run_phase "02_robochallenge_pi_probe" "RoboChallenge pi 20 任务 adapter 探测" phase_02_robochallenge_probe
  run_phase "03_rekep_probe" "ReKep 20 任务 adapter 探测" phase_03_rekep_probe
  run_phase "04_camera_angle_20" "相机角度扰动 20 任务" phase_04_camera_angle_20
  run_phase "05_wrist_blackout_20" "取消腕部相机/腕部黑屏 20 任务" phase_05_wrist_blackout_20
  run_phase "06_robot_base_shift_20" "机器人基座偏移 20 任务" phase_06_robot_base_shift_20
  run_phase "07_other_models_probe" "Pi05/GR00T/PaliGemma/Cosmos/阿里模型 20 任务可运行性与对照记录" phase_07_other_models_probe
  append_md "\n## 队列完成\n\n- 完成时间：$(date '+%Y-%m-%d %H:%M:%S %Z')\n- 状态 JSONL：\`${STATUS_JSONL}\`\n"
  json_event "queue" "completed" "0" "all configured phases reached terminal state" "{}"
  refresh_notebook
}

main "$@"
