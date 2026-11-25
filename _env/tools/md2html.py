"""把 md 转成可直接双击打开的本地网页（UTF-8，表格、链接可点）。用法：md2html.py 文件或文件夹..."""
import sys, pathlib, re, markdown
CSS = """body{font-family:"Microsoft YaHei",sans-serif;max-width:900px;margin:24px auto;padding:0 16px;line-height:1.7;color:#222;background:#fff}
table{border-collapse:collapse;margin:12px 0}td,th{border:1px solid #ccc;padding:6px 10px}th{background:#f2f2f2}
code{background:#f3f3f3;padding:1px 4px;border-radius:3px}h1,h2{border-bottom:1px solid #ddd;padding-bottom:4px}a{color:#0a58ca}"""
def conv(p):
    t = p.read_text(encoding="utf-8")
    t = re.sub(r"\]\(([^)]+?)\.md\)", r"](\1.html)", t)
    body = markdown.markdown(t, extensions=["tables", "fenced_code", "sane_lists"])
    out = p.with_suffix(".html")
    out.write_text(f'<!doctype html><meta charset="utf-8"><title>{p.stem}</title><style>{CSS}</style>{body}', encoding="utf-8")
    print(out)
for a in sys.argv[1:]:
    a = pathlib.Path(a)
    for p in ([a] if a.is_file() else a.rglob("*.md")): conv(p)
