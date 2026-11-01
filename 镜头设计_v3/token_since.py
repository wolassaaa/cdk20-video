"""HKBU SCIE1007 coursework science video: adds up the tokens a Claude Code session spent, for the numbers in 工作记录.md.

Run: python token_since.py <session.jsonl> [since]    since is a local time such as 2026-11-02T01:20; leave it out for the whole session.
Reads the session's transcript and any subagent transcripts beside it. Each message counts once.
"""
import collections
import datetime
import glob
import json
import os
import sys

KEYS = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")


def read(path, since, seen):
    for line in open(path, encoding="utf8"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        m = d.get("message")
        u = m.get("usage") if isinstance(m, dict) else None
        if not u or not d.get("timestamp"):
            continue
        t = datetime.datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00")).astimezone().replace(tzinfo=None)
        if since is None or t >= since:
            seen[m.get("id") or d.get("uuid")] = u


def main():
    path = sys.argv[1]
    since = datetime.datetime.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else None
    seen = {}
    read(path, since, seen)
    subs = glob.glob(os.path.join(path[:-len(".jsonl")], "subagents", "*.jsonl"))
    for p in subs:
        read(p, since, seen)
    tot = collections.Counter()
    for u in seen.values():
        for k in KEYS:
            tot[k] += u.get(k) or 0
    print("messages", len(seen), "subagent files", len(subs))
    print("new tokens (input + output + cache write):", tot["input_tokens"] + tot["output_tokens"] + tot["cache_creation_input_tokens"])
    print("cache read:", tot["cache_read_input_tokens"])


if __name__ == "__main__":
    main()
