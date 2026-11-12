"""HKBU SCIE1007 coursework video: picture restoration for members whose phone smeared the image (step 4, after matting).

    _env/footage/Scripts/python.exe 镜头设计_v3/素材流程/restore.py B

Who gets it is set in config.json, video.restore (director, 11-13: B only; A's phone is the quality reference, D next,
C reshoots). The member's <name>_std.mp4 from step 4 is read whole, each frame is halved, run through
Real-ESRGAN x2plus back to full size (blotches from the phone's own noise reduction go, edges of eyes, teeth and
hair come back; picked from a six-way comparison on B), and written as <name>_stdr.mp4 with the same frame count.
The matte from step 4 still fits (same frame grid, geometry untouched), so nothing is re-matted. index.json gets
"std_restored" per clip; step 5 uses it when present. Everything heavy runs on the 5080; nothing else should use the
card meanwhile. Clips already done with the same settings are skipped.
"""
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as C  # noqa: E402

MODELS = {"x2plus_half": ("RealESRGAN_x2plus.pth", 0.5)}        # weights in _env/cache/sr, scale applied before the model
FPS = 60


def main():
    C.setup_env()
    import torch
    import torch.nn.functional as F
    from spandrel import ModelLoader
    person = sys.argv[1]
    cfg = C.load_config()["video"]
    how = cfg.get("restore", {}).get(person)
    if not how:
        sys.exit(f"{person} 不在 config.json 的 video.restore 里，不做修复")
    weights, pre = MODELS[how]
    out = C.OUT / person / C.STEP_DIRS[4]
    index = C.read_json(out / "index.json")
    model = ModelLoader().load_from_file(str(C.ENV / "cache" / "sr" / weights)).cuda().eval().half()
    to_y = torch.tensor([0.2126, 0.7152, 0.0722], device="cuda").view(1, 3, 1, 1)
    for c in index["clips"]:
        W, H = c["size"]
        src, dst = out / c["std"], out / c["std"].replace("_std.mp4", "_stdr.mp4")
        stamp = {"how": how, "src_size": src.stat().st_size}
        if c.get("restore_stamp") == stamp and dst.exists():
            print(f"  {c['name']:16} 已修复过，跳过")
            continue
        t0 = time.time()
        reader = subprocess.Popen([C.FFMPEG, "-v", "error", "-hwaccel", "cuda", "-i", str(src), "-an", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                  stdout=subprocess.PIPE, bufsize=W * H * 3)
        writer = subprocess.Popen([C.FFMPEG, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{W}x{H}", "-r", str(FPS),
                                   "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv", "-i", "-",
                                   "-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", "19", "-b:v", "0", "-pix_fmt", "yuv420p",
                                   "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
                                   "-movflags", "+faststart", str(dst)], stdin=subprocess.PIPE)
        n = 0
        while True:
            buf = reader.stdout.read(W * H * 3)
            if len(buf) < W * H * 3:
                break
            with torch.inference_mode():
                x = torch.frombuffer(bytearray(buf), dtype=torch.uint8).cuda().view(H, W, 3).permute(2, 0, 1)[None].float() / 255
                y = model(F.interpolate(x, scale_factor=pre, mode="area").half()).float().clamp(0, 1)
                if y.shape[-2:] != (H, W):
                    y = F.interpolate(y, size=(H, W), mode="bicubic", antialias=True).clamp(0, 1)
                yp = (y * to_y).sum(1, keepdim=True)
                cb = F.avg_pool2d((y[:, 2:3] - yp) / 1.8556, 2)
                cr = F.avg_pool2d((y[:, 0:1] - yp) / 1.5748, 2)
                data = b"".join(p.round().clamp(0, 255).byte().cpu().numpy().tobytes() for p in (16 + 219 * yp, 128 + 224 * cb, 128 + 224 * cr))
            writer.stdin.write(data)
            n += 1
        reader.wait()
        writer.stdin.close()
        writer.wait()
        ok = n == c["frames"]
        c["std_restored"] = dst.name if ok else None
        c["restore_stamp"] = stamp if ok else None
        c["restore"] = {"how": how, "frames": n, "seconds": round(time.time() - t0, 1), "ms_per_frame": round((time.time() - t0) * 1000 / max(1, n))}
        C.write_json(out / "index.json", index)
        print(f"  {c['name']:16} {n} 帧 {time.time() - t0:.0f} 秒（每帧 {c['restore']['ms_per_frame']} 毫秒）  {'过' if ok else f'没过：帧数 {n}，应有 ' + str(c['frames'])}", flush=True)
    done = sum(1 for c in index["clips"] if c.get("std_restored"))
    print(f"{person}：{done}/{len(index['clips'])} 条修复好了")


if __name__ == "__main__":
    main()
