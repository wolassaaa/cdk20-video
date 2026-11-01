"""HKBU SCIE1007 coursework science video. Smoke test of glass_kit: real liver and vessels as glass on the black mirror."""
import sys, math
sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/_shared")
import glass_kit as gk
sc = gk.scene(samples=128)
gk.floor_mirror(z=-1.15)
skin = gk.liver_skin(gk.glass(rough=0.03))
gk.stl("portal_vein_hepatic", gk.glass_tinted((0.9, 0.006, 0.05), 30))
gk.stl("hepatic_veins", gk.glass_tinted((0.02, 0.10, 1.0), 22))
gk.rig_cold(k=0.9)
gk.area("key", (2, -4, 3), (math.radians(55), 0, math.radians(20)), 3, 90, (1, 1, 1))
gk.camera((0.6, -5.2, 0.1), (0.2, 0, -0.05), lens=50)
gk.render(r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/_work_glass/t_liver.png")
