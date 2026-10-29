"""Run one or more .jsx files in the open After Effects and wait until they finish.

usage: python run_in_ae.py oncam_card.jsx [render_demo.jsx ...]

AfterFX.exe -r can't open a script whose path contains Chinese characters (it fails silently),
so this writes a launcher with an ASCII-only path to %TEMP% and $.evalFile()s each target
by a \\u-escaped path. Results go to %TEMP%/ae_runner.txt. AE must already be open (cold-start + -r does nothing).
"""
import os, subprocess, sys, tempfile, time

AE = r"D:\software\Adobe After Effects 2026\Support Files\AfterFX.exe"
tmp = tempfile.gettempdir()
log = os.path.join(tmp, "ae_runner.txt").replace("\\", "/")
esc = lambda s: "".join(c if ord(c) < 128 else "\\u%04X" % ord(c) for c in s)

targets = [os.path.abspath(p).replace("\\", "/") for p in sys.argv[1:]]
js = [f'var __L=new File("{esc(log)}"); __L.open("w");']
for n, t in enumerate(targets):
    # scripts share the global scope, so the launcher avoids loop variables a target could overwrite
    js.append(f'try {{ $.evalFile(new File("{esc(t)}")); __L.writeln("ok {n}"); }} catch(e) {{ __L.writeln("ERR {n} line "+e.line+": "+e); }}')
js.append('__L.writeln("END"); __L.close();')
launcher = os.path.join(tmp, "ae_launcher.jsx")
open(launcher, "w", encoding="ascii").write("\n".join(js))

if os.path.exists(log):
    os.remove(log)
subprocess.Popen([AE, "-r", launcher])
for _ in range(600):
    if os.path.exists(log) and "END" in open(log, encoding="utf-8", errors="replace").read():
        break
    time.sleep(1)
else:
    sys.exit("AE did not finish in 10 min (a dialog may be blocking it)")
print(open(log, encoding="utf-8", errors="replace").read().strip())
