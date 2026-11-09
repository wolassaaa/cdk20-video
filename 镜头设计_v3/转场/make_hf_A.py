"""HKBU SCIE1007 课程作业的科普视频：方案 A（推进相纸）铺开用的生成脚本。

照样板 hf_A_102_104/index.html 的做法、缓动、时长：相纸照 entry.jsx 的 Print 落下，镜头推进，相纸往背离图的一侧展开成 16:9，
整屏出镜（灰色剪影占位片），拉回、合上，再跟着原片的镜头横移滑出。每处一个工程，只放用到的片段。

用法（在 镜头设计_v3/转场 下，先 source ../hyperframes/hfenv.sh）：
  python make_hf_A.py <接头名> [--no-cut]     生成 hf_A_<接头名>/（index.html、assets/film.mp4、standin_A.mp4、vendor/）
接头名见下面的 JOINTS。样板工程、Print、entry.jsx 都不动。
"""
import argparse
import json
import math
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = HERE.parent
INS = P / "styleframes/art/fusion/s1/inserts"
TL = json.load(open(P.parent / "镜头设计_v2/tests/T4_remotion/src/v3/fusion/s1_timeline.json"))["cam"]
STANDIN = HERE / "hf_A_102_104/assets/standin_A.mp4"
GSAP = HERE / "hf_A_102_104/vendor/gsap.min.js"

clamp = lambda x: min(1.0, max(0.0, x))
smooth = lambda x: (lambda x: x * x * x * (x * (6 * x - 15) + 10))(clamp(x))


def cam_s1(F):
    return TL[min(round(F * 60), len(TL) - 1)]


def cam_s3(slide_at, slide_len, dist):
    """S3 prints are screen-space in the take and slide left by -dist*smooth((t-at)/len); as a camera that is cx = 960 + dist*smooth."""
    return lambda F: [960 + dist * smooth((F - slide_at) / slide_len), 540, 1.0]


def cam_s3_3_01(F):
    return [960 + 752 * smooth(F - 287), 540, 1.0] if F >= 283 else [960, 540, 1.0]


# a segment: world rect of the print (1080 units, as in entry.jsx), drop time, open direction (-1 = away to the left),
# push/open/pull/close/full spans in film seconds (None = not present), when its overlay stops being drawn
def seg(who, x, y, w, h, rot, drop, *, dir=-1, push=None, full=None, pull=None, hide=None):
    return dict(who=who, x=x, y=y, w=w, h=h, rot=rot, drop=drop, dir=dir, push=push, full=full, pull=pull, hide=hide)


JOINTS = {
    # W0 -> 1-01 -> 1-02: A's print lands while the camera is still settling from its opening zoom
    "W0_102": dict(
        T0=1.0, T1=8.9, cam=cam_s1, src=[("S1S2_table_2.mp4", 1.0, 8.9)], standin=8.0,
        segs=[seg("A", 96, 84, 760, 912, -1.2, 2.15, push=(2.80, 4.05), pull=(6.63, 7.65), full=(4.05, 6.63))]),
    # 2-01 -> 2-02 -> 2-03 -> 2-04 -> 2-05: A's print stays through 2-03 and slides out as C's lands
    "201_205": dict(
        T0=173.5, T1=194.5, cam=cam_s1, src=[("S1S2_table_2.mp4", 173.5, 194.5)], standin=22.5,
        segs=[seg("A", 15456, 1164, 760, 912, -0.9, 174.9, push=(175.55, 176.80), pull=(182.98, 184.0), full=(176.80, 182.98)),
              seg("C", 17376, 1248, 620, 744, -0.9, 190.05, push=(190.80, 191.40), pull=(192.40, 193.0), full=(191.40, 192.40))]),
    # 3-05 -> 3-06 -> 3-07: flat print over the oblique take, as in the film; it slides off at 358.6
    "305_307": dict(
        T0=351.0, T1=360.3, cam=cam_s3(358.6, 2.0, 2200), src=[("S3_all_2.mp4", 351.0 - 283, 360.3 - 283)], standin=8.0,
        segs=[seg("D", 72, 168, 620, 744, -1.0, 352.0, push=(352.65, 353.90), pull=(357.58, 358.6), full=(353.90, 357.58))]),
    # 1-04 -> 1-05 D, 1-06 B, 1-07 C -> 1-08: push into D, cut between the three (swap of speakers), pull out of C
    "104_108": dict(
        T0=51.0, T1=62.0, cam=cam_s1, src=[("S1S2_table_2.mp4", 51.0, 62.0)], standin=8.0,
        segs=[seg("D", 5840, 170, 500, 600, -1.5, 52.05, dir=-1, push=(52.70, 53.30), full=(53.30, 55.0), hide=55.0),
              seg("B", 6430, 170, 500, 600, 1.0, 55.0, full=(55.0, 58.0), hide=55.0),
              seg("C", 7020, 170, 500, 600, -0.8, 58.0, dir=1, full=(58.0, 59.0), pull=(59.0, 60.0))]),
    # 2-08 gap -> 3-01 -> 3-02: two source files, S1S2 gap then the S3 take
    "208_302": dict(
        T0=281.5, T1=288.2, cam=cam_s3_3_01, src=[("S1S2_table_2.mp4", 281.5, 283.0), ("S3_all_2.mp4", 0.0, 5.2)], standin=8.0,
        segs=[seg("D", 72, 168, 620, 744, -1.0, 283.1, push=(283.75, 284.35), full=(284.35, 286.40), pull=(286.40, 287.0))]),
}

