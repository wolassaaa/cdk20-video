"""Bench runner for the 4K tests. Runs the cases of a JSON file one at a time, each one command, and logs what plan section 4 asks for:
wall time per frame, peak VRAM (nvidia-smi samples), peak system RAM, free disk on C: and D:. A case stops at its time limit or when VRAM passes its limit.
After every case OUT/results.json and OUT/results.md are rewritten, so a crash loses nothing. Each case's output goes to OUT/logs/NAME.log.

  python run_bench.py cases_4k.json [--out DIR] [--only r01*,r02*] [--resume] [--dry-run]

--only     comma-separated name patterns.  --resume  skips cases already "ok" in OUT/results.json.
--dry-run  launches none of the real commands. It prints each one, checks the program, the script and every --flag against the script's source, then runs a
           harmless stand-in through the same monitor and writes OUT/dryrun.json and OUT/dryrun.md. Exit code 1 if a check failed.

Cases file:
  vars      {NAME} is replaced anywhere in cmd, cwd and mkdir. A list var fills a cmd slot of its own. OUT, PY and BENCH always exist.
  defaults  any case field: time_limit_s, vram_limit_gib, gpu
  cases     name, cmd (list), frames (expected, for s/frame and the completeness check), time_limit_s, est_min, note, and optionally
            cwd; mkdir (list of folders to create); gpu (false: no VRAM sensor needed); vram_limit_gib; blocked (text: never run, say why);
            frame_marker (regex for one output line per finished frame, default Blender's "Saved: '"; with a group, the group is the frames done so far)
Status: ok, failed (exit code), incomplete (exit 0 but fewer frames than expected: Blender can exit 0 after a script error), time_limit, vram_limit, no_sensor, blocked, dry-run.
"""
import argparse, ctypes, fnmatch, glob, json, os, re, shutil, statistics, subprocess, sys, threading, time

BENCH = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
MARKER = r"Saved: '"
POLL = 1.0
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
STAND_IN = [sys.executable, "-c", "import time\nfor i in range(3): print(\"Saved: 'dry-run %d'\" % i, flush=True); time.sleep(0.1)"]


# ---------------------------------------------------------------- sensors
def gpu_now():
    """(memory.used MiB, utilization %) of the busiest card, or None if nvidia-smi does not answer."""
    try:
        o = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,utilization.gpu", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=5, creationflags=NO_WINDOW).stdout
        rows = [[int(x) for x in l.split(",")] for l in o.strip().splitlines()]
        return max(r[0] for r in rows), max(r[1] for r in rows)
    except Exception:
        return None


class MemoryStatus(ctypes.Structure):
    _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong), ("total", ctypes.c_ulonglong), ("avail", ctypes.c_ulonglong)] + [(k, ctypes.c_ulonglong) for k in ("tp", "ap", "tv", "av", "ae")]


def ram_used():
    """whole-system physical memory in use, MiB"""
    if os.name == "nt":
        m = MemoryStatus(); m.length = ctypes.sizeof(m)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        return (m.total - m.avail) // 2 ** 20
    v = {l.split(":")[0]: int(l.split()[1]) for l in open("/proc/meminfo")}
    return (v["MemTotal"] - v["MemAvailable"]) // 1024


def disks():
    """free GiB on C: and D:"""
    out = {}
    for d in ("C", "D"):
        try: out[d] = round(shutil.disk_usage(d + ":/").free / 2 ** 30, 2)
        except OSError: pass
    return out


def kill_tree(p):
    """Blender has no children, but node has Chrome and the compositor: everything must go or the next case starts on a busy card."""
    if os.name == "nt": subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True, creationflags=NO_WINDOW)
    else: os.killpg(p.pid, 9)
    try: p.wait(timeout=15)
    except subprocess.TimeoutExpired: p.kill()


