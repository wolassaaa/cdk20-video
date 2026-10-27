from pathlib import Path
import csv, hashlib, json, logging, re, sys
import xml.etree.ElementTree as ET
from pypdf import PdfReader

BASE=Path(__file__).resolve().parent.parent
logging.getLogger('pypdf').setLevel(logging.ERROR)
checks=[]

def check(label, condition, detail=''):
    checks.append((label,bool(condition),detail))

main=BASE/'内容资料包.md'
notes=BASE/'来源与核查说明.md'
body=main.read_text(encoding='utf-8')
source_notes=notes.read_text(encoding='utf-8')
with (BASE/'证据清单.csv').open(encoding='utf-8-sig',newline='') as f:
    rows=list(csv.DictReader(f))
ids={r['证据编号'] for r in rows}
check('主资料包重新打开',len(body)>6000,f'characters={len(body)}')
check('来源说明重新打开',len(source_notes)>1500,f'characters={len(source_notes)}')
check('CSV格式与编号',len(rows)==35 and ids=={f'E{i:02d}' for i in range(1,36)},f'rows={len(rows)} unique_ids={len(ids)}')
check('CSV字段完整',all(len(r)==15 and all(str(v).strip() for v in r.values()) for r in rows),'15 fields; no empty values')
check('Excel中文编码',(BASE/'证据清单.csv').read_bytes().startswith(b'\xef\xbb\xbf'),'UTF-8 BOM')
refs=set(re.findall(r'\bE\d{2}\b',body))
check('正文证据引用均存在',refs.issubset(ids),f'referenced={len(refs)}')
source_ids={'S01','S02','S02-SI','S03','S04','S05','S06','S07','S08','S09','S10','T01'}
check('证据来源编号有效',all(set(r['来源编号'].split(';')).issubset(source_ids) for r in rows))

root=ET.parse(BASE/'sources/Ren_2023_CDK20_fulltext.xml').getroot()
t=re.sub(r'\s+',' ',' '.join(root.itertext()))
doi=root.find(".//article-id[@pub-id-type='doi']").text
check('主案例正式DOI',doi.lower()=='10.1039/d2sc05709c',doi)
needles=['8918 molecules','54 molecules','7 compounds','30 days','9.2 ± 0.5','>6000','16 novel molecules','6 out of 16','566.7 ± 256.2','360.0 ± 14.1','33.4 ± 22.6','208.7 ± 3.3','1706.7 ± 670.0','three independent experiments']
for needle in needles:
    check('原文数值匹配 '+needle,needle in t)
check('正式版本单位换算',abs(9.2*1000-9200)<1e-10 and '1 μM 等于 1,000 nM' in body)
for filename,doi_expected in [('AlphaFold_2021_fulltext.xml','10.1038/s41586-021-03819-2'),('Chemistry42_2023_fulltext.xml','10.1021/acs.jcim.2c01191')]:
    x=ET.parse(BASE/'sources'/filename).getroot()
    d=x.find(".//article-id[@pub-id-type='doi']").text
    check('方法全文重新解析 '+filename,d.lower()==doi_expected,d)

pdf=BASE/'sources/SC-014-D2SC05709C-s001.pdf'
r=PdfReader(pdf)
st=' '.join((p.extract_text() or '') for p in r.pages)
check('补充材料重新打开',len(r.pages)==16 and 'ISM042-2-001' in st and 'ISM042-2-048' in st,'pages=16; compounds found')
page_index=json.loads((BASE/'sources/补充材料页索引.json').read_text(encoding='utf-8'))
check('逐页索引完整',len(page_index)==16 and [p['page'] for p in page_index]==list(range(1,17)))
index=(BASE/'sources/正文定位索引.txt').read_text(encoding='utf-8')
check('正文定位索引重新打开','Results and discussion' in index and 'Fig. 9' in index)

originals=json.loads((BASE/'sources/input_hashes_before.json').read_text(encoding='utf-8'))
for filename,old_hash in originals.items():
    new_hash=hashlib.sha256((BASE.parent/filename).read_bytes()).hexdigest()
    check('原有资料未改动 '+filename,new_hash==old_hash,new_hash)

