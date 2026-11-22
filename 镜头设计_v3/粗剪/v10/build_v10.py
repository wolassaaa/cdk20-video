"""HKBU SCIE1007 课程作业的科普视频：v10 整片拼片器（1080p60）。只拼接、合声音、出清单和机检，不改任何一段的画面；v10 不烧字幕。

依据：17_收尾排班.md 第五节 T2；19 的 2.5（清单字段）、4.7（彩蛋）、第六节（接点代号）、7.1（全片机检门槛）、7.3（时长门槛）；
     17 的 1.3（每段用哪个文件、退路）；18 的 2.6、4.3（W2、W3 用哪个文件；不加 ROUGH CUT 角标）；
     导演检查_20261120/09_片头_时间线.json 和 inserts/assemble_w0w1.py（W0、W1 怎么接）。

做法：
  - 段序读 映射/master_v2.json（没有就 master_v1）的 groups，最后接片尾彩蛋（group EGG，19 的 4.7；文件不在就不接，清单里写明）。
  - 每段的候选文件读 sources_v10.json（按先后排：导演检查_20261123 → 21 → 20 → 18 → 17 的 1.3 表里的退路），
    取存在、读得出帧数、20 秒内没被改过、而且不在 blocklist.txt 里的第一个。blocklist.txt 一行一个文件名（或相对项目根的路径），# 起头是注释。
  - 段长 = 成片自己的帧数（30 fps 的源按时长换算到 60 fps，复帧，不拉伸；不冻末帧）。W2 取前 1500 帧；W3 用 lanczos 缩到 1080p 取前 900 帧。
  - W0：G:/cdk20/work/w1/w0_final 前 168 帧；它的擦除层 w0wipe_final 第 168–183 帧叠在 1-01 头 16 帧上（同 assemble_w0w1.py）。
    W1：w1z_final 共 1250 帧 = 尾 120 + W1 1010 + 头 120；尾 120 帧盖在 1-11 最后 120 帧的画面上、头 120 帧盖在 2-01 头 120 帧的画面上，
    两处切换各一道 14 帧 T6 光扫（同 assemble_w0w1.py 的 sweep）；1-11、2-01 的段长和声音不变。
    W0、W1 的声音从 导演检查_20261120/09_片头W0_大标题W1.mp4 里按 09_片头_时间线.json 截（同一首歌、同一套帧）。
  - 1-01：sources 里写了 trim_tail_black，段尾的黑帧（19 的 J02，约 0.5 秒）裁掉。
  - 每段转码一次存缓存 G:/cdk20/work/v10/pieces/（文件名含源路径、大小、修改时间的摘要；源没变就不重转）；不删任何文件。
    画面 h264_nvenc 1080p60 yuv420p bt709，声音 48 kHz 立体声 PCM，补静音或截到正好 = 帧数 ÷ 60。
    每段转码时顺便量黑帧（blackdetect d=0.05 pix_th=0.06）和冻帧（freezedetect −60 dB ≥ 0.5 s），结果和缓存放一起。
  - 画面 concat 直接拷贝，声音 wav 接起来（带 --mix <wav> 时改用外面给的整片混音，补齐或截到画面长度），合成 AAC 256k。
  - 接点叠层（11-23 审查批 1 rc02 第 ③ 条，位 3 加）：OVERLAY_ON 里的接点照 joints_v10.json 的 overlay 叠擦除层——
    assembly-left 叠左段最后 17 帧（擦除层入场半段 0–16）、assembly-right 叠右段头 17 帧（退场半段 17–33）、assembly 两边都叠；
    T2 的接点（J22）左段还是 v9 旧页时，最后 8 帧做甩镜（向左推出 2304 px、横向模糊到 40 px；新做的 3-03 钻取自带甩镜，不再加）。叠好的段单独缓存，声音不动。
    11-23 T2b（位 1）补全：ASM 表逐接点写死 19 的 6.3 全部"装配叠"（只叠自己不带擦除的那一侧；B 页那一侧页面已画），
    按两侧这一版实际用的片（v9 / 简版 / 新）选退路做法；四处章首 T6 光扫（SWEEP_ON：3-01、4-01、7-01、8-01 第 0–15 帧）。
    接点机检 K1–K7 在 粗剪/_check/check_joints_v10.py。

用法（在项目根目录；用 C:/Python314 的 python：_env/footage 的 python 和 _env/ffmpeg 没有写 G 盘的许可）：
  python -X utf8 镜头设计_v3/粗剪/v10/build_v10.py            滚动版 → G:/cdk20/work/v10/rc/v10_rcNN.mp4（NN 自动加 1）
  ... build_v10.py --rc 01                                                              指定版号
  ... build_v10.py --final                                                              → 导演检查_20261123/01_v10_整片.mp4 和 01_v10_清单.html
  ... build_v10.py --mix G:/cdk20/work/audio/v10/master_v10.wav                         用整片混音替换各段自带的声音
  ... build_v10.py --dry                                                                只选文件、写清单，不转码不拼
每次都写：粗剪/v10/manifest_v10.json、清单_v10.md/.html；导演检查_20261123/_机检_v10.md/.json。
"""
import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
V3 = ROOT / "镜头设计_v3"
FF = os.environ.get("CDK20_FF") or next(p for p in ("D:/software/tools/CipherTalk/resources/app.asar.unpacked/node_modules/ffmpeg-static/ffmpeg.exe",
                                                    str(ROOT / "_env/ffmpeg/ffmpeg.exe")) if Path(p).exists())   # 只有这一个 ffmpeg 有写 G 盘的许可（受控文件夹）
FP = str(ROOT / "_env/ffmpeg/ffprobe.exe")
WORK = Path(os.environ.get("CDK20_WORK", "G:/cdk20/work"))
PIECES = WORK / "v10/pieces"
RC = WORK / "v10/rc"
D23 = ROOT / "导演检查_20261123"
FPS = 60
W, H = 1920, 1080
SR = 48000
LIMIT_F = 71700                       # 19 的 7.3：≤ 19:55.0
MIN_F = 54000                         # ≥ 15:00
PIPE_VER = "v10.1"                    # 转码做法变了就改这个，缓存全部重转
NV = ["-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", "19", "-b:v", "0", "-pix_fmt", "yuv420p", "-r", str(FPS),
      "-g", "120", "-bf", "0", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
      "-video_track_timescale", "60000"]
VF = f"scale=1920:1080:flags=lanczos:out_range=tv,format=yuv420p,setsar=1"
WORKERS = 2                           # CPU、内存紧：同时最多转两段

# 19 的 6.3 接点代号（joints_v10.json 没有时用；Jk 是第 k 段左边的接点，J00 = 文件头）
# 19 的 6.3 接点表定稿（11-22 夜，第十节第 8 条改了 44 行：出镜段和 B 页之间用这一组自己的擦除层；J19、J60 零件冲镜直接接；J21、J29 是 T3；J38 用 key；J59 一镜到底）
JCODE = ["—", "T5", "T1+T5", "T5", "T1+T5", "T5", "T1+T5", "T5", "T5", "T5", "T6+one-take", "one-take+T6", "T5", "T5", "T5",
         "T1+T5", "T2", "T2", "T5", "T1+T6", "T1", "T3", "T2", "T5", "T5", "T1+T5", "T2", "T5", "T1+T5", "T3+T6", "T2", "T2",
         "T5", "T1+T5", "T2", "T5", "T1+T5", "T5", "T5", "T5", "T1+T5+T6", "T5", "T1+T5", "T5", "T5", "T1+T5", "T2", "T5", "T1",
         "T5", "T2+T6", "T2", "T2", "T5", "T1+T5", "T2", "T2", "T2", "T5", "one-take", "T1", "T1+T6", "T1+T5", "T2", "T2",
         "T5+T6", "T1+T5", "T2", "T5", "T1+T5", "black", "black"]
