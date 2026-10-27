from pathlib import Path
import csv, hashlib, json, logging, shutil, zipfile
from datetime import datetime
from pypdf import PdfReader

logging.getLogger('pypdf').setLevel(logging.ERROR)
BASE = Path(__file__).resolve().parent.parent
TMP = BASE / '_build' / 'paper_download'
OUT = BASE / '参考文献下载'
OUT.mkdir(exist_ok=True)
rows = []
items = [
 ('S02', TMP/'ren_s3.pdf', 'S02_Ren_2023_CDK20主案例_正式全文.pdf', 'AlphaFold accelerates artificial intelligence powered drug discovery: efficient discovery of a novel CDK20 small molecule inhibitor', 'https://doi.org/10.1039/D2SC05709C', 'https://pmc-oa-opendata.s3.amazonaws.com/PMC9906638.1/PMC9906638.1.pdf', '论文全文；正式发表版本', 'AlphaFold accelerates', 10),
 ('S02-SI', BASE/'sources/SC-014-D2SC05709C-s001.pdf', 'S02_SI_CDK20主案例_化学合成补充材料.pdf', 'Supporting Information: CDK20 small molecule inhibitor', 'https://doi.org/10.1039/D2SC05709C', 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9906638/supplementaryFiles', '补充材料；复用此前下载的原始PDF', 'Supporting Information', 16),
 ('S03', BASE.parent/'pharmaceuticals-16-00253.pdf', 'S03_Wang_2023_AI抗癌药物设计综述.pdf', 'Advances of Artificial Intelligence in Anti-Cancer Drug Design: A Review of the Past Decade', 'https://doi.org/10.3390/ph16020253', '原有本地文件：pharmaceuticals-16-00253.pdf', '论文全文；复制已有文件，未修改内容', 'Anti-Cancer Drug Design', 18),
 ('S04', TMP/'af.pdf', 'S04_Jumper_2021_AlphaFold方法原文.pdf', 'Highly accurate protein structure prediction with AlphaFold', 'https://doi.org/10.1038/s41586-021-03819-2', 'https://www.nature.com/articles/s41586-021-03819-2.pdf', '论文全文；出版社PDF', 'Highly accurate protein structure', 12),
 ('S05', TMP/'chem_s3.pdf', 'S05_Ivanenkov_2023_Chemistry42方法原文.pdf', 'Chemistry42: An AI-Driven Platform for Molecular Design and Optimization', 'https://doi.org/10.1021/acs.jcim.2c01191', 'https://pmc-oa-opendata.s3.amazonaws.com/PMC9930109.1/PMC9930109.1.pdf', '论文全文；正式发表版本', 'Chemistry42:', 7),
 ('S05-SI', TMP/'chem_si.pdf', 'S05_SI_Chemistry42方法补充材料.pdf', 'Supporting Information: Chemistry42', 'https://doi.org/10.1021/acs.jcim.2c01191', 'https://pmc-oa-opendata.s3.amazonaws.com/PMC9930109.1/ci2c01191_si_001.pdf', '补充材料；额外收录，帮助理解方法', 'Supporting Information', 21),
 ('S08', TMP/'feng_jci.pdf', 'S08_Feng_2011_CDK20_CCRK靶点早期研究.pdf', 'Cell cycle-related kinase is a direct androgen receptor-regulated gene that drives beta-catenin/T cell factor-dependent hepatocarcinogenesis', 'https://doi.org/10.1172/JCI45967', 'https://www.jci.org/articles/view/45967/version/1/pdf/render.pdf', '论文全文；出版社PDF，含1页封面', 'hepatocarcinogenesis', 18),
 ('S10', BASE/'sources/Wiley_book_sample_3527312781.pdf', 'S10_Lengauer_2007_计算生物学书籍公开第一章.pdf', 'Bioinformatics — From Genomes to Therapies, Vol. 1, Chapter 1', 'https://application.wiley-vch.de/books/sample/3527312781_c01.pdf', 'https://application.wiley-vch.de/books/sample/3527312781_c01.pdf', '书籍公开章节；不是整本书，复用此前下载的原始PDF', 'Bioinformatics', 24),
]

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

for sid, src, name, title, doi, url, status, expected, pages in items:
    before = sha(src)
    dest = OUT/name
    shutil.copy2(src, dest)
    assert sha(dest) == before == sha(src)
    assert dest.read_bytes().startswith(b'%PDF-')
    reader = PdfReader(dest)
    assert len(reader.pages) == pages, (name, len(reader.pages))
    texts = [p.extract_text() or '' for p in reader.pages]
    assert expected.lower() in texts[0].lower(), (name, 'title mismatch')
    assert all(len(t.strip()) > 10 for t in texts), (name, 'empty page')
    rows.append({'来源编号':sid, '题名':title, '状态':status, '文件名':name,
                 '页数':pages, 'DOI或官网':doi, '实际获取来源':url,
                 'SHA256':before, '核查日期':'2026-10-07'})
    print(f'PDF_PASS | {sid} | pages={pages} | {name}', flush=True)

shutil.copy2(TMP/'bender.html', OUT/'S07_Bender_2026_出版社摘要页面_非全文.html')
assert (OUT/'S07_Bender_2026_出版社摘要页面_非全文.html').stat().st_size > 10000
shutil.copy2(BASE/'sources/Bender_2026_Crossref_metadata.json', OUT/'S07_Bender_2026_书目信息.json')
assert json.loads((OUT/'S07_Bender_2026_书目信息.json').read_text(encoding='utf-8'))
shared='https://rdcu.be/fyr77'
for name,url in [('S07_Bender_2026_作者提供的免费阅读链接.url',shared),('S01_NCI_肝癌官方介绍.url','https://www.cancer.gov/types/liver')]:
    (OUT/name).write_text('[InternetShortcut]\nURL='+url+'\n',encoding='utf-8')
rows.append({'来源编号':'S07','题名':'Artificial intelligence in drug discovery — what it is, where we stand and the path forward','状态':'公开摘要与书目信息已保存；全文PDF待补；作者提供免费在线阅读链接','文件名':'S07_Bender_2026_出版社摘要页面_非全文.html','页数':'','DOI或官网':'https://doi.org/10.1038/s41573-026-01496-2','实际获取来源':'出版社页面；作者官网 https://andreasbender.de/ 提供 '+shared,'SHA256':sha(OUT/'S07_Bender_2026_出版社摘要页面_非全文.html'),'核查日期':'2026-10-07'})
rows.append({'来源编号':'S01','题名':'Liver and Bile Duct Cancer','状态':'官方背景网页，非论文；附官网快捷方式','文件名':'S01_NCI_肝癌官方介绍.url','页数':'','DOI或官网':'https://www.cancer.gov/types/liver','实际获取来源':'官网链接','SHA256':sha(OUT/'S01_NCI_肝癌官方介绍.url'),'核查日期':'2026-10-07'})
with (OUT/'下载清单.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
shutil.copy2(BASE/'视频内容稿/证据索引.csv',OUT/'证据索引_对应视频稿.csv')

readme='''# 视频稿参考文献下载包

本包对应英文＋简中、英文＋繁中视频内容稿中的来源编号。编号保留原来的 S01、S02 等，不重新排序，以便与证据索引核对。

## 已收录
- 5 篇论文的完整 PDF：S02、S03、S04、S05、S08。
- 2 份补充材料 PDF：S02-SI、S05-SI。
- 1 份出版社公开书籍章节 PDF：S10，共24页，不是整本书。
- S07（2026 年领域评价文章）：保存了出版社公开摘要页面、书目信息和作者提供的免费在线阅读链接。全文 PDF 待补，摘要页面不是全文。
- S01 是 NCI 官方疾病背景网页，不是论文；附上官网链接。
- 下载清单记录各文件的来源、页数、状态与 SHA256；证据索引保留视频稿中的35条证据编号。

## 建议先读哪几个
1. **S02 主案例**：最重要。先看摘要、流程图、生成与筛选过程、实验结果和讨论。
2. **S02-SI 补充材料**：查真实合成和化学表征；不必从头背下来。
3. **S04 AlphaFold 与 S05 Chemistry42**：分别解释预测蛋白形状、生成与评价候选分子。
4. **S03 综述**：理解计算辅助药物发现的背景。
5. **S08 早期靶点研究**：解释为什么会研究 CDK20/CCRK；不是2023年候选分子的动物实验。
6. **S07 评价文章与 S10 书籍章节**：用于理解局限、概念与证据质量。

## S07 的阅读入口
- 作者官网：https://andreasbender.de/
- 作者公开提供的免费阅读链接：https://rdcu.be/fyr77
- 出版社页面：https://www.nature.com/articles/s41573-026-01496-2
- 若需下载正式全文 PDF，可从学校图书馆登录出版社页面后查看 Download PDF。
- 本次视频稿对 S07 的使用仍限于公开摘要与元数据；不将取得阅读链接说成已经核查全文。

## 文件核查
所有8份PDF均检查了PDF文件头、页数、首页题名与每页文本读取；已重新打开。原PDF未改写。本轮仅下载和整理文献，没有改动视频稿。
'''
(OUT/'先读我_阅读顺序与下载状态.md').write_text(readme,encoding='utf-8')
assert len(list(csv.DictReader((OUT/'下载清单.csv').open(encoding='utf-8-sig'))))==10
manifest={p.name:sha(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='文件校验_SHA256.json'}
(OUT/'文件校验_SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
for name,h in json.loads((OUT/'文件校验_SHA256.json').read_text(encoding='utf-8')).items():assert sha(OUT/name)==h
assert (OUT/'先读我_阅读顺序与下载状态.md').read_text(encoding='utf-8')==readme
assert (OUT/'证据索引_对应视频稿.csv').read_bytes()==(BASE/'视频内容稿/证据索引.csv').read_bytes()
zip_path=BASE/'视频稿参考文献下载包.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.iterdir()):
        if p.is_file():z.write(p,arcname=OUT.name+'/'+p.name)
with zipfile.ZipFile(zip_path) as z:
    assert z.testzip() is None
    for p in OUT.iterdir():
        if p.is_file():assert hashlib.sha256(z.read(OUT.name+'/'+p.name)).hexdigest()==sha(p)
report='PDF_FILES=8; FULL_PAPERS=5; SUPPLEMENTS=2; BOOK_CHAPTERS=1\nPDF_HEADER_TITLE_PAGECOUNT_ALL_PAGE_TEXT=PASS\nCOPIED_SOURCE_HASHES_UNCHANGED=PASS\nS07_FULL_PDF=PENDING; ABSTRACT_METADATA_AND_AUTHOR_READ_LINK=INCLUDED\nINDEX_CSV_AND_FILE_MANIFEST_REOPENED=PASS\nZIP_CRC_AND_FILE_HASHES=PASS\n'
(BASE/'_build/论文下载验证.txt').write_text(report,encoding='utf-8')
assert (BASE/'_build/论文下载验证.txt').read_text(encoding='utf-8')==report
print(report)
print('FOLDER',OUT)
print('ZIP',zip_path,'BYTES',zip_path.stat().st_size)
