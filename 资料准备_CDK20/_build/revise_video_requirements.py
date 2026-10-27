from pathlib import Path
import json,csv,re,sys,shutil,hashlib,difflib
BASE=Path(__file__).resolve().parent.parent;OUT=BASE/'视频内容稿'
BACK=BASE/'_build/requirements_revision_20261007/before'
BACK.mkdir(parents=True,exist_ok=True)
for p in list(OUT.iterdir())+[BASE/'_build/build_video_documents.py',BASE/'_build/verify_video_content.py']:
 if p.is_file() and not (BACK/p.name).exists():shutil.copy2(p,BACK/p.name)
sys.path.insert(0,str(BASE/'_build/script_dependencies'))
from opencc import OpenCC
cc=OpenCC('s2t');tc=lambda s:cc.convert(s).replace('爲','為').replace('纔','才').replace('覈','核')
d=json.loads((BACK/'双语内容主稿.json').read_text(encoding='utf-8'))
ps=[p for s in d['sections'] for p in s['paragraphs']]
ps[1]['en']='AI offers an interesting possibility: use patterns learned from existing data to suggest designs worth investigating. But a suggested structure is not yet an experimentally confirmed hit. We will follow one liver cancer study from design to testing and improvement, then ask what AI contributed, which benefits remain possible rather than proven, and what better evidence would require.'
ps[1]['zh_sc']='AI提供了一种值得研究的可能：利用从已有数据中学到的规律，提出值得进一步探索的设计。不过，提出一个结构，还不等于得到实验确认的命中物。我们会沿着一项肝癌研究，追踪设计、测试与改进，再判断AI具体贡献了什么、哪些收益仍只是潜力，以及还需要怎样的证据。'
ps[29]['en']='Those experiments give us a basis for discussing benefits. Predicted protein structure supported design, AI-assisted generation proposed molecules, and experiments identified a hit and supported further improvement. This is a contribution to early discovery, not proof of a finished treatment. We should separate what this workflow achieved from the wider advantages we hope it could bring.'
ps[29]['zh_sc']='这些实验让我们有依据讨论收益。预测蛋白结构支持了设计，AI辅助生成提出了分子，实验找到了命中物，也支持了进一步改进。这是对早期发现的贡献，不是已经完成治疗药物的证明。我们应把这条流程实际取得的成果，与希望它进一步带来的好处分开。'
ps[35]['en']='We can now answer our opening question. Can we predict whether a molecule is worth testing before we even make it? We can make informed predictions, but experiments must test them. In this case, algorithms helped people propose and prioritise designs, while experiments guided the next step. The promise is a better-directed search. How much faster that search becomes, and whether it leads to a useful medicine, remain questions for further evidence.'
ps[35]['zh_sc']='现在可以回答开场的问题：一个还没做出来的分子，我们能先预测它是否值得测试吗？我们可以提出有依据的预测，但必须用实验检验。在本案例中，算法帮助人提出设计和安排优先级，实验则引导下一步。它的潜力在于让探索更有方向；这种探索到底快了多少，最终能否带来有用的药物，仍要由进一步证据回答。'
new=[
 {'en':'The wider hopes include health, cost and animal welfare. Earlier useful candidates might support future treatments, and avoiding low-value experiments might save resources. Better predictions might also help researchers consider alternatives to some animal experiments. These are possibilities, not measured outcomes of this case. We would need evidence of actual savings and suitable validation, not simply a shorter list of molecules.',
 'zh_sc':'更广泛的期待包括健康、成本与动物福利。更早找到有用的候选物，可能支持未来治疗研究；避免低价值实验，也可能节省资源。更好的预测还可能帮助研究者考虑某些动物实验的替代方法。这些是可能性，不是本案例已经测出的结果。我们需要实际节省投入的证据和合适的验证，不能只看分子清单变短了。','refs':['E36']},
 {'en':'Environmental claims need the same care. Fewer unnecessary syntheses could mean less material use and waste, but computers also consume electricity. We should compare the resources used by both the calculations and the laboratory work for a similar research outcome. Without that comparison, this case does not establish that AI is cheaper, reduces animal use or is environmentally better overall.',
 'zh_sc':'环境收益也要同样谨慎。减少不必要的合成，可能减少材料消耗与废物，但电脑也会耗电。我们应在取得相近研究成果的条件下，比较计算和实验两部分的资源投入。缺少这种比较，就不能用本案例断言AI总体上更便宜、减少了动物使用，或更加环保。','refs':['E37']}
]
last=d['sections'][-1]['paragraphs'];last[3:3]=new
mapping=[]
for n,s in enumerate(d['sections'],1):
 s['id']=f'C{n:02d}'
 s['role_en']='Overview' if n==1 else 'Introduction' if n==2 else 'Body' if n<8 else 'Benefits, future directions and conclusion'
 for p in s['paragraphs']:
  old=p.get('id','new');i=len(mapping)+1;p['id']=f'P{i:02d}';p['zh_tc']=tc(p['zh_sc']);mapping.append((old,p['id']))
