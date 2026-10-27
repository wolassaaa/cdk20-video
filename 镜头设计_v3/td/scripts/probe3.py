def main():
    c = op('/project1/design/lava4')
    t = c.op('lava').par.pdat.eval().text
    print('skin line present:', '0.62, 0.60, 0.58' in t)
    i = c.create(infoDAT, 'inf'); i.par.op = c.op('lava'); i.cook(force=True); print(i.text[:800]); i.destroy()
main()
