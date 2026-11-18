"""HKBU SCIE1007 课程作业的科普视频：二维页面（说明书页 Manual、出镜页 OnCam）一段的准备、检查、出片，一条命令做完。

用法（项目根目录，任何 python 3.11 都行；跟踪那一步自己调 py -3.11）：
  python 镜头设计_v3/映射/page_tool.py prep  3-02          导出这段声音；出镜段再做人物跟踪、抠像序列、对时偏移
  python 镜头设计_v3/映射/page_tool.py check 3-02          validate + resolve + 拷 keys；渲整段 1080p；按事件落点抽静帧；找长静止；写报告
  python 镜头设计_v3/映射/page_tool.py check 3-02 --stills-only   不渲整段，只出静帧（用 remotion still，慢一点但省 CPU）

页面文件和合成名：说明书页 src/v3/manual/Manual<段号去横线>.jsx，合成 id 同名（3-02 → Manual302）；
出镜页 OnCam<第一段号去横线>.jsx（4-04+4-05 → OnCam404）。页面 import keys_<段>.json（说明书页）或 oncam_<段>.json（出镜页），段名里的 + 换成 _。
出：映射/_cache/pages/<合成>.mp4、映射/_cache/pages/<合成>/f<帧>.png、映射/_cache/pages/<合成>/report.md。不删任何东西。
"""
import json
import os
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
REM = ROOT / "镜头设计_v2/tests/T4_remotion"
MAN = REM / "src/v3/manual"
PUB = HERE / "_cache/ch1/public"           # 所有二维页面共用的 public 目录
OUT = HERE / "_cache/pages"
FF = str(ROOT / "_env/ffmpeg/ffmpeg.exe")
PLACE = ROOT / "素材流程_out"
TRACK = Path("G:/cdk20/work/track")
FLOW = ROOT / "镜头设计_v3/素材流程"
PY = sys.executable
# Remotion 每次渲染都把 6 G 的 public 复制成一个临时包，放 G 盘，旧包（3 小时以上）开跑前清掉
RTMP = Path("G:/cdk20/work/remotion_tmp")
RTMP.mkdir(parents=True, exist_ok=True)
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", TEMP=str(RTMP), TMP=str(RTMP))


def clean_bundles(hours=1):
    import time
    for d in list(RTMP.glob("remotion-webpack-bundle-*")) + list(RTMP.glob("tmp*")):
        if time.time() - d.stat().st_mtime > hours * 3600:
            shutil.rmtree(d, ignore_errors=True)
            print("  清旧临时包", d)


def group(name):
    m = json.loads((HERE / "master_v1.json").read_text(encoding="utf-8"))
    for g in m["groups"]:
        if g["group"] == name:
            return g
    sys.exit(f"总表里没有段 {name}")


def safe(name):
    return name.replace("+", "_")


def comp(name, g):
    first = g["segs"][0] if g.get("segs") else name
    return ("OnCam" if g["kind"] == "ON-CAM" else "Manual") + first.replace("-", "")


def _hl(a, b):
    try:
        os.link(a, b)
    except OSError:
        shutil.copy2(a, b)


def slim_public(name):
    """只含本段要用的东西的 public（声音、零件图、字体，加本段用到的 person_ 帧），
    用硬链接和目录联接搭在 G 盘，免得 Remotion 每次复制 6 G 的整个 public。"""
    d = RTMP.parent / "pub_slim" / safe(name)
    d.mkdir(parents=True, exist_ok=True)
    need = set()
    oc = MAN / f"oncam_{safe(name)}.json"
    if oc.exists():
        need = {f"person_{c['seg']}" for c in json.loads(oc.read_text(encoding="utf-8")).get("clips", [])}
    for e in PUB.iterdir():
        if e.name.startswith("person_") and e.name not in need:
            continue
        t = d / e.name
        if e.is_dir():                              # Remotion 复制时碰到联接会报 EPERM，目录要真复制（文件用硬链接）
            if t.is_junction():
                os.rmdir(t)
            shutil.copytree(e, t, dirs_exist_ok=True, copy_function=lambda a, b: None if Path(b).exists() and Path(b).stat().st_size == Path(a).stat().st_size else _hl(a, b))
        elif not t.exists() or t.stat().st_mtime < e.stat().st_mtime:
            if t.exists():
                t.unlink()
            try:
                os.link(e, t)
            except OSError:
                shutil.copy2(e, t)
    return d


