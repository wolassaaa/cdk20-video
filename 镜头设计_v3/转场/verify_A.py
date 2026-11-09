"""HKBU SCIE1007 课程作业的科普视频：方案 A 转场成片的验收（只读，不改任何片子）。

对 A_<接头名>_4k60.mp4 做：ffprobe（尺寸、帧率、帧数、音轨）；首帧、尾帧各和原片同一时刻的帧用 check_4k.py --ref 比；
相纸展开时新盖住的那一块在原片里是不是空的（不压图）；出一张联系表。
用法（先 source ../hyperframes/hfenv.sh）：python verify_A.py <接头名>
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_hf_A as M  # noqa: E402

HERE = M.HERE
INS = M.INS
CHECK = M.INS / "check_4k.py"
RT = HERE.parent.parent / "_render_tmp/hf"
BOT = np.array([0xEC, 0xEA, 0xE4], np.float32)


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf8", errors="replace")


def grab(path, t, out):
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t - 0.004:.4f}", "-i", str(path), "-frames:v", "1", str(out)])
    return Image.open(out).convert("RGB")


def grab_n(path, n, out):
    run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-vf", f"select=eq(n\,{n})", "-frames:v", "1", str(out)])
    return Image.open(out).convert("RGB")


def orig_frame(J, F, out):
    # by frame number, as the cut in make_hf_A.py does (S3_all_2 has slightly off timestamps, so seconds are not safe there)
    # which source file holds film time F
    if len(J["src"]) == 1:
        f, a, b = J["src"][0]
        return grab_n(INS / f, round((a + (F - J["T0"])) * 60), out)
    t = F - J["T0"]
    for f, a, b in J["src"]:
        if t < b - a - 1e-6:
            return grab_n(INS / f, round((a + t) * 60), out)
        t -= b - a
    raise ValueError


def main(name):
    J = M.JOINTS[name]
    clip = HERE / f"A_{name}_4k60.mp4"
    work = RT / f"verify_{name}"
    work.mkdir(parents=True, exist_ok=True)
    print(f"== {name}  {clip.name}")
    pr = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-count_packets", "-of", "json", str(clip)]).stdout)["streams"]
    v = [s for s in pr if s["codec_type"] == "video"][0]
    dur = round(J["T1"] - J["T0"], 3)
    want = round(dur * 60)
    audio = [s for s in pr if s["codec_type"] == "audio"]
    print(f"1. ffprobe: {v['width']}x{v['height']} {v['r_frame_rate']} frames {v.get('nb_read_packets') or v.get('nb_frames')} (want {want}) audio {len(audio)} "
          f"{v.get('color_space')}  ->", "PASS" if (v["width"], v["height"], v["r_frame_rate"]) == (3840, 2160, "60/1") and str(want) in (v.get("nb_read_packets"), v.get("nb_frames")) and not audio else "FAIL")
    n = int(v.get("nb_read_packets") or v.get("nb_frames"))
    first = grab(clip, 0.0, work / "first.png")
    last = grab(clip, (n - 1) / 60, work / "last.png")
    o0 = orig_frame(J, J["T0"], work / "orig_first.png")
    o1 = orig_frame(J, J["T1"] - 1 / 60, work / "orig_last.png")
    for tag, ref in (("first", "orig_first"), ("last", "orig_last")):
        r = run([sys.executable, str(CHECK), str(work / f"{tag}.png"), "--ref", str(work / f"{ref}.png")])
        print(f"2. {tag} vs original:", " | ".join(l.strip() for l in r.stdout.splitlines() if l.strip())[:400])
    r = run([sys.executable, str(CHECK), str(clip)])
    print("2b. check_4k on the clip:\n" + "\n".join("   " + l for l in r.stdout.splitlines()[:30]))

    # 3. the part of the film the opened print newly covers must be empty paper
    film = HERE / f"hf_A_{name}/assets/film.mp4"
    worst = []
    for si, s in enumerate(J["segs"]):
        if not s["push"] or s["push"] is None:
            continue
        ranges = [(s["push"][0], s["full"][0])] + ([(s["pull"][0], s["pull"][1])] if s["pull"] else [])
        for (a, b) in ranges:
            F = a
            while F <= b + 1e-9:
                c = M.cam_s1(F) if J["cam"] is M.cam_s1 else J["cam"](F)
                k = 2 * c[2]
                PW, PH = s["w"] * 2, s["h"] * 2
                cx = 1920 + k * (s["x"] + s["w"] / 2 - c[0])
                cy = 1080 + k * (s["y"] + s["h"] / 2 - c[1])
                WIDE = (PH - 80) * 16 / 9 + 80
                d = s["push"] if (a == s["push"][0]) else s["pull"]
                dd = d[1] - d[0]
                # opening fraction as in the page
                if a == s["push"][0]:
                    w = M.smooth((F - d[0] - 0.12 * dd) / (0.76 * dd))
                else:
                    w = 1 - M.smooth((F - (d[0] + 0.098 * dd)) / (0.784 * dd))
                pw = PW + (WIDE - PW) * w
                x0, x1 = (cx + PW / 2 - pw, cx - PW / 2) if s["dir"] < 0 else (cx + PW / 2, cx - PW / 2 + pw)
                if x1 - x0 > 4:
                    img = grab(film, F - J["T0"], work / "f.png").resize((960, 540))
                    arr = np.asarray(img, np.float32)
                    xa, xb = max(0, int(x0 / 4)), min(960, int(x1 / 4))
                    ya, yb = max(0, int((cy - PH / 2) / 4)), min(540, int((cy + PH / 2) / 4))
                    if xb > xa and yb > ya:
                        reg = arr[ya:yb, xa:xb]
                        share = float((np.abs(reg - BOT).max(axis=2) > 26).mean())
                        worst.append((share, F, si))
                F += 0.05
    if worst:
        worst.sort(reverse=True)
        print("3. newly covered strip, share of non-paper pixels in the original: worst %.4f at F=%.2f (seg %d); over 0.5%% at %d of %d samples ->" % (
            worst[0][0], worst[0][1], worst[0][2], sum(1 for w in worst if w[0] > 0.005), len(worst)), "PASS" if worst[0][0] < 0.005 else "LOOK")
    else:
        print("3. no opening strip to check")

    # contact sheet: push, open, full, pull, close
    times = []
    for s in J["segs"]:
        if s["push"]:
            times += [s["push"][0] - 0.2, (s["push"][0] + s["push"][1]) / 2, s["full"][0] + 0.2]
        if s["pull"]:
            times += [s["pull"][0] + 0.1, (s["pull"][0] + s["pull"][1]) / 2, s["pull"][1] + 0.3]
    times = sorted(set(round(t, 3) for t in times if J["T0"] < t < J["T1"]))[:12]
    cols = 4
    rows = (len(times) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 640, rows * 360), "white")
    for i, F in enumerate(times):
        im = grab(clip, F - J["T0"], work / "c.png").resize((640, 360))
        ImageDraw.Draw(im).text((8, 8), f"F={F:.2f}", fill=(220, 0, 0))
        sheet.paste(im, ((i % cols) * 640, (i // cols) * 360))
    sheet.save(HERE / f"A_{name}_4k60_过程.png")
    print("sheet:", HERE / f"A_{name}_4k60_过程.png")


if __name__ == "__main__":
    main(sys.argv[1])
