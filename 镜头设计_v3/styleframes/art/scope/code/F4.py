"""HKBU SCIE1007 coursework science video. Scope direction, frame F4 (script 4-03): the AI-predicted CDK20, with the stretch the model is unsure of.
Real data only: AlphaFold DB v6 ribbon and surface, residues split at the model's own confidence of 70. Tail is residues 303 to 346.
Blue is the channel for residues at 70 or above, red for residues below it. The split is the data, not a choice of look.
Scale bar: the render is orthographic at PPA px per Angstrom, 1 nm = 10 Angstrom, so the bar is 10 x PPA px long."""
from scopelib import *


def cdk_layers(dx=0, dy=0):
    """Blue and red channels of the real model, as (rgb, alpha) on black. dx, dy slide the render inside the frame."""
    D = np.load(WORK / "cdk.npz")
    ra = D["ra"].astype(np.float32)
    n = smooth_norm(D["rn"].astype(np.float32), ra)
    z = D["rz"].astype(np.float32) / np.maximum(ra, 1e-3)
    p = D["rp"].astype(np.float32) / np.maximum(ra, 1e-3)
    shell, sa = D["shell"].astype(np.float32), D["sa"].astype(np.float32)
    z = np.where(ra > .02, z, 0)
    # shading: light from upper left, far parts dimmer as if leaving the focal plane, a dark seam where a nearer strand crosses a farther one
    L = np.array([-.42, .55, .72], np.float32)
    L /= np.linalg.norm(L)
    lit = np.clip(n @ L, 0, 1)
    rim = 1 - np.clip(n[..., 2], 0, 1)
    zm = z[ra > .5]
    z0, z1 = np.percentile(zm, 2), np.percentile(zm, 98)
    zn = np.clip((z - z0) / (z1 - z0), 0, 1)
    zfill = gblur(zn * ra, 5) / np.maximum(gblur(ra, 5), 1e-3)
    seam = np.clip((zn - zfill) * 9, 0, 1)
    level = (.34 + 1.05 * lit ** 1.6) * (1 - .52 * zn ** 1.3) * (1 - .9 * seam) + .16 * rim ** 2 * (1 - zn)
    low = (p < 70).astype(np.float32)
    s = np.clip(shell / 2.0, 0, 1) ** .72
    rgb = blank()
    rgb = over(rgb, KLEIN, np.clip(s * 1.25, 0, 1) * sa)
    rgb = over(rgb, BLUE, np.clip(s * 1.9 - 1.0, 0, 1) * .75)
    body, tail = (1 - low) * ra, low * ra
    lv = np.clip(level, 0, 1)[..., None]
    ramp = lambda lo, hi: np.where(lv < .42, lo * lv / .42, lo + (hi - lo) * np.clip((lv - .42) / .42, 0, 1))
    col = ramp(KLEIN, BLUE)
    col = col + (BONE - col) * np.clip((lv - .86) / .14, 0, 1) * .55
    rgb = rgb * (1 - np.clip(gblur(body, 3) * .9, 0, 1)[..., None] * .75)
    rgb = over(rgb, col, body)
    bloom = gblur(rgb, 14) * .55 + gblur(rgb, 4) * .25
    rgb = np.clip(rgb + bloom * (1 - rgb), 0, 1)
    # the red channel replaces whatever is behind it, so no purple
    halo = np.clip(gblur(tail, 7) * 1.5, 0, 1)
    rgb = rgb * (1 - halo[..., None] * .95)
    rgb = over(rgb, DARKRED, np.clip(gblur(tail, 4) * 1.2, 0, 1) * .45)
    lv = np.clip(lv * 1.5, 0, 1)
    colr = ramp(DARKRED, RED)
    rgb = over(rgb, colr, tail)
    only_b = over(blank(), KLEIN, np.clip(s * 1.25, 0, 1) * sa)
    only_b = over(only_b, col, body)
    only_r = over(blank(), colr, tail)
    roll = lambda a: np.roll(np.roll(a, dx, 1), dy, 0)
    return roll(rgb), roll(only_b), roll(only_r), float(D["ppa"])


if __name__ == "__main__":
    cx, cy, R = 560, 540, 486
    rgb, ob, orr, PPA = cdk_layers(int(cx - W / 2))
    field = disc(cx, cy, R)
    rgb = rgb * illum(cx, cy, R)[..., None]
    rgb = rgb + over(blank(), KLEIN, field * (1 - np.clip(rgb.sum(-1) * 4, 0, 1)) * .05)
    rgb = ring(rgb, cx, cy, R, "dotted")
    clean(rgb, "F4")
    # measuring scale at the foot of the field: one division = 1 nm = 10 Angstrom = 10 x PPA px
    rgb = ruler(rgb, cx - 2.5 * 10 * PPA, 902, 10 * PPA, 5, "5 nm")

    # tail callout
    rgb = line(rgb, [(1120, 330), (1040, 330), (930, 500)], RED, 3)
    rgb = text(rgb, "floppy tail", (1136, 346), (sans, 76, 600), RED, halo=False)
    rgb = text(rgb, "low confidence", (1138, 412), 44, BONE, halo=False)
    rgb = tag(rgb, 1136, 160, "dotted", "AlphaFold DB v6 · predicted", size=30)

    # legend: the two channels of the same image, split the way a two-channel figure is laid out
    def thumb(a, xc, yc, r):
        global rgb
        x0 = int(cx - R * .92)
        crop = (x0, int(cy - R * .92), int(cx + R * .92), int(cy + R * .92))
        t = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).crop(crop).resize((2 * r, 2 * r), Image.LANCZOS)
        im = np.zeros((H, W, 3), np.uint8)
        im[yc - r:yc + r, xc - r:xc + r] = np.asarray(t)
        rgb = rgb * (1 - disc(xc, yc, r)[..., None]) + im.astype(np.float32) / 255 * disc(xc, yc, r)[..., None]
        rgb = ring(rgb, xc, yc, r, "dotted", w=2.4)

    ob2, orr2 = np.roll(ob, 0, 1), np.roll(orr, 0, 1)
    thumb(ob2, 1300, 700, 158)
    thumb(orr2, 1660, 700, 158)
    rgb = text(rgb, "more confident", (1300, 920), 38, BONE, anchor="ms", halo=False)
    rgb = text(rgb, "less confident", (1660, 920), 38, BONE, anchor="ms", halo=False)
    rgb = minimap(rgb, 1590, 1022, 1)
    purple_check(rgb)
    save(rgb, "F4.png")
