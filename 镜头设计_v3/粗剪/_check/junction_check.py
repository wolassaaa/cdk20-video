import re,json,sys
L=open('_check/sil_cut_v3_1114.txt').read().split('\n')
iv=[]
for l in L:
    m=re.match(r'silence_end: ([\d.]+) \| silence_duration: ([\d.]+)',l)
    if m: iv.append((float(m[1])-float(m[2]),float(m[1])))
b=json.load(open('cut_v3.json',encoding='utf-8'))['beats']
allowed={'2-08','4-12','5-09','6-12','7-04','8-07','W2','W3'}
bad=[];mus=0;tot=0
for i in range(len(b)-1):
    a=b[i];n=b[i+1];jt=a['new_end']+(a.get('breath_after') or 0)/2
    for s,e in iv:
        if s<=jt+0.02 and e>=jt-0.02:
            tot+=1
            if e-s>0.42:
                if a['kind']=='MUSIC' or n['kind']=='MUSIC' or a['seg'] in allowed: mus+=1
                else: bad.append((a['seg'],n['seg'],round(e-s,2)))
            break
print('junctions',len(b)-1,'silent>=0.4:',tot,'excused(music/breath)',mus,'over',len(bad)); print(bad)
