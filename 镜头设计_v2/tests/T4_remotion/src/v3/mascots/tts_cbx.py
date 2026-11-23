# HKBU SCIE1007 coursework video: AI mascot insert v2. Chatterbox TTS (GPU) for the three AI characters.
# Runs in the separate venv $CDK20_WORK/tts/cbx (not system Python), with HF_HOME=$CDK20_WORK/tts/hf:
#   python tts_cbx.py cand                       -> voice candidates (same test line per character, 3 refs x 2 takes)
#   python tts_cbx.py trial c2 en-GB-SoniaNeural -1 0.9 0.35 sonia_ex09   -> one line at one setting
#   python tts_cbx.py lines [c1,g2]              -> every line (or listed ids), TAKES takes each; then pick_takes.py
import json, os, sys, subprocess
import torch, torchaudio
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ.get("CDK20_WORK", "D:/cdk20_work")
LINES_FILE = os.environ.get("LINES", "lines.json")
OUT = os.environ.get("VOICE_OUT", f"{WORK}/mascots/voice_v2")
REFS = f"{OUT}/refs"
FF = os.environ.get("CDK20_FFMPEG", "D:/software/TouchDesigner/bin/ffmpeg.exe")
TAKES = 4

# candidate refs per character (edge-tts clips used only as timbre prompts; Chatterbox does the acting)
CAND = {  # director 11-21: Claude and GPT mature, composed (yujie); DeepSeek bright, lively girl
    "Claude": [("sonia_dn1", "en-GB-SoniaNeural", -1.0), ("ava_dn1", "en-US-AvaNeural", -1.0), ("aria_dn15", "en-US-AriaNeural", -1.5)],
    "GPT": [("michelle_dn1", "en-US-MichelleNeural", -1.0), ("jenny_dn15", "en-US-JennyNeural", -1.5), ("clara_dn1", "en-CA-ClaraNeural", -1.0)],
    "DeepSeek": [("libby_up15", "en-GB-LibbyNeural", 1.5), ("molly_up1", "en-NZ-MollyNeural", 1.0), ("natasha_up15", "en-AU-NatashaNeural", 1.5)],
}
TEST = {"Claude": "c2", "GPT": "g2", "DeepSeek": "d3"}


def ref_wav(voice, st):
    """mp3 -> 24 kHz mono wav, optional pitch shift in semitones (resample trick keeps tempo via atempo)."""
    os.makedirs(REFS, exist_ok=True)
    dst = f"{REFS}/{voice}_{st:+.1f}.wav"
    if not os.path.exists(dst):
        mp3 = f"{REFS}/{voice}.mp3"
        if not os.path.exists(mp3):
            alt = f"{WORK}/mascots/voice_v2/refs/{voice}.mp3"
            if os.path.exists(alt):
                mp3 = alt
            else:
                import asyncio, edge_tts
                asyncio.run(edge_tts.Communicate(
                    "Hello everyone, let's look closely at the real experimental data together.",
                    voice
                ).save(mp3))
        f = "aresample=24000"
        if st:
            r = 2 ** (st / 12)
            f = f"asetrate={int(24000 * r)},aresample=24000,atempo={1 / r:.5f}"
        subprocess.run([FF, "-y", "-v", "error", "-i", mp3, "-af", f, "-ac", "1", dst], check=True)
    return dst


def load():
    from chatterbox.tts import ChatterboxTTS
    return ChatterboxTTS.from_pretrained(device="cuda")


def gen(model, text, ref, exag, cfg, temp, seed, path):
    torch.manual_seed(seed)
    wav = model.generate(text, audio_prompt_path=ref, exaggeration=exag, cfg_weight=cfg, temperature=temp)
    torchaudio.save(path, wav.cpu(), model.sr)
    return path


def main():
    mode = sys.argv[1]
    lines_path = LINES_FILE if os.path.isabs(LINES_FILE) else os.path.join(HERE, LINES_FILE)
    cfg = json.load(open(lines_path, encoding="utf-8"))
    L = {l["id"]: l for l in cfg["lines"]}
    model = load()
    if mode == "cand":
        os.makedirs(f"{OUT}/cand", exist_ok=True)
        for who, cands in CAND.items():
            ln = L[TEST[who]]
            for tag, voice, st in cands:
                for k in range(2):
                    p = f"{OUT}/cand/{who}_{tag}_t{k}.wav"
                    gen(model, ln["text"], ref_wav(voice, st), ln["exag"], ln["cfg"], ln["temp"], 1000 + k, p)
                    print("cand", p, flush=True)
    elif mode == "cand_voices":
        os.makedirs(f"{OUT}/cand", exist_ok=True)
        for who, v in cfg["voices"].items():
            cands = [l for l in cfg["lines"] if l["who"] == who]
            ln = max(cands, key=lambda x: len(x["text"].split()))
            for k in range(2):
                p = f"{OUT}/cand/{who}_cand_t{k}.wav"
                gen(model, ln["text"], ref_wav(v["ref"], v["pitch_st"]), ln["exag"], ln["cfg"], ln["temp"], 1000 + k, p)
                print("cand_voices", ln["id"], p, flush=True)
    elif mode == "trial":   # trial <line id> <edge voice> <semitones> <exag> <cfg> <tag> [takes]: one line, one setting
        lid, voice, st, ex, cf, tag = sys.argv[2], sys.argv[3], float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6]), sys.argv[7]
        n = int(sys.argv[8]) if len(sys.argv) > 8 else 2
        os.makedirs(f"{OUT}/cand", exist_ok=True)
        for k in range(n):
            p = f"{OUT}/cand/{L[lid]['who']}_{tag}_t{k}.wav"
            gen(model, L[lid]["text"], ref_wav(voice, st), ex, cf, L[lid]["temp"], 1000 + k, p)
            print("trial", p, flush=True)
    elif mode == "lines":
        os.makedirs(f"{OUT}/takes", exist_ok=True)
        only = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
        for ln in cfg["lines"]:
            if only and ln["id"] not in only:
                continue
            v = cfg["voices"][ln["who"]]
            voice, st = v["ref"], v["pitch_st"]
            for k in range(ln.get("takes", TAKES)):
                p = f"{OUT}/takes/{ln['id']}_t{k}.wav"
                gen(model, ln["text"], ref_wav(voice, st), ln["exag"], ln["cfg"], ln["temp"], 2000 + k * 17 + sum(map(ord, ln["id"])), p)
                print("take", p, flush=True)


if __name__ == "__main__":
    main()
