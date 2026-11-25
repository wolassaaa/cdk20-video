p = 'D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/arena/code/scene.py'
s = open(p, encoding='utf8').read()
s = s.replace('ap.add_argument("--flat", action="store_true")', 'ap.add_argument("--anim", default="")                 # "first,last": motion test frames of T4, 15 fps\nap.add_argument("--flat", action="store_true")')
# keep the thin beams so they can move
s = s.replace('        spot((x, 44, 96), (tx, ty, 0), G, powr[i % 7], wid[i % 7], 0.15, 0.2)\n', '        BEAMS.append((spot((x, 44, 96), (tx, ty, 0), G, powr[i % 7], wid[i % 7], 0.15, 0.2), np.array([x, 44, 96.0]), np.array([tx, ty, 0.0])))\n')
s = s.replace('META = {"shot": A.shot}\n', 'META = {"shot": A.shot}\nBEAMS = []\n', 1)
s = s.replace('''t = time.time()
exr = os.path.join(WORK, tag + ".exr")
sc.render.filepath = exr
bpy.ops.render.render(write_still=True)
''', '''if A.anim:
    # slow by construction: each beam drifts along its own sine, once in about 12 s, the camera creeps 3 m. Fixed seed, fixed samples, no time limit, so frames match.
    first, last = (int(v) for v in A.anim.split(","))
    c_.use_adaptive_sampling, c_.time_limit = False, 0
    mdir = os.path.join(WORK, "motion")
    os.makedirs(mdir, exist_ok=True)
    start = Vector(cam.location)
    for f in range(first, last + 1):
        t0 = time.time()
        u = f / 15.0
        for i, (ob, pos, tgt) in enumerate(BEAMS):
            ph = 1.7 * i
            d = np.array([26 * math.sin(2 * math.pi * u / 12 + ph), 16 * math.cos(2 * math.pi * u / 15 + 0.6 * ph), 0])
            ob.rotation_euler = Vector(tgt + d - pos).to_track_quat("-Z", "Y").to_euler()
        cam.location = start + Vector((0.12, 0.5, 0.0)) * u
        exr = os.path.join(mdir, f"f{f:04d}.exr")
        sc.render.filepath = exr
        bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(exr)
        iw, ih = im.size
        a = np.empty(iw * ih * 4, np.float32)
        im.pixels.foreach_get(a)
        np.save(os.path.join(mdir, f"f{f:04d}.npy"), a.reshape(ih, iw, 4)[::-1, :, :3].astype(np.float16))
        bpy.data.images.remove(im)
        os.remove(exr)
        print(f"FRAME {f} {time.time() - t0:.1f}s", flush=True)
    print("DONE anim")
    sys.exit(0)

t = time.time()
exr = os.path.join(WORK, tag + ".exr")
sc.render.filepath = exr
bpy.ops.render.render(write_still=True)
''')
open(p, 'w', encoding='utf8').write(s)
print('ok')
