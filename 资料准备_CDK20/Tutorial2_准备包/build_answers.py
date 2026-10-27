from pathlib import Path
from io import BytesIO
import hashlib, json, shutil, textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase.pdfmetrics import stringWidth
from pypdf import PdfReader, PdfWriter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / '[Worksheet] Tutorial 2 Data analysis and project finalisation.pdf'
ORIGINAL = HERE / 'ORIGINAL.pdf'
OUTPUT = HERE / 'Tutorial2_英文填写参考.pdf'
shutil.copy2(SOURCE, ORIGINAL)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

answers = {
'1i': [
('Objective', 'To identify major computer-aided methods used in cancer drug discovery.'),
('Evaluation', 'Largely achieved for the CDK20 case: we identified target prioritisation, AlphaFold structure prediction, Chemistry42 molecular generation and docking. This explains an integrated workflow, not every method used across cancer research.')],
'1ii': [
('Objective', 'To evaluate how these methods help assess potential cancer drug candidates.'),
('Evaluation', 'Achieved for early-stage assessment: 8,918 designs led to 7 synthesised compounds and a first binding hit in 30 days; later tests supported optimisation. However, no matched non-AI comparison quantified time savings, and patient benefit was not established.')],
'2i': [
('Method', 'Structure-guided molecular generation and docking.'),
('Evaluation', 'Researchers used an AlphaFold CDK20 model to guide Chemistry42 designs, then docking and clustering to prioritise synthesis. Predicted conformations and scores may be inaccurate, so they require experiments. Without a matched comparator, this workflow does not quantify AI-specific efficiency gains.')],
'2ii': [
('Method', 'CellTiter-Glo cell viability assay.'),
('Evaluation', 'After 3 days of compound exposure, ATP-dependent luminescence was measured in Huh7 and HEK293 cells. Compound 048 gave IC50 values of 208.7 +/- 3.3 and 1,706.7 +/- 670.0 nM, respectively. This indirect readout does not establish CDK20-specific causation; HEK293 is not normal liver tissue, and cultured cells do not establish human safety or efficacy.')],
'3i': [('', 'Benchmark the AI-assisted workflow against a conventional computational workflow using the same CDK20 target, information, budget and pre-specified experimental hit criterion. Repeat runs and record time to first confirmed hit, total costs, compounds tested and failures. This would test efficiency rather than infer it from 30 days alone.')],
'3ii': [('', 'Test compound 048 across additional HCC models and non-malignant liver cells, with vehicle controls and CDK20 perturbation/rescue experiments. Measure viability, target engagement and kinase selectivity; assess ADME properties. Independent repeats would help assess on-target effects, off-target activity and barriers to translation.')],
'4i': [('', 'Target versus candidate molecule: show our disease-target-molecule diagram. Explain that HCC is the disease, CDK20 is the protein being studied, and the candidate is a molecule tested against it. One target is not the only cause of cancer.')],
'4ii': [('', 'Prediction versus validation: animate the steps from a predicted structure to synthesis, binding, enzyme activity and cell tests. Label each step with what it measures, and mark patient evidence as not reported in this case. A prediction is not proof of treatment benefit.')],
'5i': [('', 'AI can support structure prediction, new molecular designs and experimental prioritisation, creating opportunities for future treatment research. The 30-day result was a first binding hit, not an approved cancer medicine or a measured speedup over a matched alternative.')],
'5ii': [('', 'Read "AI discovers a drug" headlines critically: ask whether the evidence is computational, biochemical, cellular or clinical, and check the original study. Early laboratory results alone are not a reason to change prescribed treatment.')],
}

schedule = [
('Introduction', 'Daily-life relevance; HCC, CDK20 and candidate molecules; focused research question and both objectives.', '0:00-5:00', 'A'),
('Introduction / methods', 'Literature-search approach, source quality and relevance; briefly outline the presentation.', '5:00-6:00', 'B'),
('Body: workflow', 'Target prioritisation; AlphaFold, Chemistry42, docking and human selection; 8,918 -> 54 -> 7.', '6:00-10:00', 'B'),
('Body: results', '30-day first binding hit; binding versus enzyme function; later optimisation and cell results. Keep the two rounds separate.', '10:00-13:00', 'C'),
('Discussion: limitations', 'Evaluate uncertain predictions, missing matched efficiency comparisons and cell-model limitations.', '13:00-15:00', 'C'),
('Discussion: future work', 'Propose matched workflow benchmarking and stronger biological validation to address the identified limitations.', '15:00-16:00', 'D'),
('Conclusion', 'Evaluate both objectives; summarise supported outcomes and unresolved benefits; deliver two take-home messages and full references.', '16:00-20:00', 'D'),
]