# ---------------------------------------------------------------- one case
def frame_stats(marks, wall, frames):
    """marks = (seconds since start, frames done). First frame carries the start-up (scene build, BVH, browser); s_per_frame is the steady rate after it."""
    res = dict(frames_done=marks[-1][1] if marks else None, first_frame_s=round(marks[0][0], 2) if marks else None, per_frame_s=[], s_per_frame=None, median_s=None, max_s=None)
    if len(marks) > 1:
        steps = [(b[0] - a[0]) / (b[1] - a[1]) for a, b in zip(marks, marks[1:])]
        res.update(per_frame_s=[round(s, 2) for s in steps], s_per_frame=round((marks[-1][0] - marks[0][0]) / (marks[-1][1] - marks[0][1]), 2), median_s=round(statistics.median(steps), 2), max_s=round(max(steps), 2))
    elif marks: res["s_per_frame"] = res["first_frame_s"]
    elif frames: res["s_per_frame"] = round(wall / frames, 2)
    return res


def run_case(case, cmd, cwd, log, vram_limit):
    """Launch cmd and watch it. Returns the measurements."""
    marker = re.compile(case.get("frame_marker") or MARKER)
    limit = case["time_limit_s"]
    gpu = case.get("gpu", True)
    start = gpu_now() if gpu else None
    res = dict(vram_idle_mib=start[0] if start else None, gpu_util_start=start[1] if start else None, ram_idle_mib=ram_used(), disk_before=disks())
    if gpu and start is None:
        return dict(res, status="no_sensor", note="nvidia-smi gave no reading, so the VRAM stop cannot work. Not started.")
    os.makedirs(os.path.dirname(log), exist_ok=True)
    marks = []; t0 = time.monotonic()
    p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=dict(os.environ, PYTHONUNBUFFERED="1"), creationflags=NO_WINDOW, start_new_session=os.name != "nt")

    def reader():
        with open(log, "wb") as f:
            for line in p.stdout:
                f.write(line)
                m = marker.search(line.decode("utf-8", "replace"))
                if m:
                    n = int(m.group(1)) if m.groups() else (marks[-1][1] + 1 if marks else 1)
                    if not marks or n > marks[-1][1]: marks.append((time.monotonic() - t0, n))
    th = threading.Thread(target=reader, daemon=True); th.start()

    vram_peak, ram_peak, free_min, stopped = res["vram_idle_mib"] or 0, res["ram_idle_mib"], dict(res["disk_before"]), None
    while True:
        g = gpu_now() if gpu else None
        if g: vram_peak = max(vram_peak, g[0])
        ram_peak = max(ram_peak, ram_used())
        for d, v in disks().items(): free_min[d] = min(free_min[d], v)
        if p.poll() is not None: break
        if time.monotonic() - t0 > limit: stopped = "time_limit"
        elif vram_limit and g and g[0] > vram_limit: stopped = "vram_limit"
        if stopped: kill_tree(p); break
        try: p.wait(timeout=POLL)
        except subprocess.TimeoutExpired: pass
    wall = time.monotonic() - t0
    th.join(timeout=10)
    code = p.wait()
    res.update(frame_stats(marks, wall, case.get("frames")))
    res.update(exit_code=code, wall_s=round(wall, 1), vram_peak_mib=vram_peak if start else None, ram_peak_mib=ram_peak, disk_min=free_min, disk_after=disks())
    if stopped: res["status"] = stopped
    elif code: res["status"] = "failed"
    elif marks and case.get("frames") and res["frames_done"] < case["frames"]: res["status"] = "incomplete"
    elif not marks and case.get("frames") and case.get("frame_marker", MARKER) is not None: res["status"] = "incomplete"
    else: res["status"] = "ok"
    return res


# ---------------------------------------------------------------- cases file
def expand(v, names):
    """{NAME} -> value until nothing changes; names it does not know stay, so JSON in a command is safe"""
    if isinstance(v, list):
        out = []
        for x in v:
            if isinstance(x, str) and x[:1] == "{" and x[-1:] == "}" and isinstance(names.get(x[1:-1]), list): out += expand(names[x[1:-1]], names)
            else: out.append(expand(x, names))
        return out
    if not isinstance(v, str): return v
    for _ in range(8):
        new = re.sub(r"\{(\w+)\}", lambda m: str(names[m.group(1)]) if isinstance(names.get(m.group(1)), (str, int, float)) else m.group(0), v)
        if new == v: break
        v = new
    return v


