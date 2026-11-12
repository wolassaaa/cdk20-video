"""HKBU SCIE1007 coursework video: client for the model that watches whole clips and listens to whole recordings.

Used only as a second opinion in the footage pipeline (does the denoised voice sound damaged, does a matte edge
flicker). Pass or fail still comes from measured numbers.

  _env/keys.env      GEMINI_API_KEY=...        never printed, logged or written to a manifest
  _env/gemini.conf   GEMINI_BASE_URL           the relay's OpenAI-style address (ends in /v1)
                     GEMINI_MODELS_ALLOWED     the only model names that may be used
                     GEMINI_MODEL              the default
                     GEMINI_MODEL_FALLBACK     used when the default does not answer (optional, must be allowed too)

    from watch import ask, WatchError
    text = ask("Transcribe, then ...", ["take.mp3"])          # audio, video (mp4) or images, as data URLs

Found on 11-12: the relay's Gemini-style address refuses video and silently drops audio (the model then invents a
transcript), so only /chat/completions is used, and callers must make the model transcribe first and compare that
with the script before trusting anything else it says. The relay needs a User-Agent and sometimes answers 502 or
times out: retried. Media goes inline, so keep a file under about 15 MB (cut and shrink first).
"""
import base64
import json
import mimetypes
import time
import urllib.error
import urllib.request
from pathlib import Path

from llm import ENV, KEYS, KeysMissing, _read_env

CONF = ENV / "gemini.conf"
MAX_BYTES = 15 * 2 ** 20


FALLBACK = None
last_model = None       # the model that gave the last answer


class WatchError(RuntimeError):
    pass


def _load():
    conf = _read_env(CONF)
    key = _read_env(KEYS).get("GEMINI_API_KEY", "")
    if not key:
        raise KeysMissing(f"钥匙没填：{KEYS} 里的 GEMINI_API_KEY 还空着")
    if not conf.get("GEMINI_BASE_URL") or not conf.get("GEMINI_MODEL"):
        raise KeysMissing(f"钥匙没填：{CONF} 不完整")
    allowed = conf.get("GEMINI_MODELS_ALLOWED", "").replace(",", " ").split() or [conf["GEMINI_MODEL"]]
    global FALLBACK
    FALLBACK = conf.get("GEMINI_MODEL_FALLBACK") or None
    return key, conf["GEMINI_BASE_URL"].rstrip("/"), conf["GEMINI_MODEL"], allowed


def ready():
    try:
        _load()
        return True
    except KeysMissing:
        return False


def model_name():
    return _load()[2]


def ask(prompt, media=(), model=None, temperature=0.1, max_tokens=1500, timeout=120, tries=2):
    """One question about some media files; returns the reply text (watch.last_model says who answered).
    Each model gets `tries` attempts; when the default gives nothing, the fallback is asked. Raises WatchError."""
    global last_model
    key, base, default, allowed = _load()
    models = [model or default] + ([FALLBACK] if not model and FALLBACK and FALLBACK != default else [])
    for m in models:
        if m not in allowed:
            raise WatchError(f"不许用这个模型：{m}（只许 {'、'.join(allowed)}）")
    parts = []
    for p in map(Path, media):
        if p.stat().st_size > MAX_BYTES:
            raise WatchError(f"文件太大（{p.stat().st_size >> 20} MB），先切短或缩小：{p.name}")
        mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
        parts.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode("ascii")}})
    hide = lambda s: str(s).replace(key, "***")
    last = ""
    for model, i in [(m, i) for m in models for i in range(tries)]:
        body = {"model": model, "temperature": temperature, "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": parts + [{"type": "text", "text": prompt}]}]}
        req = urllib.request.Request(base + "/chat/completions", data=json.dumps(body).encode("utf-8"), method="POST",
                                     headers={"Content-Type": "application/json", "Authorization": "Bearer " + key, "User-Agent": "curl/8.9.0"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                text = json.loads(r.read().decode("utf-8"))["choices"][0]["message"]["content"]
            if text and text.strip():
                last_model = model
                return text.strip()
            last = "空回答"
        except urllib.error.HTTPError as e:
            last = f"接口报错 {e.code}：{hide(e.read().decode('utf-8', 'replace')[:200])}"
            if e.code in (400, 401, 403, 404):
                continue
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError, IndexError, TypeError) as e:
            last = f"{type(e).__name__}：{hide(e)[:200]}"
        time.sleep(3 * (i + 1))
    raise WatchError(last)
