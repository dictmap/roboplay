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
REPORT_DIR="${PACK_ROOT}/robolab_repro_artifacts"
QUEUE_ID="${QUEUE_ID:-$(cat "${REPORT_DIR}/current_companion_queue_id.txt")}"
LOG_DIR="${PACK_ROOT}/remote_logs/${QUEUE_ID}"
STATUS_JSONL="${REPORT_DIR}/${QUEUE_ID}_status.jsonl"
QUEUE_MD="${PACK_ROOT}/EXPERIMENT_21_companion_experiment_queue.md"
LIVE_MD="${PACK_ROOT}/COMPANION_QUEUE_LIVE_PROGRESS.md"
QUEUE_NB="${PACK_ROOT}/RoboLab_4090_companion_experiments_20260621.ipynb"
LIVE_NB="${PACK_ROOT}/RoboLab_4090_companion_live_progress.ipynb"
TASKS20_TXT="${REPORT_DIR}/${QUEUE_ID}_tasks20.txt"
SUPERVISOR_LOG="${LOG_DIR}/resume_supervisor.log"

mkdir -p "${LOG_DIR}" "${REPORT_DIR}"
cd "${PACK_ROOT}" || exit 2
exec > >(tee -a "${SUPERVISOR_LOG}") 2>&1

log_line() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')" "$*"
}

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

refresh_notebook() {
  "${PYTHON_BIN}" scripts/update_companion_notebook.py --md "${LIVE_MD}" --status-jsonl "${STATUS_JSONL}" --out "${LIVE_NB}" >/tmp/roboplay_live_nb_refresh.log 2>&1 || true
  "${PYTHON_BIN}" scripts/update_companion_notebook.py --md "${QUEUE_MD}" --status-jsonl "${STATUS_JSONL}" --out "${QUEUE_NB}" >/tmp/roboplay_queue_nb_refresh.log 2>&1 || true
}

append_md_section() {
  local text="$1"
  printf '%b\n' "$text" >> "${LIVE_MD}"
  printf '%b\n' "$text" >> "${QUEUE_MD}"
  refresh_notebook
}

load_tasks20() {
  if [[ ! -f "${TASKS20_TXT}" ]]; then
    log_line "missing tasks file: ${TASKS20_TXT}"
    return 2
  fi
  mapfile -t TASKS20 < "${TASKS20_TXT}"
  TASKS_STRING="${TASKS20[*]}"
}

count_episode_rows() {
  local root="$1"
  "${PYTHON_BIN}" - "$root" <<'PYCOUNT'
import sys
from pathlib import Path
root=Path(sys.argv[1])
ep=root/'episode_results.jsonl'
print(sum(1 for line in ep.open(encoding='utf-8', errors='ignore') if line.strip()) if ep.exists() else 0)
PYCOUNT
}

artifact_counts_json() {
  local root="$1" target="$2"
  "${PYTHON_BIN}" - "$root" "$target" <<'PYCOUNTS'
import glob, json, sys
from pathlib import Path
root=Path(sys.argv[1]); target=int(sys.argv[2])
counts={'root':str(root),'exists':root.exists(),'variant_dirs':0,'episode_rows':0,'hdf5':0,'mp4':0,'subtask_logs':0,'target_episode_rows':target}
if root.exists():
    counts['variant_dirs']=len([p for p in root.iterdir() if p.is_dir()])
    ep=root/'episode_results.jsonl'
    counts['episode_rows']=sum(1 for line in ep.open(encoding='utf-8', errors='ignore') if line.strip()) if ep.exists() else 0
    counts['hdf5']=len(glob.glob(str(root/'**/*.hdf5'), recursive=True))
    counts['mp4']=len(glob.glob(str(root/'**/*.mp4'), recursive=True))
    counts['subtask_logs']=len(glob.glob(str(root/'**/log_0_env0.json'), recursive=True))
print(json.dumps(counts, ensure_ascii=False))
PYCOUNTS
}

