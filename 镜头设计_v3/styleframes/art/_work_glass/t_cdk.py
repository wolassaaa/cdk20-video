"""HKBU SCIE1007 coursework science video. Smoke test of glass_kit: real CDK20 surface as glass, standing in the old tube row on the black mirror."""
import sys, math
sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/_shared")
import glass_kit as gk
sc = gk.scene(samples=128)
gk.floor_mirror()
gk.cdk20(gk.glass_tinted((0.04, 0.12, 1.0), density=0.35), loc=(0, 0, 2.6), rot=(math.radians(100), 0, math.radians(20)), scale=0.75)
for i in range(6):
    gk.tube(-5.0 + i * 0.42, 1.2, fill=0)
    gk.tube(5.0 - i * 0.42, 1.2, fill=0)
gk.rig_cold(k=1.4)
gk.area("key", (3, -6, 6), (math.radians(50), 0, math.radians(25)), 4, 260, (1, 1, 1))
gk.camera((0, -13, 2.2), (0, 0, 2.3), lens=50)
gk.render(r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/_work_glass/t_cdk.png")
