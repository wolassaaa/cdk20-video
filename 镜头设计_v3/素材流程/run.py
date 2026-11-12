"""HKBU SCIE1007 coursework video: one-command entry of the phone-footage pipeline.

    _env/footage/Scripts/python.exe 镜头设计_v3/素材流程/run.py 人员素材啊/D [--steps 0,1] [--force]

Runs the steps in order. Each step writes its products and a manifest.json into
素材流程_out/<person>/<step>/ and is skipped when its inputs and settings have not changed.
Originals in the person's folder are only ever read.
"""
import argparse
import importlib
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as C  # noqa: E402

STEPS = {
    0: ("steps.s0_probe", "量规格"),
    1: ("steps.s1_ident", "认片"),
    2: ("steps.s2_pick", "选条"),
    3: ("steps.s3_audio", "声音"),
    4: ("steps.s4_video", "画面"),
    5: ("steps.s5_place", "上片"),
    6: ("steps.s6_qc", "质检"),
}


class Ctx:
    """What a step gets: the person's folder, the output folders, the settings."""

    def __init__(self, folder, cfg):
        self.src = Path(folder).resolve()
        self.person = self.src.name
        self.cfg = cfg
        self.out = C.OUT / self.person
        self.videos, self.audios = C.media_files(self.src)

    def dir(self, step):
        d = self.out / C.STEP_DIRS[step]
        d.mkdir(parents=True, exist_ok=True)
        return d


def main():
    C.setup_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", help="一个人的素材文件夹，比如 人员素材啊/D")
    ap.add_argument("--steps", default="0,1,2,3,4,5,6")
    ap.add_argument("--force", action="store_true", help="不管清单，重跑")
    a = ap.parse_args()
    folder = Path(a.folder)
    if not folder.is_absolute():
        folder = C.ROOT / folder
    if not folder.is_dir():
        sys.exit(f"找不到文件夹：{folder}")
    ctx = Ctx(folder, C.load_config())
    print(f"{ctx.person}：{len(ctx.videos)} 条视频，{len(ctx.audios)} 条录音 → {ctx.out}")

    for n in sorted(int(x) for x in a.steps.split(",") if x.strip()):
        modname, label = STEPS[n]
        mod = importlib.import_module(modname)
        if not hasattr(mod, "run"):
            print(f"[{n} {label}] 还没做")
            continue
        d = ctx.dir(n)
        inputs, params = mod.inputs(ctx), mod.params(ctx)
        old = C.read_manifest(d)
        if (old and not a.force and old.get("fingerprint") == C.fingerprint(inputs, params)
                and all((d / o).exists() for o in old.get("outputs", []))):
            print(f"[{n} {label}] 输入和参数没变，跳过（上次 {old['finished']}，用了 {old['seconds']} 秒）")
            continue
        print(f"[{n} {label}] 开始 {time.strftime('%H:%M:%S')}")
        t = time.time()
        outputs = mod.run(ctx, d)
        C.write_manifest(d, f"{n} {label}", inputs, params, outputs, time.time() - t)
        print(f"[{n} {label}] 完成，{time.time() - t:.0f} 秒，{len(outputs)} 个产物")


if __name__ == "__main__":
    main()