JWIPE = {  # 用 T5 的接点用哪块擦除层（G:/cdk20/work/bwipe/<名>；w0plate = G:/cdk20/work/w1/w0wipe_final）；oncam_<组> 目录不在就退 runner
    "J01": "w0plate", "J02": "oncam_1-01", "J03": "oncam_1-03", "J04": "oncam_1-03",
    "J05": "oncam_1-05_1-06_1-07", "J06": "oncam_1-05_1-06_1-07", "J07": "runner", "J08": "liver",
    "J09": "runner", "J12": "runner", "J13": "key", "J14": "oncam_2-04",
    "J15": "oncam_2-04", "J18": "runner", "J23": "socket", "J24": "oncam_3-06",
    "J25": "oncam_3-06", "J27": "oncam_3-09", "J28": "runner", "J32": "oncam_4-04_4-05",
    "J33": "oncam_4-04_4-05", "J35": "oncam_4-08", "J36": "oncam_4-08", "J37": "runner",
    "J38": "key", "J39": "oncam_4-11_4-12", "J40": "oncam_4-11_4-12", "J41": "oncam_5-02",
    "J42": "oncam_5-02", "J43": "socket_bore", "J44": "socket", "J45": "oncam_5-05_5-06",
    "J47": "oncam_5-09", "J49": "socket_bore", "J53": "oncam_6-04_6-05", "J54": "oncam_6-04_6-05",
    "J58": "runner", "J62": "oncam_7-01", "J65": "oncam_8-01", "J66": "oncam_8-01",
    "J68": "oncam_8-04_8-05_8-06_8-07", "J69": "w0plate",
    # 11-23 T2b（位 1）：JWIPE 记"成片里实际用的那块"。J37：4-09 页尾自带的是 runner（B409 T5Out runner），不是 19 写的 chip；
    # J23、J29、J43、J49：B 页 11-23 换了亮版 socket_bore（commit 2595e00）；J29 设计是 T3（4-01 第 0 帧对位 W2 末帧），
    # 4-01 页面还没改成 T3、段首仍是 socket_bore 退场半段，拼片先把同一块的入场半段补在 W2 尾上（见 ASM），T3 等页面重渲。
    "J23": "socket_bore", "J29": "socket_bore",
}
# 页面（B 档）里自己已经画了的半段：拼片不再叠，只补另一侧（11-23 从 btier/B*.jsx 的 T5In/T5Out 读出来的）
#   出镜段 ↔ B 页：B 页这一头现在画的是 runner（19 的 6.3：v10 照现状，11-24 重渲时再换 oncam_<组>），所以 B 页那一侧不叠。

# 19 的 6.3 "装配叠"：两边（或一边）不重渲，拼片时叠擦除层。每个接点 (左段尾叠入场半段, 右段头叠退场半段)，只列自己不带擦除的那一侧。
# 条件是一个函数 (左段 row, 右段 row) → (左, 右, 左段尾甩镜帧数, 说明)；不成立就返回 None。
def _st(r):
    return (r or {}).get("state") or ""


ASM = {
    "J02": lambda L, R: (None, "oncam_1-01", 0, "1-01 段尾零件冲镜，1-02（C）头 17 帧叠 oncam_1-01 退场半段"),
    "J03": lambda L, R: ("oncam_1-03", None, 0, "1-02（C）尾 17 帧叠 oncam_1-03 入场半段"),
    "J07": lambda L, R: (None, "runner", 0, "1-08 页尾自带 runner 入场半段，1-09（C）头 17 帧叠退场半段"),
    "J08": lambda L, R: ("liver", "liver", 0, "两边都是 C，装配叠 liver"),
    "J09": lambda L, R: ("runner", None, 0, "补全：1-11 页首自带 runner 退场半段，1-10（C）尾 17 帧补入场半段（19 写的是页面已写，只有半段就是硬切）"),
    "J12": lambda L, R: (None, "runner", 0, "补全：2-01 页尾自带 runner 入场半段，2-02（v9 出镜）头 17 帧补退场半段") if _st(R) == "v9" else
                        (None, "oncam_2-02", 0, "2-02 三维出镜：头上叠自己的 oncam_2-02 退场半段") if (WORK / "bwipe/oncam_2-02").exists() else None,
    "J13": lambda L, R: ("key", "key", 0, "2-02（v9）、2-03（C）都不重渲，装配叠 key") if _st(L) == "v9" else
                        (None, "oncam_2-02" if (WORK / "bwipe/oncam_2-02").exists() else "key", 0, "2-02 重做后：T1 加退场半段叠在 2-03 头"),
    "J14": lambda L, R: ("oncam_2-04", None, 0, "2-03（C）尾 17 帧叠 oncam_2-04 入场半段"),
    "J19": lambda L, R: ("runner", None, 0, "2-08 是简版长路页：尾 17 帧叠 runner 入场半段（19 的 6.3 简版做法）") if _st(L) == "简版" else None,
    "J20": lambda L, R: ("key", "key", 0, "3-02 还是 v9 页面：T5 key，装配叠（19 的 6.3 退路）") if _st(R) == "v9" else None,
    "J21": lambda L, R: (None, None, 8, "3-02 还是 v9 页面：T2，3-02 尾 8 帧甩镜（19 的 6.3 退路）") if _st(L) == "v9" else None,
    "J22": lambda L, R: (None, None, 8, "3-03 还是 v9 旧页：尾 8 帧甩镜（新钻取版自带）") if _st(L) == "v9" else None,
    "J28": lambda L, R: (None, "runner", 0, "3-09 段尾钻进磨砂壳；W2 第 0–16 帧叠 runner 第 17–33 帧（18 的 2.6）"),
    "J29": lambda L, R: ("socket_bore", None, 0, "T3 退路：4-01 页首还是 socket_bore 退场半段，W2 尾 17 帧补入场半段；4-01 改成 T3 后去掉"),
    "J37": lambda L, R: (None, "runner", 0, "补全：4-09 页尾自带 runner 入场半段，W3 头 17 帧补退场半段"),
    "J38": lambda L, R: ("key", None, 0, "补全：4-10 页首自带 key 退场半段，W3 尾 17 帧补入场半段"),
    "J49": lambda L, R: ("socket_bore", None, 0, "补全：5-10 页首自带 socket_bore 退场半段，W4 尾 17 帧补入场半段"),
    "J68": lambda L, R: (None, "runner", 0, "8-04–07 还不是三维出镜（没有 oncam 擦除层）：8-03 页尾自带 runner 入场半段，8-04–07 头 17 帧补退场半段") if _st(R) == "v9" else None,
    "J69": lambda L, R: ("w0plate" if _st(L) == "v9" else None, "w0plate", 0,
                         "W5 第 0–16 帧叠白料牌擦除层第 17–33 帧" + ("；8-04–07 不是三维出镜（段尾没有零件冲镜），尾 17 帧补白料牌入场半段" if _st(L) == "v9" else "")),
}
# 章首 T6 光扫（19 的 6.1）：拼片叠在右段第 0–15 帧。第 2、5、6 章做在画面里，不叠。
SWEEP_ON = {"J19": "3-01", "J29": "4-01", "J61": "7-01", "J65": "8-01"}

