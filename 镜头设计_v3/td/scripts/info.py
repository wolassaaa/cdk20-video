def main():
    m = op('/project1/design/lava2/liver_mat')
    i = m.parent().create(infoDAT, 'liver_info'); i.par.op = m; i.cook(force=True)
    print(i.text[:2500]); i.destroy()
main()