current_camera_json() {
  local root="$1" target="$2" log="$3"
  "${PYTHON_BIN}" - "$root" "$target" "$log" <<'PYSNAP'
import glob, json, re, subprocess, sys
from pathlib import Path
root=Path(sys.argv[1]); target=int(sys.argv[2]); log=Path(sys.argv[3])
text=log.read_text(encoding='utf-8', errors='ignore')[-1200000:] if log.exists() else ''
current=''
for line in reversed(text.splitlines()):
    if '[RoboLab] Running' in line:
        current=re.sub(r'\x1b\[[0-9;]*m','',line)
        break
m=list(re.finditer(r'(\d+)%\|[^\r\n]*?\|\s*(\d+)/(\d+)\s*\[(\d+:\d+)<([^,\]]+)', text))
progress={}
if m:
    g=m[-1].groups(); progress={'percent':int(g[0]),'step':int(g[1]),'total_steps':int(g[2]),'elapsed':g[3],'eta':g[4]}
counts={'root':str(root),'exists':root.exists(),'variant_dirs':0,'episode_rows':0,'hdf5':0,'mp4':0,'subtask_logs':0,'target_episode_rows':target}
if root.exists():
    counts['variant_dirs']=len([p for p in root.iterdir() if p.is_dir()])
    ep=root/'episode_results.jsonl'
    counts['episode_rows']=sum(1 for line in ep.open(encoding='utf-8', errors='ignore') if line.strip()) if ep.exists() else 0
    counts['hdf5']=len(glob.glob(str(root/'**/*.hdf5'), recursive=True))
    counts['mp4']=len(glob.glob(str(root/'**/*.mp4'), recursive=True))
    counts['subtask_logs']=len(glob.glob(str(root/'**/log_0_env0.json'), recursive=True))
try:
    gpu=subprocess.check_output(['nvidia-smi','--query-gpu=timestamp,temperature.gpu,power.draw,memory.used,memory.total,utilization.gpu','--format=csv,noheader,nounits'], text=True).strip()
except Exception as exc:
    gpu=f'unavailable: {exc}'
print(json.dumps({'current_run':current,'progress':progress,'counts':counts,'gpu':gpu}, ensure_ascii=False))
PYSNAP
}

append_progress() {
  local phase="$1" label="$2" root="$3" target="$4" log_path="$5"
  local snapshot
  snapshot="$(current_camera_json "$root" "$target" "$log_path")"
  json_event "$phase" "running_progress" "NA" "$label" "$snapshot"
  "${PYTHON_BIN}" - "${LIVE_MD}" "${QUEUE_MD}" "$phase" "$label" "$snapshot" <<'PYMD'
import json, sys
from datetime import datetime
live, queue, phase, label, snap_s = sys.argv[1:6]
snap=json.loads(snap_s)
counts=snap.get('counts', {})
section=f"""

## {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {label}

- 阶段 ID：`{phase}`
- 状态：`running_progress`
- 当前运行：`{snap.get('current_run') or '等待日志刷新/进程切换中'}`
- episode 进度：`{counts.get('episode_rows')}/{counts.get('target_episode_rows')}`
- 产物计数：variant_dirs=`{counts.get('variant_dirs')}`，HDF5=`{counts.get('hdf5')}`，MP4=`{counts.get('mp4')}`，subtask_logs=`{counts.get('subtask_logs')}`
- step 进度：`{snap.get('progress')}`
- GPU：`{snap.get('gpu')}`
- 输出：`{counts.get('root')}`
"""
for path in [live, queue]:
    with open(path, 'a', encoding='utf-8') as f:
        f.write(section)
PYMD
  refresh_notebook
}

summarize_root() {
  local label="$1" root="$2" out_prefix="$3"
  log_line "summarize ${label}: ${root}"
  "${PYTHON_BIN}" scripts/summarize_ablation_outputs.py --roots "${root}" \
    --out-json "${REPORT_DIR}/${QUEUE_ID}_${out_prefix}_summary.json" \
    --out-csv "${REPORT_DIR}/${QUEUE_ID}_${out_prefix}_summary.csv" || true
}

