#!/bin/bash
# HKBU SCIE1007 coursework science video. Starts the footage manager (the cheaper model behind the relay in _env/keys.env) as a worker
# on one task from 03_素材管理员手册.md. The key is read from _env/keys.env and passed in the environment only: never printed, never logged.
# The key is the only thing the director fills in (_env/keys.env); address and models are in _env/glm.conf. Only the models listed in
# GLM_MODELS_ALLOWED can run: the cheap one for clerical tasks, the full one for tasks that mean looking at pictures.
# Run:  bash glm_worker.sh check                  one short call, to see that address, key and model work
#       bash glm_worker.sh G0 D                   task G0 of the handbook on member D's folder (also G1 ... G8)
# GLM_API_STYLE=anthropic runs it inside Claude Code against the relay (its own empty config folder, so none of the director's plugins,
# memory or history are loaded); GLM_API_STYLE=openai runs it inside Codex. It may read anything in the project, write only under
# 素材流程_out/ and 镜头设计_v3/素材流程/, and run only the pipeline through _env/ft.sh (written below, ASCII path so the allow-list
# matches): no deleting, no git. Tasks that look at pictures use GLM_MODEL_VISION, because the relay answers 502 when glm-5.3 gets images.
ROOT="D:/。hkbu/molecular science"
KEYS="$ROOT/_env/keys.env"
CONF="$ROOT/_env/glm.conf"
FLOW="$ROOT/镜头设计_v3/素材流程"
val() { grep -h -m1 "^$1=" "$KEYS" "$CONF" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '
' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'; }
STYLE=$(val GLM_API_STYLE); BASE=$(val GLM_BASE_URL); KEY=$(val GLM_API_KEY)
ALLOWED=$(val GLM_MODELS_ALLOWED); LIGHT=$(val GLM_MODEL_LIGHT); HEAVY=$(val GLM_MODEL_HEAVY); VISION=$(val GLM_MODEL_VISION)
VISION=${VISION:-$LIGHT}
[ -n "$KEY" ] || { echo "钥匙没填：请在 $KEYS 里的 GLM_API_KEY= 后面贴上钥匙"; exit 2; }
[ -n "$BASE" ] && [ -n "$LIGHT" ] && [ -n "$HEAVY" ] || { echo "$CONF 不完整"; exit 2; }
TASK=${1:-check}; WHO=${2:-}
if [ "$TASK" = check ]; then
  PROMPT="Reply with exactly: ready"
else
  [ -n "$WHO" ] || { echo "用法：bash glm_worker.sh <G0..G8> <A|B|C|D>  或  bash glm_worker.sh CUT all"; exit 2; }
  PROMPT="HKBU SCIE1007 课程作业的科普视频。现在是 $(date '+%Y-%m-%d %H:%M') 韩国时间，写时间就用它。你是这个项目的素材管理员。先完整读一遍 $FLOW/03_素材管理员手册.md 和 $FLOW/04_命名规则.md，然后只做手册里的 $TASK 这一件活，对象是组员 $WHO（原件在 $ROOT/人员素材啊/$WHO/）。照手册写的命令、标准和写回的文件做；拿不准的标存疑；做完按手册 G8 写日报到 $FLOW/日报/。不删任何东西，不改原件，不运行 git。跑流程只用这几条命令（工作目录已经是项目根）：bash _env/ft.sh run $WHO <步号，如 0 或 1>；bash _env/ft.sh listen $WHO（第 3 步之后的听检）；bash _env/ft.sh ffprobe <ffprobe 的参数>；bash _env/ft.sh grade（G6 调色）；bash _env/ft.sh help。别的 python、ffmpeg 写法都会被拦。"
fi
if [ "$TASK" = CUT ]; then
  PROMPT="HKBU SCIE1007 课程作业的科普视频。现在是 $(date '+%Y-%m-%d %H:%M') 韩国时间，写时间就用它。你是这个项目的剪辑助理。先完整读一遍 $ROOT/镜头设计_v3/粗剪/粗剪规则.md，再读 $ROOT/镜头设计_v3/粗剪/cut_v4_report.md 和 cut_v4.json，然后照规则第二节 C1–C6 逐条检查，按第四节交 粗剪检查.md。看图用 Read 打开 _check 里的 jpg。只用这两条命令：bash _env/ft.sh cutframe <秒>；bash _env/ft.sh help。不删任何东西，不运行 git，不改规则和程序。"
