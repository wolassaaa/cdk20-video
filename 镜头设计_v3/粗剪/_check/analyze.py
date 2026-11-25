import json, os
os.environ["PYTHONUTF8"]="1"
here=os.path.dirname(os.path.abspath(__file__))
res=json.load(open(here+"/scan_text_out.json"))
man=json.load(open(here+"/../v10/manifest_v10.json",encoding="utf8"))["segments"]
def seg_of(f):
    for s in man:
        if s["start_f"]<=f<s["start_f"]+s["frames"]: return s
def mmss(t): return f"{int(t//60)}:{t%60:05.2f}"
cands=[]
for k,bx in sorted(res.items(),key=lambda x:int(x[0])):
    n=int(k); t=n*0.5; f=int(t*60); s=seg_of(f)
    if not bx: continue
    mx=max(b["lap"] for b in bx)
    for b in bx:
        h=b["b"][3]-b["b"][1]; why=[]
        if h>=24 and mx>0 and b["lap"]/mx<0.35 and len(b["t"])>=4: why.append("blur")
        if b["edge"]: why.append("edge")
        if b["con"]<0.18 and len(b["t"])>=3: why.append("lowcon")
        if b["c"]<0.6 and len(b["t"])>=5 and h>=20: why.append("lowconf")
        if why: cands.append(dict(n=n,t=t,seg=s["group"] if s else "?",tier=s["tier"] if s else "?",txt=b["t"],box=b["b"],lap=b["lap"],ratio=round(b["lap"]/mx,2),con=b["con"],c=b["c"],why=why))
json.dump(cands,open(here+"/cands.json","w"),ensure_ascii=False,indent=0)
print(len(cands), sum(1 for c in cands if "blur" in c["why"]), sum(1 for c in cands if "edge" in c["why"]), sum(1 for c in cands if "lowcon" in c["why"]), sum(1 for c in cands if "lowconf" in c["why"]))
