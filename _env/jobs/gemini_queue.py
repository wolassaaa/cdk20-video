# HKBU SCIE1007 coursework video: run several Gemini (neon) design/writing jobs in parallel.
# Usage: py -3.11 -X utf8 gemini_queue.py job.json
# job.json: [{"prompt": "...md", "out": "...md", "attach": ["...", ...], "model": "gemini-4-neon"}, ...]
# Paths are relative to the project root. Each job writes its answer to "out"; a summary prints at the end.
import json, os, sys, threading
ROOT = "D:/。hkbu/molecular science"
sys.path.insert(0, ROOT + "/镜头设计_v3/素材流程")
import watch  # noqa: E402

TEXT = (".md", ".json", ".txt", ".py", ".jsx", ".csv")
TAIL = "\n\n（要求：果断给出一个完整方案，不要列多个备选，不要反问。）"


def run(job, res):
    p = lambda x: x if ":" in x else os.path.join(ROOT, x)
    prompt = open(p(job["prompt"]), encoding="utf-8").read()
    media = []
    for a in job.get("attach", []):
        if a.lower().endswith(TEXT):
            prompt += f"\n\n===== 附件：{os.path.basename(a)} =====\n" + open(p(a), encoding="utf-8").read()
        else:
            media.append(p(a))
    prompt += TAIL
    first = job.get("model", "gemini-4-neon")
    for m in dict.fromkeys([first, "gemini-4-neon", "gemini-4-hydrogen"]):
        try:
            ans = watch.ask(prompt, media, model=m, max_tokens=16000, timeout=500, tries=2)
            open(p(job["out"]), "w", encoding="utf-8").write(ans)
            res.append(f"OK  {job['out']}  {len(ans)} chars  {m}")
            return
        except Exception as e:  # relay hiccup: next model
            err = e
    res.append(f"FAIL {job['out']}  {str(err)[:150]}")


jobs = json.load(open(sys.argv[1], encoding="utf-8"))
res = []
th = [threading.Thread(target=run, args=(j, res)) for j in jobs]
for t in th:
    t.start()
for t in th:
    t.join()
print("\n".join(res))
