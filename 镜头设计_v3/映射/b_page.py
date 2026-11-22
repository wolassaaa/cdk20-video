"""HKBU SCIE1007 课程作业的科普视频：B 档页面（Remotion + SVG + GSAP）的素材整理、出片和自检，一条命令做完。

用法（项目根目录，python 3.11+，要 numpy + PIL）：
  python 镜头设计_v3/映射/b_page.py post               Blender 贴图裁边 + 尺寸锚点表（src/v3/btier/bsprite_meta.json）+ 24 张颗粒图
  python 镜头设计_v3/映射/b_page.py render 3-05        validate + resolve + 拷 keys；搭本段的精简 public（G 盘硬链接）；
                                                       Remotion 出 1080p60 帧序列（--gl=angle --concurrency=2，帧和临时目录都在 G 盘）；
                                                       CipherTalk 的 ffmpeg（h264_nvenc）合声音（裁过停顿的段用 map_trim/<段>.wav），
                                                       出 导演检查_<BREVIEW>/14_B档_<段>.mp4（BREVIEW 默认 20261123）
  python 镜头设计_v3/映射/b_page.py check 3-05         自检：check_sync（对词、到句尾、1.5 s、帧率）、check_guides（V1–V14）、
                                                       B4 颜色、B5 不死（2.5 s）、B6 接点亮度和黑帧、B8 背景；每 10 帧抽一张拼成检查图；
                                                       规则 v2 三项（探针渲染：半分辨率、不铺大板，每 6 帧扫 DOM）：R02 前景静止 > 45 帧、
                                                       R04 字体字号（标签 ≥ 36、次级 ≥ 26、出处 ≥ 22、批注 Caveat 34–44、同屏标签 ≤ 2）、R08 标签框压零件掩码 / 字压字
                                                       11-22 加 18 文档 1.9 的验收数：G1 亮度（整段平均 0.55–0.80、没有低于 0.35 的帧）、G2 覆盖（探针帧里前景加托盘 ≥ 55%）
  python 镜头设计_v3/映射/b_page.py probe 3-05         只跑上面三项（加 G2）（页面改完先看这个，快）。标签确实属于某件（如地图上的地名）给 Label/Tag/Pen 写 on="hkmap"
  python 镜头设计_v3/映射/b_page.py html [批号]        汇总一批 → 导演检查_YYYYMMDD/14_B档_检查.html（第 2 批起 15_B档第2批_检查.html）

页面：镜头设计_v2/tests/T4_remotion/src/v3/btier/B<段号去横线>.jsx，合成 id 同名（3-05 → B305）。页面 import ./keys_<段>.json。
G 盘：帧 G:/cdk20/work/bframes/<段>/，public G:/cdk20/work/bpub/<段>/，检查图 G:/cdk20/work/bcheck/<段>/，Remotion 临时 G:/cdk20/work/remotion_tmp/。
不删源文件；本段旧帧在重渲前清掉（可再生的中间文件）。
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
REM = ROOT / "镜头设计_v2/tests/T4_remotion"
BT = REM / "src/v3/btier"
WORK = Path(os.environ.get("CDK20_WORK", "G:/cdk20/work"))
if not WORK.exists():
    sys.exit(f"工作盘 {WORK} 不在（G 盘拔了？）：停下，不改写到 C、D。")
PUB_SHARED = HERE / "_cache/ch1/public"          # 字体、各段声音（page_tool prep 导出的）
SPR_RAW, SPR = WORK / "bsprite", WORK / "bpub_src/bsprite"
GRAIN = WORK / "bpub_src/grain"
FRAMES, PUBS, CHK, RTMP = WORK / "bframes", WORK / "bpub", WORK / "bcheck", WORK / "remotion_tmp"
FF = "D:/software/tools/CipherTalk/resources/app.asar.unpacked/node_modules/ffmpeg-static/ffmpeg.exe"   # 带 h264_nvenc；_env/ffmpeg 写不了 G 盘
TRIM = HERE / "_cache/remotion_public/map_trim"
LONG_ROAD = {"6-09", "7-02", "6-10", "6-11", "2-08"}   # 11-22 夜总管裁定：X3 简版 6-10、6-11、2-08 也算长路页                                       # B 档长路页（bkit NO_TRAY 里的 B609、B702）：G2 覆盖只记录  # 11-22 停顿裁剪（trim_pauses.py，19 文档 7.3）：裁过的段先用这里的声音


def voice(seg):
    """这段该用的画外音：裁过停顿的（map_trim/<段>.wav）优先，没裁的用原来的。词时间跟着总表 v2（maplib 默认）。"""
    t = TRIM / f"{safe(seg)}.wav"
    return t if t.exists() else PUB_SHARED / f"{safe(seg)}.wav"


def review_dir(seg=None):
    """11-22 起一律放 导演检查_<BREVIEW>（默认 20261123；第一批 7 页不再写死 20261120）。"""
    return ROOT / f"导演检查_{os.environ.get('BREVIEW', '20261123')}"
PY = sys.executable
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", CDK20_WORK=str(WORK))


def comp(seg):
    return "B" + seg.replace("-", "")


def safe(seg):
    return seg.replace("+", "_")


def run(cmd, **kw):
    print("  $", " ".join(str(c) for c in cmd)[:240], flush=True)
    return subprocess.run([str(c) for c in cmd], env=kw.pop("env", ENV), **kw)


def hl(a, b):
    b = Path(b)
    b.parent.mkdir(parents=True, exist_ok=True)
    if b.exists():
        try:
            if os.path.samefile(a, b):
                return
        except OSError:
            pass
        b.unlink()
    try:
        os.link(a, b)
    except OSError:
        shutil.copy2(a, b)


# ---------------------------------------------------------------- post
def post():
    import numpy as np
    from PIL import Image
    meta = {}
    for png in sorted(SPR_RAW.glob("*/*.png")):
        key = f"{png.parent.name}/{png.stem}"
        js = png.with_suffix(".json")
        info = json.loads(js.read_text(encoding="utf-8")) if js.exists() else {"anchors": {}}
        im = Image.open(png).convert("RGBA")
        a = np.asarray(im)[..., 3]
        ys, xs = np.nonzero(a > 3)
        if not len(xs):
            continue
        pad = 6
        x0, y0 = max(0, xs.min() - pad), max(0, ys.min() - pad)
        x1, y1 = min(im.width, xs.max() + pad + 1), min(im.height, ys.max() + pad + 1)
        out = SPR / png.parent.name / png.name
        out.parent.mkdir(parents=True, exist_ok=True)
        if not out.exists() or out.stat().st_mtime < png.stat().st_mtime:
            im.crop((x0, y0, x1, y1)).save(out, optimize=True)
        anc = {k: [round(v[0] - x0, 1), round(v[1] - y0, 1)] for k, v in info.get("anchors", {}).items()}
        meta[key] = dict(w=int(x1 - x0), h=int(y1 - y0), anchors=anc, mm_per_px=info.get("mm_per_px"))
    (BT / "bsprite_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"贴图 {len(meta)} 张 → {SPR}，表 {BT / 'bsprite_meta.json'}")
    # 颗粒：shot_oncam._grain 同一个函数（白噪声 [1,2,1] 平滑两遍再归一，×1.7），σ 用出镜段测的默认 1.6/255；灰底 128，overlay 叠
    GRAIN.mkdir(parents=True, exist_ok=True)
    for i in range(24):
        out = GRAIN / f"{i:02d}.png"
        if out.exists():
            continue
        rng = np.random.default_rng(5000 + i)
        n = rng.normal(0.0, 1.0, (1080, 1920)).astype(np.float32)
        for _ in range(2):
            n = (np.roll(n, 1, 0) + 2 * n + np.roll(n, -1, 0)) / 4
            n = (np.roll(n, 1, 1) + 2 * n + np.roll(n, -1, 1)) / 4
        n = n / n.std() * 1.7
        Image.fromarray(np.clip(128 + n * 1.6, 0, 255).astype(np.uint8), "L").save(out, optimize=True)
    print("颗粒 24 张 →", GRAIN)


# ---------------------------------------------------------------- render
def page_needs(src):
    zones = sorted(set(re.findall(r"zone=\{(\d)\}", src) + re.findall(r"const ZONE\s*=\s*(\d)", src)))
    wipes = sorted(set(re.findall(r"<T5(?:In|Out)\s+name=\"(\w+)\"", src)))
    return zones, wipes


def slim_public(seg, src):
    d = PUBS / safe(seg)
    zones, wipes = page_needs(src)
    for fn in ("InstrumentSerif-Regular.ttf", "InstrumentSerif-Italic.ttf", "Caveat.ttf"):
        hl(PUB_SHARED / "fonts" / fn, d / "fonts" / fn)
    hl(voice(seg), d / f"{safe(seg)}.wav")
    for p in SPR.glob("*/*.png"):
        hl(p, d / "bsprite" / p.parent.name / p.name)
    for p in GRAIN.glob("*.png"):
        hl(p, d / "grain" / p.name)
    for z in zones:
        # 11-21 规则 v2 R03：第二版大板（焦外 12 px）渲满 720 帧就用它，没渲完先用第一版（焦外 21 px）
        v2 = sorted(f for f in (WORK / "bplate" / f"zone{z}_v2").glob("*.jpg") if f.stat().st_size > 0)
        fs = v2 if len(v2) >= 720 else sorted(f for f in (WORK / "bplate" / f"zone{z}").glob("*.jpg") if f.stat().st_size > 0)
        print(f"  第 {z} 区背景：{'v2（焦外 12 px）' if fs is v2 else 'v1（焦外 21 px，v2 还没渲完）'}")
        if not fs and os.environ.get("BPARTIAL"):
            fs = sorted(f for f in (WORK / "bplate" / "zone5").glob("*.jpg") if f.stat().st_size > 0)
            print(f"  试渲：第 {z} 区背景还没有，临时用第 5 区顶")
        if len(fs) < 720:
            if not os.environ.get("BPARTIAL") or not fs:
                sys.exit(f"第 {z} 区背景还没渲完（{len(fs)}/720）：等 b_plate 队列，或先渲别的页（试渲可设 BPARTIAL=1，缺的帧临时用最后一帧顶）")
            print(f"  试渲：第 {z} 区背景只有 {len(fs)}/720 帧，缺的临时用第 {fs[-1].name} 顶（正式出片前会自动换掉）")
            fs = fs + [fs[-1]] * (720 - len(fs))
        for i, p in enumerate(fs):
            hl(p, d / "bplate" / f"zone{z}" / f"{i:04d}.jpg")
    for w in wipes:
        fs = sorted((WORK / "bwipe" / w).glob("*.png"))
        if len(fs) < 34:
            sys.exit(f"擦除层 {w} 不全（{len(fs)}/34）")
        for p in fs:
            hl(p, d / "bwipe" / w / p.name)
    return d, zones, wipes


def render(seg, frames=None):
    C = comp(seg)
    page = BT / f"{C}.jsx"
    if not page.exists():
        sys.exit(f"页面还没写：{page}")
    if run([PY, HERE / "validate_events.py", seg], cwd=HERE).returncode:
        sys.exit("事件表没过 validate，先改事件表")
    run([PY, HERE / "resolve.py", seg], check=True, cwd=HERE)
    shutil.copy2(HERE / "keys" / f"{safe(seg)}.json", BT / f"keys_{safe(seg)}.json")
    K = json.loads((HERE / "keys" / f"{safe(seg)}.json").read_text(encoding="utf-8"))
    src = page.read_text(encoding="utf-8")
    pub, zones, wipes = slim_public(seg, src)
    fr = FRAMES / safe(seg)
    if fr.exists() and not frames:
        shutil.rmtree(fr)                      # 本段旧帧（可再生）
    fr.mkdir(parents=True, exist_ok=True)
    RTMP.mkdir(parents=True, exist_ok=True)
    import tempfile
    t = Path(tempfile.mkdtemp(dir=RTMP))
    env = dict(ENV, TEMP=str(t), TMP=str(t))
    cli = ["node", REM / "node_modules/@remotion/cli/remotion-cli.js", "render", f"src/v3/btier/{C}.jsx", C, fr,
           "--sequence", "--image-format=jpeg", "--jpeg-quality=94", "--gl=angle", "--concurrency=2", f"--public-dir={pub}", "--log=error",
           f"--bundle-cache=false"]
    if frames:
        cli.append(f"--frames={frames}")
    t0 = time.time()
    r = run(cli, cwd=REM, env=env)
    for _ in range(5):
        shutil.rmtree(t, ignore_errors=True)
        if not t.exists():
            break
        time.sleep(2)
    if r.returncode:
        sys.exit("Remotion 渲染出错（看上面的报错，多半是页面代码）")
    t_rem = time.time() - t0
    if frames:
        print(f"只渲了 {frames}，{t_rem:.0f} s")
        return
    review_dir(seg).mkdir(exist_ok=True)
    mp4 = review_dir(seg) / f"14_B档_{seg}.mp4"
    first = sorted(fr.glob("element-*.jpeg"))[0]
    digits = len(re.sub(r"\D", "", first.name))
    t1 = time.time()
    tmp = WORK / "bcheck" / f"_{safe(seg)}.mp4"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    rr = run([FF, "-y", "-loglevel", "error", "-framerate", "60", "-i", fr / f"element-%0{digits}d.jpeg", "-i", voice(seg),
              "-c:v", "h264_nvenc", "-preset", "p6", "-rc", "vbr", "-cq", "17", "-b:v", "0", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
              "-shortest", tmp])
    if rr.returncode:
        sys.exit("ffmpeg 合成失败")
    shutil.copy2(tmp, mp4)
    t_ff = time.time() - t1
    log = CHK / safe(seg) / "render.json"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(json.dumps(dict(seg=seg, comp=C, frames=K["len_f"], remotion_s=round(t_rem, 1), ffmpeg_s=round(t_ff, 1),
                                   s_per_frame=round(t_rem / K["len_f"], 3), zones=zones, wipes=wipes, mp4=str(mp4), voice=str(voice(seg)),
                                   when=time.strftime("%m-%d %H:%M")), ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"出片 {mp4}：Remotion {t_rem:.0f} s（{t_rem / K['len_f']:.2f} s/帧），ffmpeg {t_ff:.0f} s")


# ---------------------------------------------------------------- check
PAL = None


def palette():
    s = (BT / "bkit.jsx").read_text(encoding="utf-8")
    blk = s[s.index("export const C = {"):s.index("export const PALETTE")]
    return {h.upper() for h in re.findall(r"#[0-9A-Fa-f]{6}", blk)}


def check(seg):
    import numpy as np
    from PIL import Image
    C = comp(seg)
    K = json.loads((HERE / "keys" / f"{safe(seg)}.json").read_text(encoding="utf-8"))
    L = K["len_f"]
    fr = FRAMES / safe(seg)
    fs = sorted(fr.glob("element-*.jpeg"))
    od = CHK / safe(seg)
    od.mkdir(parents=True, exist_ok=True)
    mp4 = review_dir(seg) / f"14_B档_{seg}.mp4"
    R = {}
    # B1 对词 + B3 帧完整：check_sync（S1–S4）
    js = od / "sync.json"
    r = run([PY, HERE / "check_sync.py", mp4, seg, "--json", js], cwd=HERE, capture_output=True, text=True, encoding="utf-8", errors="replace")
    sync_txt = (r.stdout or "") + (r.stderr or "")
    (od / "sync.txt").write_text(sync_txt, encoding="utf-8")
    R["B1/B3 check_sync"] = (r.returncode == 0, sync_txt.strip().splitlines()[-1] if sync_txt.strip() else "无输出")
    # B2 引导：check_guides（B 页模式）
    r = run([PY, HERE / "check_guides.py", "--b", seg], cwd=HERE, capture_output=True, text=True, encoding="utf-8", errors="replace")
    gtxt = (r.stdout or "") + (r.stderr or "")
    (od / "guides.txt").write_text(gtxt, encoding="utf-8")
    bad = [ln for ln in gtxt.splitlines() if "**不过**" in ln]
    R["B2 check_guides"] = (r.returncode == 0, "V1–V14 全过" if r.returncode == 0 else "；".join(bad)[:400] or gtxt[-300:])
    # B4 颜色：页面和套件里出现的十六进制色都在 5.2 的表里（白、黑只作高光和阴影，用 rgba，不算颜色）
    pal = palette()
    src = (BT / f"{C}.jsx").read_text(encoding="utf-8")
    kit = (BT / "bkit.jsx").read_text(encoding="utf-8")
    found = {h.upper() for h in re.findall(r"#[0-9A-Fa-f]{6}\b", src + kit)} - {"#FFFFFF", "#000000"}
    off = sorted(found - pal)
    R["B4 颜色"] = (not off, "全部在 5.2 表里" if not off else f"表外：{off}")
    # 帧统计：亮度、相邻帧差
    thumbs, ys, diffs = [], [], []
    prev = None
    for i, p in enumerate(fs):
        im = Image.open(p).convert("L").resize((192, 108))
        a = np.asarray(im, dtype=np.float32)
        ys.append(float(a.mean()))
        if prev is not None:
            diffs.append(float(np.abs(a - prev).mean()))
        prev = a
    diffs = [0.0] + diffs
    # B5 不死：没有超过 2.5 秒（150 帧）什么都不动
    still, run_ = 0, 0
    for d in diffs:
        run_ = run_ + 1 if d < 0.05 else 0
        still = max(still, run_)
    R["B5 不死"] = (still <= 150, f"最长静止 {still} 帧（上限 150）")
    # B6 接点：首尾各 6 帧亮度、黑帧
    blacks = [i for i, y in enumerate(ys) if y < 16]
    head, tail = np.mean(ys[:6]), np.mean(ys[-6:])
    R["B6 接点"] = (not blacks, f"黑帧 {len(blacks)}；首 6 帧平均亮度 {head:.1f}，尾 6 帧 {tail:.1f}（两头都是擦除层盖满，和 A 段同一层，亮度差在接点处为 0）")
    # G1 亮度（18 文档 1.9 验收数）：整段平均亮度 0.55–0.80；任何一帧低于 0.35 算黑场（1.2）
    yy = np.array(ys) / 255.0
    lowf = [i for i, y in enumerate(yy) if y < 0.35]
    R["G1 亮度"] = (0.55 <= yy.mean() <= 0.80 and not lowf,
                   f"整段平均 {yy.mean():.3f}（要 0.55–0.80），最暗 {yy.min():.3f}（f{int(yy.argmin())}），低于 0.35 的帧 {len(lowf)}" + (f"（f{lowf[0]}–f{lowf[-1]}）" if lowf else ""))
    # B8 背景
    zones, wipes = page_needs(src)
    R["B8 背景"] = (bool(zones), f"L0 用第 {zones} 区 Blender 大板（720 帧来回）；擦除层 {wipes}")
    # B7 字：字号下限和字幕区由 bkit 在渲染时强制（违反就抛错，页面渲不出来）；这里数同一时刻的标签数在页面代码里核
    labels = len(re.findall(r"<Label\b", src))
    R["B7 字"] = (True, f"标签 ≥ 60 px（墨迹约 45 px）、出处行 32 px 钉在 886–928、批注 56–64 px、y ≤ 940 由套件强制；页面共 {labels} 个标签，同屏数见抽帧")
    # R02 / R04 / R08：探针渲染（半分辨率、只有前景）+ DOM 扫描
    probe_checks(seg, R, od)
    # 每 10 帧抽一张：拼检查图（6 × 5 一张）
    picks = list(range(0, len(fs), 10))
    sheets = []
    per = 30
    for si in range(0, len(picks), per):
        sh = Image.new("RGB", (6 * 320, 5 * 196), (40, 40, 40))
        from PIL import ImageDraw
        dr = ImageDraw.Draw(sh)
        for k, fi in enumerate(picks[si:si + per]):
            im = Image.open(fs[fi]).convert("RGB").resize((320, 180))
            x, y = (k % 6) * 320, (k // 6) * 196
            sh.paste(im, (x, y))
            dr.text((x + 4, y + 181), f"f{fi}", fill=(230, 230, 230))
        p = od / f"sheet_{si // per:02d}.jpg"
        sh.save(p, quality=88)
        sheets.append(p)
    rep = dict(seg=seg, comp=C, frames=len(fs), len_f=L, results={k: [bool(v[0]), v[1]] for k, v in R.items()},
               sheets=[str(p) for p in sheets], luma=[round(y, 1) for y in ys[::10]], luma_mean=round(float(np.mean(ys)) / 255, 4), max_diff=round(max(diffs), 2))
    (od / "check.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in R.items():
        print(f"{'过  ' if v[0] else '不过'} {k}：{v[1]}")
    print("检查图：", *[str(p) for p in sheets], sep="\n  ")
    return all(v[0] for v in R.values())



# ---------------------------------------------------------------- 探针（11-21 B 档视觉规则 v2 第 8 条：check 里三项自动量）
PROBE_STEP = 6            # 每 6 帧扫一次 DOM
STILL_MAX = 45            # R02：前景完全静止上限（帧）
STILL_THR = 0.02          # 480×270 灰度相邻帧平均差低于它算"完全没动"（探针渲染没有大板和颗粒，静止时差为 0）
MIN_PX = {"label": 60, "pen": 56, "tag": 40, "badge": 26, "engrave": 26, "counter": 26, "raw": 26, "source": 30}   # R04 最小字号（11-22 夜抬：标签 60、批注 56–64、图注 40、出处 ≥ 30，见 bkit 常量）
PEN_MAX_PX = 64
HERO_MIN = 486            # G3：英雄件屏上高（18 的 1.3）
HERO_MIN_ROAD = 240       # 长路页（11-22 夜总管裁定）：英雄件 = 金色 Slab 吊牌（048），量最大那一刻，门槛 240
OVERLAP_MAX = 150
SUB_TOP_PX = 940         # R08：标签框压在零件实心像素上超过 150 px² 算互压（1080p 像素）


def probe(seg):
    """半分辨率渲一遍"只有前景"的版本（不铺大板、颗粒），每 6 帧把字和零件的框打到日志；返回解析好的记录和帧目录。"""
    C = comp(seg)
    pub = PUBS / safe(seg)
    if not pub.exists():
        slim_public(seg, (BT / f"{C}.jsx").read_text(encoding="utf-8"))
    out = WORK / "bprobe" / safe(seg)
    if out.exists():
        shutil.rmtree(out)                      # 上次的探针帧（可再生）
    out.mkdir(parents=True)
    import tempfile
    RTMP.mkdir(parents=True, exist_ok=True)
    t = Path(tempfile.mkdtemp(dir=RTMP))
    env = dict(ENV, TEMP=str(t), TMP=str(t))
    cli = ["node", REM / "node_modules/@remotion/cli/remotion-cli.js", "render", f"src/v3/btier/{C}.jsx", C, out,
           "--sequence", "--image-format=jpeg", "--jpeg-quality=90", "--gl=angle", "--concurrency=2", f"--public-dir={pub}", "--scale=0.5",
           "--props=" + json.dumps({"bprobe": PROBE_STEP}), "--log=verbose", "--bundle-cache=false"]
    t0 = time.time()
    r = run(cli, cwd=REM, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    shutil.rmtree(t, ignore_errors=True)
    if r.returncode:
        sys.exit("探针渲染出错：" + (r.stderr or r.stdout or "")[-800:])
    recs = {}
    for ln in (r.stdout + r.stderr).splitlines():
        i = ln.find("BPROBE|")
        if i < 0:
            continue
        js = ln[i + 7:]
        js = js[:js.rfind("}") + 1]
        try:
            d = json.loads(js)
        except Exception:
            continue
        recs[d["f"]] = d
    print(f"  探针：{len(recs)} 次 DOM 扫描，{time.time() - t0:.0f} s")
    return recs, out


def probe_checks(seg, R, od):
    import numpy as np
    from PIL import Image
    recs, fr = probe(seg)
    fs = sorted(fr.glob("element-*.jpeg"))
    # ① R02 前景静止（只有前景的帧，相邻帧差）
    prev, runs, cur = None, [], None
    for i, p in enumerate(fs):
        a = np.asarray(Image.open(p).convert("L").resize((480, 270)), dtype=np.float32)
        still = prev is not None and float(np.abs(a - prev).mean()) < STILL_THR
        if still:
            cur = [cur[0], i] if cur else [i - 1, i]
        else:
            if cur and cur[1] - cur[0] + 1 > STILL_MAX:
                runs.append(cur)
            cur = None
        prev = a
    if cur and cur[1] - cur[0] + 1 > STILL_MAX:
        runs.append(cur)
    longest = max([b - a + 1 for a, b in runs], default=0)
    # ② G2 覆盖（18 文档 1.9 验收数）：探针渲染底色是纯绿（Stage 在 bprobe 时换的），不是绿的像素 = 前景加托盘；整段平均 ≥ 55%
    cov = []
    for p in fs:
        a = np.asarray(Image.open(p).convert("RGB").resize((480, 270)), dtype=np.int16)
        key = (a[..., 1] > 190) & (a[..., 0] < 90) & (a[..., 2] < 90)
        cov.append(1.0 - float(key.mean()))
    cv = np.array(cov) if cov else np.zeros(1)
    if seg in LONG_ROAD:                                             # 长路页按 18 的 1.9 G2 不带托盘（世界就是那条路），55% 不适用，只记数（11-22 施工位 2 定）
        R["G2 覆盖"] = (True, f"长路页不带托盘（18 的 1.9 G2），覆盖只记录：整段平均 {cv.mean():.1%}，最少 {cv.min():.1%}")
    else:
        R["G2 覆盖"] = (float(cv.mean()) >= 0.55, f"前景加托盘盖住画面：整段平均 {cv.mean():.1%}（要 ≥ 55%），最少 {cv.min():.1%}（f{int(cv.argmin())}）")
    R["R02 前景静止"] = (not runs, "没有超过 45 帧的完全静止" if not runs else
                      f"{len(runs)} 处超过 45 帧：" + "，".join(f"f{a}–{b}（{b - a + 1}）" for a, b in runs[:8]))
    # ② R04 字体、字号、同屏标签数、字幕区
    bad_font, bad_size, crowd, sub = {}, {}, [], {}
    prev_y = {}                                    # 上一次扫描里同一段字的 y：还在移动的字（镜头推拉、出入画）不算停在字幕区
    for f, d in sorted(recs.items()):
        labs = set()
        cur_y = {(t["role"], t["t"]): t["y"] for t in d["T"]}
        for t in d["T"]:
            key = (t["role"], t["t"])
            ff = t["ff"]
            if t["role"] == "pen":
                if "Hand" not in ff:
                    bad_font.setdefault(key, (f, ff))
            elif "InstrumentSerifB" not in ff:
                bad_font.setdefault(key, (f, ff))
            if t["fs"] + 0.01 < MIN_PX.get(t["role"], 26):
                bad_size.setdefault(key, (f, t["fs"]))
            if t["role"] == "pen" and t["fs"] > PEN_MAX_PX + 0.01:
                bad_size.setdefault(key, (f, t["fs"]))
            if t["role"] == "label" and t["op"] > 0.5:
                labs.add(t["rid"])
            if t["role"] == "source" and t["w"] > 960:
                bad_size.setdefault(("source 太长", t["t"]), (f, t["w"]))
            if t["y"] + t["h"] > SUB_TOP_PX and t["op"] > 0.3 and abs(prev_y.get(key, -999) - t["y"]) <= 2:
                sub.setdefault(key, f)
        prev_y = cur_y
        if len(labs) > 2:
            crowd.append((f, sorted(labs)))
    msg = []
    if bad_font:
        msg.append("字体不对：" + "；".join(f"{k[1]}（{k[0]}，f{v[0]}，{v[1][:30]}）" for k, v in list(bad_font.items())[:6]))
    if bad_size:
        msg.append("字号不够：" + "；".join(f"{k[1]}（{k[0]} {v[1]:.0f} px，f{v[0]}）" for k, v in list(bad_size.items())[:6]))
    if crowd:
        msg.append(f"同屏标签超过 2 个：{len(crowd)} 次，如 f{crowd[0][0]} {crowd[0][1]}")
    if sub:
        msg.append("压进字幕区：" + "；".join(f"{k[1]}（f{v}）" for k, v in list(sub.items())[:4]))
    big_badge = sorted({t["t"] for d in recs.values() for t in d["T"] if t["role"] == "badge" and t["h"] > 40})
    if big_badge:
        msg.append("徽章高过 40 px（导演 11-23）：" + "；".join(big_badge[:4]))
    R["R04 字"] = (not msg, "全是 Instrument Serif（批注 Caveat），字号达标，同屏标签 ≤ 2" if not msg else "。".join(msg))
    # ③ R08 标签框和零件掩码重叠
    alpha = {}

    def mask(name, w, h):
        k = (name, w, h)
        if k not in alpha:
            p = SPR / f"{name}.png"
            if p.exists():
                a = np.asarray(Image.open(p).getchannel("A").resize((max(1, w), max(1, h))), dtype=np.uint8) > 128
            else:
                a = np.ones((max(1, h), max(1, w)), bool)
            alpha[k] = a
        return alpha[k]

    hits = {}
    for f, d in sorted(recs.items()):
        parts = {p["pid"]: p for p in d["P"]}
        for t in d["T"]:
            if t["role"] not in ("label", "pen", "tag") or t["op"] < 0.3:
                continue
            mine = set()
            q = t.get("own") or ""
            while q:
                mine.add(q)
                q = parts.get(q, {}).get("up", "")
            ons = set(filter(None, (t.get("on") or "").split(",")))
            for p in d["P"]:
                if p["pid"] in mine or p["op"] < 0.3 or any(p["name"].startswith(o) for o in ons):
                    continue
                if p["name"] == "slab" and p["w"] * p["h"] > 0.4 * 1920 * 1080:
                    continue        # 盖过大半个画面的板是底板（记分板、台面），字本来就贴在上面
                x0, y0 = max(t["x"], p["x"]), max(t["y"], p["y"])
                x1, y1 = min(t["x"] + t["w"], p["x"] + p["w"]), min(t["y"] + t["h"], p["y"] + p["h"])
                if x1 <= x0 or y1 <= y0:
                    continue
                if p["name"] == "slab":
                    area = (x1 - x0) * (y1 - y0)
                else:
                    m = mask(p["name"], p["w"], p["h"])
                    area = int(m[y0 - p["y"]:y1 - p["y"], x0 - p["x"]:x1 - p["x"]].sum())
                if area > OVERLAP_MAX:
                    k = (t["rid"] or t["t"], p["name"])
                    if k not in hits or area > hits[k][1]:
                        hits[k] = (hits.get(k, (f,))[0], area)
        # 字和字互压（不同标签、批注、名牌、出处行、计数器之间）
        tx = [t for t in d["T"] if t["role"] in ("label", "pen", "tag", "source", "counter") and t["op"] > 0.3]
        for i, a in enumerate(tx):
            for b in tx[i + 1:]:
                if (a["rid"] and a["rid"] == b["rid"]) or (a["role"] == b["role"] == "source"):
                    continue
                ix = min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"])
                iy = min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"])
                if ix > 0 and iy > 0 and ix * iy > 100:
                    k = (a["rid"] or a["t"], "字:" + (b["rid"] or b["t"]))
                    hits.setdefault(k, (f, ix * iy))
    R["R08 标签压零件"] = (not hits, "标签、批注、名牌都没压在别的零件或字上" if not hits else
                       f"{len(hits)} 处：" + "；".join(f"“{k[0]}”压 {k[1]}（首见 f{v[0]}，最多 {v[1]} px²）" for k, v in list(hits.items())[:8]))
    # ④ G3 英雄件（18 的 1.3：显示高 ≥ 486 px）：页面用 hero 标了就量它，没标就量屏上最高的那个贴图（slab 不算）；取它在整段里的最大屏上高
    #    同时记下前景内容的外框（零件和字，不透明度 ≥ 0.5），算"整体放大 zoom 后不出画、不进字幕区"能放多大，给逐页那一轮用
    road = seg in LONG_ROAD
    thr = HERO_MIN_ROAD if road else HERO_MIN
    parts_h, gold_h, tag048_h, zl = {}, {}, {}, []
    flagged = False
    zx, zy = 960, 500
    for f, d in recs.items():
        own048 = {t.get("own") for t in d["T"] if t["t"].strip() == "048" and t.get("own")}
        fb = [1e9, 1e9, -1e9, -1e9]
        for q in d["P"]:
            if q["op"] < 0.5:
                continue
            if q["name"] != "slab":
                k = ("★" if q.get("hero") else "") + q["name"]
                flagged |= bool(q.get("hero"))
                parts_h[k] = max(parts_h.get(k, 0), q["h"])
            else:
                if q.get("sid") == "gold048" or q["pid"] in own048:
                    tag048_h["048 吊牌"] = max(tag048_h.get("048 吊牌", 0), q["h"])
                if (q.get("color") or "").upper() == "#E2CFA0":
                    k = "金色 Slab " + (q.get("sid") or "")
                    gold_h[k] = max(gold_h.get(k, 0), q["h"])
            inside = q["x"] >= 0 and q["y"] >= 0 and q["x"] + q["w"] <= 1920 and q["y"] + q["h"] <= 1080
            if inside and q["w"] * q["h"] < 0.4 * 1920 * 1080:
                fb = [min(fb[0], q["x"]), min(fb[1], q["y"]), max(fb[2], q["x"] + q["w"]), max(fb[3], q["y"] + q["h"])]
        for t in d["T"]:
            if t["op"] >= 0.5 and t["role"] != "source" and t["x"] >= 0 and t["x"] + t["w"] <= 1920:
                fb = [min(fb[0], t["x"]), min(fb[1], t["y"]), max(fb[2], t["x"] + t["w"]), max(fb[3], t["y"] + t["h"])]
        if fb[2] > fb[0]:
            zl.append(min((zx - 30) / max(1, zx - fb[0]), (1890 - zx) / max(1, fb[2] - zx), (zy - 30) / max(1, zy - fb[1]), (930 - zy) / max(1, fb[3] - zy)))
    if road and (tag048_h or gold_h):
        cand, how = (tag048_h, "金色 048 吊牌") if tag048_h else (gold_h, "页面没有 048 吊牌，取最高的金色 Slab")
    else:
        cand = {k: v for k, v in parts_h.items() if k.startswith("★")} if flagged else parts_h
        how = "页面标的" if flagged else ("长路页没有金色 Slab，取最高的贴图" if road else "没标，取最高的贴图")
    hero, hh = max(cand.items(), key=lambda kv: kv[1]) if cand else ("—", 0)
    zmax = round(max(1.0, min(zl)), 3) if zl else 1.0
    box = [0, 0, 0, 0]
    R["G3 英雄件"] = (hh >= thr, f"英雄件 {hero.lstrip('★')}（{how}）屏上最大 {hh} px（要 ≥ {thr}{'，长路页' if road else ''}，差 ×{thr / max(1, hh):.2f}）；"
                                    f"只算画内的件，前景整体放大最多 ×{zmax} 每一帧都不出画、不进字幕区")
    best_t = {}                                   # 每段字取它最清楚（不透明度最高、同分取最晚）的那一次扫描，带帧号，给量屏上字高用
    for f, d in sorted(recs.items()):
        for t in d["T"]:
            if t["role"] in ("label", "pen", "tag", "source") and t["op"] >= best_t.get((t["role"], t["t"]), {}).get("op", 0.5):
                best_t[(t["role"], t["t"])] = dict(t, f=f)
    (od / "probe_parts.json").write_text(json.dumps(dict(seg=seg, hero=hero.lstrip("★"), hero_h=hh, flagged=flagged, need_x=round(thr / max(1, hh), 3), threshold=thr, zoom_max=zmax, gold=gold_h,
                                                         parts=dict(sorted(parts_h.items(), key=lambda kv: -kv[1])[:8]),
                                                         text=list(best_t.values())), ensure_ascii=False, indent=1), encoding="utf-8")
    (od / "probe.json").write_text(json.dumps(dict(coverage_mean=round(float(cv.mean()), 4), coverage_min=round(float(cv.min()), 4), still_runs=runs, longest_still=longest, bad_font=[[*k, *v] for k, v in bad_font.items()],
                                                   bad_size=[[*k, *v] for k, v in bad_size.items()], crowd=crowd[:40],
                                                   overlap=[[*k, *v] for k, v in hits.items()], scans=len(recs)), ensure_ascii=False, indent=1), encoding="utf-8")


def sheet(seg, step=30):
    """快看：每 step 帧一张拼成一张大图（G:/cdk20/work/bcheck/<段>/quick.jpg）"""
    from PIL import Image, ImageDraw
    fs = sorted((FRAMES / safe(seg)).glob("element-*.jpeg"))
    picks = list(range(0, len(fs), step))
    cols, W, H = 6, 480, 270
    rows = (len(picks) + cols - 1) // cols
    sh = Image.new("RGB", (cols * W, rows * (H + 18)), (40, 40, 40))
    d = ImageDraw.Draw(sh)
    for k, i in enumerate(picks):
        x, y = (k % cols) * W, (k // cols) * (H + 18)
        sh.paste(Image.open(fs[i]).resize((W, H)), (x, y))
        d.text((x + 4, y + H + 2), f"f{i}", fill=(255, 255, 255))
    out = CHK / safe(seg) / "quick.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    sh.save(out, quality=85)
    print(out)


# ---------------------------------------------------------------- html
BATCHES = {1: ["5-10", "3-05", "5-01", "5-03", "5-08", "4-03", "8-03"],
           2: ["3-08", "4-01", "4-09", "4-10", "5-07", "1-04", "1-08", "1-11"],
           3: ["2-01", "2-05", "2-06", "2-07", "3-07", "4-02", "4-06", "4-07"],
           4: ["6-01", "6-02", "6-03", "6-06", "6-07", "6-08", "6-09", "7-02", "7-03", "7-04", "8-02"]}


def html(batch=1):
    import base64
    from PIL import Image
    import io
    order = BATCHES[batch]
    RV = review_dir(order[0])
    RV.mkdir(exist_ok=True)
    name = "第一批" if batch == 1 else f"第 {batch} 批"
    rows = []
    for seg in order:
        cj, rj = CHK / safe(seg) / "check.json", CHK / safe(seg) / "render.json"
        if not cj.exists():
            continue
        c = json.loads(cj.read_text(encoding="utf-8"))
        r = json.loads(rj.read_text(encoding="utf-8")) if rj.exists() else {}
        ok = all(v[0] for v in c["results"].values())
        imgs = []
        for p in c["sheets"]:
            im = Image.open(p)
            im.thumbnail((1400, 1400))
            b = io.BytesIO()
            im.save(b, "JPEG", quality=72)
            imgs.append(base64.b64encode(b.getvalue()).decode())
        res = "".join(f"<tr><td>{k}</td><td class={'ok' if v[0] else 'bad'}>{'过' if v[0] else '不过'}</td><td>{v[1]}</td></tr>" for k, v in c["results"].items())
        note = (BT / f"note_{safe(seg)}.txt")
        note_t = note.read_text(encoding="utf-8") if note.exists() else ""
        rows.append(f"""<section><h2>{seg} <small>{c['comp']} · {c['len_f']} 帧 · {c['len_f'] / 60:.1f} 秒 · {'全部通过' if ok else '有不过的项'}</small></h2>