def bl_common_flags():
    txt = open(BENCH + "/../w0/bl_common.py", encoding="utf-8").read()
    out = set()
    for name in ("RENDER_FLAGS", "SEQ_FLAGS"):
        m = re.search(name + r"\s*=\s*\{(.*?)\n\}", txt, re.S)
        if m: out |= {"--" + k for k in re.findall(r'^\s*"([\w-]+)"\s*:', m.group(1), re.M)}
    return out


def known_flags(script):
    """every --flag a script's source defines, None if it cannot be told"""
    if script.endswith(".js"):
        opts = os.path.join(os.path.dirname(script), "..", "renderer", "dist", "options")
        return {"--" + f for p in glob.glob(opts + "/*.js") for f in re.findall(r"cliFlag = '([\w-]+)'", open(p, encoding="utf-8").read())}
    if not script.endswith(".py"): return None
    txt = open(script, encoding="utf-8").read()
    out = {f for call in re.findall(r"add_argument\(([^)]*)\)", txt) for f in re.findall(r'"(--[\w-]+)"', call)}
    if "add_render_flags" in txt or "RENDER_FLAGS" in txt: out |= bl_common_flags()
    m = re.search(r"U\.args\(\{(.*?)\}\)", txt, re.S)
    if m: out |= {"--" + k for k in re.findall(r'"([\w-]+)"\s*:', m.group(1))}
    return out


def check(cmd, cwd, out):
    """what a dry-run can prove without launching anything"""
    bad = ["path not found: " + a for a in cmd[1:] if re.match(r"[A-Za-z]:/", a) and not a.startswith(out) and "*" not in a and not os.path.exists(a)]
    if not (os.path.isfile(cmd[0]) or shutil.which(cmd[0])): bad.append("program not found: " + cmd[0])
    if cwd and not os.path.isdir(cwd): bad.append("cwd not found: " + cwd)
    if "-c" in cmd[:3]: return bad
    i = cmd.index("-P") + 1 if "-P" in cmd else next((k for k, x in enumerate(cmd[1:], 1) if x.endswith((".py", ".js"))), None)
    if i is None: return bad
    script = cmd[i]
    if not os.path.isfile(script): return bad + ["script not found: " + script]
    flags = known_flags(script)
    args = cmd[cmd.index("--") + 1:] if "--" in cmd else cmd[i + 1:]
    for a in args:
        if flags is not None and re.match(r"--[A-Za-z]", a) and a.split("=")[0] not in flags: bad.append("no such flag in %s: %s" % (os.path.basename(script), a))
    return bad


def fmt(v, spec="%s"): return "" if v is None else spec % v


