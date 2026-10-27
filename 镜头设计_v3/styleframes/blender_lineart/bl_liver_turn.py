"""Frame 4 - 4 s / 24 fps test: the liver (with its vessels) turning slowly, animated on twos with line boil.

Run (from this folder):
  blender -b --factory-startup --python bl_liver_turn.py -- bl_liver_turn.mp4 [--frames DIR] [--preview]

  * Everything that moves changes only every 2nd frame ("on twos"): the turn is stepped, the GP Noise / Length
    modifiers re-seed with step=2, and the python hatching is rebuilt for every new pose with a new random seed,
    so hatch ends and pen breaks boil like a redrawn cel.
  * Only 48 unique drawings are rendered; each is composited twice with a different film-grain seed (grain on
    ones, drawing on twos), written as a PNG sequence, then encoded with ffmpeg (H.264, yuv420p, crf 16).
"""
import bpy, sys, os, time, math, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ink_common import *
import bl_liver_ink as L

FFMPEG = r"D:\。hkbu\molecular science\视觉音乐测试_5分钟_20261018\_deps\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
FPS, SECONDS, ON = 24, 4, 2
TURN = (-15.0, 20.0)          # degrees about the body's vertical axis, linear (the hand-made feel comes from the twos)

if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:]
    OUT = os.path.abspath(argv[0])
    FR = os.path.abspath(argv[argv.index("--frames") + 1]) if "--frames" in argv else os.path.join(L.HERE, "_frames_turn")
    os.makedirs(FR, exist_ok=True)
    preview = "--preview" in argv
    t0 = time.time()
    S = L.build(preview=preview, turn=math.radians(TURN[0]))
    L.add_labels(S, leader=False)
    sc = S["sc"]
    n = 6 if "--test" in argv else FPS * SECONDS
    sc.frame_start, sc.frame_end = 1, n
    sc.render.fps = FPS
    tmp = os.path.join(FR, "_passes")
    times = []
    for i in range(0, n, ON):
        ts = time.time()
        f = 1 + i
        u = i / max(n - ON, 1)
        S["pivot"].rotation_euler.z = math.radians(TURN[0] + (TURN[1] - TURN[0]) * u)
        bpy.context.view_layer.update()
        L.shade_vgroup(S["liver"], L.LIGHT)
        L.make_hatch(S, f, seed=3)
        sc.frame_set(f)
        p = L.render_passes(S, tmp, "t")
        for j in range(ON):
            L.composite(p, os.path.join(FR, f"f_{f + j:04d}.png"), seed=f + j)
        times.append(time.time() - ts)
        print(f"step {i // ON + 1}/{n // ON} frame {f} {times[-1]:.1f}s", flush=True)
    t1 = time.time()
    cmd = [FFMPEG, "-y", "-framerate", str(FPS), "-i", os.path.join(FR, "f_%04d.png"), "-c:v", "libx264",
           "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "slow", "-movflags", "+faststart", OUT]
    subprocess.run(cmd, check=True)
    print(f"TIMING build+render {t1 - t0:.1f}s (per drawing {sum(times) / len(times):.1f}s) "
          f"encode {time.time() - t1:.1f}s total {time.time() - t0:.1f}s")
