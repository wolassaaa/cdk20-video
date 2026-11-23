import json,sys,time
sys.path.insert(0,'.')
import retime_v8 as V, retime_v6 as RT, build_rough as R
from pathlib import Path
for seg in [a for a in sys.argv[1:] if not a.startswith('--')]:
    B=json.load(open(f'beats/{seg}.json',encoding='utf-8'))
    s=B['source']; src=R.P/s['file']; fin=s['fin']; fout=s['fout']
    if seg in RT.SRC_OVERRIDE: src,fin,fout,_=RT.SRC_OVERRIDE[seg]
    avail=min(R.probe_duration(src)-fin, fout-fin+(0 if seg in RT.HARD_END else 0.5))
    hand=None
    if seg in RT.S1A:
        S=RT.S1A[seg]; hand=[]
        for a in S['actions']:
            h=[x for x in B['words'] if x['w']==a.get('word')]
            if h: hand.append((round(a['src_t']-S['src_start'],3),h[0]['t0']))
    t=time.time()
    pos,spd,info,act,fps=V.plan_vo(seg,B['words'],B['audio']['seconds'],B['audio']['piece'],src,fin,avail,hand=hand)
    print(seg,round(time.time()-t,1),json.dumps({k:info[k] for k in ('anchors','speed_min','speed_max','coverage','s_a','s_b')}))
    if '--r' in sys.argv[-1:]: pass
import numpy as np
if '--dbg' in sys.argv:
    print('thr',info['thr'])
    for j in range(0,len(pos),15):
        k=int(pos[j]); print(f"t={j/30:5.1f} src={k/fps:6.2f} spd={spd[j]:.2f} act={act[min(k,len(act)-1)]:.4f}")
