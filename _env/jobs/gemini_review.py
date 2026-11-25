# HKBU SCIE1007 coursework video: first-pass review of new review videos by Gemini (native video+audio) via the relay.
# For each new mp4 in 导演检查_* (ledger-based), make a small proxy on G:, ask gemini-4-hydrogen (fallback neon) to
# review it against 镜头设计_v3/审片/导演标准_审片用.md, write the full answer to G:/cdk20/work/gemini_review/ and a
# summary row to 导演检查_<today>/_Gemini审片.md. Claude still makes the final call; this saves Claude's quota.
# Usage: python gemini_review.py [file.mp4 ...]   (no args = all new files)
import datetime, glob, json, os, re, subprocess, sys

ROOT = "D:/。hkbu/molecular science"
sys.path.insert(0, ROOT + "/镜头设计_v3/素材流程")
import watch  # noqa: E402

FF = "D:/software/tools/CipherTalk/resources/app.asar.unpacked/node_modules/ffmpeg-static/ffmpeg.exe"
OUT = "G:/cdk20/work/gemini_review"
LEDGER = ROOT + "/_env/jobs/gemini_ledger.json"
STD = open(ROOT + "/镜头设计_v3/审片/导演标准_审片用.md", encoding="utf-8").read()
SKIP = re.compile(r"_v\d+\.mp4$|_tmp\.mp4$|wink_")
MODELS = ["gemini-4-hydrogen", "gemini-4-neon"]
CHUNK = 60  # seconds per request

PROMPT = """你是这部课程作业科普视频的审片员。下面是导演的审片标准，照它逐条看这段视频（画面和声音都要看/听）。

{std}

这段是：{name}（第 {a:.0f}–{b:.0f} 秒）。

要求：
- 果断，不要犹豫、不要客套、不要重复标准原文。看到就报，没看到就不报。
- 先用一行写出你听到的英文旁白（原话）。
- 然后列问题，每条一行，格式：`[必改|应改|可改] 时间点(秒) — 问题 — 建议怎么改`。时间点用这段视频里的秒数。
- 最后一行只写：`结论：过` 或 `结论：不过`（有任何必改就是不过）。
- 只看得出的才报；不确定的标"(存疑)"。全部用中文，旁白原话保留英文。"""


def proxy(src, a, dur, dst):
    subprocess.run([FF, "-v", "error", "-y", "-ss", str(a), "-t", str(dur), "-i", src, "-vf", "scale=960:-2",
                    "-r", "30", "-c:v", "libx264", "-crf", "30", "-preset", "veryfast", "-c:a", "aac", "-b:a", "96k", dst],
                   check=True)


def duration(src):
    r = subprocess.run([ROOT + "/_env/ffmpeg/ffprobe.exe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", src], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def ask(path, name, a, b):
    last = None
    for m in MODELS:
        try:
            return m, watch.ask(PROMPT.format(std=STD, name=name, a=a, b=b), [path], model=m,
                                max_tokens=8000, timeout=300, tries=2)
        except Exception as e:  # relay hiccups: try the next model
            last = e
    raise RuntimeError(f"all models failed: {last}")


def review(src):
    name = os.path.basename(src)
    os.makedirs(OUT, exist_ok=True)
    total = duration(src)
    parts, verdict = [], "过"
    a = 0.0
    while a < total - 0.05:
        b = min(total, a + CHUNK)
        tmp = f"{OUT}/_proxy.mp4"
        proxy(src, a, b - a, tmp)
        m, text = ask(tmp, name, a, b)
        parts.append(f"### {a:.0f}–{b:.0f} s（{m}）\n\n{text.strip()}\n")
        if "结论：不过" in text:
            verdict = "不过"
        a = b
    must = sum(p.count("[必改") for p in parts)
    rep = f"{OUT}/{os.path.splitext(name)[0]}.md"
    with open(rep, "w", encoding="utf-8") as f:
        f.write(f"# Gemini 审片：{name}\n\n{datetime.datetime.now():%m-%d %H:%M}\n\n" + "\n".join(parts))
    return verdict, must, rep


def main():
    led = json.load(open(LEDGER, encoding="utf-8")) if os.path.exists(LEDGER) else {}
    files = sys.argv[1:] or sorted(glob.glob(ROOT + "/导演检查_*/*.mp4"))
    day = ROOT + f"/导演检查_{datetime.date.today():%Y%m%d}/_Gemini审片.md"
    for src in files:
        src = src.replace("\\", "/")
        if SKIP.search(os.path.basename(src)):
            continue
        mt = os.path.getmtime(src)
        if len(sys.argv) == 1 and led.get(src) == mt:
            continue
        try:
            verdict, must, rep = review(src)
        except Exception as e:
            print("FAIL", src, str(e)[:200]); continue
        new = not os.path.exists(day)
        with open(day, "a", encoding="utf-8") as f:
            if new:
                f.write("# Gemini 初审（HKBU SCIE1007 课程作业的科普视频）\n\n第一道审片，照 审片/导演标准_审片用.md；全文在 G:/cdk20/work/gemini_review/。Claude 复核后才算数。\n\n| 时间 | 文件 | 结论 | 必改条数 | 全文 |\n|---|---|---|---|---|\n")
            f.write(f"| {datetime.datetime.now():%H:%M} | {os.path.basename(os.path.dirname(src))}/{os.path.basename(src)} | {verdict} | {must} | {rep} |\n")
        led[src] = mt
        json.dump(led, open(LEDGER, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(verdict, must, src)


if __name__ == "__main__":
    main()
