"""HKBU SCIE1007 课程作业的科普视频：词→画面映射总表的共用读取库（纯 Python，Blender 5.x 自带的 Python 和项目 Python 都能 import）。

总表 master_v1.json 的格式见 映射/README.md。这里只做读取和换算，不依赖 numpy / bpy：

    import sys; sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/映射")
    import maplib as M
    T = M.load()                      # 默认读 映射/master_v1.json
    g = T.group("1-08")               # 一段（出镜对话组用 "1-05+1-06+1-07"，或其中任一个段号）
    g.word("1-08.w018")               # 词：{"wid","w","t0","t1","f0","f1","g0","g1",...}，f 是段内 60 fps 帧
    g.key("only#2")                   # 按"词#第几次"找（和 beats_resolve 的写法一样）
    g.wf("ready")                     # 词开口的段内帧（=bl_s108 的 wf）
    g.sentence("1-08.s2")             # 句：首词/末词、t0/t1、f0/f1
    g.events(tool="blender")          # 事件：f_start / f_land / f_end（段内 60 fps 帧），until 解到的词
    M.ev_value(ev, f)                 # 事件在第 f 帧的进度 0–1（start→land 线性，land 之后 1），给关键帧之外的程序动作用

帧号规则：f = round(t × 60)。段内帧 0 = 这段声音在成片里开始的那一帧（cut_v8.json 的 new_start）。
"""
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
FPS = 60
DEFAULT = HERE / "master_v1.json"


def norm(w):
    """词的比较形式：小写，去掉两头标点（2.8、001's、ten-to-seventeen-years 这类中间的符号保留）。"""
    return w.lower().strip(" \t\"'“”‘’.,;:!?()[]…—–-")


def frame(t):
    return int(round(t * FPS))


class Group:
    def __init__(self, d):
        self.d = d
        self.name = d["group"]
        self.segs = d["segs"]
        self.len_f = d["len_f"]
        self._w = {w["wid"]: w for w in d["words"]}
        self._s = {s["sid"]: s for s in d["sentences"]}

    # ---- 词
    @property
    def words(self):
        return self.d["words"]

    def word(self, wid):
        return self._w[wid]

    def key(self, k, seg=None):
        """'only#2' → 这段（或组里 seg 那一段）第 2 个 only。"""
        base, _, n = k.partition("#")
        hits = [w for w in self.d["words"] if w["norm"] == norm(base) and (seg is None or w["seg"] == seg)]
        if not hits:
            raise KeyError(f"{self.name}: 没有词 {k!r}")
        return hits[int(n or 1) - 1]

    def wf(self, k, n=1, seg=None):
        """词开口的段内帧（k 可以是 wid、'word#2' 或 'word' 加 n）。"""
        if k in self._w:
            return self._w[k]["f0"]
        return self.key(k if "#" in k else f"{k}#{n}", seg)["f0"]

    def wend(self):
        return self.d["words"][-1]["f1"] if self.d["words"] else self.len_f - 1

    # ---- 句
    @property
    def sentences(self):
        return self.d["sentences"]

    def sentence(self, sid):
        return self._s[sid]

    # ---- 事件
    def events(self, tool=None, native=None):
        out = self.d["events"]
        if tool:
            out = [e for e in out if e.get("tool") == tool]
        if native is not None:
            out = [e for e in out if e.get("native") == native]
        return out

    def event(self, eid):
        return next(e for e in self.d["events"] if e["eid"] == eid)


class Table:
    def __init__(self, d):
        self.d = d
        self.fps = d["fps"]
        self.groups = [Group(g) for g in d["groups"]]
        self._by = {}
        for g in self.groups:
            self._by[g.name] = g
            for s in g.segs:
                self._by.setdefault(s, g)

    def group(self, name):
        return self._by[name]

    def all_words(self):
        for g in self.groups:
            yield from g.words


def load(path=None):
    p = Path(path or os.environ.get("CDK20_MAP") or DEFAULT)
    return Table(json.loads(p.read_text(encoding="utf-8")))


def ev_value(ev, f):
    """事件进度：f_start 之前 0，f_start→f_land 线性到 1，之后 1（f_land 是落点/长满的那一帧）。"""
    a, b = ev["f_start"], ev["f_land"]
    if f <= a:
        return 0.0
    if f >= b:
        return 1.0
    return (f - a) / max(1, b - a)
