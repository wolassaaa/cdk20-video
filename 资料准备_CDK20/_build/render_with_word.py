"""Run packaged render_docx.py using a real Microsoft Word-exported PDF.

The packaged LibreOffice path is not installed on this host. Only its conversion
hook is replaced; its DOCX page sizing and PDF-to-PNG rasterizer remain unchanged.
The exported PDF must preexist and is validated before rendering.
"""
from pathlib import Path
import importlib.util, shutil, sys, os
from pypdf import PdfReader
BASE=Path(__file__).resolve().parent.parent
SKILL=Path(r'C:\Users\woola\.codex\plugins\cache\openai-primary-runtime\documents\26.921.10847\skills\documents\render_docx.py')
PDF=BASE/'AI辅助肝癌候选分子发现内容手册.pdf'
DOCX=BASE/'AI辅助肝癌候选分子发现内容手册.docx'
pages=len(PdfReader(PDF).pages)
assert pages>0
spec=importlib.util.spec_from_file_location('packaged_docx_renderer',SKILL)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def word_export(doc_path,user_profile,convert_tmp_dir,stem,verbose):
    assert Path(doc_path).resolve()==DOCX.resolve()
    p=Path(convert_tmp_dir)/(stem+'.pdf');shutil.copy2(PDF,p)
    return str(p),f'Microsoft Word native export prevalidated pages={pages}; LibreOffice hook replaced'
m.convert_to_pdf=word_export
out=BASE/'_build/完整手册预览'
for stale in out.glob('page-*.png') if out.exists() else []:
    n=int(stale.stem.split('-')[-1])
    if n>pages:
        assert stale.resolve().parent==out.resolve()
        stale.unlink()
sys.argv=[str(SKILL),str(DOCX),'--output_dir',str(out),'--dpi','130','--verbose']
m.main()
print('RENDER_BACKEND=Microsoft Word native PDF + packaged render_docx.py rasterizer')