def write_results(path, cases_file, results):
    with open(path + ".json", "w", encoding="utf-8") as f:
        json.dump(dict(cases_file=cases_file, updated=time.strftime("%Y-%m-%d %H:%M:%S"), cases=results), f, indent=1, ensure_ascii=False)
    rows = ["| case | status | frames | s/frame | first frame s | wall s | VRAM peak MiB | VRAM idle MiB | RAM peak MiB | RAM idle MiB | min free C: GiB | min free D: GiB |", "|" + " --- |" * 12]
    for r in results:
        d = r.get("disk_min") or {}
        rows.append("| %s | %s | %s/%s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["name"], r["status"], fmt(r.get("frames_done")), fmt(r.get("frames")), fmt(r.get("s_per_frame")), fmt(r.get("first_frame_s")), fmt(r.get("wall_s")),
            fmt(r.get("vram_peak_mib")), fmt(r.get("vram_idle_mib")), fmt(r.get("ram_peak_mib")), fmt(r.get("ram_idle_mib")), fmt(d.get("C")), fmt(d.get("D"))))
    notes = ["- **%s**: %s" % (r["name"], r["note"]) for r in results if r.get("note")]
    with open(path + ".md", "w", encoding="utf-8") as f:
        f.write("\n".join(rows + ([""] + notes if notes else [])) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cases"); ap.add_argument("--out", default=""); ap.add_argument("--only", default=""); ap.add_argument("--resume", action="store_true"); ap.add_argument("--dry-run", action="store_true")
    A = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    data = json.load(open(A.cases, encoding="utf-8"))
    out = os.path.abspath(A.out or os.path.join(BENCH, "out")).replace("\\", "/")
    os.makedirs(out, exist_ok=True)
    names = dict(data.get("vars", {}), OUT=out, PY=sys.executable.replace("\\", "/"), BENCH=BENCH)
    results_path = os.path.join(out, "dryrun" if A.dry_run else "results")
    done = {}
    prior = json.load(open(results_path + ".json", encoding="utf-8"))["cases"] if os.path.exists(results_path + ".json") else []
    if A.resume: done = {r["name"]: r for r in prior if r["status"] == "ok"}
    pats = [p for p in A.only.split(",") if p]
    results, problems = [], 0

    def merged():
        """earlier rows survive an --only run: their VRAM and timing exist nowhere else"""
        now = {r["name"] for r in results}
        return [r for r in prior if r["name"] not in now] + results

    selected = [c for c in data["cases"] if not pats or any(fnmatch.fnmatch(c["name"], p) for p in pats)]
    print("%d cases, about %.0f min by the estimates%s" % (len(selected), sum(c.get("est_min", 0) for c in selected if not c.get("blocked")), " (dry run)" if A.dry_run else ""), flush=True)
    for c in selected:
        c = dict(data.get("defaults", {}), **c)
        name = c["name"]
        if name in done:
            print("[%s] already ok, skipped" % name, flush=True); results.append(done[name]); continue
        cmd, cwd = expand(c["cmd"], names), expand(c.get("cwd"), names)
        if c.get("frame_marker"): c["frame_marker"] = expand(c["frame_marker"], names)
        base = dict(name=name, cmd=cmd, cwd=cwd, frames=c.get("frames"), time_limit_s=c.get("time_limit_s"), est_min=c.get("est_min"), note=c.get("note", ""))
        if c.get("blocked"):
            print("[%s] blocked: %s" % (name, c["blocked"]), flush=True)
            results.append(dict(base, status="blocked", note=c["blocked"])); write_results(results_path, A.cases, merged()); continue
        if A.dry_run:
            print("[%s] %s" % (name, subprocess.list2cmdline(cmd)), flush=True)
            bad = check(cmd, cwd, out)
            for b in bad: print("    !! " + b, flush=True)
            problems += len(bad)
        vram_limit = c["vram_limit_gib"] * 1024 if c.get("gpu", True) else None
        for d in expand(c.get("mkdir", []), names): os.makedirs(d, exist_ok=True)
        log = os.path.join(out, "logs", name + ".log")
        if A.dry_run:
            res = run_case(dict(frames=3, time_limit_s=30, gpu=c.get("gpu", True)), STAND_IN, None, log, None)
            if res["status"] == "ok": res["status"] = "dry-run"
            res["problems"] = bad
        else:
            res = run_case(c, cmd, cwd, log, vram_limit)
            if (res.get("gpu_util_start") or 0) > 15: base["note"] = ("card was %d %% busy at the start, the time is not clean. " % res["gpu_util_start"]) + base["note"]
        results.append(dict(base, **res)); write_results(results_path, A.cases, merged())
        print("[%s] %s  %s frames  %s s/frame  wall %s s  VRAM %s MiB  RAM %s MiB  free %s" % (name, res["status"], fmt(res.get("frames_done")), fmt(res.get("s_per_frame")), fmt(res.get("wall_s")), fmt(res.get("vram_peak_mib")), fmt(res.get("ram_peak_mib")), res.get("disk_min")), flush=True)
    print("wrote %s.json and .md" % results_path, flush=True)
    if A.dry_run and problems:
        print("%d problems found" % problems); sys.exit(1)


if __name__ == "__main__":
    main()
