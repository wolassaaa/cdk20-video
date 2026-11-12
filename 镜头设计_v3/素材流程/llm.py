"""HKBU SCIE1007 coursework video: tiny client for a text / vision model, used inside the footage pipeline.

For chores: checking a transcript against the script, looking at thumbnail strips.

Where things are read from (both stay on this machine, _env/ is not in git):
  _env/keys.env   GLM_API_KEY=...           the key; never printed, logged or written to a manifest
  _env/glm.conf   GLM_API_STYLE             anthropic (POST <base>/v1/messages) or openai (POST <base>/v1/chat/completions)
                  GLM_BASE_URL              the relay address
                  GLM_MODELS_ALLOWED        the only model names that may be used
                  GLM_MODEL_LIGHT / _HEAVY  everyday model / the one for pictures and judgement

    from llm import chat, ready, KeysMissing, LLMError
    text = chat("Is this the same sentence? ...")                       # text, light model
    text = chat("Who is in these frames?", images=["a.jpg", "b.jpg"])   # text + images (light model: see chat())
    text = chat("Pick the best take ...", heavy=True)                   # judgement, heavy model

    python llm.py "say hi"                        # quick test
    python llm.py "what is this" --image strip.jpg

Standard library only. With no key filled in, chat() raises KeysMissing ("钥匙没填") instead of crashing.
"""
import base64
import json
import mimetypes
import sys
import urllib.error
import urllib.request
from pathlib import Path

ENV = Path(__file__).resolve().parents[2] / "_env"
KEYS = ENV / "keys.env"
CONF = ENV / "glm.conf"


class KeysMissing(RuntimeError):
    """钥匙没填: the key (or the address / model settings) is not filled in."""


class LLMError(RuntimeError):
    pass


def _read_env(path):
    vals = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals


def _load():
    conf = _read_env(CONF)
    conf.update({k: v for k, v in _read_env(KEYS).items() if v})   # older layout kept everything in keys.env
    key = conf.get("GLM_API_KEY", "")
    if not key:
        raise KeysMissing(f"钥匙没填：{KEYS} 里的 GLM_API_KEY 还空着")
    need = [k for k in ("GLM_BASE_URL", "GLM_MODEL_LIGHT") if not conf.get(k) and not (k == "GLM_MODEL_LIGHT" and conf.get("GLM_MODEL"))]
    if need:
        raise KeysMissing(f"钥匙没填：{CONF} 里的 {'、'.join(need)} 还空着")
    light = conf.get("GLM_MODEL_LIGHT") or conf["GLM_MODEL"]
    heavy = conf.get("GLM_MODEL_HEAVY") or light
    allowed = conf.get("GLM_MODELS_ALLOWED", "").replace(",", " ").split() or [light, heavy]
    return {"key": key, "base": conf["GLM_BASE_URL"].rstrip("/"), "style": conf.get("GLM_API_STYLE", "anthropic").lower(),
            "light": light, "heavy": heavy, "allowed": allowed}


def ready():
    """True when the key and settings are filled in. Never raises, never shows the key."""
    try:
        _load()
        return True
    except KeysMissing:
        return False


def _b64(path):
    p = Path(path)
    return mimetypes.guess_type(p.name)[0] or "image/jpeg", base64.b64encode(p.read_bytes()).decode("ascii")


def chat(prompt, images=(), system=None, model=None, heavy=False, temperature=0.1, max_tokens=2000, timeout=180):
    """Send one message (text, optionally with images) and return the reply text.
    Model: `model` if given (must be on the allowed list), else the heavy one for heavy=True, else the light one."""
    k = _load()
    if model is None and images and not heavy:
        # 11-12: the relay answers 502 to every request with an image on the heavy model (both API styles);
        # the light model reads images fine, so images go to the light model unless heavy=True is asked for
        model = k["light"]
    model = model or (k["heavy"] if (images or heavy) else k["light"])
    if model not in k["allowed"]:
        raise LLMError(f"不许用这个模型：{model}（只许 {'、'.join(k['allowed'])}）")
    root = k["base"][:-3] if k["base"].endswith("/v1") else k["base"]
    if k["style"] == "anthropic":
        content = [{"type": "image", "source": {"type": "base64", "media_type": m, "data": d}} for m, d in map(_b64, images)]
        content.append({"type": "text", "text": prompt})
        body = {"model": model, "max_tokens": max_tokens, "temperature": temperature, "messages": [{"role": "user", "content": content}]}
        if system:
            body["system"] = system
        url = root + "/v1/messages"
        headers = {"x-api-key": k["key"], "Authorization": "Bearer " + k["key"], "anthropic-version": "2023-06-01"}
    elif k["style"] == "openai":
        content = prompt if not images else [{"type": "text", "text": prompt}] + [
            {"type": "image_url", "image_url": {"url": f"data:{m};base64,{d}"}} for m, d in map(_b64, images)]
        body = {"model": model, "max_tokens": max_tokens, "temperature": temperature,
                "messages": ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": content}]}
        url = root + "/v1/chat/completions"
        headers = {"Authorization": "Bearer " + k["key"]}
    else:
        raise LLMError(f"GLM_API_STYLE 只认 anthropic 或 openai，现在是 {k['style']}")
    headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST", headers=headers)
    hide = lambda s: str(s).replace(k["key"], "***")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise LLMError(f"模型接口报错 {e.code}：{hide(e.read().decode('utf-8', 'replace')[:300])}") from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        raise LLMError(f"连不上模型接口：{hide(e)}") from None
    try:
        if k["style"] == "anthropic":
            return "".join(b.get("text", "") for b in data["content"] if b.get("type") == "text")
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise LLMError("模型接口回的格式不对：" + hide(json.dumps(data, ensure_ascii=False)[:300])) from None


if __name__ == "__main__":
    for st in (sys.stdout, sys.stderr):
        if hasattr(st, "reconfigure"):
            st.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    imgs = []
    while "--image" in args:
        i = args.index("--image")
        imgs.append(args[i + 1])
        del args[i:i + 2]
    if not args:
        sys.exit('用法：python llm.py "一句话" [--image 图.jpg ...]')
    try:
        print(chat(" ".join(args), images=imgs))
    except (KeysMissing, LLMError) as e:
        sys.exit(str(e))