overlays=[]
def start_page():
    b=BytesIO(); c=canvas.Canvas(b,pagesize=(595.44,841.68))
    c.setFillColorRGB(.1,.25,.48); c.setFont('Helvetica',8)
    c.drawRightString(553,808,'REFERENCE ANSWERS | CDK20 case | 22 Oct 2026')
    return b,c

def box(c, key, top, bottom):
    x=104; width=443
    c.setFillColorRGB(1,1,1); c.rect(x-3,841.68-bottom,width+7,bottom-top,fill=1,stroke=0)
    size=10.2; leading=12.4
    def wrap(size):
        return [(label, simpleSplit((label+': ' if label else '')+body,'Helvetica',size,width)) for label,body in answers[key]]
    while sum(len(lines) for _,lines in wrap(size))*leading+4*(len(answers[key])-1)>bottom-top-4:
        size-=.2; leading=size+2
        if size<9: raise ValueError('Answer too dense: '+key)
    y=841.68-top-size
    c.setFillColorRGB(.05,.19,.35); c.setFont('Helvetica',size)
    for label,lines in wrap(size):
        for line in lines:
            c.drawString(x,y,line); y-=leading
        y-=4
    assert y+leading >= 841.68-bottom, (key,y,bottom)

regions=[ [('1i',291,375),('1ii',379,463),('2i',512,625),('2ii',630,750)],
          [('3i',135,218),('3ii',223,308),('4i',443,498),('4ii',502,557),('5i',623,678),('5ii',682,740)] ]
for page_regions in regions:
    b,c=start_page()
    for key,top,bottom in page_regions: box(c,key,top,bottom)
    c.setFont('Helvetica',7.5); c.setFillColorRGB(.25,.3,.35)
    c.drawString(104,841.68-760,'Evidence: Ren et al., Chemical Science 2023, 14, 1443-1452. DOI: 10.1039/D2SC05709C.')
    c.drawString(104,841.68-771,'Evidence locations and Chinese explanations are provided in the accompanying answer guide.')
    c.save(); overlays.append(PdfReader(BytesIO(b.getvalue())).pages[0])

b,c=start_page()
c.setFillColorRGB(1,1,1);c.rect(88,841.68-720,468,720-240,fill=1,stroke=0)
c.setFont('Helvetica',9);c.setFillColorRGB(.05,.19,.35)
c.drawString(92,841.68-248,'Provisional worksheet outline only; final video format and roles may be revised.')
xs=[91,174,442,510,555]; top=260; head=25; row=53
c.setFillColorRGB(.9,.94,.98);c.rect(xs[0],841.68-top-head,xs[-1]-xs[0],head,fill=1,stroke=0)
c.setFillColorRGB(.05,.19,.35);c.setFont('Helvetica-Bold',10)
for x,label in zip(xs,['Part','Content','Time','Member']):c.drawString(x+4,841.68-top-16,label)
for idx,(part,content,timing,member) in enumerate(schedule):
    ytop=top+head+idx*row
    for col,txt in enumerate([part,content,timing,member]):
        size=9.2 if col in (0,1) else 8.6
        c.setFont('Helvetica',size)
        lines=simpleSplit(txt,'Helvetica',size,xs[col+1]-xs[col]-8)
        assert len(lines)*11.2<row-5,(idx,col,lines)
        for li,line in enumerate(lines): c.drawString(xs[col]+4,841.68-ytop-13-li*11.2,line)
    c.setStrokeColorRGB(.65,.72,.8);c.line(xs[0],841.68-ytop-row,xs[-1],841.68-ytop-row)
