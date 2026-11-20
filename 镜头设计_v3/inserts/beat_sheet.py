"""HKBU SCIE1007 课程作业的科普视频：读"卡点表"（音乐/卡点/<段名>_<歌名>.json），把按拍写的镜头表换成帧。

换歌时画面设计不动，只换这张表：歌的速度、选的那一段从歌的第几秒起、每个大动作落在第几拍、淡入淡出怎么走。
渲染脚本（Blender 里的 shot_w0w1.py / shot_w1z.py）、合成（assemble_w0w1.py）、验收（check_w0w1.py）都读同一张表。
做法和坑见项目技能 .claude/skills/beat-retime/SKILL.md。

选哪张表：环境变量 CDK20_SEG（段名，默认 w0w1）和 CDK20_SONG（歌名，默认 Blinding Lights）。
纯标准库，Blender 自带的 Python 也能 import。
"""
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
MUSIC = HERE.parent / "音乐"
FPS = 60


def sheet_path(seg=None, song=None):
    seg = seg or os.environ.get("CDK20_SEG", "w0w1")
    song = song or os.environ.get("CDK20_SONG", "Blinding Lights")
    return MUSIC / "卡点" / f"{seg}_{song}.json"


def load(seg=None, song=None):
    p = sheet_path(seg, song)
    if not p.exists():
        raise SystemExit(f"beat sheet missing: {p.name}（先照 beat-retime 技能写卡点表）")
    s = json.loads(p.read_text(encoding="utf-8"))
    s["path"] = str(p)
    s["beat_s"] = 60.0 / s["bpm"]
    return s


def song_file(s):
    return MUSIC / "原曲" / s["file"]


def f_of_beat(s, n, fps=FPS):
    """第 n 拍（可以是半拍）→ 帧。"""
    return round(fps * s["beat_s"] * n)


def song_t(s, part, beat=0.0):
    """这一段的第 beat 拍在歌里是第几秒（part = "w0" / "w1"…，表里 song_t_at_beat = [拍, 歌里的秒]）。"""
    b0, t0 = s[part]["song_t_at_beat"]
    return t0 + (beat - b0) * s["beat_s"]


class Warp:
    """设计刻度 u（镜头表原来的单位，动作之间的相对位置按它写）→ 新歌的拍。

    表里给出"哪个动作落在第几拍"（锚点）；锚点之间线性插值，所以落在锚点上的动作一帧不差地在拍上，
    写成"某动作 + 0.3 u"的小偏移跟着所在那一段伸缩。锚点必须严格递增（动作顺序不变）。
    两头以外按 unit_s（设计刻度原来的秒数）走，保证段外的时间还是真实秒。"""

    def __init__(self, pairs, beat_s, unit_s):
        pairs = sorted(set((float(u), float(b)) for u, b in pairs))
        for (u0, b0), (u1, b1) in zip(pairs[:-1], pairs[1:]):
            if not (u1 > u0 and b1 > b0):
                raise SystemExit(f"beat sheet: anchors not increasing at u={u0}->{u1}, beat={b0}->{b1}")
        self.p, self.k = pairs, unit_s / beat_s

    def beat(self, u):
        p = self.p
        if u <= p[0][0]:
            return p[0][1] + (u - p[0][0]) * self.k
        if u >= p[-1][0]:
            return p[-1][1] + (u - p[-1][0]) * self.k
        for (u0, b0), (u1, b1) in zip(p[:-1], p[1:]):
            if u <= u1:
                return b0 + (b1 - b0) * (u - u0) / (u1 - u0)

    def u(self, beat):
        p = self.p
        if beat <= p[0][1]:
            return p[0][0] + (beat - p[0][1]) / self.k
        if beat >= p[-1][1]:
            return p[-1][0] + (beat - p[-1][1]) / self.k
        for (u0, b0), (u1, b1) in zip(p[:-1], p[1:]):
            if beat <= b1:
                return u0 + (u1 - u0) * (beat - b0) / (b1 - b0)


def warp_from(s, part, tl):
    """把镜头表 tl（名字 → 设计刻度，或一串刻度）和卡点表里同名的拍配成锚点。"""
    pairs = []
    for k, b in s[part]["beats"].items():
        if k not in tl:
            raise SystemExit(f"beat sheet: {k} not in shot table")
        if isinstance(b, list):
            if len(b) != len(tl[k]):
                raise SystemExit(f"beat sheet: {k} needs {len(tl[k])} beats")
            pairs += list(zip(tl[k], b))
        else:
            pairs.append((tl[k], b))
    return Warp(pairs, s["beat_s"], s[part]["unit_s"])


def envelope(points, t):
    """音量包络：points = [[秒, 增益], …]，中间用 smoothstep 过渡（没有折角，听不出"切"）。"""
    if t <= points[0][0]:
        return points[0][1]
    for (t0, g0), (t1, g1) in zip(points[:-1], points[1:]):
        if t <= t1:
            x = (t - t0) / (t1 - t0)
            x = x * x * (3 - 2 * x)
            return g0 + (g1 - g0) * x
    return points[-1][1]
