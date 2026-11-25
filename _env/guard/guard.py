# -*- coding: utf-8 -*-
"""HKBU SCIE1007 coursework video: hard rules for Claude Code sessions (PreToolUse hook).

Reads the hook JSON on stdin. Prints a deny decision when a rule is broken, prints nothing otherwise.
Only acts on this project (cwd or the command mentions it). Any error in this script lets the call through.
Pause GPU work:  create C:/Users/woola/cdk20_guard/GPU_PAUSED   (delete it to resume).
"""
import sys, json, re, os, subprocess

GUARD_DIR = os.path.dirname(os.path.abspath(__file__))
PAUSE_FLAG = os.path.join(GUARD_DIR, "GPU_PAUSED")
PROJECT_MARKS = ("molecular science", "cdk20")
MAX_BLENDER = 2

# folders that must never be deleted or overwritten wholesale
PROTECTED = ("人员素材啊", "导演检查_", "镜头设计_v2", "镜头设计_v3/assets", "镜头设计_v3\\assets",
             "素材流程_out", "cdk20/final", "cdk20\\final")
DELETE_CMD = re.compile(r"(^|[\s;&|(])(rm|rmdir|rd|del|erase|Remove-Item|ri|shred)\b|robocopy\b.*(/MIR|/PURGE)|"
                        r"\bgit\s+clean\b|shutil\.rmtree|Clear-Content", re.I)
SECRET_READ = re.compile(r"(^|[\s;&|(])(cat|type|more|less|head|tail|bat|Get-Content|gc|cp|copy|Copy-Item|scp|curl|"
                         r"git\s+add|xxd|strings|grep|rg|Select-String|echo|print)\b", re.I)
SPEED = re.compile(r"minterpolate|tblend|framerate=|atempo|setpts\s*=\s*[^,\"' ]*(\*|/)\s*[\d.(]|setpts\s*=\s*[\d.]+\s*\*", re.I)
GPU_CMD = re.compile(r"blender|touchdesigner|fast_render|render_s\w*\.sh|resume_renders|nvenc|kit_parts\.py", re.I)
BLENDER_LAUNCH = re.compile(r"blender(\.exe)?[\"']?\s+(-b|--background|-P|--python)|fast_render|render_s\w*\.sh|"
                            r"resume_renders|\"\$B\"\s+-b|\$B\s+-b|\$BLENDER", re.I)


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": "[cdk20 hard rule] " + reason}},
                     ensure_ascii=True))
    sys.exit(0)


def blender_count():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq blender.exe", "/FO", "CSV", "/NH"],
                             capture_output=True, timeout=5).stdout.decode("ascii", "ignore")
        return sum(1 for ln in out.splitlines() if ln.lower().startswith('"blender.exe"'))
    except Exception:
        return 0


def check_shell(cmd):
    low = cmd.lower()
    killing = re.search(r"taskkill|stop-process|tasklist|get-process|pkill", low)

    if GPU_CMD.search(cmd) and not killing and os.path.exists(PAUSE_FLAG):
        deny("GPU is paused by the director (flag file %s exists). Do not start Blender, TouchDesigner or GPU "
             "encodes. Do CPU-only work, or wait until the director says to resume." % PAUSE_FLAG)

    if BLENDER_LAUNCH.search(cmd) and not killing:
        n = blender_count()
        starts = max(1, len(re.findall(r"(-b|--background)\b[^\n&]*&(?!&)", cmd)))
        if n + starts > MAX_BLENDER:
            deny("At most %d Blender processes at once: %d already running and this command starts %d more. "
                 "Wait for one to finish (tasklist | grep blender)." % (MAX_BLENDER, n, starts))

    if DELETE_CMD.search(cmd):
        for p in PROTECTED:
            if p.lower() in low:
                deny("This command deletes or mirrors over a protected folder (%s): member originals, review "
                     "folders, the live Remotion project and source assets are never deleted. Ask the director." % p)

    if "keys.env" in low and SECRET_READ.search(cmd) and not re.search(r"(source|\.)\s+\S*keys\.env", cmd):
        deny("_env/keys.env holds API keys and is never printed, copied or added to git. Use _env/ft.sh, "
             "which loads it internally.")

    if "名字.txt" in cmd and SECRET_READ.search(cmd):
        deny("名字.txt holds real names and student IDs. It is never printed, copied or committed; only the "
             "local title-card render script may open it. Use A/B/C/D everywhere else.")

    if "ffmpeg" in low and SPEED.search(cmd):
        deny("Never speed-change or frame-blend a finished render or the voice (setpts scaling, minterpolate, "
             "tblend, framerate, atempo). Re-render natively at 60 fps from the mapping table instead.")

    if re.search(r"\bgit\s+add\s+(-A\b|--all\b|\.(\s|$)|-u\b)|\bgit\s+commit\s+[^|;&]*-\w*a\w*\b(?!\S)", cmd):
        deny("Stage files by name. 'git add -A / . / -u' and 'git commit -a' sweep in other agents' uncommitted "
             "work and media; add only the files you wrote.")

    if re.search(r"\bgit\s+push\b.*(--force\b|-f\b)|\bgit\s+reset\s+--hard\b|\bgit\s+stash\s*(pop)?\s*($|[;&|])", cmd):
        deny("No force-push, hard reset or bare 'git stash'/'git stash pop' in this shared repo (worktrees share "
             "the stash). Use a WIP commit or 'git stash push -u -m <tag>' + 'git stash apply <sha>'.")


def main():
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {}) or {}
    cwd = (data.get("cwd") or os.getcwd()).lower()
    blob = json.dumps(ti, ensure_ascii=False).lower()
    if not any(m in cwd or m in blob for m in PROJECT_MARKS):
        return

    if tool in ("Bash", "PowerShell"):
        check_shell(ti.get("command", ""))

    elif tool in ("Read", "Edit", "Write", "NotebookEdit"):
        path = (ti.get("file_path") or ti.get("notebook_path") or "").replace("\\", "/")
        pl = path.lower()
        if pl.endswith("keys.env"):
            deny("_env/keys.env holds API keys and is never read or edited by an agent.")
        if path.endswith("名字.txt"):
            deny("名字.txt holds real names and student IDs and is never read or edited by an agent.")
        if tool != "Read" and "人员素材啊/" in path:
            deny("人员素材啊/ holds the members' original footage and is read-only. Write outputs elsewhere.")

    elif tool == "Agent":
        prompt = ti.get("prompt", "")
        if ti.get("subagent_type") != "web-fetch" and "SCIE1007" not in prompt:
            deny("Every agent prompt must open by saying this is the HKBU SCIE1007 coursework science video "
                 "(not research), then state the picture or render task. Add that line and resend.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        pass
