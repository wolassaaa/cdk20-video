"""HKBU SCIE1007 课程作业的科普视频：零件库的批量预渲染（透明底），给二维说明书页和人出镜旁边的图形用。

    blender -b --factory-startup -P kit_batch.py -- flat  [编号,编号…|all|hero]   正上方的零件图 1 张（线稿由 Remotion 从透明通道描边，Freestyle 在 5.3 的 Cycles 下出不了线）
    blender -b --factory-startup -P kit_batch.py -- turn  [编号,编号…|all|hero]   转台 4 秒 240 帧（60 fps，首尾相接）
    blender -b --factory-startup -P kit_batch.py -- status                       只打印进度，不渲染

断点续渲：已经有的帧跳过，重跑是安全的。进度写在 OUT/progress.json，`status` 会打印成表。
显卡暂停（C:/Users/woola/cdk20_guard/GPU_PAUSED 存在）时，渲完当前帧就退出。
"""
import bpy, sys, os, json, math, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_parts as KP

OUT = "G:/cdk20/work/kit"
PAUSE = "C:/Users/woola/cdk20_guard/GPU_PAUSED"
HERO = ["01", "02", "03", "04", "19", "20", "21", "22", "23", "24", "29", "30", "31", "32", "39", "40"]   # 要拍三维近景的 16 种
TURN_FRAMES = 240
SLUG = {no: f"{no}_{name.split(',')[0].split('(')[0].strip().lower().replace(' ', '-').replace('/', '-')}" for no, name, _ in KP.CATALOG}


def pick(arg):
    if arg in (None, "all"):
        return [c[0] for c in KP.CATALOG]
    if arg == "hero":
        return HERO
    return [a.zfill(2) for a in arg.split(",")]


def progress():
    p = os.path.join(OUT, "progress.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def note(kind, no, done, total):
    d = progress()
    d.setdefault(kind, {})[no] = {"done": done, "total": total, "at": time.strftime("%m-%d %H:%M")}
    with open(os.path.join(OUT, "progress.json"), "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


def stage(no, samples):
    """清场，只放这一种零件（不带格子框和浇口），透明底。返回场景、零件根、零件占的半宽（mm）。"""
    sc = KP.scene_base(samples)
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGBA"
    sc.render.use_persistent_data = True
    K = KP.Kit()
    gen = next(c[2] for c in KP.CATALOG if c[0] == no)
    part = gen(K)
    nx, ny = part.get("span", (1, 1))
    half = max(KP.CX + (nx - 1) * KP.PX / 2, KP.CY + (ny - 1) * KP.PY / 2) + 4
    KP.lights(0, 0, 0.6)
    return sc, part, half


def do_flat(no):
    d = os.path.join(OUT, "flat"); os.makedirs(d, exist_ok=True)
    f_col = os.path.join(d, SLUG[no] + "_color.png")
    if os.path.exists(f_col):
        note("flat", no, 1, 1); return
    sc, part, half = stage(no, 128)
    sc.render.resolution_x = sc.render.resolution_y = 1536
    KP.camera(sc, (0, 0, 0), 0.6, 89.9, 0, ortho=2 * half * KP.MM)
    if not os.path.exists(f_col):
        KP.render(sc, f_col, 100)
    note("flat", no, 1, 1)


def do_turn(no):
    d = os.path.join(OUT, "turn", SLUG[no]); os.makedirs(d, exist_ok=True)
    todo = [f for f in range(TURN_FRAMES) if not os.path.exists(os.path.join(d, f"{f:04d}.png"))]
    note("turn", no, TURN_FRAMES - len(todo), TURN_FRAMES)
    if not todo:
        return
    sc, part, half = stage(no, 64)
    sc.render.resolution_x = sc.render.resolution_y = 1080
    sc.render.fps = 60
    KP.camera(sc, (0, 0, 0.004), half * KP.MM * 5.2, 32, 0, lens=85)
    piv = bpy.data.objects.new("turn_pivot", None); bpy.context.collection.objects.link(piv)
    part.parent = piv
    for i, f in enumerate(todo):
        if os.path.exists(PAUSE):
            print("GPU paused: stop after", f); break
        piv.rotation_euler = (0, 0, 2 * math.pi * f / TURN_FRAMES)
        sc.frame_set(f)
        KP.render(sc, os.path.join(d, f"{f:04d}.png"), 100)
        if i % 20 == 19:
            note("turn", no, TURN_FRAMES - len(todo) + i + 1, TURN_FRAMES)
    left = sum(1 for f in range(TURN_FRAMES) if not os.path.exists(os.path.join(d, f"{f:04d}.png")))
    note("turn", no, TURN_FRAMES - left, TURN_FRAMES)


def status():
    d = progress()
    for kind in ("flat", "turn"):
        rows = d.get(kind, {})
        done = sum(r["done"] for r in rows.values()); total = sum(r["total"] for r in rows.values())
        print(f"{kind}: {len(rows)} parts, {done}/{total} frames")
        for no in sorted(rows):
            r = rows[no]
            if r["done"] < r["total"]:
                print(f"   {SLUG[no]}: {r['done']}/{r['total']}  ({r['at']})")


if __name__ == "__main__" and "--" in sys.argv:
    a = sys.argv[sys.argv.index("--") + 1:]
    os.makedirs(OUT, exist_ok=True)
    if a[0] == "status":
        status()
    else:
        for no in pick(a[1] if len(a) > 1 else None):
            if os.path.exists(PAUSE):
                print("GPU paused: not starting", no); break
            t = time.time()
            (do_flat if a[0] == "flat" else do_turn)(no)
            print(f"[kit_batch] {a[0]} {SLUG[no]} {time.time() - t:.1f}s", flush=True)
