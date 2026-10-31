"""HKBU SCIE1007 coursework science video. Eclipse direction: logs peak python memory and lowest free RAM during a render, until the given flag file exists."""
import ctypes
import subprocess
import sys
import time
from pathlib import Path


class M(ctypes.Structure):
    _fields_ = [("l", ctypes.c_ulong), ("load", ctypes.c_ulong), ("tot", ctypes.c_ulonglong), ("free", ctypes.c_ulonglong), ("a", ctypes.c_ulonglong), ("b", ctypes.c_ulonglong),
                ("c", ctypes.c_ulonglong), ("d", ctypes.c_ulonglong), ("e", ctypes.c_ulonglong)]


flag = Path(sys.argv[1])
peak, low = 0, 1e9
while not flag.exists():
    o = subprocess.run(["tasklist", "/fi", "imagename eq python.exe", "/fo", "csv", "/nh"], capture_output=True, text=True).stdout
    tot = sum(int(l.split('","')[4].replace(",", "").replace('"', "").replace(" K", "").strip()) for l in o.strip().splitlines() if "python" in l) / 1e6
    m = M()
    m.l = ctypes.sizeof(M)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    peak, low = max(peak, tot), min(low, m.free / 2 ** 30)
    time.sleep(2)
print("peak python working set GB", round(peak, 2), "lowest free RAM GB", round(low, 2))
