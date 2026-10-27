from pathlib import Path
import importlib.util,sys,shutil
from pypdf import PdfReader
BASE=Path(__file__).resolve().parent.parent/'视频内容稿'/'教师要求补齐版'
SKILL=Path(r'C:\Users\woola\.codex\plugins\cache\openai-primary-runtime\documents\26.921.10847\skills\documents\render_docx.py')
for edition in ['简中','繁中']:
 stem='视频内容稿_英文加'+edition;pdf=BASE/(stem+'.pdf');docx=BASE/(stem+'.docx')
 assert len(PdfReader(pdf).pages)>0
 spec=importlib.util.spec_from_file_location('packaged_renderer_'+edition,SKILL);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 def convert(doc_path,user_profile,convert_tmp_dir,stem,verbose):
  assert Path(doc_path).resolve()==docx.resolve();out=Path(convert_tmp_dir)/(stem+'.pdf');shutil.copy2(pdf,out);return str(out),'Microsoft Word native export + packaged rasterizer'
 m.convert_to_pdf=convert
 out=Path(__file__).resolve().parent/'视频稿v2预览'/edition
 for stale in out.glob('page-*.png') if out.exists() else []:
  if int(stale.stem.split('-')[-1])>len(PdfReader(pdf).pages):
   assert stale.resolve().parent==out.resolve();stale.unlink()
 sys.argv=[str(SKILL),str(docx),'--output_dir',str(out),'--dpi','120'];m.main()
 print('RENDERED',edition,len(PdfReader(pdf).pages))