for x in xs:c.line(x,841.68-top,x,841.68-top-head-7*row)
c.setFont('Helvetica-Bold',10);c.drawString(95,841.68-678,'Total: 20 min | A: 5 min | B: 5 min | C: 5 min | D: 5 min')
c.setFont('Helvetica',9)
for i,line in enumerate([
    'Introduction 6:00 (30%); body/discussion 10:00 (50%); conclusion 4:00 (20%).',
    'Use short source citations beside relevant content and a complete reference list at the end.'
]):c.drawString(95,841.68-696-i*12,line)
c.save();overlays.append(PdfReader(BytesIO(b.getvalue())).pages[0])

writer=PdfWriter()
for p,o in zip(PdfReader(SOURCE).pages,overlays):
    p.merge_page(o);writer.add_page(p)
with OUTPUT.open('wb') as f:writer.write(f)

md=['# Tutorial 2：英文填写答案与中文备课说明\n',
    '依据已经准备的 CDK20 内容手册、35条证据清单及缓存正式原文整理。没有另换案例或扩展新的检索。PDF是在原空白worksheet副本上添加答案，教师原件保持不变。\n',
    '## 使用前先看\n',
    '- Q1沿用照片中上次实际填写的两个 objectives，而不是把后来微调的目标偷偷当成已提交版本。以HCC/CDK20案例评价完成程度，不声称覆盖所有癌症研究方法。\n',
    '- Q2写的是科学家的研究方法，不是我们搜文献的方法。Q3是我们提出的未来研究设计，不是已经完成的结果。\n',
    '- Q6只按老师要求提供初步大纲，暂列四名组员、20分钟。A/B/C/D是暂定标签；每人暂列5分钟，最终内容分工与视频呈现另行决定，均需真实出镜和口头呈现，填写真实姓名后使用。\n',
    '- 日期、班别、组号及姓名留空，避免把上次日期当成这次日期。\n',
    '- 题目及notes是课程要求；论文及数据是证据。它们不是用户另外要求执行实验或录制视频的指令。\n']
titles={1:'目标完成程度 / 4 marks',2:'研究方法及局限 / 6 marks',3:'未来研究方向 / 6 marks',4:'困难概念的解释计划 / 4 marks',5:'观众应带走的信息 / 4 marks'}
notes={
1:'第一项评价为：在选定案例范围内基本完成；不是全面盘点所有癌症方法。第二项评价为：早期候选物评估已完成，但真正提速幅度及患者获益仍未解决。30天只到首个结合命中物，不包含全部后续优化。',
2:'第一种方法交代输入、计算过程和输出；局限是结构/评分不确定以及缺少效率对照。第二种方法是具体细胞测定：ATP相关发光是间接活力指标，并非直接证明细胞死亡机制。Huh7与HEK293敏感性不同，不等于人体安全范围，也不证明作用完全由CDK20介导。',
3:'两个方向分别回应Q2两个缺口：①公平比较效率；②检验模型外推与作用机制。方案中的对照、重复与读出都是拟议设计。预先约定命中阈值再比较，不能事后按最佳结果选标准；本参考未捏造已测出的阈值。ADME指吸收、分布、代谢和排泄。',
4:'直接复用现成图，不增加术语清单。第一张图分开疾病、靶点、候选分子；第二张图用证据阶梯分开预测、结合、功能、细胞与患者证据。可请零基础读者复述两者区别，作为之后的实际理解检查。',
5:'第一条解释科学价值与边界；第二条给出日常信息判断行为。不要为了凑“生活影响”写成本已降低、药价已下降或患者已经获益。'}
for q in range(1,6):
    md.append(f'## Q{q} {titles[q]}\n')
    for suffix in ['i','ii']:
        md.append(f'### {suffix}. 英文填写版\n')
        for label,body in answers[str(q)+suffix]:md.append(f'**{label}:** {body}\n' if label else body+'\n')
    md.append('**中文理解：** '+notes[q]+'\n')
