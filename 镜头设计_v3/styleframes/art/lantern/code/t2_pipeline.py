"""HKBU SCIE1007 coursework science video. Lantern: what a member's phone clip goes through before it joins T2, run on a real frame of our own test clip. No clip of a speaker exists yet, so the subject is a hand, not a face. No frame here is retouched by hand."""
from lk import *
import pg

a, k = pg.hand_alpha()
a = a[430:960]
k = k[430:960]
h_, w_ = a.shape[:2]
Y, X = np.mgrid[0:h_, 0:w_].astype(np.float32)
LAMP = (330.0, 200.0)
step2 = pg.phone_grade(a, LAMP, 520.0, d0=420.0, black=0.05, white=0.95, gamma=1.0, X=X, Y=Y)
step3 = pg.phone_grade(a * k[..., None], LAMP, 520.0, d0=420.0, black=0.05, white=0.95, gamma=0.85, X=X, Y=Y)
PANEL = 600
c = blank()
labels = [("1  phone frame, room lights on", a), ("2  crush + amber ramp + hard arc", step2), ("3  same, with a skin key", step3)]
for i, (lab, im) in enumerate(labels):
    p = Image.fromarray((np.clip(im, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((PANEL, int(h_ * PANEL / w_)), Image.LANCZOS)
    x = 30 + i * (PANEL + 30)
    arr = np.asarray(p, np.float32) / 255
    c[150:150 + arr.shape[0], x:x + PANEL] = arr
    c = lay(c, tx(lab, 36, 600, x, 120), AMBER_HI)
c = lay(c, tx("Shot in a dark room, step 3 is not needed: the room is already black.", 36, 500, 30, 860), CHALK)
c = lay(c, tx("Real pixels from our own test clip. No face clip exists yet.", 36, 500, 30, 916), CHALK)
save(c, "T2_pipeline.png")
