# HKBU SCIE1007 coursework video: AI mascot insert. TTS per line (edge-tts), then timeline.json with mouth envelopes at 60 fps.
import asyncio, json, subprocess, sys, os, struct
import edge_tts
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = "G:/cdk20/work/mascots/voice"
FF = "D:/software/TouchDesigner/bin/ffmpeg.exe"
FPS = 60
GAP = 0.25      # seconds between lines
LEAD = 1.1      # intro before first line
TAIL = 1.2

async def main():
    cfg = json.load(open(os.path.join(HERE, "lines.json"), encoding="utf-8"))
    os.makedirs(OUT, exist_ok=True)
    t = LEAD
    lines = []
    for ln in cfg["lines"]:
        v = cfg["voices"][ln["who"]]
        mp3 = f"{OUT}/{ln['id']}.mp3"
        await edge_tts.Communicate(ln["text"], v["voice"], rate=v["rate"], pitch=v["pitch"]).save(mp3)
        raw = subprocess.run([FF, "-v", "error", "-i", mp3, "-f", "s16le", "-ac", "1", "-ar", "16000", "-"], capture_output=True).stdout
        n = len(raw) // 2
        s = struct.unpack(f"<{n}h", raw[:n * 2])
        dur = n / 16000
        step = 16000 // FPS
        env = []
        for i in range(0, n - step + 1, step):
            seg = s[i:i + step]
            env.append((sum(x * x for x in seg) / len(seg)) ** 0.5 / 32768)
        mx = max(env) or 1
        env = [round(min(1.0, e / (mx * 0.7)), 3) for e in env]
        d = dict(ln); d.update(start=round(t, 3), dur=round(dur, 3), env=env, voice=v["voice"])
        lines.append(d)
        print(ln["id"], round(t, 2), round(dur, 2))
        t += dur + GAP
    total = t - GAP + TAIL
    json.dump({"fps": FPS, "total": round(total, 3), "lines": lines}, open(os.path.join(HERE, "data", "timeline.json"), "w"), ensure_ascii=False)
    # full mix (concat with silences) for muxing
    inputs, filt = [], []
    for i, d in enumerate(lines):
        inputs += ["-i", f"{OUT}/{d['id']}.mp3"]
        filt.append(f"[{i}:a]adelay={int(d['start']*1000)}|{int(d['start']*1000)},apad[a{i}]")
    mix = ";".join(filt) + ";" + "".join(f"[a{i}]" for i in range(len(lines))) + f"amix=inputs={len(lines)}:normalize=0,atrim=0:{total:.3f}[o]"
    subprocess.run([FF, "-y", "-v", "error"] + inputs + ["-filter_complex", mix, "-map", "[o]", "-ar", "48000", "-ac", "2", f"{OUT}/mix.wav"], check=True)
    print("total", total)
asyncio.run(main())