manifest=json.loads((BASE/'sources/source_manifest.json').read_text(encoding='utf-8'))
for item in manifest:
    path=Path(item['file']);b=path.read_bytes()
    check('来源文件完整 '+path.name,len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256'])

for heading in ['一 我们为肝癌寻找的是什么','二 为什么早期药物发现需要计算帮助','三 主案例中的方法怎样协作','四 主案例实际得到什么结果','五 药物发现的优点怎样体现','六 怎样评价原因而不是只展示好结果','七 下一步研究怎样获得更强证据','八 可直接复用的内容表述','九 常见追问及回答','十 资料检验与复用']:
    check('内容覆盖 '+heading,heading in body)
check('没有增加第二病例',not any(w in body for w in ['AtomNet','POLYGON','DrugnomeAI','DDR1']))
schedule_pattern=r'(?m)^\s*\|?\s*(?:[01]?\d|20):[0-5]\d\s*[–-]'
check('时间检查区分期刊卷页与安排',not re.search(schedule_pattern,'Nature Medicine. 2025;31:45–59') and bool(re.search(schedule_pattern,'| 0:00–1:00 | 开场 |')))
check('没有展示时间与成员分配',not re.search(schedule_pattern,body) and not re.search(r'成员[一二三四1234]|每人\d+分钟',body))
check('没有混用预印本数值','210.0 ± 42.4' not in body and 'n = 2' not in body)
check('未伪造实验执行或受众测试','本资料是文献研究与内容整理' in source_notes and '目前没有把真实受众测试写成已经通过' in body)
check('公开摘要与目录层级透明','仅公开摘要' in body and '未把章节正文计为已精读' in body)

feng_html=(BASE/'sources/Feng_2011_CCRK_fulltext.html').read_text(encoding='utf-8')
feng=(BASE/'sources/Feng_2011_CCRK_text.txt').read_text(encoding='utf-8')
check('前期靶点官方全文重新打开','10.1172/JCI45967' in feng_html and 'Oncogenic properties of CCRK in HCC.' in feng)
for needle in ['52 pairs of HCC cases','69.2% (36/52)','Constitutively active β-catenin and TCF rescued','3 independent experiments']:
    check('前期靶点原文匹配 '+needle,needle in feng)
check('靶点依据来源分界','E31、E32' in body and 'E33' in body and '不能把它写成肝癌唯一的病因' in body)

draft_path=BASE/'内容初稿_零基础版.md'
draft=draft_path.read_text(encoding='utf-8')
check('零基础内容初稿重新打开',len(draft)>1800,f'characters={len(draft)}')
check('初稿引用证据编号有效',set(re.findall(r'\bE\d{2}\b',draft)).issubset(ids))
check('初稿来源编号有效',set(re.findall(r'\bS\d{2}\b',draft)).issubset(source_ids))
check('初稿区分早期成果与疗效','不是30天完成了新药研发' in draft and '尚不是患者疗效证明' in draft)
check('初稿区分靶点和分子实验','不是这些AI候选分子的动物试验' in draft)
check('初稿没有时间与成员分配',not re.search(schedule_pattern,draft) and not re.search(r'成员[一二三四1234]|每人\d+分钟',draft))
check('初稿保留待检验状态','不声称已经通过理解测试' in draft)

failed=[c for c in checks if not c[1]]
lines=['资料核查记录','核查日期 2026-10-03','',f'CHECKS={len(checks)} PASS={len(checks)-len(failed)} FAIL={len(failed)}','']
for label,ok,detail in checks:
    lines.append(f'{"PASS" if ok else "FAIL"} | {label} | {detail}')
lines.extend(['','执行命令',f'"C:\\Users\\woola\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe" "{Path(__file__).resolve()}"','', '自动检查覆盖文件完整性、数字匹配、内容覆盖与输入哈希；不等同于独立同行评审或实际读者理解测试。'])
(BASE/'验证记录.txt').write_text('\n'.join(lines),encoding='utf-8')
print(lines[3])
for label,ok,detail in failed: print('FAIL:',label,detail)
print('REOPENED:',main)
print('REOPENED:',BASE/'证据清单.csv')
print('REOPENED:',notes)
print('REOPENED:',draft_path)
print('REOPENED:',BASE/'验证记录.txt')
sys.exit(1 if failed else 0)
