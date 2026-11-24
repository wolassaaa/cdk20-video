# -*- coding: utf-8 -*-
"""HKBU SCIE1007 课程作业的科普视频：音乐段 W2 / W3（新模板重做）的合成。

设计：镜头设计_v3/深化/20_W2W3新模板重做.md 第七节。
  W2：Blender 帧 G:/cdk20/work/drill/W2/frames/f_%04d.png
      + 押韵字幕和出处行层（Remotion 合成 W2LyricsLayer，透明 PNG 序列 → G:/cdk20/work/drill/W2/lyr/）
      + 音轨 -c:a copy 取自 导演检查_20261123/24_W2_加工.mp4
      → 导演检查_20261124/03_W2_重做.mp4
  W3（接口，W3 施工方按自己的配方改 SEGS["W3"]）：Blender 帧 + W3SrcStill 一张 PNG + 24_W3_加工.mp4 的声音
      → 导演检查_20261124/04_W3_重做.mp4

文档写的是 comp_gpu.py 的 torch 两进程叠层；这里只有两层不透明底 + 一层 alpha，ffmpeg overlay 一条命令就够（W2 施工方替导演定，可改回）。
编码 h264_nvenc cq16（和 shot_drill.encode 同参数）；不加 -shortest（会丢最后一帧），用 -frames:v 卡帧数。
用 G:/cdk20/work/jg1123/bin/ffmpeg.exe（有 nvenc 和 aac，能写导演检查文件夹），先写 _tmp.mp4 再改名。

用法（项目根目录下，Git Bash）：
  PYTHONIOENCODING=utf-8 python 镜头设计_v3/inserts/comp_w23.py W2            # 渲字幕层（缺才渲）+ 合成
  PYTHONIOENCODING=utf-8 python 镜头设计_v3/inserts/comp_w23.py W2 --layer    # 只渲字幕层
  PYTHONIOENCODING=utf-8 python 镜头设计_v3/inserts/comp_w23.py W2 --relayer  # 字幕层重渲后合成
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(os.environ.get("CDK20_WORK", "G:/cdk20/work"))
FF = os.environ.get("COMP_FF", "G:/cdk20/work/jg1123/bin/ffmpeg.exe")
REMO = ROOT / "镜头设计_v2/tests/T4_remotion"
PUBLIC = ROOT / "镜头设计_v3/remotion_public"
OUT_DIR = ROOT / "导演检查_20261124"
AUD_DIR = ROOT / "导演检查_20261123"

SEGS = {
    "W2": dict(frames=WORK / "drill/W2/frames", n=1500, dur=25.0,
               layer=dict(comp="W2LyricsLayer", seq=True, out=WORK / "drill/W2/lyr", props='{"t0":0.083}'),
               audio=AUD_DIR / "24_W2_加工.mp4", out=OUT_DIR / "03_W2_重做.mp4"),
    # W3 接口：施工方确认帧数、输出名后改这里。出处行是一张静图（W3SrcStill），整段叠同一张。
    "W3": dict(frames=WORK / "drill/W3/frames", n=900, dur=15.0,
               layer=dict(comp="W3SrcStill", seq=False, out=WORK / "drill/W3/src.png", props=None),
               audio=AUD_DIR / "24_W3_加工.mp4", out=OUT_DIR / "04_W3_重做.mp4",
               # W3 施工方（11-24）：出处行 0.3 s 起 0.5 s 淡入（20 号第四节、和 11-23 加工版同写法）；src.png 已从 jg1123/w3src.png（同一个 W3SrcStill）拷好，缺了才重渲
               fade=(0.3, 0.5)),
}


def bundle(seg):
    b = WORK / f"drill/{seg}/rbundle"
    if not (b / "index.html").exists():
        subprocess.run(["node", "node_modules/@remotion/cli/remotion-cli.js", "bundle", "src/v3/fusion/entry.jsx",
                        f"--out-dir={b}", f"--public-dir={PUBLIC}", "--log=error"], cwd=REMO, check=True,
                       env=dict(os.environ, TEMP="D:/render_tmp", TMP="D:/render_tmp"))
    return b


def render_layer(seg, force=False):
    L = SEGS[seg]["layer"]
    out = Path(L["out"])
    if not force:
        if L["seq"] and out.exists() and len(list(out.glob("*.png"))) >= SEGS[seg]["n"]:
            return out
        if not L["seq"] and out.exists():
            return out
    b = bundle(seg)
    cli = ["node", "node_modules/@remotion/cli/remotion-cli.js"]
    if L["seq"]:
        out.mkdir(parents=True, exist_ok=True)
        cmd = cli + ["render", str(b), L["comp"], str(out), "--sequence", "--image-format=png", "--concurrency=6", "--log=error"]
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        cmd = cli + ["still", str(b), L["comp"], str(out), "--image-format=png", "--log=error"]
    if L["props"]:
        cmd.append(f"--props={L['props']}")
    subprocess.run(cmd, cwd=REMO, check=True, env=dict(os.environ, TEMP="D:/render_tmp", TMP="D:/render_tmp"))
    return out


def seq_pattern(d):
    """Remotion 的序列名 element-0000.png（位数随总帧数），找出来拼成 ffmpeg 的 %0Nd。"""
    fs = sorted(Path(d).glob("*.png"))
    if not fs:
        raise SystemExit(f"{d} 里没有 PNG")
    stem = fs[0].stem
    i = len(stem)
    while i and stem[i - 1].isdigit():
        i -= 1
    return str(Path(d) / f"{stem[:i]}%0{len(stem) - i}d.png"), int(stem[i:])


def comp(seg):
    S = SEGS[seg]
    fr = Path(S["frames"])
    have = len(list(fr.glob("f_*.png")))
    if have < S["n"]:
        raise SystemExit(f"{seg} 帧不全：{have}/{S['n']}，先等渲染")
    lay = render_layer(seg)
    ins = ["-framerate", "60", "-start_number", "0", "-i", str(fr / "f_%04d.png")]
    if S["layer"]["seq"]:
        pat, st = seq_pattern(lay)
        ins += ["-framerate", "60", "-start_number", str(st), "-i", pat]
    else:
        ins += ["-loop", "1", "-framerate", "60", "-i", str(lay)]
    ins += ["-i", str(S["audio"])]
    tmp = S["out"].with_name(S["out"].stem + "_tmp.mp4")
    cmd = [FF, "-y", "-v", "error"] + ins + [
        "-filter_complex", (f"[1:v]format=rgba,fade=t=in:st={S['fade'][0]}:d={S['fade'][1]}:alpha=1[s];[0:v][s]overlay=0:0:shortest=1:format=auto,format=yuv420p[v]"
                            if S.get("fade") else "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v]"),
        "-map", "[v]", "-map", "2:a", "-frames:v", str(S["n"]),
        "-c:v", "h264_nvenc", "-preset", "p7", "-tune", "hq", "-rc", "vbr", "-cq", "16", "-b:v", "0", "-maxrate", "60M",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-r", "60", "-c:a", "copy", "-t", f"{S['dur']:.3f}", "-movflags", "+faststart", str(tmp)]
    print("COMP", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)
    if S["out"].exists():                     # 导演检查文件夹不删东西：旧版改名留存
        k = 1
        while S["out"].with_name(f"{S['out'].stem}_旧{k}.mp4").exists():
            k += 1
        os.replace(S["out"], S["out"].with_name(f"{S['out'].stem}_旧{k}.mp4"))
    os.replace(tmp, S["out"])
    print("COMP done", S["out"], flush=True)


if __name__ == "__main__":
    seg = sys.argv[1] if len(sys.argv) > 1 else "W2"
    if "--layer" in sys.argv:
        render_layer(seg, force=True)
    else:
        if "--relayer" in sys.argv:
            render_layer(seg, force=True)
        comp(seg)