wait_and_finish_camera() {
  local root="${ROBO_ROOT}/output/${QUEUE_ID}_camera_angle_camera_pose_variation"
  local log_path="${LOG_DIR}/04_camera_angle_20_resume_after_reboot.log"
  local attempts=0
  while true; do
    local rows
    rows="$(count_episode_rows "$root")"
    log_line "camera rows=${rows}/60"
    if [[ "${rows}" -ge 60 ]]; then
      local counts
      counts="$(artifact_counts_json "$root" 60)"
      json_event "04_camera_angle_20" "completed" "0" "camera variation 20 tasks completed after recovery" "$counts"
      append_md_section "\n## $(date '+%Y-%m-%d %H:%M:%S') - 相机角度扰动完成\n\n- 阶段 ID：\`04_camera_angle_20\`\n- 状态：\`completed\`\n- episode：\`${rows}/60\`\n- 输出：\`${root}\`\n"
      summarize_root "camera_angle" "$root" "camera_angle"
      return 0
    fi
    if pgrep -f "run_camera_pose_variation.py.*${QUEUE_ID}_camera_angle_camera_pose_variation" >/dev/null; then
      append_progress "04_camera_angle_20" "相机角度扰动运行中" "$root" 60 "$log_path"
      sleep 300
      continue
    fi
    attempts=$((attempts+1))
    if [[ "${attempts}" -gt 3 ]]; then
      local counts
      counts="$(artifact_counts_json "$root" 60)"
      json_event "04_camera_angle_20" "failed_or_blocked" "1" "camera variation process stopped before 60 rows after retries" "$counts"
      append_md_section "\n## $(date '+%Y-%m-%d %H:%M:%S') - 相机角度扰动未完成\n\n- 阶段 ID：\`04_camera_angle_20\`\n- 状态：\`failed_or_blocked\`\n- episode：\`${rows}/60\`\n- 说明：进程退出且重试超过上限，需要人工检查。\n"
      return 1
    fi
    json_event "04_camera_angle_20" "retrying" "NA" "camera process stopped at ${rows}/60; retry ${attempts}/3 from same output root" "$(artifact_counts_json "$root" 60)"
    load_tasks20 || return 2
    TASKS="${TASKS_STRING}" RUN_BASELINE=0 RUN_CAMERA_VARIATION=1 RUN_WRIST_BLACKOUT=0 \
      POLICY=pi05 REMOTE_HOST="${REMOTE_HOST}" REMOTE_PORT="${REMOTE_PORT}" \
      NUM_ENVS="${NUM_ENVS}" NUM_RUNS="${NUM_RUNS}" VIDEO_MODE="${VIDEO_MODE}" DEVICE="${DEVICE}" \
      OUTPUT_PREFIX="${QUEUE_ID}_camera_angle" bash scripts/run_camera_ablation_4090.sh
    json_event "04_camera_angle_20" "retry_exit" "$?" "camera retry process returned" "$(artifact_counts_json "$root" 60)"
  done
}

run_wrist_blackout() {
  load_tasks20 || return 2
  local root="${ROBO_ROOT}/output/${QUEUE_ID}_wrist_blackout_wrist_blackout"
  local rows
  rows="$(count_episode_rows "$root")"
  if [[ "${rows}" -ge 20 ]]; then
    json_event "05_wrist_blackout_20" "completed" "0" "wrist blackout already has 20 rows" "$(artifact_counts_json "$root" 20)"
    summarize_root "wrist_blackout" "$root" "wrist_blackout"
    return 0
  fi
  json_event "05_wrist_blackout_20" "running" "NA" "starting wrist camera blackout 20-task rollout" "{\"output_root\":\"${root}\"}"
  append_md_section "\n## $(date '+%Y-%m-%d %H:%M:%S') - 取消腕部相机/腕部黑屏 20 任务\n\n- 阶段 ID：\`05_wrist_blackout_20\`\n- 状态：\`running\`\n- 输出：\`${root}\`\n"
  set +e
  TASKS="${TASKS_STRING}" RUN_BASELINE=0 RUN_CAMERA_VARIATION=0 RUN_WRIST_BLACKOUT=1 \
    WRIST_BLACKOUT_INSTALLER="${PACK_ROOT}/scripts/create_pi05_wrist_blackout_runner.py" \
    POLICY=pi05 REMOTE_HOST="${REMOTE_HOST}" REMOTE_PORT="${REMOTE_PORT}" \
    NUM_ENVS="${NUM_ENVS}" NUM_RUNS="${NUM_RUNS}" VIDEO_MODE="${VIDEO_MODE}" DEVICE="${DEVICE}" \
    OUTPUT_PREFIX="${QUEUE_ID}_wrist_blackout" bash scripts/run_camera_ablation_4090.sh
  local rc=$?
  set -e
  rows="$(count_episode_rows "$root")"
  local status="completed"
  if [[ "${rc}" != "0" || "${rows}" -lt 20 ]]; then status="failed_or_blocked"; fi
  json_event "05_wrist_blackout_20" "$status" "$rc" "wrist blackout finished with rows=${rows}/20" "$(artifact_counts_json "$root" 20)"
  append_md_section "\n## $(date '+%Y-%m-%d %H:%M:%S') - 腕部相机取消结果\n\n- 阶段 ID：\`05_wrist_blackout_20\`\n- 状态：\`${status}\`\n- returncode：\`${rc}\`\n- episode：\`${rows}/20\`\n- 输出：\`${root}\`\n"
  summarize_root "wrist_blackout" "$root" "wrist_blackout"
  return 0
}

