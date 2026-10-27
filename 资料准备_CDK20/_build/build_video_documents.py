from pathlib import Path
import json,csv,shutil,sys
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.enum.text import WD_ALIGN_PARAGRAPH
BASE=Path(__file__).resolve().parent.parent;OUT=BASE/'视频内容稿'/'教师要求补齐版'
sys.path.insert(0,str(BASE/'_build/script_dependencies'))
from opencc import OpenCC
cc=OpenCC('s2t')
def tc(s):return cc.convert(s).replace('爲','為').replace('纔','才').replace('覈','核')
data=json.loads((OUT/'双语内容主稿.json').read_text(encoding='utf-8'))
# Revised evidence index retains the original 35 rows and adds E36/E37.
refs=[
('S01','National Cancer Institute. Liver and Bile Duct Cancer.','https://www.cancer.gov/types/liver','疾病定义；官方网页。'),
('S02','Ren F, et al. AlphaFold accelerates artificial intelligence powered drug discovery: efficient discovery of a novel CDK20 small molecule inhibitor. Chemical Science. 2023;14:1443–1452.','https://doi.org/10.1039/D2SC05709C','主案例；正式全文与16页化学补充材料已核查。流程、数字及实验以此为准。'),
('S03','Wang L, et al. Advances of Artificial Intelligence in Anti-Cancer Drug Design: A Review of the Past Decade. Pharmaceuticals. 2023;16:253.','https://doi.org/10.3390/ph16020253','背景综述；全文已核查，不替代主案例实验。'),
('S04','Jumper J, et al. Highly accurate protein structure prediction with AlphaFold. Nature. 2021;596:583–589.','https://doi.org/10.1038/s41586-021-03819-2','结构预测方法；全文已核查。'),
('S05','Ivanenkov YA, et al. Chemistry42: An AI-Driven Platform for Molecular Design and Optimization. Journal of Chemical Information and Modeling. 2023;63:695–701.','https://doi.org/10.1021/acs.jcim.2c01191','平台方法；全文已核查，与主案例团队有重叠，不是独立重复验证。'),
('S07','Bender A, et al. Artificial intelligence in drug discovery — what it is, where we stand and the path forward. Nature Reviews Drug Discovery. Published online 7 August 2026.','https://doi.org/10.1038/s41573-026-01496-2','评价视角；只使用公开摘要与元数据，不引用未读全文的数值。'),
('S08','Feng H, et al. Cell cycle-related kinase is a direct androgen receptor-regulated gene that drives β-catenin/T cell factor-dependent hepatocarcinogenesis. Journal of Clinical Investigation. 2011;121:3159–3175.','https://www.jci.org/articles/view/45967','前期靶点依据；全文已核查，不是2023年候选分子的动物试验。'),
('S10','Lengauer T, ed. Bioinformatics — From Genomes to Therapies. Vol. 1. Wiley-VCH, 2007. Public Chapter 1, pp.1–24; especially p.7.','https://application.wiley-vch.de/books/sample/3527312781_c01.pdf','实际读到的学术书章节；解释靶点、分子及选择性，不用于推导当前AI效率。'),
]
def runfont(r,size=11,bold=False,color='000000'):
 r.font.name='Calibri';r.font.size=Pt(size);r.font.bold=bold;r.font.color.rgb=RGBColor.from_string(color);r._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'Microsoft YaHei')
def para(d,text,size=11,bold=False,color='000000',keep=False,after=5):
 p=d.add_paragraph();p.paragraph_format.keep_with_next=keep;p.paragraph_format.widow_control=True;p.paragraph_format.space_after=Pt(after);runfont(p.add_run(text),size,bold,color);return p
def hyperlink(d,text,url):
 p=d.add_paragraph();p.paragraph_format.space_after=Pt(3);p.paragraph_format.keep_with_next=True
 link=OxmlElement('w:hyperlink');link.set(qn('r:id'),p.part.relate_to(url,RT.HYPERLINK,is_external=True));r=OxmlElement('w:r');pr=OxmlElement('w:rPr');sz=OxmlElement('w:sz');sz.set(qn('w:val'),'18');pr.append(sz);c=OxmlElement('w:color');c.set(qn('w:val'),'254F6B');pr.append(c);r.append(pr);t=OxmlElement('w:t');t.text=text;r.append(t);link.append(r);p._p.append(link)