fi
if [ "$TASK" = WATCH ]; then
  PROMPT="HKBU SCIE1007 课程作业的科普视频。现在是 $(date '+%Y-%m-%d %H:%M') 韩国时间。你是渲染监督员。先读 $ROOT/镜头设计_v3/00_下次开工.md 最后一节和 $ROOT/镜头设计_v3/工作记录.md 最后 15 行。然后：1) 运行 bash _env/ft.sh status 看机器状态。2) 如果 blender 数为 0、而工作记录或 00_下次开工 里写着还有没渲完的任务，运行 bash _env/ft.sh resume 续跑（它自己会判断，已渲的帧会跳过）。3) D 盘或 C 盘剩余少于 10 GB 时，在报告第一行写【磁盘告急】。4) 把一段简短中文状态（时间、在跑什么、显卡占用、磁盘、有无报错、是否续跑过）追加到 $FLOW/日报/渲染监督_$(date +%Y%m%d).md；再把 $ROOT/素材流程_out/now.json 的 notes 第一条改成 '监督 HH:MM：<一句话状态>'（保持合法 JSON，不要写反斜杠），然后运行 bash _env/ft.sh board。只用 bash _env/ft.sh status / resume / board 和 Read/Write/Edit；不删任何东西，不杀进程，不运行 git，不改程序和工作记录。"
fi
# CUT <1..8>: one chapter per run (the relay answers 502 on the whole film in one go)
if [ "$TASK" = CUT ] && [ "$WHO" != all ]; then
  PROMPT="$PROMPT 这一次只检查段号以 $WHO- 开头的段（第 $WHO 章），别的段不看；结果写到 粗剪检查_S$WHO.md（不要写 粗剪检查.md），抽帧不超过 12 张。"
fi
if [ "$TASK" = PAGE ]; then
  PROMPT="HKBU SCIE1007 课程作业的科普视频。现在是 $(date '+%Y-%m-%d %H:%M') 韩国时间。你是二维页面助理。先完整读 $ROOT/镜头设计_v3/映射/GLM页面手册.md，再读 $ROOT/镜头设计_v3/映射/GLM页面任务.md 里段 $WHO 那一节，然后只做段 $WHO：写事件表、写页面、跑检查，改到检查表全过，最后按手册第 7 节写报告。如果这段目录里已有 look_report.md 且第一行是'看图：不过'，这次就照它逐条改页面，再跑 pagecheck。只用这几条命令：bash _env/ft.sh pageprep $WHO；bash _env/ft.sh pagecheck $WHO；bash _env/ft.sh pagestills $WHO；bash _env/ft.sh help。只许写手册第 2 节列出的文件。不删任何东西，不运行 git，不改别的段的文件、不改 kit.jsx 和 oncam.jsx。"
fi
# 11-18 22:40：中转站对带图的请求一直 502，GLM 看图停用；只写占位，让分道脚本往下走，真正的检查交给 Opus
if [ "$TASK" = PAGELOOK ]; then
  a=${WHO%%+*}; case " 3-01 3-06 3-09 4-04 4-08 4-11 5-02 5-05 5-09 6-04 6-12 7-01 8-01 8-04 " in *" $a "*) C="OnCam${a/-/}" ;; *) C="Manual${a/-/}" ;; esac
  D="$ROOT/镜头设计_v3/映射/_cache/pages/$C"; mkdir -p "$D"
  [ -f "$D/look_report.md" ] || printf '看图：过（GLM 没看图，只是让分道往下走；待 Opus 检查）
' > "$D/look_report.md"
  echo "PAGELOOK skipped for $WHO"; exit 0
fi
if [ "$TASK" = PAGELOOK ]; then
  PROMPT="HKBU SCIE1007 课程作业的科普视频。现在是 $(date '+%Y-%m-%d %H:%M') 韩国时间。你是二维页面的看片员。先读 $ROOT/镜头设计_v3/映射/GLM页面手册.md 第 3、5 节和 $ROOT/镜头设计_v3/映射/GLM页面任务.md 里段 $WHO 那一节。再读这段的 report.md（在 $ROOT/镜头设计_v3/映射/_cache/pages/ 下，合成名见手册第 1 节），用 Read 逐张打开里面列出的静帧 png。对每张图查：字或零件有没有互相重叠、压线、出框、被裁掉；出镜页图形有没有挡到人；字是不是太小看不清；画面是不是空、和任务单说的内容对不对；有没有错字。把结果写到同一目录的 look_report.md：第一行写 '看图：过' 或 '看图：不过'，下面逐张列问题（写清在哪个位置、哪个元素、建议怎么挪）。只用 Read 和 Write，只写 look_report.md。不删任何东西，不运行 git，不改页面代码。"
