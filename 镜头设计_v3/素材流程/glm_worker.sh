#!/bin/bash
# HKBU SCIE1007 coursework science video. Starts the footage manager (the cheaper model behind the relay in _env/keys.env) as a worker
# on one task from 03_素材管理员手册.md. The key is read from _env/keys.env and passed in the environment only: never printed, never logged.
# The key is the only thing the director fills in (_env/keys.env); address and models are in _env/glm.conf. Only the models listed in
# GLM_MODELS_ALLOWED can run: the cheap one for clerical tasks, the full one for tasks that mean looking at pictures.
# Run:  bash glm_worker.sh check                  one short call, to see that address, key and model work
#       bash glm_worker.sh G0 D                   task G0 of the handbook on member D's folder (also G1 ... G8)
# GLM_API_STYLE=anthropic runs it inside Claude Code against the relay (its own empty config folder, so none of the director's plugins,
# memory or history are loaded); GLM_API_STYLE=openai runs it inside Codex. It may read anything in the project, write only under
# 素材流程_out/ and 镜头设计_v3/素材流程/, and run only the pipeline's own python and ffmpeg: no deleting, no git.
ROOT="D:/。hkbu/molecular science"
KEYS="$ROOT/_env/keys.env"
CONF="$ROOT/_env/glm.conf"
FLOW="$ROOT/镜头设计_v3/素材流程"
val() { grep -h -m1 "^$1=" "$KEYS" "$CONF" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'; }
STYLE=$(val GLM_API_STYLE); BASE=$(val GLM_BASE_URL); KEY=$(val GLM_API_KEY)
ALLOWED=$(val GLM_MODELS_ALLOWED); LIGHT=$(val GLM_MODEL_LIGHT); HEAVY=$(val GLM_MODEL_HEAVY)
[ -n "$KEY" ] || { echo "钥匙没填：请在 $KEYS 里的 GLM_API_KEY= 后面贴上钥匙"; exit 2; }
[ -n "$BASE" ] && [ -n "$LIGHT" ] && [ -n "$HEAVY" ] || { echo "$CONF 不完整"; exit 2; }
TASK=${1:-check}; WHO=${2:-}
if [ "$TASK" = check ]; then
  PROMPT="Reply with exactly: ready"
else
  [ -n "$WHO" ] || { echo "用法：bash glm_worker.sh <G0..G8> <A|B|C|D>"; exit 2; }
  PROMPT="HKBU SCIE1007 课程作业的科普视频。你是这个项目的素材管理员。先完整读一遍 $FLOW/03_素材管理员手册.md 和 $FLOW/04_命名规则.md，然后只做手册里的 $TASK 这一件活，对象是组员 $WHO（原件在 $ROOT/人员素材啊/$WHO/）。照手册写的命令、标准和写回的文件做；拿不准的标存疑；做完按手册 G8 写日报到 $FLOW/日报/。不删任何东西，不改原件，不运行 git。"
fi
case "$TASK" in G1|G3|G4|G5|G6|G7) MODEL=$HEAVY ;; *) MODEL=$LIGHT ;; esac
[ -n "$GLM_MODEL_OVERRIDE" ] && MODEL=$GLM_MODEL_OVERRIDE
case " $ALLOWED " in *" $MODEL "*) ;; *) echo "不允许的模型：$MODEL（只许 $ALLOWED）"; exit 2 ;; esac
echo "model: $MODEL"
mkdir -p "$FLOW/日报" "$ROOT/_env/glm_home" "$ROOT/_env/glm_log"
LOG="$ROOT/_env/glm_log/$(date +%Y%m%d_%H%M%S)_${TASK}_${WHO}.log"
cd "$ROOT" || exit 1
if [ "$STYLE" = openai ]; then
  OPENAI_BASE_URL="$BASE" OPENAI_API_KEY="$KEY" codex exec -m "$MODEL" --sandbox workspace-write "$PROMPT" 2>&1 | tee "$LOG"
else
  CLAUDE_CONFIG_DIR="$ROOT/_env/glm_home" ANTHROPIC_BASE_URL="$BASE" ANTHROPIC_AUTH_TOKEN="$KEY" ANTHROPIC_MODEL="$MODEL" ANTHROPIC_SMALL_FAST_MODEL="$MODEL" \
    claude -p "$PROMPT" --model "$MODEL" --permission-mode acceptEdits \
    --allowedTools "Read" "Glob" "Grep" "Write" "Edit" "Bash(*/_env/footage/Scripts/python.exe *)" "Bash(*/_env/ffmpeg/*)" "Bash(ls *)" "Bash(cat *)" "Bash(nvidia-smi*)" \
    --disallowedTools "Bash(rm *)" "Bash(git *)" "Bash(mv *)" "Bash(del *)" "WebFetch" "WebSearch" 2>&1 | tee "$LOG"
fi
echo "log: $LOG"
