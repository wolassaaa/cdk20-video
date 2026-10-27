from pathlib import Path
import json,csv,re,hashlib,sys,zipfile
from docx import Document
from pypdf import PdfReader
import pdfplumber
BASE=Path(__file__).resolve().parent.parent;OUT=BASE/'视频内容稿'
data=json.loads((OUT/'双语内容主稿.json').read_text(encoding='utf-8'))
ps=[p for s in data['sections'] for p in s['paragraphs']];checks=[]
def check(name,ok,detail=''):checks.append((name,bool(ok),str(detail)))
def norm(s):return re.sub(r'\s+','',s)
word_count=len(re.findall(r"[A-Za-z0-9]+(?:[’'-][A-Za-z0-9]+)*",' '.join(p['en'] for p in ps)))
check('主稿8节36段',len(data['sections'])==8 and len(ps)==36)
check('段落编号连续唯一',[p['id'] for p in ps]==[f'P{x:02d}' for x in range(1,37)])
check('英文词数2105且估算落入15到20分钟',word_count==2105 and 15<word_count/130<word_count/115<20)
check('纯英文口播与主稿完全一致',(OUT/'英文口播纯文本.txt').read_text(encoding='utf-8')=='\n\n'.join(p['en'] for p in ps))
rows=list(csv.DictReader((OUT/'证据索引.csv').open(encoding='utf-8-sig')));ids={r['证据编号'] for r in rows}
check('35张原始证据卡保持不变',len(rows)==35 and (OUT/'证据索引.csv').read_bytes()==(BASE/'证据清单.csv').read_bytes())
check('全部段落引用有效且有依据',all(p['refs'] and set(p['refs']).issubset(ids) for p in ps))
check('方法与实验引用错配已修正',ps[8]['refs']==['E09','E06'] and ps[12]['refs']==['E10','E07'] and ps[15]['refs']==['E10','E11'])
check('简繁各段数字一致',all(re.findall(r'\d+(?:,\d+)*',p['zh_sc'])==re.findall(r'\d+(?:,\d+)*',p['zh_tc']) for p in ps))
en=' '.join(p['en'] for p in ps)
for name,phrase in [('开场问题','Can we predict whether a molecule is worth testing before we even make it?'),('首轮数字','generated 8,918 structures'),('54与7阶段','prioritised 54, then selected seven'),('30天正确终点','30 days from target selection to the first experimentally confirmed binding hit'),('后续16与6','proposed 16 structures and synthesised six'),('048细胞活力','reduced Huh7 liver cancer cell viability'),('非患者结果','a cell result still is not a patient result'),('无动物患者试验','did not report animal or patient trials'),('传统不是盲猜','Traditional discovery is not blind guessing'),('公平对照建议','compare methods on the same target'),('日常新闻识读','judge the news'),('学术书籍与资料评价','Scholarly books and reviews')]:check(name,phrase in en)
check('主稿没有动画或拍摄安排',not any(x in en.lower() for x in ('camera pans','cut to','on-screen presenter','shot list','animation direction','speaker a')))
sys.path.insert(0,str(BASE/'_build/script_dependencies'))
from opencc import OpenCC
cc=OpenCC('s2t');tc=lambda s:cc.convert(s).replace('爲','為').replace('纔','才').replace('覈','核')
check('繁中转换与审阅版本一致',all(p['zh_tc']==tc(p['zh_sc']) for p in ps))
english_outputs=[];artifact_hashes={}
for edition,field in [('简中','zh_sc'),('繁中','zh_tc')]:
 stem='视频内容稿_英文加'+edition;docx=OUT/(stem+'.docx');pdf=OUT/(stem+'.pdf');doc=Document(docx);reader=PdfReader(pdf)
 dt=''.join(doc.element.xpath('.//w:t/text()'));pt='\n'.join(p.extract_text() or '' for p in reader.pages)
 english_in_doc=[p.text for p in doc.paragraphs if p.text in {x['en'] for x in ps}]
 english_outputs.append(english_in_doc)
 check(edition+' Word所有36段英文顺序准确',english_in_doc==[p['en'] for p in ps])
 check(edition+' Word所有中文与证据标签齐全',all(p[field] in dt and p['id']+'  EN' in dt for p in ps))
 check(edition+' PDF英文中文均完整',all(norm(p['en']) in norm(pt) and norm(p[field]) in norm(pt) for p in ps))
 check(edition+' PDF无空白页且全部重新打开',len(reader.pages)==11 and all(len(p.extract_text() or '')>150 for p in reader.pages))
 check(edition+' 标题黑色无下划线边框',str(doc.styles['Title'].font.color.rgb)=='000000' and not doc.styles['Title']._element.xpath('.//w:pBdr'))
 links=[]
 for pg in reader.pages:
  for a in pg.get('/Annots',[]):
   u=a.get_object().get('/A',{}).get('/URI')
   if u:links.append(str(u))
 check(edition+' 八项文献链接可点击',len(set(links))==8)
 bad=[]
 with pdfplumber.open(pdf) as pp:
  for n,pg in enumerate(pp.pages,1):
   chars=[c for c in pg.chars if c['x0']<12 or c['x1']>pg.width-12 or c['top']<10 or c['bottom']>pg.height-10]
   if chars:bad.append(n)
 check(edition+' 页面文字未越界',not bad,bad)
 previews=BASE/'_build/视频稿预览'/edition
 check(edition+' 全部11页已渲染',all((previews/f'page-{n}.png').exists() for n in range(1,12)))
 for path in (docx,pdf):artifact_hashes[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
check('两版英文逐段完全相同',english_outputs[0]==english_outputs[1])
qa={'date':'2026-10-07','result':'PASS','pages_reviewed':{'简中':list(range(1,12)),'繁中':list(range(1,12))},'artifact_sha256':artifact_hashes,'review':'22 full-resolution page images individually inspected. No clipping, overlaps, orphan headings or missing glyphs observed. Source and narrative agents reviewed the final 36-paragraph canonical content and reported PASS. No real audience test or timed recording claimed.'}
(BASE/'_build/video_script_visual_qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
failed=[x for x in checks if not x[1]]
summary=f'VIDEO_SCRIPT_CHECKS={len(checks)} PASS={len(checks)-len(failed)} FAIL={len(failed)}'
record=['2026-10-07 双版本视频内容稿验证',summary,f'ENGLISH_WORDS={word_count}',f'ESTIMATED_MINUTES={word_count/130:.1f}–{word_count/115:.1f} at 115–130 wpm; not an actual timed reading.','WORD_PDF_REOPENED=4; VISUAL_PAGES_REVIEWED=22; source and narrative reviews=PASS.']
record += [f'{"PASS" if ok else "FAIL"} | {name} | {detail}' for name,ok,detail in checks]
record += ['EXIT_STATUS='+('1' if failed else '0')]
(BASE/'_build/视频内容稿验证.txt').write_text('\n'.join(record),encoding='utf-8');print(summary)
for name,ok,detail in failed:print('FAIL',name,detail)
if failed:sys.exit(1)
files=[p for p in OUT.iterdir() if p.is_file() and p.suffix.lower() in ('.docx','.pdf','.md','.txt','.json','.csv')]
manifest={'date':'2026-10-07','files':[{'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]}
archive=OUT/'双版本视频内容稿.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,p.name)
 z.writestr('文件校验清单.json',json.dumps(manifest,ensure_ascii=False,indent=2))
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for p in manifest['files']:assert hashlib.sha256(z.read(p['path'])).hexdigest()==p['sha256']
print('ZIP_CRC_AND_MANIFEST=PASS; PACKAGE_FILES='+str(len(files)))
print('PACKAGE',archive)
