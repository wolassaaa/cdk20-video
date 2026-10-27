"""Pair script_v3.3.md (English) with script_v3.3_zh.md (Chinese) beat by beat and write script_v3.3_bilingual.html."""
import re, os, html, json

HERE = os.path.dirname(os.path.abspath(__file__))
E = lambda s: html.escape(s)
en = open(os.path.join(HERE, "script_v3.3.md"), encoding="utf-8").read()
zh = open(os.path.join(HERE, "script_v3.3_zh.md"), encoding="utf-8").read()
en = en[en.index("## Part 3"):]
en = en[:en.index("## Part 4")] if "## Part 4" in en else en

HEAD = re.compile(r"^\*\*((?:\d-\d\d)|W\d) · ([\d:–]+) · (.+?)\*\*", re.M)


def beats(text, quote):
    out, order = {}, []
    ms = list(HEAD.finditer(text))
    for k, m in enumerate(ms):
        body = text[m.end(): ms[k + 1].start() if k + 1 < len(ms) else len(text)]
        body = re.split(r"\n#{2,3} ", body)[0]
        if quote:
            line = " ".join(l[2:].strip() for l in body.splitlines() if l.startswith("> "))
            vis = next((l.split(":", 1)[1].strip() for l in body.splitlines() if l.startswith("- Visual:")), "")
        else:
            paras = [p.strip() for p in body.strip().split("\n\n") if p.strip() and not p.strip().startswith("#")]
            line = paras[0] if paras else ""
            vis = ""
        out[m.group(1)] = {"id": m.group(1), "time": m.group(2), "who": m.group(3), "text": line, "visual": vis}
        order.append(m.group(1))
    return out, order


EN, order = beats(en, True)
ZH, _ = beats(zh, False)
secs = [(m.start(), m.group(1)) for m in re.finditer(r"^### (S\d · .+)$", en, re.M)]
zsecs = [m.group(1) for m in re.finditer(r"^#{2,3} (S\d.*)$", zh, re.M)]


def section_of(pos):
    cur = None
    for p, name in secs:
        if p <= pos:
            cur = name
    return cur


pos = {m.group(1): m.start() for m in HEAD.finditer(en)}
rows, last = [], None
for bid in order:
    sec = section_of(pos[bid])
    if sec != last:
        idx = [n for _, n in secs].index(sec)
        zname = zsecs[idx] if idx < len(zsecs) else ""
        rows.append('<tr class="sec"><td colspan="3"><span>%s</span><em>%s</em></td></tr>' % (E(sec), E(zname)))
        last = sec
    e, z = EN[bid], ZH.get(bid, {"text": "", "who": ""})
    music = bid.startswith("W")
    who = re.findall(r"\b([ABCD])\b", e["who"])
    oncam = "ON-CAM" in e["who"]
    tag = "music" if music else ("on" if oncam else "vo")
    label = "纯音乐" if music else ("出镜" if oncam else "画外音")
    en_text = e["text"] if not music else e["visual"]
    rows.append(
        '<tr class="beat %s" data-who="%s"><td class="meta"><b>%s</b><span>%s</span><span class="who">%s</span><span class="kind k-%s">%s</span></td>'
        '<td class="en">%s</td><td class="zh">%s</td></tr>' % (
            tag, " ".join(who) or "-", E(bid), E(e["time"]), E(" ".join(who) or "—"), tag, label,
            E(en_text), E(z["text"])))