def run(cmd, **kw):
    print("  $", " ".join(str(c) for c in cmd)[:200])
    if not any("remotion" in str(c) for c in cmd[:2]):
        return subprocess.run([str(c) for c in cmd], env=ENV, **kw)
    # 每次 Remotion 调用用自己的临时目录，跑完整个删掉（里面只有这次复制的 public 包）
    import tempfile
    t = Path(tempfile.mkdtemp(dir=RTMP))
    try:
        return subprocess.run([str(c) for c in cmd], env=dict(ENV, TEMP=str(t), TMP=str(t)), **kw)
    finally:
        import time
        for _ in range(5):                     # Chrome 退出慢，文件可能还锁着，等一下再删
            shutil.rmtree(t, ignore_errors=True)
            if not t.exists():
                break
            time.sleep(2)


# ---------- prep ----------
def prep(name):
    g = group(name)
    run([PY, HERE / "export_remotion.py", name], check=True, cwd=HERE)
    PUB.mkdir(parents=True, exist_ok=True)
    shutil.copy2(HERE / "_cache/remotion_public/map" / f"{safe(name)}.wav", PUB / f"{safe(name)}.wav")
    if g["kind"] != "ON-CAM":
        print(f"{name}：说明书页，声音已放到 public/{safe(name)}.wav")
        return
    for s in g["sources"]:
        seg, take = s["seg"], s["take"]
        if not (TRACK / f"{seg}_landmarks.json").exists():
            env = dict(ENV, PYTHONPATH=str(TRACK / "pydeps"))
            r = subprocess.run(["py", "-3.11", str(FLOW / "track_pose.py"), "clip", take], env=env, cwd=FLOW)
            if r.returncode:
                sys.exit(f"跟踪 {take} 失败")
        d = PUB / f"person_{seg}"
        if not d.exists() or not any(d.iterdir()):
            d.mkdir(parents=True, exist_ok=True)
            P = PLACE / take[0] / "5_place" / take
            run([FF, "-y", "-v", "error", "-i", f"{P}_fg.mp4", "-i", f"{P}_a.mp4", "-filter_complex",
                 "[1]format=gray[a];[0][a]alphamerge,scale=1728:972:flags=lanczos", "-start_number", "0", d / "%04d.png"], check=True)
    write_oncam(name)


