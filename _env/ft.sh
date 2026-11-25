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
