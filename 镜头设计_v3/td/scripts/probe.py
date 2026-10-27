def main():
    print(app.version, app.build, app.product)
    print([c.name for c in op('/project1').children][:80])
    print(op('/project1').children.__len__())
main()
