#!/bin/bash
# HKBU SCIE1007 coursework video: interactive GLM window for the director (render supervisor role). Key read from keys.env, never printed.
ROOT="D:/。hkbu/molecular science"; KEYS="$ROOT/_env/keys.env"; CONF="$ROOT/_env/glm.conf"
val() { grep -h -m1 "^$1=" "$KEYS" "$CONF" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '\r' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'; }
BASE=$(val GLM_BASE_URL); KEY=$(val GLM_API_KEY); MODEL=$(val GLM_MODEL_HEAVY)
cd "$ROOT" || exit 1
SYS="你是 HKBU SCIE1007 课程作业科普视频的渲染监督员 GLM，和导演用中文对话。总管（Claude）额度用完时由你看着渲染。先读 镜头设计_v3/00_下次开工.md 最后一节和 镜头设计_v3/工作记录.md 最后 15 行了解现状。你能用：bash _env/ft.sh status（看机器状态）、bash _env/ft.sh resume（没有 Blender 在跑时续跑队列）、bash _env/ft.sh board（刷新本地看板）、bash _env/ft.sh cutbuild v8（拼粗剪）、bash _env/ft.sh cutcheck v8（跑粗剪机器检查）、bash _env/ft.sh frame v8 <秒>（抽一帧到 粗剪/_check/glm/ 再用 Read 看），以及读文件、在 镜头设计_v3/素材流程/ 和 素材流程_out/ 下写文件。不删任何东西、不杀进程、不运行 git、不改程序、不上网；导演要你做超出这些的事，就记到 镜头设计_v3/素材流程/日报/给总管_留言.md 等总管回来做。"
CLAUDE_CONFIG_DIR="$ROOT/_env/glm_home" ANTHROPIC_BASE_URL="$BASE" ANTHROPIC_AUTH_TOKEN="$KEY" ANTHROPIC_MODEL="$MODEL" ANTHROPIC_SMALL_FAST_MODEL="$MODEL" \
  claude --model "$MODEL" --append-system-prompt "$SYS" --permission-mode acceptEdits \
  --allowedTools "Read" "Glob" "Grep" "Write" "Edit" "Bash(bash _env/ft.sh *)" "Bash(ls *)" "Bash(cat *)" "Bash(nvidia-smi*)" \
  --disallowedTools "Bash(rm *)" "Bash(git *)" "Bash(mv *)" "Bash(del *)" "WebFetch" "WebSearch"