for edition,field in [('简中','zh_sc'),('繁中','zh_tc')]:
 c=lambda s:tc(s) if edition=='繁中' else s
 d=Document();sec=d.sections[0];sec.page_width=Cm(21);sec.page_height=Cm(29.7);sec.top_margin=sec.bottom_margin=Cm(1.7);sec.left_margin=sec.right_margin=Cm(1.9);sec.footer_distance=Cm(.8)
 for name,size in [('Normal',11),('Title',21),('Subtitle',10),('Heading 1',15)]:
  st=d.styles[name];st.font.name='Calibri';st.font.size=Pt(size);st.font.color.rgb=RGBColor(0,0,0);st._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'Microsoft YaHei');st.paragraph_format.space_after=Pt(7);st.paragraph_format.line_spacing=1.13
  for e in list(st._element.xpath('.//w:pBdr')):e.getparent().remove(e)
  if name in ('Title','Heading 1'):st.font.bold=True
 d.core_properties.title=c(data['title_sc'])+' '+c('英文与中文对照视频内容稿');d.core_properties.author='SCIE1007 project group'
 d.add_paragraph('Can AI help design a molecule worth testing?',style='Title')
 d.add_paragraph(c(data['title_sc']),style='Subtitle')
 para(d,c('英文＋'+('简体中文' if edition=='简中' else '繁体中文')+'对照内容稿  |  教师要求补齐版 v2  |  2026年10月7日'),9,color='444444')
 para(d,c('主题：Computer-aided drug discovery and its benefits。英文为口播；中文、目录、证据编号和附录用于审阅，不朗读。'),9,after=7)
 para(d,'Research question / '+c('研究问题'),10,bold=True,keep=True,after=3)
 para(d,data['research_question_en'],10,keep=True,after=3)
 para(d,c(data['research_question_sc']),9.5,after=7)
 para(d,'Objectives / '+c('两个研究目标'),10,bold=True,keep=True,after=3)
 for n,o in enumerate(data['objectives'],1):
  para(d,str(n)+'. '+o['en'],9.5,keep=True,after=2)
  para(d,c(o['zh_sc']),9.5,after=5)
 words=data['english_word_count']
 para(d,c(f'英文正文 {words:,} 词；每分钟120–135词时，纯口播估算{words/135:.1f}–{words/120:.1f}分钟。最终成片含片头、停顿和参考文献须控制在15–20分钟；尚待实际试读。'),8.5,color='444444',after=7)
 para(d,'Contents / '+c('目录'),11,bold=True,keep=True,after=4)
 toc=d.add_paragraph();fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'TOC \\o "1-1" \\h \\z \\u');toc._p.append(fld)
 for name in ['TOC 1']:
  if name in d.styles:
   d.styles[name].font.size=Pt(9);d.styles[name].paragraph_format.space_after=Pt(2)
 d.add_page_break()
 for i,s in enumerate(data['sections']):
  head=d.add_heading(s['id']+'  '+s['title_en'],1)
  head.paragraph_format.space_before=Pt(12)
  para(d,c(s['title_sc'])+'  |  '+s['role_en'],10,color='444444',keep=True,after=8)
  for p in s['paragraphs']:
   if s['id']=='C08' and p['id'] in ['P30','P35','P37']:
    labels={'P30':('Benefits and trade-offs','收益与代价'),'P35':('Challenges and future directions','挑战与未来方向'),'P37':('Conclusion and daily-life relevance','结论与日常生活联系')}
    en,zh=labels[p['id']];para(d,en+' / '+c(zh),11,bold=True,keep=True,after=6)
   para(d,p['id']+'  EN',8.5,bold=True,color='444444',keep=True,after=3)
   para(d,p['en'],11,keep=True,after=5)
   para(d,p[field],10.5,color='333333',keep=True,after=4)
   para(d,c('核对依据：')+' · '.join(p['refs']),8,color='555555',after=11)
 h=d.add_heading(c('证据与参考资料'),1);h.paragraph_format.page_break_before=True
 para(d,c('本页不属于口播。E编号对应同文件夹的《证据索引.csv》，其中记录原文章节、图号、结果与推论边界。未来比较方案是我们的建议，不是已经实施的实验。'),10,after=9)
 for sid,bib,url,note in refs:
  para(d,sid+'  '+bib,9.5,keep=True,after=3);hyperlink(d,url,url);para(d,c(note),9,color='333333',after=8)
 h=d.add_heading('Teacher requirements and final checks',1);h.paragraph_format.page_break_before=True
 para(d,c('老师要求与最终检查（内部附录，不朗读）'),11,bold=True,after=8)
 notes=[
 ('Structure — 20%','概览C01、引入C02、主体C03–C07，以及C08的收益、未来方向和结论。问题式讲法保留，不要求照老师课件页序讲。'),
 ('Content — 30%','主题覆盖计算方法、具体疾病案例和已有/潜在收益；预测、结合、功能、细胞和患者证据分别说明。'),
 ('Literature — 10%','期刊原始论文、综述、学术书章节各有用途，并评价相关性与来源边界。S07仍只使用公开摘要。'),
 ('Audience — 10%','概念按需解释；日常生活联系落在理解AI新药新闻，不暗示已经治疗患者。'),
 ('Critical thinking — 5%','讨论可靠性和效率归因；提出公平比较、实验反馈、多性质评价三条研究方向。'),
 ('Teamwork — 5%','四位成员均须出镜且口头讲解，除非已获老师许可；只署名或只幕后制作不满足要求。该项等待实际视频核对。'),
 ('Delivery and visuals — 20%','清晰英文表达与有助理解的视觉呈现分别占10%；内容稿不能证明成片已达到，等待后续制作检查。'),
 ('Submission','15–20分钟，2026年11月27日23:59前在所属lab section的Moodle提交视频，mp4等格式可用；以之后课程公告更新为准。'),
 ('AI assistance','本稿使用AI协助整理、起草和简繁转换；学生需自行阅读、核查与理解。最终按实际使用情况说明工具与用途，不把本草稿中的核查等同于组员已经完成。')]
 for en,zh in notes:para(d,en+' — '+c(zh),9.5,after=6)
 para(d,c('课程文件依据：以下T编号是老师文件，不是新增科研论文。目录/字体/APA格式没有在已核对文件中被指定；本稿排版属于审阅建议。'),9,after=6)
 teacher=[('T01','Group_Project_Rubrics_for_Moodle.pdf','1'),('T02','Group Project Introduction.pdf','45–49'),('T03','Overview of Projects.pdf','2–3'),('T04','Lab course introduction.pdf','9'),('T05','Guidelines for generative AI for SCIE 1007.pdf','5')]
 for tid,name,pages in teacher:para(d,tid+'  '+name+' | '+c('PDF页')+pages,8.5,after=3)
 para(d,c('新增E36/E37来自T02第49页的讨论维度，加上主案例范围与本稿条件性分析；不是新增资源节省或动物使用的实验结果。完整状态表见《持续核查清单.md》。'),9,after=6)
 footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT;runfont(footer.add_run(c('视频内容稿  |  ')),8,color='555555');f=OxmlElement('w:fldSimple');f.set(qn('w:instr'),'PAGE');footer._p.append(f)
 path=OUT/f'视频内容稿_英文加{edition}.docx';d.save(path);reopened=Document(path);assert len(reopened.paragraphs)>100;print('DOCX_CREATED',path)
english='\n\n'.join(p['en'] for s in data['sections'] for p in s['paragraphs'])
(OUT/'英文口播纯文本.txt').write_text(english,encoding='utf-8')
(OUT/'阅读说明.txt').write_text('两份稿件共用一份英文口播；共38段、2233词。正文英文才是口播，中文及所有附录不朗读。\n目录是可点击的Word目录，PDF也可点击。章节C、来源S、证据E、课程文件T分别编号。\n新增伦理与环境讨论只谈潜力和需要的比较证据，不宣称已经节省成本、减少动物使用或总体更环保。\n完整成片15–20分钟；实际英文试读、四人出镜口述、字幕与音画质量等待后续检查。\n本次修订保留旧版备份，原始科研文献及此前资料包未修改。',encoding='utf-8')
