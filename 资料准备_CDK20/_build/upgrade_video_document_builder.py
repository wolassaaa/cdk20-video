from pathlib import Path
p=Path(__file__).with_name('build_video_documents.py')
s=p.read_text(encoding='utf-8')
s=s.replace("shutil.copy2(BASE/'证据清单.csv',OUT/'证据索引.csv')", "# Revised evidence index retains the original 35 rows and adds E36/E37.")
a=s.index(" d.add_paragraph(c(data['title_sc']),style='Title')")
b=s.index(" for i,s in enumerate(data['sections']):",a)
s=s[:a]+''' d.add_paragraph('Can AI help design a molecule worth testing?',style='Title')
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
 toc=d.add_paragraph();fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'TOC \\\\o "1-1" \\\\h \\\\z \\\\u');toc._p.append(fld)
 for name in ['TOC 1']:
  if name in d.styles:
   d.styles[name].font.size=Pt(9);d.styles[name].paragraph_format.space_after=Pt(2)
 d.add_page_break()
''' +s[b:]
s=s.replace("head=d.add_heading(s['id']+'  '+c(s['title_sc']),1)","head=d.add_heading(s['id']+'  '+s['title_en'],1)")
s=s.replace("para(d,s['title_en'],10,color='444444',keep=True,after=8)","para(d,c(s['title_sc'])+'  |  '+s['role_en'],10,color='444444',keep=True,after=8)")
s=s.replace("  for p in s['paragraphs']:\n   para", "  for p in s['paragraphs']:\n   if s['id']=='C08' and p['id'] in ['P30','P35','P37']:\n    labels={'P30':('Benefits and trade-offs','收益与代价'),'P35':('Challenges and future directions','挑战与未来方向'),'P37':('Conclusion and daily-life relevance','结论与日常生活联系')}\n    en,zh=labels[p['id']];para(d,en+' / '+c(zh),11,bold=True,keep=True,after=6)\n   para")
anchor=" footer=sec.footer.paragraphs[0]"
appendix=''' h=d.add_heading('Teacher requirements and final checks',1);h.paragraph_format.page_break_before=True
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
'''
s=s.replace(anchor,appendix+anchor)
a=s.index("(OUT/'阅读说明.txt').write_text(")
s=s[:a]+'''(OUT/'阅读说明.txt').write_text('两份稿件共用一份英文口播；共38段、2233词。正文英文才是口播，中文及所有附录不朗读。\\n目录是可点击的Word目录，PDF也可点击。章节C、来源S、证据E、课程文件T分别编号。\\n新增伦理与环境讨论只谈潜力和需要的比较证据，不宣称已经节省成本、减少动物使用或总体更环保。\\n完整成片15–20分钟；实际英文试读、四人出镜口述、字幕与音画质量等待后续检查。\\n本次修订保留旧版备份，原始科研文献及此前资料包未修改。',encoding='utf-8')
'''
p.write_text(s,encoding='utf-8')
compile(s,str(p),'exec')
print('BUILDER_UPDATED')
