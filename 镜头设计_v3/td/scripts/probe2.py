def main():
    import numpy as np
    c = op('/project1/design/lava4')
    r = c.op('r_lava4_k2_branch'); r.cook(force=True)
    a = r.numpyArray()[..., :3]
    lum = a.sum(-1); m = lum > 1e-4
    print('covered', m.mean())
    for ch in range(3): print(ch, np.percentile(a[m][:, ch], [5, 25, 50, 75, 95]))
    g = a[m]; grey = (np.abs(g[:, 0] - g[:, 2]) < 0.05).mean(); print('greyish frac', grey)
main()