def write_oncam(name):
    """oncam_<段>.json：clips（seg, off：段帧 = 素材帧 + off；cut：从这一帧起用这条；n：素材帧数）、nose、事件。"""
    g = group(name)
    words = g["words"]
    clips = []
    for i, s in enumerate(g["sources"]):
        seg = s["seg"]
        ws = [w for w in words if w["seg"] == seg and w.get("src")]
        off = round(statistics.median(w["f0"] - w["src"]["t0"] * 60 for w in ws))
        n = len(list((PUB / f"person_{seg}").glob("*.png")))
        if i == 0:
            cut = 0
        else:
            prev = [w for w in words if w["seg"] == g["sources"][i - 1]["seg"]]
            cut = max(off, (prev[-1]["f1"] + ws[0]["f0"]) // 2)
        clips.append(dict(seg=seg, off=off, cut=cut, n=n))
    end = min(g["len_f"], clips[-1]["off"] + clips[-1]["n"])
    nose = [None] * end
    for i, c in enumerate(clips):
        L = json.loads((TRACK / f"{c['seg']}_landmarks.json").read_text(encoding="utf-8"))["smoothed"]["nose"]
        nxt = clips[i + 1]["cut"] if i + 1 < len(clips) else end
        for f in range(c["cut"], nxt):
            k = f - c["off"]
            if 0 <= k < len(L):
                nose[f] = L[k]
    kp = HERE / "keys" / f"{safe(name)}.json"
    K = json.loads(kp.read_text(encoding="utf-8")) if kp.exists() else dict(events=[], words=[], sentences=[], len_f=g["len_f"])
    out = dict(group=name, len_f=end, len_f_group=g["len_f"], src=[3328, 1872], clips=clips, nose=nose,
               events=K.get("events", []), words=K.get("words", []), sentences=K.get("sentences", []))
    (MAN / f"oncam_{safe(name)}.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    miss = sum(p is None for p in nose)
    print(f"{name}：出镜，clips={clips}，出片 {end} 帧（段长 {g['len_f']}），缺头 {miss} 帧")


# ---------- check ----------
def check(name, stills_only=False):
    g = group(name)
    C = comp(name, g)
    page = MAN / f"{C}.jsx"
    if not page.exists():
        sys.exit(f"页面还没写：{page}")
    if run([PY, HERE / "validate_events.py", name], cwd=HERE).returncode:
        sys.exit("事件表没过 validate，先改事件表")
    run([PY, HERE / "resolve.py", name], check=True, cwd=HERE)
    K = json.loads((HERE / "keys" / f"{safe(name)}.json").read_text(encoding="utf-8"))
    shutil.copy2(HERE / "keys" / f"{safe(name)}.json", MAN / f"keys_{safe(name)}.json")
    if g["kind"] == "ON-CAM":
        write_oncam(name)
        L = json.loads((MAN / f"oncam_{safe(name)}.json").read_text(encoding="utf-8"))["len_f"]
    else:
        L = K["len_f"]
    od = OUT / C
    od.mkdir(parents=True, exist_ok=True)
    clean_bundles()
    marks = sorted({min(L - 1, e["f_land"] + 12) for e in K["events"]} | {L - 1})
    cli = [ "node", REM / "node_modules/@remotion/cli/remotion-cli.js"]
    rep = [f"# {C}（{name}）检查报告", "", f"段长 {L} 帧（{L / 60:.2f} 秒），事件 {len(K['events'])} 个。", ""]
    sp = slim_public(name)
    if stills_only:
        # 打包一次，所有静帧都从这个包出
        import tempfile
        b = Path(tempfile.mkdtemp(dir=RTMP)) / "bundle"
        if run(cli + ["bundle", f"src/v3/manual/{C}.jsx", f"--public-dir={sp}", f"--out-dir={b}", "--log=error"], cwd=REM).returncode:
            sys.exit("Remotion 打包出错，看上面的报错")
        try:
            for f in marks:
                run(cli + ["still", b, C, od / f"f{f:04d}.png", f"--frame={f}", "--log=error"], cwd=REM)
        finally:
            shutil.rmtree(b.parent, ignore_errors=True)
    else:
        fr = HERE / "_cache/ch2render" / f"fr_{C}"
        r = run(cli + ["render", f"src/v3/manual/{C}.jsx", C, fr, "--sequence", "--image-format=png", f"--public-dir={sp}", "--concurrency=6", "--log=error"], cwd=REM)
        if r.returncode:
            sys.exit("Remotion 渲染出错，看上面的报错（多半是页面代码写错）")
        first = sorted(os.listdir(fr))[0]
        digits = len("".join(ch for ch in first if ch.isdigit()))
        mp4 = OUT / f"{C}.mp4"
        run([FF, "-y", "-loglevel", "error", "-framerate", "60", "-i", fr / f"element-%0{digits}d.png", "-i", PUB / f"{safe(name)}.wav",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", "-c:a", "aac", "-b:a", "192k", "-shortest", ROOT / "_tmp" / mp4.name], check=True)
        shutil.move(ROOT / "_tmp" / mp4.name, mp4)          # ffmpeg 直接写 G 盘会被拒（_cache 在 G 盘），先写 D 盘再挪
        for f in marks:
            src = fr / f"element-{f:0{digits}d}.png"
            if src.exists():
                shutil.copy2(src, od / f"f{f:04d}.png")
        fz = subprocess.run([FF, "-hide_banner", "-i", str(mp4), "-vf", "freezedetect=n=0.0005:d=2.8", "-map", "0:v", "-f", "null", "-"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
        st = [ln.split("freeze_start: ")[1].strip() for ln in fz.splitlines() if "freeze_start" in ln]
        en = [ln.split("freeze_end: ")[1].strip() for ln in fz.splitlines() if "freeze_end" in ln]
        rep += [f"成片：`{mp4.relative_to(ROOT)}`", ""]
        if st:
            rep.append("**长静止（≥2.8 秒，不合格，要按旁白的词补事件）：**")
            for a, b in zip(st, en + ["段尾"] * (len(st) - len(en))):
                rep.append(f"- {a} 秒 到 {b} 秒")
        else:
            rep.append("长静止：没有（合格）")
    rep += ["", "静帧（每个事件落地后 12 帧，加最后一帧）："] + [f"- `{(od / f'f{f:04d}.png').relative_to(ROOT)}`" for f in marks]
    (od / "report.md").write_text("\n".join(rep) + "\n", encoding="utf-8")
    print("\n".join(rep))


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("prep", "check"):
        sys.exit(__doc__)
    if sys.argv[1] == "prep":
        prep(sys.argv[2])
    else:
        check(sys.argv[2], "--stills-only" in sys.argv)
