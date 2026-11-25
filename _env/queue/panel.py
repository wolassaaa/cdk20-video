# -*- coding: utf-8 -*-
"""HKBU SCIE1007 coursework video: local render-queue control panel, 127.0.0.1:8770 only. No delete endpoint."""
import os, sys, json, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qlib as L

PORT = 8770
HOSTS = ("127.0.0.1:%d" % PORT, "localhost:%d" % PORT)


def state():
    q = L.load()
    st = L.settings()
    eta = L.simulate(q, st)
    try:
        hb = time.time() - os.path.getmtime(os.path.join(L.Q, "heartbeat.txt"))
    except OSError:
        hb = 1e9
    jobs = []
    for j in q["jobs"]:
        d = {k: j.get(k) for k in ("id", "title", "kind", "res", "after", "est_min", "status", "tries",
                                   "started", "ended", "note")}
        e = eta.get(j["id"])
        if e:
            d["eta_start"], d["eta_end"] = [time.strftime("%Y-%m-%d %H:%M", time.localtime(x)) for x in e]
        jobs.append(d)
    counts = {}
    for j in q["jobs"]:
        counts[j["status"]] = counts.get(j["status"], 0) + 1
    g = L.gpu_state(st)
    return {"now": L.now_s(), "runner_alive": hb < 30, "hb_age": int(min(hb, 99999)),
            "paused_all": L.flag_on("PAUSED_ALL"), "gpu": {"code": g[0], "text": g[1]},
            "gpu_hold": L.flag_on("GPU_HOLD"), "gpu_guard": os.path.exists(L.GUARD_PAUSED),
            "quiet": st.get("gpu_quiet", ""), "counts": counts, "jobs": jobs}


def tail(jid, n=40):
    q = L.load()
    j = next((x for x in q["jobs"] if x["id"] == jid), None)
    if not j:
        return "没有这个任务"
    try:
        with open(L.log_path(j), "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 20000))
            data = f.read().decode("utf-8", "replace")
        return "\n".join(data.splitlines()[-n:]) or "（日志为空）"
    except FileNotFoundError:
        return "（还没有日志）"


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype):
        b = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(b)

    def _host_ok(self):
        return self.headers.get("Host", "") in HOSTS

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, "bad host", "text/plain")
        u = urlparse(self.path)
        if u.path == "/":
            return self._send(200, PAGE, "text/html; charset=utf-8")
        if u.path == "/api/state":
            return self._send(200, json.dumps(state(), ensure_ascii=False), "application/json; charset=utf-8")
        if u.path == "/api/log":
            jid = parse_qs(u.query).get("id", [""])[0]
            return self._send(200, tail(jid), "text/plain; charset=utf-8")
        self._send(404, "not found", "text/plain")

    def do_POST(self):
        if not self._host_ok() or "application/json" not in self.headers.get("Content-Type", ""):
            return self._send(403, "forbidden", "text/plain")
        if self.path != "/api/act":
            return self._send(404, "not found", "text/plain")
        try:
            n = int(self.headers.get("Content-Length", 0))
            d = json.loads(self.rfile.read(n).decode("utf-8"))
            if d.get("act") not in ("top", "up", "down", "hold", "release", "retry", "stop", "pause_all",
                                    "resume_all", "gpu_hold", "gpu_release", "quiet"):
                raise ValueError("bad act")
            ok, msg = L.act(d["act"], d.get("id"), d.get("value"))
        except Exception as e:
            ok, msg = False, str(e)
        self._send(200, json.dumps({"ok": ok, "msg": msg}, ensure_ascii=False), "application/json; charset=utf-8")


