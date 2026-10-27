from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether, Table, TableStyle
from pypdf import PdfReader
import json

BASE=Path(__file__).resolve().parent.parent
OUT=BASE/'组员讨论用_研究问题微调.pdf'
pdfmetrics.registerFont(TTFont('YaHei','C:/Windows/Fonts/msyh.ttc',subfontIndex=0))
pdfmetrics.registerFont(TTFont('YaHeiBold','C:/Windows/Fonts/msyhbd.ttc',subfontIndex=0))
pdfmetrics.registerFontFamily('YaHei',normal='YaHei',bold='YaHeiBold',italic='YaHei',boldItalic='YaHeiBold')

styles={
 'title':ParagraphStyle('title',fontName='YaHeiBold',fontSize=20,leading=28,textColor=colors.black,spaceAfter=8),
 'sub':ParagraphStyle('sub',fontName='YaHei',fontSize=9.5,leading=15,textColor=colors.HexColor('#626B75'),spaceAfter=17),
 'heading':ParagraphStyle('heading',fontName='YaHeiBold',fontSize=12,leading=18,textColor=colors.black,spaceBefore=12,spaceAfter=7),
 'body':ParagraphStyle('body',fontName='YaHei',fontSize=10.6,leading=17.6,textColor=colors.HexColor('#20262D'),spaceAfter=7,wordWrap='CJK'),
 'refs':ParagraphStyle('refs',fontName='YaHei',fontSize=9.8,leading=16,textColor=colors.HexColor('#20262D'),spaceAfter=6,wordWrap='CJK'),
 'box':ParagraphStyle('box',fontName='YaHei',fontSize=10.5,leading=18,textColor=colors.HexColor('#20262D'),wordWrap='CJK'),
}
story=[]
def p(text,style='body'):story.append(Paragraph(text,styles[style]))
def heading(text):p(text,'heading')

p('肝癌候选分子研究方向微调','title')
p('供小组讨论  |  聚焦研究问题与资料可行性','sub')

heading('微调后的研究问题')
p('<b>AI 怎样帮助研究者更高效地发现肝癌候选分子？已有研究支持哪些优点，又有哪些仍需要验证？</b>')
p('这次把较宽泛的癌症药物研究收紧到一个具体案例。重点放在前期怎样提出、筛选和改进值得实验的分子，而不是诊断患者或介绍药物工业生产。')

heading('准备采用的具体案例')
p('主案例是 Ren 等人 2023 年发表的研究，针对肝癌相关蛋白 CDK20 寻找候选分子。研究结合 AI、其他计算方法和真实实验，既有计算流程，也有合成与测试结果。')
p('论文报告，从选择研究靶点到得到第一个实验确认能结合目标蛋白的分子，用了 <b>30 天</b>；之后又进行了进一步优化。这是早期研究结果，不是“30 天做出了上市药”，也不直接证明比其他方法快多少倍。')

heading('内容准备围绕什么展开')
p('<b>肝癌研究需求 → 选择药物作用对象 → 计算设计与筛选分子 → 合成和实验验证 → 评价收益与局限。</b>')
p('选靶只是故事起点，主体放在分子设计与验证。我们主要讨论：是否有助于较快获得前期结果、探索新的分子，以及让实验选择更有针对性。每个优点都回到论文结果，不只介绍 AI 技术名称。')

heading('已找到的主要参考文章')
refs=[
 ('Ren 等，2023，Chemical Science','主案例：肝癌相关 CDK20 候选分子的发现与验证。','https://doi.org/10.1039/D2SC05709C'),
 ('Jumper 等，2021，Nature','方法参考：AlphaFold 如何预测蛋白结构。','https://doi.org/10.1038/s41586-021-03819-2'),
 ('Ivanenkov 等，2023，JCIM','方法参考：Chemistry42 怎样生成和评价分子。','https://doi.org/10.1021/acs.jcim.2c01191'),
 ('Wang 等，2023，Pharmaceuticals','综述参考：AI 在抗癌药物设计中的应用。','https://doi.org/10.3390/ph16020253'),
]
for name,desc,url in refs:
 p(f'<link href="{url}" color="#234B69"><b>{name}</b></link><br/>{desc}','refs')

story.append(Spacer(1,11))
box=Table([[Paragraph('<b>想请大家判断</b><br/>这个问题是否够聚焦、容易讲清？主案例是否足以支持效率与优点的讨论？研究问题或资料方向还有哪些需要调整？',styles['box'])]],colWidths=[503.3])
box.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#F1F4F6')),('LEFTPADDING',(0,0),(-1,-1),13),('RIGHTPADDING',(0,0),(-1,-1),13),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
story.append(KeepTogether([box]))

def footer(c,doc):
 c.setFont('YaHei',8.3);c.setFillColor(colors.HexColor('#68727B'))
 c.drawString(46,26,'讨论稿  |  文献研究方向，不是已完成的药物实验')
 c.drawRightString(A4[0]-46,26,str(doc.page))

doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=46,leftMargin=46,topMargin=39,bottomMargin=44,title='肝癌候选分子研究方向微调',author='SCIE1007 项目资料',pageCompression=1)
doc.build(story,onFirstPage=footer,onLaterPages=footer)
r=PdfReader(OUT)
text='\n'.join(page.extract_text() or '' for page in r.pages)
links=[]
for page in r.pages:
 for a in page.get('/Annots',[]):
  action=a.get_object().get('/A',{})
  if action.get('/URI'):links.append(str(action['/URI']))
checks={'one_page':len(r.pages)==1,'question_present':'AI 怎样帮助研究者' in text,'case_present':'CDK20' in text,'scope_clear':'不是“30 天做出了上市药”' in text,'sources_clickable':len(links)==4,'peer_review_request':'想请大家判断' in text}
(BASE/'_build/brief_checks.json').write_text(json.dumps({'pdf':str(OUT),'pages':len(r.pages),'checks':checks,'links':links,'characters':len(text)},ensure_ascii=False,indent=2),encoding='utf-8')
print('PDF',OUT)
print('PAGES',len(r.pages),'LINKS',len(links),'TEXT_CHARS',len(text),'CHECKS',checks)
assert all(checks.values()),checks
