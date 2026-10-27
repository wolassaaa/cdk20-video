def main():
    c = op('/project1/design/f5_streams')
    c.op('ink').par.linecoloratt = 'Color'
    o = c.op('out')
    for _ in range(3): o.cook(force=True)
    o.save(r'C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/99ee4c52-bc4b-442d-ae78-602740c170d9/scratchpad/tdd/png/t5.png')
main()
