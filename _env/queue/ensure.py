# -*- coding: utf-8 -*-
"""HKBU SCIE1007 coursework video: start runner / panel if they are not alive. Run by Task Scheduler and start_queue.bat."""
import os, sys, socket, subprocess, time, webbrowser
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qlib as L

PYW = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
PY = PYW if os.path.exists(PYW) else sys.executable


def spawn(script, logname):
    lf = open(os.path.join(L.LOGS, logname), "ab")
    subprocess.Popen([PY, "-X", "utf8", os.path.join(L.Q, script)], cwd=L.Q, stdin=subprocess.DEVNULL,
                     stdout=lf, stderr=subprocess.STDOUT, creationflags=0x08000000 | 0x00000200 | 0x00000008)


def panel_alive():
    try:
        socket.create_connection(("127.0.0.1", 8770), timeout=1).close()
        return True
    except OSError:
        return False


def runner_alive():
    try:
        pid = int(open(os.path.join(L.Q, "runner.pid")).read().strip())
        return L.pid_alive(pid) and time.time() - os.path.getmtime(os.path.join(L.Q, "heartbeat.txt")) < 60
    except Exception:
        return False


def main():
    os.makedirs(L.LOGS, exist_ok=True)
    if not runner_alive():
        spawn("runner.py", "runner.log")
    if not panel_alive():
        spawn("panel.py", "panel.log")
    if "--open" in sys.argv:
        for _ in range(20):
            if panel_alive():
                break
            time.sleep(0.5)
        webbrowser.open("http://127.0.0.1:8770")


if __name__ == "__main__":
    main()