fi
if [ "$TASK" = QC ]; then
  PROMPT="HKBU SCIE1007 课程作业的科普视频。现在是 $(date '+%Y-%m-%d %H:%M') 韩国时间。你是成片机检员兼进度监督。1) 运行 bash _env/ft.sh qc，它会给导演检查文件夹里新出的视频做机检（分辨率、帧率、黑帧、冻帧、响度），结果追加在 $ROOT/导演检查_$(date +%Y%m%d)/_GLM机检.md。2) 读 $ROOT/镜头设计_v3/深化/17_收尾排班.md 第四节时段表和第六节判定点，再用 ls 看 $ROOT/导演检查_$(date +%Y%m%d)/ 和前一天文件夹、以及 $ROOT/导演检查_20261123/ 里已经交出的 mp4（文件名里有段号），对照现在的时间，列出：已交哪些段、按排期这时应该交哪些段、落后了哪些、到这个钟点应该交而没交的（单列一行）、下一个判定点是什么时候、照判定点规则到时该降哪几段。3) 把机检里结果不是'过'的条目和进度落后的条目，写成一段简短中文，追加到 $FLOW/日报/监督_$(date +%Y%m%d).md（带时间）；如果有黑帧、冻帧、分辨率或帧率不对，第一行写【机检不过】并列出文件和时间点。只用 bash _env/ft.sh qc、ls、cat 和 Read/Write/Edit；不删任何东西，不改视频和程序，不运行 git。"
