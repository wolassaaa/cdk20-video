def main():
    t = op('/project1').create(baseCOMP, 'tmp_probe')
    for ty in [lineMAT, phongMAT, pbrMAT, torusSOP, circleSOP, lightCOMP, geometryCOMP, renderTOP, constantMAT]:
        o = t.create(ty)
        names = [p.name for p in o.pars() if not p.name.startswith(('ext', 'promote', 'relpath', 'parent'))]
        if ty is geometryCOMP: names = [n for n in names if n.startswith('instance')]
        print(ty.__name__ if hasattr(ty,'__name__') else ty, ':', ' '.join(names)[:1800])
    t.destroy()
main()