OVERLAY_ON = set(ASM) | set(SWEEP_ON)   # 11-23 位 3 先开了六处（J08、J13、J14、J22、J28、J69），T2b（位 1）补全到 6.3 全部装配叠和四处章首光扫


def wipe_halves(name):
    """擦除层 → (入场半段 17 张, 退场半段 17 张)，每张是 PNG 路径或 None（那一帧不叠）。
    bwipe/<名>/0000–0033.png：入场 0–16、退场 17–33。w0plate：同 J01，退场用 w0wipe_final 第 168–184 帧。
    bwipe/oncam_<组>/w_<帧>.png 是出镜段段首 16 帧和段尾 16 帧的零件层：入场 = 段首倒放（第 0 帧盖满对着接点），退场 = 段尾倒放。"""
    if name == "w0plate":
        d = WORK / "w1/w0wipe_final"      # wipe [150, 161, 183]：入场 151–167（W0 自己的尾巴），退场 168–184（同 J01）
        return [d / f"f_{151 + i:04d}.png" for i in range(17)], [d / f"f_{168 + i:04d}.png" for i in range(17)]
    d = WORK / "bwipe" / name
    if name.startswith("oncam_"):
        fs = sorted(int(p.stem[2:]) for p in d.glob("w_*.png"))
        nf = fs[-1] + 1
        cin = [None] + [d / f"w_{15 - k:04d}.png" for k in range(16)]          # 左段最后 17 帧：第 k 帧叠段首第 16−k 帧
        cout = [d / f"w_{nf - 1 - i:04d}.png" for i in range(16)] + [None]     # 右段头 17 帧：第 i 帧叠段尾第 nf−1−i 帧
        return cin, cout
    return [d / f"{i:04d}.png" for i in range(17)], [d / f"{17 + i:04d}.png" for i in range(17)]


def whip(img, t):
    """T2 甩镜一帧（t 0..1）：画面向左推出 2304·t² px，横向盒式模糊半径 4 → 40 px。"""
    np, _ = _np()
    dx = int(round(2304 * t * t)) % W
    a = np.roll(img[..., :3], -dx, axis=1).astype(np.float32)
    r = int(4 + 36 * t)
    c = np.cumsum(np.pad(a, ((0, 0), (r + 1, r), (0, 0)), mode="edge"), axis=1)
    return ((c[:, 2 * r + 1:] - c[:, :-2 * r - 1]) / (2 * r + 1)).clip(0, 255).astype(np.uint8)


_T6_CACHE = {}


def t6_sweep(img, k, n=16):
    """章首 T6 光扫（19 的 6.1，照 btier/bkit.jsx 的 T6Sweep）：240 px 宽、斜 20° 的白色渐变带，n 帧从左扫到右，
    峰值不透明度 0.55（颜色 255,250,240），screen 叠：out = base + a·c·(1 − base)。k = 0..n−1。"""
    np, _ = _np()
    p = k / max(1, n - 1)
    cx = -400 + p * (1920 + 800)
    if "g" not in _T6_CACHE:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        _T6_CACHE["g"] = (xx, yy)
    xx, yy = _T6_CACHE["g"]
    c, s = math.cos(math.radians(20)), math.sin(math.radians(20))
    d = (xx - cx) * c + (yy - H / 2) * s                       # 到光带中线的距离（沿带宽方向）
    a = (0.55 * np.clip(1 - np.abs(d) / 120.0, 0, 1))[..., None]
    col = np.array([255, 250, 240], np.float32)[None, None, :] / 255.0
    f = img[..., :3].astype(np.float32) / 255.0
    return (np.clip(f + a * col * (1 - f), 0, 1) * 255).astype(np.uint8)


def piece_overlay(g, pc, head, tail, whip_n, sweep_n=0):
    """转好的段上叠接点层：head = 头 17 帧的 PNG 列表（退场半段），tail = 尾 17 帧的（入场半段），whip_n = 尾上甩镜帧数，
    sweep_n = 头上章首 T6 光扫帧数（16，叠在擦除层上面）。"""
    n = pc["meta"]["frames"]
    pngs = [p for p in (head or []) + (tail or []) if p is not None and Path(p).exists()]
    key = sig(pc["v"], *pngs, extra=f"ov|{len(head or [])}|{len(tail or [])}|{whip_n}|t6{sweep_n}")
    vp, mp = PIECES / f"{g}_ov_{key}.mp4", PIECES / f"{g}_ov_{key}.json"
    if not (vp.exists() and mp.exists()):
        def gen():
            for i, fr in enumerate(decode(pc["v"], n)):
                if head and i < len(head) and head[i] is not None and Path(head[i]).exists():
                    fr = over(fr, read_png(head[i]))
                if sweep_n and i < sweep_n:
                    fr = t6_sweep(fr, i, sweep_n)
                k = i - (n - len(tail or []))
                if tail and k >= 0 and tail[k] is not None and Path(tail[k]).exists():
                    fr = over(fr, read_png(tail[k]))
                kw = i - (n - whip_n)
                if whip_n and kw >= 0:
                    fr = whip(fr, (kw + 1) / whip_n)
                yield fr
        encode_frames(gen(), vp)
        finish(vp, pc["a"], mp, n, dict(src=pc["meta"].get("src"), base=Path(pc["v"]).name))
    note = list(pc["note"])
    if head:
        note.append("头 17 帧叠接点擦除层（退场半段）")
    if tail:
        note.append("尾 17 帧叠接点擦除层（入场半段）")
    if whip_n:
        note.append(f"尾 {whip_n} 帧 T2 甩镜")
    if sweep_n:
        note.append(f"头 {sweep_n} 帧章首 T6 光扫")
    return dict(v=vp, a=pc["a"], meta=json.loads(mp.read_text(encoding="utf-8")), note=note)


def jwipe(j):
    w = JWIPE.get(j)
    if w is None:
        return None
    if w == "w0plate":
        return w if (WORK / "w1/w0wipe_final").exists() else None
    if w.startswith("oncam_") and not (WORK / "bwipe" / w).exists():
        return "runner（" + w + " 还没渲，退）"
    return w