md.extend(['## Q6 视频大纲 / 6 marks\n','| Part | Content | Time | Member |','|---|---|---|---|'])
for r in schedule:md.append('| '+' | '.join(r)+' |')
md.extend(['\n**Worksheet初步计划：总时长20分钟；A、B、C、D暂列各5分钟。此表仅用于回答老师要求的rough outline，不是最终视频制作方案。实际分工、呈现形式及具体节奏以后再定。** 按老师notes的近似结构比例安排：引言6分钟（30%），主体与讨论10分钟（50%），结论4分钟（20%）。四人均需出镜并口头呈现；完整引用在结尾展示，同时每处重要发现就近标短引用。',
    '\n## 证据定位：老师追问时查哪里\n',
    '| 题目 | 本地证据编号 | 原文定位/材料 |',
    '|---|---|---|',
    '| Q1 | E08-E13、E17-E25 | Ren 2023：Target selection and identification；Generation of novel hits...；Results and discussion；Fig.5-9 |',
    '| Q2(i) | E09-E11、E25 | Ren 2023：Generation of novel hits targeting CDK20 by using AlphaFold predicted structures；Fig.3-5 |',
    '| Q2(ii) | E21-E23 | Ren 2023：Materials and methods / Cell viability assay；Fig.9B；Results and discussion |',
    '| Q3 | E23-E25、E30、E35 | 现有手册第六节；Ren原文后续工作及我们对缺口的评价。未来方案不是既有实验结果 |',
    '| Q4 | E03、E06、E14-E23、E34 | 手册白话表、证据层级表、图一/图四 |',
    '| Q5 | E13、E23-E25 | 手册第五节日常生活联系；附录四问答 |',
    '| Q6 | Tutorial 2 worksheet Q6；notes pp.12-19 | 时长、观众、结构、引用及成员参与要求 |',
    '\n## 已有素材怎样直接复用\n',
    '- 开头：内容图示/疾病-靶点-分子关系图。',
    '- 计算流程：现有方法协作流程图。',
    '- 结果：现有首轮到后续优化图，首轮30天与第二轮分开。',
    '- 讨论及结尾：现有证据层级图，并明确患者证据未在主案例中报告。',
    '\n## 核心来源\n',
    'Ren F, et al. AlphaFold accelerates artificial intelligence powered drug discovery: efficient discovery of a novel CDK20 small molecule inhibitor. Chemical Science. 2023;14:1443-1452. DOI: https://doi.org/10.1039/D2SC05709C',
    '\n现有本地文件：内容完整版.md；证据清单.csv；来源与核查说明.md；sources/Ren_2023_CDK20_fulltext.xml。以正式原文为科学结果来源，本答案不是我们执行计算、合成或细胞实验的记录。',
    '\n## 可复用自查提示词\n',
    '```text\n只用现有CDK20手册、证据清单和Ren 2023原文检查这份Tutorial 2答案。\n逐题检查是否回应所有子问；将每个结果对应到证据编号和原文定位。\n保留Tutorial 1实际提交的目标，区分早期命中、结合、功能、细胞和临床证据。\n核对30天起止与两轮数量；未来设计用将来语气，不写成完成结果。\n核对20分钟总和与四人各连续5分钟，成员标签必须由真实组员确认。\n```\n'])
(HERE/'Tutorial2_答案与中文解释.md').write_text('\n'.join(md),encoding='utf-8')
(HERE/'DIFF_FILE.txt').write_text('Changed fields: Q1(i-ii), Q2(i-ii), Q3(i-ii), Q4(i-ii), Q5(i-ii), Q6 outline.\nOriginal blank worksheet -> reference answers on a copy.\nQ1 preserves the two objectives actually written in Tutorial 1 photos.\nHeader identity fields unchanged/blank; Q6 A/B/C/D are four member labels; 5 continuous minutes each.\nOriginal SHA256: '+sha(SOURCE)+'\n\n'+json.dumps(answers,indent=2,ensure_ascii=False)+'\n\nQ6:\n'+json.dumps(schedule,indent=2),encoding='utf-8')
(HERE/'manifest.json').write_text(json.dumps({'source':str(SOURCE),'original_sha256':sha(SOURCE),'modified':str(OUTPUT),'modified_sha256':sha(OUTPUT)},indent=2,ensure_ascii=False),encoding='utf-8')
print('CREATED: 3-page filled reference PDF and bilingual answer guide')