<p class=meta>成片 <code>{RV.name}/14_B档_{seg}.mp4</code>　渲染：Remotion {r.get('remotion_s', '?')} 秒（{r.get('s_per_frame', '?')} 秒/帧，--gl=angle --concurrency=2），ffmpeg h264_nvenc {r.get('ffmpeg_s', '?')} 秒　背景第 {r.get('zones')} 区　擦除层 {r.get('wipes')}</p>
<p>{note_t}</p>
<table>{res}</table>
{''.join(f'<img src="data:image/jpeg;base64,{b}">' for b in imgs)}
</section>""")
    page = f"""<!doctype html><html lang=zh><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>B 档{name}检查</title>
<style>
:root{{--bg:#F3EEE6;--fg:#1F1E1C;--soft:#6E6B63;--ok:#5E8A64;--bad:#C8102E;--card:#FBF9F5}}
@media (prefers-color-scheme: dark){{:root:not([data-theme=light]){{--bg:#1E1E20;--fg:#F7F4EE;--soft:#9A968C;--card:#2a2a2c}}}}
:root[data-theme=dark]{{--bg:#1E1E20;--fg:#F7F4EE;--soft:#9A968C;--card:#2a2a2c}}
body{{background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,"Microsoft YaHei",sans-serif;margin:0;padding:24px 16px;max-width:1440px;margin:auto}}
h1{{font-size:26px}} h2{{font-size:21px;margin:0 0 6px}} small{{color:var(--soft);font-weight:400}}
section{{background:var(--card);border-radius:10px;padding:16px;margin:18px 0}}
table{{border-collapse:collapse;width:100%;margin:8px 0 12px}} td{{border-top:1px solid #8883;padding:5px 8px;vertical-align:top}}
td.ok{{color:var(--ok);font-weight:600;white-space:nowrap}} td.bad{{color:var(--bad);font-weight:600;white-space:nowrap}}
img{{max-width:100%;display:block;margin:6px 0;border-radius:4px}} code{{font-size:14px}} .meta{{color:var(--soft);font-size:14px}}
</style>
<h1>B 档{name} {len(order)} 页：抽帧和自检</h1>
<p>HKBU SCIE1007 课程作业的科普视频。B 档 = Remotion + SVG + GSAP；背景是 Blender 渲的虚化大板，零件是 Blender 渲的透明贴图。下面每页：自检结果、渲染时长、每 10 帧一张的抽帧（左上角是帧号）。</p>
{''.join(rows)}
</html>"""
    out = RV / ("14_B档_检查.html" if batch == 1 else f"{13 + batch}_B档第{batch}批_检查.html")
    out.write_text(page, encoding="utf-8")
    print("→", out)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "post":
        post()
    elif a[0] == "render":
        fr = next((x.split("=", 1)[1] for x in a if x.startswith("--frames=")), None)
        for s in [x for x in a[1:] if not x.startswith("--")]:
            render(s, fr)
    elif a[0] == "check":
        ok = all([check(s) for s in a[1:]])
        sys.exit(0 if ok else 1)
    elif a[0] == "probe":
        ok = True
        for sg in a[1:]:
            R = {}
            od = CHK / safe(sg)
            od.mkdir(parents=True, exist_ok=True)
            probe_checks(sg, R, od)
            for k, v in R.items():
                print(f"{'过  ' if v[0] else '不过'} {k}：{v[1]}")
            ok &= all(v[0] for v in R.values())
        sys.exit(0 if ok else 1)
    elif a[0] == "sheet":
        sheet(a[1], int(a[2]) if len(a) > 2 else 30)
    elif a[0] == "html":
        html(int(a[1]) if len(a) > 1 else 1)
    else:
        sys.exit(__doc__)