def run(args, **kw):
    return subprocess.run([str(a) for a in args], capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def ff(*args):
    r = run([FF, "-y", "-v", "error", *args])
    if r.returncode:
        raise RuntimeError("ffmpeg 失败：" + r.stderr[-1500:])
    return r


def probe(p):
    """(画面帧数, fps, 宽, 高, 有无声音, 声音秒)；读不了返回 None（可能正在写）。"""
    r = run([FP, "-v", "error", "-count_packets", "-show_entries",
             "stream=codec_type,r_frame_rate,avg_frame_rate,nb_read_packets,duration,width,height", "-of", "json", p])
    if r.returncode:
        return None
    try:
        S = json.loads(r.stdout)["streams"]
        v = next(s for s in S if s["codec_type"] == "video")
        a = next((s for s in S if s["codec_type"] == "audio"), None)
        n, d = v["r_frame_rate"].split("/")
        return dict(nf=int(v["nb_read_packets"]), fps=int(n) / int(d), w=int(v["width"]), h=int(v["height"]),
                    avg=v.get("avg_frame_rate"), r=v["r_frame_rate"], audio=a is not None,
                    adur=float(a["duration"]) if a and a.get("duration") not in (None, "N/A") else 0.0)
    except Exception:
        return None


def rel(p):
    p = Path(p)
    for a, b in ((p, ROOT), (p.resolve(), ROOT.resolve())):
        try:
            return a.relative_to(b).as_posix()
        except ValueError:
            pass
    return p.as_posix()


def mmss(f):
    s = f / FPS
    return f"{int(s // 60):02d}:{s % 60:05.2f}"


def sig(*paths, extra=""):
    h = hashlib.sha1((PIPE_VER + extra).encode())
    for p in paths:
        p = Path(p)
        st = p.stat()
        h.update(f"{p.resolve().as_posix()}|{st.st_size}|{int(st.st_mtime)}".encode())
    return h.hexdigest()[:12]


# ---------------------------------------------------------------- 选文件


def load_block():
    p = HERE / "blocklist.txt"
    if not p.exists():
        return set()
    out = set()
    for ln in p.read_text(encoding="utf-8").splitlines():
        ln = ln.split("#")[0].strip().replace("\\", "/")
        if ln:
            out.add(ln)
    return out


def blocked(p, block):
    r = rel(p)
    return Path(p).name in block or r in block or Path(p).as_posix() in block


def resolve(entry, block):
    """候选里第一个能用的 → (路径, 状态, 备注, probe, 没用的候选说明列表)。"""
    skipped = []
    for c in entry.get("cands", []):
        p = Path(c["path"])
        if not p.is_absolute():
            p = ROOT / p
        if not p.exists():
            continue
        if blocked(p, block):
            skipped.append(f"{p.name}（blocklist）")
            continue
        if time.time() - p.stat().st_mtime < 20:
            skipped.append(f"{p.name}（正在写）")
            continue
        pr = probe(p)
        if not pr or pr["nf"] <= 0:
            skipped.append(f"{p.name}（读不出帧数）")
            continue
        st = entry.get("state_override", {}).get(rel(p)) or c["state"]
        return p, st, c.get("note", ""), pr, skipped
    return None, None, None, None, skipped


# ---------------------------------------------------------------- 转码（每段一次，存缓存）


def analyse(vp):
    """量一段转好的画面：黑帧区间、冻帧区间（段内帧号）。缩到 480×270 再量，快。"""
    r = run([FF, "-hide_banner", "-nostats", "-i", vp, "-an", "-vf",
             "scale=480:270,blackdetect=d=0.05:pix_th=0.06,freezedetect=n=-60dB:d=0.5", "-f", "null", "-"])
    blacks, freezes, fs = [], [], None
    for ln in r.stderr.splitlines():
        m = re.search(r"black_start:([\d.]+) black_end:([\d.]+)", ln)
        if m:
            blacks.append([round(float(m.group(1)) * FPS), round(float(m.group(2)) * FPS)])
        m = re.search(r"freeze_start: ([\d.]+)", ln)
        if m:
            fs = float(m.group(1))
        m = re.search(r"freeze_end: ([\d.]+)", ln)
        if m and fs is not None:
            freezes.append([round(fs * FPS), round(float(m.group(1)) * FPS)])
            fs = None
    if fs is not None:                                            # 冻到段尾
        freezes.append([round(fs * FPS), None])
    return blacks, freezes


def audio_from(src, t0, dur, ap, has_audio=True):
    if has_audio:
        ff("-ss", f"{t0:.6f}", "-i", src, "-vn", "-af", f"aresample={SR},aformat=channel_layouts=stereo,apad,atrim=0:{dur:.6f}",
           "-ac", 2, "-ar", SR, "-c:a", "pcm_s16le", ap)
    else:
        ff("-f", "lavfi", "-t", f"{dur:.6f}", "-i", f"anullsrc=r={SR}:cl=stereo", "-c:a", "pcm_s16le", ap)


def tail_black_frames(src, nf, fps):
    """源文件段尾连着的黑帧数（按源帧率），量最后 3 秒。"""
    t0 = max(0.0, nf / fps - 3.0)
    r = run([FF, "-hide_banner", "-nostats", "-ss", f"{t0:.3f}", "-i", src, "-an", "-vf", "blackdetect=d=0.03:pix_th=0.06", "-f", "null", "-"])
    end = nf / fps
    for ln in r.stderr.splitlines():
        m = re.search(r"black_start:([\d.]+) black_end:([\d.]+)", ln)
        if m and t0 + float(m.group(2)) >= end - 1.5 / fps:
            return round((end - (t0 + float(m.group(1)))) * fps)
    return 0


def piece_plain(g, src, pr, entry):
    """普通段：源 → 1080p60。返回 piece 字典。"""
    lim = entry.get("max_frames")
    n = round(pr["nf"] / pr["fps"] * FPS)
    trimmed = 0
    if entry.get("trim_tail_black"):
        tb = tail_black_frames(src, pr["nf"], pr["fps"])
        trimmed = round(tb / pr["fps"] * FPS)
        n -= trimmed
    if lim:
        n = min(n, lim)
    key = sig(src, extra=f"plain|{n}|{lim}|{trimmed}")
    vp, ap, mp = PIECES / f"{g}_{key}.mp4", PIECES / f"{g}_{key}.wav", PIECES / f"{g}_{key}.json"
    if not (vp.exists() and ap.exists() and mp.exists()):
        tmpv = vp.with_name(vp.stem + "_tmp.mp4")
        ff("-i", src, "-vf", f"fps={FPS},{VF}", "-frames:v", n, *NV, "-an", tmpv)
        os.replace(tmpv, vp)
        audio_from(src, 0.0, n / FPS, ap, pr["audio"])
        got = probe(vp)["nf"]
        bl, fr = analyse(vp)
        mp.write_text(json.dumps(dict(frames=got, want=n, blacks=bl, freezes=fr, src=rel(src), trimmed_black=trimmed), ensure_ascii=False), encoding="utf-8")
    m = json.loads(mp.read_text(encoding="utf-8"))
    note = []
    if not pr["audio"]:
        note.append("成片没有音轨，补了静音")
    elif pr["adur"] - n / FPS > 1.5 / FPS and not lim:
        note.append(f"音轨比画面长 {pr['adur'] - n / FPS:.2f} s，截掉了")
    if abs(pr["fps"] - FPS) > 0.01:
        note.append(f"源 {pr['fps']:.3g} fps，换算到 60（复帧）")
    if (pr["w"], pr["h"]) != (W, H):
        note.append(f"源 {pr['w']}×{pr['h']}，lanczos 缩到 1920×1080")
    if lim and round(pr["nf"] / pr["fps"] * FPS) > lim:
        note.append(f"取前 {lim} 帧（源 {pr['nf']} 帧）")
    if m.get("trimmed_black"):
        note.append(f"段尾黑帧 {m['trimmed_black']} 帧裁掉（J02）")
    return dict(v=vp, a=ap, meta=m, note=note)


# ---- W0、W1（帧序列 + 盖在相邻段上）


def _np():
    import numpy as np
    from PIL import Image
    return np, Image


def read_png(p):
    np, Image = _np()
    im = Image.open(p)
    return np.asarray(im.convert("RGBA" if im.mode in ("RGBA", "LA") else "RGB"))


def over(base, rgba):
    np, _ = _np()
    a = rgba[..., 3:4].astype(np.float32) / 255.0
    return (base.astype(np.float32) * (1 - a) + rgba[..., :3].astype(np.float32) * a).astype(np.uint8)


def sweep(img, k, n=14):
    """T6 光扫，照抄 assemble_w0w1.sweep：第 k 帧（0..n-1），斜亮带从左扫到右，同时整体提亮，正中最亮（上限 0.93）。"""
    np, _ = _np()
    t = (k + 0.5) / n
    bump = math.sin(math.pi * t) ** 2
    x = np.linspace(0, 1, W, dtype=np.float32)[None, :] + 0.25 * np.linspace(0, 1, H, dtype=np.float32)[:, None]
    band = np.exp(-((x - (-0.2 + 1.45 * t)) / 0.16) ** 2)
    a = np.clip(0.82 * bump + 0.5 * band * (0.3 + 0.7 * bump), 0, 1)[..., None]
    f = img[..., :3].astype(np.float32) / 255.0
    return (np.clip(f + (0.93 - f) * a, 0, 1) * 255).astype(np.uint8)


def decode(src, n):
    """源 → 60 fps rgb24 帧的生成器（最多 n 帧）。"""
    np, _ = _np()
    p = subprocess.Popen([FF, "-v", "error", "-i", str(src), "-vf", f"fps={FPS},scale=1920:1080:flags=lanczos", "-frames:v", str(n),
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    for _ in range(n):
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            break
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3)
    p.stdout.close()
    p.wait()


def encode_frames(frames, vp):
    np, _ = _np()
    tmpv = vp.with_name(vp.stem + "_tmp.mp4")
    enc = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-vf", "scale=out_range=tv,format=yuv420p,setsar=1", *NV, "-an", str(tmpv)], stdin=subprocess.PIPE)
    n = 0
    for img in frames:
        enc.stdin.write(np.ascontiguousarray(img[..., :3]).tobytes())
        n += 1
    enc.stdin.close()
    if enc.wait():
        raise RuntimeError(f"编码失败：{vp}")
    os.replace(tmpv, vp)
    return n


W1D = WORK / "w1"
TL09 = ROOT / "导演检查_20261120/09_片头_时间线.json"
MP09 = ROOT / "导演检查_20261120/09_片头W0_大标题W1.mp4"


def w_meta():
    c0 = json.loads((W1D / "w0_final/check.json").read_text(encoding="utf-8"))
    c1 = json.loads((W1D / "w1z_final/check.json").read_text(encoding="utf-8"))
    tl = json.loads(TL09.read_text(encoding="utf-8"))
    return c0, c1, tl


def w_sig():
    return [W1D / "w0_final/check.json", W1D / "w0wipe_final/check.json", W1D / "w1z_final/check.json", MP09, TL09]


def finish(vp, ap, mp, n, extra):
    got = probe(vp)["nf"]
    bl, fr = analyse(vp)
    mp.write_text(json.dumps(dict(frames=got, want=n, blacks=bl, freezes=fr, **extra), ensure_ascii=False), encoding="utf-8")


def piece_w0():
    c0, _, tl = w_meta()
    n = c0["nf"]
    key = sig(*w_sig(), extra="w0")
    vp, ap, mp = PIECES / f"W0_{key}.mp4", PIECES / f"W0_{key}.wav", PIECES / f"W0_{key}.json"
    if not (vp.exists() and ap.exists() and mp.exists()):
        encode_frames((read_png(W1D / f"w0_final/f_{f:04d}.png") for f in range(n)), vp)
        audio_from(MP09, tl["A"]["w0"][0], n / FPS, ap)
        finish(vp, ap, mp, n, dict(src="G:/cdk20/work/w1/w0_final"))
    return dict(v=vp, a=ap, meta=json.loads(mp.read_text(encoding="utf-8")),
                note=[f"w0_final 前 {n} 帧；声音从 09_片头W0_大标题W1.mp4 第 {tl['A']['w0'][0]:.2f} s 起截"])


def piece_w1():
    _, c1, tl = w_meta()
    tail, nw, head = c1["tail"], c1["nf_w1"], c1["head"]
    key = sig(*w_sig(), extra="w1")
    vp, ap, mp = PIECES / f"W1_{key}.mp4", PIECES / f"W1_{key}.wav", PIECES / f"W1_{key}.json"
    if not (vp.exists() and ap.exists() and mp.exists()):
        encode_frames((read_png(W1D / f"w1z_final/f_{f:04d}.png") for f in range(tail, tail + nw)), vp)
        audio_from(MP09, tl["B"]["w1_start"], nw / FPS, ap)
        finish(vp, ap, mp, nw, dict(src="G:/cdk20/work/w1/w1z_final"))
    return dict(v=vp, a=ap, meta=json.loads(mp.read_text(encoding="utf-8")),
                note=[f"w1z_final 第 {tail}–{tail + nw - 1} 帧；声音从 09_片头W0_大标题W1.mp4 第 {tl['B']['w1_start']:.2f} s 起截"])


def piece_neighbor(g, src, pr, entry, mode):
    """1-01（头上叠 W0 的擦除层）、1-11（尾 120 帧换成 W1 的三维尾）、2-01（头 120 帧换成 W1 的三维头）。段长、声音照源。"""
    c0, c1, _ = w_meta()
    n = round(pr["nf"] / pr["fps"] * FPS)
    trimmed = 0
    if entry.get("trim_tail_black"):
        trimmed = round(tail_black_frames(src, pr["nf"], pr["fps"]) / pr["fps"] * FPS)
        n -= trimmed
    key = sig(src, *w_sig(), extra=f"{mode}|{n}|{trimmed}")
    vp, ap, mp = PIECES / f"{g}_{key}.mp4", PIECES / f"{g}_{key}.wav", PIECES / f"{g}_{key}.json"
    tail, nw, head = c1["tail"], c1["nf_w1"], c1["head"]
    half = 7
    if not (vp.exists() and ap.exists() and mp.exists()):
        def gen():
            for i, fr in enumerate(decode(src, n)):
                if mode == "w0wipe":
                    f60 = c0["nf"] + i
                    p = W1D / f"w0wipe_final/f_{f60:04d}.png"
                    if f60 <= c0["wipe"][2] and p.exists():
                        fr = over(fr, read_png(p))
                elif mode == "w1tail":
                    k = i - (n - tail)                               # ≥ 0：换成三维尾
                    if k >= 0:
                        fr = read_png(W1D / f"w1z_final/f_{k:04d}.png")[..., :3]
                        if k < half:
                            fr = sweep(fr, k + half)
                    elif k >= -half:
                        fr = sweep(fr, k + half)
                elif mode == "w1head":
                    if i < head:
                        f = tail + nw + i
                        fr = read_png(W1D / f"w1z_final/f_{f:04d}.png")[..., :3]
                        if i >= head - half:
                            fr = sweep(fr, i - (head - half))
                    elif i < head + half:
                        fr = sweep(fr, i - head + half)
                yield fr
        encode_frames(gen(), vp)
        audio_from(src, 0.0, n / FPS, ap, pr["audio"])
        finish(vp, ap, mp, n, dict(src=rel(src), trimmed_black=trimmed))
    m = json.loads(mp.read_text(encoding="utf-8"))
    note = {"w0wipe": [f"头上叠 W0 擦除层（w0wipe_final 第 {c0['nf']}–{c0['wipe'][2]} 帧）"],
            "w1tail": [f"最后 {tail} 帧换成 W1 三维尾（w1z_final 0–{tail - 1}），切点 14 帧 T6 光扫"],
            "w1head": [f"头 {head} 帧换成 W1 三维头（w1z_final {tail + nw}–{tail + nw + head - 1}），切点 14 帧 T6 光扫"]}[mode]
    if m.get("trimmed_black"):
        note.append(f"段尾黑帧 {m['trimmed_black']} 帧裁掉（J02）")
    if abs(pr["fps"] - FPS) > 0.01:
        note.append(f"源 {pr['fps']:.3g} fps，换算到 60")
    return dict(v=vp, a=ap, meta=m, note=note)


# ---------------------------------------------------------------- 主体


def load_master():
    for nm in ("master_v2.json", "master_v1.json"):
        p = V3 / "映射" / nm
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8")), nm
    raise SystemExit("没有 master_v*.json")


def word_span(g):
    ws = g.get("words") or []
    if not ws:
        return None, None
    c0 = g["cut_start_f"]
    first = min(w["G0"] for w in ws) - c0
    last = max(round(w["g1"] * FPS) for w in ws) - c0
    return int(first), int(last)


def load_joints():
    p = HERE / "joints_v10.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    rows = d["joints"] if isinstance(d, dict) else d
    return {r["id"]: r for r in rows}


def main():
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("--rc", help="滚动版号（两位数）；不写就在现有最大号上加 1")
    ap_.add_argument("--final", action="store_true")
    ap_.add_argument("--mix", help="整片混音 wav（mix_v10.py 出）")
    ap_.add_argument("--dry", action="store_true")
    A = ap_.parse_args()
    t_start = time.time()
    PIECES.mkdir(parents=True, exist_ok=True)
    RC.mkdir(parents=True, exist_ok=True)
    D23.mkdir(parents=True, exist_ok=True)
    M, mname = load_master()
    S = json.loads((HERE / "sources_v10.json").read_text(encoding="utf-8"))
    src_by = {e["group"]: e for e in S["segments"]}
    block = load_block()
    joints = load_joints()

    # ---- 段表
    groups = []
    for g in M["groups"]:
        name = "+".join(g["segs"]) if len(g["segs"]) <= 3 else f"{g['segs'][0]}–{g['segs'][-1][-2:]}"
        groups.append(dict(group=g["group"], name=name, kind=g["kind"], segs=g["segs"], mg=g))
    groups.append(dict(group="EGG", name="EGG", kind="EGG", segs=["EGG"], mg=None))

    rows, missing = [], []
    for gi, G in enumerate(groups):
        e = src_by.get(G["group"])
        if e is None:
            raise SystemExit(f"sources_v10.json 里没有 {G['group']}")
        row = dict(i=gi + 1, group=G["group"], name=G["name"], kind=G["kind"], tier=e.get("tier"),
                   want=e.get("want_f") or (G["mg"]["len_f"] if G["mg"] else None), entry=e)
        if e.get("special") == "w0":
            ok = (W1D / "w0_final/check.json").exists() and MP09.exists()
            row.update(src=None if not ok else W1D / "w0_final", state="新", pr=None, skipped=[], cand_note="")
        elif e.get("special") == "w1":
            ok = (W1D / "w1z_final/check.json").exists() and MP09.exists()
            row.update(src=None if not ok else W1D / "w1z_final", state="新", pr=None, skipped=[], cand_note="")
        else:
            p, st, cn, pr, sk = resolve(e, block)
            row.update(src=p, state=st, pr=pr, skipped=sk, cand_note=cn)
        if row["src"] is None:
            if G["group"] == "EGG":
                missing.append("EGG")
                continue
            raise SystemExit(f"{G['group']}：候选文件一个都不能用（{e.get('cands')}；跳过的：{row['skipped']}）")
        rows.append(row)

    # ---- 转码（缓存）
    def base_piece(row):
        e, g = row["entry"], row["group"].replace("+", "_")
        sp = e.get("special")
        if sp == "w0":
            return piece_w0()
        if sp == "w1":
            return piece_w1()
        if sp in ("w0wipe", "w1tail", "w1head"):
            return piece_neighbor(g, row["src"], row["pr"], e, sp)
        return piece_plain(g, row["src"], row["pr"], e)

    def work(row):
        pc = base_piece(row)
        k = rows.index(row)
        if not joints or row["group"] == "EGG":
            return pc
        jl, jr = joints.get(f"J{k:02d}"), joints.get(f"J{k + 1:02d}")
        if jl and jl.get("right") not in (None, row["group"]):              # 接点表和段序对不上就不叠（不猜）
            print(f"接点 {jl['id']} 右段 {jl.get('right')} ≠ {row['group']}，不叠", flush=True)
            jl = None
        if jr and jr.get("left") not in (None, row["group"]):
            print(f"接点 {jr['id']} 左段 {jr.get('left')} ≠ {row['group']}，不叠", flush=True)
            jr = None
        head = tail = None
        whip_n = sweep_n = 0
        # 11-23 T2b：按 ASM 表（19 的 6.3 装配叠，按两侧这一版实际用的片定哪一侧叠）；位 3 原来按 joints 的 overlay 字段叠，
        # 但 B 页那一侧的半段页面自己已经画了（B*.jsx 的 T5In/T5Out），照 overlay 字段会叠两遍，所以改成逐接点写死。
        if jl and jl["id"] in ASM:
            p = ASM[jl["id"]](rows[k - 1] if k > 0 else None, row)
            if p and p[1]:
                head = wipe_halves(p[1])[1]
        if jl and SWEEP_ON.get(jl["id"]) == row["group"]:
            sweep_n = 16
        if jr and jr["id"] in ASM:
            p = ASM[jr["id"]](row, rows[k + 1] if k + 1 < len(rows) else None)
            if p and p[0]:
                tail = wipe_halves(p[0])[0]
            if p and p[2]:
                whip_n = p[2]
        if not (head or tail or whip_n or sweep_n):
            return pc
        return piece_overlay(row["group"].replace("+", "_"), pc, head, tail, whip_n, sweep_n)

    def joint_notes(k):
        """接点 J<k> 这一版拼片实际做了什么（写进清单）。"""
        jid = f"J{k:02d}"
        out = []
        if jid in ASM and 0 < k < len(rows):
            p = ASM[jid](rows[k - 1], rows[k])
            if p:
                out.append(p[3])
        if jid in SWEEP_ON and k < len(rows) and rows[k]["group"] == SWEEP_ON[jid]:
            out.append(f"{rows[k]['group']} 第 0–15 帧叠章首 T6 光扫")
        return "；".join(out) or None

    if not A.dry:
        with ThreadPoolExecutor(WORKERS) as ex:
            futs = {id(r): ex.submit(work, r) for r in rows}
            for r in rows:
                pc = futs[id(r)].result()
                r["piece"] = pc
                print(f"{r['i']:3d} {r['name']:14} {r['state']:8} {pc['meta']['frames']:5d}/{r['want'] or 0:5d} {rel(r['src'])}", flush=True)

    # ---- 起点、清单
    t = 0
    for k, r in enumerate(rows):
        r["frames"] = r["piece"]["meta"]["frames"] if not A.dry else (round(r["pr"]["nf"] / r["pr"]["fps"] * FPS) if r["pr"] else (r["want"] or 0))
        if A.dry and r["entry"].get("max_frames"):
            r["frames"] = min(r["frames"], r["entry"]["max_frames"])
        r["start_f"] = t
        t += r["frames"]
    total = t

    # ---- 拼
    out = None
    if not A.dry:
        tag = "final" if A.final else None
        if A.final:
            out = D23 / "01_v10_整片.mp4"
        else:
            have = [int(m.group(1)) for p in RC.glob("v10_rc*.mp4") if (m := re.match(r"v10_rc(\d+)\.mp4$", p.name))]
            nn = A.rc or f"{max(have + [0]) + 1:02d}"
            out = RC / f"v10_rc{nn}.mp4"
        lst = WORK / "v10/_concat"
        lst.mkdir(parents=True, exist_ok=True)
        (lst / "v.txt").write_text("".join(f"file '{r['piece']['v'].as_posix()}'\n" for r in rows), encoding="utf-8")
        (lst / "a.txt").write_text("".join(f"file '{r['piece']['a'].as_posix()}'\n" for r in rows), encoding="utf-8")
        ff("-f", "concat", "-safe", "0", "-i", lst / "v.txt", "-c", "copy", lst / "video.mp4")
        if A.mix:
            ff("-i", A.mix, "-af", f"aresample={SR},aformat=channel_layouts=stereo,apad,atrim=0:{total / FPS:.6f}", "-ac", 2, "-ar", SR,
               "-c:a", "pcm_s16le", lst / "audio.wav")
        else:
            ff("-f", "concat", "-safe", "0", "-i", lst / "a.txt", "-c", "copy", lst / "audio.wav")
        part = out.with_name(out.stem + "_写入中.mp4")
        ff("-i", lst / "video.mp4", "-i", lst / "audio.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
           "-ar", SR, "-movflags", "+faststart", part)
        os.replace(part, out)

    # ---- 清单 manifest_v10.json（19 的 2.5）
    segs = []
    for k, r in enumerate(rows):
        mg = next((g["mg"] for g in groups if g["group"] == r["group"]), None)
        fw, lw = word_span(mg) if mg else (None, None)
        key = "_".join(mg["segs"]) if mg else "EGG"
        vw = WORK / f"map_cache/remotion_public/map/{key}.wav"
        sw = WORK / f"audio/v10/sfx_seg/{key}.wav"
        jl, jr = f"J{k:02d}", f"J{k + 1:02d}"
        if r["group"] == "EGG":
            jl, jr = "J70", "J71"
        code = lambda j: (joints.get(j, {}).get("code") if joints else None) or (JCODE[int(j[1:])] if int(j[1:]) < len(JCODE) else None)
        subs = "none" if r["kind"] in ("MUSIC", "EGG") else r["entry"].get("subs_by_file", {}).get(r["src"].name if r["src"] else "", "burn")
        segs.append(dict(i=r["i"], group=r["group"], kind=r["kind"], tier=r["tier"], file=rel(r["src"]) if r["src"] else None,
                         frames=r["frames"], start_f=r["start_f"],
                         voice_wav=vw.as_posix() if vw.exists() else None, sfx_wav=sw.as_posix() if sw.exists() else None,
                         trans_in=code(jl) if k > 0 else None, trans_out=code(jr),
                         first_word_f=fw, last_word_end_f=lw, subs=subs,
                         state=r["state"], want_f=r["want"], diff_f=(r["frames"] - r["want"]) if r["want"] else None,
                         joint_in=jl, joint_out=jr,
                         # 擦除层：JWIPE 记成片里实际用的那块（11-23 T2b），没有再用 joints_v10.json 的设计值
                         wipe_in=(jwipe(jl) or (joints.get(jl, {}).get("wipe") if joints else None)) if k > 0 else None,
                         wipe_out=jwipe(jr) or (joints.get(jr, {}).get("wipe") if joints else None),
                         asm_in=joint_notes(k) if k > 0 and r["group"] != "EGG" else None,
                         asm_out=joint_notes(k + 1) if r["group"] != "EGG" else None, note="；".join((r["piece"]["note"] if not A.dry else []) + ([r["cand_note"]] if r["cand_note"] else []))))
    man = dict(fps=FPS, built=time.strftime("%Y-%m-%d %H:%M"), master=mname, out=rel(out) if out else None, total_f=total,
               mix=A.mix, joints_src="粗剪/v10/joints_v10.json" if joints else "19 的 6.3（build_v10.JCODE）",
               word_frames_from=mname + "（段内帧，按 master 的段时间；B 档页还没按裁停顿重渲时，和成片差几帧）",
               missing=missing, segments=segs)
    (HERE / "manifest_v10.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")

    chk = machine_check(out, rows, total, A) if out else None
    write_list(rows, total, out, chk, missing, A, mname, time.time() - t_start)
    print(f"DONE {rel(out) if out else '(dry)'} {total} 帧 {mmss(total)}，用时 {time.time() - t_start:.0f} s", flush=True)


# ---------------------------------------------------------------- 机检（19 的 7.1 末尾的全片门槛）


def machine_check(out, rows, total, A):
    pr = probe(out)
    res = []

    def put(cid, what, val, rule, ok):
        res.append(dict(id=cid, what=what, value=val, rule=rule, ok=bool(ok)))

    put("F1", "分辨率", f"{pr['w']}×{pr['h']}", "1920×1080", (pr["w"], pr["h"]) == (W, H))
    an, ad = (int(x) for x in (pr["avg"] or "0/1").split("/"))
    avg = an / ad if ad else 0.0
    cfr = pr["r"] == "60/1" and abs(avg - FPS) < 0.001
    put("F2", "帧率", f"r_frame_rate {pr['r']}，平均 {avg:.5f} fps", "60 fps 恒定（r_frame_rate 60/1，平均和 60 差 < 0.001；各段都按 60 fps 转码，concat 直接拷贝）", cfr)
    put("F3", "总帧数", f"成片 {pr['nf']}，清单各段之和 {total}", "相等", pr["nf"] == total)
    bl = []
    fz = []
    for r in rows:
        m = r["piece"]["meta"]
        for a, b in m["blacks"]:
            bl.append(dict(group=r["group"], f0=r["start_f"] + a, f1=r["start_f"] + b, seg_f=[a, b]))
        for a, b in m["freezes"]:
            b = r["frames"] if b is None else b
            fz.append(dict(group=r["group"], f0=r["start_f"] + a, f1=r["start_f"] + b, seg_f=[a, b], s=round((b - a) / FPS, 2)))
    bad_bl = [b for b in bl if b["group"] not in ("W5", "EGG")]
    put("F4", "黑帧位置（blackdetect d=0.05 pix_th=0.06，逐段量）",
        ("；".join(f"{b['group']} 段内 {b['seg_f'][0]}–{b['seg_f'][1]}（片内 {mmss(b['f0'])}）" for b in bl) or "无"),
        "只在 J70（W5 尾、彩蛋头）和 J71（彩蛋尾）", not bad_bl)
    ex_fz = ("W1", "W5", "EGG")                                  # 片名、AI 使用说明的停留在这几段里，要看图确认
    bad_fz = [z for z in fz if z["group"] not in ex_fz]
    byg = {}
    for z in fz:
        byg.setdefault(z["group"], []).append(z)
    put("F5", "冻帧 ≥ 0.5 s（freezedetect −60 dB，逐段量；逐处帧号见 json）",
        ("；".join(f"{g} {len(v)} 处共 {sum(z['s'] for z in v):.1f} s（最长 {max(z['s'] for z in v):.1f} s，片内 {mmss(v[0]['f0'])} 起）"
                  for g, v in byg.items()) or "无"),
        "没有（W1、W5、彩蛋里片名和 AI 使用说明的停留除外，要看图确认）", not bad_fz)
    put("F6", "音画长度差", f"画面 {pr['nf'] / FPS:.4f} s，声音 {pr['adur']:.4f} s，差 {abs(pr['nf'] / FPS - pr['adur']) * FPS:.2f} 帧",
        "≤ 1 帧", abs(pr["nf"] / FPS - pr["adur"]) * FPS <= 1.0)
    put("F7", "总时长（19 的 7.3）", f"{total} 帧 = {mmss(total)}", f"≤ 19:55.0（{LIMIT_F} 帧），≥ 15:00", MIN_F <= total <= LIMIT_F)
    d = dict(file=rel(out), built=time.strftime("%Y-%m-%d %H:%M"), mix=A.mix, results=res, blacks=bl, freezes=fz,
             all_ok=all(r["ok"] for r in res))
    (D23 / "_机检_v10.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    L = ["# v10 整片机检", "",
         f"HKBU SCIE1007 课程作业的科普视频。v10 拼片 `{rel(out)}` 的全片门槛（19 的 7.1 末尾），{d['built']}（韩国时间）。",
         "黑帧、冻帧在每段转码时逐段量（段与段是硬切），片内位置按清单的起点换算。接点 K1–K7 不在这里（17 的 T2b）。", "",
         f"结论：{'全过' if d['all_ok'] else '有不过的项'}。", "",
         "| # | 查什么 | 量到的 | 要求 | 结果 |", "|---|---|---|---|---|"]
    for r in res:
        L.append(f"| {r['id']} | {r['what']} | {r['value']} | {r['rule']} | {'过' if r['ok'] else '**不过**'} |")
    (D23 / "_机检_v10.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    md2html(D23 / "_机检_v10.md")
    return d


def md2html(p):
    for py in (sys.executable, "python", "C:/Python314/python.exe"):
        r = run([py, "-X", "utf8", ROOT / "_env/tools/md2html.py", p])
        if r.returncode == 0:
            return True
    return False


def write_list(rows, total, out, chk, missing, A, mname, secs):
    new = sum(r["state"] == "新" for r in rows)
    L = ["# v10 整片清单", "",
         "HKBU SCIE1007 课程作业的科普视频。v10：把各段成片按总表顺序接起来（1080p60），接点照 19 的 6.3 叠装配擦除层和章首光扫，段内画面没改，没烧字幕。",
         f"出片：`{rel(out) if out else '（--dry，没拼）'}`，{time.strftime('%Y-%m-%d %H:%M')}（韩国时间）；"
         f"全长 **{mmss(total)}**（{total} 帧）；声音：{'整片混音 ' + A.mix if A.mix else '各段成片自带的声音接起来'}；用时 {secs:.0f} 秒。",
         f"段序和“总表”帧数：`映射/{mname}`（W0 168、W1 1010 照 17 的 1.2 改；5-04 1510 照 18 的 A5 接长，11-23）。“差”= 实际 − 总表。", ""]
    ok = total <= LIMIT_F
    L.append(f"**时长门槛**（19 的 7.3，≤ 19:55.0 = {LIMIT_F} 帧）：{'过' if ok else '不过'}，"
             f"{'余' if ok else '超'} {abs(LIMIT_F - total)} 帧（{abs(LIMIT_F - total) / FPS:.2f} 秒）。")
    old_b = sorted([r for r in rows if r["tier"] in ("B", "B→A") and r["want"] and r["frames"] - r["want"] > 1],
                   key=lambda r: r["frames"] - r["want"], reverse=True)
    if old_b:
        L.append("")
        L.append(("还在用旧时间（没按裁停顿重渲）的 B 档页，按能省的帧数从大到小：" if not ok else "还在用旧时间的 B 档页（门槛已过，仅列出）：")
                 + "、".join(f"{r['group']}（{r['frames'] - r['want']:+d}）" for r in old_b) + "。")
    if missing:
        L.append("")
        L.append("没接的：" + "、".join("片尾彩蛋（`导演检查_20261123/20_片尾彩蛋.mp4` 还没有）" if m == "EGG" else m for m in missing) + "。")
    if chk:
        L += ["", f"机检：{'全过' if chk['all_ok'] else '有不过的项'}，见 `导演检查_20261123/_机检_v10.md`。"]
        for r in chk["results"]:
            if not r["ok"]:
                L.append(f"- {r['id']} {r['what']}：{r['value']}（要求 {r['rule']}）")
    from collections import Counter
    cnt = Counter(r["state"] for r in rows)
    L += ["", "状态统计：" + "、".join(f"{k} {v}" for k, v in cnt.items()) + "。", "",
          "| # | 段 | 档 | 起 | 用的文件 | 状态 | 帧数 | 总表 | 差 | 备注 |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        note = list(r["piece"]["note"]) if "piece" in r else []
        if r.get("cand_note"):
            note.append(r["cand_note"])
        if r.get("skipped"):
            note.append("没用：" + "、".join(r["skipped"]))
        diff = f"{r['frames'] - r['want']:+d}" if r["want"] else "—"
        L.append(f"| {r['i']} | {r['name']} | {r['tier']} | {mmss(r['start_f'])} | `{rel(r['src'])}` | {r['state']} | {r['frames']} | "
                 f"{r['want'] or '—'} | {diff} | {'；'.join(note)} |")
    L += ["", "## 说明", "",
          "- 选文件：`粗剪/v10/sources_v10.json` 每段的候选按先后取第一个存在、读得出、不在 `粗剪/v10/blocklist.txt` 里的。没过验收的片，把文件名写进 blocklist.txt 再拼一次。",
          "- 段长用成片自己的帧数，不拉伸、不冻末帧；30 fps 的源（W5 现成版）按时长换算成 60 fps（复帧）。",
          "- W0、W1 用渲染帧接：W1 三维尾 120 帧盖在 1-11 最后 120 帧上、三维头 120 帧盖在 2-01 头 120 帧上，各一道 14 帧 T6 光扫；W0 的擦除层叠在 1-01 头 16 帧。W1 的歌在 1-11 尾巴下面的淡入这一版没有（W0、W1 的声音按段截自 09_片头W0_大标题W1.mp4），整片混音出来后用 `--mix` 换掉。",
          "- 接点：19 的 6.3 的装配叠层和四处章首 T6 光扫由拼片叠（build_v10.ASM、SWEEP_ON，逐接点做了什么写在 manifest 的 asm_in/asm_out）；其余接点两段自己带转场。接点机检 K1–K7：`粗剪/_check/check_joints_v10.py`。",
          "- W2 取英文押韵字幕版前 1500 帧，没加 ROUGH CUT 角标；W3 4K 版 lanczos 缩到 1080p 取前 900 帧。"]
    md = HERE / "清单_v10.md"
    md.write_text("\n".join(L) + "\n", encoding="utf-8")
    md2html(md)
    if A.final:
        fm = D23 / "01_v10_清单.md"
        fm.write_text("\n".join(L) + "\n", encoding="utf-8")
        md2html(fm)


if __name__ == "__main__":
    main()
