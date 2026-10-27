def main():
    import numpy as np
    c = op('/project1/design/lava4')
    c.op('lava').par.value1x = 999
    for nm in ('r_lava4_k2_branch', 'out_lava4_k2_branch'):
        r = c.op(nm); r.cook(force=True)
        a = r.numpyArray()[..., :3]; m = a.sum(-1) > 1e-4
        print(nm, 'covered', round(float(m.mean()), 3), [np.round(np.percentile(a[m][:, ch], [5, 50, 95]), 3).tolist() for ch in range(3)])
    print(c.op('out_lava4_k2_branch').inputs[0].name, c.op('out_lava4_k2_branch').inputs[0].inputs[0].name)
main()