PAGE = r"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>渲染排期</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--bg:#faf8f3;--ink:#1d1d1b;--mut:#6b675e;--line:#ddd8cb;--card:#fff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 "Microsoft YaHei",system-ui,sans-serif;padding:20px 28px}
h1{font-size:24px;margin:0 0 4px}.sub{color:var(--mut);margin-bottom:14px}
.bar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:12px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 14px}
button{font:inherit;cursor:pointer;border:1px solid #bdb7a6;background:#fff;color:var(--ink);border-radius:6px;padding:6px 12px}
button:hover{background:#efeadc}.big{font-size:16px;padding:10px 18px;font-weight:600}
.b-warn{background:#f6d9d3;border-color:#c9776a}.b-ok{background:#d9ecd6;border-color:#6fa466}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line)}
th,td{padding:7px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:middle}
th{background:#f0ece0;font-weight:600;font-size:13px}tr.sel{background:#fbf6e3}td.t{cursor:pointer}
.st{padding:2px 9px;border-radius:10px;font-size:13px;white-space:nowrap}
.waiting{background:#e5e2d8}.running{background:#cfe3f7;color:#0b4a82}.done{background:#d3ebcf;color:#1d5a16}
.failed{background:#f5cdc7;color:#8a1c0e}.held{background:#fbe6b8;color:#7a5200}
.act button{padding:3px 8px;font-size:13px;margin-right:3px}
.ok{color:#1d5a16}.bad{color:#8a1c0e}.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px}
pre{background:#22211e;color:#e8e4d6;padding:12px;border-radius:6px;max-height:420px;overflow:auto;white-space:pre-wrap;font:12.5px/1.45 Consolas,monospace}
input{font:inherit;padding:5px 8px;border:1px solid #bdb7a6;border-radius:6px;width:130px}
.small{font-size:12px;color:var(--mut)}
</style></head><body>
<h1>渲染排期</h1><div class="sub">HKBU SCIE1007 课程作业的科普视频 · 本机时间 <span id="now"></span> · 每 5 秒自动刷新</div>
<div class="bar">
 <div class="card" id="runner"></div><div class="card" id="gpu"></div><div class="card" id="counts"></div>
</div>
<div class="bar">
 <button class="big b-warn" onclick="g('pause_all')">全部暂停</button><button class="big b-ok" onclick="g('resume_all')">全部继续</button>
 <button class="big b-warn" onclick="g('gpu_hold')">显卡暂停</button><button class="big b-ok" onclick="g('gpu_release')">显卡继续</button>
 <span class="card">显卡静音时段 <input id="q" placeholder="23:00-08:00"> <button onclick="setq()">设置</button>
 <span class="small">留空 = 不设；静音时段内不开新的显卡任务，已在跑的会跑完</span></span>
 <span id="msg" class="bad"></span>
</div>
<table><thead><tr><th>#</th><th>任务</th><th>类型</th><th>状态</th><th>预估(分)</th><th>开始</th><th>结束</th><th>预计开始 / 完成</th><th>操作</th></tr></thead><tbody id="rows"></tbody></table>
<h3 id="lt" style="margin:18px 0 6px"></h3><pre id="log" style="display:none"></pre>
<div class="small" style="margin-top:14px">这里没有删除功能：暂停就是改状态，所有开关都是新建或改名，任何文件都不会被删。</div>
<script>
const SN={waiting:'等待',running:'运行中',done:'完成',failed:'失败',held:'已暂停'};
let sel=null,S=null,editing=false;
const $=id=>document.getElementById(id);
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
async function post(o){const r=await fetch('/api/act',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(o)});const j=await r.json();$('msg').textContent=j.ok?'':j.msg;load()}
function g(a){post({act:a})}function a(act,id){post({act,id})}
function setq(){post({act:'quiet',value:$('q').value})}
function pick(id){sel=id;showlog();render()}
async function showlog(){if(!sel)return;const t=await (await fetch('/api/log?id='+encodeURIComponent(sel))).text();$('lt').textContent='日志（最后 40 行）：'+sel;const p=$('log');p.style.display='block';const bot=p.scrollTop+p.clientHeight>=p.scrollHeight-5;p.textContent=t;if(bot)p.scrollTop=p.scrollHeight}
function render(){
 if(!S)return;$('now').textContent=S.now;
 $('runner').innerHTML='<span class="dot" style="background:'+(S.runner_alive?'#3a9a2e':'#c0392b')+'"></span>'+(S.runner_alive?'后台在跑':'后台没在跑（心跳 '+S.hb_age+' 秒前）')+(S.paused_all?' · <b class="bad">已全部暂停</b>':'');
 const gc={free:'#3a9a2e',quiet:'#d09a1a',hold:'#c0392b',guard:'#c0392b'}[S.gpu.code];
 $('gpu').innerHTML='<span class="dot" style="background:'+gc+'"></span>'+esc(S.gpu.text);
 $('counts').innerHTML=Object.keys(SN).map(k=>SN[k]+' <b>'+(S.counts[k]||0)+'</b>').join(' · ');
 if(document.activeElement!==$('q'))$('q').value=S.quiet;
 $('rows').innerHTML=S.jobs.map((j,i)=>{
  const eta=j.eta_start?esc(j.eta_start.slice(5)+' → '+j.eta_end.slice(5)):(j.status==='waiting'?'被依赖/暂停卡住':'');
  const t=esc(j.started?j.started.slice(5,16):''),e=esc(j.ended?j.ended.slice(5,16):'');
  const run=j.status==='running';
  const b=run?'<button onclick="a(\'stop\',\''+j.id+'\')">停止</button>':
   (j.status==='held'?'<button onclick="a(\'release\',\''+j.id+'\')">放行</button>':'<button onclick="a(\'hold\',\''+j.id+'\')">暂停</button>')+'<button onclick="a(\'retry\',\''+j.id+'\')">重跑</button>';
  return '<tr class="'+(sel===j.id?'sel':'')+'"><td>'+(i+1)+'</td><td class="t" onclick="pick(\''+j.id+'\')"><b>'+esc(j.title)+'</b><div class="small">'+esc(j.id)+(j.after&&j.after.length?' · 等 '+esc(j.after.join(',')):'')+(j.tries?' · 已试 '+j.tries+' 次':'')+(j.note?' · '+esc(j.note):'')+'</div></td><td>'+esc(j.kind)+' / '+(j.res==='gpu'?'显卡':'CPU')+'</td><td><span class="st '+j.status+'">'+SN[j.status]+'</span></td><td>'+esc(j.est_min)+'</td><td>'+t+'</td><td>'+e+'</td><td>'+eta+'</td><td class="act"><button onclick="a(\'top\',\''+j.id+'\')">置顶</button><button onclick="a(\'up\',\''+j.id+'\')">上移</button><button onclick="a(\'down\',\''+j.id+'\')">下移</button>'+b+'</td></tr>'}).join('')||'<tr><td colspan=9>队列是空的</td></tr>';
}
async function load(){try{S=await (await fetch('/api/state')).json();render();showlog()}catch(e){$('msg').textContent='连不上面板服务'}}
load();setInterval(load,5000);
</script></body></html>"""


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
