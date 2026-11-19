"""HKBU SCIE1007 课程作业的科普视频：W1 大标题卡（h20 盒盖）上组员名字和学号的本地读取。

只在本机的 Blender 渲染进程里调用，读到的东西只在内存里用：
  - 不打印名字、学号本身，只打印 "A ok (2 words, 12 chars; id 8 digits)" 或 "B missing" 这样的行；
  - 不写盘、不写日志、不进 git；
  - 文件在 人员素材啊/<A–D>/ 下，各人文件名不同（有的叫 name，有的含"名字""学号"），这里用 glob 找，
    命令行里不出现这些文件名。
规则见 镜头设计_v3/深化/04_片头与大标题重做.md 第五节。
"""
import re
from pathlib import Path

ROOT = "D:/。hkbu/molecular science"
MEMBERS = "ABCD"
_KEYS = ("名字", "学号", "name")
_LATIN = re.compile(r"[A-Za-z]")
_OK = re.compile(r"^[A-Za-z][A-Za-z .'\-]{1,38}[A-Za-z.]$")
_CJK = re.compile(r"[\u3000-\u303f\u3400-\u9fff\uff00-\uffef]")
_ID = re.compile(r"(?<!\d)(\d{7,10})(?!\d)")


def _files(root, m):
    d = Path(root) / "人员素材啊" / m
    if not d.is_dir():
        return []
    out = [p for p in d.glob("*.txt") if any(k in p.stem.lower() for k in _KEYS)]
    return sorted(out, key=lambda p: (0 if "名字" in p.stem else 1, p.name))


def _read(p):
    raw = p.read_bytes()
    for enc in ("utf-8-sig", "gb18030", "utf-16"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return ""


def _parse(text):
    """返回 (名字, 学号)；找不到的那一项是 None。"""
    name = sid = None
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if ":" in s or "：" in s:
            s = re.split(r"[:：]", s, maxsplit=1)[1].strip()
        m = _ID.search(s)
        if m:
            if sid is None:
                sid = m.group(1)
            s = (s[:m.start()] + " " + s[m.end():]).strip()     # 名字和学号写在同一行时，去掉学号再看名字
        if name is None:
            t = _CJK.sub(" ", s)
            t = re.sub(r"[,，、/|()（）\[\]]", " ", t)
            t = re.sub(r"\s+", " ", t).strip()
            if not re.search(r"\d", t) and len(_LATIN.findall(t)) >= 3 and 3 <= len(t) <= 40 and _OK.match(t):
                name = t
    return name, sid


def load_members(root=ROOT, draft=False, verbose=True):
    """返回 {"A": {"name": str, "id": str 或 None}, ...}。缺人时：draft=False 直接退出；draft=True 用 Member X 占位。"""
    out, missing = {}, []
    for m in MEMBERS:
        name = sid = None
        for p in _files(root, m):
            n, i = _parse(_read(p))
            name = name or n
            sid = sid or i
            if name and sid:
                break
        if name:
            out[m] = {"name": name, "id": sid}
            if verbose:
                print(f"{m} ok ({len(name.split())} words, {len(name)} chars; id {'%d digits' % len(sid) if sid else 'missing'})", flush=True)
        else:
            missing.append(m)
            if verbose:
                print(f"{m} missing", flush=True)
    if missing:
        if not draft:
            raise SystemExit("names missing: " + ", ".join(missing))
        for m in missing:
            out[m] = {"name": f"Member {m}", "id": None}
            if verbose:
                print(f"{m} draft placeholder", flush=True)
    return out


def load_names(root=ROOT, draft=False):
    """04 文档第五节的接口：{"A": 名字, ...}。只在内存里用，不写盘，不打印内容。"""
    return {m: v["name"] for m, v in load_members(root, draft).items()}


def leak_scan(paths, root=ROOT):
    """守护用：在给定文本文件里不分大小写地找真名和学号，返回命中的文件路径（只报文件，不报内容）。"""
    secrets = []
    for v in load_members(root, draft=True, verbose=False).values():
        if not v["name"].startswith("Member "):
            secrets.append(v["name"].lower())
        if v["id"]:
            secrets.append(v["id"])
    hits = []
    for p in paths:
        try:
            t = Path(p).read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        if any(s in t for s in secrets):
            hits.append(str(p))
    return hits


def scan_staged(paths, root=ROOT):
    """pre-commit 用：查暂存区里这些文件的内容（git show :路径，只在内存里），返回命中的路径。"""
    import subprocess
    secrets = []
    for v in load_members(root, draft=True, verbose=False).values():
        if not v["name"].startswith("Member "):
            secrets.append(v["name"].lower())
        if v["id"]:
            secrets.append(v["id"])
    if not secrets:
        return []
    hits = []
    for p in paths:
        if not p or p.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp", ".ttf", ".otf", ".woff", ".woff2")):
            continue
        r = subprocess.run(["git", "show", ":" + p], cwd=root, capture_output=True)
        if r.returncode:
            continue
        t = r.stdout.decode("utf-8", errors="ignore").lower()
        if any(s in t for s in secrets):
            hits.append(p)
    return hits


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "scan-staged":
        names = sys.stdin.buffer.read().decode("utf-8", errors="ignore").split("\0")
        bad = scan_staged([n for n in names if n])
        for b in bad:
            print("pre-commit: blocked (member name or student ID inside):", b)
        sys.exit(1 if bad else 0)
    if len(sys.argv) > 1 and sys.argv[1] == "scan":
        bad = leak_scan(sys.argv[2:])
        for b in bad:
            print("name-leak:", b)
        sys.exit(1 if bad else 0)
    load_members(draft=True)