run_robot_base_shift() {
  load_tasks20 || return 2
  local root="${ROBO_ROOT}/output/${QUEUE_ID}_robot_base_shift"
  local rows
  rows="$(count_episode_rows "$root")"
  if [[ "${rows}" -ge 20 ]]; then
    json_event "06_robot_base_shift_20" "completed" "0" "robot base shift already has 20 rows" "$(artifact_counts_json "$root" 20)"
    summarize_root "robot_base_shift" "$root" "robot_base_shift"
    return 0
  fi
  json_event "06_robot_base_shift_20" "running" "NA" "starting robot base shift 20-task rollout" "{\"output_root\":\"${root}\",\"robot_x_offset\":0.03,\"robot_y_offset\":0.0}"
  append_md_section "\n## $(date '+%Y-%m-%d %H:%M:%S') - 机器人基座偏移 20 任务\n\n- 阶段 ID：\`06_robot_base_shift_20\`\n- 状态：\`running\`\n- 输出：\`${root}\`\n- 偏移：x=0.03m, y=0.00m\n"
  "${PYTHON_BIN}" scripts/create_robot_base_shift_runner.py --robolab-root "${ROBO_ROOT}" --force
  set +e
  cd "${ROBO_ROOT}" || exit 2
  "${UV_BIN}" run python policies/pi0_family/run_robot_base_shift.py \
    --policy pi05 --remote-host "${REMOTE_HOST}" --remote-port "${REMOTE_PORT}" \
    --task "${TASKS20[@]}" --num-envs "${NUM_ENVS}" --num-runs "${NUM_RUNS}" \
    --video-mode "${VIDEO_MODE}" --output-folder-name "${QUEUE_ID}_robot_base_shift" \
    --enable-subtask --headless --device "${DEVICE}" --robot-x-offset 0.03 --robot-y-offset 0.00
  local rc=$?
  cd "${PACK_ROOT}" || exit 2
  set -e
  rows="$(count_episode_rows "$root")"
  local status="completed"
  if [[ "${rc}" != "0" || "${rows}" -lt 20 ]]; then status="failed_or_blocked"; fi
  json_event "06_robot_base_shift_20" "$status" "$rc" "robot base shift finished with rows=${rows}/20" "$(artifact_counts_json "$root" 20)"
  append_md_section "\n## $(date '+%Y-%m-%d %H:%M:%S') - 机器人基座偏移结果\n\n- 阶段 ID：\`06_robot_base_shift_20\`\n- 状态：\`${status}\`\n- returncode：\`${rc}\`\n- episode：\`${rows}/20\`\n- 输出：\`${root}\`\n"
  summarize_root "robot_base_shift" "$root" "robot_base_shift"
  return 0
}