d['date']='2026-10-07';d['revision']='teacher-requirements revision 2'
d['research_question_en']='How can AI-assisted computation improve early molecule discovery for liver cancer, and which benefits have or have not been demonstrated?'
d['research_question_sc']='AI辅助计算怎样改善肝癌早期分子发现？哪些收益已经展示，哪些仍未得到证明？'
d['objectives']=[{'en':'Explain how computational design and experiments work together in the CDK20 case.','zh_sc':'解释CDK20案例中计算设计与实验怎样相互配合。'},{'en':'Evaluate the observed benefits, evidence gaps and practical next research steps.','zh_sc':'评价已经观察到的收益、证据缺口和具体的后续研究方向。'}]
d['english_word_count']=len(re.findall(r"[A-Za-z0-9]+(?:[’'-][A-Za-z0-9]+)*",' '.join(p['en'] for s in d['sections'] for p in s['paragraphs'])))
(OUT/'双语内容主稿.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
rows=list(csv.DictReader((BACK/'证据索引.csv').open(encoding='utf-8-sig')))
for eid,claim,boundary in [('E36','健康、成本与动物福利作为潜在收益讨论','主案例未提供成本或动物数量的同任务比较；不声称已带来患者疗效或减少动物实验'),('E37','环境收益需同时考虑计算与实验投入','没有生命周期或相同成果条件下的资源比较；不声称总体环保优势已证明')]:
 r={k:'不适用' for k in rows[0]};r.update({'证据编号':eid,'主张':claim,'来源编号':'T02;S02','定位':'Group Project Introduction 第49页 Benefits；S02已报告实验范围；本稿条件性讨论','研究阶段':'课程讨论维度与拟议评价','方法':'区分潜在收益与实际测量；提出可检验比较','样本或对照':'主案例未报告对应同任务资源/动物数量/环境对照','结果或原文信息':'老师列举健康、经济、伦理、环境及计算用电；本稿不新增实验结果','支持的表述':'作为待检验的可能收益与比较方向','推论边界':boundary,'局限':'课程课件是主题指导，不是实证研究；比较方案是我们的分析','核查层级':'本地课程原页核查＋主案例范围核对','来源URL':'file:///D:/。hkbu/molecular%20science/Group%20Project%20Introduction.pdf#page=49','核查日期':'2026-10-07'});rows.append(r)
with (OUT/'证据索引.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
for edition,field in [('简中','zh_sc'),('繁中','zh_tc')]:
 lines=['# Can AI help design a molecule worth testing?',tc(d['title_sc']) if edition=='繁中' else d['title_sc'],'','Research question: '+d['research_question_en'],'',tc(d['research_question_sc']) if edition=='繁中' else d['research_question_sc'],'']
 for s in d['sections']:
  lines+=['## '+s['id']+' '+s['role_en']+' | '+s['title_en'],'',s['title_tc'] if edition=='繁中' else s['title_sc'],'']
  for p in s['paragraphs']:lines +=[p['id']+' EN',p['en'],'',p['id']+' '+edition,p[field],'','依据：'+', '.join(p['refs']),'']
 (OUT/f'视频内容稿_英文加{edition}.md').write_text('\n'.join(lines),encoding='utf-8')
with (OUT/'修订段落对应表.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['旧段号','新段号']);w.writerows(mapping)
diff=''.join(difflib.unified_diff((BACK/'双语内容主稿.json').read_text(encoding='utf-8').splitlines(True),(OUT/'双语内容主稿.json').read_text(encoding='utf-8').splitlines(True),fromfile='before',tofile='after'))
(BASE/'_build/requirements_revision_20261007/content.diff').write_text(diff,encoding='utf-8')
print('REVISED',d['english_word_count'],'words',sum(len(s['paragraphs']) for s in d['sections']),'paragraphs; 37 evidence cards')