TEMPLATE = (HERE / "hf_A_template.html").read_text(encoding="utf8") if (HERE / "hf_A_template.html").exists() else None


def build(name, J, cut=True):
    out = HERE / f"hf_A_{name}"
    (out / "assets").mkdir(parents=True, exist_ok=True)
    (out / "vendor").mkdir(exist_ok=True)
    shutil.copy(GSAP, out / "vendor/gsap.min.js")
    if not (out / "assets/standin_A.mp4").exists():
        copies = max(1, math.ceil((J["standin"] - 0.5) / 7.5))       # 8 s stand-in; longer ones are the same clip cross-faded end to start (0.5 s)
        if copies == 1:
            shutil.copy(STANDIN, out / "assets/standin_A.mp4")
        else:
            ins = sum((["-i", str(STANDIN)] for _ in range(copies)), [])
            fc, last = "", "[0:v]"
            for i in range(1, copies):
                fc += f"{last}[{i}:v]xfade=transition=fade:duration=0.5:offset={7.5 * i}[x{i}];"
                last = f"[x{i}]"
            subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc.rstrip(";"), "-map", last, "-r", "60", "-c:v", "libx264", "-crf", "14",
                            "-preset", "medium", "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                            "-an", str(out / "assets/standin_A.mp4")], check=True)
    T0, T1 = J["T0"], J["T1"]
    dur = round(T1 - T0, 3)
    assert abs(T0 * 60 - round(T0 * 60)) < 1e-6 and abs(dur * 60 - round(dur * 60)) < 1e-6
    if cut and not (out / "assets/film.mp4").exists():
        src = J["src"]
        ins, parts = [], []
        for i, (f, a, b) in enumerate(src):
            ins += ["-i", str(INS / f)]
            parts.append(f"[{i}:v]trim=start_frame={round(a * 60)}:end_frame={round(b * 60)},setpts=PTS-STARTPTS[v{i}]")
        fc = ";".join(parts) + (";" + "".join(f"[v{i}]" for i in range(len(src))) + f"concat=n={len(src)}:v=1:a=0[o]" if len(src) > 1 else "")
        last = "[o]" if len(src) > 1 else "[v0]"
        cmd = ["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc, "-map", last, "-r", "60", "-c:v", "libx264", "-crf", "12",
               "-preset", "medium", "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
               "-color_range", "tv", "-an", str(out / "assets/film.mp4")]
        subprocess.run(cmd, check=True)
    f0 = round(T0 * 60)
    n = round(dur * 60) + 1
    camarr = [[round(v, 3) for v in J["cam"](T0 + i / 60)] for i in range(n)]
    for s in J["segs"]:                                          # open geometry assumes zoom 1 while the print is open / pushed
        for key in ("push", "full", "pull"):
            if s[key]:
                a, b = s[key]
                assert all(abs(camarr[round((F - T0) * 60)][2] - 1) < 1e-3 for F in (a, b)), (name, s["who"], key, "zoom not 1")
    html = []
    vids = []                                                    # <video> elements, one per segment: window in the print, full screen
    track = 1
    for i, s in enumerate(J["segs"]):
        show = bool(s["push"] or s["pull"])
        sstart = s["drop"] - 0.55 if show else s["full"][0] - 0.55
        s["sstart"] = round(sstart, 3)
        s["show"] = show
        if show:
            html.append(f'          <video id="win{i}" class="clip" data-start="{round(sstart - T0, 3)}" data-duration="{min(J["standin"], round(T1 - sstart, 3))}" '
                        f'data-media-start="0" data-track-index="{track}" src="assets/standin_A.mp4" muted playsinline></video>')
            track += 1
        fa, fb = s["full"]
        vids.append(f'        <video id="full{i}" class="clip" data-start="{round(fa - T0, 3)}" data-duration="{round(fb - fa + 0.05, 3)}" '
                    f'data-media-start="{round(fa - sstart, 3)}" data-track-index="{track}" src="assets/standin_A.mp4" muted playsinline></video>')
        track += 1
        assert fb - sstart + 0.05 <= J["standin"] + 1e-6, (name, i, "stand-in too short")
    prints, fulls = [], []
    for i, s in enumerate(J["segs"]):
        if s["show"]:
            win = [h for h in html if f'id="win{i}"' in h][0]
            prints.append(f'        <div id="shade{i}" class="shade"></div>\n        <div id="print{i}" class="print">\n          <div class="paper"></div>\n'
                          f'          <div id="window{i}" class="window">\n{win}\n          </div>\n        </div>')
        fulls.append(f'      <div id="fullwrap{i}" class="fullwrap">\n{vids[i]}\n      </div>')
    cfg = dict(T0=T0, DUR=dur, F0=f0, CAM=camarr, SEGS=J["segs"])
    page = TEMPLATE.replace("@@DUR@@", str(dur)).replace("@@PRINTS@@", "\n".join(prints)).replace("@@FULLS@@", "\n".join(fulls)) \
        .replace("@@NAME@@", name).replace("@@CFG@@", json.dumps(cfg, separators=(",", ":")))
    (out / "index.html").write_text(page, encoding="utf8")
    print(name, "->", out, f"{dur}s", f"{round(dur * 60)} frames")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--no-cut", action="store_true")
    a = ap.parse_args()
    assert TEMPLATE, "hf_A_template.html missing"
    build(a.name, JOINTS[a.name], cut=not a.no_cut)
