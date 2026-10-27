from pathlib import Path
from pypdf import PdfReader
import hashlib, json, sys

here = Path(__file__).resolve().parent
m = json.loads((here/'manifest.json').read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
mode = sys.argv[1]
path = Path(sys.argv[2]) if len(sys.argv)>2 else Path(m['modified'] if mode=='modified' else m['source'])
reader = PdfReader(path)
texts = [p.extract_text() for p in reader.pages]
assert len(texts)==3
assert sha(m['source'])==m['original_sha256'], 'Original source changed'
if mode in ('baseline','rollback'):
    assert sha(path)==m['original_sha256']
    assert all('REFERENCE ANSWERS' not in t for t in texts)
    print(f'{mode.upper()}: PASS; pages=3; answers=blank; original_SHA256=matched')
else:
    assert sha(path)==m['modified_sha256']
    assert all('REFERENCE ANSWERS' in t for t in texts)
    t=' '.join(' '.join(texts).split())
    for required in [
        'To identify major computer-aided methods used in cancer drug discovery.',
        'To evaluate how these methods help assess potential cancer drug candidates.',
        '8,918', '30 days', 'CellTiter-Glo', '208.7', '1,706.7',
        'Target versus candidate molecule', 'Prediction versus validation',
        'Read "AI discovers a drug"', 'Total: 20 min', 'A: 5 min', 'B: 5 min', 'C: 5 min', 'D: 5 min'
    ]: assert required in t,required
    assert sha(path)!=m['original_sha256']
    for name in ['Tutorial2_答案与中文解释.md','DIFF_FILE.txt','ROLLBACK.sh']:
        assert (here/name).read_text(encoding='utf-8').strip()
    print('MODIFIED: PASS; pages=3; Q1-Q6=present; timing=20min; A/B/C/D=5min; original=unchanged')
