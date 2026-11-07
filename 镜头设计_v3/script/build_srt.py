"""HKBU SCIE1007 coursework science video: draft English subtitle file (SRT) from the narration script.

Each beat's line in script_v3.3.md is cut into cues of at most two lines of 42 characters, and the beat's time span
is shared out by character count. These are the script's conservative time codes, not the recording: re-time every
cue against the real voice (planned 11-20 to 11-24). The SRT stays a separate file and is never burned in.

Run: python build_srt.py [script.md] [out.srt]
"""
import re
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "script_v3.3.md"
OUT = sys.argv[2] if len(sys.argv) > 2 else "subtitles_v3.3_draft.srt"
LINE, MAXC, MIN_DUR = 42, 80, 1.0

HEAD = re.compile(r"^\*\*(\d-\d{2}) · (\d{2}):(\d{2})–(\d{2}):(\d{2}) · ([A-D]) · (ON-CAM|VO)\*\*")


def beats(text):
    """(beat id, start s, end s, speaker, line) for every beat between S1 and Part 4."""
    body = text.split("### S1", 1)[1].split("## Part 4", 1)[0]
    out, cur = [], None
    for ln in body.splitlines():
        m = HEAD.match(ln)
        if m:
            b, m1, s1, m2, s2, who, _ = m.groups()
            cur = (b, int(m1) * 60 + int(s1), int(m2) * 60 + int(s2), who)
        elif ln.startswith("> ") and cur:
            out.append((*cur, ln[2:].strip()))
            cur = None
    return out


def fits(s):
    """True when s goes on at most two lines of LINE characters, broken at a space."""
    return len(s) <= LINE or any(s[k] == " " and k <= LINE and len(s) - k - 1 <= LINE for k in range(len(s)))


def split_long(s):
    """Cut a sentence that will not fit two lines at a comma or a word near the middle, until every piece fits."""
    if len(s) <= MAXC and fits(s):
        return [s]
    mid = len(s) // 2
    cuts = [m.end() for m in re.finditer(r"[,;:] ", s)] or [m.start() + 1 for m in re.finditer(r" ", s)]
    at = min(cuts, key=lambda c: abs(c - mid))
    return split_long(s[:at].strip()) + split_long(s[at:].strip())


def cues(line):
    """Sentences, then packed: two short neighbours share a cue if they fit."""
    sents = [p for s in re.split(r"(?<=[.?!…])\s+(?=[A-Z'‘\"“0-9])", line) for p in split_long(s.strip()) if p]
    out = []
    for s in sents:
        if out and len(out[-1]) + 1 + len(s) <= MAXC and len(out[-1]) < 30 and fits(out[-1] + " " + s):
            out[-1] += " " + s
        else:
            out.append(s)
    return out


def two_lines(s):
    """Break where both lines fit; prefer just after . ? ! then , ; : then the most even split."""
    if len(s) <= LINE:
        return s
    spaces = [i for i, c in enumerate(s) if c == " "]
    fit = [k for k in spaces if k <= LINE and len(s) - k - 1 <= LINE]
    def rank(k):
        p = s[k - 1]
        return (0 if p in ".?!…" else 1 if p in ",;:" else 2, abs(k - (len(s) - k - 1)))
    i = min(fit, key=rank) if fit else min(spaces, key=lambda k: max(k, len(s) - k - 1))
    return s[:i] + "\n" + s[i + 1:]


def stamp(t):
    ms = round(t * 1000)
    return "%02d:%02d:%02d,%03d" % (ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000)


def main():
    with open(SRC, encoding="utf-8") as f:
        bs = beats(f.read())
    blocks, n, longest = [], 0, 0
    for b, t0, t1, who, line in bs:
        cs = cues(line)
        span = t1 - t0
        weights = [max(len(c), 1) for c in cs]
        tot = sum(weights)
        t = t0
        for c, w in zip(cs, weights):
            d = max(MIN_DUR, span * w / tot)
            end = min(t + d, t1)
            n += 1
            txt = two_lines(c)
            longest = max(longest, max(len(x) for x in txt.split("\n")))
            blocks.append("%d\n%s --> %s\n%s\n" % (n, stamp(t), stamp(end - 0.04), txt))
            t = end
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(blocks))
    print("SRT_OK beats=%d cues=%d longest_line=%d -> %s" % (len(bs), n, longest, OUT))


if __name__ == "__main__":
    main()
