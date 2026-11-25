# -*- coding: utf-8 -*-
"""HKBU SCIE1007 coursework video: shared helpers for the render queue (runner / qctl / panel / ensure).
Nothing in here ever deletes a file: flags are turned off by renaming to <name>.off; logs only append."""
import os, sys, json, time, re, ctypes, subprocess, msvcrt, datetime, contextlib

Q = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(Q))
LOGS = os.path.join(Q, "logs")
QFILE = os.path.join(Q, "queue.json")
SETFILE = os.path.join(Q, "settings.json")
GUARD_PAUSED = "C:/Users/woola/cdk20_guard/GPU_PAUSED"
BASH = "C:/Program Files/Git/bin/bash.exe"
NOWIN = 0x08000000  # CREATE_NO_WINDOW
MAX_GPU = 3   # 11-24 导演：显存 12 GB 预算，一个 Blender 渲染约 3.5 GB
HEAVY_CPU = ("remotion", "ffmpeg")   # 旧规矩（11-24 前）：这两类同一时间只跑 1 个。QUEUE_OLD_SLOTS=1 回到旧规矩
# 11-24 并发规矩（导演定的资源上限）：非 Blender 任务按 种类上限 + 空闲内存 + 显存预算 + NVENC 会话数 放行，不再一刀切一次一个。
KIND_MAX = {"remotion": 2, "ffmpeg": 4, "comp": 4, "cut": 1, "whisper": 1}          # 同类同时最多几个（没列的种类不限个数，只看内存）
MEM_NEED_GB = {"remotion": 3.0, "ffmpeg": 0.9, "comp": 0.9, "cut": 2.0, "whisper": 3.0}  # 每个任务大约吃多少系统内存（Remotion --concurrency=6 实测约 3 GB）
MEM_NEED_DEFAULT = 0.5
MEM_RESERVE_GB = 1.0          # 放行后系统至少还剩这么多
VRAM_BUDGET_MB = 12 * 1024    # 16 GB 显存里我们用 12 GB，留 4 GB 给导演
VRAM_NEED_MB = {"comp": 400, "ffmpeg": 400, "cut": 400, "remotion": 300}
NVENC_MAX = 8                 # NVENC 同时编码会话上限（11-23 一次开 18 路报错过）
NVENC_KINDS = ("remotion", "ffmpeg", "comp", "cut")
RAMP_S = 120                  # 刚起的任务内存还没涨上来：起来不到 2 分钟的按满额预扣
OLD_SLOTS = os.environ.get("QUEUE_OLD_SLOTS") == "1"
FMT = "%Y-%m-%d %H:%M:%S"


def now_s():
    return datetime.datetime.now().strftime(FMT)


def parse_t(s):
    try:
        return datetime.datetime.strptime(s, FMT).timestamp()
    except Exception:
        return None


# ---------- flags (create / rename to .off, never delete) ----------
def fpath(n):
    return os.path.join(Q, n)


def flag_on(n):
    return os.path.exists(fpath(n))


def flag_set(n, on):
    p = fpath(n)
    off = p + ".off"
    if on:
        if os.path.exists(p):
            return
        if os.path.exists(off):
            os.replace(off, p)
        else:
            open(p, "a").close()
    elif os.path.exists(p):
        os.replace(p, off)


# ---------- lock + atomic json ----------
@contextlib.contextmanager
def locked(timeout=20):
    fd = os.open(os.path.join(Q, "queue.lock"), os.O_RDWR | os.O_CREAT)
    try:
        t0 = time.time()
        while True:
            try:
                os.lseek(fd, 0, 0)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                if time.time() - t0 > timeout:
                    raise
                time.sleep(0.05)
        try:
            yield
        finally:
            os.lseek(fd, 0, 0)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    finally:
        os.close(fd)


def _read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def _write_json(path, obj):
    tmp = "%s.tmp%d" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    for i in range(50):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            time.sleep(0.1)
    os.replace(tmp, path)


def load():
    with locked():
        return _read_json(QFILE, {"jobs": []})


@contextlib.contextmanager
def txn():
    with locked():
        q = _read_json(QFILE, {"jobs": []})
        yield q
        _write_json(QFILE, q)


def settings():
    s = _read_json(SETFILE, {})
    s.setdefault("gpu_quiet", "")
    return s


def log_event(jid, old, new, extra=""):
    os.makedirs(LOGS, exist_ok=True)
    with open(os.path.join(Q, "events.log"), "a", encoding="utf-8") as f:
        f.write("%s  %s  %s -> %s %s\n" % (now_s(), jid, old, new, extra))


# ---------- processes ----------
def pid_alive(pid):
    if not pid:
        return False
    k = ctypes.windll.kernel32
    h = k.OpenProcess(0x1000, False, int(pid))
    if not h:
        return False
    code = ctypes.c_ulong()
    ok = k.GetExitCodeProcess(h, ctypes.byref(code))
    k.CloseHandle(h)
    return bool(ok) and code.value == 259


