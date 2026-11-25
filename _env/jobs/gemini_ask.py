# HKBU SCIE1007 coursework video: one-shot design/review question to Gemini via the relay.
# Usage: py -3.11 -X utf8 gemini_ask.py <prompt.md> <out.md> [attachment ...]   (text files are inlined, images/video attached)
import os, sys
ROOT = "D:/。hkbu/molecular science"
sys.path.insert(0, ROOT + "/镜头设计_v3/素材流程")
import watch  # noqa: E402

TEXT = (".md", ".json", ".txt", ".py", ".jsx", ".csv")
prompt_file, out = sys.argv[1], sys.argv[2]
prompt = open(prompt_file, encoding="utf-8").read()
media = []
for a in sys.argv[3:]:
    if a.lower().endswith(TEXT):
        prompt += f"\n\n===== 附件：{os.path.basename(a)} =====\n" + open(a, encoding="utf-8").read()
    else:
        media.append(a)
prompt += "\n\n（要求：果断给出一个完整方案，不要列多个备选，不要反问。）"
for m in (os.environ.get("GEMINI_FIRST", "gemini-4-hydrogen"), "gemini-4-neon"):
    try:
        ans = watch.ask(prompt, media, model=m, max_tokens=16000, timeout=400, tries=2)
        break
    except Exception as e:
        ans, err = None, e
if ans is None:
    sys.exit(f"failed: {err}")
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "w", encoding="utf-8").write(ans)
print("written", out, len(ans), "chars, model", m)
