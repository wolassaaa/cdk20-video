# HKBU SCIE1007 课程作业的科普视频：字幕烧录第一步——把 subs_en.json（时间和英文）、subs_zh_hans/hant.json（中文）画成一条
# 透明小牌条（1920×220，放在画面 y = 860 起），并写出逐帧的 concat 清单，交给 ffmpeg 叠到无字幕整片上（见 run_burn.sh）。
# 样式照 深化/19 第 3.1：Instrument Serif 46 px、骨白小牌 rgba(244,241,234,.94)、圆角 16、一行一块、小牌底边离画面下沿 62 px（y = 944–1018）。
# 双语版：中文在上（Noto Serif SC 40 px）、英文在下，同一块小牌；为了让出 886–928 的出处行，整块上沿 930、下沿 1052。
# 彩蛋（EGG 段）自带英文小牌（y 约 948–1030，深色）；中文版在它上面补一块深色中文小牌（y 876–940），英文版和无字幕版不动。
# 用法：py -3.11 -X utf8 burn_subs.py --lang en|hans|hant --out G:/cdk20/work/v10/deliver/_work/strip_<lang>
import argparse, json, hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
V3 = HERE.parent
FPS, W, H = 60, 1920, 1080
STRIP_Y, STRIP_H = 860, 220
SS = 2                                                     # 超采样
EN_FONT = V3 / "remotion_public/fusion_s1/fonts/InstrumentSerif-Regular.ttf"
ZH_FONT = Path("C:/Windows/Fonts/NotoSerifSC-VF.ttf")
TOTAL_F = 70876
EGG_START = 63738


def font(path, px, zh=False):
    f = ImageFont.truetype(str(path), px * SS)
    if zh:
        f.set_variation_by_name("Regular")
    return f


def pretty(s):
    return s.replace("...", "\u2026")


def tw(f, s):
    return f.getlength(s) / SS


def rr_mask(w, h, r, size):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], r * SS, fill=255)
    return m


def render(kind, en=None, zh=None, who=None):
    """kind: 'en' (EN plate 944–1018), 'bi' (zh above en, 930–1052), 'egg_zh' (dark zh plate 876–940). Returns RGBA at 1x, size (W, STRIP_H)."""
    fe, fz = font(EN_FONT, 46), font(ZH_FONT, 40, zh=True)
    if kind == "egg_zh":
        fz = font(ZH_FONT, 44, zh=True)
    if kind == "en":
        txt = pretty(en)
        w, h, top = int(round(tw(fe, txt))) + 60, 74, 944
    elif kind == "bi":
        wen, wzh = tw(fe, pretty(en)), tw(fz, zh)
        w, h, top = int(round(max(wen, wzh))) + 60, 122, 930
    else:
        label = (who + "：") if who else ""
        wlab = tw(fz, label)
        w, h, top = int(round(wlab + tw(fz, zh))) + 52, 64, 876
    x0 = (W - w) // 2
    y0 = top - STRIP_Y
    canvas = Image.new("RGBA", (W * SS, STRIP_H * SS), (0, 0, 0, 0))
    mask = Image.new("L", canvas.size, 0)
    box = (x0 * SS, y0 * SS)
    radius = 14 if kind == "egg_zh" else 16
    m_plate = rr_mask(w, h, radius, (w * SS, h * SS))
    if not dark_kind(kind):
        # 阴影：0 6px 18px rgba(60,50,40,.22) 和 0 1px 2px rgba(60,50,40,.25)
        sh = Image.new("L", canvas.size, 0)
        sh.paste(m_plate, (box[0], box[1] + 6 * SS))
        sh = sh.filter(ImageFilter.GaussianBlur(9 * SS))
        sh2 = Image.new("L", canvas.size, 0)
        sh2.paste(m_plate, (box[0], box[1] + 1 * SS))
        sh2 = sh2.filter(ImageFilter.GaussianBlur(1 * SS))
        for s_, a in ((sh, 0.22), (sh2, 0.25)):
            layer = Image.new("RGBA", canvas.size, (60, 50, 40, 0))
            layer.putalpha(s_.point(lambda v, a=a: int(v * a)))
            canvas = Image.alpha_composite(canvas, layer)
        # 小牌本体 + 顶部 2px 白色内高光
        plate = Image.new("RGBA", (w * SS, h * SS), (255, 255, 255, 240))
        body = Image.new("RGBA", (w * SS, h * SS), (244, 241, 234, 240))
        plate.paste(body, (0, 2 * SS))
        plate.putalpha(m_plate.point(lambda v: int(v * 0.94 + 0.5)))
        # 高光层不透明度高于本体：先铺白再铺本体，整体 alpha 用 .94
        canvas.alpha_composite(plate, box)
        ink = (31, 30, 28, 255)
    else:
        plate = Image.new("RGBA", (w * SS, h * SS), (18, 16, 30, 232))
        d = ImageDraw.Draw(plate)
        d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], radius * SS, outline=(255, 255, 255, 46), width=SS)
        plate.putalpha(Image.composite(plate.getchannel("A"), Image.new("L", plate.size, 0), m_plate))
        canvas.alpha_composite(plate, box)
        ink = (244, 241, 234, 255)
    d = ImageDraw.Draw(canvas)

    def line(text, f, line_h, ty, color, cx=None, x_left=None):
        asc, desc = f.getmetrics()
        base = (ty + (line_h * SS - (asc + desc)) / 2 + asc)
        if x_left is not None:
            d.text((x_left, base), text, font=f, fill=color, anchor="ls")
        else:
            d.text(((cx if cx is not None else W * SS / 2), base), text, font=f, fill=color, anchor="ms")

    if kind == "en":
        line(pretty(en), fe, 58, (y0 + 7) * SS, ink)
    elif kind == "bi":
        line(zh, fz, 46, (y0 + 7) * SS, ink)
        line(pretty(en), fe, 58, (y0 + 7 + 46 + 2) * SS, ink)
    else:
        total = (tw(fz, who + "：" if who else "") + tw(fz, zh))
        xl = (W - total) / 2 * SS
        if who:
            line(who + "：", fz, 46, (y0 + 9) * SS, (236, 174, 122, 255), x_left=xl)
            xl += fz.getlength(who + "：")
        line(zh, fz, 46, (y0 + 9) * SS, ink, x_left=xl)
    out = canvas.resize((W, STRIP_H), Image.LANCZOS)
    return out


