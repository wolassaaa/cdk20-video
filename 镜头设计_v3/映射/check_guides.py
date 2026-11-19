"""HKBU SCIE1007 课程作业的科普视频：视线引导验收（05_视线引导.md 第七节 V1–V14），读 keys 和成片算数。

用法（项目根目录，要 numpy + PIL，python 3.12 以上，page_tool 要用）：
  python 镜头设计_v3/映射/check_guides.py 3-04 2-08 3-01      keys + 成片全查（会另渲一版关掉引导的对照片，半分辨率）
  python 镜头设计_v3/映射/check_guides.py --keys-only 1-04 …   只查能从 keys 算的（V1–V5、V8、V10、V14），渲染前用
  python 镜头设计_v3/映射/check_guides.py --film               全片 V14（所有 keys 的引导次数）

成片：映射/_cache/pages/<合成>.mp4（page_tool.py check 出的）。对照片：同一页传 --props {"noguide":true} 渲成半分辨率 jpg 序列（G 盘），
亮度差（V6）、预颤位移（V5）都拿"开引导"减"关引导"算，内容本身的变化抵掉。报告写 映射/_reports/guides_<段>.md。不删任何东西。
全部通过退出码 0，否则 1。
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
MAN = ROOT / "镜头设计_v2/tests/T4_remotion/src/v3/manual"
REM = ROOT / "镜头设计_v2/tests/T4_remotion"
FF = str(ROOT / "_env/ffmpeg/ffmpeg.exe")
NG = HERE / "_cache/guide_noguide"          # _cache 联到 G 盘
REP = HERE / "_reports"
W = 1920


def load(seg):
    K = json.loads((HERE / "keys" / f"{seg.replace('+', '_')}.json").read_text(encoding="utf-8"))
    return K


def page_of(seg):
    import page_tool as PT
    g = PT.group(seg)
    return PT.comp(seg, g), g


def speech_frames(K):
    return sum(s["f1"] - s["f0"] for s in K["sentences"])


def sent_of(K, f):
    best = None
    for s in K["sentences"]:
        if s["f0"] <= f <= s["f1"]:
            return s["sid"]
        d = min(abs(f - s["f0"]), abs(f - s["f1"]))
        if best is None or d < best[0]:
            best = (d, s["sid"])
    return best[1] if best else None


def union_len(ivs):
    tot, cur = 0, None
    for a, b in sorted(ivs):
        if cur is None or a > cur[1]:
            if cur:
                tot += cur[1] - cur[0]
            cur = [a, b]
        else:
            cur[1] = max(cur[1], b)
    if cur:
        tot += cur[1] - cur[0]
    return tot


def keys_checks(seg, K, oncam):
    G = K.get("guides", [])
    R = {}
    n = K["len_f"]
    # V1：任一帧"到位"（gon→gend）的引导最多 1 个；交接时 gs→goff 最多重叠 2 个
    held = max([sum(1 for g in G if g["gon"] <= f <= g["gend"]) for f in range(n)] or [0])
    over = max([sum(1 for g in G if g["gs"] <= f < g["goff"]) for f in range(n)] or [0])
    R["V1"] = (held <= 1 and over <= 2, f"到位重叠最多 {held} 个，交接重叠最多 {over} 个")
    # V2：相邻 gon ≥ 36；每句 ≤ 3；任意 10 秒 ≤ 5
    gaps = [b["gon"] - a["gon"] for a, b in zip(G, G[1:])]
    per = {}
    for g in G:
        per.setdefault(sent_of(K, g["land"]), []).append(g["id"])
    win = max([sum(1 for h in G if g["gon"] <= h["gon"] < g["gon"] + 600) for g in G] or [0])
    ok = all(x >= 36 for x in gaps) and all(len(v) <= 3 for v in per.values()) and win <= 5
    R["V2"] = (ok, f"最小间隔 {min(gaps) if gaps else '—'} 帧；每句最多 {max([len(v) for v in per.values()] or [0])} 次；10 秒内最多 {win} 次")
    # V3：引导处在变化中的时间 ≤ 说话时间的 45%
    ch = []
    for g in G:
        ch.append((g["gs"], max(g["land"], g["gon"] + 6) if g["kind"] == "runner" else g["land"]))
        if g["goff"] > g["gend"]:
            ch.append((g["gend"], g["goff"]))
    sp = speech_frames(K)
    r3 = union_len(ch) / max(1, sp)
    R["V3"] = (r3 <= 0.45, f"变化中 {union_len(ch)} 帧 / 说话 {sp} 帧 = {r3:.0%}")
    # V4：g_on 在落点前 4–12 帧；g_start 在落点前 16–36 帧
    bad = [g["id"] for g in G if not (4 <= g["land"] - g["gon"] <= 12 and 16 <= g["land"] - g["gs"] <= 36)]
    R["V4"] = (not bad, "全部在范围内" if not bad else f"超出：{bad}")
    # V5（时间部分）：预颤 6 帧、结束于落点（kit nudge 常数）；"嗒" g_tick 在落点前 3–6 帧
    badt = [g["id"] for g in G if not (3 <= g["land"] - g["tick"] <= 6)]
    R["V5t"] = (not badt, f"预颤 {sum(g['nudge'] for g in G)} 次（land−6→land）；嗒全在落点前 4 帧" if not badt else f"嗒越界：{badt}")
    # V8：走料
    rn = [g for g in G if g["kind"] == "runner"]
    msgs, ok8 = [], True
    per_s = {}
    for g in rn:
        per_s[sent_of(K, g["land"])] = per_s.get(sent_of(K, g["land"]), 0) + 1
        far = g.get("dist", 0) > 0.35 or g.get("from") == "offscreen"
        sec = (g["gon"] - g["gs"]) / 60
        v = g.get("path", g.get("dist", 0)) / max(sec, 1e-6)
        ok8 &= far and v <= 0.6 and 24 <= g["gon"] - g["gs"] <= 90
        msgs.append(f"{g['id']} 距离 {g.get('dist')} 画面宽、走 {g['gon'] - g['gs']} 帧、速度 {v:.2f} 画面宽/秒")
    ok8 &= all(c <= 1 for c in per_s.values())
    R["V8"] = (ok8, "；".join(msgs) + "；到浇口后 6 帧被吃掉（RunnerPulse 常数）" if rn else "本段不走料")
    # V10：有 camera_to 的引导，镜头起动不早于 g_start + 6
    cams = [e for e in K["events"] if e.get("verb") == "camera_to"]
    b10 = [e["id"] for e in cams for g in G if g["gs"] <= e["f_start"] <= g["land"] and e["f_start"] < g["gs"] + 6]
    R["V10"] = (not b10, "本段没有镜头运动" if not cams else ("镜头都在 g_start+6 之后" if not b10 else f"太早：{b10}"))
    # V14：段内每分钟次数 ≤ 25
    rate = len(G) / max(1e-6, n / 3600)
    R["V14s"] = (rate <= 25, f"{len(G)} 次 / {n / 60:.1f} 秒 = 每分钟 {rate:.1f} 次")
    return R


def page_checks(seg, C, K, oncam):
    R = {}
    src = (MAN / f"{C}.jsx").read_text(encoding="utf-8")
    kit = (MAN / "kit.jsx").read_text(encoding="utf-8")
    # V9：没有只为引导存在的点、圈、箭头（Bead 已是 null，页面不再调用；RunnerPulse 走完就消失）
    used = bool(re.search(r"<Bead\b", src))
    R["V9"] = ("export const Bead = () => null" in kit and not used, "页面不再调用 Bead，kit 里 Bead 返回 null" + ("" if not used else "（页面还有 <Bead>）"))
    # V13：Lens 参数和豁免层
    lens = re.search(r"<Lens([^>]*)>", src)
    p = {k: float(v) for k, v in re.findall(r"(blur|dim|desat)=\{([\d.]+)\}", lens.group(1))} if lens else {}
    bl, dm, ds = p.get("blur", 2.2), p.get("dim", 0.82), p.get("desat", 0.75)
    leak = []
    for m in re.finditer(r"<Layer id=\"(\w+)\">(.*?)</Layer>", src, re.S):
        for t in ("<Label", "<Pen", "<Source", "<Title", "<Legend", "<Plate", "<Tag"):
            if t in m.group(2):
                leak.append(f"{m.group(1)} 层里有 {t[1:]}")
    ok = lens is not None and bl <= 2.5 and dm >= 0.75 and ds >= 0.7 and not leak
    R["V13"] = (ok, f"模糊 {bl}px、不透明度 {dm}、饱和度 {ds}；字都在豁免层" + ("" if not leak else f"；不合：{leak}"))
    # V12：出镜段人不进 Lens；零件等待模糊 2–4 px
    if oncam:
        idle = re.search(r"idle=\{([\d.]+)\}", lens.group(1)) if lens else None
        iv = float(idle.group(1)) if idle else 0
        person_in = src.find("<Lens") < src.find("<OnCamFrame") if "<OnCamFrame" in src else False
        R["V12"] = (2 <= iv <= 4 and not person_in and "PersonFront" not in (src[src.find("<Lens"):src.find("</Lens>")] if "<Lens" in src else ""),
                    f"人物层在 Lens 外；零件等待模糊 {iv}px；手伸向钥匙那拍（key）不点名")
    # V8 颜色：RunnerPulse 不用红色
    rc = re.findall(r"<RunnerPulse[^>]*color=\{(\w+)\}", src)
    if "<RunnerPulse" in src:
        R["V8c"] = ("RED" not in rc, f"走料颜色 {rc or ['INK']}（原线色七成 + 纸色三成）")
    # V11：引导只指向画面上已有的、或马上要长出来的东西；字不会被引导提前露出（Lens 只虚化 / 提亮，不显示任何东西）
    early = [g["id"] for g in K.get("guides", []) if g["ev_s"] - g["gs"] > 40]
    R["V11"] = (not early, "引导起点都在目标事件开始前 40 帧以内；Lens 只做虚化/轮廓光，不提前显示内容" if not early else f"太早：{early}")
    # V7（二维）：拉焦 12–24 帧、smoothstep 单调不过冲；被点名图层模糊 0；背景模糊上限见 V13
    pulls = [g["gon"] - g["gs"] for g in K.get("guides", []) if g["kind"] == "focus"]
    R["V7"] = (all(12 <= x <= 24 for x in pulls), f"拉焦 {sorted(set(pulls))} 帧，单调无过冲；主体模糊 0 px；二维页背景用 V13 上限（3D 的 6–14 px 不适用）")
    return R


def ff_frame(src, n, out, scale=None):
    vf = f"select=eq(n\\,{n})" + (f",scale={scale}" if scale else "")
    subprocess.run([FF, "-v", "error", "-y", "-i", str(src), "-vf", vf, "-fps_mode", "passthrough", "-frames:v", "1", str(out)], check=True)


def yavg(src, pattern=None):
    args = [FF, "-v", "error"] + (["-framerate", "60", "-i", pattern] if pattern else ["-i", str(src)])
    args += ["-vf", "scale=960:540:out_range=full,format=yuvj444p,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-", "-f", "null", "-"]
    out = subprocess.run(args, capture_output=True, text=True).stdout
    return [float(x) for x in re.findall(r"YAVG=([\d.]+)", out)]


def render_noguide(seg, C, L):
    import page_tool as PT
    d = NG / C
    d.mkdir(parents=True, exist_ok=True)
    have = sorted(d.glob("element-*.jpeg"))
    if len(have) >= L and have[0].stat().st_mtime > (MAN / f"{C}.jsx").stat().st_mtime and have[0].stat().st_mtime > (MAN / "kit.jsx").stat().st_mtime:
        return d
    sp = PT.slim_public(seg)
    cli = ["node", REM / "node_modules/@remotion/cli/remotion-cli.js"]
    r = PT.run(cli + ["render", f"src/v3/manual/{C}.jsx", C, d, "--sequence", "--image-format=jpeg", "--jpeg-quality=95", "--scale=0.5",
                      '--props={"noguide":true}', f"--public-dir={sp}", "--concurrency=6", "--log=error"], cwd=REM)
    if r.returncode:
        sys.exit("对照片渲染出错")
    return d


def phase_shift(a, b):
    """b 相对 a 的平移（像素），numpy 版相位相关，带亚像素抛物线插值。"""
    import numpy as np
    win = np.outer(np.hanning(a.shape[0]), np.hanning(a.shape[1]))
    Fa, Fb = np.fft.fft2(a * win), np.fft.fft2(b * win)
    R = Fb * np.conj(Fa)
    r = np.fft.ifft2(R / (np.abs(R) + 1e-9)).real
    iy, ix = np.unravel_index(np.argmax(r), r.shape)

    def sub(m, i, n):
        y0, y1, y2 = m[(i - 1) % n], m[i], m[(i + 1) % n]
        d = y0 - 2 * y1 + y2
        return i + (0.5 * (y0 - y2) / d if abs(d) > 1e-12 else 0)
    dy, dx = sub(r[:, ix], iy, r.shape[0]), sub(r[iy, :], ix, r.shape[1])
    if dy > r.shape[0] / 2:
        dy -= r.shape[0]
    if dx > r.shape[1] / 2:
        dx -= r.shape[1]
    return dx, dy


def film_checks(seg, C, K, oncam):
    import numpy as np
    from PIL import Image
    gray = lambda p: np.asarray(Image.open(p).convert("L"), dtype=np.float32)
    R = {}
    mp4 = HERE / "_cache/pages" / f"{C}.mp4"
    if not mp4.exists():
        return {"V6": (False, f"没有成片 {mp4}")}
    G = K.get("guides", [])
    yg = yavg(mp4)
    L = len(yg)
    d = render_noguide(seg, C, L)
    fs = sorted(d.glob("element-*.jpeg"))
    digits = len(re.sub(r"\D", "", fs[0].name))
    yn = yavg(None, str(d / f"element-%0{digits}d.jpeg"))
    n = min(len(yg), len(yn))
    diff = np.array([(yg[i] - yn[i]) / max(1, yn[i]) for i in range(n)])
    # 引导引起的全帧亮度变化 ≤ 3%；起伏：差值曲线每秒的方向反转（幅度 > 0.2%）≤ 2 次
    mx = float(np.abs(diff).max()) if n else 0
    sm = np.convolve(diff, np.ones(3) / 3, mode="same")
    turns, last_ext, sign = [], sm[0] if n else 0, 0
    for i in range(1, n):
        dv = sm[i] - last_ext
        if sign >= 0 and dv < -0.002:
            turns.append(i); sign, last_ext = -1, sm[i]
        elif sign <= 0 and dv > 0.002:
            turns.append(i); sign, last_ext = 1, sm[i]
        elif (sign > 0 and sm[i] > last_ext) or (sign < 0 and sm[i] < last_ext):
            last_ext = sm[i]
    per_s = max([sum(1 for t in turns if a <= t < a + 60) for a in range(0, max(1, n - 59))] or [0])
    ramp = all(g["land"] - g["gs"] >= 12 and (g["goff"] - g["gend"] >= 12 or g["goff"] == g["gend"]) for g in G)
    # 局部：落点那一帧，目标框里平均亮度 开/关 之比
    loc, disp = [], []
    tmp = ROOT / "_tmp" / "guide_chk"
    tmp.mkdir(parents=True, exist_ok=True)
    cap = 2 ** 0.2 if oncam else 1.08
    for g in G:
        if not g.get("box"):
            continue
        x, y, w, h = [int(v / 2) for v in g["box"]]
        for tag, fr in (("land", g["land"]), ("peak", g["land"] - 3)):
            if fr >= n:
                continue
            a = tmp / f"{C}_{g['id']}_{tag}_g.png"
            ff_frame(mp4, fr, a, "960:540")
            A, B = gray(a), gray(fs[fr])
            cA, cB = A[y:y + h, x:x + w], B[y:y + h, x:x + w]
            if tag == "land" and g.get("rim", True):
                loc.append((g["id"], float(cA.mean() / max(1, cB.mean()))))
            if tag == "peak" and g.get("nudge"):
                sx, sy = phase_shift(cB, cA)
                disp.append((g["id"], 2 * float(np.hypot(sx, sy))))     # 半分辨率量的，乘 2 回到 1080p 像素
    okl = all(r <= cap for _, r in loc)
    R["V6"] = (mx <= 0.03 and per_s <= 2 and ramp and okl,
               f"全帧亮度因引导最大变化 {mx:.2%}；起伏每秒最多 {per_s} 次；爬升都 ≥ 12 帧；目标框局部亮度比 "
               + ", ".join(f"{i} {r:.3f}（{np.log2(max(r, 1e-6)):+.2f} EV）" for i, r in loc) + f"（上限 {cap:.3f}）")
    R["V5d"] = (all(v <= 6 for _, v in disp), "预颤屏上位移（开/关对照相位相关）：" + (", ".join(f"{i} {v:.1f}px" for i, v in disp) or "无") + "；转角按物体半径压到总位移 ≤ 6 px")
    return R


NAMES = {"V1": "同时被引导", "V2": "引导密度", "V3": "安静时间", "V4": "提前量", "V5t": "预颤和嗒（时间）", "V5d": "预颤位移",
         "V6": "亮度", "V7": "焦点", "V8": "走料", "V8c": "走料颜色", "V9": "没有常驻标记", "V10": "镜头跟焦点", "V11": "不提前泄底",
         "V12": "出镜段", "V13": "二维页", "V14s": "段内频度"}


def check(seg, keys_only=False):
    K = load(seg)
    C, g = page_of(seg)
    oncam = g["kind"] == "ON-CAM"
    if oncam:
        K = dict(K, len_f=json.loads((MAN / f"oncam_{seg.replace('+', '_')}.json").read_text(encoding="utf-8"))["len_f"])
    R = keys_checks(seg, K, oncam)
    if not keys_only:
        R.update(page_checks(seg, C, K, oncam))
        R.update(film_checks(seg, C, K, oncam))
    ok = all(v[0] for v in R.values())
    lines = [f"# 视线引导验收 {seg}（{C}）", "", f"引导 {len(K.get('guides', []))} 次：" +
             "；".join(f"{x['id']}→{'/'.join(x['target'])} {x['kind']} {x['gs']}/{x['gon']}/{x['land']}/{x['gend']}/{x['goff']}" for x in K.get("guides", [])), "",
             "| 条 | 项 | 结果 | 数 |", "|---|---|---|---|"]
    for k in sorted(R, key=lambda s: (int(re.sub(r"\D", "", s)), s)):
        lines.append(f"| {k} | {NAMES.get(k, k)} | {'过' if R[k][0] else '**不过**'} | {R[k][1]} |")
    lines.append("")
    lines.append("全部通过" if ok else "有不过的项")
    REP.mkdir(exist_ok=True)
    (REP / f"guides_{seg.replace('+', '_')}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return ok


def film():
    tot, dur, worst = 0, 0, []
    for p in sorted((HERE / "keys").glob("*.json")):
        K = json.loads(p.read_text(encoding="utf-8"))
        n = len(K.get("guides", []))
        tot += n
        dur += K["len_f"]
        worst.append((n / max(1e-6, K["len_f"] / 3600), K["group"]))
    worst.sort(reverse=True)
    rate = tot / max(1e-6, dur / 3600)
    print(f"V14 全片：{tot} 次 / {dur / 3600:.1f} 分钟 = 每分钟 {rate:.1f} 次（上限 15）；最密 {worst[0][1]} 每分钟 {worst[0][0]:.1f} 次（上限 25）")
    return rate <= 15 and worst[0][0] <= 25


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--film" in a:
        sys.exit(0 if film() else 1)
    ko = "--keys-only" in a
    segs = [x for x in a if not x.startswith("--")]
    res = [check(s, ko) for s in segs]
    sys.exit(0 if all(res) else 1)