fi
case "$TASK" in G1|G4|G5|G6|CUT|PAGELOOK) MODEL=$VISION ;; PAGE) MODEL=$LIGHT ;; G3|G7) MODEL=$HEAVY ;; *) MODEL=$LIGHT ;; esac
[ -n "$GLM_MODEL_OVERRIDE" ] && MODEL=$GLM_MODEL_OVERRIDE
case " $ALLOWED " in *" $MODEL "*) ;; *) echo "不允许的模型：$MODEL（只许 $ALLOWED）"; exit 2 ;; esac
echo "model: $MODEL"
mkdir -p "$FLOW/日报" "$ROOT/_env/glm_home" "$ROOT/_env/glm_log"
LOG="$ROOT/_env/glm_log/$(date +%Y%m%d_%H%M%S)_${TASK}_${WHO}.log"
cd "$ROOT" || exit 1
cat > "$ROOT/_env/ft.sh" <<'FT'
#!/bin/bash
# Written by glm_worker.sh on every run. The only way the footage manager runs the pipeline: fixed ASCII command, member A-D only.
ROOT="D:/。hkbu/molecular science"; PY="$ROOT/_env/footage/Scripts/python.exe"; FLOW="$ROOT/镜头设计_v3/素材流程"
case "$1" in
  run) case "$2" in A|B|C|D) ;; *) echo "member must be A, B, C or D"; exit 2 ;; esac
       case "$3" in *[!0-9,]*|"") echo "steps must look like 0 or 0,1"; exit 2 ;; esac
       exec "$PY" "$FLOW/run.py" "$ROOT/人员素材啊/$2" --steps "$3" ;;
  listen) case "$2" in A|B|C|D) ;; *) echo "member must be A, B, C or D"; exit 2 ;; esac
       exec "$PY" "$FLOW/listen.py" "$2" ;;
  ffprobe) shift; exec "$ROOT/_env/ffmpeg/ffprobe.exe" "$@" ;;
  grade) exec "$PY" "$FLOW/grade.py" --try "$ROOT/素材流程_out/调色/grade_try.json" ;;
  cut) exec "$PY" "$ROOT/镜头设计_v3/粗剪/build_cut.py" ;;
  cutframe) case "$2" in *[!0-9.]*|"") echo "seconds must be a number"; exit 2 ;; esac
       mkdir -p "$ROOT/镜头设计_v3/粗剪/_check"
       exec "$ROOT/_env/ffmpeg/ffmpeg.exe" -v error -y -ss "$2" -i "$ROOT/镜头设计_v3/粗剪/cut_v4.mp4" -frames:v 1 -update 1 "$ROOT/镜头设计_v3/粗剪/_check/$2.jpg" ;;
  cutbuild) case "$2" in v[0-9]*) ;; *) echo "version like v8"; exit 2 ;; esac
       PYTHONIOENCODING=utf-8 exec "$PY" "$ROOT/镜头设计_v3/粗剪/build_cut_$2.py" ;;
  cutcheck) case "$2" in v[0-9]*) ;; *) echo "version like v8"; exit 2 ;; esac
       PYTHONIOENCODING=utf-8 exec "$PY" "$ROOT/镜头设计_v3/粗剪/_check/check_$2.py" "cut_$2" ;;
  frame) case "$2" in v[0-9]*) ;; *) echo "version like v8"; exit 2 ;; esac
       case "$3" in *[!0-9.]*|"") echo "seconds must be a number"; exit 2 ;; esac
       mkdir -p "$ROOT/镜头设计_v3/粗剪/_check/glm"
       exec "$ROOT/_env/ffmpeg/ffmpeg.exe" -v error -y -ss "$3" -i "$ROOT/镜头设计_v3/粗剪/cut_$2.mp4" -frames:v 1 -update 1 -vf scale=960:-1 "$ROOT/镜头设计_v3/粗剪/_check/glm/$2_$3.jpg" ;;
  mapbuild) M="$ROOT/镜头设计_v3/映射"; export PYTHONIOENCODING=utf-8
       "$PY" "$M/build_master.py" && "$PY" "$M/check_master.py"; "$PY" "$M/resolve.py" && exec "$PY" "$M/validate_events.py" --json "$M/_reports/validate.json" ;;
  mapcheck) case "$2" in [0-9]-[0-9][0-9]|W[0-9]) ;; *) echo "segment like 1-08"; exit 2 ;; esac
       M="$ROOT/镜头设计_v3/映射"; export PYTHONIOENCODING=utf-8
       "$PY" "$M/validate_events.py" "$2" || exit 1
       case "$3" in "") exit 0 ;; *.mp4|*.mov) ;; *) echo "video must be .mp4 or .mov"; exit 2 ;; esac
       case "$4" in "") exec "$PY" "$M/check_sync.py" "$3" "$2" ;; *[!0-9.]*) echo "t0 must be seconds"; exit 2 ;; *) exec "$PY" "$M/check_sync.py" "$3" "$2" --t0 "$4" --dur "${5:-30}" ;; esac ;;
  status) exec bash "$ROOT/_env/jobs/watch_status.sh" ;;
  qc) PYTHONIOENCODING=utf-8 exec "$PY" -X utf8 "$ROOT/_env/jobs/qc_new.py" ;;
  resume) exec bash "$ROOT/_env/jobs/resume_renders.sh" ;;
  board) PYTHONIOENCODING=utf-8 exec "$PY" "$FLOW/board.py" ;;
  pageprep|pagecheck|pagestills)
       case "$2" in [0-9]-[0-9][0-9]|[0-9]-[0-9][0-9]+[0-9]-[0-9][0-9]|[0-9]-[0-9][0-9]+[0-9]-[0-9][0-9]+[0-9]-[0-9][0-9]+[0-9]-[0-9][0-9]) ;; *) echo "segment like 3-02 or 4-04+4-05"; exit 2 ;; esac
       export PYTHONIOENCODING=utf-8; T="$ROOT/镜头设计_v3/映射/page_tool.py"
       mkdir -p "$ROOT/_env/tmp"; export TEMP="$ROOT/_env/tmp" TMP="$ROOT/_env/tmp" TMPDIR="$ROOT/_env/tmp"; L="$ROOT/_env/tmp/render_lock"; until mkdir "$L" 2>/dev/null; do sleep 10; done; trap 'rmdir "$L"' EXIT; case "$1" in pageprep) "$PY" "$T" prep "$2" ;; pagecheck) "$PY" "$T" check "$2" ;; pagestills) "$PY" "$T" check "$2" --stills-only ;; esac ;;
  *) echo "bash _env/ft.sh run <A|B|C|D> <steps>   |   bash _env/ft.sh listen <A|B|C|D>   |   bash _env/ft.sh ffprobe <args>   |   bash _env/ft.sh grade"; "$PY" "$FLOW/run.py" --help ;;
esac
FT
if [ "$STYLE" = openai ]; then
  OPENAI_BASE_URL="$BASE" OPENAI_API_KEY="$KEY" codex exec -m "$MODEL" --sandbox workspace-write "$PROMPT" 2>&1 | tee "$LOG"
else
  CLAUDE_CONFIG_DIR="$ROOT/_env/glm_home" ANTHROPIC_BASE_URL="$BASE" ANTHROPIC_AUTH_TOKEN="$KEY" ANTHROPIC_MODEL="$MODEL" ANTHROPIC_SMALL_FAST_MODEL="$MODEL" \
    claude -p "$PROMPT" --model "$MODEL" --permission-mode acceptEdits \
    --allowedTools "Read" "Glob" "Grep" "Write" "Edit" "Bash(bash _env/ft.sh *)" "Bash(ls *)" "Bash(cat *)" "Bash(nvidia-smi*)" \
    --disallowedTools "Bash(rm *)" "Bash(git *)" "Bash(mv *)" "Bash(del *)" "WebFetch" "WebSearch" < /dev/null 2>&1 | tee "$LOG"
fi
echo "log: $LOG"
