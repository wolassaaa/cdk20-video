"""HKBU SCIE1007 coursework video: shared helpers for the phone-footage pipeline.

Paths, the bundled full ffmpeg, cache locations (all on D:, under _env/), low process priority,
and the per-step manifest that lets a rerun skip finished steps.
"""
import ctypes
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]                      # D:/。hkbu/molecular science
ENV = ROOT / "_env"
OUT = ROOT / "素材流程_out"
FFMPEG = str(ENV / "ffmpeg" / "ffmpeg.exe")
FFPROBE = str(ENV / "ffmpeg" / "ffprobe.exe")
SCRIPT_MD = ROOT / "镜头设计_v3" / "script" / "script_v3.3.md"
CONFIG = HERE / "config.json"
KEYS = ENV / "keys.env"

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".avi", ".3gp", ".mts", ".webm"}
AUDIO_EXT = {".m4a", ".wav", ".mp3", ".aac", ".flac", ".ogg", ".opus"}
CPU_THREADS = 4

# HLG / PQ -> Rec.709 8 bit (tried three on D's footage 11-12: this one keeps the window and the white shirt from blowing out)
SDR_VF = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,"
          "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")

STEP_DIRS = {0: "0_probe", 1: "1_ident", 2: "2_pick", 3: "3_audio", 4: "4_video", 5: "5_place", 6: "6_qc"}


def setup_env():
    """Caches on D:, at most 4 CPU threads, this process (and the children it starts) below normal priority."""
    cache = ENV / "cache"
    # set, not setdefault: this machine has HF_HOME / TORCH_HOME pointing at a drive that is not there
    os.environ["HF_HOME"] = str(cache / "hf")
    os.environ["HF_HUB_CACHE"] = os.environ["HUGGINGFACE_HUB_CACHE"] = str(cache / "hf" / "hub")
    os.environ["HF_HUB_DISABLE_XET"] = "1"          # the xet downloader fails on this path (os error 3)
    os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
    os.environ["TORCH_HOME"] = str(cache / "torch")
    os.environ["XDG_CACHE_HOME"] = str(cache / "xdg")
    os.environ["MPLCONFIGDIR"] = str(cache / "mpl")
    for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ.setdefault(k, str(CPU_THREADS))
    # ctranslate2 (faster-whisper) needs cuBLAS / cuDNN DLLs; the PyTorch wheel ships them in torch/lib
    tlib = Path(sys.prefix) / "Lib" / "site-packages" / "torch" / "lib"
    if tlib.exists() and str(tlib) not in os.environ.get("PATH", ""):
        os.environ["PATH"] = str(tlib) + os.pathsep + os.environ.get("PATH", "")
        try:
            os.add_dll_directory(str(tlib))
        except (OSError, AttributeError):
            pass
    if os.name == "nt":
        BELOW_NORMAL = 0x00004000  # child processes inherit this class
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), BELOW_NORMAL)
    for st in (sys.stdout, sys.stderr):
        if hasattr(st, "reconfigure"):
            st.reconfigure(encoding="utf-8")


def load_config():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def run(cmd, **kw):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
    if r.returncode != 0:
        raise RuntimeError(f"{Path(str(cmd[0])).name} failed: {r.stderr.strip()[-800:]}")
    return r


def ffmpeg(*args):
    """Run the full ffmpeg quietly with the CPU thread cap. Returns stderr (filters print their numbers there)."""
    return run([FFMPEG, "-hide_banner", "-nostdin", "-y", "-threads", str(CPU_THREADS), *args]).stderr


def ffprobe_json(path, *args):
    return json.loads(run([FFPROBE, "-v", "error", *args, "-of", "json", str(path)]).stdout)


def gpu_free_mb():
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True).stdout
        return int(out.split()[0])
    except Exception:
        return None


def wait_for_gpu(need_mb=6000, tries=30, pause=20):
    """Before heavy GPU work: wait until at least need_mb is free (someone else may be rendering)."""
    for _ in range(tries):
        free = gpu_free_mb()
        if free is None or free >= need_mb:
            return free
        print(f"  显存只空 {free} MB，不到 {need_mb} MB，等 {pause} 秒再看")
        time.sleep(pause)
    raise RuntimeError("显存一直不够，先停下")


def media_files(folder):
    """Media files of one person's folder, videos then recordings. Other files (names etc.) are never read."""
    fs = [p for p in sorted(Path(folder).iterdir()) if p.is_file()]
    return ([p for p in fs if p.suffix.lower() in VIDEO_EXT], [p for p in fs if p.suffix.lower() in AUDIO_EXT])


def stat_of(p):
    s = Path(p).stat()
    return {"file": str(p), "size": s.st_size, "mtime": int(s.st_mtime)}


def fingerprint(inputs, params):
    blob = json.dumps({"in": [stat_of(p) for p in inputs], "params": params}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def read_manifest(step_dir):
    f = Path(step_dir) / "manifest.json"
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_manifest(step_dir, step, inputs, params, outputs, seconds):
    m = {
        "step": step,
        "finished": time.strftime("%Y-%m-%d %H:%M:%S") + " 韩国时间（机器时钟）",
        "seconds": round(seconds, 1),
        "fingerprint": fingerprint(inputs, params),
        "params": params,
        "inputs": [stat_of(p) for p in inputs],
        "outputs": sorted(str(Path(o).relative_to(step_dir)).replace("\\", "/") for o in outputs),
    }
    write_json(Path(step_dir) / "manifest.json", m)
    return m


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")


def write_text(path, text):
    Path(path).write_text(text, encoding="utf-8", newline="\n")


def imread(path):
    """cv2.imread that works with the non-ASCII characters in this project's path."""
    import cv2
    import numpy as np
    return cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)


def imwrite(path, img, quality=90):
    import cv2
    ext = Path(path).suffix
    ok, buf = cv2.imencode(ext, img, [cv2.IMWRITE_JPEG_QUALITY, quality] if ext.lower() in (".jpg", ".jpeg") else [])
    buf.tofile(str(path))
    return ok