def dark_kind(kind):
    return kind == "egg_zh"


def scaled(img, a):
    if a >= 1:
        return img
    r, g, b, al = img.split()
    return Image.merge("RGBA", (r, g, b, al.point(lambda v: int(v * a + 0.5))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=["en", "hans", "hant"], required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--frames", type=int, default=TOTAL_F)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    en = json.loads((HERE / "subs_en.json").read_text("utf8"))["subs"]
    zh = {}
    if a.lang != "en":
        zh = {s["id"]: s["text_zh"] for s in json.loads((HERE / f"subs_zh_{a.lang}.json").read_text("utf8"))["subs"]}
        assert set(zh) == {s["id"] for s in en}, "中文和英文的块 id 对不上"
    plan = [None] * a.frames                                    # 每帧一张图的文件名（None = 空条）
    cache = {}

    def get(key, mk):
        if key not in cache:
            fn = out / (hashlib.md5(key.encode("utf8")).hexdigest()[:16] + ".png")
            if not fn.exists():
                mk().save(fn, compress_level=1)
            cache[key] = fn
        return cache[key]

    blank = out / "blank.png"
    Image.new("RGBA", (W, STRIP_H), (0, 0, 0, 0)).save(blank)
    kind = "en" if a.lang == "en" else "bi"
    base_cache = {}
    for s in en:
        key0 = f"{kind}|{s['text']}|{zh.get(s['id'], '')}"
        if key0 not in base_cache:
            base_cache[key0] = render(kind, en=s["text"], zh=zh.get(s["id"]))
        img = base_cache[key0]
        f0, f1 = s["f0"], s["f1"]
        for f in range(f0, f1 + 1):
            if not (0 <= f < a.frames):
                continue
            al = 1.0
            if s["fade_in_f"] and f - f0 < s["fade_in_f"]:
                al = min(al, (f - f0 + 1) / s["fade_in_f"])
            if s["fade_out_f"] and f1 - f < s["fade_out_f"]:
                al = min(al, (f1 - f + 1) / s["fade_out_f"])
            assert plan[f] is None, f"帧 {f} 被两块占用"
            plan[f] = get(f"{key0}|{al:.3f}", lambda img=img, al=al: scaled(img, al))
    n_en = sum(p is not None for p in plan)
    n_egg = 0
    if a.lang != "en":                                           # 彩蛋中文小牌
        for tag in json.loads((HERE / f"subs_tag_zh_{a.lang}.json").read_text("utf8"))["lines"]:
            for c in tag["cues"]:
                img_key = f"egg|{tag['who']}|{c['text_zh']}"
                img = None
                for f in range(c["f0"], c["f1"]):
                    g = EGG_START + f
                    if g >= a.frames:
                        continue
                    assert plan[g] is None
                    if img is None:
                        img = get(img_key, lambda t=tag, c=c: render("egg_zh", zh=c["text_zh"]))
                    plan[g] = img
                    n_egg += 1
    # 写 concat 清单：每帧一条，时长按累计微秒取整，避免 1/60 取整漂移
    lst = out / "list.txt"
    with open(lst, "w", encoding="utf8") as fh:
        fh.write("ffconcat version 1.0\n")
        prev = 0
        for i, p in enumerate(plan):
            nxt = round((i + 1) * 1_000_000 / FPS)
            fh.write(f"file '{(p or blank).as_posix()}'\nduration {(nxt - prev) / 1e6:.6f}\n")
            prev = nxt
        fh.write(f"file '{(plan[-1] or blank).as_posix()}'\n")
    print(f"{a.lang}: 正片字幕帧 {n_en}，彩蛋中文帧 {n_egg}，图 {len(cache)} 张 -> {lst}")


if __name__ == "__main__":
    main()