page = """<title>脚本 v3.3 中英对照</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@800&family=Inter+Tight:wght@400;500;600&family=JetBrains+Mono:wght@400;600&family=Noto+Sans+SC:wght@400;500&display=swap">
<style>
/* reading layout: one row per spoken beat, English left, Chinese right, filter by speaker */
:root { --ink:#070707; --panel:#111; --line:#2B2A28; --smoke:#8C8A84; --bone:#EDEBE4; --red:#FF3B1F; --cyan:#29F0FF;
  --body:"Inter Tight","Noto Sans SC","PingFang SC","Microsoft YaHei",system-ui,sans-serif; --zh:"Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif;
  --mono:"JetBrains Mono",Consolas,monospace; color-scheme:dark; }
html,body { background:var(--ink); color:var(--bone); }
body { margin:0; font-family:var(--body); font-size:16px; line-height:1.6; padding-left:max(16px,env(safe-area-inset-left,0px)); padding-right:max(16px,env(safe-area-inset-right,0px)); padding-block:0 64px; }
.wrap { max-width:1180px; margin:0 auto; }
header { padding:40px 0 20px; display:grid; gap:10px; border-bottom:1px solid var(--line); }
h1 { margin:0; font-family:"Big Shoulders Display",Impact,sans-serif; font-weight:800; font-size:clamp(40px,7vw,72px); line-height:.95; text-transform:uppercase; }
h1 b { color:var(--red); }
.sub { color:var(--smoke); margin:0; max-width:70ch; }
.bar { position:sticky; top:env(safe-area-inset-top,0px); background:var(--ink); z-index:5; display:flex; flex-wrap:wrap; gap:8px; padding:12px 0; border-bottom:1px solid var(--line); }
body::before { content:""; position:fixed; inset:0 0 auto; height:env(safe-area-inset-top,0px); z-index:10; background:var(--ink); }
.bar button { font-family:var(--mono); font-size:13px; background:transparent; color:var(--bone); border:1px solid var(--line); padding:6px 12px; cursor:pointer; }
.bar button[aria-pressed="true"] { background:var(--bone); color:var(--ink); border-color:var(--bone); }
.bar button:focus-visible { outline:2px solid var(--cyan); outline-offset:2px; }
.tablewrap { overflow-x:auto; }
table { width:100%; border-collapse:collapse; min-width:720px; }
td { vertical-align:top; padding:14px 14px 14px 0; border-bottom:1px solid var(--line); }
td.meta { width:120px; font-family:var(--mono); font-size:12px; color:var(--smoke); display:flex; flex-direction:column; gap:3px; }
td.meta b { color:var(--bone); font-size:15px; }
.who { color:var(--bone); }
.kind { align-self:start; padding:0 6px; border:1px solid var(--line); }
.k-on { color:var(--ink); background:var(--bone); border-color:var(--bone); }
.k-music { color:var(--cyan); border-color:var(--cyan); }
td.en { width:46%; }
td.zh { font-family:var(--zh); color:var(--bone); opacity:.92; }
tr.music td.en, tr.music td.zh { color:var(--smoke); font-size:14px; font-style:italic; }
tr.on td.en { font-weight:500; }
tr.sec td { padding:28px 0 8px; border-bottom:2px solid var(--bone); }
tr.sec span { font-weight:600; font-size:18px; margin-right:14px; }
tr.sec em { font-style:normal; color:var(--smoke); font-family:var(--zh); }
tr[hidden] { display:none; }
.legend { font-family:var(--mono); font-size:12px; color:var(--smoke); display:flex; gap:16px; flex-wrap:wrap; }
</style>
<div class="wrap">
<header>
  <h1>Worth testing<b>?</b> 脚本 v3.3</h1>
  <p class="sub">中英对照，一行一个台词节拍。左边是要念的英文，右边是中文意思。「出镜」要对着镜头说，「画外音」配画面，「纯音乐」是无人声的展示段。时间按保守语速估算，录完音后会重新对时间。</p>
  <div class="legend"><span>全片约 17:43</span><span>A 3:47 · B 3:49 · C 4:17 · D 3:59</span><span>来源：script_v3.3.md / script_v3.3_zh.md</span></div>
</header>
<div class="bar" role="toolbar" aria-label="按讲者筛选">
  <button type="button" data-f="all" aria-pressed="true">全部</button>
  <button type="button" data-f="A" aria-pressed="false">A</button>
  <button type="button" data-f="B" aria-pressed="false">B</button>
  <button type="button" data-f="C" aria-pressed="false">C</button>
  <button type="button" data-f="D" aria-pressed="false">D</button>
  <button type="button" data-f="on" aria-pressed="false">只看出镜句</button>
</div>
<div class="tablewrap"><table><tbody>@@rows@@</tbody></table></div>
</div>
<script>
const btns=[...document.querySelectorAll('.bar button')];
btns.forEach(b=>b.addEventListener('click',()=>{
  const f=b.dataset.f; btns.forEach(x=>x.setAttribute('aria-pressed',x===b));
  document.querySelectorAll('tr.beat').forEach(tr=>{
    const who=tr.dataset.who.split(' ');
    tr.hidden = f==='all' ? false : f==='on' ? !tr.classList.contains('on') : !who.includes(f);
  });
  document.querySelectorAll('tr.sec').forEach(tr=>{ tr.hidden = f!=='all'; });
}));
</script>
""".replace("@@rows@@", "".join(rows))
open(os.path.join(HERE, "script_v3.3_bilingual.html"), "w", encoding="utf-8").write(page)
missing = [b for b in order if b not in ZH]
print(len(order), "beats;", "missing zh:", missing, "; empty en:", [b for b in order if not EN[b]["text"] and not b.startswith("W")])
