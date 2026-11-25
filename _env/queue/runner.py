# -*- coding: utf-8 -*-
"""HKBU SCIE1007 coursework video: render queue daemon. Run: py -3.11 -X utf8 runner.py"""
import os, sys, time, subprocess, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qlib as L

PIDF = os.path.join(L.Q, "runner.pid")
HB = os.path.join(L.Q, "heartbeat.txt")
procs = {}  # id -> Popen (only for jobs this runner process started)


def heartbeat_age():
    try:
        return time.time() - os.path.getmtime(HB)
    except OSError:
        return 1e9


def single_instance():
    try:
        old = int(open(PIDF).read().strip())
    except Exception:
        old = 0
    if old and old != os.getpid() and L.pid_alive(old) and heartbeat_age() < 60:
        return False
    open(PIDF, "w").write(str(os.getpid()))
    return True


def exit_path(j):
    return os.path.join(L.LOGS, j["id"] + ".exit")


def read_exit(j):
    try:
        s = open(exit_path(j)).read().strip()
        return int(s) if s else None
    except Exception:
        return None


def finish(j, code):
    old = j["status"]
    j["ended"] = L.now_s()
    j["pid"] = None
    if code == 0:
        j["status"] = "done"
    else:
        j["tries"] = int(j.get("tries", 0)) + 1
        j["status"] = "waiting" if j["tries"] < 2 else "failed"
    L.log_event(j["id"], old, j["status"], "code=%s tries=%s" % (code, j["tries"]))


def start(j):
    os.makedirs(L.LOGS, exist_ok=True)
    open(exit_path(j), "w").close()  # truncate stale exit code
    lp = L.log_path(j)
    os.makedirs(os.path.dirname(lp), exist_ok=True)
    env = dict(os.environ, QCMD=j["cmd"], QEXIT="_env/queue/logs/%s.exit" % j["id"])
    with open(lp, "ab") as lf:
        lf.write(("\n=== %s start (try %d) ===\n" % (L.now_s(), int(j.get("tries", 0)) + 1)).encode("utf-8"))
        lf.flush()
        p = subprocess.Popen([L.BASH, "-c", 'bash -c "$QCMD"; echo $? > "$QEXIT"'], cwd=L.ROOT, env=env,
                             stdin=subprocess.DEVNULL, stdout=lf, stderr=subprocess.STDOUT,
                             creationflags=L.NOWIN | 0x00000200)
    procs[j["id"]] = p
    old = j["status"]
    j["status"], j["pid"], j["started"], j["ended"] = "running", p.pid, L.now_s(), None
    L.log_event(j["id"], old, "running", "pid=%d" % p.pid)


def tick():
    st = L.settings()
    with L.txn() as q:
        jobs = q["jobs"]
        for j in jobs:
            if j["status"] != "running":
                procs.pop(j["id"], None)
                continue
            p = procs.get(j["id"])
            if p is not None:
                if p.poll() is None:
                    continue
                code = read_exit(j)
                code = p.returncode if code is None else code
                procs.pop(j["id"], None)
            else:
                if L.pid_alive(j.get("pid")):
                    continue
                code = read_exit(j)  # None if unknown
            finish(j, code if code is not None else -1)
        if L.flag_on("PAUSED_ALL"):
            return
        done = {j["id"] for j in jobs if j["status"] == "done"}
        gpu_ok = L.gpu_state(st)[0] == "free"
        gpu_n = None
        slots = None
        for j in jobs:
            if j["status"] != "waiting" or not all(d in done for d in j.get("after", [])):
                continue
            running = [r for r in jobs if r["status"] == "running"]
            if j["res"] == "gpu":
                if not gpu_ok:
                    continue
                if gpu_n is None:
                    gpu_n = max(L.blender_count(), sum(1 for r in running if r["res"] == "gpu"))
                if gpu_n >= L.MAX_GPU:
                    continue
                gpu_n += 1
            else:                                   # 11-24：按种类上限 + 内存 + 显存 + NVENC 放行（qlib.Slots）
                if slots is None:
                    slots = L.Slots(running)
                if slots.why_not(j):
                    continue
                slots.take(j)
            try:
                start(j)
            except Exception:
                traceback.print_exc()


def main():
    if not single_instance():
        print("runner already running")
        return
    print("runner up pid", os.getpid(), flush=True)
    while True:
        try:
            tick()
        except Exception:
            traceback.print_exc()
            sys.stderr.flush()
        try:
            with open(HB, "w") as f:
                f.write(L.now_s() + "\n")
            open(PIDF, "w").write(str(os.getpid()))
        except Exception:
            pass
        time.sleep(10)


if __name__ == "__main__":
    main()
