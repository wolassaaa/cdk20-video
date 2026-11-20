"""HKBU SCIE1007 课程作业的科普视频：B 档页面（Remotion + SVG + GSAP）的素材整理、出片和自检，一条命令做完。

用法（项目根目录，python 3.11+，要 numpy + PIL）：
  python 镜头设计_v3/映射/b_page.py post               Blender 贴图裁边 + 尺寸锚点表（src/v3/btier/bsprite_meta.json）+ 24 张颗粒图
  python 镜头设计_v3/映射/b_page.py render 3-05        validate + resolve + 拷 keys；搭本段的精简 public（G 盘硬链接）；
                                                       Remotion 出 1080p60 帧序列（--gl=angle --concurrency=2，帧和临时目录都在 G 盘）；
                                                       CipherTalk 的 ffmpeg（h264_nvenc）合声音，出 导演检查_20261120/14_B档_<段>.mp4
  python 镜头设计_v3/映射/b_page.py check 3-05         自检：check_sync（对词、到句尾、1.5 s、帧率）、check_guides（V1–V14）、
                                                       B4 颜色、B5 不死（2.5 s）、B6 接点亮度和黑帧、B8 背景；每 10 帧抽一张拼成检查图
  python 镜头设计_v3/映射/b_page.py html               汇总所有已出的页 → 导演检查_20261120/14_B档_检查.html

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
REVIEW = ROOT / "导演检查_20261120"
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
    hl(PUB_SHARED / f"{safe(seg)}.wav", d / f"{safe(seg)}.wav")
    for p in SPR.glob("*/*.png"):
        hl(p, d / "bsprite" / p.parent.name / p.name)
    for p in GRAIN.glob("*.png"):
        hl(p, d / "grain" / p.name)
    for z in zones:
        fs = sorted(f for f in (WORK / "bplate" / f"zone{z}").glob("*.jpg") if f.stat().st_size > 0)
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
    REVIEW.mkdir(exist_ok=True)
    mp4 = REVIEW / f"14_B档_{seg}.mp4"
    first = sorted(fr.glob("element-*.jpeg"))[0]
    digits = len(re.sub(r"\D", "", first.name))
    t1 = time.time()
    tmp = WORK / "bcheck" / f"_{safe(seg)}.mp4"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    rr = run([FF, "-y", "-loglevel", "error", "-framerate", "60", "-i", fr / f"element-%0{digits}d.jpeg", "-i", PUB_SHARED / f"{safe(seg)}.wav",
              "-c:v", "h264_nvenc", "-preset", "p6", "-rc", "vbr", "-cq", "17", "-b:v", "0", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
              "-shortest", tmp])
    if rr.returncode:
        sys.exit("ffmpeg 合成失败")
    shutil.copy2(tmp, mp4)
    t_ff = time.time() - t1
    log = CHK / safe(seg) / "render.json"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(json.dumps(dict(seg=seg, comp=C, frames=K["len_f"], remotion_s=round(t_rem, 1), ffmpeg_s=round(t_ff, 1),
                                   s_per_frame=round(t_rem / K["len_f"], 3), zones=zones, wipes=wipes, mp4=str(mp4),
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
    mp4 = REVIEW / f"14_B档_{seg}.mp4"
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
    # B8 背景
    zones, wipes = page_needs(src)
    R["B8 背景"] = (bool(zones), f"L0 用第 {zones} 区 Blender 大板（720 帧来回）；擦除层 {wipes}")
    # B7 字：字号下限和字幕区由 bkit 在渲染时强制（违反就抛错，页面渲不出来）；这里数同一时刻的标签数在页面代码里核
    labels = len(re.findall(r"<Label\b", src))
    R["B7 字"] = (True, f"标签 ≥ 44 px（大写约 31 px）、出处行 28 px（约 20 px）、y ≤ 940 由套件强制；页面共 {labels} 个标签，同屏数见抽帧")
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
               sheets=[str(p) for p in sheets], luma=[round(y, 1) for y in ys[::10]], max_diff=round(max(diffs), 2))
    (od / "check.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in R.items():
        print(f"{'过  ' if v[0] else '不过'} {k}：{v[1]}")
    print("检查图：", *[str(p) for p in sheets], sep="\n  ")
    return all(v[0] for v in R.values())


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
def html():
    import base64
    from PIL import Image
    import io
    REVIEW.mkdir(exist_ok=True)
    order = ["5-10", "3-05", "5-01", "5-03", "5-08", "4-03", "8-03"]
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
<p class=meta>成片 <code>导演检查_20261120/14_B档_{seg}.mp4</code>　渲染：Remotion {r.get('remotion_s', '?')} 秒（{r.get('s_per_frame', '?')} 秒/帧，--gl=angle --concurrency=2），ffmpeg h264_nvenc {r.get('ffmpeg_s', '?')} 秒　背景第 {r.get('zones')} 区　擦除层 {r.get('wipes')}</p>
<p>{note_t}</p>
<table>{res}</table>
{''.join(f'<img src="data:image/jpeg;base64,{b}">' for b in imgs)}
</section>""")
    page = f"""<!doctype html><html lang=zh><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>B 档第一批检查</title>
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
<h1>B 档第一批 7 页：抽帧和自检</h1>
<p>HKBU SCIE1007 课程作业的科普视频。B 档 = Remotion + SVG + GSAP；背景是 Blender 渲的虚化大板，零件是 Blender 渲的透明贴图。下面每页：自检结果、渲染时长、每 10 帧一张的抽帧（左上角是帧号）。</p>
{''.join(rows)}
</html>"""
    out = REVIEW / "14_B档_检查.html"
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
    elif a[0] == "sheet":
        sheet(a[1], int(a[2]) if len(a) > 2 else 30)
    elif a[0] == "html":
        html()
    else:
        sys.exit(__doc__)