def kill_tree(pid):
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, creationflags=NOWIN)


def blender_count():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq blender.exe", "/FO", "CSV", "/NH"],
                             capture_output=True, timeout=10, creationflags=NOWIN).stdout.decode("ascii", "ignore")
        return sum(1 for ln in out.splitlines() if ln.lower().startswith('"blender.exe"'))
    except Exception:
        return 0


# ---------- quiet window ----------
def parse_quiet(s):
    m = re.fullmatch(r"\s*(\d\d):(\d\d)\s*-\s*(\d\d):(\d\d)\s*", s or "")
    if not m:
        return None
    a, b, c, d = map(int, m.groups())
    if a > 23 or c > 23 or b > 59 or d > 59:
        return None
    return a * 60 + b, c * 60 + d


def in_quiet(s, ts=None):
    w = parse_quiet(s)
    if not w:
        return False
    t = datetime.datetime.fromtimestamp(ts or time.time())
    m = t.hour * 60 + t.minute
    a, b = w
    if a == b:
        return False
    return (a <= m < b) if a < b else (m >= a or m < b)


def quiet_end(s, ts):
    w = parse_quiet(s)
    t = datetime.datetime.fromtimestamp(ts)
    end = t.replace(hour=w[1] // 60, minute=w[1] % 60, second=0, microsecond=0)
    if end.timestamp() <= ts:
        end += datetime.timedelta(days=1)
    return end.timestamp()


# ---------- job helpers ----------
def log_path(j):
    p = j.get("log") or "_env/queue/logs/%s.log" % j["id"]
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


def new_job(d):
    jid = d["id"]
    kind = d.get("kind", "other")
    return {
        "id": jid, "title": d.get("title", jid), "kind": kind,
        "res": d.get("res") or ("gpu" if kind == "blender" else "cpu"),
        "cmd": d["cmd"], "after": list(d.get("after", [])), "est_min": d.get("est_min", 10),
        "status": d.get("status", "waiting"), "tries": 0, "started": None, "ended": None, "pid": None,
        "log": "_env/queue/logs/%s.log" % jid, "note": d.get("note", ""),
    }


def gpu_state(st=None):
    st = st or settings()
    if os.path.exists(GUARD_PAUSED):
        return "guard", "显卡被导演总开关暂停（GPU_PAUSED）"
    if flag_on("GPU_HOLD"):
        return "hold", "显卡已在排期里暂停（GPU_HOLD）"
    if in_quiet(st.get("gpu_quiet")):
        return "quiet", "处于静音时段 %s，不再开新的显卡任务" % st["gpu_quiet"]
    return "free", "显卡空闲可用"


# ---------- 11-24 资源放行（内存 / 显存 / NVENC） ----------
class _MEMSTAT(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


def free_mem_gb():
    m = _MEMSTAT()
    m.dwLength = ctypes.sizeof(_MEMSTAT)
    try:
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        return m.ullAvailPhys / 1024 ** 3
    except Exception:
        return 99.0


def gpu_now():
    """(显存已用 MB, NVENC 会话数)；nvidia-smi 不在就返回 (0, 0)，不挡任务。"""
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,encoder.stats.sessionCount", "--format=csv,noheader,nounits"],
                             capture_output=True, timeout=10, creationflags=NOWIN).stdout.decode("ascii", "ignore").strip().splitlines()[0]
        a, b = [x.strip() for x in out.split(",")]
        return float(a), int(b)
    except Exception:
        return 0.0, 0


class Slots:
    """一次 tick 里的放行账本：开头量一次内存、显存、NVENC，之后每放行一个就预扣。"""

    def __init__(self, running):
        self.running = list(running)
        self.mem = free_mem_gb()
        now = time.time()
        for r in self.running:                                  # 刚起的任务内存还没涨上来，按满额预扣
            st = parse_t(r.get("started")) or now
            if r["res"] != "gpu" and now - st < RAMP_S:
                self.mem -= MEM_NEED_GB.get(r["kind"], MEM_NEED_DEFAULT)
        self.vram, smi_enc = gpu_now()
        self.enc = max(smi_enc, sum(1 for r in self.running if r["kind"] in NVENC_KINDS))

    def why_not(self, j):
        k = j["kind"]
        if OLD_SLOTS:
            if k in HEAVY_CPU and any(r["res"] == "cpu" and r["kind"] in HEAVY_CPU for r in self.running):
                return "旧规矩：CPU 重活一次一个"
            return None
        if k in KIND_MAX and sum(1 for r in self.running if r["kind"] == k) >= KIND_MAX[k]:
            return "同类已满 %d 个" % KIND_MAX[k]
        need = MEM_NEED_GB.get(k, MEM_NEED_DEFAULT)
        if self.mem - need < MEM_RESERVE_GB:
            return "空闲内存 %.1f GB 不够（要 %.1f + 留 %.1f）" % (self.mem, need, MEM_RESERVE_GB)
        if k in NVENC_KINDS and self.enc + 1 > NVENC_MAX:
            return "NVENC 会话已 %d 路" % self.enc
        if self.vram and self.vram + VRAM_NEED_MB.get(k, 0) > VRAM_BUDGET_MB:
            return "显存已用 %.0f MB" % self.vram
        return None

    def take(self, j):
        k = j["kind"]
        self.running.append(j)
        self.mem -= MEM_NEED_GB.get(k, MEM_NEED_DEFAULT)
        self.vram += VRAM_NEED_MB.get(k, 0)
        if k in NVENC_KINDS:
            self.enc += 1


def sim_blocked(j, running):
    """排期估算用（不量内存）：只按种类上限，和 runner 一致。"""
    k = j["kind"]
    if OLD_SLOTS:
        return k in HEAVY_CPU and any(r["res"] == "cpu" and r["kind"] in HEAVY_CPU for r in running)
    return k in KIND_MAX and sum(1 for r in running if r["kind"] == k) >= KIND_MAX[k]


# ---------- ETA simulation ----------
def simulate(q, st, now=None):
    now = now or time.time()
    jobs = q["jobs"]
    est = lambda j: max(float(j.get("est_min") or 1), 0.1) * 60
    end, running, out = {}, [], {}
    for j in jobs:
        if j["status"] == "done":
            end[j["id"]] = 0
        elif j["status"] == "running":
            s = parse_t(j.get("started")) or now
            e = max(s + est(j), now + 30)
            end[j["id"]] = e
            running.append((e, j))
    pending = [j for j in jobs if j["status"] == "waiting"]
    t = now
    quiet = st.get("gpu_quiet", "")
    for _ in range(2000):
        running = [(e, j) for e, j in running if e > t]
        started = True
        while started and pending:
            started = False
            for j in list(pending):
                if not all(d in end and end[d] <= t for d in j.get("after", [])):
                    continue
                if j["res"] == "gpu":
                    if in_quiet(quiet, t) or sum(1 for _, r in running if r["res"] == "gpu") >= MAX_GPU:
                        continue
                elif sim_blocked(j, [r for _, r in running]):
                    continue
                out[j["id"]] = (t, t + est(j))
                end[j["id"]] = t + est(j)
                running.append((t + est(j), j))
                pending.remove(j)
                started = True
        if not pending:
            break
        cands = [e for e, _ in running if e > t]
        if quiet and parse_quiet(quiet) and in_quiet(quiet, t):
            cands.append(quiet_end(quiet, t))
        if not cands:
            break
        t = min(cands)
    return out


# ---------- actions shared by qctl and panel ----------
def act(name, jid=None, value=None):
    """Returns (ok, message). All writes go through the lock."""
    if name in ("pause_all", "resume_all"):
        flag_set("PAUSED_ALL", name == "pause_all")
        log_event("-", "-", name)
        return True, "ok"
    if name in ("gpu_hold", "gpu_release"):
        flag_set("GPU_HOLD", name == "gpu_hold")
        log_event("-", "-", name)
        return True, "ok"
    if name == "quiet":
        v = (value or "").strip()
        if v and not parse_quiet(v):
            return False, "格式应为 23:00-08:00"
        with locked():
            s = _read_json(SETFILE, {})
            s["gpu_quiet"] = v
            _write_json(SETFILE, s)
        log_event("-", "-", "quiet=" + v)
        return True, "ok"
    with txn() as q:
        jobs = q["jobs"]
        idx = next((i for i, j in enumerate(jobs) if j["id"] == jid), None)
        if idx is None:
            return False, "没有这个任务 " + str(jid)
        j = jobs[idx]
        old = j["status"]
        if name == "top":
            jobs.insert(0, jobs.pop(idx))
        elif name == "up" and idx > 0:
            jobs[idx - 1], jobs[idx] = jobs[idx], jobs[idx - 1]
        elif name == "down" and idx < len(jobs) - 1:
            jobs[idx + 1], jobs[idx] = jobs[idx], jobs[idx + 1]
        elif name in ("up", "down"):
            pass
        elif name == "hold":
            if old == "running":
                return False, "正在运行，请用停止"
            j["status"] = "held"
        elif name == "release":
            if old != "held":
                return False, "只有暂停中的任务能放行"
            j["status"] = "waiting"
        elif name == "retry":
            if old == "running":
                return False, "正在运行，先停止"
            j["status"], j["tries"], j["pid"] = "waiting", 0, None
        elif name in ("stop", "cancel"):
            if old == "running" and j.get("pid"):
                kill_tree(j["pid"])
            j["status"], j["pid"] = "held", None
            if old == "running":
                j["ended"] = now_s()
        else:
            return False, "未知操作 " + name
        if j["status"] != old:
            log_event(jid, old, j["status"], "(%s)" % name)
    return True, "ok"