run_other_models_probe() {
  load_tasks20 || return 2
  json_event "07_other_models_probe" "running" "NA" "starting other model availability/probe matrix" "{}"
  "${PYTHON_BIN}" scripts/generate_policy_baseline_model_matrix.py --out "${REPORT_DIR}/${QUEUE_ID}_policy_baseline_model_matrix.json" || true
  "${PYTHON_BIN}" - "${REPORT_DIR}" "${QUEUE_ID}" "${REPORT_DIR}/${QUEUE_ID}_robolab20_task_matrix.json" <<'PYMODELS'
import json, sys
from pathlib import Path
report_dir=Path(sys.argv[1]); qid=sys.argv[2]; matrix=Path(sys.argv[3])
tasks=json.loads(matrix.read_text(encoding='utf-8'))['tasks']
models=[
 ('pi05','completed_in_phase_01','Pi05 direct RoboLab policy server; 20-task rollout completed in phase 01.'),
 ('robochallenge_pi','adapter_required','Local RoboChallenge pi05/Table30v2 ALOHA checkpoint exists, but it is not a RoboLab Franka+Robotiq joint-position websocket policy.'),
 ('rekep','planner_adapter_required','ReKep is a keypoint/planner method and needs perception plus low-level controller adapters before RoboLab scoring.'),
 ('paligemma','checkpoint_or_runner_missing','RoboLab runner supports PaliGemma only if the matching openpi-assets-simeval checkpoint and config are present.'),
 ('groot_n1_5_3b','adapter_required','GR00T checkpoints are not currently exposed as a RoboLab Pi0-family websocket action policy.'),
 ('cosmos_policy','adapter_required','Cosmos assets/checkpoints need task and action-schema adapter before Franka+Robotiq RoboLab rollout.'),
 ('qwen_vl_alibaba','not_action_policy','Qwen/Qwen-VL models are VLMs unless paired with a robot action head; not directly scoreable as RoboLab policy.'),
]
summary=[]
for policy,status,reason in models:
    out_root=report_dir/f'{qid}_{policy}_model_probe'
    out_root.mkdir(parents=True, exist_ok=True)
    with (out_root/'episode_results.jsonl').open('w', encoding='utf-8') as f:
        for t in tasks:
            f.write(json.dumps({'task_name':t['task_name'],'env_name':t['task_name'],'policy':policy,'status':status,'adapter_required':status not in {'completed_in_phase_01'},'success':None,'score':None,'episode_step':None,'reason':reason}, ensure_ascii=False)+'\n')
    (out_root/'model_probe_manifest.json').write_text(json.dumps({'policy':policy,'status':status,'reason':reason,'rows':len(tasks)}, ensure_ascii=False, indent=2), encoding='utf-8')
    summary.append({'policy':policy,'status':status,'reason':reason,'out_root':str(out_root)})
(report_dir/f'{qid}_other_models_probe_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
PYMODELS
  local rc=$?
  json_event "07_other_models_probe" "completed" "$rc" "other model probe matrix written; unavailable adapters are marked explicitly" "{\"summary\":\"${REPORT_DIR}/${QUEUE_ID}_other_models_probe_summary.json\"}"
  append_md_section "\n## $(date '+%Y-%m-%d %H:%M:%S') - 其他模型对照记录\n\n- 阶段 ID：\`07_other_models_probe\`\n- 状态：\`completed\`\n- 说明：Pi05 使用真实 20 任务结果；RoboChallenge pi、ReKep、PaliGemma、GR00T、Cosmos、阿里/Qwen 系列按当前本地可运行性写入 adapter/probe，不伪装成真实 RoboLab 成功率。\n- 输出：\`${REPORT_DIR}/${QUEUE_ID}_other_models_probe_summary.json\`\n"
  return 0
}

main() {
  log_line "resume supervisor started for ${QUEUE_ID}"
  json_event "resume_supervisor" "running" "NA" "waiting for camera phase then continuing remaining phases" "{\"log\":\"${SUPERVISOR_LOG}\"}"
  append_md_section "\n## $(date '+%Y-%m-%d %H:%M:%S') - 4090 接力 supervisor 启动\n\n- 状态：\`running\`\n- 说明：等待当前相机阶段完成，随后自动执行腕部相机取消、机器人调整、其他模型 probe。\n- 日志：\`${SUPERVISOR_LOG}\`\n"
  wait_and_finish_camera || exit 1
  run_wrist_blackout || true
  run_robot_base_shift || true
  run_other_models_probe || true
  json_event "resume_supervisor" "completed" "0" "remaining phases reached terminal state" "{\"log\":\"${SUPERVISOR_LOG}\"}"
  append_md_section "\n## $(date '+%Y-%m-%d %H:%M:%S') - 接力队列到达终态\n\n- 状态：\`completed\`\n- 状态 JSONL：\`${STATUS_JSONL}\`\n- 日志：\`${SUPERVISOR_LOG}\`\n"
  log_line "resume supervisor completed"
}

main "$@"
