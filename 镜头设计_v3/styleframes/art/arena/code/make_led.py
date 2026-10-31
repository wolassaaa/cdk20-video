"""HKBU SCIE1007 coursework science video. Arena direction: what plays on the LED wall in T2 and T5, in frame pixels.

python make_led.py writes _work/T2led.npy, T5led.npy (linear) for grade.py, and _work/T2wall.png, T5wall.png, small greyscale copies that light the haze and floor in Blender.
"""
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.normpath(os.path.join(HERE, "..", "_work"))
RECT = {"T2": (166, 190, 1754, 818), "T5": (123, 201, 1797, 858)}


def text(name):
    a = np.asarray(Image.open(os.path.join(W, "text", name + ".png")).convert("RGBA"), np.float32) / 255
    return a[..., :3] ** 2.2, a[..., 3:]


def write(shot, pic):
    x0, y0, x1, y1 = RECT[shot]
    np.save(os.path.join(W, shot + "led.npy"), pic.astype(np.float32))
    crop = pic[y0:y1, x0:x1]
    lum = np.clip(crop.mean(2), 0, 1) ** (1 / 2.2)
    Image.fromarray((lum * 255).astype(np.uint8)).resize((512, 203), Image.BILINEAR).convert("RGB").save(os.path.join(W, shot + "wall.png"))


def t2():
    """Half the wall is the phone shot, warm and left as the phone saw it. The other half is the question."""
    x0, y0, x1, y1 = RECT["T2"]
    pic = np.zeros((1080, 1920, 3), np.float32)
    pic[y0:y1, x0:x1] = np.array([.018, .012, .009])
    p = np.load(os.path.join(W, "person.npy"))
    ph = y1 - y0
    pw = 770
    # crop the square shot to the half wall, face on the upper third
    crop_h = 640
    crop_w = int(crop_h * pw / ph)
    cx, top = 500, 165
    sub = p[top:top + crop_h, cx - crop_w // 2: cx - crop_w // 2 + crop_w]
    chans = [np.asarray(Image.fromarray(sub[..., i]).resize((pw, ph), Image.BICUBIC)) for i in range(3)]
    sub = np.stack(chans, -1)
    sub = sub * np.array([1.25, 0.86, 0.56]) * 0.95    # the warm grade: the one thing in the frame that is not cold
    pic[y0:y1, x0:x0 + pw] = sub
    c, a = text("T2wall")
    pic = pic * (1 - a) + np.array([1.0, .86, .68])[None, None] * c.mean(2, keepdims=True) * 1.3 * a
    write("T2", pic)


def t5():
    """The scoreboard: the measured number, nothing behind it."""
    x0, y0, x1, y1 = RECT["T5"]
    pic = np.zeros((1080, 1920, 3), np.float32)
    pic[y0:y1, x0:x1] = np.array([.003, .018, .016])
    c, a = text("T5wall")
    pic = pic * (1 - a) + np.array([.80, 1.0, .95])[None, None] * c.mean(2, keepdims=True) * 1.5 * a
    write("T5", pic)


t2()
t5()
print("ok")
