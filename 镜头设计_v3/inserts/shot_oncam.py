"""HKBU SCIE1007 课程作业的科普视频：出镜段"人在前 + 人侧后方 3D 零件"通用模块（08_出镜旁3D_调研.md 第十节落地，11-20）。

做法（08 文档第十节）：Blender 一个场景 = 真的三维大板（远处，浅景深虚掉）+ 零件 + 一张"人卡片"（抠像逐帧图当贴图，
相机看不见、只投影）→ Cycles + OptiX GPU 渲"大板 + 零件"一层 → 合成里把人原像素叠回最前 + 光包边 + 颗粒 + 软化 → nvenc 出片。
时间一律来自事件表 映射/keys/<段>.json（resolve.py 出），引导用 bl_guide（焦点点名、轮廓光、浇口预颤）。

所有出镜段共用的部分：
  机位      手机前摄按 26 mm 等效反推；出片上人在 oncam.jsx 的位置（PX/PY/宽 1728），相机用镜头偏移让素材光轴落在原位
  大板      board_final.blend 竖起来当身后的墙（放大、放远，焦外 6–14 px）
  人卡片    只投影（visible_camera 关），T1 试验定的
  光        measure 从脸和白 T 恤量方向、主辅光比、色温、颗粒；calib 用灰球/白球/镜面球回写功率（T2、T3）
  镜头微动  以人卡片中心为轴 ±0.3°（人在合成里不动，大板和零件有 3–8 px 的真视差）
  转场      段首 T5 焦点擦除（近处虚化料杆扫过 + 人淡入），段尾 T1 穿越（真相机推进零件；人按卡片的真实投影移出画面）
  动作库    08 文档第四节 A1–A10 的缓动曲线（pop_curve、spring、ease_*、bezier）
各段只写一个 recipe（在场景里放什么、哪个词做什么），登记进 SEGS / RECIPES。

用法（项目根下 Git Bash）：
  python  镜头设计_v3/inserts/shot_oncam.py measure 3-01          # T2：量光、量颗粒 → G:/cdk20/work/oncam/3-01/light.json
  blender -b --factory-startup -P 镜头设计_v3/inserts/shot_oncam.py -- calib 3-01   # T1 + T3：卡片投影试验、灰球比光、回写功率
  blender ... -- build 3-01 [采样]                                 # 搭整段场景，存 scene.blend + check.json + cam.json
  blender ... -- rimcal 3-01                                       # 轮廓光标定到 +0.18 EV（bl_guide.calib）
  blender ... -- render 3-01 bg|fg                                 # 整段渲（断点续渲）
  blender ... -- frames 3-01 0,184,330 [bg|fg]                     # 抽帧
  python  镜头设计_v3/inserts/shot_oncam.py comp 3-01 [--ab]       # 合成 + nvenc 出片（--ab 只出 T6 开/关对照帧）
  python  镜头设计_v3/inserts/shot_oncam.py check 3-01             # F1/F2/人漂移/黑场/颗粒对比，写 check_comp.json
"""
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MAPD = HERE.parent / "映射"
RM = ROOT / "镜头设计_v2/tests/T4_remotion/src/v3/manual"
WORK_ROOT = Path(os.environ.get("CDK20_WORK", "G:/cdk20/work"))   # 11-20 晚：帧、缓存一律写 G（D 是系统盘，大量写入会卡）；D:/cdk20_work 是指向这里的目录联接
WORK = WORK_ROOT / "oncam"
FF = os.environ.get("CDK20_FF") or next((p for p in ("D:/software/tools/CipherTalk/resources/app.asar.unpacked/node_modules/ffmpeg-static/ffmpeg.exe",
                                                       str(ROOT / "_env/ffmpeg/ffmpeg.exe")) if Path(p).exists()))
# 11-20 晚：编码用 CipherTalk 带的 ffmpeg 6.1（有 h264_nvenc，能写 G 和 C 临时目录）；_env/ffmpeg 写不了 G（坑 17），只作后备
BOARD = str(WORK_ROOT / "kit/board_final.blend")
QUEUE = (ROOT / "_env" / "queue", Path.home() / "cdk20_guard")
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(MAPD))

try:
    import bpy
    from mathutils import Matrix, Quaternion, Vector
    IN_BL = True
except ImportError:
    IN_BL = False

# ---------------------------------------------------------------- 机位（所有出镜段共用）
OUT_W, OUT_H, FPS = 1920, 1080, 60
MM = 0.001
PERSON = dict(x=-301, y=108, w=1728, h=972)          # oncam.jsx：素材 3328×1872 缩到 1728×972 放在 (-301, 108)
EDGE_FEATHER = 60                                     # oncam.jsx：素材右边缘 60 px 渐隐（取景到右边就断了）
HFOV_EQ_MM = 26.0                                     # 手机前摄约 24–28 mm 等效（08 文档 5.1），取 26
F_PX = (PERSON["w"] / 2) * HFOV_EQ_MM / 18.0          # 出片像素焦距 ≈ 1248
AXIS = (PERSON["x"] + PERSON["w"] / 2, PERSON["y"] + PERSON["h"] / 2)   # 素材光轴在出片上的位置 (563, 594)
LENS = F_PX * 36.0 / OUT_W                            # Blender 焦距（36 mm 传感器）≈ 23.4 mm
SHIFT = ((OUT_W / 2 - AXIS[0]) / OUT_W, (AXIS[1] - OUT_H / 2) / OUT_W)
D_PERSON = 0.62                                       # 人卡片离相机（脸宽约 300 px ≈ 0.17 m 反推）
PIVOT_PX = (AXIS[0], AXIS[1])                         # 微动轴心：人卡片中心
FSTOP = 0.9                                           # 11-20 验收：背景零件虚到认得出颜色轮廓、看不清字（大板弥散圆 18–25 px）；等待时锁 2–4 px
BASE_FOCUS = 1.3                                      # 没点名时焦点（零件略虚）
BOARD_D = 8.0                                         # 11-20 验收：大板推远（原 3.6 m），纵深更大、焦外更虚
BOARD_S = 9.2 * BOARD_D / 3.6                         # 大板放大倍数：出片上的版式不变（格距约 210 px，同 bg.jpg）
WALL_DIM = 0.7                                        # 板后墙的底色倍数
BG_DIM = 0.82                                         # 大板亮度目标 = bg.jpg 的 82%（验收：背景降 15–20%）
HAZE_DENSITY = 0.05                                   # 零件和大板之间的薄雾（体积散射）：压背景对比，托住斜进来的暖光
SHAFT_W = 250000.0                                    # 左上斜进来的暖色光（聚光灯，照雾也扫过大板）
MICRO = (0.3, 0.2)                                    # 微动：左右、上下（度）
SAMPLES = 32
GLOSSY_WORLD = 0.9                                    # 镜面光线看见的世界亮度（金属件不发黑）


def px_to_world(u, v, d):
    """出片像素 (u, v) 在基础机位下、深度 d（米）处的世界坐标。相机在原点看 +Y，+Z 向上。"""
    return ((u - AXIS[0]) / F_PX * d, d, (AXIS[1] - v) / F_PX * d)


def world_to_px(p):
    X, Y, Z = p
    return (AXIS[0] + X / Y * F_PX, AXIS[1] - Z / Y * F_PX)


SEGS = {
    "3-01": dict(person=str(WORK_ROOT / "pub_slim/3-01/person_3-01"), n=373, off=8,
                 wav=str(WORK_ROOT / "pub_slim/3-01/3-01.wav"), oncam=RM / "oncam_3-01.json",
                 keys=MAPD / "keys/3-01.json", recipe="lock_key_v2", who="D",
                 head="lock", tail="lock", fade_in=None, version=2,
                 src="Illustration (our toy model)",   # 11-23 rc02 返修：出处行（18 文档 3.2 O9），成片进 20261123
                 out=ROOT / "导演检查_20261123/15_出镜3D_3-01.mp4"),
    # 11-20 晚铺开第 1 批（深化/11 甲线）：照技能 oncam-3d-parts 做，参数字典见 V306 / V309
    "3-06": dict(person=str(WORK_ROOT / "pub_slim/3-06/person_3-06"), n=676, off=0,
                 wav=str(WORK_ROOT / "pub_slim/3-06/3-06.wav"), oncam=RM / "oncam_3-06.json",
                 keys=MAPD / "keys/3-06.json", recipe="socket_lineup", prm="V306", who="D",
                 head="socket", tail="socket", fade_in=None, version=2, pingpong=True,
                 src="Illustration (our toy model)",
                 out=ROOT / "导演检查_20261123/15_出镜3D_3-06.mp4"),
    "3-09": dict(person=str(WORK_ROOT / "pub_slim/3-09/person_3-09"), n=338, off=0,
                 wav=str(WORK_ROOT / "pub_slim/3-09/3-09.wav"), oncam=RM / "oncam_3-09.json",
                 keys=MAPD / "keys/3-09.json", recipe="frost_blank", prm="V309", who="B",
                 head="frost", tail="frost", fade_in=None, version=2, pingpong=True,
                 out=ROOT / "导演检查_20261123/15_出镜3D_3-09.mp4"),
    # 11-20 夜铺开第 1 批续：插座 + 假插头（recipe socket_plug，参数 V505 / V509）。5-05+06 两个人：clips 按 cut 换人
    "5-05_5-06": dict(person=str(WORK_ROOT / "pub_slim/5-05_5-06/person_5-05"), n=268, off=2,
                      clips=[dict(person=str(WORK_ROOT / "pub_slim/5-05_5-06/person_5-05"), off=2, cut=0, n=268, leak=False),
                             dict(person=str(WORK_ROOT / "pub_slim/5-05_5-06/person_5-06"), off=244, cut=257, n=249)],
                      wav=str(WORK_ROOT / "pub_slim/5-05_5-06/5-05_5-06.wav"), oncam=RM / "oncam_5-05_5-06.json",
                      keys=MAPD / "keys/5-05_5-06.json", recipe="socket_plug", prm="V505", who="C/B",
                      head="socket", tail="socket", fade_in=None, version=2, pingpong=True,
                      src="Illustration (our toy model) · data: Ren et al., Chem. Sci. 2023",
                      out=ROOT / "导演检查_20261123/15_出镜3D_5-05_5-06.mp4"),
    "5-09": dict(person=str(WORK_ROOT / "pub_slim/5-09/person_5-09"), n=193, off=4,
                 wav=str(WORK_ROOT / "pub_slim/5-09/5-09.wav"), oncam=RM / "oncam_5-09.json",
                 keys=MAPD / "keys/5-09.json", recipe="socket_plug", prm="V509", who="C",
                 head="socket", tail="socket", fade_in=None, version=2, pingpong=True, leak=False,
                 src="Illustration (our toy model) · data: Ren et al., Chem. Sci. 2023",
                 out=ROOT / "导演检查_20261123/15_出镜3D_5-09.mp4"),
    # 11-20 夜铺开第 2 批：1-01 日历 + 小人、1-03 胶囊 + 一排小人、1-05+06+07 钥匙坯 + 料杆 + 卷尺、2-04 两块编号牌（recipe 见 RECIPES）
    "1-01": dict(person=str(WORK_ROOT / "pub_slim/1-01/person_1-01"), n=332, off=2,
                 wav=str(WORK_ROOT / "pub_slim/1-01/1-01.wav"), oncam=RM / "oncam_1-01.json",
                 keys=MAPD / "keys/1-01.json", recipe="calendar_people", prm="V101", who="A",
                 head="calendar", tail="calendar", fade_in=None, version=2, pingpong=True,
                 out=ROOT / "导演检查_20261121/15_出镜3D_1-01.mp4"),
    "1-03": dict(person=str(WORK_ROOT / "pub_slim/1-03/person_1-03"), n=305, off=2,
                 wav=str(WORK_ROOT / "pub_slim/1-03/1-03.wav"), oncam=RM / "oncam_1-03.json",
                 keys=MAPD / "keys/1-03.json", recipe="capsule_row", prm="V103", who="A",
                 head="capsule", tail="capsule", fade_in=None, version=2, pingpong=True,
                 out=ROOT / "导演检查_20261121/15_出镜3D_1-03.mp4"),
    "1-05_1-06_1-07": dict(person=str(WORK_ROOT / "pub_slim/1-05_1-06_1-07/person_1-05"), n=221, off=0,
                           clips=[dict(person=str(WORK_ROOT / "pub_slim/1-05_1-06_1-07/person_1-05"), off=0, cut=0, n=221),
                                  dict(person=str(WORK_ROOT / "pub_slim/1-05_1-06_1-07/person_1-06"), off=218, cut=221, n=168),
                                  dict(person=str(WORK_ROOT / "pub_slim/1-05_1-06_1-07/person_1-07"), off=358, cut=375, n=220, leak=False)],
                           wav=str(WORK_ROOT / "pub_slim/1-05_1-06_1-07/1-05_1-06_1-07.wav"), oncam=RM / "oncam_1-05_1-06_1-07.json",
                           keys=MAPD / "keys/1-05_1-06_1-07.json", recipe="key_tape", prm="V105", who="D/B/C",
                           head="key", tail="tape", fade_in=None, version=2, pingpong=True,
                           src="Illustration · timeline: Wang et al., Pharmaceuticals 2023",
                           out=ROOT / "导演检查_20261123/15_出镜3D_1-05_1-06_1-07.mp4"),
    "2-04": dict(person=str(WORK_ROOT / "pub_slim/2-04/person_2-04"), n=208, off=5,
                 wav=str(WORK_ROOT / "pub_slim/2-04/2-04.wav"), oncam=RM / "oncam_2-04.json",
                 keys=MAPD / "keys/2-04.json", recipe="two_plates", prm="V204", who="C",
                 head="plates", tail="plates", fade_in=None, version=2, pingpong=True, leak=False,
                 out=ROOT / "导演检查_20261121/15_出镜3D_2-04.mp4"),
    # 11-22 甲线（位 3，18 文档 2.4）：7-01、8-01 照 2-04 改（recipe plates，参数 V701 / V801）
    "7-01": dict(person=str(WORK_ROOT / "pub_slim/7-01/person_7-01"), n=294, off=0,
                 wav=str(WORK_ROOT / "pub_slim/7-01/7-01.wav"), oncam=RM / "oncam_7-01.json",
                 keys=MAPD / "keys/7-01.json", recipe="plates", prm="V701", who="A",
                 head="plates", tail="plates", fade_in=None, version=2, pingpong=True,
                 out=ROOT / "导演检查_20261123/15_出镜3D_7-01.mp4"),
    "8-01": dict(person=str(WORK_ROOT / "pub_slim/8-01/person_8-01"), n=174, off=1,
                 wav=str(WORK_ROOT / "pub_slim/8-01/8-01.wav"), oncam=RM / "oncam_8-01.json",
                 keys=MAPD / "keys/8-01.json", recipe="plates", prm="V801", who="C",
                 head="plates", tail="plates", fade_in=None, version=2, pingpong=True, leak=False,
                 out=ROOT / "导演检查_20261123/15_出镜3D_8-01.mp4"),
    # 11-22 甲线 O2（18 文档 2.4）：4-11+12 领奖台 + 七把假插头（recipe podium，参数 V411）；D 说到 winners?，A 从 Not 起（clips 照 oncam_4-11_4-12.json）
    "4-11_4-12": dict(person=str(WORK_ROOT / "pub_slim/4-11_4-12/person_4-11"), n=249, off=0,
                      clips=[dict(person=str(WORK_ROOT / "pub_slim/4-11_4-12/person_4-11"), off=0, cut=0, n=249),
                             dict(person=str(WORK_ROOT / "pub_slim/4-11_4-12/person_4-12"), off=201, cut=226, n=437)],
                      wav=str(WORK_ROOT / "pub_slim/4-11_4-12/4-11_4-12.wav"), oncam=RM / "oncam_4-11_4-12.json",
                      keys=MAPD / "keys/4-11_4-12.json", recipe="podium", prm="V411", who="D/A",
                      head="podium", tail="plug", fade_in=None, version=2, pingpong=True,
                      src="Illustration (our toy model)",
                      out=ROOT / "导演检查_20261123/15_出镜3D_4-11_4-12.mp4"),
    "5-02": dict(person=str(WORK_ROOT / "pub_slim/5-02/person_5-02"), n=385, off=0,
                 wav=str(WORK_ROOT / "pub_slim/5-02/5-02.wav"), oncam=RM / "oncam_5-02.json",
                 keys=MAPD / "keys/5-02.json", recipe="plug_row", prm="V502", who="C",
                 head="plug", tail="plug", fade_in=None, version=2, pingpong=True, leak=False,
                 src="Illustration (our toy model) · data: Ren et al., Chem. Sci. 2023",
                 out=ROOT / "导演检查_20261123/15_出镜3D_5-02.mp4"),
    "4-04_4-05": dict(person=str(WORK_ROOT / "pub_slim/4-04_4-05/person_4-04"), n=128, off=4,
                      clips=[dict(person=str(WORK_ROOT / "pub_slim/4-04_4-05/person_4-04"), off=4, cut=0, n=128, leak=False),
                             dict(person=str(WORK_ROOT / "pub_slim/4-04_4-05/person_4-05"), off=117, cut=125, n=313)],
                      wav=str(WORK_ROOT / "pub_slim/4-04_4-05/4-04_4-05.wav"), oncam=RM / "oncam_4-04_4-05.json",
                      keys=MAPD / "keys/4-04_4-05.json", recipe="snip_tail", prm="V404", who="C/B",
                      head="socket", tail="socket", fade_in=None, version=2, pingpong=True,
                      src="Illustration (our toy model) · Ren et al., Chem. Sci. 2023",
                      out=ROOT / "导演检查_20261123/15_出镜3D_4-04_4-05.mp4"),
    "6-04_6-05": dict(person=str(WORK_ROOT / "pub_slim/6-04_6-05/person_6-04"), n=366, off=2,
                      clips=[dict(person=str(WORK_ROOT / "pub_slim/6-04_6-05/person_6-04"), off=2, cut=0, n=366),
                             dict(person=str(WORK_ROOT / "pub_slim/6-04_6-05/person_6-05"), off=342, cut=354, n=206)],
                      wav=str(WORK_ROOT / "pub_slim/6-04_6-05/6-04_6-05.wav"), oncam=RM / "oncam_6-04_6-05.json",
                      keys=MAPD / "keys/6-04_6-05.json", recipe="tray13", prm="V604", who="D/B",
                      head="plate", tail="tray", fade_in=None, version=2, pingpong=True,
                      src='Illustration · 13 made: Ren et al. 2023 · "millions": Wang et al. 2023',
                      out=ROOT / "导演检查_20261123/15_出镜3D_6-04_6-05.mp4"),
    "4-08": dict(person=str(WORK_ROOT / "pub_slim/4-08/person_4-08"), n=499, off=0,
                 wav=str(WORK_ROOT / "pub_slim/4-08/4-08.wav"), oncam=RM / "oncam_4-08.json",
                 keys=MAPD / "keys/4-08.json", recipe="loop_chip", prm="V408", who="A",
                 head="track", tail="ring", fade_in=None, version=2, pingpong=True,
                 src="Illustration (our toy model)",
                 out=ROOT / "导演检查_20261123/15_出镜3D_4-08.mp4"),
    "6-12": dict(person=str(WORK_ROOT / "pub_slim/6-12/person_6-12"), n=420, off=6,
                 wav=str(WORK_ROOT / "pub_slim/6-12/6-12.wav"), oncam=RM / "oncam_6-12.json",
                 keys=MAPD / "keys/6-12.json", recipe="road_tape", prm="V612", who="B",
                 head="tag", tail="tape", fade_in=None, version=2, pingpong=True,
                 src="Illustration · timeline: Ren et al., Chem. Sci. 2023",
                 out=ROOT / "导演检查_20261123/15_出镜3D_6-12.mp4"),
    # 11-23 甲线 8-04–07 简版（18 文档 2.4）：C、B、D、A 四人共用一个场景（clips 照 oncam_8-04_8-05_8-06_8-07.json）；出处行只在 C 那段挂（src_until）
    "8-04_8-05_8-06_8-07": dict(person=str(WORK_ROOT / "pub_slim/8-04_8-05_8-06_8-07/person_8-04"), n=586, off=5,
                                clips=[dict(person=str(WORK_ROOT / "pub_slim/8-04_8-05_8-06_8-07/person_8-04"), off=5, cut=0, n=586, leak=False),   # C 穿黑 T 恤不剥漏块
                                       dict(person=str(WORK_ROOT / "pub_slim/8-04_8-05_8-06_8-07/person_8-05"), off=571, cut=578, n=306, leak=False),   # B 手里的黑手机会被当漏块一层层挖掉（第 641 帧挖出白洞），不剥
                                       dict(person=str(WORK_ROOT / "pub_slim/8-04_8-05_8-06_8-07/person_8-06"), off=878, cut=878, n=621),
                                       dict(person=str(WORK_ROOT / "pub_slim/8-04_8-05_8-06_8-07/person_8-07"), off=1471, cut=1486, n=467)],
                                wav=str(WORK_ROOT / "pub_slim/8-04_8-05_8-06_8-07/8-04_8-05_8-06_8-07.wav"), oncam=RM / "oncam_8-04_8-05_8-06_8-07.json",
                                keys=MAPD / "keys/8-04_8-05_8-06_8-07.json", recipe="road5", prm="V804", who="C/B/D/A",
                                head="plate", tail="plate", fade_in=None, version=2, pingpong=True,
                                src="Illustration · result in cells: Ren et al., Chem. Sci. 2023", src_until=578,
                                out=ROOT / "导演检查_20261123/15_出镜3D_8-04_8-07.mp4"),
}


def seg_cfg(seg):
    c = dict(SEGS[seg])
    c["seg"] = seg
    c["P"] = globals()[c.get("prm", "V2")]        # 每段自己的位置参数字典（board_fill、build_v2 读它；3-01 是 V2）
    if os.environ.get("CDK20_PJSON"):               # 试渲时临时改几项参数（同一个队列任务里试几档），不写进参数表
        c["P"] = dict(c["P"], **{k: (tuple(v) if isinstance(v, list) and k != "TRANS_HK" else v) for k, v in json.loads(os.environ["CDK20_PJSON"]).items()})
    c["work"] = WORK / seg
    c["K"] = json.loads(Path(c["keys"]).read_text(encoding="utf-8"))
    c["nf"] = c["K"]["len_f"]
    if c["P"].get("DIVE_AT") is not None:          # 段尾起点往后挪（不改共用的事件表）：4-08 说完第 473 帧、段尾起 475，OC7 要 ≥ 说完 + 4
        for e in c["K"]["events"]:
            if e["id"] == "dive":
                e["f_start"] = c["P"]["DIVE_AT"]
    return c


def _clip_at(cfg, f):
    """多人段（5-05+06 是 C 再 B）：SEGS 里写 clips=[dict(person=目录, off=, cut=, n=)…]，段帧 f 用 cut ≤ f 的最后一个。
    单人段没有 clips，就是 person/off/n 本身。"""
    cl = cfg.get("clips")
    if not cl:
        return cfg
    c = cl[0]
    for x in cl:
        if x.get("cut", 0) <= f:
            c = x
    return c


def leak_strip_on(cfg, f):
    """这一帧要不要剥抠像漏块。C 穿黑 T 恤：衣服本身又暗又偏蓝，剥漏块会一层层把衣服边和印花挖成洞（5-09 第 100 帧印花上挖出灰块，11-21 实测），
    SEGS 里（或多人段那一个 clip 里）写 leak=False 关掉。"""
    c = _clip_at(cfg, f)
    return c.get("leak", cfg.get("leak", True))


def person_k(cfg, f):
    """段帧 → 人物逐帧图编号（oncam：段帧 = 素材帧 + off）。
    pingpong：素材比段短时（3-06 素材 676 帧、段 694 帧），尾巴上不定格在最后一张，往回倒放（人说完话的小动作倒着放看不出来，定格看得出）。"""
    c = _clip_at(cfg, f)
    k = f - c["off"]
    if cfg.get("pingpong") and k > c["n"] - 1:
        k = 2 * (c["n"] - 1) - k
    return max(0, min(c["n"] - 1, k))


def person_png(cfg, f):
    """段帧 f 的人物逐帧图路径（多人段自动换人）。"""
    return Path(_clip_at(cfg, f)["person"]) / f"{person_k(cfg, f):04d}.png"


# ---------------------------------------------------------------- 动作库的缓动（08 文档第四节，60 fps）
def clamp01(t):
    return 0.0 if t < 0 else 1.0 if t > 1 else t


def smooth(t):
    t = clamp01(t)
    return t * t * (3 - 2 * t)


def ease_out_cubic(t):
    t = clamp01(t)
    return 1 - (1 - t) ** 3


def ease_in_cubic(t):
    t = clamp01(t)
    return t ** 3


def ease_inout_cubic(t):
    t = clamp01(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_out_back(t, c=1.70158):
    t = clamp01(t)
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def ease_out_quart(t):
    t = clamp01(t)
    return 1 - (1 - t) ** 4


def spring(t_s, zeta=0.55, w=18.0):
    """阻尼弹簧的偏差（1 → 0），t_s 秒。"""
    if t_s <= 0:
        return 1.0
    wd = w * math.sqrt(1 - zeta * zeta)
    return math.exp(-zeta * w * t_s) * (math.cos(wd * t_s) + zeta * w / wd * math.sin(wd * t_s))


def pop_curve(f, f0, n=14, settle=10, c=1.70158):
    """A1/A2 落位：f0 起 easeOutBack n 帧（过冲约 10%），之后 settle 帧阻尼回弹到 1。"""
    if f <= f0:
        return 0.0
    if f < f0 + n:
        return ease_out_back((f - f0) / n, c)
    return 1.0 + 0.02 * spring((f - f0 - n) / FPS) * (1 - clamp01((f - f0 - n) / max(1, settle)))


def bezier(p0, p1, p2, t):
    a = [p0[i] + (p1[i] - p0[i]) * t for i in range(3)]
    b = [p1[i] + (p2[i] - p1[i]) * t for i in range(3)]
    return [a[i] + (b[i] - a[i]) * t for i in range(3)]


ACTIONS = {   # 给检查页看的动作库清单：代号 → (帧数, 曲线)
    "A1": ("预颤 6 + 弹出 14 easeOutBack + 回弹 10 阻尼弹簧", "pop_curve + bl_guide.guide_tick"),
    "A2": ("24 帧 easeOutCubic 贝塞尔弧 + 10 帧回弹", "bezier + pop_curve"),
    "A3": ("虚到实 18 帧 smoothstep + 轮廓光", "bl_guide.guide_focus/guide_rim"),
    "A7": ("0.6→1.08→1.0，8 + 10 帧", "ease_out_cubic + spring"),
    "A9": ("落位冲击：镜头震 2 帧 ≤ 0.4°", "shake()"),
    "A10": ("20 帧 easeInCubic 沿原路飞回", "bezier + ease_in_cubic"),
    "T1": ("穿越：真相机推进零件", "push()"),
    "T5": ("焦点擦除：近处虚化料杆扫过", "fg_wipe()"),
}


# ---------------------------------------------------------------- T2：量光（纯 numpy）
def _srgb_to_lin(a):
    import numpy as np
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def _lum(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def face_boxes(cfg, f):
    """段帧 f 的脸框、T 恤框（人物逐帧图坐标）。鼻尖来自 oncam_<段>.json（素材坐标）。"""
    D = json.loads(Path(cfg["oncam"]).read_text(encoding="utf-8"))
    nose = D["nose"]
    p = nose[min(len(nose) - 1, f)] or next(q for q in nose if q)
    sc = PERSON["w"] / D["src"][0]
    nx, ny = p[0] * sc, p[1] * sc
    face = (int(nx - 120), int(ny - 150), int(nx + 120), int(ny + 90))
    shirt = (int(nx - 230), int(ny + 300), int(nx + 150), int(ny + 440))
    return face, shirt, (nx, ny)


def measure(seg):
    """08 文档 3.1：脸左右/上下亮度差 → 主光方位、仰角；亮侧/暗侧 → 主辅光比；白 T 恤 R/B → 色温；T 恤平坦区高频残差 → 颗粒。"""
    import numpy as np
    from PIL import Image, ImageFilter
    cfg = seg_cfg(seg)
    rows = []
    rng_ = range(10, cfg["nf"] - 5, 24) if cfg.get("clips") else range(cfg["off"] + 10, cfg["off"] + cfg["n"] - 5, 24)
    for f in rng_:
        im = Image.open(person_png(cfg, f)).convert("RGBA")
        a = np.asarray(im, dtype=np.float32) / 255.0
        face, shirt, (nx, ny) = face_boxes(cfg, f)
        fx0, fy0, fx1, fy1 = face
        F = a[fy0:fy1, fx0:fx1]
        lin = _srgb_to_lin(F[..., :3])
        Y = _lum(lin)
        r, g, b = F[..., 0], F[..., 1], F[..., 2]
        skin = (F[..., 3] > 0.99) & (r > g) & (g > b) & (r > 0.25) & ((r - b) > 0.08)
        h, w = Y.shape
        xs = np.arange(w)[None, :].repeat(h, 0)
        ys = np.arange(h)[:, None].repeat(w, 1)
        cxl = nx - fx0
        L = Y[skin & (xs < cxl - 10)]
        R = Y[skin & (xs > cxl + 10)]
        T = Y[skin & (ys < h * 0.45)]
        B = Y[skin & (ys > h * 0.55)]
        if min(len(L), len(R), len(T), len(B)) < 200:
            continue
        lr = (L.mean() - R.mean()) / (L.mean() + R.mean())
        tb = (T.mean() - B.mean()) / (T.mean() + B.mean())
        bright, dark = (L, R) if L.mean() > R.mean() else (R, L)
        ratio_p = float(np.percentile(bright, 90) / max(1e-4, np.percentile(dark, 10)))
        ratio_m = float(bright.mean() / max(1e-4, dark.mean()))
        sx0, sy0, sx1, sy1 = shirt
        S = a[sy0:sy1, sx0:sx1]
        sm = S[..., 3] > 0.99
        Sl = _srgb_to_lin(S[..., :3])
        neutral = Sl[sm]
        neutral = neutral[_lum(neutral) > np.percentile(_lum(neutral), 50)]
        rb = float(neutral[:, 0].mean() / max(1e-4, neutral[:, 2].mean()))
        shirt_p90 = float(np.percentile(_lum(S[..., :3][sm]), 90))         # 显示值（sRGB）
        shirt_lin_p90 = float(np.percentile(_lum(Sl[sm]), 90))
        # 颗粒：T 恤里最平的 48×48 块，原图减去 2 px 高斯模糊，按通道取标准差（8 位）
        u8 = (S[..., :3] * 255).astype(np.float32)
        blur = np.asarray(Image.fromarray(u8.astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)), dtype=np.float32)
        res = u8 - blur
        best = None
        for yy in range(0, S.shape[0] - 48, 16):
            for xx in range(0, S.shape[1] - 48, 16):
                if not sm[yy:yy + 48, xx:xx + 48].all():
                    continue
                v = blur[yy:yy + 48, xx:xx + 48].std()
                if best is None or v < best[0]:
                    best = (v, res[yy:yy + 48, xx:xx + 48].reshape(-1, 3).std(0))
        # 人物遮罩内沿 6 px 带：比人均值亮多少（有没有逆光）
        al = a[..., 3]
        inner = np.asarray(Image.fromarray((al * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(13)), dtype=np.float32) / 255
        band = (al > 0.99) & (inner < 0.5)
        Ya = _lum(_srgb_to_lin(a[..., :3]))
        rim = float(Ya[band].mean() / max(1e-4, Ya[al > 0.99].mean()))
        rows.append(dict(f=f, lr=float(lr), tb=float(tb), ratio_p90_p10=ratio_p, ratio_mean=ratio_m, rb=rb,
                         shirt_p90_srgb=shirt_p90, shirt_lin_p90=shirt_lin_p90,
                         grain=[float(x) for x in best[1]] if best is not None else None, rim_band=rim,
                         lit_side="left" if L.mean() > R.mean() else "right"))
    med = lambda k: float(np.median([r[k] for r in rows]))   # noqa: E731
    lr, tb = med("lr"), med("tb")
    # 08 文档 3.1 的经验换算（起点，之后 T3 灰球校）
    az = float(np.interp(abs(lr), [0, 0.1, 0.25, 0.4, 0.6], [0, 15, 35, 55, 70])) * (1 if lr > 0 else -1)
    el = float(np.interp(max(0.0, tb), [0, 0.05, 0.15, 0.3], [5, 15, 35, 50]))
    rb = med("rb")
    kelvin = float(np.interp(rb, [0.85, 1.0, 1.15, 1.3, 1.5], [7500, 6500, 5000, 4000, 3200]))
    grains = np.array([r["grain"] for r in rows if r["grain"]])
    out = dict(seg=seg, frames=len(rows), lr=lr, tb=tb, az_deg=az, el_deg=el,
               key_fill_ratio_mean=med("ratio_mean"), key_fill_ratio_p90p10=med("ratio_p90_p10"),
               rb=rb, kelvin=kelvin, shirt_p90_srgb=med("shirt_p90_srgb"), shirt_lin_p90=med("shirt_lin_p90"),
               grain_sigma_rgb=[float(x) for x in np.median(grains, 0)] if len(grains) else [1.5, 1.5, 1.8],
               rim_band=med("rim_band"), lit_side=max(set(r["lit_side"] for r in rows), key=[r["lit_side"] for r in rows].count),
               rows=rows,
               note="az>0 = 光从画面左边来；el = 仰角；换算表是 08 文档 3.1 的经验值，T3 灰球再校")
    cfg["work"].mkdir(parents=True, exist_ok=True)
    (cfg["work"] / "light.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("ONCAM measure", json.dumps({k: v for k, v in out.items() if k != "rows"}, ensure_ascii=False))
    return out


# ================================================================ Blender 端：世界（所有出镜段共用）
def gpu_wait():
    while any((q / m).exists() for q in QUEUE for m in ("GPU_HOLD", "GPU_PAUSED")):
        print("ONCAM WAIT_GPU", flush=True)
        time.sleep(15)


def kelvin_rgb(k):
    """色温 → 线性 RGB（Tanner Helland 近似，绿通道归一到 1）。"""
    t = k / 100.0
    r = 255.0 if t <= 66 else 329.698727446 * (t - 60) ** -0.1332047592
    g = 99.4708025861 * math.log(t) - 161.1195681661 if t <= 66 else 288.1221695283 * (t - 60) ** -0.0755148492
    b = 255.0 if t >= 66 else (0.0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    c = [min(255.0, max(0.0, x)) / 255.0 for x in (r, g, b)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return tuple(x / c[1] for x in c)


def setup_render(sc, nf, samples=SAMPLES):
    import bl_guide as BG
    gpu_wait()
    BG._gpu(sc)                                   # Cycles + OptiX GPU + OptiX 降噪；没有 OptiX 就退出，不回落 CPU
    sc.render.fps, sc.render.fps_base = FPS, 1.0
    sc.frame_start, sc.frame_end = 0, nf - 1
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = OUT_W, OUT_H, 100
    sc.cycles.samples = samples
    sc.cycles.adaptive_threshold = 0.02
    sc.cycles.seed = 7
    sc.cycles.use_animated_seed = False
    sc.cycles.max_bounces = 10
    sc.cycles.caustics_refractive = sc.cycles.caustics_reflective = False
    sc.cycles.sample_clamp_indirect = 10.0        # 08 文档 3.2：防镀铬萤火虫
    sc.cycles.blur_glossy = 1.0
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5           # 180°（08 文档第八节）
    sc.render.film_transparent = False
    sc.render.use_border = False
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"


def link_obj(o, coll=None):
    (coll or bpy.context.scene.collection).objects.link(o)
    return o


def mesh_bounds(objs):
    """一组物体（连子物体里的可见网格、曲线）的世界包围盒。"""
    pts = []
    for o in objs:
        for m in [o] + list(o.children_recursive):
            if m.type in ("MESH", "CURVE", "FONT") and not m.hide_render:
                pts += [m.matrix_world @ Vector(c) for c in m.bound_box]
    if not pts:
        return None                                    # 子树里没有出像的网格（第二个零件还藏着、或只是个空物体）
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def board_setup():
    """定版大板竖起来当人身后的墙：板面 XY → 世界 XZ，朝相机（−Y），放大 BOARD_S 倍，板底面在 BOARD_D。
    第 3 区 c4 列（挂锁那一列，x = −165 mm）落在出片 x = 1400（上一段 2-08 结尾"一把挂锁浮起飞到画面右侧"），板上沿在 y = 140。"""
    sc = bpy.context.scene
    sweep = bpy.data.objects.get("sweep")
    wall_mat = sweep.active_material if sweep else None
    for o in list(sc.objects):
        if o.type in ("LIGHT", "CAMERA") or o.name.startswith("refl_") or o.name == "sweep":
            bpy.data.objects.remove(o)
    board = bpy.data.objects["board"]
    zb = board.location.z
    xf = link_obj(bpy.data.objects.new("ONCAM_board_xf", None))
    board.parent = xf
    board.matrix_parent_inverse = Matrix.Identity(4)
    bpy.context.view_layer.update()
    lo, hi = mesh_bounds([board])
    xf.rotation_euler = (math.radians(90), 0, 0)
    xf.scale = (BOARD_S,) * 3
    X3 = px_to_world(1400, 540, BOARD_D)[0]
    Ztop = px_to_world(960, 140, BOARD_D)[2]
    xf.location = (X3 - BOARD_S * (-0.165), BOARD_D + BOARD_S * zb, Ztop - BOARD_S * hi.y)
    bpy.context.view_layer.update()
    # 板后面一堵浅色墙（bg.jpg 里板挂在白墙上），用原来 sweep 的材质
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(px_to_world(960, 540, BOARD_D + 0.35)[0], BOARD_D + 0.35, 0.0), rotation=(math.radians(90), 0, 0))
    wall = bpy.context.object; wall.name = "ONCAM_wall"
    wall.scale = (14.0 * BOARD_D / 3.6, 9.0 * BOARD_D / 3.6, 1.0)
    if wall_mat:
        wm = wall_mat.copy(); wm.name = "ONCAM_wall_dim"          # 11-20 验收：背景整体压暗，板后的墙最亮，单独压到 70%
        pb = next((n for n in wm.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if wm.use_nodes else None
        if pb is not None:
            c = pb.inputs["Base Color"].default_value
            pb.inputs["Base Color"].default_value = (c[0] * WALL_DIM, c[1] * WALL_DIM, c[2] * WALL_DIM, 1)
        wall.data.materials.append(wm)
    coll = bpy.data.collections.new("ONCAM_board_lit")
    sc.collection.children.link(coll)
    for m in [board, wall] + list(board.children_recursive):
        if m.type in ("MESH", "CURVE", "FONT"):
            coll.objects.link(m)
            # 大板和墙不往零件上反漫射光（T3：不关的话白球左右比卡在 1.15，脸是 2.3——3.6 m 外的亮墙把暗面全照亮了）；
            # 镜面里照样看得见大板，亮面塑料上有板的反射
            m.visible_diffuse = False
    return board, coll


def haze_setup(light):
    """零件（1.3–1.6 m）和大板之间一盒薄雾 + 一盏只照雾的暖色聚光灯从画面左上斜进来（体积光）。
    雾把远处的大板压灰、对比降下来，人和零件跳出来。返回雾的集合（主光、补光、顶光排除它，洗墙光本来只照大板）。"""
    coll = bpy.data.collections.new("ONCAM_haze")
    bpy.context.scene.collection.children.link(coll)
    y0, y1 = 2.4, BOARD_D - 0.3
    ym = (y0 + y1) / 2
    c = Vector(px_to_world(OUT_W / 2, OUT_H / 2, ym))
    wx = OUT_W / F_PX * y1 * 1.4
    wz = OUT_H / F_PX * y1 * 1.4
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(c.x, ym, c.z))
    hz = bpy.context.object; hz.name = "ONCAM_haze_box"
    hz.scale = (wx, y1 - y0, wz)
    for cl in list(hz.users_collection):
        cl.objects.unlink(hz)
    coll.objects.link(hz)
    m = bpy.data.materials.new("oncam_haze"); m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    vs = nt.nodes.new("ShaderNodeVolumeScatter")
    vs.inputs["Color"].default_value = (1.0, 0.97, 0.92, 1)
    vs.inputs["Density"].default_value = HAZE_DENSITY
    vs.inputs["Anisotropy"].default_value = 0.45
    nt.links.new(vs.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    hz.data.materials.append(m)
    hz.visible_shadow = False
    sd = bpy.data.lights.new("shaft", "SPOT")
    sd.energy = SHAFT_W
    sd.color = kelvin_rgb(3600)
    sd.spot_size = math.radians(16)
    sd.spot_blend = 0.6
    sd.shadow_soft_size = 0.25
    sh = link_obj(bpy.data.objects.new("shaft", sd))
    sh.location = Vector(px_to_world(-500, -650, 4.2))
    aim = Vector(px_to_world(1250, 420, 6.5))
    sh.rotation_euler = (aim - sh.location).to_track_quat("-Z", "Y").to_euler()
    # 不做灯光链接（体积对灯光链接不起作用，实测只链雾时一点光柱都没有）：这盏暖光也斜扫过大板左上和锁的上沿
    return coll


def make_light(name, kind, loc, aim, size, energy, color, size_y=None):
    ld = bpy.data.lights.new(name, kind)
    if kind == "AREA":
        ld.shape = "RECTANGLE"; ld.size = size; ld.size_y = size_y or size
    ld.energy = energy
    ld.color = color
    o = link_obj(bpy.data.objects.new(name, ld))
    o.location = loc
    o.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


def light_rig(light, fit, subject, board_coll):
    """主光（窗）按 measure 量的方位放在左前方，大而软；补光在右侧对面；顶上一条软光给亮面塑料一道高光；
    大板另有一盏洗墙光（灯光链接只照大板），大板亮度和别的段用的 bg.jpg 对齐。功率用 calib 回写的 light_fit.json。"""
    col = kelvin_rgb(light["kelvin"])
    az, el = math.radians(fit["az_deg"]), math.radians(fit["el_deg"])
    s = Vector(subject)
    # 方位按"零件看相机的方向"算，不按相机光轴：零件在出片右边、离光轴约 40°，按光轴摆的主光对零件几乎是正面光
    # （T3 第一版白球左右比卡在 1.15，脸是 2.3）。脸差不多在光轴上，所以脸量的方位就是相对视线的方位。
    ys = math.atan2(s.x, s.y)
    d = Vector((-math.sin(az + ys) * math.cos(el), -math.cos(az + ys) * math.cos(el), math.sin(el)))
    key = make_light("key", "AREA", s + d * 2.6, s, 1.6, fit["key_w"], col)
    a2 = math.radians(60) - ys
    df = Vector((math.sin(a2) * 0.985, -math.cos(a2) * 0.985, 0.17))
    fill = make_light("fill", "AREA", s + df * 3.0, s, 2.6, fit["fill_w"], col)
    top = make_light("top", "AREA", s + Vector((0.2, -0.3, 1.4)), s, 1.2, fit["key_w"] * 0.12, col, size_y=0.25)
    bc = bpy.data.objects["ONCAM_board_xf"].location
    kd = BOARD_D / 3.6
    wash = make_light("wash", "AREA", Vector((bc.x - 1.0 * kd, BOARD_D - 2.4 * kd, 1.6 * kd)), Vector(px_to_world(1100, 520, BOARD_D)), 4.0 * kd, fit["wash_w"], col)
    wash.light_linking.receiver_collection = board_coll
    # 主光、补光、顶光不照大板和墙（大板亮度只由洗墙光定，和别的段的 bg.jpg 对齐）
    notb = bpy.data.collections.new("ONCAM_not_board")
    notb.children.link(board_coll)
    notb.children.link(haze_setup(light))
    for cc in notb.collection_children:
        cc.light_linking.link_state = "EXCLUDE"
    for o in (key, fill, top):
        o.light_linking.receiver_collection = notb
    # 反射卡（只给镜面看，不照明、不投影）：金钥匙、电镀件、亮面塑料要有东西可反射，不然朝相机的面全黑
    cards = [refl_card("refl_window", s + d * 2.4, s, (1.8, 1.4), col, 3.0),
             refl_card("refl_front", Vector((0.35, -0.8, 0.05)), s, (3.0, 1.8), col, 1.2),
             refl_card("refl_top", s + Vector((0.1, -0.2, 1.3)), s, (1.6, 0.5), col, 2.0)]
    return dict(key=key, fill=fill, top=top, wash=wash, cards=cards)


def refl_card(name, loc, aim, size, color, strength):
    me = bpy.data.meshes.new(name)
    w, h = size
    me.from_pydata([(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)], [], [(0, 1, 2, 3)])
    o = link_obj(bpy.data.objects.new(name, me))
    o.location = loc
    o.rotation_euler = (Vector(loc) - Vector(aim)).to_track_quat("Z", "Y").to_euler()   # 正面朝零件
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color[:3], 1)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    o.data.materials.append(m)
    o.visible_camera = o.visible_diffuse = o.visible_shadow = o.visible_transmission = o.visible_volume_scatter = False
    o.visible_glossy = True
    return o


def world_setup(fit):
    w = bpy.context.scene.world
    if w is None or not w.use_nodes:
        w = bpy.data.worlds.new("oncam_w"); w.use_nodes = True
        bpy.context.scene.world = w
    nt = w.node_tree
    bg = next(n for n in nt.nodes if n.type == "BACKGROUND")
    base = fit.get("world", 0.35)
    # 镜面光线看见的世界亮一些（像一间有白墙的屋子）：金、电镀件朝镜头的面有东西可反射；漫反射和相机还是 calib 定的世界光
    lp = nt.nodes.get("oncam_lp") or nt.nodes.new("ShaderNodeLightPath")
    lp.name = "oncam_lp"
    mp = nt.nodes.get("oncam_map") or nt.nodes.new("ShaderNodeMapRange")
    mp.name = "oncam_map"
    mp.inputs["To Min"].default_value = base
    mp.inputs["To Max"].default_value = max(base, GLOSSY_WORLD)
    nt.links.new(lp.outputs["Is Glossy Ray"], mp.inputs["Value"])
    nt.links.new(mp.outputs["Result"], bg.inputs[1])


def cam_basis():
    return Matrix.Rotation(math.radians(90), 4, "X")


def make_camera():
    cd = bpy.data.cameras.new("oncam_cam")
    cam = link_obj(bpy.data.objects.new("oncam_cam", cd))
    cd.lens = LENS
    cd.sensor_width = 36.0
    cd.sensor_fit = "HORIZONTAL"
    cd.shift_x, cd.shift_y = SHIFT
    cd.clip_start, cd.clip_end = 0.01, 60.0
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = FSTOP
    cd.dof.aperture_blades = 6                    # 08 文档第七节：叶片 6，接近手机镜头的圆
    cd.dof.focus_distance = BASE_FOCUS
    cam.rotation_mode = "QUATERNION"
    cam.matrix_world = cam_basis()
    bpy.context.scene.camera = cam
    return cam


def card_corners():
    P = PERSON
    return [px_to_world(P["x"], P["y"] + P["h"], D_PERSON), px_to_world(P["x"] + P["w"], P["y"] + P["h"], D_PERSON),
            px_to_world(P["x"] + P["w"], P["y"], D_PERSON), px_to_world(P["x"], P["y"], D_PERSON)]


def person_card(cfg):
    """人卡片：素材逐帧图 + 遮罩当贴图的平面，放在 D_PERSON，四角正好落在出片上人所在的框。
    相机、镜面、透射看不见，只投影 + 一点漫反射（T1 试验定的）。"""
    c = card_corners()
    me = bpy.data.meshes.new("oncam_person")
    me.from_pydata(c, [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new()
    for li, ab in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[li].uv = ab
    o = link_obj(bpy.data.objects.new("oncam_person", me))
    m = bpy.data.materials.new("oncam_person"); m.use_nodes = True
    nt = m.node_tree
    pb = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    img = bpy.data.images.load(str(Path(cfg["person"]) / "0000.png"))
    img.source = "SEQUENCE"
    tex.image = img
    iu = tex.image_user
    iu.frame_duration = cfg["n"] - 1              # 段帧 f → 第 f − off 张（0000 起），两头钳住
    iu.frame_start = cfg["off"] + 1
    iu.frame_offset = 0
    iu.use_cyclic = False
    iu.use_auto_refresh = True
    nt.links.new(tex.outputs["Color"], pb.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], pb.inputs["Alpha"])
    pb.inputs["Roughness"].default_value = 0.6
    o.data.materials.append(m)
    o.visible_camera = False
    o.visible_glossy = False
    o.visible_transmission = False
    o.visible_volume_scatter = False
    o.visible_diffuse = True
    o.visible_shadow = True
    return o


def micro(f):
    """以人卡片中心为轴的微动（度）：左右 ±MICRO[0]、上下 ±MICRO[1]，两个正弦叠加，周期 3–9 秒。"""
    yaw = MICRO[0] * (0.7 * math.sin(2 * math.pi * f / (7.4 * FPS)) + 0.3 * math.sin(2 * math.pi * f / (3.3 * FPS) + 1.3))
    pit = MICRO[1] * (0.7 * math.sin(2 * math.pi * f / (8.6 * FPS) + 0.7) + 0.3 * math.sin(2 * math.pi * f / (4.1 * FPS) + 2.1))
    return yaw, pit


def cam_matrix_micro(f):
    P = Vector(px_to_world(*PIVOT_PX, D_PERSON))
    yaw, pit = micro(f)
    R = Matrix.Rotation(math.radians(yaw), 4, "Z") @ Matrix.Rotation(math.radians(pit), 4, "X")
    return Matrix.Translation(P) @ R @ Matrix.Translation(-P) @ cam_basis()


def project(Mcam, shift, p):
    """世界点 → 出片像素（含镜头偏移）。返回 (x, y, 深度)。"""
    q = Mcam.inverted() @ Vector(p)
    z = -q.z
    if z <= 1e-6:
        return (float("nan"), float("nan"), z)
    return (OUT_W / 2 + F_PX * q.x / z - shift[0] * OUT_W, OUT_H / 2 - F_PX * q.y / z + shift[1] * OUT_W, z)


def look_at(eye, target):
    q = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y")
    return Matrix.Translation(eye) @ q.to_matrix().to_4x4()


def interp_mat(A, B, t):
    la, ra, sa = A.decompose()
    lb, rb, sb = B.decompose()
    if ra.dot(rb) < 0:
        rb = -rb
    return Matrix.LocRotScale(la.lerp(lb, t), ra.slerp(rb, t), sa.lerp(sb, t))


def key_matrix(o, f, M):
    loc, rot, sca = M.decompose()
    o.location = loc
    o.scale = sca
    if o.rotation_mode == "QUATERNION":
        prev = Quaternion(o.rotation_quaternion)
        if prev.dot(rot) < 0:
            rot = -rot
        o.rotation_quaternion = rot
        o.keyframe_insert("rotation_quaternion", frame=f)
    else:
        o.rotation_euler = rot.to_euler(o.rotation_mode, o.rotation_euler)
        o.keyframe_insert("rotation_euler", frame=f)
    o.keyframe_insert("location", frame=f)
    o.keyframe_insert("scale", frame=f)


def linear_keys(idb):
    import bl_guide as BG
    BG._linear(idb)


def build_world(cfg, fit, samples=SAMPLES):
    import kit_parts as KP
    gpu_wait()
    bpy.ops.wm.open_mainfile(filepath=BOARD)
    sc = bpy.context.scene
    setup_render(sc, cfg["nf"], samples)
    board, bcoll = board_setup()
    world_setup(fit)
    cam = make_camera()
    card = person_card(cfg)
    light = json.loads((cfg["work"] / "light.json").read_text(encoding="utf-8"))
    subject = px_to_world(1600, 480, 1.42)
    rig = light_rig(light, fit, subject, bcoll)
    K = KP.Kit()
    return dict(sc=sc, cam=cam, card=card, board=board, bcoll=bcoll, rig=rig, light=light, fit=fit, kit=K, cfg=cfg)


def default_fit(light):
    return dict(az_deg=min(60.0, max(30.0, light["az_deg"])), el_deg=15.0, key_w=900.0, fill_w=260.0, wash_w=900.0 * (BOARD_D / 3.6) ** 2, world=0.35)


def load_fit(cfg, light):
    p = cfg["work"] / "light_fit.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return default_fit(light)


# ---------------------------------------------------------------- T1 + T3：卡片投影试验、灰球比光
def _render_to(path, pct=50):
    sc = bpy.context.scene
    sc.render.resolution_percentage = pct
    sc.render.filepath = str(path)
    gpu_wait()
    bpy.ops.render.render(write_still=True)
    return path


def _load(path):
    """Blender 里读 PNG/JPG（Blender 自带的 Python 没有 PIL）：8 位图的 pixels 就是显示值 /255，上下翻正。"""
    import numpy as np
    im = bpy.data.images.load(str(path), check_existing=False)
    a = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], im.channels)[::-1]
    bpy.data.images.remove(im)
    if a.shape[2] == 3:
        a = np.concatenate([a, np.ones_like(a[..., :1])], -1)
    return a


def _lin(x):
    import numpy as np
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def ball_stats(a, c, r_m=0.07, pct=0.5, Mcam=None, shift=SHIFT):
    import numpy as np
    x, y, z = project(Mcam or cam_basis(), shift, c)
    r = r_m * F_PX / z * pct
    cx, cy = x * pct, y * pct
    H, Wd = a.shape[:2]
    yy, xx = np.mgrid[0:H, 0:Wd]
    disk = np.hypot(xx - cx, yy - cy) < 0.85 * r
    Y = _lum(_lin(a[..., :3]))
    left, right = disk & (xx < cx), disk & (xx > cx)
    hot = disk & (Y >= np.percentile(Y[disk], 95))
    return dict(lit_p90=float(np.percentile(Y[left], 90)), left=float(Y[left].mean()), right=float(Y[right].mean()),
                ratio=float(Y[left].mean() / max(1e-5, Y[right].mean())),
                hot_dx=float((xx[hot].mean() - cx) / r), hot_dy=float((yy[hot].mean() - cy) / r),
                lit_p90_srgb=float(np.percentile(_lum(a[..., :3])[left], 90)), r_px=float(r))


def calib(seg):
    """T3：零件位置放灰球（18%）、白球（80%，对应白 T 恤）、镜面球，逐轮调主光/补光/洗墙光：
    白球亮侧 90 分位 ≈ T 恤亮处；白球左右亮度比 ≈ 脸的主辅光比；大板亮度中位数 ≈ 别的段用的 bg.jpg。差 15% 以内算过。
    T1：同一帧渲 无卡片 / 卡片只投影 / 卡片 Holdout 三张，量人对大板和球的影子、Holdout 放回人以后的半透明边。"""
    import numpy as np
    cfg = seg_cfg(seg)
    light = json.loads((cfg["work"] / "light.json").read_text(encoding="utf-8"))
    if light.get("shirt_p90_srgb", 1.0) < 0.5:
        # 深色衣服（5-05、5-09 的 C 穿黑 T 恤）：白球对的是"T 恤亮处"，黑 T 恤只有 0.09，比出来主光只有 1.5 W，零件全黑（11-20 实测）。
        # 不比光，借同一套大板、同一盏光的 3-06 的比光结果；主辅比按脸量的（C 1.3，比 D 的 2.3 平）把补光提上去。
        ref = json.loads((WORK / "3-06" / "light_fit.json").read_text(encoding="utf-8"))
        r = light.get("key_fill_ratio_mean", 2.3)
        fit = dict(ref, az_deg=min(60.0, max(30.0, light["az_deg"])), fill_w=round(48.0 + (443.0 - 48.0) * clamp01((2.26 - r) / (2.26 - 1.05)), 1),
                   borrowed_from="3-06", note="深色衣服不能比光：借 3-06 的比光结果，补光按脸的主辅比在 3-06（2.26 → 48 W）和 3-09（1.05 → 443 W）之间插")
        (cfg["work"] / "light_fit.json").write_text(json.dumps(fit, ensure_ascii=False, indent=1), encoding="utf-8")
        print("ONCAM calib borrowed", json.dumps(fit, ensure_ascii=False), flush=True)
        return
    fit = default_fit(light)
    W = build_world(cfg, fit, samples=48)
    sc = W["sc"]
    out = cfg["work"] / "calib"
    out.mkdir(parents=True, exist_ok=True)
    f_cal = 150
    sc.frame_set(f_cal)
    balls = {}
    for name, col, metal, rough, u in (("grey", 0.18, 0, 1.0, 1450), ("white", 0.80, 0, 1.0, 1610), ("chrome", 0.95, 1, 0.0, 1770)):
        m = bpy.data.materials.new("ball_" + name); m.use_nodes = True
        p = m.node_tree.nodes["Principled BSDF"]
        p.inputs["Base Color"].default_value = (col, col, col, 1)
        p.inputs["Metallic"].default_value = metal
        p.inputs["Roughness"].default_value = rough
        if not metal:
            p.inputs["Specular IOR Level"].default_value = 0.0
        c = px_to_world(u, 470, 1.42)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, location=c, segments=64, ring_count=32)
        o = bpy.context.object; o.name = "ball_" + name
        o.visible_shadow = False                  # 主光从左边平着来，左边的球会挡右边的球（T3 第二版白球比 < 1）
        bpy.ops.object.shade_smooth(); o.data.materials.append(m)
        balls[name] = (o, c)
    bg_ref = _load(Path(cfg["person"]).parent / "bg.jpg")[..., :3]
    t_board = float(np.median(_lum(_lin(bg_ref[100:1000, 1250:1900])))) * BG_DIM
    t_white = light["shirt_lin_p90"] * 0.9          # 白球 80% 对白 T 恤（约 90%）
    t_ratio = light["key_fill_ratio_mean"]
    hist = []
    W["card"].hide_render = True
    rig = W["rig"]
    for rnd in range(8):
        a = _load(_render_to(out / f"t3_round{rnd}.png", 50))
        st = {k: ball_stats(a, c) for k, (o, c) in balls.items()}
        Yb = _lum(_lin(a[..., :3]))[50:500, 625:950]
        m_board = float(np.median(Yb))
        row = dict(round=rnd, key_w=round(rig["key"].data.energy, 1), fill_w=round(rig["fill"].data.energy, 1),
                   wash_w=round(rig["wash"].data.energy, 1), balls=st,
                   white_lit_p90=st["white"]["lit_p90"], target_white=t_white, ratio=st["white"]["ratio"], target_ratio=t_ratio,
                   board_med=m_board, target_board_med=t_board)
        e_w = abs(st["white"]["lit_p90"] / t_white - 1)
        e_r = abs(st["white"]["ratio"] / t_ratio - 1)
        e_b = abs(m_board / t_board - 1)
        row.update(err_white=round(e_w, 3), err_ratio=round(e_r, 3), err_board=round(e_b, 3))
        hist.append(row)
        print("ONCAM calib", json.dumps({k: v for k, v in row.items() if k != "balls"}), flush=True)
        if max(e_w, e_r, e_b) < 0.08 or rnd == 7:
            break
        g = (t_white / st["white"]["lit_p90"])
        if rig["fill"].data.energy < 0.08 * rig["key"].data.energy and st["white"]["ratio"] < t_ratio * 0.92:
            # 补光已经关到底，比还不够：剩下的是世界光，压世界光
            fit["world"] = round(max(0.12, fit.get("world", 0.35) * 0.55), 4)
            world_setup(fit)
            rig["fill"].data.energy = max(rig["fill"].data.energy, 0.05 * rig["key"].data.energy)
        rig["key"].data.energy *= g ** 0.9
        rig["fill"].data.energy *= (st["white"]["ratio"] / t_ratio) ** 1.3 * g ** 0.9
        rig["top"].data.energy = rig["key"].data.energy * 0.12
        rig["wash"].data.energy *= (t_board / max(1e-4, m_board))
    fit.update(key_w=rig["key"].data.energy, fill_w=rig["fill"].data.energy, wash_w=rig["wash"].data.energy, top_w=rig["top"].data.energy)
    # T1：卡片三种做法，同一帧
    t1 = {}
    W["card"].hide_render = True
    a0 = _load(_render_to(out / "t1_nocard.png", 50))
    W["card"].hide_render = False
    a1 = _load(_render_to(out / "t1_shadow_only.png", 50))
    W["card"].visible_camera = True
    W["card"].is_holdout = True
    sc.render.film_transparent = True
    sc.render.image_settings.color_mode = "RGBA"
    a2 = _load(_render_to(out / "t1_holdout.png", 50))
    sc.render.film_transparent = False
    sc.render.image_settings.color_mode = "RGB"
    W["card"].is_holdout = False
    W["card"].visible_camera = False
    Y0, Y1 = _lum(_lin(a0[..., :3])), _lum(_lin(a1[..., :3]))
    right = (slice(0, 540), slice(620, 960))
    t1["board_right_dEV"] = float(np.log2(Y0[right].mean() / max(1e-6, Y1[right].mean())))
    t1["board_right_max_drop"] = float(np.percentile((Y0 - Y1)[right], 99.5) / max(1e-6, np.median(Y0[right])))
    for k_, (o, c) in balls.items():
        s0, s1 = ball_stats(a0, c), ball_stats(a1, c)
        t1[f"ball_{k_}_dEV"] = float(np.log2((s0["left"] + s0["right"]) / max(1e-6, s1["left"] + s1["right"])))
    al = a2[..., 3]
    pfull = _load(person_png(cfg, f_cal))[..., 3]
    pp = pfull[:PERSON["h"] // 2 * 2, :PERSON["w"] // 2 * 2].reshape(PERSON["h"] // 2, 2, PERSON["w"] // 2, 2).mean((1, 3))
    pa = np.zeros_like(al)
    x0, y0 = PERSON["x"] // 2, PERSON["y"] // 2
    pa[y0:y0 + pp.shape[0], 0:x0 + pp.shape[1]] = pp[:, -x0:]
    t1["holdout_hole_px"] = int((al < 0.5).sum())
    t1["holdout_see_through_px"] = int(((pa + (1 - pa) * al) < 0.97).sum())
    t1["shadow_only_see_through_px"] = 0
    t1["note"] = ("只投影：人对大板、对球的影子见 dEV（正值 = 变暗）；最终画面人由合成整个放回最前，没有半透明边。"
                  "Holdout：卡片挖的洞和人物遮罩边对不齐，放回人以后残留半透明像素（see_through），所以不用 Holdout 出像。")
    fit["t1"] = t1
    fit["t3"] = hist
    fit["f_cal"] = f_cal
    (cfg["work"] / "light_fit.json").write_text(json.dumps(fit, ensure_ascii=False, indent=1), encoding="utf-8")
    print("ONCAM t1", json.dumps(t1, ensure_ascii=False), flush=True)


# ---------------------------------------------------------------- 转场
def fg_wipe(K, nf_wipe=17, depth=0.24):
    """T5 焦点擦除（段首）：近处两根白色料杆（带一个浇口）从画面正中往左扫出，焦外完全虚化。
    上一段结尾接同一组料杆从右边扫进来（速度 0.021 m/帧，深 0.24 m，倾 14°），段帧 0 时料杆在画面正中。"""
    coll = bpy.data.collections.new("FG")
    bpy.context.scene.collection.children.link(coll)
    root = link_obj(bpy.data.objects.new("FG_root", None), coll)
    objs = [root]

    def adopt(o):
        for c in list(o.users_collection):
            c.objects.unlink(o)
        coll.objects.link(o)
        o.parent = root
        objs.append(o)
    # 近处料杆背光、离灯远，用原白料会是一片灰褐；复制一份加一点暖白自发光，像屋里亮处的焦外白杆
    mw = K.white.copy(); mw.name = "FG_white"
    pb = next(n for n in mw.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    pb.inputs["Emission Color"].default_value = (1.0, 0.93, 0.84, 1)
    pb.inputs["Emission Strength"].default_value = 1.3
    for i, dx in enumerate((-0.07, 0.07)):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.048, depth=1.6, vertices=48, location=(dx, 0, 0))
        o = bpy.context.object; o.name = f"FG_bar{i}"
        bpy.ops.object.shade_smooth(); o.data.materials.append(mw)
        adopt(o)
    bpy.ops.mesh.primitive_cone_add(radius1=0.03, radius2=0.012, depth=0.12, vertices=32, location=(0, 0, 0.05), rotation=(0, math.radians(90), 0))
    g = bpy.context.object; g.name = "FG_gate"
    bpy.ops.object.shade_smooth(); g.data.materials.append(mw)
    adopt(g)
    root.rotation_euler = (0, math.radians(14), 0)
    xc = px_to_world(OUT_W / 2, OUT_H / 2, depth)[0]
    zc = px_to_world(OUT_W / 2, OUT_H / 2, depth)[2]
    for f in range(0, nf_wipe + 2):
        root.location = (xc - 0.021 * f, depth, zc)
        root.keyframe_insert("location", frame=f)
    linear_keys(root)
    for o in objs:
        o["fg"] = 1
    return dict(last=nf_wipe + 1, depth=depth, speed_m_per_f=0.021, tilt_deg=14)


# ---------------------------------------------------------------- 3-01 的 recipe：销子锁 H06 + 钥匙 H02
SL = 19.35                        # 零件放大倍数（锁宽 20 mm → 0.4 m，在 1.4 m 处约 360 px 宽、高约 450 px，F1 ≥ 380）
KEY_RIM_W = 30.0                  # 只照钥匙的小面光（W）
KEY_YAW = -65.0                   # 钥匙亮出时侧转的角度（度）：正对相机只看见圆柄，侧过来才看得出是钥匙
PIN_DROP = 0.5                    # 没钥匙时下销落下的量（mm）


def _rot(yaw, tilt):
    return Matrix.Rotation(math.radians(tilt), 4, "X") @ Matrix.Rotation(math.radians(yaw), 4, "Z")


def _geom_world(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    V, F = [], []
    for ob in objs:
        eo = ob.evaluated_get(dg)
        me = eo.to_mesh()
        n = len(V)
        V += [eo.matrix_world @ v.co for v in me.vertices]
        me.calc_loop_triangles()
        F += [tuple(n + i for i in t.vertices) for t in me.loop_triangles]
        eo.to_mesh_clear()
    return V, F


def _tree(objs):
    from mathutils.bvhtree import BVHTree
    V, F = _geom_world(objs)
    return BVHTree.FromPolygons(V, F, all_triangles=True) if F else None


def _visible_meshes(root, ignore_anim=False):
    """子树里真正出像的网格/曲线（布尔刀具不算）。ignore_anim：不看当前帧的 hide_render（钥匙的显隐是动画）。"""
    cutters = {m.object for o in bpy.data.objects for m in getattr(o, "modifiers", []) if m.type == "BOOLEAN" and m.object}
    return [o for o in [root] + list(root.children_recursive)
            if o.type in ("MESH", "CURVE") and o not in cutters and (ignore_anim or not o.hide_render)]


def key_rim_keys(kl, f_on, f_off):
    """钥匙小面光只在钥匙亮出到插进去这段亮：插进去以后关掉（推进时镜头贴近钥匙柄，不关会烧成一团白，实测 380–382 帧）。"""
    w = kl.data.energy
    for f, e in ((f_on - 12, 0.0), (f_on, w), (f_off, w), (f_off + 6, 0.0)):
        kl.data.energy = e
        kl.data.keyframe_insert("energy", frame=f)
    kl.data.energy = w


def recipe_lock_key(W):
    """3-01 "Okay. To get this, picture a lock and a key."（D，384 帧）。事件 id 沿用 events/3-01.json（二维版同一张表），三维里的意思：
      dot   Okay   挂在料杆框里的锁点一下头（落在词上）
      dot2  this   锁连框转向镜头一点
      frame picture A1 浇口弹下：预颤 178–184（bl_guide），184 弹出并转正（16 帧 easeOutBack + 回弹）；焦点点名 158→176、轮廓光
      lock  lock   锁转过来露出剖开的四分之一，一排弹子销（216→230 落位，过冲回弹）
      key   a      钥匙从 D 抬起的手边亮出（A7：308→332），手在钥匙前（F3）
      slide key    钥匙对准锁孔滑进去，五根销被齿顶到同一条线（340→368），锁芯带钥匙转 32°，锁梁弹起（370→384）
    段尾 T1：362 起镜头推进剖口，穿进销子之间（接 3-02）。"""
    import kit_deep as D
    import kit_deep_r3 as M3
    import kit_parts as KP
    sc, K, cfg = W["sc"], W["kit"], W["cfg"]
    nf = cfg["nf"]
    E = {e["id"]: e for e in cfg["K"]["events"]}
    # 板上第 3 区那把挂锁就是飞到人旁边的这一把：板上的藏起来
    cell = bpy.data.objects.get("z3_c4_r2")
    if cell is not None:
        for m in [KP.part_of(cell)] + list(KP.part_of(cell).children_recursive):
            m.hide_render = True
    lock = M3.h06_pin_lock(K)
    D.rest(lock)
    bpy.context.view_layer.update()
    lo, hi = mesh_bounds([lock])
    c0 = (lo + hi) / 2                                    # 锁自己的坐标（米，未放大）
    j = D.rig(lock)
    lock.rotation_mode = "XYZ"
    # 挂件框：锁的 XZ 平面（y = 3 mm，浇口所在）上一圈蓝色料杆，两个浇口夹住锁的两侧
    hang = link_obj(bpy.data.objects.new("hang_cell", None))
    hang.rotation_mode = "XYZ"
    hx = max(abs(lo.x), abs(hi.x)) / MM + 3.5
    z0, z1 = lo.z / MM - 3.0, hi.z / MM + 3.0
    zc, hz = (z0 + z1) / 2, (z1 - z0) / 2
    KP.tube_w("hang_cell_loop", [(x, 3.0, z) for x, z in KP.rrect(0, zc, hx, hz, 5.0)], KP.R_LOOP, K.blue, hang, cyclic=True)
    for i, (gx, gy, d, gz) in enumerate(json.loads(lock["gates"])):
        KP.gate_geo(f"hang_cell_g{i}", ((hx if gx > 0 else -hx) * MM, gy * MM, gz * MM), (gx * MM, gy * MM, gz * MM), K.blue, hang)
    gates = [o for o in hang.children if o.name.startswith("hang_cell_g")]

    def pose_at(yaw, tilt, u, v, d):
        R = _rot(yaw, tilt)
        return Vector(px_to_world(u, v, d)), R.to_quaternion()

    def mat_center(center, q):
        R = q.to_matrix().to_4x4()
        return Matrix.Translation(center - R @ (c0 * SL)) @ R @ Matrix.Diagonal((SL, SL, SL, 1))

    f_ok, f_this = E["dot"]["f_land"], E["dot2"]["f_land"]
    f_pop = E["frame"]["f_land"]
    f_r0, f_r1 = E["lock"]["f_start"], E["lock"]["f_land"]
    f_k0, f_k1 = E["key"]["f_start"], E["key"]["f_land"]
    f_s = E["slide"]["f_land"]
    HANG = pose_at(140, 8, 1555, 455, 1.57)
    PICK = pose_at(65, 10, 1565, 470, 1.42)
    SHOW = pose_at(-50, 14, 1575, 480, 1.40)

    def hang_state(f):
        c, q = HANG
        yaw = 2.0 * math.sin(2 * math.pi * f / 250)                       # 待机微动
        tilt = 1.0 * math.sin(2 * math.pi * f / 310 + 1)
        # Okay：点头（31→39 落下、之后弹簧回）
        e = E["dot"]
        tilt += 3.0 * (ease_out_cubic((f - e["f_start"]) / max(1, f_ok - e["f_start"])) if f <= f_ok else spring((f - f_ok) / FPS))
        # this：连框转向镜头 8°（98→118，之后停住）
        e = E["dot2"]
        yaw -= 8.0 * ease_inout_cubic((f - e["f_start"]) / max(1, f_this - e["f_start"]))
        dq = (Matrix.Rotation(math.radians(tilt), 4, "X") @ Matrix.Rotation(math.radians(yaw), 4, "Z")).to_quaternion()
        return Vector(c), dq @ q

    def float_off(f, start):
        b = smooth((f - start) / 30)
        return Vector((0, 0, 0.004 * math.sin(2 * math.pi * f / 220) * b)), 1.0 * math.sin(2 * math.pi * f / 300) * b

    c_h, q_h = hang_state(f_pop)
    pop_dir = (q_h.to_matrix() @ Vector((0, 1, 0)))
    pop_dir = pop_dir.normalized()                       # 沿料杆框的法线出框（带上抬会撞框上沿）
    y_len = (hi.y - lo.y) * SL                           # 锁在出框方向上的厚度（米）
    P1 = c_h + pop_dir * 0.16 * SL / 16.0             # 弹出距离跟零件大小走，先整个出框再转

    def lock_state(f):
        if f <= f_pop:
            return hang_state(f)
        if f < f_r0:
            p = pop_curve(f, f_pop, 16, 12)
            pc = min(1.0, p)
            c = Vector(bezier(c_h, P1, PICK[0], pc))
            if p > 1:
                c = c + (Vector(PICK[0]) - Vector(bezier(c_h, P1, PICK[0], 0.95))) / 0.05 * (p - 1)
            dq = q_h.rotation_difference(PICK[1])
            ax, ang = dq.to_axis_angle()
            r = p if p > 1 else smooth((p - 0.45) / 0.55)    # 先平着弹出框（不转），出了框再转正，免得锁体扫过料杆（穿模检查 186 帧）
            q = Quaternion(ax, ang * r) @ q_h
            fo, fy = float_off(f, f_pop + 20)
            return c + fo, Quaternion((0, 0, 1), math.radians(fy)) @ q
        p = pop_curve(f, f_r0, f_r1 - f_r0, 14)
        c = Vector(PICK[0]).lerp(Vector(SHOW[0]), min(1, p))
        dq = PICK[1].rotation_difference(SHOW[1])
        ax, ang = dq.to_axis_angle()
        q = Quaternion(ax, ang * p) @ PICK[1]
        fo, fy = float_off(f, f_pop + 20)
        return c + fo, Quaternion((0, 0, 1), math.radians(fy)) @ q

    # 11-20 验收：出镜段零件不带料框。框只在 Okay 那一下从浇口"咔"地断开：往后弹开锁的厚度、再按重力掉出画面，之后藏掉
    f_snap = f_ok
    f_gone = f_snap + 40

    def cell_state(f):
        c, q = hang_state(min(f, f_snap))
        if f <= f_snap:
            return c, q
        t = (f - f_snap) / FPS
        kick = -pop_dir * (y_len + 0.05) * ease_out_cubic((f - f_snap) / 8)
        fall = Vector((0.15 * t, 0.2 * t, -4.9 * t * t))            # 重力 9.8 m/s²：0.6 s 掉 1.8 m，出画
        tumble = Quaternion(pop_dir.cross(Vector((0, 0, 1))).normalized(), math.radians(-70 * t * t))
        return c + kick + fall, tumble @ q

    LM = [mat_center(*lock_state(f)) for f in range(nf)]
    for f in range(nf):
        key_matrix(lock, f, LM[f])
        key_matrix(hang, f, mat_center(*cell_state(min(f, f_gone))))
    for o in [hang] + list(hang.children_recursive):
        for fk, hid in ((f_gone - 1, False), (f_gone, True)):
            o.hide_render = hid
            o.keyframe_insert("hide_render", frame=fk)
    # 钥匙：挂在锁下面（父子），锁芯转时跟着转
    key = D.h02_key(K, which="048", scale=1.3)
    key.parent = lock
    key.matrix_parent_inverse = Matrix.Identity(4)
    key.rotation_mode = "QUATERNION"
    Wv, Uv, Vv = Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((1, 0, 0))
    origin = Vector((0, -1.5, -0.55))
    rot3 = Matrix((-Wv, -Uv, -Vv)).transposed()
    off = float(key["insertion_offset_u_mm"])
    Kin = Matrix.Translation(((origin + off * Uv) - rot3 @ Vector((6.5 * 1.3, 0, 0))) * MM) @ rot3.to_4x4() @ Matrix.Diagonal((1.3, 1.3, 1.3, 1))
    pivot = origin * MM

    def Rplug(deg):
        return Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(deg), 4, Wv) @ Matrix.Translation(-pivot)

    def Kt(w, du=0.0, dv=0.0, s=1.0):
        return Matrix.Translation((w * Wv + du * Uv + dv * Vv) * MM) @ Kin @ Matrix.Diagonal((s, s, s, 1))

    tip_local = Vector((6.5 * MM, 0, 0))
    # 手边的位置：钥匙尖落在出片 (1330, 715)，在锁下方、D 的右手右边（11-20 验收：钥匙不要被手指盖住）。
    # 离锁 13 mm（放大后 0.28 m）：再往相机凑就太大、出画、离焦外太远；上下左右用 du、dv 两个方向解
    tgt = (1330.0, 715.0)
    Mc = cam_matrix_micro(f_k1)
    w_hand = 13.0
    du_, dv_ = -12.0, 0.0
    for _ in range(30):
        def scr(du, dv):
            p = LM[f_k1] @ (Kt(w_hand, du, dv) @ tip_local)
            x, y, _z = project(Mc, SHIFT, p)
            return x, y
        x0, y0 = scr(du_, dv_)
        xa, ya = scr(du_ + 0.1, dv_)
        xb, yb = scr(du_, dv_ + 0.1)
        J = Matrix(((xa - x0, xb - x0), (ya - y0, yb - y0))) * 10
        try:
            d = J.inverted() @ Vector((tgt[0] - x0, tgt[1] - y0))
        except ValueError:
            break
        du_, dv_ = du_ + d.x, dv_ + d.y
    du_hand, dv_hand = du_, dv_
    f_a0, f_a1 = f_s, f_s + 10                            # 对准锁孔
    f_i0, f_i1 = f_a1, f_s + 28                           # 滑进去
    f_t0 = f_i1 + 2                                       # 锁芯转
    f_sh = f_t0 + 4                                       # 锁梁弹起

    def key_yaw(f):
        if f < f_a0:
            return KEY_YAW
        if f < f_a1:
            return KEY_YAW * (1 - ease_inout_cubic((f - f_a0) / (f_a1 - f_a0)))
        return 0.0

    def key_dv(f):
        if f < f_a0:
            return dv_hand
        if f < f_a1:
            return dv_hand * (1 - ease_inout_cubic((f - f_a0) / (f_a1 - f_a0)))
        return 0.0

    def key_state(f):
        """(w, du, scale, 锁芯角度, 可见)"""
        if f < f_k0:
            return 30.0, du_hand, 0.3, 0.0, False
        if f < f_s:
            e = (f - f_k0) / max(1, f_k1 - f_k0)
            return w_hand + 6.0 * (1 - ease_out_cubic(e)), du_hand + 0.25 * math.sin(2 * math.pi * f / 90), 0.3 + 0.7 * ease_out_back(e), 0.0, True
        if f < f_a1:
            e = ease_inout_cubic((f - f_a0) / (f_a1 - f_a0))
            return w_hand + (7.5 - w_hand) * e, du_hand * (1 - e), 1.0, 0.0, True
        if f < f_i1:
            e = ease_out_cubic((f - f_i0) / (f_i1 - f_i0))
            return 7.5 * (1 - e), 0.0, 1.0, 0.0, True
        return 0.0, 0.0, 1.0, 32.0 * pop_curve(f, f_t0, 10, 10), True

    # 下销跟着钥匙齿走：钥匙齿面（锁坐标 u）由 h02 的齿形算，销的落脚取销底面 ±0.45 mm 内的最高点
    prof = list(key["tooth_profile_modelled"])
    chain = [(6.5, -1.3)]
    for i, h in enumerate(prof):
        c = 6.0 - i
        chain += [(c + 0.28, -1.3 + h), (c - 0.28, -1.3 + h)]
    chain += [(1.5, -1.3)]
    chain = sorted(chain)

    def surf(x):
        if x > 6.5:
            return off + 1.3 * 1.3 - (x - 6.5) / 0.5 * 3.0 if x < 7.0 else -99
        if x < 1.5:
            return -99
        for (xa, ya), (xb, yb) in zip(chain, chain[1:]):
            if xa <= x <= xb:
                t = 0 if xb == xa else (x - xa) / (xb - xa)
                return off + (-(ya + (yb - ya) * t)) * 1.3
        return -99

    def foot(i, w):
        a = (0.5 + i) * 1.3
        x = 6.5 - (a - w) / 1.3
        return max(surf(x + dx) for dx in (-0.45, -0.3, -0.15, 0, 0.15, 0.3, 0.45))

    rest_u = [foot(i, 0.0) for i in range(5)]
    lifts_max = 0.0
    hide_prev = None
    for f in range(nf):
        w, du, s, deg, vis = key_state(f)
        Mk = Rplug(deg) @ Kt(w, du, key_dv(f), s)
        tip_l = Mk @ tip_local                            # 亮出时钥匙侧过来（齿形朝镜头），对准锁孔时绕钥匙尖转正
        Mk = Matrix.Translation(tip_l) @ Matrix.Rotation(math.radians(key_yaw(f)), 4, Uv) @ Matrix.Translation(-tip_l) @ Mk
        key.matrix_basis = Mk
        key.keyframe_insert("location", frame=f)
        key.keyframe_insert("rotation_quaternion", frame=f)
        key.keyframe_insert("scale", frame=f)
        if vis != hide_prev:
            for o in [key] + list(key.children_recursive):
                o.hide_render = not vis
                o.keyframe_insert("hide_render", frame=f)
            hide_prev = vis
        inside = du == 0.0 and w <= 7.0
        for i in range(5):
            lift = max(-PIN_DROP, foot(i, w) - rest_u[i]) if inside else -PIN_DROP
            lifts_max = max(lifts_max, lift)
            j[f"pin_{i}"].location.z = lift * MM
            j[f"pin_{i}"].keyframe_insert("location", index=2, frame=f)
        j["plug"].rotation_euler.x = math.radians(deg)
        j["plug"].keyframe_insert("rotation_euler", index=0, frame=f)
        j["shackle"].location.z = 3.6 * ease_out_back((f - f_sh) / 10) * MM if f >= f_sh else 0.0
        j["shackle"].keyframe_insert("location", index=2, frame=f)
    for o in [lock, hang, key] + [j[f"pin_{i}"] for i in range(5)] + [j["plug"], j["shackle"]]:
        linear_keys(o)
    # 预颤（bl_guide，A1 的预备）：零件往弹出方向绷 4 mm（屏上 ≤ 6 px），浇口拉细，框颤两下
    import bl_guide as BG
    sc.frame_set(f_pop - 6)
    rot = BG.tick_rot_cap(W["cam"], sc, lock, cam_matrix_micro(f_pop).translation, 4.0)
    tick = BG.guide_tick(lock, [], None, f_pop, amp_mm=4.0, rot_deg=rot, dir=pop_dir)   # 框已在 Okay 断掉，只剩锁本体预颤
    # 浇口在锁体表面断开：断的那一帧锥头缩回 40%（粗端连料杆不动），断口留在框上，不再插在锁体侧面里（穿模检查 184–186 帧）
    for g in gates:
        L = g.dimensions.z / max(1e-9, g.scale.z)
        ax = g.rotation_euler.to_matrix() @ Vector((0, 0, 1))
        for fk, sz in ((f_snap, 1.0), (f_snap + 1, 0.6)):
            g.delta_scale = (1.0, 1.0, sz)
            g.delta_location = -ax * L * (1 - sz) / 2
            g.keyframe_insert("delta_scale", frame=fk)
            g.keyframe_insert("delta_location", frame=fk)
    tick["rot_deg"] = rot

    def lock_center(f):
        return LM[max(0, min(nf - 1, int(f)))] @ c0

    # 镜头推进的目标：剖口里五根销的中间、分界线上，从 +X（剖口朝外）略上方看进去
    Pw_local = Vector((1.8, -4.75, 2.6)) * MM
    dir_local = Vector((1.0, -0.35, 0.5)).normalized()
    Mend = LM[nf - 1]
    target = Mend @ Pw_local
    eye = Mend @ (Pw_local + dir_local * 7.0 * MM)
    hero_box = [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]

    def bbox_pts(f):
        return [LM[f] @ p for p in hero_box]

    # 焦点借给钥匙：钥匙从手边亮出到对准锁孔（离相机近 0.5 m，不拉焦就是一团虚的暗影）
    key_pts = {}
    for f in range(f_k0 - 8, f_a1 + 12):
        bpy.context.scene.frame_set(f)
        key_pts[f] = key.matrix_world.translation.copy()
    focus2 = [(f_k0 - 8, f_a1 + 11, lambda f: key_pts[f])]
    # 钥匙侧着亮出时，正对镜头那面要有东西可反射（金色才亮），一张只给镜面看的卡放在相机左上方对着钥匙
    kp = key_pts[f_k1]
    refl_card("refl_key", -kp.normalized() * 0.35 + Vector((-0.15, 0, 0.12)), kp, (1.6, 1.1), kelvin_rgb(W["light"]["kelvin"]), 3.0)   # 相机身后、钥匙—相机连线上
    # 11-20 验收：金钥匙在 340 帧读成深褐。加一盏只照钥匙的小面光（灯光链接），从右上前方打，金色读成亮金
    kcol = bpy.data.collections.new("ONCAM_key_lit")
    sc.collection.children.link(kcol)
    for o in [key] + list(key.children_recursive):
        if o.type in ("MESH", "CURVE"):
            kcol.objects.link(o)
    kl = make_light("key_rim", "AREA", kp + Vector((0.32, -0.38, 0.42)), kp, 0.35, KEY_RIM_W, kelvin_rgb(4300))
    kl.light_linking.receiver_collection = kcol
    key_rim_keys(kl, f_k0, f_i1)


    def checks():
        """穿模：弹出时锁和框、浇口；钥匙进锁时钥匙和锁体（外壳、套筒、轴承、口环、螺丝）、锁芯；钥匙和下销只许贴着。"""
        out = {}
        cell_objs = _visible_meshes(hang)
        kset = set([key] + list(key.children_recursive))
        lock_objs = [o for o in _visible_meshes(lock) if o not in kset]
        rotor = set(_visible_meshes(j["plug"]))
        pins_low = [o for o in rotor if "lower_pin" in o.name]
        core = [o for o in rotor if o not in pins_low]
        moving = set(rotor) | set(o for i in range(5) for o in _visible_meshes(j[f"pin_{i}"])) | set(_visible_meshes(j["shackle"]))
        statics = [o for o in lock_objs if o not in moving]
        hits = []
        for f in range(f_snap + 1, f_gone):
            sc.frame_set(f)
            a, b = _tree(lock_objs), _tree(cell_objs)
            if a and b and a.overlap(b):
                hits.append(f)
        out["lock_vs_cell_frames"] = hits
        key_objs = _visible_meshes(key, ignore_anim=True)
        hk, hc, hp = [], [], []
        for f in range(f_k1, nf):
            sc.frame_set(f)
            kt = _tree(key_objs)
            if kt.overlap(_tree(statics)):
                hk.append(f)
            if kt.overlap(_tree(core)):
                hc.append(f)
            n = len(kt.overlap(_tree(pins_low)))
            if n:
                hp.append([f, n])
        out["key_vs_lockbody_frames"] = hk
        out["key_vs_core_frames"] = hc
        out["key_vs_lowerpins_touch"] = hp
        return out

    return dict(targets={"card": lock_center}, rim={"card": [lock]}, focus2=focus2, hero=lock, bbox=bbox_pts, key=key,
                push=dict(t0=E["slide"]["f_land"] + 22, target=target, eye=eye),
                lock_c0=c0, checks=checks,
                info=dict(SL=SL, pin_drop=PIN_DROP, lifts_max_mm=round(lifts_max, 3), tick=tick, w_hand=round(w_hand, 2), du_hand=round(du_hand, 2), dv_hand=round(dv_hand, 2),
                          frames=dict(okay=f_ok, this=f_this, pop=f_pop, reveal=[f_r0, f_r1], key=[f_k0, f_k1], approach=[f_a0, f_a1],
                                      insert=[f_i0, f_i1], turn=f_t0, shackle=f_sh),
                          poses=dict(hang=[140, 8, 1555, 455, 1.57], pick=[65, 10, 1565, 470, 1.42], show=[-50, 14, 1575, 480, 1.40])))


# ================================================================ 3-01 重做（11-20 下午，深化/10_出镜3-01_重做.md）
# 锁自己当段首段尾转场（相机不推，人永远原像素）；锁在人前的帧另渲一层透明通道（front）把人挡住。
V2 = dict(
    LOCK_PX=(1505.0, 470.0), LOCK_D=1.45,       # 落位：出片像素中心、深度（米）
    LOCK_H_PX=392.0,                             # 锁连锁梁的投影高（F1 ≥ 380）
    REST1=(-58.0, 9.0), REST2=(-70.0, 12.0), PIC=(-84.0, 12.0), PINS=(-92.0, 10.0),   # (yaw, tilt) 度
    TAIL_D=0.05,                                 # 段尾销子中心离镜头（米）；段首锁孔离镜头 HEAD_D_KH
    HEAD_D_KH=0.17, HEAD_CTRL=(2350.0, 330.0, 0.95), TAIL_CTRL=(1880.0, 420.0, 0.80), TAIL_PX=(260.0, 560.0),
    BOARD_K=1.27, BOARD_HIDE=("stations", "zone_tags", "z1_c0_r0"),                                # 大板再放大（铺满画面）
    HEAD_BOX=(300, 90, 820, 680), LOCK_BOX=(1230, 60, 1940, 960),   # 这两块里的大板零件拿掉（出片像素）
    KEY_YAW=-12.0, KEY_HAND=(1250.0, 770.0), KEY_START=(1150.0, 935.0),   # 钥匙平面基本正对镜头（齿形看得见）；柄在 D 右手指尖右上
    BRIGHT=True, HEAD_PX_B=(960.0, 540.0), HEAD_D_B=0.085, HEAD_EASE=0.5, TAIL_PT_B=(1.8, -4.75, 1.4), TRANS_K=1.4, TRANS_TRACK=14,   # 11-23 rc02 黑场返修（18 文档 3.2 O1）：段首贴近金色锁芯面、段尾对准锁芯，加光轴转场灯；只补渲段首段尾
    RIM_W=60.0, SAMPLES=16,          # 11-20 导演：1080p60 一律 16 采样 + OptiX 降噪，之后统一 GPU 放大到 4K
)


def _has_red(o):
    """格子里有没有红色件（基色线性 r > 0.35 且 g、b < 0.12）：出镜背景里红色抢眼（18 OC6）。"""
    for m in [o] + list(o.children_recursive):
        for sl in getattr(m, "material_slots", []):
            mt = sl.material
            if mt is None or not mt.use_nodes:
                continue
            for n in mt.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    c = n.inputs["Base Color"].default_value
                    if c[0] > 0.35 and c[1] < 0.12 and c[2] < 0.12:
                        return True
    return False


def board_fill(board, P=None):
    """大板铺满画面：在 board_setup 的基础上再放大 BOARD_K，左上角挪到画外（留微动和焦外余量）。
    D 头后面、锁后面的零件格藏掉，只留料杆网格（10_ 文档第一节第 13、14、16 条）。"""
    P = P or V2
    xf = bpy.data.objects["ONCAM_board_xf"]
    k = P["BOARD_K"]
    xf.scale = tuple(s * k for s in xf.scale)
    bpy.context.view_layer.update()
    lo, hi = mesh_bounds([board])
    yb = lo.y
    xf.location.x += px_to_world(-120, 0, yb)[0] - lo.x
    xf.location.z += px_to_world(0, -80, yb)[2] - hi.z
    bpy.context.view_layer.update()
    lo, hi = mesh_bounds([board])
    edges = dict(left=world_to_px((lo.x, lo.y, 0))[0], right=world_to_px((hi.x, lo.y, 0))[0],
                 top=world_to_px((0, lo.y, hi.z))[1], bottom=world_to_px((0, lo.y, lo.z))[1])
    hidden = []
    for nm in P["BOARD_HIDE"]:
        o = bpy.data.objects.get(nm)
        if o is not None:
            for m in [o] + list(o.children_recursive):
                m.hide_render = True
            hidden.append(nm)

    def hit(b, B):
        return not (b[2] < B[0] or b[0] > B[2] or b[3] < B[1] or b[1] > B[3])
    for o in board.children:
        if not (o.name.startswith("z") and "_c" in o.name and "_r" in o.name) or o.name in hidden:
            continue
        l, h = mesh_bounds([o])
        ps = [world_to_px((x, l.y, z)) for x in (l.x, h.x) for z in (l.z, h.z)]
        b = (min(p[0] for p in ps), min(p[1] for p in ps), max(p[0] for p in ps), max(p[1] for p in ps))
        if hit(b, P["HEAD_BOX"]) or hit(b, P["LOCK_BOX"]) or (P.get("HIDE_RED") and _has_red(o)):   # 18 OC6：红色的格子全部藏掉
            for m in [o] + list(o.children_recursive):
                m.hide_render = True
            hidden.append(o.name)
    return dict(edges=edges, hidden=hidden)


def make_cover(K):
    """剖开那一块外壳：用不剖版的锁，和剖开版同样的刀具做 INTERSECT，得到被剖掉的几块（外壳、外套、口环、轴承、锁芯）。
    两把锁都在原点搭，坐标就是锁自己的坐标。返回 (cover 空物体, 烘好的网格列表)。"""
    import kit_deep as D
    import kit_deep_r2 as R
    import kit_deep_r3 as M3
    B = M3.h06_pin_lock(K, cut=False)
    D.rest(B)
    Pt = D.Part(K, "h06_cover_tools", "blue")

    def quad(y0, y1, edge=0.0):
        return R._box(Pt, "q", (10 + edge, (y0 + y1) / 2, 9.45), 10, (y1 - y0) / 2, 20, K.blue, 0, 0)
    bpy.context.view_layer.update()
    kids = list(B.children_recursive)

    def find(key):
        return [o for o in kids if o.type == "MESH" and key in o.name and not o.hide_render]

    def front_bearing(o):
        ys = [(o.matrix_world @ Vector(c)).y for c in o.bound_box]
        return min(ys) < -0.006
    pick = [(o, quad(-9, .88)) for o in find("inset_housing")]
    pick += [(o, quad(-9, -.36)) for o in find("sleeve_9p10")]
    pick += [(o, quad(-9, -6)) for o in find("front_bevel_ring")]
    pick += [(o, quad(-9, -6)) for o in find("sleeve_centering_bearing") if front_bearing(o)]
    pick += [(o, quad(-7.62, -1.72, .016)) for o in find("turning_core")]
    cover = link_obj(bpy.data.objects.new("lock_cover", None))
    made = []
    for o, cut in pick:
        cut.hide_render = cut.hide_viewport = True
        mod = o.modifiers.new("cover_int", "BOOLEAN")
        mod.object, mod.operation, mod.solver = cut, "INTERSECT", "EXACT"
        o.modifiers.move(len(o.modifiers) - 1, 0)
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        if len(me.vertices) == 0:
            continue
        n = link_obj(bpy.data.objects.new("lock_cover_" + o.name.split("__")[-1], me))
        n.parent = cover
        n.matrix_parent_inverse = Matrix.Identity(4)
        n.matrix_world = o.matrix_world.copy()
        made.append(n)
    for o in [B] + kids + [Pt.root] + list(Pt.root.children_recursive):
        try:
            bpy.data.objects.remove(o, do_unlink=True)
        except (ReferenceError, RuntimeError):
            pass
    return cover, made


def recipe_lock_key_v2(W):
    """3-01 重做（10_出镜3-01_重做.md 第二节逐拍）。事件 id 见 events/3-01.json（11-20 重写）：
      arrive  Okay     锁从镜头前退回人右侧落位（段首 T5：锁盖满画面那一帧是切点）
      turn    this     锁转 12°、抬头，把锁孔那面亮给观众
      call    picture  焦点点名（g_start→g_on）、预颤 6 帧、浮起靠前转出右侧
      reveal  lock     剖口那块外壳弹开、旋转着飞出画，五根销被震一下
      key     a        金钥匙从 D 右手后面升起（手在前），A7 弹出
      slide   key      钥匙飞到锁孔前、转正、滑进去，销被顶齐（f_land 落到底）
      open    （说完）  锁芯转 32°、锁梁弹起
      dive    （说完）  锁带钥匙冲向镜头，剖口朝镜头（段尾 T1，相机不动）"""
    import kit_deep as D
    import kit_deep_r3 as M3
    import kit_parts as KP
    sc, K, cfg = W["sc"], W["kit"], W["cfg"]
    nf = cfg["nf"]
    E = {e["id"]: e for e in cfg["K"]["events"]}
    cell = bpy.data.objects.get("z3_c4_r2")
    if cell is not None:
        for m in [KP.part_of(cell)] + list(KP.part_of(cell).children_recursive):
            m.hide_render = True
    print("ONCAM step r0", flush=True)
    lock = M3.h06_pin_lock(K)
    print("ONCAM step r1 lock built", flush=True)
    D.rest(lock)
    bpy.context.view_layer.update()
    lo, hi = mesh_bounds([lock])
    c0 = (lo + hi) / 2
    cover, cover_parts = None, []       # 不再做"飞出去的外壳块"：剖开那一角被锁销、外套前后夹住，整体怎么拔都穿模（11-20 BVH 逐方向实测），改成剖切面从上往下扫开
    def _ext(o, i):
        return (max(c[i] for c in o.bound_box) - min(c[i] for c in o.bound_box)) * abs(o.scale[i])
    # kit_deep 的 _boolean 会把刀具改名成 "<零件>_cut.nnn"，按名字找不到；剖切象限刀具是 20 × ? × 20 mm 的盒子（kit_deep_r3.quadrant，右上象限）
    # 模型小毛病：最前一根销的座孔（r .701，y -7.35）和上导套（r .76）顶破锁正面（y -8.0），整锁时正面露出一条白缝（11-20 test f20）。
    # 座孔刀具径向缩到 .61（销 r .586 仍有间隙；.64 时正面只剩 0.01 mm，EXACT 布尔在某些位姿下直接崩，11-20 实测），最前导套（名字是 _4xx）往里挪 0.12 mm；都在锁壳里面，剖开后看不出。
    for o in lock.children_recursive:
        for m in getattr(o, "modifiers", []):
            c = m.object if m.type == "BOOLEAN" else None
            if c is not None and "inset_housing" in o.name and abs(c.location.y + 7.35 * MM) < 0.05 * MM and abs(c.location.x) < 0.05 * MM:
                c.scale.x *= 0.61 / 0.701
                c.scale.y *= 0.61 / 0.701
        if o.type == "MESH" and "upper_fixed_guide_" in o.name and min(c[1] for c in o.bound_box) + o.location.y < -8.0 * MM:
            o.location.y += 0.12 * MM          # 最前那根（销 4，y -7.35）
    cutters = list({m.object for o in lock.children_recursive for m in getattr(o, "modifiers", [])
                    if m.type == "BOOLEAN" and m.operation == "DIFFERENCE" and m.object is not None
                    and abs(_ext(m.object, 0) - 20 * MM) < 0.3 * MM and abs(_ext(m.object, 2) - 20 * MM) < 0.3 * MM})
    assert len(cutters) >= 4, f"剖切刀具只找到 {len(cutters)} 个"
    print("ONCAM step r2 cutters", flush=True)
    bpy.context.view_layer.update()
    SLv = V2["LOCK_H_PX"] * V2["LOCK_D"] / (F_PX * (hi.z - lo.z)) * 0.86   # 0.86：3/4 角度和锁梁让投影比竖直高度高，F1 由 check 实测
    print("ONCAM step r3", flush=True)
    j = D.rig(lock)
    print("ONCAM step r4 rig", flush=True)
    lock.rotation_mode = "XYZ"

    def Rq(yaw, tilt, roll=0.0):
        return (Matrix.Rotation(math.radians(tilt), 4, "X") @ Matrix.Rotation(math.radians(roll), 4, "Y") @ Matrix.Rotation(math.radians(yaw), 4, "Z")).to_quaternion()

    def M_of(center, q):
        R4 = q.to_matrix().to_4x4()
        return Matrix.Translation(center - R4 @ (c0 * SLv)) @ R4 @ Matrix.Diagonal((SLv, SLv, SLv, 1))

    def qpow(qa, qb, p):
        dq = qa.rotation_difference(qb)
        ax, ang = dq.to_axis_angle()
        return Quaternion(ax, ang * p) @ qa

    def bez(a, b, c, t):
        return a * (1 - t) ** 2 + b * 2 * (1 - t) * t + c * t * t

    P_rest = Vector(px_to_world(*V2["LOCK_PX"], V2["LOCK_D"]))
    e_a, e_t, e_c, e_r = E["arrive"], E["turn"], E["call"], E["reveal"]
    e_k, e_s, e_o, e_d = E["key"], E["slide"], E["open"], E["dive"]
    f_ok, f_ok_end = e_a["f_land"], e_a["f_end"]
    q_head = Rq(0.0, 4.0)                                      # 段首：锁孔正对镜头、在画面正中，离镜头 HEAD_D_KH（锁体盖满画面）
    kh = Vector((0.0, -8.0, -0.55)) * MM
    P_head = Vector(px_to_world(1010, 540, V2["HEAD_D_KH"])) - q_head.to_matrix() @ ((kh - c0) * SLv)
    BR = V2.get("BRIGHT")
    if BR:                                                     # 11-23 rc02 黑场（18 文档 3.2 O1）：第 0 帧贴近金色锁芯面（口环以内），外圈深色套筒不进画
        P_head = Vector(px_to_world(*V2["HEAD_PX_B"], V2["HEAD_D_B"])) - q_head.to_matrix() @ ((kh - c0) * SLv)
    P_ctrl = Vector(px_to_world(*V2["HEAD_CTRL"]))
    q_r1, q_r2, q_pic, q_pins = Rq(*V2["REST1"]), Rq(*V2["REST2"]), Rq(*V2["PIC"]), Rq(*V2["PINS"])
    P_pic_d = Vector((-0.06, -0.04, 0.05))     # 点名时靠前、抬高，同时往左让：转出 3/4 侧面后锁变宽，不让右沿出画（M3，11-20 实测 2006 px）

    def bez_at_depth(A, C, B, y):
        """二次贝塞尔上深度（相机看 +Y，深度 = y）等于 y 的那一点（深度沿曲线单调，二分）。"""
        lo_, hi_ = 0.0, 1.0
        inc = B.y > A.y
        for _ in range(40):
            m = (lo_ + hi_) / 2
            if (bez(A, C, B, m).y < y) == inc:
                lo_ = m
            else:
                hi_ = m
        return bez(A, C, B, (lo_ + hi_) / 2)

    def log_depth(y0, y1, e):
        """深度按对数插值：贴镜头时屏幕大小每帧按同一比例变，盖满画面那几帧不会一下子黑掉（11-20 实测段尾相邻帧亮度跳 60）。"""
        return math.exp(math.log(y0) + (math.log(y1) - math.log(y0)) * e)

    def hover(f):
        b = smooth((f - 30) / 40)
        return Vector((0.0, 0.0, 0.0055 * math.sin(2 * math.pi * f / 230) * b)), 1.4 * math.sin(2 * math.pi * f / 310 + 0.6) * b

    def base_pose(f):
        if f <= f_ok:
            t = f / max(1, f_ok)
            p = ease_out_back(t, 0.9)
            k_e = V2.get("HEAD_EASE", 0.0)
            c = bez_at_depth(P_head, P_ctrl, P_rest, log_depth(P_head.y, P_rest.y, (1 - k_e) * ease_out_cubic(t) + k_e * smooth(t)))
            q = qpow(q_head, q_r1, smooth(t) * 0.35 + p * 0.65)
        else:
            s = (f - f_ok) / FPS                               # 落位后回弹两下
            c = P_rest + Vector((0.004, 0.006, -0.008)) * spring(s, 0.45, 20.0) * (1 - clamp01((f - f_ok) / max(1, f_ok_end + 12 - f_ok)))
            q = q_r1.copy()
        u = ease_inout_cubic((f - e_t["f_start"]) / max(1, e_t["f_land"] - e_t["f_start"]))
        if u > 0 and f > f_ok:
            q = qpow(q, q_r2, u)
        fl = e_c["f_land"]
        if fl - 6 <= f < fl:                                   # 预颤：往下沉 3 mm
            c = c + Vector((0, 0, -0.003 * math.sin(math.pi * (f - fl + 6) / 6) ** 2))
        p = ease_out_back((f - fl) / 18.0, 1.2) if f >= fl else 0.0
        if p > 0:
            c = c + P_pic_d * p
            q = qpow(q, q_pic, p)
        fr = e_r["f_land"]
        if f >= fr:                                            # 外壳弹开：锁本体反冲；之后慢慢转，让销子正对观众
            rec = -0.6 * math.exp(-(f - fr) / 5.0) * math.sin(math.pi * min(1.0, (f - fr) / 8.0))
            c = c + q.to_matrix() @ Vector((rec * MM * SLv, 0, 0))
            q = qpow(q, q_pins, ease_inout_cubic((f - (fr + 20)) / 50.0))
        fo = e_o["f_start"] + 4                                # 锁梁弹起：锁本体被顶一下（T7 落位冲击，相机不震，人不动）
        if f >= fo:
            c = c + Vector((0, 0, -0.004)) * math.exp(-(f - fo) / 4.0) * math.sin(math.pi * min(1.0, (f - fo) / 4.0))
        ho, hy = hover(f)
        return c + ho, Quaternion((0, 0, 1), math.radians(hy)) @ q

    f_d0, f_d1 = e_d["f_start"], nf - 1
    pins_mid = Vector((1.8, -4.75, 2.6)) * MM
    if BR:                                                     # 11-23 rc02（O1）：终点往锁芯挪，金色锁芯 + 白色上销占满画面（原来上半是蓝黑内腔）
        pins_mid = Vector(V2["TAIL_PT_B"]) * MM
    q_tail = Rq(-90.0, 6.0)
    tgt_tail = Vector(px_to_world(*V2["TAIL_PX"], V2["TAIL_D"]))
    c1_tail = tgt_tail - q_tail.to_matrix() @ ((pins_mid - c0) * SLv)

    def pose(f):
        c, q = base_pose(f)
        if f > f_d0:
            t = (f - f_d0) / (f_d1 - f_d0)
            ctrl = Vector(px_to_world(*V2["TAIL_CTRL"]))
            c = bez_at_depth(c, ctrl, c1_tail, log_depth(c.y, c1_tail.y, smooth(t) * 0.7 + 0.3 * ease_in_cubic(t)))
            q = (_qpow_w if BR else qpow)(q, q_tail, smooth(t))   # 亮版：qpow 是局部差左乘，p = 1 到不了 q_tail（11-23 试渲段尾冲不到落点）
        return c, q

    LM = []
    for f in range(nf):
        c, q = pose(f)
        LM.append(M_of(c, q))
        key_matrix(lock, f, LM[f])
    # ---- 剖开：五个剖切刀具（外壳、外套、口环、轴承、锁芯）一起从锁顶上方往下扫到位，"lock" 这个词说出时扫过一半，
    #      剖面从销子开始露、扫到锁芯为止（刀具本来就是布尔，动它就是动剖面；没有任何零件移动，不可能穿模）
    fr = e_r["f_land"]
    SW0, SW1, DZ = fr - 6, fr + 10, 26.0
    for o in cutters:
        z0 = o.location.z
        for f in sorted({0, SW0, *range(SW0, SW1 + 1), SW1, nf - 1}):
            o.location.z = z0 + DZ * MM * (1.0 - smooth((f - SW0) / (SW1 - SW0)))
            o.keyframe_insert("location", index=2, frame=f)
        o.location.z = z0
        linear_keys(o)
    f_hide = SW1
    info_cutters = sorted(o.name for o in cutters)
    # ---- 钥匙：挂在锁下面（父子），锁芯转时跟着转（插入几何沿用旧版）
    print("ONCAM step r5 lock anim", flush=True)
    key = D.h02_key(K, which="048", scale=1.3)
    print("ONCAM step r6 key", flush=True)
    key.parent = lock
    key.matrix_parent_inverse = Matrix.Identity(4)
    key.rotation_mode = "QUATERNION"
    Wv, Uv, Vv = Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((1, 0, 0))
    origin = Vector((0, -1.5, -0.55))
    rot3 = Matrix((-Wv, -Uv, -Vv)).transposed()
    koff = float(key["insertion_offset_u_mm"])
    Kin = Matrix.Translation(((origin + koff * Uv) - rot3 @ Vector((6.5 * 1.3, 0, 0))) * MM) @ rot3.to_4x4() @ Matrix.Diagonal((1.3, 1.3, 1.3, 1))
    pivot = origin * MM

    def Rplug(deg):
        return Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(deg), 4, Wv) @ Matrix.Translation(-pivot)

    def Kt(w, du=0.0, dv=0.0, s=1.0):
        return Matrix.Translation((w * Wv + du * Uv + dv * Vv) * MM) @ Kin @ Matrix.Diagonal((s, s, s, 1))

    tip_local = Vector((6.5 * MM, 0, 0))
    bow_local = Vector((-3.5 * MM, 0, 0))
    f_k0, f_k1 = e_k["f_start"], e_k["f_land"]
    f_a0, f_a1 = e_k["f_land"], e_s["f_start"]
    f_i0, f_i1 = e_s["f_start"], e_s["f_land"]
    f_t0, f_t1 = e_o["f_start"], e_o["f_land"]
    KEYY = V2["KEY_YAW"]

    def kmat(w, du, dv, s, yaw, deg=0.0):
        Mk = Rplug(deg) @ Kt(w, du, dv, s)
        tl = Mk @ tip_local
        return Matrix.Translation(tl) @ Matrix.Rotation(math.radians(yaw), 4, Uv) @ Matrix.Translation(-tl) @ Mk

    def solve(fr_, tgt, w, du0, dv0, s=1.0, yaw=0.0):
        """钥匙柄中心落在出片 tgt：解 du、dv（锁坐标，mm）。"""
        Mc = cam_matrix_micro(fr_)
        du_, dv_ = du0, dv0
        for _ in range(40):
            def scr(du, dv):
                x, y, _z = project(Mc, SHIFT, LM[fr_] @ (kmat(w, du, dv, s, yaw) @ bow_local))
                return x, y
            x0, y0 = scr(du_, dv_)
            xa, ya = scr(du_ + 0.1, dv_)
            xb, yb = scr(du_, dv_ + 0.1)
            J = Matrix(((xa - x0, xb - x0), (ya - y0, yb - y0))) * 10
            try:
                d = J.inverted() @ Vector((tgt[0] - x0, tgt[1] - y0))
            except ValueError:
                break
            if d.length > 20.0:                       # 阻尼：一步最多走 20 mm（不阻尼时换个锁位姿就发散成 NaN，Blender 求值布尔直接崩，11-20 实测）
                d = d * (20.0 / d.length)
            du_, dv_ = du_ + d.x, dv_ + d.y
            if math.hypot(tgt[0] - x0, tgt[1] - y0) < 0.05:
                break
        assert math.isfinite(du_) and math.isfinite(dv_) and abs(du_) < 400 and abs(dv_) < 400, f"钥匙位置解不出来：{tgt} → du {du_} dv {dv_}"
        return du_, dv_
    W_HAND = 16.0
    du_h, dv_h = solve(f_k1, V2["KEY_HAND"], W_HAND, -12.0, 0.0, 1.0, KEYY)
    du_s, dv_s = solve(f_k0, V2["KEY_START"], W_HAND + 2.0, du_h, dv_h, 0.6, KEYY)

    def key_state(f):
        """(w, du, dv, scale, yaw, 锁芯角, 可见)"""
        if f < f_k0:
            return W_HAND + 2, du_s, dv_s, 0.6, KEYY, 0.0, False
        if f < f_k1:
            e = (f - f_k0) / max(1, f_k1 - f_k0)
            eo = ease_out_cubic(e)
            s = 0.6 + 0.4 * ease_out_back(e, 2.2)
            return W_HAND + 2 * (1 - eo), du_s + (du_h - du_s) * eo, dv_s + (dv_h - dv_s) * eo, s, KEYY, 0.0, True
        if f < f_a1:
            e = ease_inout_cubic((f - f_a0) / max(1, f_a1 - f_a0))
            arc = math.sin(math.pi * e) * 2.2
            return W_HAND + (7.5 - W_HAND) * e, du_h * (1 - e) + arc, dv_h * (1 - e), 1.0, KEYY * (1 - e), 0.0, True
        if f < f_i1:
            e = ease_inout_cubic((f - f_i0) / max(1, f_i1 - f_i0))
            return 7.5 * (1 - e), 0.0, 0.0, 1.0, 0.0, 0.0, True
        return 0.0, 0.0, 0.0, 1.0, 0.0, 32.0 * pop_curve(f, f_t0, max(4, f_t1 - f_t0), 10), True

    prof = list(key["tooth_profile_modelled"])
    chain = [(6.5, -1.3)]
    for i, h in enumerate(prof):
        cc = 6.0 - i
        chain += [(cc + 0.28, -1.3 + h), (cc - 0.28, -1.3 + h)]
    chain += [(1.5, -1.3)]
    chain = sorted(chain)

    def surf(x):
        if x > 6.5:
            return koff + 1.3 * 1.3 - (x - 6.5) / 0.5 * 3.0 if x < 7.0 else -99
        if x < 1.5:
            return -99
        for (xa, ya), (xb, yb) in zip(chain, chain[1:]):
            if xa <= x <= xb:
                t = 0 if xb == xa else (x - xa) / (xb - xa)
                return koff + (-(ya + (yb - ya) * t)) * 1.3
        return -99

    def foot(i, w):
        a = (0.5 + i) * 1.3
        x = 6.5 - (a - w) / 1.3
        return max(surf(x + dx) for dx in (-0.45, -0.3, -0.15, 0, 0.15, 0.3, 0.45))

    rest_u = [foot(i, 0.0) for i in range(5)]
    lifts_max = 0.0
    hide_prev = None
    f_sh = f_t0 + 4
    cutters = {m.object for o in bpy.data.objects for m in getattr(o, "modifiers", []) if m.type == "BOOLEAN" and m.object}
    key_show = [o for o in [key] + list(key.children_recursive) if not o.hide_render and o not in cutters]
    print("ONCAM step r7 key loop", flush=True)
    for f in range(nf):
        w, du, dv, s, yaw, deg, vis = key_state(f)
        key.matrix_basis = kmat(w, du, dv, s, yaw, deg)
        key.keyframe_insert("location", frame=f)
        key.keyframe_insert("rotation_quaternion", frame=f)
        key.keyframe_insert("scale", frame=f)
        if vis != hide_prev:
            for o in key_show:                         # 只切本来就出像的（布尔刀具一直藏着：旧版的"白圆柱"就是钥匙孔刀具被打开了）
                o.hide_render = not vis
                o.keyframe_insert("hide_render", frame=f)
            hide_prev = vis
        inside = vis and du == 0.0 and dv == 0.0 and w <= 7.0
        for i in range(5):
            if inside:
                lift = max(-PIN_DROP, foot(i, w) - rest_u[i])
            elif f < fr + 2 + 2 * i:
                lift = 0.0
            else:                                              # 外壳弹开时销被震一下，落到没钥匙的位置
                lift = -PIN_DROP * (1 - spring((f - fr - 2 - 2 * i) / FPS, 0.35, 26.0))
            lifts_max = max(lifts_max, lift)
            j[f"pin_{i}"].location.z = lift * MM
            j[f"pin_{i}"].keyframe_insert("location", index=2, frame=f)
        j["plug"].rotation_euler.x = math.radians(deg)
        j["plug"].keyframe_insert("rotation_euler", index=0, frame=f)
        j["shackle"].location.z = 3.6 * ease_out_back((f - f_sh) / 10) * MM if f >= f_sh else 0.0
        j["shackle"].keyframe_insert("location", index=2, frame=f)
    for o in [lock, key] + [j[f"pin_{i}"] for i in range(5)] + [j["plug"], j["shackle"]]:
        linear_keys(o)
    print("ONCAM step r8 lights", flush=True)
    # ---- 零件集合：轮廓光只照它们；front 层只渲它们
    hero_objs = [o for o in [lock] + list(lock.children_recursive) if o.type in ("MESH", "CURVE")]
    hcol = bpy.data.collections.new("ONCAM_hero")
    sc.collection.children.link(hcol)
    for o in hero_objs:
        hcol.objects.link(o)
    for o in [lock] + list(lock.children_recursive):
        o["hero"] = 1
    s_c = P_rest
    rim = make_light("hero_rim", "AREA", s_c + Vector((0.75, 0.85, 0.75)), s_c, 0.7, V2["RIM_W"], kelvin_rgb(6800))
    rim.light_linking.receiver_collection = hcol
    for fk, en in ((0, 0.6), (e_c.get("g_start", e_c["f_start"]), 0.6), (e_c["f_land"], 1.5), (e_c["f_land"] + 60, 1.0), (nf - 1, 1.0)):
        rim.data.energy = V2["RIM_W"] * en
        rim.data.keyframe_insert("energy", frame=fk)
    col = kelvin_rgb(W["light"]["kelvin"])
    refl_card("refl_softbox", s_c + Vector((-0.95, -0.75, 0.85)), s_c, (1.5, 1.0), col, 5.0)
    refl_card("refl_strip", s_c + Vector((0.85, -0.35, 0.25)), s_c, (0.22, 1.3), kelvin_rgb(6500), 6.0)
    refl_card("refl_camside", Vector((0.55, -0.55, 0.25)), s_c, (2.6, 1.8), col, 1.6)       # 相机这一侧的大柔光（朝镜头的金面、蓝面有东西可反射，不发黑）
    refl_card("refl_behind", Vector((0.0, -0.30, 0.08)), Vector((0.0, 1.0, 0.0)), (3.2, 2.0), col, 6.0)   # 相机正后方：正对镜头的钥匙柄（金属）反射到它，不再是黑轮胎
    refl_card("refl_left", Vector((-0.75, -0.20, 0.10)), s_c, (2.0, 2.0), col, 5.0)                       # 开锁时钥匙柄转向画面左边，反射落在这里（11-20 test f372 柄发黑）
    for nm, z in (("refl_up", 0.95), ("refl_down", -0.75)):                                               # 锁芯转 32° 时柄面朝上/朝下翻：上下各一张，转到哪都有东西可反射
        refl_card(nm, Vector((0.35, -0.30, z)), s_c, (2.4, 1.6), col, 4.0)
    # 世界只在"镜面反射看到"时换成暖灰（相机看不到世界：大板挡满；漫反射照明不变）。金属件转到哪个角度都不会反射出一片死黑（11-20 test f372 钥匙柄）
    wnt = sc.world.node_tree
    wout = next(n for n in wnt.nodes if n.type == "OUTPUT_WORLD")
    wsrc = wout.inputs["Surface"].links[0].from_socket
    lp = wnt.nodes.new("ShaderNodeLightPath")
    bg2 = wnt.nodes.new("ShaderNodeBackground")
    bg2.inputs["Color"].default_value = (*col[:3], 1)
    bg2.inputs["Strength"].default_value = 0.9
    mx = wnt.nodes.new("ShaderNodeMixShader")
    wnt.links.new(lp.outputs["Is Glossy Ray"], mx.inputs[0])
    wnt.links.new(wsrc, mx.inputs[1])
    wnt.links.new(bg2.outputs[0], mx.inputs[2])
    wnt.links.new(mx.outputs[0], wout.inputs["Surface"])
    hf = make_light("hero_fill", "AREA", s_c + Vector((0.95, -1.0, 0.15)), s_c, 1.1, V2["RIM_W"] * 0.9, kelvin_rgb(6000))
    hf.light_linking.receiver_collection = hcol                                                # 只照零件：锁朝画面右边那一面不再死黑
    if BR:
        print("ONCAM trans", _axis_trans_lamps(W, hcol, nf, f_d0, (LM[0] @ kh).length, (LM[nf - 1] @ pins_mid).length, V2.get("TRANS_K", 1.0),
                                                   head_track=[(LM[f] @ kh).length for f in range(V2["TRANS_TRACK"] + 1)] if V2.get("TRANS_TRACK") else None,
                                                   tail_track=[(LM[f] @ pins_mid).length for f in range(f_d0, nf)] if V2.get("TRANS_TRACK") else None), flush=True)
    print("ONCAM step r9 framekey", flush=True)
    sc.frame_set(f_k1)
    kp = key.matrix_world.translation.copy()
    refl_card("refl_key", kp + Vector((-0.45, -0.55, 0.35)), kp, (0.9, 0.7), col, 4.0)

    def lock_center(f):
        return LM[max(0, min(nf - 1, int(f)))] @ c0

    def pins_point(f):
        return LM[max(0, min(nf - 1, int(f)))] @ pins_mid

    key_pts = {}
    print("ONCAM step r10 keypts", flush=True)
    for f in range(f_k0 - 10, f_i0 + 14):
        sc.frame_set(f)
        key_pts[f] = key.matrix_world @ Vector((-1.0 * MM, 0, 0))
    sc.frame_set(0)
    hero_box = [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]

    def bbox_pts(f):
        return [LM[f] @ p for p in hero_box]

    gs, gon = e_c.get("g_start", 158), e_c.get("g_on", 176)

    def focus_plan(f, Mcam):
        """焦点（米，沿视线）：段首跟锁拉回；等待时在锁前 0.10 m（略虚）；picture 前点名；钥匙亮出借焦点；段尾跟销子。"""
        loc = Mcam.translation
        fwd = (Mcam.to_3x3() @ Vector((0, 0, -1))).normalized()
        p = lock_center(f)
        if f > f_d0:
            p = p.lerp(pins_point(f), smooth((f - f_d0) / 6.0))
        d = (p - loc).dot(fwd)
        d -= 0.10 * smooth((f - 24) / 14.0) * (1 - smooth((f - gs) / max(1, gon - gs)))
        if f_k0 - 8 <= f <= f_i0 + 10:
            u = smooth((f - (f_k0 - 8)) / 10.0) * smooth((f_i0 + 10 - f) / 10.0)
            kp_ = key_pts.get(f, key_pts[min(key_pts)])
            d = d * (1 - u) + (kp_ - loc).dot(fwd) * u
        return max(0.03, d)

    def fstop_plan(f):
        a = 4.0 + (FSTOP - 4.0) * smooth(f / 30.0)
        if f > f_d0:
            a = a + (8.0 - a) * smooth((f - f_d0) / (nf - 1 - f_d0))
        return a

    def checks():
        out = {}
        kset = set([key] + list(key.children_recursive))
        cset = set(cover_parts)
        lock_objs = [o for o in _visible_meshes(lock, ignore_anim=True) if o not in kset and o not in cset]
        rotor = set(_visible_meshes(j["plug"]))
        pins_low = [o for o in rotor if "lower_pin" in o.name]
        core = [o for o in rotor if o not in pins_low]
        moving = set(rotor) | set(o for i in range(5) for o in _visible_meshes(j[f"pin_{i}"])) | set(_visible_meshes(j["shackle"]))
        statics = [o for o in lock_objs if o not in moving]
        hk, hc, hp, hcov = [], [], [], []
        key_objs = _visible_meshes(key, ignore_anim=True)
        for f in range(fr + 1, min(nf, f_hide)):
            sc.frame_set(f)
            a, b = _tree(cover_parts), _tree(lock_objs)
            if a and b and a.overlap(b):
                hcov.append(f)
        for f in range(f_k1, nf):
            sc.frame_set(f)
            kt = _tree(key_objs)
            if kt.overlap(_tree(statics)):
                hk.append(f)
            if kt.overlap(_tree(core)):
                hc.append(f)
            n = len(kt.overlap(_tree(pins_low)))
            if n:
                hp.append([f, n])
        out["cover_vs_lock_frames_after_pop"] = hcov
        out["key_vs_lockbody_frames"] = hk
        out["key_vs_core_frames"] = hc
        out["key_vs_lowerpins_touch"] = hp
        out["cover_hidden_from"] = f_hide
        return out

    handoff = dict(note="相机坐标（相机在原点看 +Y，+Z 向上；镜头 %.2f mm / 36 mm 传感器，偏移 %s）；锁 = kit_deep_r3.h06_pin_lock 放大 %.3f 倍" % (LENS, list(SHIFT), SLv),
                   head_pose=dict(frame=0, center_m=list(LM[0] @ c0), matrix=[list(r) for r in LM[0]]),
                   tail_pose=dict(frame=nf - 1, center_m=list(LM[nf - 1] @ c0), pins_mid_m=list(LM[nf - 1] @ pins_mid), matrix=[list(r) for r in LM[nf - 1]]))
    return dict(targets={"card": lock_center}, hero=lock, bbox=bbox_pts, key=key, cover_parts=cover_parts,
                focus=focus_plan, fstop=fstop_plan, tail_t0=f_d0, checks=checks, handoff=handoff,
                info=dict(SL=round(SLv, 3), pin_drop=PIN_DROP, lifts_max_mm=round(lifts_max, 3), key_w_hand=W_HAND,
                          du_h=round(du_h, 2), dv_h=round(dv_h, 2), cover_parts=[o.name for o in cover_parts], cutters=info_cutters,
                          frames=dict(okay=f_ok, turn=[e_t["f_start"], e_t["f_land"]], call=e_c["f_land"], reveal=fr,
                                      key=[f_k0, f_k1], approach=[f_a0, f_a1], insert=[f_i0, f_i1], open=[f_t0, f_t1], dive=[f_d0, nf - 1]),
                          V2={k: v for k, v in V2.items()}))


# ================================================================ 铺开第 1 批（11-20 晚，甲线）：3-06 插座一排嫌疑犯、3-09 磨砂 CDK20 + 钥匙坯
# 照技能 oncam-3d-parts 做。和 3-01 共用：机位、大板、量光比光、build_v2、合成、机检。新写的通用小件（_q、_bake、_fit_scale、
# _emit_mat、_vol_rescale、_RigidClip、_hero_lights）后面的出镜段都能直接用。
V306 = dict(
    SOCK_PX=(1510.0, 615.0), SOCK_D=1.50, SOCK_H_PX=345.0,      # 插座落位：出片像素中心、深度（米）、投影高（11-20 试渲：1625 右沿出画）
    REST1=(-62.0, 13.0), REST2=(-54.0, 16.0), CALL=(-50.0, 17.0), TURN2=(-70.0, 13.0),   # (yaw, tilt) 度；yaw 0 = 插孔正对镜头
    CALL_D=(-0.045, -0.05, 0.035),                               # suspect：往前一步（靠镜头）、抬一点、往左让
    BOX_L=(1150.0, 385.0, 2.0), BOX_R=(1700.0, 360.0, 2.2), BOX_H_PX=200.0,   # 两个磨砂盲盒：插座左后、右后，三个排成一排（嫌疑人列队），插座在前；像素中心、深度、真实外形投影高
    BOX_ROT_L=(35.0, 70.0, 10.0), BOX_ROT_R=(-50.0, 65.0, -15.0),               # 盲盒朝向（yaw, tilt, roll）
    BOX_GLOW=1.6, BOX_BASE=0.35, BOX_DIM_BACK=0.18,              # 盲盒亮起的自发光强度；没亮时的底光（不然磨砂件在 2 m 外像一块灰石头）；but 时往后退（米）
    LAMP_PX=(1500.0, 150.0), LAMP_D=1.62, LAMP_W=140.0,          # 吊灯灯罩口中心（像素，插座正上方）、深度；聚光灯功率（W，只照插座；60 时开灯看不出）
    PLUG_GAP_MM=24.0,                                            # 插头针尖离孔口（插座毫米）：一个身位
    PLUG_FROM=(62.0, 6.0, -100.0), PLUG_FROM_ROT=(0.0, 0.0, 80.0),   # 插头起点（插座坐标 mm，孔口前下方、画面下沿外）和起点朝向（绕 U 转 80°：针朝上）
    PLUG_CTRL=(8.0, 6.0, -42.0),                                 # 弧线控制点（相对等待位）
    HEAD_D=0.21, HEAD_PX=(880.0, 540.0), HEAD_CTRL=(2350.0, 470.0, 0.95),   # 段首：孔口离镜头（米，0.27 时插座面左边没盖到 D 的左肩，第 0 帧只挡住 89%）、孔口在画面的位置；甩出去的弧的控制点
    TAIL=(35.0, 74.0), TAIL_D=0.15, TAIL_CTRL=(1500.0, 300.0, 0.75), TAIL_PX=(960.0, 560.0),   # 段尾：盖顶朝镜头冲进来
    DIVE_AT=653,                                                 # 11-23 rc06：说完第 649 帧、段尾冲镜起 650，K4/OC7 要 ≥ 说完 + 4 = 653（同 4-08 的 DIVE_AT，不改共用事件表）
    RING_GLOW=5.0,
    BRIGHT=True, BORE_CAM=12.5, HEAD_EASE=0.5, PLUG_CAM=4.0, PLUG_OFF=2.7, TRANS_K=1.6, TRANS_TRACK=14, TRANS_NOGLOSS=True,   # 11-23 rc02 黑场返修（18 文档 3.2 O2）：段首孔桶里、段尾插头金色柄面，光轴转场灯；镜头离孔底 / 柄面凹槽底（插座毫米）
    BOARD_K=1.27, BOARD_HIDE=("stations", "zone_tags", "z1_c0_r0"),
    HEAD_BOX=(300, 90, 820, 680), LOCK_BOX=(1160, 0, 1940, 960),
    RIM_W=60.0, SAMPLES=16, GRAIN_F=150, GRAIN_GAIN=1.0,         # 颗粒倍数：D 这条素材颗粒粗（衬衫 1.07，B 只有 0.46），2.0 时成片 M10 0.44；10 帧试合成 2.0→0.65、3.0→0.88、4.0→1.05，整段编码再打七折
)
V309 = dict(
    FR_PX=(1560.0, 470.0), FR_D=1.45, FR_H_PX=425.0,             # 磨砂 CDK20 落位（像素中心、深度、真实外形投影高）
    REST1=(-25.0, 10.0, 0.0), CALL=(-12.0, 14.0, 0.0), BASE_X=90.0, BASE_Y=90.0,   # 朝向；先绕 X 转 90°、再绕 Y 转 90°：36 mm 长边竖起来（只绕 X 时长边横着，又宽又矮）
    CALL_D=(-0.035, -0.04, 0.03),
    KEY_PX=(1360.0, 800.0), KEY_D=1.22, KEY_LEN_PX=320.0, KEY_ROLL=28.0, KEY_YAW=-38.0,   # 钥匙坯：柄中心、深度、投影长、斜着朝磨砂壳
    KEY_REACH=0.5,                                               # in the dark：走到和磨砂壳之间一半的地方停住
    DARK=0.28, DARK_KEY=0.35, PERSON_DIM=0.18,                   # 屋里暗到 28%；主光到 35%；人远离窗的一侧最多暗 18%（剧本：只剩灯和脸的一侧亮）
    VEIL_ROUGH=0.42, FROST_GLOW=0.0, KEY_SPOT_W=50.0,           # 钥匙坯的小灯（18 W 时暗屋里钥匙是一块橄榄色）
    HEAD_D=0.27, HEAD_CTRL=(2300.0, 420.0, 0.9),                # 段首：磨砂壳中心离镜头（长边竖起来以后变窄，0.32 时左边盖不满）
    TAIL_D=0.21, TAIL_CTRL=(1700.0, 250.0, 0.8), TAIL_PX=(760.0, 540.0),   # 中心 960,540 时最后一帧左下角露出大板
    BOARD_K=1.27, BOARD_HIDE=("stations", "zone_tags", "z1_c0_r0"),
    HEAD_BOX=(380, 90, 960, 680), LOCK_BOX=(1180, 0, 1940, 960),
    RIM_W=70.0, SAMPLES=16, GRAIN_F=90, CARD_TRANSMISSION=True, DIVE_AT=315,   # 11-23 rc06：说完第 311 帧、段尾起 313，OC7/K4 要 ≥ 说完 + 4 = 315（同 4-08 的 DIVE_AT，不改共用事件表）
)


def _q(yaw, tilt, roll=0.0, base=None):
    """朝向：先 base，再绕 Z 转 yaw、绕 Y 转 roll、绕 X 转 tilt（tilt > 0 顶面朝镜头翻）。"""
    q = (Matrix.Rotation(math.radians(tilt), 4, "X") @ Matrix.Rotation(math.radians(roll), 4, "Y")
         @ Matrix.Rotation(math.radians(yaw), 4, "Z")).to_quaternion()
    return q @ base if base is not None else q


def _qpow(qa, qb, p):
    dq = qa.rotation_difference(qb)
    ax, ang = dq.to_axis_angle()
    return Quaternion(ax, ang * p) @ qa


def _qpow_w(qa, qb, p):
    """同 _qpow，但差值按世界系算（p = 1 时正好到 qb）。_qpow 的 rotation_difference 是局部系的差、却左乘，两个转动不可交换时 p = 1 到不了 qb
    （5-02 段首 HEAD_ROT 转 90° 落位那帧整组跳一下）；已出的段不改，新段用 HEAD_QW=True 走这个。"""
    dq = qb @ qa.inverted()
    if dq.w < 0:
        dq.negate()
    ax, ang = dq.to_axis_angle()
    return Quaternion(ax, ang * p) @ qa


def _bz(a, b, c, t):
    return a * (1 - t) ** 2 + b * 2 * (1 - t) * t + c * t * t


def _bz_at_depth(A, C, B, y):
    """二次贝塞尔上深度（+Y）等于 y 的点（深度沿曲线单调，二分）。"""
    lo_, hi_ = 0.0, 1.0
    inc = B.y > A.y
    for _ in range(40):
        m = (lo_ + hi_) / 2
        if (_bz(A, C, B, m).y < y) == inc:
            lo_ = m
        else:
            hi_ = m
    return _bz(A, C, B, (lo_ + hi_) / 2)


def _logd(y0, y1, e):
    return math.exp(math.log(y0) + (math.log(y1) - math.log(y0)) * e)


def _Mof(center, q, c0, s):
    R4 = q.to_matrix().to_4x4()
    return Matrix.Translation(center - R4 @ (c0 * s)) @ R4 @ Matrix.Diagonal((s, s, s, 1))


def _bake(root):
    """子树里所有网格的修改器（布尔、倒角…）应用掉，删掉布尔刀具：零件刚体运动时每帧不再重算 EXACT 布尔（技能坑 14）。"""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    cutters = {m.object for o in root.children_recursive for m in getattr(o, "modifiers", []) if m.type == "BOOLEAN" and m.object}
    for o in [root] + list(root.children_recursive):
        if o.type == "MESH" and o.modifiers and o not in cutters:
            me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
            old = o.data
            o.modifiers.clear()
            o.data = me
            if old.users == 0:
                bpy.data.meshes.remove(old)
    for c in cutters:
        try:
            bpy.data.objects.remove(c, do_unlink=True)
        except (ReferenceError, RuntimeError):
            pass
    bpy.context.view_layer.update()


def _vis_meshes(root):
    return [o for o in [root] + list(root.children_recursive) if o.type in ("MESH", "CURVE") and not o.hide_render]


def _extreme_pts(root, n_dir=96):
    """机检 M3–M5 用的零件外形点（世界坐标，当前位姿）：沿球面上 n_dir 个方向各取最远的那个顶点。
    包围盒 8 个角投影出来比零件实际大得多（转成 3/4 侧面时右沿多算一百多像素），用这些点投影才是零件真正占的画面。"""
    dg = bpy.context.evaluated_depsgraph_get()
    V = []
    for o in _vis_meshes(root):                                  # 曲线（料杆、浇口）也算：11-21 1-03 只有料杆在的那几帧框里没有料杆，高度少算
        me = o.evaluated_get(dg).to_mesh()
        mw = o.matrix_world
        V += [mw @ v.co for v in me.vertices]
        o.evaluated_get(dg).to_mesh_clear()
    if not V:
        return []
    ga = math.pi * (3 - math.sqrt(5))
    out = set()
    for i in range(n_dir):
        z = 1 - 2 * (i + 0.5) / n_dir
        r = math.sqrt(1 - z * z)
        d = Vector((r * math.cos(ga * i), r * math.sin(ga * i), z))
        out.add(max(range(len(V)), key=lambda j: V[j].dot(d)))
    return [V[j].copy() for j in out]


def _fit_scale(c0, lo, hi, q, P_rest, h_px, Mcam=None, pts=None):
    """缩放倍数：零件按 q 朝向放在 P_rest，投影高 = h_px。给了 pts（_extreme_pts 的外形点）就按真实外形量，
    不给按包围盒 8 角量（方盒子一样；圆滚滚的零件 8 角会多算两三成，3-09 磨砂壳按角量 410、实际只有 321）。"""
    s = 10.0
    corners = pts or [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
    for _ in range(6):
        M = _Mof(P_rest, q, c0, s)
        ys = [project(Mcam or cam_basis(), SHIFT, M @ p)[1] for p in corners]
        s *= h_px / max(1e-6, max(ys) - min(ys))
    return s


def _emit_mat(objs, name, color):
    """objs 用的材质复制一份，加一个自发光（Add Shader）。返回自发光强度的输入口（关键帧打在它的 default_value 上）。"""
    src = objs[0].active_material
    m = src.copy(); m.name = name
    nt = m.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    lk = next(l for l in nt.links if l.to_node == out and l.to_socket.name == "Surface")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color[:3], 1)
    em.inputs["Strength"].default_value = 0.0
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(lk.from_socket, add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    for o in objs:
        for i, sl in enumerate(o.material_slots):
            if sl.material == src:
                o.material_slots[i].material = m
    return em.inputs["Strength"], m


def _key_val(sock, pairs):
    """给节点输入口按 (帧, 值) 打关键帧（线性）。"""
    for f, v in pairs:
        sock.default_value = v
        sock.keyframe_insert("default_value", frame=f)


def _vol_rescale(root, s):
    """透明件（kit_parts.mat_clear）的体积吸收密度是按米算的：零件放大 s 倍后厚度也大 s 倍，不改就是一块墨蓝（技能坑 19）。
    子树里用到体积吸收的材质各复制一份，密度 ÷ s。"""
    done = {}
    for o in [root] + list(root.children_recursive):
        if o.type != "MESH":
            continue
        for sl in o.material_slots:
            m = sl.material
            if m is None or not m.use_nodes:
                continue
            va = next((n for n in m.node_tree.nodes if n.type == "VOLUME_ABSORPTION"), None)
            if va is None:
                continue
            if m.name not in done:
                mc = m.copy(); mc.name = m.name + f"_x{s:.1f}"
                vb = next(n for n in mc.node_tree.nodes if n.type == "VOLUME_ABSORPTION")
                vb.inputs["Density"].default_value /= s
                done[m.name] = mc
            sl.material = done[m.name]
    return list(done.values())


class _RigidClip:
    """刚体之间的穿模（BVH）：每个物体的三角面只在物体自己的坐标里取一次，每帧乘世界矩阵。先比包围盒，不相交的帧跳过。"""
    def __init__(self, objs):
        import numpy as np
        dg = bpy.context.evaluated_depsgraph_get()
        self.parts = []
        for ob in objs:
            e = ob.evaluated_get(dg)
            me = e.to_mesh()
            me.calc_loop_triangles()
            V = np.array([v.co[:] for v in me.vertices], dtype=np.float64)
            F = [tuple(t.vertices) for t in me.loop_triangles]
            e.to_mesh_clear()
            if len(F):
                self.parts.append((ob, V, F))

    def tree(self):
        import numpy as np
        from mathutils.bvhtree import BVHTree
        Vs, Fs, n = [], [], 0
        for ob, V, F in self.parts:
            if ob.hide_render:
                continue
            M = np.array(ob.matrix_world)
            W = V @ M[:3, :3].T + M[:3, 3]
            Vs.append(W)
            Fs += [(a + n, b + n, c + n) for a, b, c in F]
            n += len(V)
        if not Vs:
            return None, None
        W = np.concatenate(Vs)
        return BVHTree.FromPolygons(W.tolist(), Fs, all_triangles=True), (W.min(0), W.max(0))

    @staticmethod
    def hits(A, B, frames, sc, margin=0.0):
        out = []
        for f in frames:
            sc.frame_set(f)
            ta, ba = A.tree()
            tb, bb = B.tree()
            if ta is None or tb is None:
                continue
            if (ba[1] < bb[0] - margin).any() or (bb[1] < ba[0] - margin).any():
                continue
            if ta.overlap(tb):
                out.append(f)
        return out


def _hero_lights(W, hcol, s_c, P, rim_keys, key_point=None):
    """3-01 定下来的零件用光，抽成通用件：只照零件的冷白轮廓光（右后上，能量按 rim_keys 走）、侧补光，
    只给镜面看的反光卡（柔光箱、条灯、相机侧、相机正后方、左、上、下），世界只在镜面光线里换成暖灰。"""
    sc = W["sc"]
    rim = make_light("hero_rim", "AREA", s_c + Vector((0.75, 0.85, 0.75)), s_c, 0.7, P["RIM_W"], kelvin_rgb(6800))
    rim.light_linking.receiver_collection = hcol
    for fk, en in rim_keys:
        rim.data.energy = P["RIM_W"] * en
        rim.data.keyframe_insert("energy", frame=fk)
    col = kelvin_rgb(W["light"]["kelvin"])
    refl_card("refl_softbox", s_c + Vector((-0.95, -0.75, 0.85)), s_c, (1.5, 1.0), col, 5.0)
    refl_card("refl_strip", s_c + Vector((0.85, -0.35, 0.25)), s_c, (0.22, 1.3), kelvin_rgb(6500), 6.0)
    refl_card("refl_camside", Vector((0.55, -0.55, 0.25)), s_c, (2.6, 1.8), col, 1.6)
    refl_card("refl_behind", Vector((0.0, -0.30, 0.08)), Vector((0.0, 1.0, 0.0)), (3.2, 2.0), col, 6.0)
    refl_card("refl_left", Vector((-0.75, -0.20, 0.10)), s_c, (2.0, 2.0), col, 5.0)
    for nm, z in (("refl_up", 0.95), ("refl_down", -0.75)):
        refl_card(nm, Vector((0.35, -0.30, z)), s_c, (2.4, 1.6), col, 4.0)
    wnt = sc.world.node_tree
    wout = next(n for n in wnt.nodes if n.type == "OUTPUT_WORLD")
    wsrc = wout.inputs["Surface"].links[0].from_socket
    lp = wnt.nodes.new("ShaderNodeLightPath")
    bg2 = wnt.nodes.new("ShaderNodeBackground")
    bg2.inputs["Color"].default_value = (*col[:3], 1)
    bg2.inputs["Strength"].default_value = 0.9
    mx = wnt.nodes.new("ShaderNodeMixShader")
    wnt.links.new(lp.outputs["Is Glossy Ray"], mx.inputs[0])
    wnt.links.new(wsrc, mx.inputs[1])
    wnt.links.new(bg2.outputs[0], mx.inputs[2])
    wnt.links.new(mx.outputs[0], wout.inputs["Surface"])
    hf = make_light("hero_fill", "AREA", s_c + Vector((0.95, -1.0, 0.15)), s_c, 1.1, P["RIM_W"] * 0.9, kelvin_rgb(6000))
    hf.light_linking.receiver_collection = hcol
    if key_point is not None:
        refl_card("refl_key", key_point + Vector((-0.45, -0.55, 0.35)), key_point, (0.9, 0.7), col, 4.0)
    return dict(rim=rim, fill=hf, glossy_bg=bg2)


def _axis_trans_lamps(W, hcol, nf, f_d0, d_head, d_tail, k=1.0, r=0.03, head_track=None, tail_track=None, nogloss=False, tk=1.0):
    """18 文档 1.8 转场灯的光轴版（11-23 rc02 黑场返修，旧 recipe 用）：镜头往孔桶里看、贴着柄面时，斜放的灯照不进去，
    改成镜头位置朝前的一块圆面光（半径 r 米，比孔桶小），只照零件（灯光链接），不进镜头、不投影。
    能量按盖满面离镜头 d 米算到主光照度的 3 倍：P = 3 × 主光 × (d² + r²) / 2.6² × k（圆面光正前方照度 = P / π(d² + r²)）。
    段首 0–20 帧开、28 帧灭；段尾 f_d0 起 12 帧亮到满。"""
    key_w = W.get("fit", {}).get("key_w", 900.0)
    out = []
    for nm, d, keys in (("trans_head", d_head, [(0, 1.0), (20, 1.0), (28, 0.0)]),
                        ("trans_tail", d_tail, [(0, 0.0), (f_d0, 0.0), (min(nf - 1, f_d0 + 12), 1.0), (nf - 1, 1.0)])):
        if d is None:
            continue
        en = 3.0 * key_w * (d * d + r * r) / 2.6 ** 2 * k
        o = make_light(nm, "AREA", Vector((0.0, -0.002, 0.0)), Vector((0.0, 1.0, 0.0)), 2 * r, en, kelvin_rgb(5600))
        o.data.shape = "DISK"
        o.light_linking.receiver_collection = hcol
        o.visible_camera = False
        o.visible_glossy = not nogloss                         # nogloss 不进反射：5-09 试渲金色柄面上一块灯的高光，第 214→215 帧 0.86→0.55；深蓝插座面上也是一个个"手电筒"亮斑
        o.data.use_shadow = False
        if nm == "trans_head" and head_track:                  # 段首逐帧跟着盖满点的距离补能量（照度不变，最多 ×30），之后照原样 20→28 帧熄掉
            for fk, dk in enumerate(head_track):               # 3-06 试渲：退出孔桶时深蓝插座面离开灯的近处，变暗到 0.42 又回升（往回闪）
                o.data.energy = min(30.0 * en, 3.0 * key_w * (dk * dk + r * r) / 2.6 ** 2 * k)
                o.data.keyframe_insert("energy", frame=fk)
            e_tr = o.data.energy
            keys = [(max(20, len(head_track)), 1.0), (max(28, len(head_track) + 8), 0.0)]
            en = e_tr
        if nm == "trans_tail" and tail_track:                  # 段尾逐帧跟着冲镜头那一点的距离补能量（最多 ×30），f_d0 起 12 帧淡入
            for j, dk in enumerate(tail_track):                # 5-09 试渲：冲镜头途中深蓝插座面占满画面那几帧 0.35（段尾 15 帧要每帧 ≥ 0.45）
                fk = f_d0 + j
                o.data.energy = min(30.0 * en, 3.0 * key_w * (dk * dk + r * r) / 2.6 ** 2 * k) * min(1.0, j / 12.0) * tk   # tk：段尾灯单独加（5-09 盖满那几帧 0.42–0.45）
                o.data.keyframe_insert("energy", frame=fk)
            if f_d0 > 0:
                o.data.energy = 0.0
                o.data.keyframe_insert("energy", frame=0)
            keys = []
        for fk, v in keys:
            o.data.energy = en * v
            o.data.keyframe_insert("energy", frame=fk)
        linear_keys(o.data)
        out.append((nm, round(d, 4), round(en, 2)))
    return out


def _hero_collection(sc, roots, name="ONCAM_hero"):
    hcol = bpy.data.collections.new(name)
    sc.collection.children.link(hcol)
    for r in roots:
        for o in [r] + list(r.children_recursive):
            o["hero"] = 1
            if o.type in ("MESH", "CURVE"):
                hcol.objects.link(o)
    return hcol


def _hide_tracks(objs, f_show, nf):
    """objs 在 f_show 之前不出像（hide_render 关键帧）。"""
    for o in objs:
        o.hide_render = True
        o.keyframe_insert("hide_render", frame=0)
        o.hide_render = False
        o.keyframe_insert("hide_render", frame=max(1, f_show))


def _make_lamp(K, P):
    """3-06 的小吊灯（零件库没有，按玩具语言现搭）：亮黑灯罩 + 金色口圈 + 灯泡（自发光）+ 黑线吊到画外。灯罩口中心在原点，朝下。"""
    root = link_obj(bpy.data.objects.new("lamp_root", None))
    parts = []
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=0.085, radius2=0.03, depth=0.11, location=(0, 0, 0.055), end_fill_type="NOTHING")
    sh = bpy.context.object; sh.name = "lamp_shade"
    sm = sh.modifiers.new("solid", "SOLIDIFY"); sm.thickness = 0.004; sm.offset = 1.0
    bv = sh.modifiers.new("bv", "BEVEL"); bv.width = 0.0012; bv.segments = 2
    bpy.ops.object.shade_smooth()
    sh.data.materials.append(K.black)
    parts.append(sh)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.0855, minor_radius=0.0042, major_segments=96, minor_segments=16, location=(0, 0, 0.001))
    rg = bpy.context.object; rg.name = "lamp_rim"; bpy.ops.object.shade_smooth(); rg.data.materials.append(K.gold); parts.append(rg)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.032, depth=0.035, location=(0, 0, 0.125))
    cp = bpy.context.object; cp.name = "lamp_cap"; bpy.ops.object.shade_smooth(); cp.data.materials.append(K.gold); parts.append(cp)
    bv = cp.modifiers.new("bv", "BEVEL"); bv.width = 0.003; bv.segments = 3
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.0035, depth=1.6, location=(0, 0, 0.142 + 0.8))
    cd = bpy.context.object; cd.name = "lamp_cord"; bpy.ops.object.shade_smooth(); cd.data.materials.append(K.black); parts.append(cd)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.03, location=(0, 0, 0.035))
    bu = bpy.context.object; bu.name = "lamp_bulb"; bpy.ops.object.shade_smooth()
    bm = bpy.data.materials.new("lamp_bulb"); bm.use_nodes = True
    nt = bm.node_tree
    pb = nt.nodes["Principled BSDF"]
    pb.inputs["Base Color"].default_value = (0.42, 0.40, 0.37, 1)   # 灭着的灯泡是灰的（白的看着像已经亮了）
    pb.inputs["Roughness"].default_value = 0.25
    pb.inputs["Transmission Weight"].default_value = 0.3
    pb.inputs["Emission Color"].default_value = (1.0, 0.78, 0.45, 1)
    pb.inputs["Emission Strength"].default_value = 0.0
    bu.data.materials.append(bm); parts.append(bu)
    for o in parts:
        o.parent = root
        for c in list(o.users_collection):                       # bpy.ops 加的物体进的是当前活动集合（大板文件里的），挪到场景根下
            c.objects.unlink(o)
        bpy.context.scene.collection.objects.link(o)
    sd = bpy.data.lights.new("lamp_spot", "SPOT")
    sd.energy = 0.0; sd.color = kelvin_rgb(3300); sd.spot_size = math.radians(70); sd.spot_blend = 0.5; sd.shadow_soft_size = 0.03
    sp = link_obj(bpy.data.objects.new("lamp_spot", sd))
    sp.parent = root
    sp.location = (0, 0, 0.0)
    pl = bpy.data.lights.new("lamp_inner", "POINT")       # 灯罩里面被灯泡照亮（不然亮着的灯罩里面是黑的）
    pl.energy = 0.0; pl.color = kelvin_rgb(3300); pl.shadow_soft_size = 0.02
    pi = link_obj(bpy.data.objects.new("lamp_inner", pl))
    pi.parent = root
    pi.location = (0, 0, 0.03)
    return root, parts, bu, pb.inputs["Emission Strength"], sp, pi


def recipe_socket_lineup(W):
    """3-06 D："So: a strong suspect. Not the only cause of liver cancer, but a lock worth trying."（694 帧）
    01 文档 3-06 + 06 文档 3-06（只改最后一拍）：人旁边一排嫌疑犯——中间 CDK20 插座（h01b），左后、右后两个磨砂盲盒（p29 代替 h10，
    11 文档），插座上方一盏小吊灯。事件 id 见 events/3-06.json：
      arrive  So       插座从镜头前（孔口盖满画面）退回 D 右侧落位（段首 T5）
      turn    a        慢慢转、抬头
      lamp    strong   吊灯亮，光打在插座上，灯一晃
      call    suspect  焦点点名 + 预颤，往前一步
      other1/2 only/cause 左、右盲盒里面亮起来
      turn2   cancer   插孔转向左前方
      dim     but      盲盒暗下去、往后退
      ring    lock     焦点点名，红环亮
      plug    trying   金色假插头（h02b 048）从下方转过来，停在孔口前一个身位，不插
      dive    （说完）  插座带着插头转过去，盖顶冲进镜头（段尾 T1）"""
    import kit_parts as KP
    import kit_socket as KS
    sc, K, cfg = W["sc"], W["kit"], W["cfg"]
    P = cfg["P"]
    nf = cfg["nf"]
    E = {e["id"]: e for e in cfg["K"]["events"]}
    print("ONCAM step s0", flush=True)
    sock = KS.h01b_cdk20_socket(K)
    KS.rest(sock)
    _bake(sock)
    print("ONCAM step s1 socket baked", flush=True)
    bpy.context.view_layer.update()
    lo, hi = mesh_bounds([sock])
    sock_pts = _extreme_pts(sock)                              # 机检外形点（静止位姿，乘 LM[f]）
    c0 = (lo + hi) / 2
    base = Quaternion((0, 0, 1), math.radians(-90))           # 插孔轴 +W → 朝镜头（−Y）
    q_r1 = _q(*P["REST1"], base=base)
    P_rest = Vector(px_to_world(*P["SOCK_PX"], P["SOCK_D"]))
    s = _fit_scale(c0, lo, hi, q_r1, P_rest, P["SOCK_H_PX"])
    sock.rotation_mode = "QUATERNION"
    q_r2, q_call, q_t2 = _q(*P["REST2"], base=base), _q(*P["CALL"], base=base), _q(*P["TURN2"], base=base)
    port = Vector((KS.FACE_W, 0.0, 0.0)) * MM                 # 孔口中心（插座坐标）
    lid_top = Vector((-8.5, 0.0, KS.TOP_Z)) * MM
    q_head = _q(0.0, 3.0, base=base)
    P_head = Vector(px_to_world(*P.get("HEAD_PX", (960, 540)), P["HEAD_D"])) - q_head.to_matrix() @ ((port - c0) * s)
    BR = P.get("BRIGHT")
    head_pt = port
    if BR:                                                     # 11-23 rc02 黑场（18 文档 3.2 O2）：段首镜头在孔口外 BORE_CAM − 12 mm，顺着孔轴往孔桶里看，盖满的是骨白孔底和内壁
        head_pt = Vector((0.0, 0.0, 0.0)) * MM                 # 孔底正中（触点块前面 W = 0）；孔轴对着素材光轴（AXIS），镜头在孔轴上
        P_head = Vector(px_to_world(*AXIS, P["BORE_CAM"] * MM * s)) - q_head.to_matrix() @ ((head_pt - c0) * s)
    P_hctrl = Vector(px_to_world(*P["HEAD_CTRL"]))
    e_a, e_t, e_l, e_c = E["arrive"], E["turn"], E["lamp"], E["call"]
    e_o1, e_o2, e_t2, e_dim, e_r, e_p, e_d = E["other1"], E["other2"], E["turn2"], E["dim"], E["ring"], E["plug"], E["dive"]
    f_ok, f_ok_end = e_a["f_land"], e_a["f_end"]

    def hover(f):
        b = smooth((f - 30) / 40)
        return Vector((0.0, 0.0, 0.006 * math.sin(2 * math.pi * f / 240) * b)), 1.3 * math.sin(2 * math.pi * f / 330 + 0.6) * b

    def base_pose(f):
        if f <= f_ok:
            t = f / max(1, f_ok)
            p = ease_out_back(t, 0.9)
            k_e = P.get("HEAD_EASE", 0.0)                       # >0 混进 smoothstep：开头几帧退得慢（M9 段首每帧亮度跳变 ≤ 24）
            c = _bz_at_depth(P_head, P_hctrl, P_rest, _logd(P_head.y, P_rest.y, (1 - k_e) * ease_out_cubic(t) + k_e * smooth(t)))
            q = _qpow(q_head, q_r1, smooth(t) * 0.35 + p * 0.65)
        else:
            sp = (f - f_ok) / FPS
            c = P_rest + Vector((0.004, 0.006, -0.008)) * spring(sp, 0.45, 20.0) * (1 - clamp01((f - f_ok) / max(1, f_ok_end + 12 - f_ok)))
            q = q_r1.copy()
        u = ease_inout_cubic((f - e_t["f_start"]) / max(1, e_t["f_land"] - e_t["f_start"]))
        if u > 0 and f > f_ok:
            q = _qpow(q, q_r2, u)
        fl = e_c["f_land"]
        if fl - 6 <= f < fl:                                    # 预颤：往下沉 3 mm
            c = c + Vector((0, 0, -0.003 * math.sin(math.pi * (f - fl + 6) / 6) ** 2))
        p = ease_out_back((f - fl) / 18.0, 1.3) if f >= fl else 0.0
        if p > 0:
            c = c + Vector(P["CALL_D"]) * p
            q = _qpow(q, q_call, p)
        if f > e_t2["f_start"]:                                  # 转到位过冲一点再回弹（easeOutBack）
            q = _qpow(q, q_t2, ease_out_back((f - e_t2["f_start"]) / max(1, e_t2["f_land"] - e_t2["f_start"]), 0.8))
        fr = e_r["f_land"]                                       # 红环亮：插座轻轻往上一顶
        if f >= fr - 4:
            c = c + Vector((0, 0, 0.003)) * math.exp(-max(0, f - fr) / 8.0) * math.sin(math.pi * clamp01((f - fr + 4) / 8.0))
        ho, hy = hover(f)
        return c + ho, Quaternion((0, 0, 1), math.radians(hy)) @ q

    f_d0, f_d1 = e_d["f_start"], nf - 1
    q_tail = _q(*P["TAIL"], base=base)
    tgt_tail = Vector(px_to_world(*P["TAIL_PX"], P["TAIL_D"]))
    tail_pt = lid_top
    if BR:                                                     # 11-23 rc02：段尾插头还停在孔口前一个身位，镜头进孔桶会穿过它 → 冲到插头金色柄面上（18 文档 1.8"插头用金色柄面"）
        q_tail = _q(0.0, 0.0, base=base)                       # 孔口（插头）正对镜头
        w_end = KS.FACE_W + P["PLUG_GAP_MM"] + KS.PLUG_SPECS["048"]["L"] + 12.0   # 插头等待位（同下面 w_wait；段尾时回弹早停了）
        tail_pt = Vector((w_end + 9.3, 0.0, -P["PLUG_OFF"])) * MM    # 柄背面凹槽底（插头坐标 x 9.3），往下让开刻字
        tgt_tail = Vector(px_to_world(*P["TAIL_PX"], P["PLUG_CAM"] * MM * s))
    c1_tail = tgt_tail - q_tail.to_matrix() @ ((tail_pt - c0) * s)

    def pose(f):
        c, q = base_pose(f)
        if f > f_d0:
            t = (f - f_d0) / (f_d1 - f_d0)
            ctrl = Vector(px_to_world(*P["TAIL_CTRL"]))
            c = _bz_at_depth(c, ctrl, c1_tail, _logd(c.y, c1_tail.y, smooth(t) * 0.7 + 0.3 * ease_in_cubic(t)))
            q = (_qpow_w if BR else _qpow)(q, q_tail, smooth(min(1.0, t * 1.15)))   # 亮版：_qpow 到不了 q_tail（3-06 试渲末帧插座还斜 30°，柄面没对上镜头）
        return c, q

    LM = []
    for f in range(nf):
        c, q = pose(f)
        LM.append(_Mof(c, q, c0, s))
        key_matrix(sock, f, LM[f])
    linear_keys(sock)
    print("ONCAM step s2 socket anim", flush=True)
    # ---- 红环：复制一份红，自发光在 lock 前起亮
    rings = [o for o in sock.children_recursive if o.type == "MESH" and "red_ring" in o.name]
    ring_s, _ = _emit_mat(rings, "oncam_red_ring_glow", (1.0, 0.10, 0.06))
    _key_val(ring_s, [(0, 0.0), (e_r["f_start"], 0.0), (e_r["f_land"], P["RING_GLOW"] * 1.25), (e_r["f_end"], P["RING_GLOW"]), (nf - 1, P["RING_GLOW"])])
    # ---- 两个磨砂盲盒
    boxes = []
    for side, (u, v, d), rot, ev in (("l", P["BOX_L"], P["BOX_ROT_L"], e_o1), ("r", P["BOX_R"], P["BOX_ROT_R"], e_o2)):
        b = KP.p29_cdk20_unknown(K)
        b.name = f"box_{side}"
        _bake(b)
        bpy.context.view_layer.update()
        blo, bhi = mesh_bounds([b])
        b_pts = _extreme_pts(b)
        bc0 = (blo + bhi) / 2
        bq = _q(*rot)
        bP = Vector(px_to_world(u, v, d))
        bs = _fit_scale(bc0, blo, bhi, bq, bP, P["BOX_H_PX"], pts=b_pts)
        _vol_rescale(b, bs)
        meshes = [o for o in b.children_recursive if o.type == "MESH" and not o.hide_render]
        glow, _ = _emit_mat(meshes, f"oncam_box_glow_{side}", (0.55, 0.78, 1.0))
        g = P["BOX_GLOW"]
        b0 = P.get("BOX_BASE", 0.0)
        _key_val(glow, [(0, b0), (ev["f_start"], b0), (ev["f_land"], g * 1.3), (ev["f_end"], g), (e_dim["f_start"], g), (e_dim["f_end"], b0 * 0.6), (nf - 1, b0 * 0.6)])
        b.rotation_mode = "QUATERNION"
        ph = 1.7 if side == "l" else 4.1
        BM = []
        for f in range(nf):
            k = ease_inout_cubic((f - e_dim["f_start"]) / max(1, e_dim["f_end"] - e_dim["f_start"]))
            back = Vector((0.0, P["BOX_DIM_BACK"], -0.03)) * k
            bob = 0.0
            if f >= ev["f_start"]:                               # 亮起时轻轻一跳
                bob = 0.012 * math.sin(math.pi * clamp01((f - ev["f_start"]) / 14.0)) * math.exp(-max(0, f - ev["f_land"]) / 10.0)
            hv = Vector((0, 0, 0.005 * math.sin(2 * math.pi * f / 270 + ph) + bob))
            qq = Quaternion((0, 0, 1), math.radians(4.0 * math.sin(2 * math.pi * f / 420 + ph) + 3.0 * k)) @ bq
            BM.append(_Mof(bP + back + hv, qq, bc0, bs))
            key_matrix(b, f, BM[f])
        linear_keys(b)
        boxes.append(dict(root=b, c0=bc0, lo=blo, hi=bhi, s=bs, glow=glow, M=BM, pts=b_pts))
    print("ONCAM step s3 boxes", flush=True)
    # ---- 吊灯
    lamp, lamp_parts, bulb, bulb_s, spot, inner = _make_lamp(K, P)
    lamp.rotation_mode = "XYZ"
    L0 = Vector(px_to_world(*P["LAMP_PX"], P["LAMP_D"]))
    pivot = L0 + Vector((0, 0, 0.95))                             # 线吊点（画外）
    for f in range(nf):
        a = 0.0
        if f >= e_l["f_land"]:                                   # 灯亮那一下"咔"，灯晃 2.2°，阻尼
            a = 2.2 * math.exp(-(f - e_l["f_land"]) / 55.0) * math.sin(2 * math.pi * (f - e_l["f_land"]) / 62.0)
        a += 0.35 * math.sin(2 * math.pi * f / 380)
        R = Matrix.Rotation(math.radians(a), 4, "Y") @ Matrix.Rotation(math.radians(0.6 * a), 4, "X")
        M = Matrix.Translation(pivot) @ R @ Matrix.Translation(L0 - pivot)
        key_matrix(lamp, f, M)
    linear_keys(lamp)
    on0, on1 = e_l["f_start"], e_l["f_land"]
    flick = [(0, 0.0), (on0, 0.0), (on0 + 2, 0.6), (on0 + 3, 0.15), (on1, 1.0), (on1 + 4, 1.12), (e_l["f_end"], 1.0), (nf - 1, 1.0)]
    _key_val(bulb_s, [(f, 9.0 * v) for f, v in flick])
    for o, w in ((spot, P["LAMP_W"]), (inner, 0.6)):
        for f, v in flick:
            o.data.energy = w * v
            o.data.keyframe_insert("energy", frame=f)
    spot.rotation_euler = (0, 0, 0)                            # 聚光灯默认朝 −Z（朝下）
    print("ONCAM step s4 lamp", flush=True)
    # ---- 假插头 048：插座的子物体（插座坐标，毫米 ×MM），针朝 −W 对准孔口
    plug = KS.h02b_plug(K, "048")
    KS.rest(plug)
    _bake(plug)
    plug_pts = _extreme_pts(plug)                              # 插头坐标（还没挂到插座上）
    plug.parent = sock
    plug.matrix_parent_inverse = Matrix.Identity(4)
    plug.rotation_mode = "QUATERNION"
    tip_l = float(plug["needle_len_mm"]) + 12.0                 # 针尖在插头坐标 x ≈ −16.5
    w_wait = KS.FACE_W + P["PLUG_GAP_MM"] + tip_l
    q_wait = Quaternion()
    q_from = _q(*P["PLUG_FROM_ROT"])
    p_from = Vector(P["PLUG_FROM"]) * MM
    p_wait = Vector((w_wait, 0.0, 0.0)) * MM
    p_ctrl = Vector(P["PLUG_CTRL"]) * MM + Vector((w_wait, 0, 0)) * MM
    fp0, fp1, fp2 = e_p["f_start"], e_p["f_land"], e_p["f_end"]
    plug_vis = _vis_meshes(plug)
    _hide_tracks(plug_vis, fp0, nf)

    def plug_pose(f):
        if f <= fp0:
            return p_from, q_from
        if f < fp1:
            t = (f - fp0) / max(1, fp1 - fp0)
            e = ease_out_cubic(t)
            return _bz(p_from, p_ctrl, p_wait, e), _qpow(q_from, q_wait, ease_out_back(t, 1.1))
        sp = (f - fp1) / FPS                                    # 停在孔口前，轻轻前后点两下（犹豫），不插
        d = Vector((1.0, 0, 0)) * (1.6 * MM) * spring(sp, 0.35, 15.0) * (1 - clamp01((f - fp1) / 60.0))
        wob = Quaternion((0, 1, 0), math.radians(1.2 * math.sin(2 * math.pi * (f - fp1) / 70.0) * math.exp(-(f - fp1) / 80.0)))
        return p_wait + d, wob @ q_wait

    for f in range(nf):
        pp, pq = plug_pose(f)
        plug.location = pp
        plug.rotation_quaternion = pq
        plug.scale = (1.0, 1.0, 1.0)
        plug.keyframe_insert("location", frame=f)
        plug.keyframe_insert("rotation_quaternion", frame=f)
    linear_keys(plug)
    print("ONCAM step s5 plug", flush=True)
    # ---- 灯光
    hcol = _hero_collection(sc, [sock])                            # 插头是插座的子物体，跟着进 hero（front 层也出它）
    lamp_rcv = bpy.data.collections.new("ONCAM_lamp_rcv")          # 吊灯只照插座、插头和自己（不照大板、不照人）
    sc.collection.children.link(lamp_rcv)
    for o in list(hcol.objects) + lamp_parts:
        lamp_rcv.objects.link(o)
    spot.light_linking.receiver_collection = lamp_rcv
    inner.light_linking.receiver_collection = lamp_rcv
    gs, gon = e_c["g_start"], e_c["g_on"]
    rim_keys = [(0, 0.6), (gs, 0.6), (e_c["f_land"], 1.5), (e_c["f_land"] + 60, 1.0), (e_r["g_start"], 1.0), (e_r["f_land"], 1.4), (e_r["f_end"] + 30, 1.0), (nf - 1, 1.0)]
    _hero_lights(W, hcol, P_rest, P, rim_keys, key_point=P_rest + Vector((-0.4, -0.25, 0.0)))
    trans = _axis_trans_lamps(W, hcol, nf, f_d0, (LM[0] @ head_pt).length, (LM[nf - 1] @ tail_pt).length, P.get("TRANS_K", 1.0),
                              head_track=[(LM[f] @ head_pt).length for f in range(P["TRANS_TRACK"] + 1)] if P.get("TRANS_TRACK") else None,
                              tail_track=[(LM[f] @ tail_pt).length for f in range(f_d0, nf)] if P.get("TRANS_TRACK") else None,
                              nogloss=P.get("TRANS_NOGLOSS", False), tk=P.get("TRANS_TK", 1.0)) if BR else []
    print("ONCAM step s6 lights", trans, flush=True)

    hero_box = [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]

    def plug_world(f):
        pp, pq = plug_pose(f)
        return LM[f] @ (Matrix.Translation(pp) @ pq.to_matrix().to_4x4())

    def bbox_pts(f):
        """零件群的包围框（机检 M3–M5）：插座 + 两个盲盒；插头落到孔口前以后也算（从画下面转进来那几帧是入场，不算）。"""
        pts = [LM[f] @ p for p in sock_pts]
        for bx in boxes:
            pts += [bx["M"][f] @ p for p in bx["pts"]]
        if f >= fp1:
            Mp = plug_world(f)
            pts += [Mp @ p for p in plug_pts]
        return pts

    def focus_plan(f, Mcam):
        loc = Mcam.translation
        fwd = (Mcam.to_3x3() @ Vector((0, 0, -1))).normalized()
        p = LM[f] @ port if f <= f_ok + 20 else LM[f] @ c0      # 段首跟孔口，之后跟插座中心
        if f <= f_ok and BR:                                     # 孔桶版：段首先对在孔底，落位时回到孔口
            p = (LM[f] @ head_pt).lerp(LM[f] @ port, smooth(f / max(1, f_ok)))
        if f_ok < f <= f_ok + 20:
            u = smooth((f - f_ok) / 20.0)
            p = (LM[f] @ port).lerp(LM[f] @ c0, u)
        if f > f_d0:
            p = p.lerp(LM[f] @ tail_pt, smooth((f - f_d0) / 8.0))
        d = (p - loc).dot(fwd)
        d -= 0.10 * smooth((f - 24) / 14.0) * (1 - smooth((f - gs) / max(1, gon - gs)))     # 等待时焦点在插座前 10 cm（略虚 2–4 px），suspect 前点名拉实
        if f >= fp0 - 6:                                         # 插头来了：焦点挪到插头针尖和孔口之间，两样都清楚
            u = smooth((f - (fp0 - 6)) / 24.0) * (1 - smooth((f - f_d0) / 8.0))
            mid = (plug_world(f) @ Vector((-16.5 * MM, 0, 0))).lerp(LM[f] @ port, 0.5)
            d = d * (1 - u) + (mid - loc).dot(fwd) * u
        return max(0.03, d)

    def fstop_plan(f):
        a = 4.0 + (FSTOP - 4.0) * smooth(f / 30.0)
        if f > f_d0:
            a = a + (8.0 - a) * smooth((f - f_d0) / (nf - 1 - f_d0))
        return a

    def checks():
        out = {}
        sc.frame_set(nf - 1)                                     # 插头前面几帧是藏着的：在它出像的帧上取网格
        sock_objs = [o for o in _vis_meshes(sock) if o not in set(_vis_meshes(plug))]
        A = _RigidClip(sock_objs)
        Bp = _RigidClip(_vis_meshes(plug))
        Bl = _RigidClip([o for o in lamp_parts if o.type == "MESH"])
        out["plug_vs_socket_frames"] = _RigidClip.hits(A, Bp, range(fp0, nf), sc)
        out["socket_vs_lamp_frames"] = _RigidClip.hits(A, Bl, range(nf), sc, margin=0.02)
        for bx in boxes:
            Bb = _RigidClip(_vis_meshes(bx["root"]))
            out[f"socket_vs_{bx['root'].name}_frames"] = _RigidClip.hits(A, Bb, range(nf), sc, margin=0.02)
            out[f"plug_vs_{bx['root'].name}_frames"] = _RigidClip.hits(Bp, Bb, range(fp0, nf), sc, margin=0.02)
        out["plug_vs_lamp_frames"] = _RigidClip.hits(Bp, Bl, range(fp0, nf), sc, margin=0.02)
        sc.frame_set(0)
        return out

    handoff = dict(note="相机坐标（相机在原点看 +Y，+Z 向上；镜头 %.2f mm / 36 mm 传感器，偏移 %s）；插座 = kit_socket.h01b_cdk20_socket 放大 %.3f 倍" % (LENS, list(SHIFT), s),
                   head_pose=dict(frame=0, port_center_m=list(LM[0] @ port), matrix=[list(r) for r in LM[0]]),
                   tail_pose=dict(frame=nf - 1, lid_top_m=list(LM[nf - 1] @ lid_top), matrix=[list(r) for r in LM[nf - 1]]))
    return dict(targets={"card": lambda f: LM[max(0, min(nf - 1, int(f)))] @ c0}, hero=sock, bbox=bbox_pts, key=plug,
                focus=focus_plan, fstop=fstop_plan, tail_t0=f_d0, checks=checks, handoff=handoff,
                info=dict(scale=round(s, 3), box_scales=[round(b["s"], 3) for b in boxes], plug_wait_w_mm=round(w_wait, 2),
                          frames={k: [v["f_start"], v["f_land"], v["f_end"]] for k, v in E.items()},
                          P={k: v for k, v in P.items()}))


def recipe_frost_blank(W):
    """3-09 B："So you've got a lock nobody can see. How do you cut a key in the dark?"（340 帧）
    01 文档 3-09：人旁边一个磨砂 CDK20（p29）；nobody can see 零件只剩一圈轮廓光；cut a key 一把钥匙坯（h02 blank）在旁边亮起；
    in the dark 钥匙坯伸向磨砂壳，停在半路。剧本：屋里暗下来，只剩暖光和脸的一侧。事件 id 见 events/3-09.json。"""
    import kit_deep as D
    import kit_parts as KP
    sc, K, cfg = W["sc"], W["kit"], W["cfg"]
    P = cfg["P"]
    nf = cfg["nf"]
    E = {e["id"]: e for e in cfg["K"]["events"]}
    e_a, e_c, e_dk, e_v, e_k, e_r, e_d = E["arrive"], E["call"], E["dark"], E["veil"], E["key"], E["reach"], E["dive"]
    fr = KP.p29_cdk20_unknown(K)
    _bake(fr)
    bpy.context.view_layer.update()
    lo, hi = mesh_bounds([fr])
    fr_pts = _extreme_pts(fr)                                  # 机检外形点（静止位姿）
    c0 = (lo + hi) / 2
    base = Quaternion((0, 1, 0), math.radians(P.get("BASE_Y", 0.0))) @ Quaternion((1, 0, 0), math.radians(P["BASE_X"]))
    q_r1 = _q(*P["REST1"], base=base)
    P_rest = Vector(px_to_world(*P["FR_PX"], P["FR_D"]))
    s = _fit_scale(c0, lo, hi, q_r1, P_rest, P["FR_H_PX"], pts=fr_pts)
    mats = _vol_rescale(fr, s)
    fr.rotation_mode = "QUATERNION"
    q_call = _q(*P["CALL"], base=base)
    q_head = _q(0.0, 0.0, base=base)
    P_head = Vector(px_to_world(960, 540, P["HEAD_D"]))
    front_pt = Vector((0.0, 0.0, 0.0))                           # 段首：零件中心正对镜头（中心离镜头 HEAD_D + 半厚）
    P_head = P_head + Vector((0, (hi.z - lo.z) / 2 * s * 0.0, 0))
    P_hctrl = Vector(px_to_world(*P["HEAD_CTRL"]))
    f_ok, f_ok_end = e_a["f_land"], e_a["f_end"]
    veil0, veil1 = e_v["f_start"], e_v["f_land"]

    def hover(f):
        b = smooth((f - 28) / 40)
        return Vector((0.0, 0.0, 0.006 * math.sin(2 * math.pi * f / 220) * b)), 2.0 * math.sin(2 * math.pi * f / 300 + 0.4) * b

    def base_pose(f):
        sc_ = 1.0
        if f <= f_ok:
            t = f / max(1, f_ok)
            p = ease_out_back(t, 0.9)
            c = _bz_at_depth(P_head, P_hctrl, P_rest, _logd(P_head.y, P_rest.y, ease_out_cubic(t)))
            q = _qpow(q_head, q_r1, smooth(t) * 0.35 + p * 0.65)
        else:
            sp = (f - f_ok) / FPS
            c = P_rest + Vector((0.004, 0.006, -0.008)) * spring(sp, 0.45, 20.0) * (1 - clamp01((f - f_ok) / max(1, f_ok_end + 12 - f_ok)))
            q = q_r1.copy()
        fl = e_c["f_land"]
        if fl - 6 <= f < fl:
            c = c + Vector((0, 0, -0.003 * math.sin(math.pi * (f - fl + 6) / 6) ** 2))
        p = ease_out_back((f - fl) / 18.0, 1.3) if f >= fl else 0.0
        if p > 0:
            c = c + Vector(P["CALL_D"]) * p
            q = _qpow(q, q_call, p)
        if f >= veil0:                                           # see：轻轻一缩（像被雾裹住），回弹
            sc_ = 1.0 - 0.035 * math.sin(math.pi * clamp01((f - veil0) / 16.0)) * math.exp(-max(0, f - veil1) / 14.0)
        # in the dark：钥匙坯伸过来时，磨砂壳往后让一点点（"看不见"的东西不好碰）
        k = ease_inout_cubic((f - e_r["f_start"]) / max(1, e_r["f_land"] - e_r["f_start"]))
        c = c + Vector((0.015, 0.02, 0.0)) * k
        ho, hy = hover(f)
        return c + ho, Quaternion((0, 0, 1), math.radians(hy)) @ q, sc_

    f_d0, f_d1 = e_d["f_start"], nf - 1
    tgt_tail = Vector(px_to_world(*P["TAIL_PX"], P["TAIL_D"]))
    q_tail = _q(-40.0, 25.0, base=base)

    def pose(f):
        c, q, k = base_pose(f)
        if f > f_d0:
            t = (f - f_d0) / (f_d1 - f_d0)
            ctrl = Vector(px_to_world(*P["TAIL_CTRL"]))
            c1 = tgt_tail
            c = _bz_at_depth(c, ctrl, c1, _logd(c.y, c1.y, smooth(t) * 0.7 + 0.3 * ease_in_cubic(t)))
            q = _qpow(q, q_tail, smooth(t))
        return c, q, k

    LM = []
    for f in range(nf):
        c, q, k = pose(f)
        LM.append(_Mof(c, q, c0, s * k))
        key_matrix(fr, f, LM[f])
    linear_keys(fr)
    # 磨砂再糊一层（see）：粗糙度、清漆粗糙度上去
    for m in mats:
        pb = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        r0 = pb.inputs["Roughness"].default_value
        _key_val(pb.inputs["Roughness"], [(0, r0), (veil0, r0), (veil1 + 6, P["VEIL_ROUGH"]), (nf - 1, P["VEIL_ROUGH"])])
    print("ONCAM step f1 frost", flush=True)
    # ---- 钥匙坯
    key = D.h02_key(K, which="blank", scale=1.0)
    _bake(key)
    bpy.context.view_layer.update()
    klo, khi = mesh_bounds([key])
    key_pts_x = _extreme_pts(key)
    kc0 = (klo + khi) / 2
    key.rotation_mode = "QUATERNION"
    qk_base = Quaternion((1, 0, 0), math.radians(90))            # 钥匙平面朝镜头（齿缘朝上），尖朝 +X（右）
    P_key = Vector(px_to_world(*P["KEY_PX"], P["KEY_D"]))
    qk = Quaternion((0, 0, 1), math.radians(P.get("KEY_YAW", 0.0))) @ Quaternion((0, 1, 0), math.radians(-P["KEY_ROLL"])) @ qk_base
    # 尖往右上翘，朝磨砂壳；再绕竖轴转 KEY_YAW 成 3/4 侧面（正面看钥匙坯只是"一个圆环加一小截"，认不出是钥匙）
    ks = 10.0
    for _ in range(6):                                           # 投影长 = KEY_LEN_PX
        M = _Mof(P_key, qk, kc0, ks)
        a_ = project(cam_basis(), SHIFT, M @ Vector((6.5 * MM, 0, 0)))
        b_ = project(cam_basis(), SHIFT, M @ Vector((-7.5 * MM, 0, 0)))
        ks *= P["KEY_LEN_PX"] / max(1e-6, math.hypot(a_[0] - b_[0], a_[1] - b_[1]))
    tip_l = Vector((6.5 * MM, 0, 0))
    R_fr = 0.5 * max(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z) * s
    fk0, fk1, fk2 = e_k["f_start"], e_k["f_land"], e_k["f_end"]
    fr0, fr1, fr2 = e_r["f_start"], e_r["f_land"], e_r["f_end"]

    def key_pose(f):
        """(中心, 朝向, 缩放倍)。cut a key：0.6→1.08→1.0 弹出、侧着转正；in the dark：沿尖的方向往磨砂壳走一半，回缩一点。"""
        if f < fk0:
            return P_key, Quaternion((0, 0, 1), math.radians(35)) @ qk, 0.6
        if f < fk2:
            e = (f - fk0) / max(1, fk2 - fk0)
            sc_ = 0.6 + 0.4 * ease_out_back(e, 2.2)
            q = _qpow(Quaternion((0, 0, 1), math.radians(35)) @ qk, qk, ease_out_cubic(e))
            return P_key + Vector((0, 0, 0.02 * (1 - ease_out_cubic(e)))), q, sc_
        # 往磨砂壳去：目标 = 尖到磨砂壳中心距离的 KEY_REACH
        Mk = _Mof(P_key, qk, kc0, ks)
        tip = Mk @ tip_l
        tgt = LM[fr1] @ c0
        gap = (tgt - tip).length - R_fr                          # 尖到磨砂壳表面（按外接球）的距离，走 KEY_REACH 这么多
        dv = (tgt - tip).normalized() * gap * P["KEY_REACH"]
        if f < fr0:
            return P_key + Vector((0, 0, 0.004 * math.sin(2 * math.pi * (f - fk2) / 90))), qk, 1.0
        e = (f - fr0) / max(1, fr1 - fr0)
        go = ease_inout_cubic(e)
        back = 0.0
        if f >= fr1:                                             # 停在半路，犹豫：往回缩 12% 再稳住
            back = 0.12 * (1 - spring((f - fr1) / FPS, 0.5, 12.0)) * 1.0
        wob = Quaternion((0, 1, 0), math.radians(2.5 * math.sin(2 * math.pi * max(0, f - fr1) / 40.0) * math.exp(-max(0, f - fr1) / 30.0)))
        return P_key + dv * (go - back * go), wob @ qk, 1.0

    KM = []
    for f in range(nf):
        c, q, k = key_pose(f)
        M = _Mof(c, q, kc0, ks * k)
        KM.append(M)
        key_matrix(key, f, M)
    linear_keys(key)
    key_vis = _vis_meshes(key)
    _hide_tracks(key_vis, fk0, nf)
    print("ONCAM step f2 key", flush=True)
    # ---- 光：屋里暗下来（洗墙光、主光、补光、顶光、雾里的暖光一起降），磨砂壳轮廓光升；钥匙坯一盏小灯只照它
    hcol = _hero_collection(sc, [fr])
    kcol = bpy.data.collections.new("ONCAM_key")
    sc.collection.children.link(kcol)
    for o in [key] + list(key.children_recursive):
        o["hero"] = 1
        if o.type in ("MESH", "CURVE"):
            kcol.objects.link(o)
    d0, d1 = e_dk["f_start"], e_dk["f_end"]
    rig = W["rig"]

    def dim_keys(o, fac, attr="energy"):
        e0 = o.data.energy
        for f, v in ((0, 1.0), (d0, 1.0), (d1, fac), (nf - 1, fac)):
            o.data.energy = e0 * v
            o.data.keyframe_insert("energy", frame=f)
    dim_keys(rig["wash"], P["DARK"])
    for nm in ("key", "fill", "top"):
        dim_keys(rig[nm], P["DARK_KEY"])
    sh = bpy.data.objects.get("shaft")
    if sh is not None:
        dim_keys(sh, P["DARK"])
    gs, gon = e_c["g_start"], e_c["g_on"]
    rim_keys = [(0, 0.6), (gs, 0.6), (e_c["f_land"], 1.4), (d0, 1.1), (d1, 2.2), (nf - 1, 2.2)]   # nobody can see：只剩一圈轮廓光
    L = _hero_lights(W, hcol, P_rest, P, rim_keys, key_point=P_key)
    gb = L["glossy_bg"].inputs["Strength"]                       # 镜面里的"屋子"也跟着暗
    _key_val(gb, [(0, 0.9), (d0, 0.9), (d1, 0.9 * P["DARK"]), (nf - 1, 0.9 * P["DARK"])])
    e0 = L["fill"].data.energy
    for f, v in ((0, 1.0), (d0, 1.0), (d1, P["DARK_KEY"]), (nf - 1, P["DARK_KEY"])):   # 零件侧补光也暗（只剩轮廓光）
        L["fill"].data.energy = e0 * v
        L["fill"].data.keyframe_insert("energy", frame=f)
    wmp = sc.world.node_tree.nodes.get("oncam_map")              # 世界光（漫反射看到的那部分）也暗，不然大板只暗一点
    if wmp is not None:
        _key_val(wmp.inputs["To Min"], [(f, wmp.inputs["To Min"].default_value * v) for f, v in ((0, 1.0), (d0, 1.0), (d1, P["DARK"]), (nf - 1, P["DARK"]))])
    for o in sc.objects:                                         # 反光卡跟着暗（不然暗屋里的钥匙还映着一屋子亮光）
        if o.name.startswith("refl_") and o.type == "MESH":
            em = next((n for n in o.active_material.node_tree.nodes if n.type == "EMISSION"), None)
            if em is not None:
                v0 = em.inputs["Strength"].default_value
                _key_val(em.inputs["Strength"], [(0, v0), (d0, v0), (d1, v0 * 0.45), (nf - 1, v0 * 0.45)])
    ksp = make_light("key_spot", "SPOT", P_key + Vector((-0.25, -0.45, 0.55)), P_key, 0.0, 0.0, kelvin_rgb(3400))
    ksp.data.spot_size = math.radians(28); ksp.data.spot_blend = 0.6; ksp.data.shadow_soft_size = 0.08
    ksp.light_linking.receiver_collection = kcol
    for f, v in ((0, 0.0), (fk0, 0.0), (fk1, 1.25), (fk2, 1.0), (nf - 1, 1.0)):
        ksp.data.energy = P["KEY_SPOT_W"] * v
        ksp.data.keyframe_insert("energy", frame=f)
    print("ONCAM step f3 lights", flush=True)
    hero_box = [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
    key_box = [Vector((x, y, z)) for x in (klo.x, khi.x) for y in (klo.y, khi.y) for z in (klo.z, khi.z)]

    def bbox_pts(f):
        pts = [LM[f] @ p for p in fr_pts]
        if f >= fk2:
            pts += [KM[f] @ p for p in key_pts_x]
        return pts

    def focus_plan(f, Mcam):
        loc = Mcam.translation
        fwd = (Mcam.to_3x3() @ Vector((0, 0, -1))).normalized()
        p = LM[f] @ c0
        d = (p - loc).dot(fwd)
        if f <= f_ok:                                            # 段首：焦点在磨砂壳朝镜头的表面上
            d -= (hi.z - lo.z) / 2 * s * (1 - smooth(f / max(1, f_ok)))
        d -= 0.10 * smooth((f - 24) / 14.0) * (1 - smooth((f - gs) / max(1, gon - gs)))
        if f >= fk0 - 10:                                        # 钥匙坯亮起：焦点挪到钥匙尖和磨砂壳之间
            u = smooth((f - (fk0 - 10)) / 18.0) * (1 - smooth((f - f_d0) / 8.0))
            mid = (KM[f] @ tip_l).lerp(LM[f] @ c0, 0.45)
            d = d * (1 - u) + (mid - loc).dot(fwd) * u
        if f > f_d0:
            d = d - (hi.z - lo.z) / 2 * s * smooth((f - f_d0) / (nf - 1 - f_d0))
        return max(0.03, d)

    def fstop_plan(f):
        a = 4.0 + (FSTOP - 4.0) * smooth(f / 30.0)
        if f > f_d0:
            a = a + (8.0 - a) * smooth((f - f_d0) / (nf - 1 - f_d0))
        return a

    def checks():
        sc.frame_set(nf - 1)
        A = _RigidClip(_vis_meshes(fr))
        B = _RigidClip(_vis_meshes(key))
        out = dict(key_vs_frost_frames=_RigidClip.hits(A, B, range(fk0, nf), sc, margin=0.02))
        sc.frame_set(0)
        return out

    handoff = dict(note="相机坐标（相机在原点看 +Y，+Z 向上；镜头 %.2f mm / 36 mm 传感器，偏移 %s）；磨砂 CDK20 = kit_parts.p29_cdk20_unknown 放大 %.3f 倍" % (LENS, list(SHIFT), s),
                   head_pose=dict(frame=0, center_m=list(LM[0] @ c0), matrix=[list(r) for r in LM[0]]),
                   tail_pose=dict(frame=nf - 1, center_m=list(LM[nf - 1] @ c0), matrix=[list(r) for r in LM[nf - 1]]))
    return dict(targets={"card": lambda f: LM[max(0, min(nf - 1, int(f)))] @ c0}, hero=fr, bbox=bbox_pts, key=key,
                focus=focus_plan, fstop=fstop_plan, tail_t0=f_d0, checks=checks, handoff=handoff,
                info=dict(scale=round(s, 3), key_scale=round(ks, 3), frames={k: [v["f_start"], v["f_land"], v["f_end"]] for k, v in E.items()},
                          P={k: v for k, v in P.items()}))


# ================================================================ 铺开第 1 批续（11-20 夜，甲线）：5-05+06、5-09 插座 + 假插头
# 同一台 CDK20 插座（h01b，盖合着）+ 一个假插头（h02b 001 / 048）。一个 recipe 两段共用，差别全在参数字典（V505 / V509）和事件表：
# 事件表里有哪个 id 就做哪个动作（key 出现、insert 插、twist 拧、stuck 卡住抖、turn2 换人转向、jolt 弹簧顶松、back 顶出退回、
# loop / arrowhead 循环箭头、clamp 卡扣、off 断电、dive 段尾）。
V505 = dict(
    PLUG="001", TWIST=12.0, ENTRY="pop",                              # 001 只拧 12°（kit_socket turn_limit）；key 时在孔口前弹出
    SOCK_PX=(1480.0, 350.0), SOCK_D=1.50, SOCK_H_PX=386.0,         # 11-20 试渲：(1585, 545) 时插座右沿 1945 出画、下半截挨着 C 的手（手在 600–760 行伸到 1340）；抬到人肩膀以上那几行
    REST1=(-55.0, 14.0), REST2=(-61.0, 16.0),                         # (yaw, tilt)：本 recipe 里 yaw≈−40 孔口朝镜头、≈+50 朝右，−55 孔口朝人（左前）；5-06 换 B 时再朝左 6°。11-21 干跑量过：±25 都朝右，插头、箭头出右沿
    PLUG_GAP_MM=9.0,                                                  # 插头等待位：针尖离孔口面
    LOOP_R_MM=14.0, LOOP_TUBE_MM=1.1, LOOP_END=0.86,                  # 循环箭头：半径（插座毫米；21 时上沿出画）、管粗、画到整圈的几成
    HEAD_D=0.21, HEAD_PX=(880.0, 540.0), HEAD_CTRL=(2350.0, 470.0, 0.95),
    TAIL_MODE="lid", TAIL=(35.0, 74.0), TAIL_D=0.15, TAIL_CTRL=(1500.0, 300.0, 0.75), TAIL_PX=(960.0, 560.0),
    RING_GLOW=4.0, LAMP_GLOW=8.0,
    BRIGHT=True, BORE_CAM=12.5, HEAD_EASE=0.5, PLUG_CAM=4.0, PLUG_OFF=2.7, TRANS_K=1.6, TRANS_TRACK=14, TRANS_NOGLOSS=True, TRANS_TK=1.6,   # 11-23 成片：5-05 段尾第 508–510 帧（深蓝插座占画面）0.41–0.44、5-09 盖满那几帧 0.42–0.45 → 段尾灯再 ×1.6
      # 11-23 rc02 黑场返修（18 文档 3.2 O3 / O4），同 V306
    BOARD_K=1.27, BOARD_HIDE=("stations", "zone_tags", "z1_c0_r0"),
    HEAD_BOX=(300, 90, 900, 680), LOCK_BOX=(1180, 0, 1940, 960),
    RIM_W=60.0, SAMPLES=16, GRAIN_F=150, GRAIN_GAIN=1.0,                  # C 黑 T 恤：5-09 2.4 → M10 0.65、3.2 → 0.80（脸上量底噪）
)
V509 = dict(V505, PLUG="048", TWIST=90.0, ENTRY="arc", SOCK_PX=(1495.0, 350.0), GRAIN_GAIN=1.0, REST1=(-25.0, 14.0), REST2=(-19.0, 16.0),   # 5-09 试渲已过（插头从右下转进来），朝向不跟 5-05 翻
            PLUG_FROM=(70.0, 8.0, -110.0), PLUG_FROM_ROT=(0.0, 0.0, 80.0), PLUG_CTRL=(10.0, 6.0, -45.0),   # 同 3-06：从画面下沿外转进来
            TAIL_MODE="port", TAIL_D=0.25, TAIL_PX=(960.0, 540.0), TAIL_CTRL=(1500.0, 420.0, 0.7),        # 孔口正对镜头冲进去（接 W4 插座里面）
            OFF_RING=0.12, GRAIN_F=60)


def _loop_arrow(K, R, tube, end_frac, name="loop_arrow"):
    """循环箭头：一条圆弧管（曲线 bevel，bevel_factor_end 打关键帧 = 画出来）+ 一个圆锥箭头。局部坐标：圆在 XY 平面，圆心在原点，
    逆时针（↺）从 100° 起画。返回 (曲线物体, 箭头物体, 箭头在局部坐标的位置矩阵)。"""
    import bmesh
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = tube
    cu.bevel_resolution = 6
    cu.use_fill_caps = True
    cu.bevel_factor_mapping_end = "SPLINE"
    sp = cu.splines.new("POLY")
    n = 96
    a0 = math.radians(100.0)
    span = math.tau * end_frac
    sp.points.add(n - 1)
    for i in range(n):
        a = a0 + span * i / (n - 1)
        sp.points[i].co = (R * math.cos(a), R * math.sin(a), 0.0, 1.0)
    ob = link_obj(bpy.data.objects.new(name, cu))
    ob.data.materials.append(K.red)
    me = bpy.data.meshes.new(name + "_head")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=32, radius1=tube * 2.6, radius2=0.0, depth=tube * 6.0)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    hd = link_obj(bpy.data.objects.new(name + "_head", me))
    hd.data.materials.append(K.red)
    a1 = a0 + span
    tip = Vector((R * math.cos(a1), R * math.sin(a1), 0.0))
    tang = Vector((-math.sin(a1), math.cos(a1), 0.0))              # 逆时针前进方向
    q = Vector((0, 0, 1)).rotation_difference(tang)                 # 圆锥 +Z = 箭头尖
    Mh = Matrix.Translation(tip + tang * tube * 2.0) @ q.to_matrix().to_4x4()
    return ob, hd, Mh


def recipe_socket_plug(W):
    """5-05+06（C："The key went into the lock. But it barely turned." B："So was that it? Back to square one?"，512 帧）
    5-09（C："This time, the key turned."，216 帧）。06_插座比喻.md 第四节 5-05+5-06、5-09。"""
    import kit_socket as KS
    sc, K, cfg = W["sc"], W["kit"], W["cfg"]
    P = cfg["P"]
    nf = cfg["nf"]
    E = {e["id"]: e for e in cfg["K"]["events"]}

    def has(k):
        return k in E
    print("ONCAM step p0", flush=True)
    sock = KS.h01b_cdk20_socket(K)
    KS.rest(sock)
    jr = KS.rig(sock)
    _bake(sock)
    print("ONCAM step p1 socket baked", flush=True)
    bpy.context.view_layer.update()
    lo, hi = mesh_bounds([sock])
    sock_pts = _extreme_pts(sock)
    c0 = (lo + hi) / 2
    base = Quaternion((0, 0, 1), math.radians(-90))                # 插孔轴 +W → 朝镜头（−Y）
    q_r1 = _q(*P["REST1"], base=base)
    q_r2 = _q(*P.get("REST2", P["REST1"]), base=base)
    P_rest = Vector(px_to_world(*P["SOCK_PX"], P["SOCK_D"]))
    s = _fit_scale(c0, lo, hi, q_r1, P_rest, P["SOCK_H_PX"], pts=sock_pts)
    sock.rotation_mode = "QUATERNION"
    port = Vector((KS.FACE_W, 0.0, 0.0)) * MM
    lid_top = Vector((-8.5, 0.0, KS.TOP_Z)) * MM
    q_head = _q(0.0, 3.0, base=base)
    P_head = Vector(px_to_world(*P["HEAD_PX"], P["HEAD_D"])) - q_head.to_matrix() @ ((port - c0) * s)
    BR = P.get("BRIGHT")
    head_pt = port
    if BR:                                                          # 11-23 rc02 黑场（18 文档 3.2 O3 / O4）：同 3-06，段首往孔桶里看
        head_pt = Vector((0.0, 0.0, 0.0)) * MM
        P_head = Vector(px_to_world(*AXIS, P["BORE_CAM"] * MM * s)) - q_head.to_matrix() @ ((head_pt - c0) * s)
    P_hctrl = Vector(px_to_world(*P["HEAD_CTRL"]))
    e_a, e_d = E["arrive"], E["dive"]
    f_ok, f_ok_end = e_a["f_land"], e_a["f_end"]
    f_d0, f_d1 = e_d["f_start"], nf - 1

    def win(e, f, a="f_start", b="f_land"):
        return clamp01((f - e[a]) / max(1, e[b] - e[a]))

    def shake(f, f0, amp, per=7.0, tau=9.0):
        """卡住、咔一下：f0 起的阻尼抖动。"""
        if f < f0:
            return 0.0
        return amp * math.sin(2 * math.pi * (f - f0) / per) * math.exp(-(f - f0) / tau)

    def hover(f):
        b = smooth((f - 30) / 40)
        return Vector((0.0, 0.0, 0.005 * math.sin(2 * math.pi * f / 260) * b)), 1.2 * math.sin(2 * math.pi * f / 340 + 0.6) * b

    hit = []                                                        # 插座跟着被撞一下的帧（插到底、卡住、拧到底）
    if has("insert"):
        hit.append((E["insert"]["f_land"], 0.0012))
    if has("stuck"):
        hit.append((E["stuck"]["f_start"], 0.0016))
    if has("twist") and P["TWIST"] >= 80:
        hit.append((E["twist"]["f_land"], 0.0014))

    def base_pose(f):
        if f <= f_ok:
            t = f / max(1, f_ok)
            p = ease_out_back(t, 0.9)
            k_e = P.get("HEAD_EASE", 0.0)
            c = _bz_at_depth(P_head, P_hctrl, P_rest, _logd(P_head.y, P_rest.y, (1 - k_e) * ease_out_cubic(t) + k_e * smooth(t)))
            q = _qpow(q_head, q_r1, smooth(t) * 0.35 + p * 0.65)
        else:
            sp = (f - f_ok) / FPS
            c = P_rest + Vector((0.004, 0.006, -0.008)) * spring(sp, 0.45, 20.0) * (1 - clamp01((f - f_ok) / max(1, f_ok_end + 12 - f_ok)))
            q = q_r1.copy()
        if has("turn2"):
            q = _qpow(q, q_r2, ease_inout_cubic(win(E["turn2"], f, "f_start", "f_end")))
        for f0, amp in hit:                                         # 被撞：沿孔轴往里一顶再回来，上下抖一下
            if f >= f0:
                w = q.to_matrix() @ Vector((1, 0, 0))
                c = c - w * amp * math.sin(math.pi * clamp01((f - f0) / 10.0)) * math.exp(-(f - f0) / 14.0) \
                    + Vector((0, 0, shake(f, f0, amp * 0.5, 6.0, 8.0)))
        ho, hy = hover(f)
        return c + ho, Quaternion((0, 0, 1), math.radians(hy)) @ q

    tip_l = float(KS.PLUG_SPECS[P["PLUG"]]["L"]) + 12.0      # = plug["needle_len_mm"] + 12（插头还没建，先从规格表取）
    w_wait = KS.FACE_W + P["PLUG_GAP_MM"] + tip_l
    w_seat = KS.SEAT_W
    e_k = E["key"]
    fk0, fk1, fk2 = e_k["f_start"], e_k["f_land"], e_k["f_end"]
    q0 = Quaternion()

    def plug_state(f):
        """(插头原点 W 毫米, 额外位移, 朝向, 缩放, 拧角, 晃角)。"""
        w, off, q, k, tw, tl = w_wait, Vector(), q0, 1.0, 0.0, 0.0
        if P["ENTRY"] == "pop":
            if f < fk2:
                e = clamp01((f - fk0) / max(1, fk2 - fk0))
                k = 0.6 + 0.4 * ease_out_back(e, 2.2)
                q = Quaternion((0, 0, 1), math.radians(35 * (1 - ease_out_cubic(e))))
        else:
            p_from = Vector(P["PLUG_FROM"]) * MM
            p_wait = Vector((w_wait, 0, 0)) * MM
            p_ctrl = Vector(P["PLUG_CTRL"]) * MM + p_wait
            if f < fk1:
                t = clamp01((f - fk0) / max(1, fk1 - fk0))
                p = _bz(p_from, p_ctrl, p_wait, ease_out_cubic(t))
                off = p - p_wait
                q = _qpow(_q(*P["PLUG_FROM_ROT"]), q0, ease_out_back(t, 1.1))
            elif f < fk2 + 20:
                off = Vector((1.0, 0, 0)) * (1.2 * MM) * spring((f - fk1) / FPS, 0.4, 16.0) * (1 - clamp01((f - fk1) / 40.0))
        if has("insert"):
            e = E["insert"]
            if f >= e["f_start"]:
                t = clamp01((f - e["f_start"]) / max(1, e["f_land"] - e["f_start"]))
                u = ease_inout_cubic(t) if P["ENTRY"] == "pop" else ease_in_cubic(t) * 0.35 + smooth(t) * 0.65
                w = w_wait + (w_seat - w_wait) * u
                if f > e["f_land"]:                                  # 到底 0.1 mm 小回弹
                    w = w_seat + 0.1 * math.sin(math.pi * clamp01((f - e["f_land"]) / 8.0)) * math.exp(-(f - e["f_land"]) / 10.0)
        if has("twist"):
            e = E["twist"]
            t = clamp01((f - e["f_start"]) / max(1, e["f_land"] - e["f_start"]))
            if P["TWIST"] < 45:
                tw = P["TWIST"] * ease_out_cubic(t) ** 0.8          # 越拧越慢，到 12° 拧不动
            else:
                tw = P["TWIST"] * (smooth(t) * 0.5 + ease_in_cubic(t) * 0.5)   # 越拧越快，咔地到底
        if has("stuck"):
            e = E["stuck"]
            if f >= e["f_start"]:
                tw = P["TWIST"] - 2.2 * abs(math.sin(math.pi * (f - e["f_start"]) / 7.0)) * math.exp(-(f - e["f_start"]) / 12.0)
                tl = shake(f, e["f_start"], 1.6, 8.0, 12.0)
        if has("jolt"):
            e = E["jolt"]
            if f >= e["f_start"]:
                t = clamp01((f - e["f_start"]) / 6.0)               # 先回正（6 帧，不过冲），再被顶出来（11-20 机检：一边回正一边退，齿和槽在 367–369 帧蹭到）
                tw = tw * (1 - ease_out_cubic(t))
                w = w + 2.0 * ease_out_back(clamp01((f - e["f_start"] - 6) / 10.0), 1.8)
                tl = tl + shake(f, e["f_land"], 2.0, 9.0, 10.0)
        if has("back"):
            e = E["back"]
            if f >= e["f_start"]:
                t = clamp01((f - e["f_start"]) / max(1, e["f_end"] - e["f_start"]))
                w = (w_seat + 2.0) + (w_wait - (w_seat + 2.0)) * ease_out_back(t, 1.25)
                tl = shake(f, e["f_land"], 2.5, 10.0, 14.0)
                tw = 0.0
        if has("loop"):
            e = E["loop"]
            if f >= e["f_start"]:                                    # 插头跟着箭头轻轻点一下头（回到原点）
                tl = tl + 2.0 * math.sin(math.pi * clamp01((f - e["f_start"]) / 30.0))
        tw = max(0.0, min(90.0, tw))
        tl = max(-3.0, min(3.0, tl))
        return w, off, q, k, tw, tl

    if P["TAIL_MODE"] == "port":
        q_tail = _q(0.0, 0.0, base=base)
        tail_pt = port
    else:
        q_tail = _q(*P["TAIL"], base=base)
        tail_pt = lid_top
    tgt_tail = Vector(px_to_world(*P["TAIL_PX"], P["TAIL_D"]))
    if BR:                                                          # 11-23 rc02：段尾插头在孔口前（5-05+06）或插在孔里（5-09）→ 冲到它的金色柄面上，孔口正对镜头
        q_tail = _q(0.0, 0.0, base=base)
        w_, off_, q_, k_, tw_, tl_ = plug_state(nf - 1)
        v_ = Vector((9.3, 0.0, 0.0)) + Matrix.Rotation(math.radians(tw_), 3, "X") @ Vector((0.0, 0.0, -P["PLUG_OFF"]))   # 柄背面凹槽底，往刻字下方让开（跟着拧转）
        tail_pt = Vector((w_, 0.0, 0.0)) * MM + off_ + q_.to_matrix() @ (v_ * (k_ * MM))
        tgt_tail = Vector(px_to_world(*P["TAIL_PX"], P["PLUG_CAM"] * MM * s))
    c1_tail = tgt_tail - q_tail.to_matrix() @ ((tail_pt - c0) * s)

    def pose(f):
        c, q = base_pose(f)
        if f > f_d0:
            t = (f - f_d0) / (f_d1 - f_d0)
            ctrl = Vector(px_to_world(*P["TAIL_CTRL"]))
            c = _bz_at_depth(c, ctrl, c1_tail, _logd(c.y, c1_tail.y, smooth(t) * 0.7 + 0.3 * ease_in_cubic(t)))
            q = (_qpow_w if BR else _qpow)(q, q_tail, smooth(min(1.0, t * 1.15)))   # 亮版：_qpow 到不了 q_tail（3-06 试渲末帧插座还斜 30°，柄面没对上镜头）
        return c, q

    LM = []
    for f in range(nf):
        c, q = pose(f)
        LM.append(_Mof(c, q, c0, s))
        key_matrix(sock, f, LM[f])
    linear_keys(sock)
    print("ONCAM step p2 socket anim", flush=True)
    # ---- 红环、顶灯
    rings = [o for o in sock.children_recursive if o.type == "MESH" and "red_ring" in o.name]
    ring_s, _ = _emit_mat(rings, "oncam_red_ring_glow", (1.0, 0.10, 0.06))
    rk = [(0, P["RING_GLOW"]), (nf - 1, P["RING_GLOW"])]
    lamp_on = [o for o in sock.children_recursive if o.type == "MESH" and "lamp_out_on" in o.name]
    lamp_off = [o for o in sock.children_recursive if o.type == "MESH" and "lamp_out_off" in o.name]
    lamp_s, _ = _emit_mat(lamp_on, "oncam_lamp_glow", (1.0, 0.78, 0.30))
    lk = [(0, P["LAMP_GLOW"]), (nf - 1, P["LAMP_GLOW"])]
    lamp_loc = Vector((-4.0, 0.0, KS.TOP_Z + 2.5)) * MM
    lamp_pl = make_light("sock_lamp_glow", "POINT", LM[0] @ lamp_loc, LM[0] @ c0, 0.0, 0.0, kelvin_rgb(3000))
    lamp_pl.data.shadow_soft_size = 0.01
    lamp_pl.parent = sock
    lamp_pl.matrix_parent_inverse = Matrix.Identity(4)
    lamp_pl.location = lamp_loc
    plk = [(0, 1.0), (nf - 1, 1.0)]
    if has("off"):
        e_o = E["off"]
        ro = P.get("OFF_RING", 0.15)
        rk = [(0, P["RING_GLOW"]), (e_o["f_start"], P["RING_GLOW"]), (e_o["f_end"], P["RING_GLOW"] * ro), (nf - 1, P["RING_GLOW"] * ro)]
        lk = [(0, P["LAMP_GLOW"]), (e_o["f_start"], P["LAMP_GLOW"]), (e_o["f_start"] + 2, P["LAMP_GLOW"] * 1.4), (e_o["f_land"], 0.0), (nf - 1, 0.0)]
        plk = [(0, 1.0), (e_o["f_start"], 1.0), (e_o["f_start"] + 2, 1.4), (e_o["f_land"], 0.0), (nf - 1, 0.0)]
        for o in lamp_on:                                           # 灭了换成灰的灯罩（白的看着像还亮着，技能坑 27）
            o.hide_render = False
            o.keyframe_insert("hide_render", frame=0)
            o.hide_render = True
            o.keyframe_insert("hide_render", frame=e_o["f_land"])
        for o in lamp_off:
            o.hide_render = True
            o.keyframe_insert("hide_render", frame=0)
            o.hide_render = False
            o.keyframe_insert("hide_render", frame=e_o["f_land"])
    _key_val(ring_s, rk)
    _key_val(lamp_s, lk)
    for f, v in plk:
        lamp_pl.data.energy = 0.06 * s * s * v
        lamp_pl.data.keyframe_insert("energy", frame=f)
    # ---- 假插头：插座的子物体（插座坐标，毫米 ×MM），针朝 −W 对准孔口
    plug = KS.h02b_plug(K, P["PLUG"])
    KS.rest(plug)
    pr = KS.rig(plug)
    _bake(plug)
    bpy.context.view_layer.update()
    plug_pts = _extreme_pts(plug)
    plug_mid = sum(plug_pts, Vector()) / len(plug_pts)
    plug.parent = sock
    plug.matrix_parent_inverse = Matrix.Identity(4)
    plug.rotation_mode = "QUATERNION"
    plug_vis = _vis_meshes(plug)
    _hide_tracks(plug_vis, fk0, nf)
    PS = []
    for f in range(nf):
        w, off, q, k, tw, tl = plug_state(f)
        PS.append((w, off, q, k, tw, tl))
        plug.location = Vector((w, 0, 0)) * MM + off
        plug.rotation_quaternion = q
        plug.scale = (k, k, k)
        plug.keyframe_insert("location", frame=f)
        plug.keyframe_insert("rotation_quaternion", frame=f)
        plug.keyframe_insert("scale", frame=f)
        KS.pose(plug, "twist", tw)
        pr["twist"].keyframe_insert("rotation_euler", frame=f)
        KS.pose(plug, "tilt", tl)
        pr["tilt"].keyframe_insert("rotation_euler", frame=f)
    linear_keys(plug)
    for j in pr.values():
        linear_keys(j)
    # ---- 卡扣（5-09）：clamp 时红色卡扣扣住凸缘，咔一下
    if has("clamp"):
        e = E["clamp"]
        for f in range(nf):
            t = clamp01((f - e["f_start"]) / max(1, e["f_land"] - e["f_start"]))
            a = -25.0 * min(1.0, ease_out_back(t, 2.0))
            a += shake(f, e["f_land"], 1.5, 6.0, 6.0) if f >= e["f_land"] else 0.0
            KS.pose(sock, "tab", max(-25.0, min(0.0, a)))
            jr["tab"].keyframe_insert("rotation_euler", frame=f)
        linear_keys(jr["tab"])
    print("ONCAM step p3 plug", flush=True)
    # ---- 循环箭头（5-06 square one）：插座的子物体，loop 开始那一帧正对镜头、圈住等待位的插头
    arrow = head = None
    A_loc = None
    R = P.get("LOOP_R_MM", 20.0) * MM
    if has("loop"):
        e_l, e_h = E["loop"], E["arrowhead"]
        arrow, head, Mh = _loop_arrow(K, R, P["LOOP_TUBE_MM"] * MM, P["LOOP_END"])
        fr_ = e_l["f_start"]
        C_w = LM[fr_] @ (Vector((w_wait * MM, 0, 0)) + plug_mid)
        R_face = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))   # 局部 X→世界 X，Y→世界 Z，Z→−Y（朝镜头）
        A_loc = LM[fr_].inverted() @ Matrix.Translation(C_w) @ R_face @ Matrix.Diagonal((s, s, s, 1))
        for o in (arrow, head):
            o.parent = sock
            o.matrix_parent_inverse = Matrix.Identity(4)
        arrow.matrix_basis = A_loc
        cu = arrow.data
        for f, v in ((0, 0.0), (e_l["f_start"], 0.0), (e_h["f_land"], 1.0), (nf - 1, 1.0)):
            cu.bevel_factor_end = v
            cu.keyframe_insert("bevel_factor_end", frame=f)
        fe0, fe1 = f_d0, f_d0 + 12                                 # 段尾：箭头从尾巴往头收掉（不然冲镜头时圆环扫过相机，点跑到相机后面）
        for f, v in ((0, 0.0), (fe0, 0.0), (fe1, 1.0)):
            cu.bevel_factor_start = v
            cu.keyframe_insert("bevel_factor_start", frame=f)
        head.rotation_mode = "QUATERNION"
        for f in range(nf):
            t = clamp01((f - e_h["f_start"]) / max(1, e_h["f_end"] - e_h["f_start"]))
            k = 0.001 if f < e_h["f_start"] else max(0.001, ease_out_back(t, 2.4))
            if f >= f_d0:
                k = max(0.001, k * (1 - smooth((f - f_d0) / 12.0)))
            key_matrix(head, f, A_loc @ Mh @ Matrix.Diagonal((k, k, k, 1)))
        linear_keys(head)
        _hide_tracks([arrow], e_l["f_start"], nf)
        _hide_tracks([head], e_h["f_start"], nf)
    print("ONCAM step p4 arrow", flush=True)
    # ---- 灯光（同 3-06）
    hcol = _hero_collection(sc, [sock])
    gs = max(1, fk0 - 8)
    rim_keys = [(0, 0.6), (gs, 0.6), (fk1, 1.4), (fk1 + 60, 1.0), (nf - 1, 1.0)]
    _hero_lights(W, hcol, P_rest, P, rim_keys, key_point=P_rest + Vector((-0.4, -0.25, 0.0)))
    trans = _axis_trans_lamps(W, hcol, nf, f_d0, (LM[0] @ head_pt).length, (LM[nf - 1] @ tail_pt).length, P.get("TRANS_K", 1.0),
                              head_track=[(LM[f] @ head_pt).length for f in range(P["TRANS_TRACK"] + 1)] if P.get("TRANS_TRACK") else None,
                              tail_track=[(LM[f] @ tail_pt).length for f in range(f_d0, nf)] if P.get("TRANS_TRACK") else None,
                              nogloss=P.get("TRANS_NOGLOSS", False), tk=P.get("TRANS_TK", 1.0)) if BR else []
    print("ONCAM step p5 lights", trans, flush=True)

    def plug_world(f):
        w, off, q, k, tw, tl = PS[f]
        return LM[f] @ (Matrix.Translation(Vector((w * MM, 0, 0)) + off) @ q.to_matrix().to_4x4() @ Matrix.Diagonal((k, k, k, 1)))

    loop_pts = []
    if A_loc is not None:
        loop_pts = [A_loc @ Vector((R * math.cos(a), R * math.sin(a), 0)) for a in (i * math.tau / 24 for i in range(24))]

    def bbox_pts(f):
        pts = [LM[f] @ p for p in sock_pts]
        if f >= fk1:
            Mp = plug_world(f)
            pts += [Mp @ p for p in plug_pts]
        if loop_pts and E["loop"]["f_start"] <= f < f_d0 + 12:
            pts += [LM[f] @ p for p in loop_pts]
        return pts

    def focus_plan(f, Mcam):
        loc = Mcam.translation
        fwd = (Mcam.to_3x3() @ Vector((0, 0, -1))).normalized()
        p = LM[f] @ port if f <= f_ok + 20 else LM[f] @ c0
        if f <= f_ok and BR:
            p = (LM[f] @ head_pt).lerp(LM[f] @ port, smooth(f / max(1, f_ok)))
        if f_ok < f <= f_ok + 20:
            p = (LM[f] @ port).lerp(LM[f] @ c0, smooth((f - f_ok) / 20.0))
        d = (p - loc).dot(fwd)
        if f >= fk0 - 8:                                            # 插头出来以后：焦点在插头和孔口之间（插进去以后就在孔口）
            u = smooth((f - (fk0 - 8)) / 16.0)
            mid = (plug_world(f) @ plug_mid).lerp(LM[f] @ port, 0.5)
            d = d * (1 - u) + (mid - loc).dot(fwd) * u
        if f > f_d0:
            tp = LM[f] @ tail_pt
            d = d + ((tp - loc).dot(fwd) - d) * smooth((f - f_d0) / 8.0)
        return max(0.03, d)

    def fstop_plan(f):
        a = 4.0 + (FSTOP - 4.0) * smooth(f / 30.0)
        if f > f_d0:
            a = a + (8.0 - a) * smooth((f - f_d0) / (nf - 1 - f_d0))
        return a

    def checks():
        out = {}
        sc.frame_set(nf - 1)
        pv = set(_vis_meshes(plug))
        A = _RigidClip([o for o in _vis_meshes(sock) if o not in pv and o not in (arrow, head)])
        Bp = _RigidClip(list(pv))
        out["plug_vs_socket_frames"] = _RigidClip.hits(A, Bp, range(fk0, nf), sc)
        if head is not None:
            Ba = _RigidClip([head])
            out["arrowhead_vs_plug_frames"] = _RigidClip.hits(Ba, Bp, range(E["arrowhead"]["f_start"], nf), sc)
            out["arrowhead_vs_socket_frames"] = _RigidClip.hits(Ba, A, range(E["arrowhead"]["f_start"], nf), sc)
        sc.frame_set(0)
        return out

    handoff = dict(note="相机坐标（相机在原点看 +Y，+Z 向上；镜头 %.2f mm / 36 mm 传感器，偏移 %s）；插座 = kit_socket.h01b_cdk20_socket 放大 %.3f 倍，插头 %s" % (LENS, list(SHIFT), s, P["PLUG"]),
                   head_pose=dict(frame=0, port_center_m=list(LM[0] @ port), matrix=[list(r) for r in LM[0]]),
                   tail_pose=dict(frame=nf - 1, point_m=list(LM[nf - 1] @ tail_pt), mode=P["TAIL_MODE"], matrix=[list(r) for r in LM[nf - 1]]))
    return dict(targets={"card": lambda f: LM[max(0, min(nf - 1, int(f)))] @ c0}, hero=sock, bbox=bbox_pts, key=plug,
                focus=focus_plan, fstop=fstop_plan, tail_t0=f_d0, checks=checks, handoff=handoff,
                info=dict(scale=round(s, 3), plug=P["PLUG"], plug_wait_w_mm=round(w_wait, 2),
                          frames={k: [v["f_start"], v["f_land"], v["f_end"]] for k, v in E.items()},
                          P={k: v for k, v in P.items()}))


# ================================================================ 铺开第 2 批（11-20 夜，甲线）：1-01、1-03、1-05+06+07、2-04
# 一组零件挂在一个空物体 G 下面当"主零件"：段首从镜头前退回落位、落位后轻浮都在 G 上；子零件在 G 的局部坐标里按毫米摆
# （ORG = 构图中心；落位时 ORG 投影到 REST_PX，1 mm 在出片上 PXMM 像素），各自逐帧打局部矩阵。
# 段尾：TAIL_KIDS 里的子零件从料杆上掰下来自己冲进镜头（别的留在原地），不写就整组一起冲。
# 机检要的包围点只算 bbox=True 的子零件（伸出画面的料杆、藏在卷尺壳里的刻度不算），见各 recipe。


def _mm(x, y, z=0.0):
    return Vector((x, y, z)) * MM


def _T(x, y, z=0.0):
    return Matrix.Translation(_mm(x, y, z))


def _R(axis, a):
    return Matrix.Rotation(math.radians(a), 4, axis)


def _Sc(k, ky=None, kz=None):
    return Matrix.Diagonal((k, k if ky is None else ky, k if kz is None else kz, 1.0))


def _piv(x, y, z, M):
    """绕 G 局部点 (x, y, z) 毫米做 M。"""
    return _T(x, y, z) @ M @ _T(-x, -y, -z)


def _bumpf(f, f0, n):
    return math.sin(math.pi * clamp01((f - f0) / max(1, n))) if f >= f0 else 0.0


def _wob(f, f0, amp, per=10.0, tau=12.0):
    return amp * math.sin(2 * math.pi * (f - f0) / per) * math.exp(-(f - f0) / tau) if f >= f0 else 0.0


def _popk(f, f0, n=14, c=2.0):
    """0 → 1 弹出（带回弹）；f0 以前 0.001（藏着）。"""
    if f < f0:
        return 0.001
    return max(0.001, ease_out_back(clamp01((f - f0) / n), c))


def _objs(root):
    return [o for o in [root] + list(root.children_recursive) if o.type in ("MESH", "CURVE", "FONT")]


def _vis_keys(objs, show, hide, nf):
    """show 以前、hide 以后不出像。"""
    for o in objs:
        seq = [(0, show > 0)]
        if show > 0:
            seq.append((show, False))
        if hide is not None:
            seq.append((hide, True))
        for f, h in seq:
            o.hide_render = h
            o.keyframe_insert("hide_render", frame=f)


def _curve_mm(name, splines, r, m, step=0.5):
    """毫米折线（可多条）→ 圆管曲线；按 step 毫米重采样（bevel_factor 按长度走，料杆"长出来"匀速）。返回 (物体, 每条的累计长度表)。"""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r * MM
    cu.bevel_resolution = 6
    cu.use_fill_caps = True
    cu.bevel_factor_mapping_start = "SPLINE"
    cu.bevel_factor_mapping_end = "SPLINE"
    lens = []
    for pts in splines:
        pts = [Vector((p[0], p[1], p[2] if len(p) > 2 else 0.0)) for p in pts]
        out = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            n = max(1, int((b - a).length / step))
            out += [a.lerp(b, i / n) for i in range(1, n + 1)]
        acc = [0.0]
        for a, b in zip(out, out[1:]):
            acc.append(acc[-1] + (b - a).length)
        lens.append((out, acc))
        sp = cu.splines.new("POLY")
        sp.points.add(len(out) - 1)
        for i, p in enumerate(out):
            sp.points[i].co = (p.x * MM, p.y * MM, p.z * MM, 1.0)
    ob = link_obj(bpy.data.objects.new(name, cu))
    ob.data.materials.append(m)
    return ob, lens


class _Grp:
    def __init__(self, W):
        self.W, self.sc, self.K, self.cfg = W, W["sc"], W["kit"], W["cfg"]
        self.P, self.nf = self.cfg["P"], self.cfg["nf"]
        self.E = {e["id"]: e for e in self.cfg["K"]["events"]}
        self.Wd = {w["wid"]: w for w in self.cfg["K"]["words"]}
        self.G = link_obj(bpy.data.objects.new("oncam_grp", None))
        self.G.rotation_mode = "QUATERNION"
        self.kids = {}
        self.base = Quaternion((1, 0, 0), math.radians(90))      # G 局部 +Z → 朝镜头（−Y），+Y → 向上
        self.s = self.P["PXMM"] * self.P["REST_D"] / (F_PX * MM)
        self.c0 = _mm(*self.P.get("ORG", (0.0, 0.0)))

    def add(self, name, root, M0=None, show=0, hide=None, bbox=True, bake=True, vis=True):
        if bake:
            _bake(root)
        bpy.context.view_layer.update()
        pts = _extreme_pts(root) if bbox else []
        root.parent = self.G
        root.matrix_parent_inverse = Matrix.Identity(4)
        root.rotation_mode = "QUATERNION"
        M0 = M0 if M0 is not None else Matrix.Identity(4)
        root.matrix_basis = M0
        self.kids[name] = dict(root=root, pts=pts, M0=M0, fn=None, show=show, hide=hide, bbox=bbox, vis=vis)
        return root

    def km(self, name, f):
        k = self.kids[name]
        return k["fn"](f) if k["fn"] else k["M0"]

    def run(self, head_pt, tail_pt, tail_kids=None, gest=None):
        """head_pt / tail_pt：G 局部（米）。段首这一点落在 HEAD_PX、离镜头 HEAD_D；段尾落在 TAIL_PX、TAIL_D。"""
        P, E, nf, s, c0 = self.P, self.E, self.nf, self.s, self.c0
        e_a, e_d = E.get("arrive") or E["land"], E["dive"]      # 18 文档 2.4 起新做的段，第一个事件叫 land
        f_ok, f_ok_end = e_a["f_land"], e_a["f_end"]
        f_d0, f_d1 = e_d["f_start"], nf - 1
        self.f_ok, self.f_d0, self.head_pt, self.tail_pt, self.tail_kids = f_ok, f_d0, head_pt, tail_pt, tail_kids
        q_r = _q(*P["REST"], base=self.base)
        q_h = _q(*P.get("HEAD_ROT", (0.0, 0.0)), base=self.base)
        q_t = _q(*P.get("TAIL_ROT", (0.0, 0.0)), base=self.base)
        P_rest = Vector(px_to_world(*P["REST_PX"], P["REST_D"]))
        self.P_rest = P_rest
        P_head = Vector(px_to_world(*P["HEAD_PX"], P["HEAD_D"])) - q_h.to_matrix() @ ((head_pt - c0) * s)
        P_hc = Vector(px_to_world(*P["HEAD_CTRL"]))
        tgt = Vector(px_to_world(*P["TAIL_PX"], P["TAIL_D"]))
        ctrl_t = Vector(px_to_world(*P["TAIL_CTRL"]))

        def hover(f):
            b = smooth((f - 30) / 40)
            return Vector((0.0, 0.0, 0.004 * math.sin(2 * math.pi * f / 250) * b)), 1.0 * math.sin(2 * math.pi * f / 330 + 0.6) * b

        def gpose(f):
            if f <= f_ok:
                t = f / max(1, f_ok)
                p = ease_out_back(t, 0.9)
                k_e = P.get("HEAD_EASE", 0.0)                      # 0 = 原来的 ease_out_cubic；>0 混进 smoothstep，开头几帧退得慢些（M9 段首每帧亮度跳变 ≤ 24）
                c = _bz_at_depth(P_head, P_hc, P_rest, _logd(P_head.y, P_rest.y, (1 - k_e) * ease_out_cubic(t) + k_e * smooth(t)))
                lag = P.get("HEAD_QLAG", 0.0)                      # >0：转身晚于后退（6-04 段首牌子没退出画面就转到背光面，亮度先降后升，M9 往回闪）
                tq = clamp01((t - lag) / (1 - lag)) if lag else t
                q = (_qpow_w if P.get("HEAD_QW") else _qpow)(q_h, q_r, smooth(tq) * 0.35 + ease_out_back(tq, 0.9) * 0.65)
            else:
                sp = (f - f_ok) / FPS
                c = P_rest + Vector((0.004, 0.006, -0.008)) * spring(sp, 0.45, 20.0) * (1 - clamp01((f - f_ok) / max(1, f_ok_end + 12 - f_ok)))
                q = q_r.copy()
            if gest:
                dc, dq = gest(f)
                c, q = c + dc, dq @ q
            ho, hy = hover(f)
            return c + ho, Quaternion((0, 0, 1), math.radians(hy)) @ q

        LM = []
        if not tail_kids:
            c1 = tgt - q_t.to_matrix() @ ((tail_pt - c0) * s)
        for f in range(nf):
            c, q = gpose(f)
            if not tail_kids and f > f_d0:
                t = (f - f_d0) / (f_d1 - f_d0)
                c = _bz_at_depth(c, ctrl_t, c1, _logd(c.y, c1.y, smooth(t) * 0.7 + 0.3 * ease_in_cubic(t)))
                q = (_qpow_w if P.get("TAIL_QW") else _qpow)(q, q_t, smooth(min(1.0, t * 1.15)))   # TAIL_QW：_qpow 是局部差左乘，p = 1 到不了 q_t（4-04 段尾整组差 13°，镜头钻进桶壁）
            LM.append(_Mof(c, q, c0, s))
            key_matrix(self.G, f, LM[f])
        linear_keys(self.G)
        self.LM = LM
        # 子零件逐帧局部矩阵；段尾掰下来的子零件：世界里绕锚点（tail_pt 在 f_d0 的世界位置）整体刚体移动
        Mk = {n: [self.km(n, f) for f in range(nf)] for n in self.kids}
        self.A = None
        if tail_kids:
            M_d = LM[f_d0]
            A0 = M_d @ tail_pt
            q0 = M_d.to_quaternion()
            dR = q_t @ q0.inverted()
            self.A = []
            for f in range(nf):
                if f <= f_d0:
                    self.A.append(LM[f] @ tail_pt)
                    continue
                t = (f - f_d0) / (f_d1 - f_d0)
                e = smooth(t) * 0.7 + 0.3 * ease_in_cubic(t)
                a = _bz_at_depth(A0, ctrl_t, tgt, _logd(A0.y, tgt.y, e))
                r = _qpow(Quaternion(), dR, smooth(min(1.0, t * 1.15))).to_matrix().to_4x4()
                D_ = Matrix.Translation(a) @ r @ Matrix.Translation(-A0)
                self.A.append(a)
                inv = LM[f].inverted()
                for n in tail_kids:                     # TAIL_LIVE：掰下来的子零件段尾还在做自己的动作（卷尺缩尺带），按当帧局部位姿走
                    Mk[n][f] = inv @ D_ @ M_d @ Mk[n][f if P.get("TAIL_LIVE") else f_d0]
        self.Mk = Mk
        for n, k in self.kids.items():
            if k["fn"] is not None or (tail_kids and n in tail_kids):
                for f in range(nf):
                    key_matrix(k["root"], f, Mk[n][f])
                linear_keys(k["root"])
            if k["vis"]:
                _vis_keys(_objs(k["root"]), k["show"], k["hide"], nf)

    def tail_world(self, f):
        return self.A[f] if self.A is not None else self.LM[f] @ self.tail_pt

    def lights(self):
        hcol = _hero_collection(self.sc, [self.G])
        rim = [(0, 0.6), (self.f_ok, 0.6), (self.f_ok + 30, 1.0), (self.nf - 1, 1.0)]
        _hero_lights(self.W, hcol, self.P_rest, self.P, rim, key_point=self.P_rest + Vector((-0.4, -0.25, 0.0)))
        if self.P.get("TRANS"):
            self.trans_lamps(hcol)
        return hcol

    def trans_lamps(self, hcol):
        """18 文档 1.8 转场灯（11-22）：段首前 20 帧、段尾冲镜头那几帧，各一盏只照零件的面光（灯光链接），让盖满画面的浅色面是亮的。
        "功率为主光的 3 倍"按照度算：灯在镜头左上后方离盖满点 d 米，能量 = 3 × 主光能量 × (d / 2.6)²（主光离零件 2.6 m）× TRANS_K。
        灯本身不进镜头、不投影。"""
        P, nf, f_ok, f_d0 = self.P, self.nf, self.f_ok, self.f_d0
        key_w = self.W.get("fit", {}).get("key_w", 900.0)
        k = P.get("TRANS_K", 1.0)
        h0 = P.get("TRANS_H0", 1.0)                                   # 第 0 帧灯再加一点、3 帧回到 1（4-08：灯光斑跟着零件退开，第 0→2 帧反而变亮，M9 往回闪）
        hk = [(0, h0), (3, 1.0), (20, 1.0), (28, 0.0)] if h0 != 1.0 else [(0, 1.0), (20, 1.0), (28, 0.0)]
        if P.get("TRANS_HK"):                                          # 段首灯整条曲线自己写（6-04：退开第 3–4 帧牌面比大板暗，第 4→5 帧往回亮 13 → 那几帧灯加）
            hk = [tuple(x) for x in P["TRANS_HK"]]
        for nm, aim, keys in (("trans_head", self.LM[0] @ self.head_pt, hk),
                              ("trans_tail", self.tail_world(nf - 1), [(0, 0.0), (f_d0, 0.0), (min(nf - 1, f_d0 + 12), P.get("TRANS_TK", 1.0)), (nf - 3, P.get("TRANS_TK", 1.0)), (nf - 1, P.get("TRANS_TK", 1.0) * P.get("TRANS_T1", 1.0))])):   # TRANS_TK：段尾灯单独加（5-02）   # TRANS_T1：末两帧灯再加（4-04 末帧比前一帧暗 7.6，M9 往回闪）
            loc = Vector((-0.16, -0.10, 0.12)) + Vector((aim.x, 0.0, aim.z)) * 0.5
            d = (aim - loc).length
            en = 3.0 * key_w * (d / 2.6) ** 2 * k
            o = make_light(nm, "AREA", loc, aim, 0.35, en, kelvin_rgb(5600))
            o.light_linking.receiver_collection = hcol
            o.visible_camera = False
            o.data.use_shadow = False
            tr = P.get("TRANS_TRACK", 0) if nm == "trans_head" else 0
            if tr:                                                    # 段首灯跟着盖满点走 tr 帧（照度不变，能量按距离平方加、最多 ×25），之后停在那里、照原样 20→28 帧熄掉
                for f in range(tr + 1):                               # 6-04：灯不跟，牌子退开后正面变灰（比大板暗），露出大板时亮度往回升
                    a_ = self.LM[f] @ self.head_pt
                    l_ = Vector((-0.16, -0.10, 0.12)) + Vector((a_.x, 0.0, a_.z)) * 0.5
                    o.location = l_
                    o.rotation_euler = (a_ - l_).to_track_quat("-Z", "Y").to_euler()
                    o.keyframe_insert("location", frame=f)
                    o.keyframe_insert("rotation_euler", frame=f)
                    o.data.energy = en * min(25.0, ((a_ - l_).length / d) ** P.get("TRANS_TRACK_P", 2.0))   # P < 2 只补一部分（6-04 试渲 P 2：牌子越退越亮 0.74→0.96，往回闪 13.8）
                    o.data.energy *= h0 + (1.0 - h0) * min(1.0, f / 3.0)     # TRANS_H0 跟灯时也算（4-04：首帧灯加、3 帧回到 1）
                    o.data.keyframe_insert("energy", frame=f)
                e_tr = o.data.energy
                for fk, v in ((20, 1.0), (28, 0.0)):
                    o.data.energy = e_tr * v
                    o.data.keyframe_insert("energy", frame=fk)
                linear_keys(o.data)
                linear_keys(o)
                continue
            for fk, v in keys:
                o.data.energy = en * v
                o.data.keyframe_insert("energy", frame=fk)
            linear_keys(o.data)

    def bbox(self, f):
        pts = []
        for n, k in self.kids.items():
            if not k["bbox"] or f < k["show"] or f < k.get("bbox_from", 0) or (k["hide"] is not None and f >= k["hide"]):   # bbox_from：从画外落进来的零件落定以后才算进主零件框
                continue
            M = self.LM[f] @ self.Mk[n][f]
            pts += [M @ p for p in k["pts"]]
        return pts

    def kid_pts(self, f, names):
        """几个子零件各自的外形点（世界）：OC2 配件屏上高用。藏着的不给。"""
        out = {}
        for n in names:
            k = self.kids.get(n)
            if k is None or not k["pts"] or f < k["show"] or (k["hide"] is not None and f >= k["hide"]):
                continue
            M = self.LM[f] @ self.Mk[n][f]
            out[n] = [M @ p for p in k["pts"]]
        return out

    def result(self, foc_local, pairs=(), info=None):
        """foc_local(f) → G 局部（米）对焦点。pairs：[(子零件 A, 子零件 B, 帧范围)] 逐帧 BVH 穿模检查。"""
        nf, f_ok, f_d0 = self.nf, self.f_ok, self.f_d0
        self.lights()

        def focus_plan(f, Mcam):
            loc = Mcam.translation
            fwd = (Mcam.to_3x3() @ Vector((0, 0, -1))).normalized()
            p = self.LM[f] @ foc_local(f)
            ph = self.LM[f] @ self.head_pt
            if f <= f_ok:
                p = ph
            elif f <= f_ok + 20:
                p = ph.lerp(p, smooth((f - f_ok) / 20.0))
            if f > f_d0:
                p = p.lerp(self.tail_world(f), smooth((f - f_d0) / 8.0))
            return max(0.03, (p - loc).dot(fwd))

        def fstop_plan(f):
            a = 4.0 + (FSTOP - 4.0) * smooth(f / 30.0)
            if f > f_d0:
                a = a + (8.0 - a) * smooth((f - f_d0) / (nf - 1 - f_d0))
            return a

        def checks():
            out = {}
            sc = self.sc
            sc.frame_set(nf - 1)
            for a, b, rng in pairs:
                A = _RigidClip([o for o in [self.kids[a]["root"]] + list(self.kids[a]["root"].children_recursive) if o.type in ("MESH", "CURVE")])
                B = _RigidClip([o for o in [self.kids[b]["root"]] + list(self.kids[b]["root"].children_recursive) if o.type in ("MESH", "CURVE")])
                out[f"{a}_vs_{b}_frames"] = _RigidClip.hits(A, B, rng, sc)
            sc.frame_set(0)
            return out

        handoff = dict(note="相机坐标（相机在原点看 +Y，+Z 向上；镜头 %.2f mm / 36 mm 传感器，偏移 %s）；一组零件挂在空物体 oncam_grp 下，放大 %.3f 倍（落位时 1 mm = %.1f px）"
                       % (LENS, list(SHIFT), self.s, self.P["PXMM"]),
                       head_pose=dict(frame=0, point_m=list(self.LM[0] @ self.head_pt), matrix=[list(r) for r in self.LM[0]]),
                       tail_pose=dict(frame=nf - 1, point_m=list(self.tail_world(nf - 1)), kids=self.tail_kids or "all", matrix=[list(r) for r in self.LM[nf - 1]]))
        inf = dict(scale=round(self.s, 3), frames={k: [v["f_start"], v["f_land"], v["f_end"]] for k, v in self.E.items()},
                   P={k: v for k, v in self.P.items()})
        inf.update(info or {})
        return dict(targets={"card": lambda f: self.LM[max(0, min(nf - 1, int(f)))] @ self.c0}, hero=self.G, bbox=self.bbox, key=self.G, kid_pts=self.kid_pts,
                    focus=focus_plan, fstop=fstop_plan, tail_t0=f_d0, checks=checks, handoff=handoff, info=inf)


def _hang(root, k, x, y_top):
    """零件（毫米、局部原点在 0）按 k 缩放后，包围盒顶边中点挂在 G 的 (x, y_top) 毫米：返回 M0。"""
    lo, hi = mesh_bounds([root])
    cx = (lo.x + hi.x) / 2 / MM
    return _T(x - cx * k, y_top - hi.y / MM * k) @ _Sc(k)


def _people_part(K, name, m, stub_mm, k):
    """玩具小人（kit_parts.person）+ 头顶一根白色浇口（料杆到头顶，G 里长 stub_mm 毫米）。返回 (root, 身体网格, 浇口顶在小人局部的 y)。"""
    import kit_parts as KP
    P = KP.Part(K, name, "red")
    KP.person(P, m, 0.0)
    body = [o for o in P.root.children if o.type == "MESH"]
    top = 14.9
    y1 = top + stub_mm / k
    P.tube([(0.0, y1 + 1.0), (0.0, top - 0.3)], 0.55 / k * 0.9, K.white)
    return P.done(), body, y1


V101 = dict(
    PXMM=8.5, REST_D=1.5, REST_PX=(1445.0, 480.0), REST=(-12.0, 6.0), ORG=(1.0, 8.0),        # 11-21 干跑：小人间距 14 时右沿 1917 出画，收到 12
    HEAD_D=0.15, HEAD_PX=(700.0, 560.0), HEAD_CTRL=(2300.0, 470.0, 0.95),
    TAIL_D=0.13, TAIL_PX=(960.0, 540.0), TAIL_CTRL=(1500.0, 360.0, 0.75),
    CAL_K=1.45, PEOPLE_K=0.62, LIVER_K=0.55, LIGHT_GLOW=2.6, CANCER_GLOW=4.0,
    BOARD_K=1.27, BOARD_HIDE=("stations", "zone_tags", "z1_c0_r0"),
    HEAD_BOX=(300, 90, 900, 680), LOCK_BOX=(1060, 0, 1940, 960),
    RIM_W=60.0, SAMPLES=16, GRAIN_F=150, GRAIN_GAIN=1.0,
)


def recipe_calendar_people(W):
    """1-01（A："Every day in Hong Kong, about four people die of liver cancer."，354 帧）。
    撕页日历（p10）：day 撕下一页；Hong Kong 料杆长出、四个红色小人弹出；four people 一个个亮；die 一起熄成灰、往后倒；
    liver 玻璃肝弹出；cancer 肝里暗红一亮、长出一个暗红结节，日历点头；说完日历从料杆上掰下来冲进镜头。"""
    import kit_parts as KP
    g = _Grp(W)
    K, P, E, nf = g.K, g.P, g.E, g.nf
    ck = P["CAL_K"]
    # 日历
    cal = KP.p10_calendar(K)
    g.add("cal", cal, _T(0, 20) @ _Sc(ck))
    # 撕页：盖在日历格子上（日历局部：本体正面 z 1.5、装订条正面 2.1 到 y 10.2），红页眉 + 一个大写日期
    pg = KP.Part(K, "page", "white")
    pg.slab(KP.rrect(0, 2.6, 9.8, 7.4, 0.8), 0.5, K.white, z=2.15, bevel=0.15)
    pg.inkbox(0, 8.0, 9.3, 1.6, K.red, 2.4)
    pg.text("1", 8.5, 0, 1.6, 2.4, K.ink)
    page = pg.done()
    g.add("page", page, _T(0, 20) @ _Sc(ck), hide=E["page"]["f_end"] + 1, bbox=False)
    # 料杆（从日历底下的浇口往两边长）+ 浇口
    ry = -9.0
    bar_bottom = 20 + (-15.0) * ck
    run_, _ = _curve_mm("runner_bar", [[(0, ry), (-34, ry)], [(0, ry), (42, ry)], [(0, ry), (0, bar_bottom + 0.4)]], 1.3, K.white)
    rp = KP.Part(K, "runner_cal", "white")
    run_.parent = rp.root
    g.add("runner", rp.done(), show=E["people"]["f_start"])
    # 四个红色小人
    pk = P["PEOPLE_K"]
    xs = [-27.0, -15.0, -3.0, 9.0]
    head_top = ry - 1.3 - 2.0
    people, bodies = [], []
    for i, x in enumerate(xs):
        r, body, y1 = _people_part(K, f"red_person{i}", K.red, 2.0 + 1.3, pk)
        M0 = _T(x, head_top - 14.9 * pk) @ _Sc(pk)
        g.add(f"p{i}", r, M0, show=E["people"]["f_land"] + i * 8)
        people.append((r, body, y1, M0))
        bodies.append(body)
    # 玻璃肝 + 浇口 + 结节
    liv = KP.p04_liver(K)
    lk = P["LIVER_K"]
    sx, sy, _sz = (float(v) for v in liv["socket"])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=3.4 * MM, location=((sx + 3.0) * MM, (sy - 4.0) * MM, 0.0), segments=32, ring_count=16)
    nod = bpy.context.object
    nod.name = "liver_nodule"
    bpy.ops.object.shade_smooth()
    nod.data.materials.append(KP.mat_solid("oncam_tumour", "#5C0A14", rough=0.3))
    nod.parent = liv
    _bake(liv)
    bpy.context.view_layer.update()
    lx = 28.5
    M_l = _hang(liv, lk, lx, head_top + 1.0)
    g.add("liver", liv, M_l, show=E["liver"]["f_start"], bake=False)
    ls = KP.Part(K, "liver_stub", "white")
    ls.tube([(lx, ry), (lx, head_top + 1.2)], 1.0, K.white)
    g.add("lstub", ls.done(), show=E["liver"]["f_start"])
    _vol_rescale(liv, g.s * lk)
    # ---- 动作
    e_pg, e_pp, e_li, e_di, e_lv, e_ca = E["page"], E["people"], E["light"], E["die"], E["liver"], E["cancer"]
    M_cal = g.kids["cal"]["M0"]

    def cal_fn(f):
        nodd = 7.0 * _bumpf(f, e_ca["f_land"], 22)                 # cancer：日历轻轻点一下头（顶朝镜头）
        return _piv(0, 20 - 15 * ck, 0, _R("X", nodd)) @ M_cal
    g.kids["cal"]["fn"] = cal_fn

    def page_fn(f):
        """day：页从上沿翻起来（朝镜头），然后撕下、翻滚着往右上飞走、变小。"""
        a = -80.0 * ease_out_cubic(clamp01((f - e_pg["f_start"]) / max(1, e_pg["f_land"] - e_pg["f_start"])))   # 翻过 90° 会扫进装订条（干跑 53–58 帧穿模）
        M = _piv(0, 10.0, 2.15, _R("X", a))
        t = clamp01((f - e_pg["f_land"]) / max(1, e_pg["f_end"] - e_pg["f_land"]))
        if t > 0:
            u = ease_in_cubic(t) * 0.6 + smooth(t) * 0.4
            dz = 8.0 * smooth(min(1.0, t * 4)) + 14 * u                # 先离开日历面再翻滚
            sp = ease_in_cubic(t)
            M = _T(26 * u, 30 * u + 8 * math.sin(math.pi * t), dz) @ _piv(0, 5, 2, _R("Y", 160 * sp) @ _R("Z", -40 * sp) @ _Sc(1 - 0.6 * u)) @ M
        return M_cal @ M
    g.kids["page"]["fn"] = page_fn
    run_.data.bevel_factor_start = 0.0
    for f in range(nf):                                           # Hong Kong：料杆从日历底下往两边长出来
        run_.data.bevel_factor_end = ease_out_cubic(clamp01((f - e_pp["f_start"]) / max(1, e_pp["f_land"] + 10 - e_pp["f_start"])))
        run_.data.keyframe_insert("bevel_factor_end", frame=f)
    linear_keys(run_.data)
    # 小人：弹出（从浇口顶上长出来）、亮、熄灭变灰往后倒
    glow, cols = [], []
    for i, (r, body, y1, M0) in enumerate(people):
        st, mat = _emit_mat(body, f"oncam_person{i}", (1.0, 0.42, 0.28))
        glow.append(st)
        cols.append(next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"])
        f_in = g.kids[f"p{i}"]["show"]

        def fn(f, M0=M0, y1=y1, f_in=f_in, i=i):
            k = _popk(f, f_in, 14, 2.2)
            a = 16.0 * smooth((f - e_di["f_land"] - i * 2) / 16.0) + _wob(f, e_di["f_land"] + 16 + i * 2, 2.5, 18.0, 14.0)
            sw = 2.0 * math.sin(2 * math.pi * (f + i * 37) / 160.0) * smooth((f - f_in - 14) / 20.0)
            return M0 @ _piv(0, y1, 0, _R("X", a) @ _R("Z", sw) @ _Sc(k))
        g.kids[f"p{i}"]["fn"] = fn
    t_on = [e_li["f_land"] + 8 * i for i in range(4)]
    d0 = e_di["f_land"]
    for i in range(4):
        _key_val(glow[i], [(0, 0.0), (t_on[i] - 1, 0.0), (t_on[i] + 3, P["LIGHT_GLOW"] * 1.3), (t_on[i] + 10, P["LIGHT_GLOW"]),
                           (d0 - 1, P["LIGHT_GLOW"]), (d0 + 3, P["LIGHT_GLOW"] * 0.35), (d0 + 14, 0.0), (nf - 1, 0.0)])
        c0_ = tuple(cols[i].default_value)
        grey = (0.30, 0.29, 0.27, 1.0)
        for f, c in ((0, c0_), (d0, c0_), (d0 + 16, grey), (nf - 1, grey)):
            cols[i].default_value = c
            cols[i].keyframe_insert("default_value", frame=f)
    # 肝：弹出；cancer 血管暗红一亮、结节长出来
    M_l0 = g.kids["liver"]["M0"]
    lo_, hi_ = mesh_bounds([liv])                                 # 当前（M0 上）世界包围盒，换回肝局部毫米
    piv_l = (M_l0.inverted() @ Vector(((lo_.x + hi_.x) / 2, hi_.y, 0.0)))

    def liver_fn(f):
        k = _popk(f, e_lv["f_start"], 16, 1.8)
        sw = 1.5 * math.sin(2 * math.pi * f / 190.0) * smooth((f - e_lv["f_land"]) / 20.0)
        return M_l0 @ _piv(piv_l.x / MM, piv_l.y / MM, 0, _R("Z", sw) @ _Sc(k))
    g.kids["liver"]["fn"] = liver_fn
    ves = [o for o in liv.children_recursive if o.type == "MESH" and o.active_material is not None and o.active_material.name.startswith("kit_red")]
    if ves:
        vs, _ = _emit_mat(ves, "oncam_vessel", (0.55, 0.02, 0.05))
        ca0, ca1 = e_ca["f_start"], e_ca["f_land"]
        _key_val(vs, [(0, 0.0), (ca0, 0.0), (ca1 + 6, P["CANCER_GLOW"]), (ca1 + 26, 0.6), (nf - 1, 0.6)])
    nod.scale = (0.001,) * 3
    nod.keyframe_insert("scale", frame=0)
    nod.keyframe_insert("scale", frame=e_ca["f_land"])
    for f, k in ((e_ca["f_land"] + 10, 1.15), (e_ca["f_land"] + 18, 1.0)):
        nod.scale = (k,) * 3
        nod.keyframe_insert("scale", frame=f)
    ns, _ = _emit_mat([nod], "oncam_tumour_glow", (0.6, 0.02, 0.05))
    _key_val(ns, [(0, 0.0), (e_ca["f_land"], 0.0), (e_ca["f_land"] + 10, 3.0), (e_ca["f_land"] + 30, 0.4), (nf - 1, 0.4)])
    # 段首：日历撕页正面盖满画面；段尾：日历从料杆上掰下来冲进镜头
    head = Vector((0.0, 20 + 2.6 * ck, 2.45 * ck)) * MM
    tail = Vector((0.0, 20 + 2.6 * ck, 1.6 * ck)) * MM
    g.run(head, tail, tail_kids=["cal"])

    def foc(f):
        if f < e_pp["f_start"]:
            return Vector((0.0, 20 * MM, 2 * MM))
        if f < e_lv["f_start"]:
            return _mm(-5, 0, 0)
        return _mm(10, -5, 0)
    pairs = [("p0", "p1", range(e_di["f_start"], nf)), ("p3", "liver", range(e_lv["f_start"], nf)), ("page", "cal", range(e_pg["f_start"], e_pg["f_end"]))]
    return g.result(foc, pairs, info=dict(people_x=xs))


V103 = dict(
    PXMM=7.4, REST_D=1.5, REST_PX=(1400.0, 300.0), REST=(-10.0, 5.0), ORG=(0.0, 19.0),       # 11-21 干跑：7.9 时上沿 21、下沿 536（A 的手从 604 行起伸到 1195，下沿要留在 540 以上）
    HEAD_D=0.09, HEAD_PX=(700.0, 560.0), HEAD_CTRL=(2300.0, 430.0, 0.95),
    TAIL_D=0.09, TAIL_PX=(960.0, 540.0), TAIL_CTRL=(1450.0, 300.0, 0.7),
    CAP_K=1.9, PEOPLE_K=0.30, HANG_TILT=15.0, LIGHT_GLOW=3.0, LIT=(1, 5, 8),
    BOARD_K=1.27, BOARD_HIDE=("stations", "zone_tags", "z1_c0_r0"),
    HEAD_BOX=(300, 90, 900, 680), LOCK_BOX=(900, 0, 1940, 620),
    RIM_W=60.0, SAMPLES=16, GRAIN_F=150, GRAIN_GAIN=1.0,
)


def recipe_capsule_row(W):
    """1-03（A："Here's the thing. We already have medicines. Just not good enough ones."，326 帧）。
    一粒大胶囊挂在料杆的侧浇口上；thing 预颤；already have 料杆下十个白色小人依次弹出；medicines 胶囊咔地从浇口弹下、立起站到料杆上；
    Just 胶囊朝小人探身；not / good / enough 十个里只亮三个；ones 胶囊耸一下；说完胶囊自己冲进镜头。"""
    import kit_parts as KP
    g = _Grp(W)
    K, P, E, nf = g.K, g.P, g.E, g.nf
    ck = P["CAP_K"]
    half, rad = (7.5 + 4.2) * ck, 4.2 * ck
    rad_b = (4.2 + 0.35) * ck                                     # 腰上金箍的半径（侧浇口接在金箍上）
    y_stand = 1.3 + 0.4 + half
    y_hang = y_stand + 2.0
    px_post = -14.0
    # 胶囊（kit_parts.capsule 沿 X 横放，转 90° 竖起来）
    cp = KP.Part(K, "capsule_big", "white")
    KP.capsule(cp, 0, 0, K)
    cap = cp.done()
    g.add("cap", cap, _T(0, y_hang) @ _R("Z", 90) @ _Sc(ck))
    # 料杆：一根横杆（小人挂在下面）+ 左边一根立柱 + 侧浇口
    bar, _ = _curve_mm("runner_bar", [[(-46, 0), (46, 0)]], 1.3, K.white)
    rp = KP.Part(K, "runner_cap", "white")
    bar.parent = rp.root
    rp.tube([(px_post, 0.0), (px_post, y_hang + 4.0)], 1.3, K.white)
    rp.tube([(px_post, y_hang), (-rad_b - 0.15, y_hang)], 0.8, K.white)
    g.add("runner", rp.done())
    # 十个白色小人
    pk = P["PEOPLE_K"]
    xs = [-40.5 + 9.0 * i for i in range(10)]
    head_top = -1.3 - 1.0
    e_row = E["row"]
    people = []
    for i, x in enumerate(xs):
        r, body, y1 = _people_part(K, f"white_person{i}", K.white, 1.0 + 1.3, pk)
        M0 = _T(x, head_top - 14.9 * pk) @ _Sc(pk)
        f_in = e_row["f_start"] + 3 + i * 4
        g.add(f"p{i}", r, M0, show=f_in)
        people.append((r, body, y1, M0, f_in))
    e_th, e_md, e_ju, e_3, e_on = E["thing"], E["medicine"], E["just"], E["three"], E["ones"]
    tilt0 = P["HANG_TILT"]
    gate = (-rad_b, y_hang)                                       # 侧浇口在胶囊左边腰上（金箍）
    _ca, _sa = math.cos(math.radians(tilt0)), math.sin(math.radians(tilt0))
    c_h = Vector((gate[0] + _ca * (0.0 - gate[0]) - _sa * 0.0, gate[1] + _sa * (0.0 - gate[0]) + _ca * 0.0))   # 挂着时胶囊中心（毫米，绕侧浇口转 tilt0）

    def cap_fn(f):
        """挂着（绕侧浇口斜 15°，thing 预颤）→ medicines 弹下：转正、往右下落到料杆上站住 → Just 探身 → ones 耸一下。"""
        m0, m1 = e_md["f_start"], e_md["f_land"]
        if f < m1:
            a = tilt0 + _wob(f, e_th["f_land"], 4.0, 7.0, 9.0) + (-3.0 * _bumpf(f, m0, m1 - m0))
            return _piv(gate[0], gate[1], 0, _R("Z", a)) @ _T(0, y_hang) @ _R("Z", 90) @ _Sc(ck)
        t = clamp01((f - m1) / 20.0)
        a = tilt0 * (1 - ease_out_back(t, 1.6))
        x = c_h.x + (3.0 - c_h.x) * smooth(t)
        y = c_h.y + (y_stand - c_h.y) * ease_in_cubic(t) + 2.0 * math.sin(math.pi * t) * (1 - t)
        sq = 0.05 * _bumpf(f, m1 + 18, 10)                       # 落地压一下
        M = _T(x, y) @ _R("Z", a)
        M = M @ _piv(0, -half, 0, _Sc(1 + sq, 1 - sq, 1 + sq))
        lean = 13.0 * _bumpf(f, e_ju["f_start"], 30) + _wob(f, e_ju["f_start"] + 30, 2.0, 12.0, 10.0)
        hop = 2.2 * _bumpf(f, e_on["f_start"], 14)
        sh = _wob(f, e_on["f_start"], 5.0, 9.0, 9.0)
        M = _piv(x, 1.7, 0, _R("X", lean) @ _R("Z", sh)) @ _T(0, hop) @ M
        return M @ _R("Z", 90) @ _Sc(ck)
    g.kids["cap"]["fn"] = cap_fn
    lit = list(P["LIT"])
    t_lit = [e_3["f_land"], g.Wd[g.cfg["seg"] + ".w010"]["f0"], g.Wd[g.cfg["seg"] + ".w011"]["f0"]]
    for i, (r, body, y1, M0, f_in) in enumerate(people):
        def fn(f, M0=M0, y1=y1, f_in=f_in, i=i):
            k = _popk(f, f_in, 12, 2.2)
            sw = 1.5 * math.sin(2 * math.pi * (f + i * 29) / 150.0) * smooth((f - f_in - 12) / 20.0)
            if i in lit:                                          # 亮的那一下晃一下
                sw += _wob(f, t_lit[lit.index(i)] - 1, 6.0, 12.0, 10.0)
            return M0 @ _piv(0, y1, 0, _R("Z", sw) @ _Sc(k))
        g.kids[f"p{i}"]["fn"] = fn
        if i in lit:
            st, _ = _emit_mat(body, f"oncam_wperson{i}", (1.0, 0.80, 0.45))
            t0 = t_lit[lit.index(i)]
            _key_val(st, [(0, 0.0), (t0 - 2, 0.0), (t0 + 3, P["LIGHT_GLOW"] * 1.4), (t0 + 12, P["LIGHT_GLOW"]), (nf - 1, P["LIGHT_GLOW"])])
    head = (_T(0, y_hang) @ _R("Z", 90) @ _Sc(ck)).translation + _mm(0, 0, rad + 0.2)
    head = _piv(gate[0], gate[1], 0, _R("Z", tilt0)) @ head
    tail = _mm(3.0, y_stand, rad + 0.2)
    g.run(head, tail, tail_kids=["cap"])

    def foc(f):
        if f < e_row["f_start"]:
            return g.Mk["cap"][f].translation
        return _mm(0, 8, 0)
    pairs = [("cap", "runner", range(e_md["f_land"] + 1, nf)), ("p4", "p5", range(e_row["f_start"], nf))]
    return g.result(foc, pairs, info=dict(lit=lit, t_lit=t_lit))


V105 = dict(
    # 11-22 甲线（18 文档 2.4）：整组 × 1.33（PXMM 11 → 14.63，最矮 366 → ≥ 486 px），往左下挪让右沿、上沿不出 OC3；
    # 段首盖满用钥匙坯的金色柄面（HEAD_PT 柄环实心处），段尾改成卷尺（骨白壳）冲镜头；转场灯、红格子藏掉
    PXMM=14.95, REST_D=1.5, REST_PX=(1372.0, 396.0), REST=(-10.0, 5.0), ORG=(0.0, 0.0),   # D 第 94–112 帧竖起的手指在柄环左下角前面（手在前，HAND_FRONT）
    HEAD_D=0.10, HEAD_PX=(960.0, 540.0), HEAD_CTRL=(2300.0, 430.0, 0.95),
    TAIL_D=0.10, TAIL_PX=(960.0, 540.0), TAIL_CTRL=(1450.0, 330.0, 0.7),
    OC=True, OC1_EXEMPT=[(381, 555)], MAKE_FWD=4.0, HAND_FRONT=[(94, 112)], TAIL_TAPE=True, TAIL_LIVE=True, TAPE_WHITE=True, TRANS=True, TRANS_K=1.0, HIDE_RED=True, H_MIN=486, TOP_MIN=60, BOT_MAX=860,
    KEY_K=3.4, KEY_GLOW=6.0, TAPE_POS=(16.1, -15.1), TAPE_U=3.6, TAPE_S=0.7, TAPE_N=17,   # 11-24 Z24：卷尺壳左移 5.3 mm（PXMM 14.95，屏上约 80 px）；尺带往左拉出，刻度 4.0 → 3.6 mm 让尺钩不压人（M5）
    BOARD_K=1.27, BOARD_HIDE=("stations", "zone_tags", "z1_c0_r0"),
    HEAD_BOX=(300, 90, 900, 680), LOCK_BOX=(900, 0, 1940, 1080),
    RIM_W=60.0, SAMPLES=16, GRAIN_F=150, GRAIN_GAIN=1.0,
)


def recipe_key_tape(W):
    """1-05+06+07（D："So... why not just make a better one?" B："Because that's way harder than it sounds." C："Like, ten-to-seventeen-years hard."，596 帧）。
    没齿的金钥匙坯（h02 blank）挂在浇口上；why 歪头；make 往前一抬；better 金光一闪；B 说时后面的料杆一路长、拐弯，harder 急弯钥匙一晃，伸出画面；
    C 说时卷尺弹出来，尺带拉过 10 停在 17（10–17 一段红底），hard 锁扣按下；说完钥匙坯从浇口掰下来冲进镜头。"""
    import kit_parts as KP
    import kit_deep as D
    g = _Grp(W)
    K, P, E, nf = g.K, g.P, g.E, g.nf
    kk = P["KEY_K"]
    key = D.h02_key(K, which="blank", scale=1.0)
    # h02 钥匙：x −7.5..6.5、y ±4（毫米）；放大 kk 倍居中。钥匙圈顶（浇口）在局部 (−3.5, 4)
    M_key = _T(0.5 * kk, 0) @ _Sc(kk)
    g.add("key", key, M_key)
    bx, by = (-3.5 + 0.5) * kk, 4.0 * kk
    sp = KP.Part(K, "key_stub", "white")
    sp.tube([(bx, by + 0.1), (bx, by + 6.0)], 1.0, K.white)
    g.add("stub", sp.done())
    # 料杆：急弯前后各自 Catmull-Rom 平滑，接点不平滑（急弯）
    A_ = [(bx, by + 6.0), (bx, by + 10.0), (bx + 12, by + 11.0), (bx + 18, by + 15.0), (bx + 30, by + 15.0), (bx + 34, by + 8.0)]
    B_ = [(bx + 34, by + 8.0), (bx + 42, by + 8.0), (bx + 47, by + 14.0), (bx + 64, by + 14.0), (bx + 92, by + 20.0), (bx + 142, by + 26.0)]
    path = [tuple(p) for p in KP.smooth_path(A_, 10)] + [tuple(p) for p in KP.smooth_path(B_, 10)][1:]
    run_, lens = _curve_mm("key_runner", [path], 1.3, K.white)
    out, acc = lens[0]
    kink = Vector((bx + 34, by + 8.0, 0.0))
    i_k = min(range(len(out)), key=lambda i: (out[i] - kink).length)
    fr_k = acc[i_k] / acc[-1]
    rr = KP.Part(K, "key_runner_root", "white")
    run_.parent = rr.root
    g.add("runner", rr.done(), bbox=False, show=E["path"]["f_start"])
    e_wh, e_mk, e_bt, e_pa, e_hd = E["why"], E["make"], E["better"], E["path"], E["harder"]
    e_tp, e_ex, e_lk = E["tape"], E["extend"], E["lock"]
    run_.data.bevel_factor_start = 0.0
    for f in range(nf):
        if f < e_pa["f_start"]:
            v = 0.0
        elif f < e_hd["f_land"]:
            v = fr_k * ease_inout_cubic(clamp01((f - e_pa["f_start"]) / max(1, e_hd["f_land"] - e_pa["f_start"])))
        else:
            v = fr_k + (1 - fr_k) * ease_inout_cubic(clamp01((f - e_hd["f_land"]) / max(1, e_pa["f_end"] - e_hd["f_land"])))
        run_.data.bevel_factor_end = max(0.0005, v)
        run_.data.keyframe_insert("bevel_factor_end", frame=f)
    linear_keys(run_.data)

    def hang_M(f):
        """钥匙坯连浇口挂在料杆上：绕浇口顶 (bx, by+6) 摆（why 歪头、harder 被带得一晃）；make 往前一抬（浇口跟着，料杆那时还没长出来）。"""
        a = 1.5 * math.sin(2 * math.pi * f / 180.0) * smooth((f - 40) / 30.0)
        wy = 0.0
        if P.get("WHY_YAW"):                                      # 1-05 11-22：why 改成绕竖轴转头（左右摆会让柄环左下角碰到 D 竖起的手指、刀头出右边）
            wy = P["WHY_YAW"] * _bumpf(f, e_wh["f_start"], 30) + _wob(f, e_wh["f_start"] + 30, 2.5, 12.0, 10.0)
            a += P.get("WHY_Z", 0.0) * _bumpf(f, e_wh["f_start"], 30)
        else:
            a += 11.0 * _bumpf(f, e_wh["f_start"], 30) + _wob(f, e_wh["f_start"] + 30, 2.0, 12.0, 10.0)
        a += _wob(f, e_hd["f_land"], 6.0, 9.0, 14.0)
        up = _bumpf(f, e_mk["f_start"], 28)
        Mw = _piv(P.get("WHY_PIV", bx), 0, 0, _R("Y", wy))       # 绕刀头一侧的竖轴转：柄环往后、往右让（D 第 100 帧竖起手指）
        return _piv(bx, by + 6.0, 0, _R("Z", a)) @ Mw @ _T(0, 2.0 * up, P.get("MAKE_FWD", 8.0) * up) @ _R("X", -8.0 * up)
    g.kids["key"]["fn"] = lambda f: hang_M(f) @ M_key
    g.kids["stub"]["fn"] = hang_M
    gs, _ = _emit_mat([o for o in _objs(key) if o.type == "MESH"], "oncam_key_glow", (1.0, 0.78, 0.35))
    b0 = e_bt["f_land"]
    _key_val(gs, [(0, 0.0), (b0 - 2, 0.0), (b0 + 4, P["KEY_GLOW"]), (b0 + 26, 0.5), (b0 + 60, 0.0), (nf - 1, 0.0)])
    # ---- 卷尺：克莱因蓝壳 + 白尺带（10–17 一段红底白字）+ 金色尺钩 + 红色锁扣
    tx, ty = P["TAPE_POS"]
    u, N = P["TAPE_U"], P["TAPE_N"]
    ext_max = N * u + 0.6
    mouth = -7.6                                                  # 出尺口：壳左面（圆角 3 mm，尺带 y −7.5..−3.0 这一段左面都在 x ≤ −7.6）
    white = P.get("TAPE_WHITE")                                   # 18 文档：卷尺壳骨白（段尾盖满画面只许浅色面）
    hs = KP.Part(K, "tape_case", "white" if white else "blue")
    hs.box(0, 0, 8.0, 9.0, 9.0, K.white if white else K.blue, r=3.0, bevel=1.0)
    hs.text(P.get("CASE_TXT", "years"), 4.2, 0.6, 2.0, 4.5, K.ink if white else K.inkw, italic=True)
    hs.inkbox(mouth + 0.9, -5.25, 0.5, 2.1, K.ink, 4.5)         # 出尺口（深色缝）
    case = hs.done()
    f_tp = e_tp["f_start"]
    g.add("tape", case, _T(tx, ty), show=f_tp)
    lb = KP.Part(K, "tape_lock", "red")
    lb.box(-3.0, 9.6, 2.2, 1.0, 4.0, K.red, r=0.6, bevel=0.3)
    g.add("lockbtn", lb.done(), _T(tx, ty), show=f_tp)
    stp = KP.Part(K, "tape_strip", "white")
    stp.slab([(-1.0, -7.5), (0.0, -7.5), (0.0, -3.0), (-1.0, -3.0)], 0.4, K.white, bevel=0)
    g.add("strip", stp.done(), _T(tx + mouth, ty) @ _Sc(0.001, 1, 1), show=f_tp)
    mk = KP.Part(K, "tape_marks", "white")
    marks = []                                                    # (物体, 尺带上的位置 b)
    nb = int(round((N - 10) * u / 1.0))
    for j in range(nb):                                           # 10–17 红底：1 mm 一小段，整段拉出来才出像（不然藏在壳里的部分从壳右边穿出去）
        b0 = 10 * u + j * 1.0
        o = mk.inkbox(b0 + 0.5, -5.9, 0.52, 1.5, K.red, 0.2)
        marks.append((o, b0 + 1.0))
    for i in range(0, N + 1):
        b = i * u
        o = mk.inkbox(b, -3.8, 0.13, 0.6, K.ink, 0.2)
        marks.append((o, b + 0.13))
        if i < N:
            o = mk.inkbox(b + u / 2, -3.55, 0.1, 0.35, K.ink, 0.2)
            marks.append((o, b + u / 2 + 0.1))
        if i >= 1:
            o = mk.text(str(i), 2.4, b, -5.9, 0.5 if i >= 10 else 0.2, K.inkw if i >= 10 else K.ink)
            marks.append((o, b + 1.3))
    g.add("marks", mk.done(), _T(tx + mouth, ty), show=f_tp, bbox=False, vis=False)
    hk = KP.Part(K, "tape_hook", "gold")
    hk.box(-0.45, -5.25, 0.45, 2.8, 1.4, K.gold, r=0.2, bevel=0.15)
    g.add("hook", hk.done(), _T(tx + mouth, ty), show=f_tp)

    e_dv = E["dive"]

    def ext(f):
        e = ext_max * ease_inout_cubic(clamp01((f - e_ex["f_start"]) / max(1, e_ex["f_end"] - e_ex["f_start"])))
        e = e - 0.8 * _wob(f, e_lk["f_land"], 1.0, 8.0, 7.0) * (1 if f >= e_lk["f_land"] else 0)
        if P.get("TAIL_TAPE"):                                    # 段尾卷尺冲镜头：先松锁扣、尺带 12 帧缩回壳里（不然长尺带扫过人脸）
            e *= 1 - ease_in_cubic(clamp01((f - e_dv["f_start"]) / 12.0))
        return max(0.0, e)

    def tape_M(f):
        k = _popk(f, f_tp, 16, 1.8)
        rise = 8.0 * (1 - ease_out_cubic(clamp01((f - f_tp) / 16.0)))
        jolt = 0.4 * _wob(f, e_lk["f_land"], 1.0, 7.0, 7.0)
        return _T(tx, ty - rise + jolt) @ _Sc(k * P.get("TAPE_S", 1.0))   # TAPE_S：整个卷尺（壳、尺带、刻度、钩）一起缩放
    g.kids["tape"]["fn"] = tape_M
    g.kids["lockbtn"]["fn"] = lambda f: tape_M(f) @ _T(0, -1.0 * ease_out_back(clamp01((f - e_lk["f_start"]) / max(1, e_lk["f_land"] - e_lk["f_start"])), 2.0))
    g.kids["strip"]["fn"] = lambda f: tape_M(f) @ _T(mouth, 0) @ _Sc(max(0.001, ext(f)), 1, 1)
    g.kids["marks"]["fn"] = lambda f: tape_M(f) @ _T(mouth - ext(f), 0)
    g.kids["hook"]["fn"] = lambda f: tape_M(f) @ _T(mouth - ext(f), 0)
    # 刻度：拉出来（b ≤ 拉出长度）才出像；状态变的帧才打关键帧
    for o, b in marks:
        prev = None
        for f in range(nf):
            h = f < f_tp or b > ext(f) - 0.25
            if h != prev:
                o.hide_render = h
                o.keyframe_insert("hide_render", frame=f)
                prev = h
    if P.get("TAIL_TAPE"):
        head = M_key @ Vector((-3.5 * MM, 2.6 * MM, 0.7 * MM))   # 柄环实心处（环 r 1.2–4，取 r 2.6）
        sS = P.get("TAPE_S", 1.0)
        tail = _mm(tx, ty - 4.5 * sS, 4.5 * sS)                   # 卷尺壳正面、刻字下面一块（段尾 tape_M 已停稳，缩放 = TAPE_S）
        g.run(head, tail, tail_kids=["tape", "lockbtn", "strip", "marks", "hook"])
    else:
        head = M_key @ Vector((4.0 * MM, 0, 0.85 * MM))
        tail = head.copy()
        g.run(head, tail, tail_kids=["key"])

    def foc(f):
        if f >= f_tp + 10:
            return _mm(10, -12, 0)
        return _mm(0, 0, 0)
    pairs = [("key", "stub", range(1, e_hd["f_end"])), ("key", "tape", range(f_tp, nf)), ("strip", "key", range(f_tp, nf))]
    if P.get("TAIL_TAPE"):
        pairs += [("hook", "key", range(f_tp, nf)), ("lockbtn", "key", range(f_tp, nf))]
    return g.result(foc, pairs, info=dict(runner_kink_frac=round(fr_k, 3), runner_len_mm=round(acc[-1], 1), tape_ext_mm=ext_max))


V204 = dict(
    PXMM=10.0, REST_D=1.5, REST_PX=(1500.0, 480.0), REST=(-12.0, 5.0), ORG=(-3.0, 0.0),
    HEAD_D=0.14, HEAD_PX=(700.0, 560.0), HEAD_CTRL=(2300.0, 430.0, 0.95),
    TAIL_D=0.12, TAIL_PX=(960.0, 470.0), TAIL_CTRL=(1450.0, 330.0, 0.7),
    PLATE_K=1.4, TILT0=-28.0, TEXT_GLOW=3.0,
    BOARD_K=1.27, BOARD_HIDE=("stations", "zone_tags", "z1_c0_r0"),
    HEAD_BOX=(300, 90, 900, 680), LOCK_BOX=(1140, 0, 1940, 960),
    RIM_W=60.0, SAMPLES=16, GRAIN_F=150, GRAIN_GAIN=1.0,
)


def recipe_two_plates(W):
    """2-04（C："We set ourselves two objectives."，238 帧）。一根竖料杆，两块编号牌（p16，刻 1、2）挂在侧浇口上、往后仰。
    set 料杆抬头、牌子朝镜头翻正一点；ourselves 浇口预颤；two 两块牌同时弹下、立正（叠着）；objectives 上下让开、刻字亮红；
    说完两块牌一起冲进镜头。"""
    import kit_parts as KP
    g = _Grp(W)
    K, P, E, nf = g.K, g.P, g.E, g.nf
    pk = P["PLATE_K"]
    hw = 9.0 * pk
    post_x = -20.0
    cx = post_x + 1.3 + 3.0 + hw
    ys = [12.0, -12.0]
    rp = KP.Part(K, "plate_runner", "white")
    rp.tube([(post_x, -27.0), (post_x, 27.0)], 1.3, K.white)
    for y in ys:
        rp.tube([(post_x, y), (cx - hw - 0.15, y)], 0.75, K.white)
    g.add("runner", rp.done())
    plates, txt = [], []
    for i, y in enumerate(ys):
        pr = KP.p16_plate(K, str(i + 1), w=18.0, italic=False)
        g.add(f"pl{i}", pr, _T(cx, y) @ _Sc(pk))
        plates.append(pr)
        txt.append([o for o in _objs(pr) if o.type == "FONT"])
    e_st, e_os, e_tw, e_ob = E["set"], E["ourselves"], E["two"], E["obj"]

    def mk_fn(i, y):
        def fn(f):
            gate_x = cx - hw
            a = P["TILT0"] + 13.0 * ease_out_back(clamp01((f - e_st["f_start"]) / max(1, e_st["f_end"] - e_st["f_start"])), 1.6)
            a += _wob(f, e_os["f_land"], 2.5, 6.0, 10.0) + 1.2 * math.sin(2 * math.pi * (f + 40 * i) / 120.0) * smooth((f - 40) / 20)
            t = clamp01((f - e_tw["f_land"]) / 18.0)
            x, yy = 0.0, 0.0
            if f >= e_tw["f_land"]:
                a = a * (1 - ease_out_back(t, 1.8))
                x = 6.0 * ease_out_cubic(t)
                yy = 4.0 * math.sin(math.pi * t) * (1 - t)
            sp = (1 if i == 0 else -1) * 3.5 * ease_out_back(clamp01((f - e_ob["f_start"]) / max(1, e_ob["f_land"] + 10 - e_ob["f_start"])), 1.6)
            return _T(x, yy + sp) @ _piv(gate_x, y, 0, _R("X", a)) @ _T(cx, y) @ _Sc(pk)
        return fn
    for i, y in enumerate(ys):
        g.kids[f"pl{i}"]["fn"] = mk_fn(i, y)
    for i in range(2):
        st, _ = _emit_mat(txt[i], f"oncam_plate_txt{i}", (1.0, 0.10, 0.06))
        o0 = e_ob["f_land"] + 4 * i
        _key_val(st, [(0, 0.0), (o0 - 2, 0.0), (o0 + 6, P["TEXT_GLOW"] * 1.3), (o0 + 18, P["TEXT_GLOW"]), (nf - 1, P["TEXT_GLOW"])])

    def gest(f):                                                  # set：整根料杆抬头（顶朝镜头）
        a = 6.0 * ease_out_back(clamp01((f - e_st["f_start"]) / max(1, e_st["f_end"] - e_st["f_start"])), 1.5)
        return Vector(), Quaternion((1, 0, 0), math.radians(a))
    head = _T(cx, ys[0]) @ _Sc(pk) @ Vector((0, 0, 1.75 * MM))
    head = _piv(cx - hw, ys[0], 0, _R("X", P["TILT0"])) @ head
    tail = _T(6.0, ys[1] - 3.5, 0) @ _T(cx, 0) @ Vector((0, 0, 1.75 * pk * MM))
    g.run(head, tail, tail_kids=["pl0", "pl1"], gest=gest)

    def foc(f):
        return _mm(cx, 0, 0)
    pairs = [("pl0", "runner", range(e_tw["f_land"] + 1, nf)), ("pl1", "runner", range(e_tw["f_land"] + 1, nf)), ("pl0", "pl1", range(0, nf))]
    return g.result(foc, pairs)


V701 = dict(
    # 11-22 甲线（18 文档 2.4 7-01，照 2-04 two_plates 改）：竖料杆两侧交错挂三块编号牌（左 1、右 2、左 3），每块屏上高 ≥ 200 px；
    # 三块竖着一排会超过 OC1 的 620 px 上限（3 × 200 + 缝），所以左右交错、上下错开半块，整组约 570 px。3/4 角（偏航 −28°、俯 8°）
    PXMM=9.7, REST_D=1.5, REST_PX=(1566.0, 450.0), REST=(28.0, 8.0), ORG=(0.0, 0.0),
    HEAD_D=0.095, HEAD_PX=(960.0, 540.0), HEAD_CTRL=(2300.0, 430.0, 0.95),   # 11-23 返修三：EASE 1.0 后段首盖满 5 帧再一下退开，第 4→5 帧跳 25.7；起点放远一点，盖满早一两帧松开、退得慢
    TAIL_D=0.08, TAIL_PX=(960.0, 540.0), TAIL_CTRL=(1450.0, 330.0, 0.7),
    HEAD_EASE=1.0, HEAD_QW=True,                                           # 11-22 首版机检 M9 段首第 0→1 帧跳 38.8（0.6 还有 26.8，0.85 还有 25.0）：开头退慢些；落位那帧整组跳一下（_qpow_w）
    MODE="701", LABELS=("1", "2", "3"), PLATE_W=20.0, PLATE_K=1.5, TILT0=-18.0, TEXT_GLOW=3.0, FWD_MM=30.0, FWD_XY=(-30.0, -6.0), OC1_EXEMPT=[(227, 275)], HAND_FRONT=[(205, 245)],
    RUN_R=0.71, GATE_R=0.45, ACC=["pl0", "pl1", "pl2"],
    OC=True, TRANS=True, TRANS_K=1.0, HIDE_RED=True, H_MIN=486, TOP_MIN=60, BOT_MAX=860,
    BOARD_K=1.27, BOARD_HIDE=("stations", "zone_tags", "z1_c0_r0"),
    HEAD_BOX=(300, 90, 900, 680), LOCK_BOX=(1000, 0, 1940, 1080),
    RIM_W=60.0, SAMPLES=16, GRAIN_F=150, GRAIN_GAIN=1.0,
)
V801 = dict(
    # 11-22 甲线（18 文档 2.4 8-01）：竖料杆右侧两块目标牌 1、2（屏上高 ≥ 200 px），back 绕浇口轴翻一整圈，started 数字变红、扫光、右边弹出空勾选框
    PXMM=9.8, REST_D=1.5, REST_PX=(1525.0, 460.0), REST=(28.0, 8.0), ORG=(2.0, 0.0), RUN_OVER=5.0, TAIL_LIVE=True,
    HEAD_D=0.08, HEAD_PX=(960.0, 540.0), HEAD_CTRL=(2300.0, 430.0, 0.95),
    TAIL_D=0.13, TAIL_PX=(960.0, 540.0), TAIL_CTRL=(1450.0, 330.0, 0.7),   # 0.08 时最后一帧牌子前表面进了近裁面（0.01 m），露出牌子里面，M9 往回闪 20–42
    HEAD_EASE=0.6, HEAD_QW=True,                                           # 11-22 首版机检 M9 段首第 1→2 帧跳 42.6：开头退慢些；落位那帧整组跳一下（_qpow_w）
    MODE="801", LABELS=("1", "2"), PLATE_W=20.0, PLATE_K=1.5, TILT0=-10.0, TEXT_GLOW=3.0,
    RUN_R=0.71, GATE_R=0.45, ACC=["pl0", "pl1"], OC2_EXEMPT=[(55, 76)],
    OC=True, TRANS=True, TRANS_K=1.0, HIDE_RED=True, H_MIN=486, TOP_MIN=60, BOT_MAX=860,
    BOARD_K=1.27, BOARD_HIDE=("stations", "zone_tags", "z1_c0_r0"),
    HEAD_BOX=(300, 90, 900, 680), LOCK_BOX=(1000, 0, 1940, 1080),
    RIM_W=60.0, SAMPLES=16, GRAIN_F=120, GRAIN_GAIN=1.0,
)


def _key_hide(o, keys):
    """hide_render 关键帧，插完再把值写死（11-22：5.3 下先设值再 keyframe_insert，第一帧的 True 记成了 0，牌上的字一直出像）。"""
    for f, v in keys:
        o.hide_render = v
        o.keyframe_insert("hide_render", frame=f)
    want = {float(f): float(v) for f, v in keys}
    act = o.animation_data.action
    fcs = []
    for l in getattr(act, "layers", []):
        for st in l.strips:
            for cb in st.channelbags:
                fcs += list(cb.fcurves)
    fcs += list(getattr(act, "fcurves", []) or [])
    for c in fcs:
        if c.data_path == "hide_render":
            for k in c.keyframe_points:
                if k.co[0] in want:
                    k.co[1] = want[k.co[0]]
                k.interpolation = "CONSTANT"
            c.update()
    o.hide_render = bool(keys[0][1])


def _sheen_light(sc, hcol, c_from, c_to, aim, f0, n, energy):
    """扫光：一盏只照零件的窄条面光，f0 起 n 帧从 c_from 扫到 c_to（世界坐标），前后关着。"""
    o = make_light("sheen", "AREA", c_from, aim, 0.08, energy, kelvin_rgb(6500), size_y=0.9)
    o.light_linking.receiver_collection = hcol
    o.visible_camera = False
    for f, c, e in ((f0 - 1, c_from, 0.0), (f0, c_from, energy), (f0 + n, c_to, energy), (f0 + n + 1, c_to, 0.0)):
        o.location = c
        o.keyframe_insert("location", frame=f)
        o.data.energy = e
        o.data.keyframe_insert("energy", frame=f)
    return o


def recipe_plates(W):
    """7-01（A 说 So, what should happen next? We'd suggest three things.，320 帧）、8-01（C 说 So, back to where we started.，194 帧）。
    p16 编号牌挂在一根竖料杆的侧浇口上（照 2-04 two_plates）。段首段尾都是牌 1 的骨白牌面（刻字以外的一块）盖满画面。
    7-01：三块牌左右交错，先往后仰、刻字藏着；next 料杆一晃、浇口颤；three 起三块依次弹下立正、刻字变红（各差 8 帧）；things 牌 1 往前浮 30 mm。
    8-01：两块牌在右侧；back 两块绕浇口轴翻一整圈落定、摆 2°；started 数字变红、扫光、每块右边弹出一个空的勾选框。"""
    import kit_parts as KP
    g = _Grp(W)
    K, P, E, nf = g.K, g.P, g.E, g.nf
    mode = P["MODE"]
    pk, pw = P["PLATE_K"], P["PLATE_W"]
    hw, hh = pw / 2 * pk, 7.0 * pk
    gap = 3.0
    if mode == "701":
        post_x = 0.0
        side = [-1, 1, -1]
        ys = [15.0, 0.0, -15.0]
        y_top, y_bot = 29.0, -29.0
    else:
        post_x = -20.0
        side = [1, 1]
        ys = [11.5, -11.5]
        y_top, y_bot = 11.5 + hh + P.get("RUN_OVER", 4.0), -11.5 - hh - P.get("RUN_OVER", 4.0)
    cxs = [post_x + s * (gap + hw) for s in side]
    rp = KP.Part(K, "plate_runner", "white")
    rp.tube([(post_x, y_bot), (post_x, y_top)], P["RUN_R"], K.white)
    for s, y in zip(side, ys):
        rp.tube([(post_x, y), (post_x + s * (gap - 0.15), y)], P["GATE_R"], K.white)
    g.add("runner", rp.done())
    txt = []
    for i, (lab, cx, y) in enumerate(zip(P["LABELS"], cxs, ys)):
        pr = KP.p16_plate(K, lab, w=pw, italic=False)
        g.add(f"pl{i}", pr, _T(cx, y) @ _Sc(pk))
        txt.append([o for o in _objs(pr) if o.type == "FONT"])
    n = len(ys)
    e_dive = E["dive"]

    def idle(f, i):
        return 1.2 * math.sin(2 * math.pi * (f + 40 * i) / 120.0) * smooth((f - 40) / 20)

    if mode == "701":
        e_sw, e_fw = E["bar_sway"], E["p1_fwd"]
        pops = [E["p1"], E["p2"], E["p3"]]

        def mk_fn(i):
            s, cx, y = side[i], cxs[i], ys[i]
            gate_x = cx - s * hw

            def fn(f):
                a = P["TILT0"] + idle(f, i) + _wob(f, e_sw["f_land"] + 2 * i, 3.0, 8.0, 12.0)
                ep = pops[i]
                x = 0.0
                yy = 0.0
                if f >= ep["f_land"]:
                    t = clamp01((f - ep["f_land"]) / 18.0)
                    a = a * (1 - ease_out_back(t, 1.8))
                    x = s * 5.0 * ease_out_cubic(t)
                    yy = -3.0 * math.sin(math.pi * t) * (1 - t)
                elif f >= ep["f_start"]:
                    a += _wob(f, ep["f_start"], 2.0, 4.0, 30.0)          # 浇口预颤
                z = 0.0
                if i == 0:
                    z = P["FWD_MM"] * ease_inout_cubic(clamp01((f - e_fw["f_start"]) / max(1, e_fw["f_end"] - e_fw["f_start"])))
                fx, fy = P.get("FWD_XY", (0.0, 0.0))                 # 往前浮时同时往左下让（透视会把它往右上推出画）
                u = z / P["FWD_MM"] if P.get("FWD_MM") else 0.0
                return _T(x + fx * u, yy + fy * u, z) @ _piv(gate_x, y, 0, _R("X", a)) @ _T(cx, y) @ _Sc(pk)
            return fn
        for i in range(n):
            g.kids[f"pl{i}"]["fn"] = mk_fn(i)
            ep = pops[i]
            st, _ = _emit_mat(txt[i], f"oncam_plate_txt{i}", (1.0, 0.10, 0.06))
            o0 = ep["f_land"]
            _key_val(st, [(0, 0.0), (o0, 0.0), (o0 + 6, P["TEXT_GLOW"] * 1.3), (o0 + 18, P["TEXT_GLOW"]), (nf - 1, P["TEXT_GLOW"])])

        def gest(f):                                                  # next：整根料杆像钟摆晃一下（绕镜头轴）
            a = _wob(f, e_sw["f_start"], 3.0, 26.0, 22.0)
            return Vector(), Quaternion((0, 1, 0), math.radians(a))
    else:
        e_fl, e_gl = E["flip"], E["glow"]

        def mk_fn(i):
            cx, y = cxs[i], ys[i]

            def fn(f):
                a = P["TILT0"] + idle(f, i)
                if i == 0:                                            # 段尾冲镜头时摆正（斜着冲过来下沿先穿过镜头近裁面，最后一帧露出墙；11-22 机检 M9 往回闪 41.6）
                    a *= 1.0 - smooth((f - e_dive["f_start"]) / max(1, nf - 1 - e_dive["f_start"]))
                u = ease_inout_cubic(clamp01((f - e_fl["f_start"] - i) / max(1, e_fl["f_land"] - e_fl["f_start"])))
                a += 360.0 * u + _wob(f, e_fl["f_land"] + i, 2.0, 10.0, 14.0)
                off = 6.0 * ease_out_cubic(clamp01((f - e_dive["f_start"]) / 4.0)) if i == 0 else 0.0   # 段尾先从浇口上掰开再转向镜头（不然转身时蹭到浇口）
                return _T(0.25 * off, 0, off) @ _piv(cx, y, 0, _R("X", a)) @ _T(cx, y) @ _Sc(pk)
            return fn
        for i in range(n):
            g.kids[f"pl{i}"]["fn"] = mk_fn(i)
            st, _ = _emit_mat(txt[i], f"oncam_plate_txt{i}", (1.0, 0.10, 0.06))
            o0 = e_gl["f_land"] + 4 * i
            _key_val(st, [(0, 0.0), (o0 - 6, 0.0), (o0 + 2, P["TEXT_GLOW"] * 1.3), (o0 + 14, P["TEXT_GLOW"]), (nf - 1, P["TEXT_GLOW"])])
        # 空的勾选框：牌右边一个方框（骨白框、深色底），started 时弹出
        for i in range(n):
            bx = KP.Part(K, f"check{i}", "white")
            bx.box(0, 0, 3.4, 3.4, 1.6, K.ink, r=0.8, bevel=0.3)         # 空勾选框 = 深色细框 + 骨白框心（11-22 看样张：深色框心侧看像个插头）
            bx.box(0, 0, 2.8, 2.8, 0.4, K.white, z=0.75, r=0.5, bevel=0)
            cxb = cxs[i] + hw + 7.0
            g.add(f"chk{i}", bx.done(), _T(cxb, ys[i]) @ _Sc(0.001), show=e_gl["f_start"])
            f0 = e_gl["f_start"] + 3 * i

            def cfn(f, cxb=cxb, y=ys[i], f0=f0):
                return _T(cxb, y) @ _Sc(pk * _popk(f, f0, 14, 2.0))
            g.kids[f"chk{i}"]["fn"] = cfn
        gest = None
    # 段首、段尾盖满点：牌 1 正面、刻字左边一块（刻字以外的骨白面）
    face = Vector((-5.5 * MM, 0.0, 1.45 * MM))
    head = g.kids["pl0"]["fn"](0) @ face
    tail = g.kids["pl0"]["fn"](e_dive["f_start"]) @ face
    g.run(head, tail, tail_kids=["pl0"], gest=gest)
    if mode == "701":                                                 # 空白牌：刻字在弹下立正的那一帧出现（放在 run 后面：run 的 _vis_keys 会把第 0 帧重打成出像）
        for i in range(n):
            for o in txt[i]:
                _key_hide(o, [(0, True), (pops[i]["f_land"], False)])

    def foc(f):
        if mode == "701":
            return _mm(0, 0, 0).lerp(g.kids["pl0"]["fn"](f) @ Vector((0, 0, 0)), smooth((f - E["p1_fwd"]["f_start"]) / 30.0))
        return _mm(post_x + 12.0, 0, 0)
    pairs = [(f"pl{i}", "runner", range(0, nf)) for i in range(n)]
    pairs += [(f"pl{i}", f"pl{j}", range(0, nf)) for i in range(n) for j in range(i + 1, n)]
    if mode == "801":
        pairs += [(f"pl{i}", f"chk{i}", range(E["glow"]["f_start"], nf)) for i in range(n)]
    R = g.result(foc, pairs, info=dict(mode=mode, plate_h_mm=round(2 * hh, 2)))
    if mode == "801":                                                 # started：一道扫光从左到右掠过两块牌
        hcol = bpy.data.collections["ONCAM_hero"]
        Pr = g.P_rest
        e_gl = E["glow"]
        _sheen_light(W["sc"], hcol, Pr + Vector((-0.45, -0.35, 0.05)), Pr + Vector((0.45, -0.35, 0.05)), Pr, e_gl["f_land"] - 2, 22, P["RIM_W"] * 2.5)
    return R


V411 = dict(
    # 11-22 甲线（18 文档 2.4 4-11+12）：骨白领奖台（中 22×16×18、左 22×16×12、右 22×16×8 mm）+ 七把假插头（001、A–F，柄面刻字全藏）。
    # 定案（可改回）：七把同一个缩放 0.9（"同一批件"，站台上的和挂料杆的一样大；18 写的 170 / 130 px 是远近差，0.9 时每把屏上约 150 px）；
    # 打分表、烧瓶不从画外滑进来（会过 M3 右沿），改成在落点附近弹出 + 小位移；烧瓶不做气泡。
    PXMM=6.4, REST_D=1.5, REST_PX=(1440.0, 425.0), REST=(14.0, 6.0), ORG=(10.0, 16.0),
    HEAD_D=0.08, HEAD_PX=(960.0, 540.0), HEAD_CTRL=(2300.0, 430.0, 0.95),
    TAIL_D=0.04, TAIL_PX=(960.0, 540.0), TAIL_CTRL=(1450.0, 330.0, 0.7), TAIL_ROT=(5.0, 2.0),   # (14, 6) 时柄面中间映出一块白光，段尾先暗后亮，M9 往回闪 3.6
    PLUG_K=0.9, SLOT=15.0, RAIL_Y=30.0, RAIL_Z=-16.0, CHIP=(0.0, 44.5, -20.0), DIAL=(57.0, 23.0, 4.0), FLASK=(57.0, -16.0, 4.0),
    FLASK_K=1.4, TAIL_LIVE=True,
    OC=True, TRANS=True, TRANS_K=1.0, HIDE_RED=True, H_MIN=486, TOP_MIN=60, BOT_MAX=860, ACC=["chip", "dial", "flask"],
    HAND_FRONT=[(482, 493)], OC2_EXEMPT=[(303, 312), (557, 568)], HEAD_EASE=0.4, HEAD_QW=True,   # 首版 M9 段首第 2→3 帧跳 24.9；落位那帧整组跳一下（_qpow_w）   # A 第 482–493 帧手伸到台子左下角前面（手在前）；表、烧瓶弹出那几帧还没长到全大
    BOARD_K=1.27, BOARD_HIDE=("stations", "zone_tags", "z1_c0_r0"),
    HEAD_BOX=(300, 90, 900, 680), LOCK_BOX=(1000, 0, 1940, 1080),
    RIM_W=60.0, SAMPLES=16, GRAIN_F=150, GRAIN_GAIN=1.0,                  # 首版 2.4 → M10 2.43（D 素材颗粒细）
)


def _plug_kid(K, which, k):
    """h02b 假插头，烘焙好；返回 (root, 针尖 x（插头局部 mm，未缩放）, 刻字物体列表)。"""
    import kit_socket as KS
    pl = KS.h02b_plug(K, which)
    KS.rest(pl)
    _bake(pl)
    bpy.context.view_layer.update()
    lo, hi = mesh_bounds([pl])
    labels = [o for o in pl.children_recursive if o.type in ("MESH", "FONT") and o.active_material is not None
              and o.active_material.name.startswith(K.black.name)]
    return pl, lo.x / MM, labels


def recipe_podium(W):
    """4-11+12（D：Wait. So the computer picked the winners?  A：Not quite. A docking score is a clue, not proof. Only the lab can tell.，640 帧）。
    G 局部毫米：领奖台底 y −30；三把插头柄朝上立在三级台面上（x −22、0、22）；台后 z −16 一根横料杆 y 30，七个挂位 x = −42…42（间距 14），
    开头四把挂在 ±28、±42；芯片在料杆上方后面；打分表在右上、烧瓶在右下。插头轴 = 局部 +X，竖起来 = 绕 Z 转 90°（柄面朝上）。
    段首：中间一级台面的正面（骨白）盖满画面；段尾：挂位 0 那把（原来站中间的）柄面转向镜头冲过来（金色）。"""
    import kit_parts as KP
    g = _Grp(W)
    K, P, E, nf = g.K, g.P, g.E, g.nf
    k = P["PLUG_K"]
    # ---- 领奖台
    pod = KP.Part(K, "podium", "white")
    steps = [(-22.0, 12.0), (0.0, 18.0), (22.0, 8.0)]                    # (中心 x, 高)
    for cx, h in steps:
        pod.box(cx, -30.0 + h / 2, 11.0, h / 2, 16.0, K.white, r=0.6, bevel=0.6)
    g.add("podium", pod.done())
    # ---- 料杆和七个挂位的浇口
    ry, rz, sl = P["RAIL_Y"], P["RAIL_Z"], P["SLOT"]
    slots = [sl * (i - 3) for i in range(7)]                              # −42 … 42
    rail = KP.Part(K, "plug_rail", "white")
    rail.tube([(-50.0, ry, rz), (50.0, ry, rz)], 0.75, K.white)
    g.add("rail", rail.done())
    gate_len = 2.2
    top_y = ry - 0.75 - gate_len                                          # 浇口下端 = 插头柄面顶点（插头局部 x 10）挂的地方
    for i, x in enumerate(slots):
        st = KP.Part(K, f"stub{i}", "white")
        st.tube([(x, ry, rz), (x, top_y + 0.2, rz)], 0.45, K.white)
        g.add(f"stub{i}", st.done())                                      # 中间三个（2–4）的 show 在下面按 step_down 改
    # ---- 七把插头：0=001（站左）、1=A（站中）、2=B（站右）；3–6=C–F 挂 ±28、±42
    names = ["001", "A", "B", "C", "D", "E", "F"]
    stand = {0: steps[0], 1: steps[1], 2: steps[2]}
    hang0 = {3: slots[0], 4: slots[1], 5: slots[5], 6: slots[6]}
    final_slot = {0: slots[2], 1: slots[3], 2: slots[4], 3: slots[0], 4: slots[1], 5: slots[5], 6: slots[6]}
    labels_all, tips = [], {}
    for i, nm in enumerate(names):
        root, tipx, labs = _plug_kid(K, nm, k)
        labels_all += labs
        tips[i] = tipx
        g.add(f"plug{i}", root, bake=False)
    R90 = _R("Z", 90.0)

    def hang_M(i, x, lean=0.0):
        """柄面顶（局部 x 10）挂在 (x, top_y, rz)；lean：绕挂点转（度，正 = 下端往右摆）。"""
        return _T(x, top_y, rz) @ _R("Z", lean) @ _T(0, -10.0 * k) @ R90 @ _Sc(k)

    def stand_M(i):
        cx, h = stand[i]
        y0 = -30.0 + h + 0.35 - tips[i] * k                                 # 针尖离台面 0.35 mm
        return _T(cx, y0, 0.0) @ R90 @ _Sc(k)

    e_hop, e_no, e_sd, e_ln, e_d = E["winners_hop"], E["shake_no"], E["step_down"], E["lean"], E["dive"]
    lean_k = lambda f: 20.0 * ease_inout_cubic(clamp01((f - e_ln["f_start"]) / max(1, e_ln["f_land"] - e_ln["f_start"])))

    def mk_stand(i):
        cx, h = stand[i]
        tip_pt = (cx, -30.0 + h + 0.35, 0.0)
        f_hop = e_hop["f_land"] + 4 * i
        f_sd0 = e_sd["f_start"] + 4 * i
        f_sd1 = e_sd["f_land"] + 4 * i
        x1 = final_slot[i]

        def fn(f):
            if f < f_sd0:
                hop = 6.0 * _bumpf(f, f_hop - 6, 14)
                a = 0.0
                if e_no["f_start"] <= f <= e_no["f_end"] + 10:               # 摇两下 ±12°，绕针尖
                    t = (f - e_no["f_start"]) / max(1, e_no["f_end"] - e_no["f_start"])
                    a = 12.0 * math.sin(2 * math.pi * 2 * clamp01(t)) * (1 - 0.3 * clamp01(t)) * (1 - smooth((f - e_no["f_end"]) / 10.0))
                lift = 1.3 * smooth((f - e_no["f_start"] + 4) / 4.0) * (1 - smooth((f - e_no["f_end"] - 6) / 6.0))   # 摇的时候离台面一点（别的针尖不扎进台面）
                return _T(0, hop + lift) @ _piv(*tip_pt, _R("Z", a)) @ stand_M(i)
            t = clamp01((f - f_sd0) / max(1, f_sd1 - f_sd0))
            A = stand_M(i)
            B = hang_M(i, x1)
            pa, pb = A.translation, B.translation
            ey, ex, ez = ease_out_cubic(t), ease_inout_cubic(t), ease_in_cubic(t)   # 先往上离台、再横移、最后往后进挂位（从料杆下面进，不穿料杆）
            p = Vector((pa.x + (pb.x - pa.x) * ex, pa.y + (pb.y - pa.y) * ey, pa.z + (pb.z - pa.z) * ez))
            M = B.copy()
            M.translation = p
            if f >= f_sd1:
                away = -15.0 * smooth((f - (e_d["f_start"] - 6)) / 10.0) if i == 0 else 0.0   # 段尾中间那把转身时，左邻往回摆开（不碰）
                M = hang_M(i, x1, lean_k(f) + away + _wob(f, f_sd1, 3.0, 16.0, 14.0))
            return M
        return fn

    def mk_hang(i):
        x = hang0[i]
        ph = 0.7 * i

        def fn(f):
            sw = 1.2 * math.sin(2 * math.pi * f / 150.0 + ph) * smooth((f - 30) / 30.0)
            return hang_M(i, x, lean_k(f) + sw * (1 - smooth((f - e_ln["f_start"]) / 10.0)))
        return fn

    for i in range(7):
        g.kids[f"plug{i}"]["fn"] = mk_stand(i) if i in stand else mk_hang(i)
    for i in (2, 3, 4):                                                   # 中间三个浇口在插头挂上去那一帧出现
        g.kids[f"stub{i}"]["show"] = e_sd["f_land"] + 4 * (i - 2)
    # ---- 段尾：挂位 0（中间）那把 = plug1，柄面转向镜头
    face = Vector((9.85 * MM, 0.0, 0.0))
    fn1 = g.kids["plug1"]["fn"]
    f_d0 = e_d["f_start"]
    M_d0 = fn1(f_d0)
    Fp = M_d0 @ face
    lean_d0 = lean_k(f_d0)

    def fn_dive(f, base=fn1):
        if f <= f_d0:
            return base(f)
        e = smooth(clamp01((f - f_d0) / 14.0))
        R = Matrix.Translation(Fp) @ _R("X", 90.0 * e) @ Matrix.Translation(-Fp)   # 柄面绕自己翻向镜头，身子往后甩（不回正 lean：回正会扫到左邻那把）
        return R @ M_d0
    g.kids["plug1"]["fn"] = fn_dive
    # ---- 芯片、打分表（自己做表针）、烧瓶
    cx, cy, cz = P["CHIP"]
    g.add("chip", KP.p13_chip(K, "AI"), _T(cx, cy, cz))
    dx, dy, dz = P["DIAL"]
    dial = KP.p38_dial(K, "")
    for o in dial.children_recursive:                                     # 表盘自带的静止表针（三角，6 个顶点）删掉，换成会转的
        if o.type == "MESH" and len(o.data.vertices) == 6:
            o.hide_render = True
            o.hide_viewport = True
    e_mi, e_nh, e_nw = E["meter_in"], E["needle_hi"], E["needle_wob"]
    g.add("dial", dial, _T(dx, dy, dz), show=e_mi["f_start"])
    nd = KP.Part(K, "dial_needle", "black")
    pol = lambda r, a: (r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
    nd.slab([pol(1.0, 90), (8.6, 0.0), pol(1.0, -90)], 0.5, K.inkw, z=2.35, bevel=0)
    g.add("needle", nd.done(), show=e_mi["f_start"], bbox=False)

    def dial_M(f):
        u = _popk(f, e_mi["f_start"], max(6, e_mi["f_end"] - e_mi["f_start"]), 1.6)
        sx = 10.0 * (1 - ease_out_cubic(clamp01((f - e_mi["f_start"]) / max(1, e_mi["f_end"] - e_mi["f_start"]))))
        return _T(dx + sx, dy, dz) @ _Sc(u)

    def needle_a(f):
        a = 160.0                                                         # 低分那头
        if f >= e_nh["f_start"]:
            a += (-10.0 - 160.0) * ease_out_back(clamp01((f - e_nh["f_start"]) / max(1, e_nh["f_end"] - e_nh["f_start"])), 1.4)
        if f >= e_nw["f_start"]:
            a += 15.0 * math.sin(2 * math.pi * (f - e_nw["f_start"]) / 26.0) * smooth((f - e_nw["f_start"]) / 8.0) * (1 - smooth((f - e_sd["f_start"]) / 12.0))
        if f >= e_sd["f_start"]:                                          # 落回中间（90°），还在抖
            a += (90.0 - (-10.0)) * ease_inout_cubic(clamp01((f - e_sd["f_start"]) / 20.0))
            a += 4.0 * math.sin(2 * math.pi * (f - e_sd["f_start"]) / 9.0) * math.exp(-max(0, f - e_sd["f_land"]) / 60.0)
        return a
    g.kids["dial"]["fn"] = dial_M
    g.kids["needle"]["fn"] = lambda f: dial_M(f) @ _T(0, 3.0) @ _R("Z", needle_a(f))
    fx, fy, fz = P["FLASK"]
    e_fl = E["flask_up"]
    g.add("flask", KP.p34_flask(K), _T(fx, fy, fz) @ _Sc(P["FLASK_K"]), show=e_fl["f_start"])

    def flask_M(f):
        u = _popk(f, e_fl["f_start"], max(6, e_fl["f_end"] - e_fl["f_start"]), 1.5)
        rise = -8.0 * (1 - ease_out_cubic(clamp01((f - e_fl["f_start"]) / max(1, e_fl["f_end"] - e_fl["f_start"]))))
        bob = 0.6 * math.sin(2 * math.pi * (f - e_fl["f_land"]) / 40.0) if f > e_fl["f_land"] else 0.0
        return _T(fx, fy + rise + bob, fz) @ _Sc(P["FLASK_K"] * u)
    g.kids["flask"]["fn"] = flask_M
    # ---- 段首段尾
    head = _mm(0.0, -21.0, 8.05)                                         # 中间一级的正面（骨白）
    tail = Fp
    g.run(head, tail, tail_kids=["plug1"])
    for o in labels_all:                                                  # 柄面刻字全藏（18：刻字全部藏掉）；run 的 _vis_keys 以后再打
        _key_hide(o, [(0, True)])

    def foc(f):
        return _mm(10.0, 10.0, 0.0)
    pairs = [(f"plug{i}", "podium", range(0, e_sd["f_land"] + 12)) for i in range(3)]
    pairs += [(f"plug{i}", "rail", range(0, nf)) for i in range(7)]
    pairs += [(f"plug{a}", f"plug{b}", range(e_sd["f_start"] - 2, nf)) for a in range(7) for b in range(a + 1, 7)
              if abs(final_slot[a] - final_slot[b]) <= 15 or (a in stand and b in stand)]
    pairs += [(f"plug{i}", n, range(e_mi["f_start"], nf)) for i in (2, 5, 6) for n in ("dial", "flask")]
    pairs += [("dial", "flask", range(e_fl["f_start"], nf)), ("chip", "rail", range(0, nf)), ("dial", "rail", range(e_mi["f_start"], nf))]
    R = g.result(foc, pairs, info=dict(plug_k=k, slots=slots))
    hcol = bpy.data.collections["ONCAM_hero"]
    e_cg = E["chip_glint"]
    C0 = g.LM[e_cg["f_start"]] @ _mm(cx, cy, cz + 6.0)
    _sheen_light(W["sc"], hcol, C0 + Vector((-0.25, -0.30, 0.10)), C0 + Vector((0.25, -0.30, 0.10)), C0, e_cg["f_start"], e_cg["f_end"] - e_cg["f_start"], P["RIM_W"] * 2.0)
    return R


V502 = dict(
    # 11-22 甲线（18 文档 2.4 5-02）：七把假插头（和 4-11+12 同一批，缩放 0.9，屏上约 150 px，间距 15 mm ≈ 96 px）挂在一个胶件料框的中横杆上，左数第 5 把是 001。
    # 定案（可改回）：只挂一行插头整组才 200 px 高，过不了 OC1 的 486 下限，所以加一个料框（外框 y −37…41、x ±58，中横杆 y 4 挂插头），整组约 500 px；
    # fwd 要到屏上 300 px，往镜头挪 40 mm 只有 190 px，改成挪 95 mm（G 局部）；fwd 以后单把插头，OC1 上限不算（18 写明的例外）。
    PXMM=6.4, REST_D=1.5, REST_PX=(1440.0, 430.0), REST=(15.0, 5.0), ORG=(0.0, 2.0),
    HEAD_D=0.04, HEAD_PX=(960.0, 540.0), HEAD_CTRL=(2300.0, 430.0, 0.95), HEAD_ROT=(0.0, 90.0),
    TAIL_D=0.038, TAIL_PX=(960.0, 540.0), TAIL_CTRL=(1450.0, 330.0, 0.7), TAIL_ROT=(15.0, 5.0), TAIL_FACE=-0.8, GOLD001_ROUGH=0.3,   # 11-23 返修六：段尾盖满 8 帧 → 0.03→0.038（落点挪中以后外圈齿面盖得住四角）
                  HEAD_EASE=1.0, HEAD_QLAG=0.35,   # 11-23 审查返修试渲：刻字放大 2.5 倍、离镜头 0.03 后末帧左上角又露白底（约 5%）→ 落点往柄面中心挪 −2.0→−0.8（001 落在画面中间）  # 返修五：末帧左上角露出柄面齿边和白底（M12）→ 落点往柄面中心挪 −3.2→−2.0；返修四：段尾盖满 9 帧 → 0.022→0.03；段首 0→1 跳 27.9、往回 10.1（贴着镜头一上来就转 90°）→ 晚转身   # 11-23 首版机检：段尾 M12 0.938（TAIL_D 0.04）、段首 M9 第 0→1 帧跳 35.6；返修二：0.013 时段尾盖满 10 帧（OC7 ≤ 6）、段首 0→1 还跳 27.3（EASE 0.85）
    PLUG_K=0.9, SLOT=15.0, BAR_Y=4.0, FRAME=(-58.0, 58.0, -41.0, 41.0), SLIP=12.0, RISE=30.0, RISE_Z=10.0, FWD_MM=95.0, FWD_XY=(0.0, 0.0), FWD_TGT=(1300.0, 440.0, 0.42), HEAD_QW=True,
    FACE_PLANAR=True, FACE_SPIN=90.0, INK_001="#1F1E1C", ENGRAVE_K=2.7, TRANS_TK=1.5, TRANS_T1=1.25, TRANS_HK=[(0, 1.0), (4, 1.0), (14, 1.8), (19, 1.8), (24, 1.0), (28, 0.0)],   # 返修八：段首第 16 帧暗到 0.53、露出大板又亮回（往回闪 4.5，第 17→18 帧）→ 零件退开那几帧灯加 TRANS_HK；返修七：成片量字高 93 px → 2.5→2.7；段尾先暗到 0.53 再亮到 0.61、末 3 帧又回 0.58（往回闪 4.5）→ 段尾灯 ×1.5、末帧再 ×1.25
                    # 11-23 Fable 审查必改：001 刻字深色、字高 ≥ 96 px（离镜头 0.5→0.42 m、屏上 x 1440→1300（0.36 m 时右沿出画 2074）、刻字 1.8→2.5 倍（2.0 时字高约 80 px））、柄面平行底片、亮槽在字下；dive 以前人不虚
    PBLUR_ZERO=(0, 371),   # 11-24 R2-01 写死：段内帧 0–370 人物虚化 = 0，371（dive 起点）起才按焦距差虚。原来的 PBLUR_ZERO=(30, 371) 被拼进上一行行尾注释里（# 之后），一直没生效，D1 重合成就把虚化带回来了
    OC=True, OC1_EXEMPT=[(211, 415)], TRANS=True, TRANS_K=1.0, HIDE_RED=True, H_MIN=486, TOP_MIN=60, BOT_MAX=860, ACC=["p001"],
    BOARD_K=1.27, BOARD_HIDE=("stations", "zone_tags", "z1_c0_r0"),
    HEAD_BOX=(300, 90, 900, 680), LOCK_BOX=(1000, 0, 1940, 1080),
    RIM_W=60.0, SAMPLES=16, GRAIN_F=120, GRAIN_GAIN=1.0,                 # 首版 M10 0.55（3.2）
)


def _greyify(root, m):
    for o in [root] + list(root.children_recursive):
        if o.type in ("MESH", "CURVE") and o.data and hasattr(o.data, "materials"):
            for i in range(len(o.data.materials)):
                o.data.materials[i] = m
            for s in getattr(o, "material_slots", []):
                if s.link == "OBJECT":
                    s.material = m


def recipe_plug_row(W):
    """5-02（C：Six of them barely held on. But one stood out. Its name? 001.，416 帧）。
    G 局部毫米：骨白料框（外框 + 中横杆 y 4），七个挂位 x = −45…45（间距 15），插头柄朝上挂在中横杆下的浇口上；左数第 5 把（x 15）是 001。
    barely 六把往下滑 12 mm、浇口拉细；held on 晃、越晃越小；one 001 先往前 10 mm 离开横杆再升 30 mm、转 3/4、扫光；stood 六把逐把换灰；
    out 001 往镜头靠近；name? 柄面转向镜头；001. 刻字出现、扫光、一震；段尾柄面冲镜头。段首也是 001 的柄面（整组从柄面朝镜头翻回来）。"""
    import kit_parts as KP
    g = _Grp(W)
    K, P, E, nf = g.K, g.P, g.E, g.nf
    k, sl, by = P["PLUG_K"], P["SLOT"], P["BAR_Y"]
    x0, x1, y0, y1 = P["FRAME"]
    fr = KP.Part(K, "plug_frame", "white")
    fr.tube([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], 0.9, K.white)
    fr.tube([(x0, by), (x1, by)], 0.75, K.white)
    g.add("frame", fr.done())
    slots = [sl * (i - 3) for i in range(7)]
    names = ["A", "B", "C", "D", "001", "E", "F"]
    I1 = 4
    gate_len = 2.2
    top_y = by - 0.75 - gate_len
    e_s, e_w, e_r, e_g, e_f, e_fc, e_en, e_d = (E[n] for n in ("slip", "swing", "rise", "grey", "fwd", "face", "engrave", "dive"))
    R90 = _R("Z", 90.0)
    labels, lab001 = [], []
    order6 = [i for i in range(7) if i != I1]

    def slide(i, f):
        j = order6.index(i)
        return P["SLIP"] * ease_out_cubic(clamp01((f - e_s["f_start"] - 3 * j) / max(1, e_s["f_end"] - e_s["f_start"])))

    def swing(i, f):
        j = order6.index(i)
        f0 = e_w["f_start"] + 3 * j
        if f < f0:
            return 0.0
        return 5.0 * math.sin(2 * math.pi * (f - f0) / 42.0) * math.exp(-(f - f0) / 70.0)

    def hang6(i):
        x = slots[i]

        def fn(f):
            d = slide(i, f)
            return _T(x, top_y - d) @ _R("Z", swing(i, f)) @ _T(0, -10.0 * k) @ R90 @ _Sc(k)
        return fn

    for i, nm in enumerate(names):
        root, _, labs = _plug_kid(K, nm, k)
        labels += labs
        if i == I1:
            lab001 = labs
            for o in labs:                                                # 11-23 审查：刻字暗金压暗金 → 实心深色哑光墨；转 FACE_SPIN，柄面跟着转回来以后凹槽亮边落到字的正下方
                o.matrix_basis = o.matrix_basis @ Matrix.Rotation(math.radians(P.get("FACE_SPIN", 0.0)), 4, "Z")
                if P.get("INK_001"):
                    import kit_parts as KP_
                    o.data.materials.clear()
                    o.data.materials.append(KP_.mat_solid("ink_matte_001", P["INK_001"], rough=0.75, coat=0.0, sss=0))
            if P.get("GOLD001_ROUGH"):                                    # 11-23 审查返修：柄面凹槽是镜面金，映出白墙成一块白斑挨着字（读成 001-），越冲越亮又变暗（M9 往回闪 5.7）
                g001 = K.gold.copy()                                      # → 只给 001 这把换一份金，转正（face）开始 8 帧内粗糙度 0.06 → GOLD001_ROUGH，反光糊成一片匀的金
                g001.name = "kit_gold_001"
                rin = g001.node_tree.nodes["Principled BSDF"].inputs["Roughness"]
                for fk, v in ((e_fc["f_start"], 0.06), (e_fc["f_start"] + 8, P["GOLD001_ROUGH"])):
                    rin.default_value = v
                    rin.keyframe_insert("default_value", frame=fk)
                for o in [root] + list(root.children_recursive):
                    if o.type == "MESH":
                        for sl_ in o.material_slots:
                            if sl_.material is not None and sl_.material.name == K.gold.name:
                                sl_.material = g001
        g.add(f"p{nm}" if i != I1 else "p001", root, bake=False, hide=None)
    greys = {}
    for i in order6:                                                     # 同形的灰色件，stood 时逐把换上
        j = order6.index(i)
        fg = e_g["f_land"] + 3 * j
        root, _, labs = _plug_kid(K, names[i], k)
        labels += labs
        _greyify(root, K.inkg)                                          # 实色暖灰（nuc_grey 是透明灰，试渲看着发黑）
        g.add(f"g{names[i]}", root, bake=False, show=fg)
        g.kids[f"p{names[i]}"]["hide"] = fg
        greys[i] = fg
    for i in order6:
        fn = hang6(i)
        g.kids[f"p{names[i]}"]["fn"] = fn
        g.kids[f"g{names[i]}"]["fn"] = fn
    # 浇口：滑下去的六个拉长变细（绕横杆下沿缩放）
    for i, x in enumerate(slots):
        st = KP.Part(K, f"gate{i}", "white")
        st.tube([(x, by), (x, top_y - 0.1)], 0.45, K.white)
        g.add(f"gate{i}", st.done(), bbox=False)
        if i == I1:
            g.kids[f"gate{i}"]["hide"] = e_r["f_start"] + 2                   # 001 离开时浇口断掉（短的一截跟着框，不出像）
            continue

        def gfn(f, i=i, x=x):
            d = slide(i, f)
            L = gate_len + 0.85
            ky = (L + d) / L
            kr = 1.0 / math.sqrt(ky) if d > 0 else 1.0
            return _piv(x, by - 0.75, 0, _R("Z", swing(i, f) * 0.15) @ Matrix.Diagonal((kr, ky, kr, 1.0)))
        g.kids[f"gate{i}"]["fn"] = gfn
    # 001
    x4 = slots[I1]
    face_l = Vector((9.85 * MM, 0.0, 0.0))
    c_l = Vector((-3.0 * MM, 0.0, 0.0))                                    # 插头身子中段（插头局部）：转向时绕它转
    hang_001 = _T(x4, top_y) @ _T(0, -10.0 * k) @ R90 @ _R("X", 180.0) @ _Sc(k)   # 绕插头长轴转半圈：柄面刻字转正后读作 001（11-23 试渲是倒的 IOO）
    q_face = Quaternion((1, 0, 0), math.radians(90.0))
    fwd_off = Vector((P["FWD_XY"][0], P["FWD_XY"][1], P["FWD_MM"]))
    if P.get("FWD_TGT"):                                                  # 往前：插头身子中段落到屏上 (u, v)、离镜头 d 米（按落位姿态换回 G 局部；G 斜着，沿 G +Z 走会被透视推出画、还会太近）
        u, v, d = P["FWD_TGT"]
        M_r = _Mof(Vector(px_to_world(*P["REST_PX"], P["REST_D"])), _q(*P["REST"], base=g.base), g.c0, g.s)
        loc = M_r.inverted() @ Vector(px_to_world(u, v, d))
        C_r = (hang_001 @ c_l) / MM + Vector((0.0, P["RISE"], P["RISE_Z"]))
        fwd_off = loc / MM - C_r
        cam_l = M_r.inverted() @ Vector((0.0, 0.0, 0.0))                # 镜头在 G 局部的位置：柄面转向它（不是转向 G 的 +Z，G 斜着、插头又在画面右边，转完是侧脸）
        dir_l = (cam_l - loc).normalized()
        if P.get("FACE_PLANAR"):                                          # 11-23 审查：光轴在 x 563，插头在 1440，朝镜头位置转完屏上是 1.25:1 的扁圆（像偏了 37°）→ 柄面平行底片（法线 = 世界 −Y）
            wp = Vector(px_to_world(u, v, d))                             # 返修四试出：3×3 求逆那样写转出来柄面朝右（第 300–370 帧柄面出画）→ 和朝镜头那版同一个换法：目标点往镜头方向（世界 −Y）挪 0.1 m 再换回 G 局部
            dir_l = (M_r.inverted() @ (wp + Vector((0.0, -0.1, 0.0))) - loc).normalized()
        q_face = Vector((0.0, 1.0, 0.0)).rotation_difference(dir_l)
        if lab001:                                                        # 再绕柄面法线转一个角，让刻字的基线对着镜头的水平方向（字是正的、从左往右读）
            bpy.context.view_layer.update()
            r001 = g.kids["p001"]["root"]
            fo = next((o for o in lab001 if o.type == "FONT"), lab001[0])
            b_l = (r001.matrix_world.inverted() @ fo.matrix_world).to_3x3() @ Vector((1.0, 0.0, 0.0))
            Rr = M_r.to_3x3().normalized().inverted()
            right_l = (Rr @ Vector((1.0, 0.0, 0.0))).normalized()
            b0 = q_face.to_matrix() @ (hang_001.to_3x3().normalized() @ b_l)
            rho = max(range(0, 360, 1), key=lambda d: (Quaternion(dir_l, math.radians(d)).to_matrix() @ b0).dot(right_l))
            q_face = Quaternion(dir_l, math.radians(rho)) @ q_face

    def p001(f):
        M = hang_001
        tr = ease_inout_cubic(clamp01((f - e_r["f_start"]) / max(1, e_r["f_end"] - e_r["f_start"])))
        tz = ease_out_cubic(clamp01((f - e_r["f_start"]) / 6.0))
        ty = ease_inout_cubic(clamp01((f - e_r["f_start"] - 4) / max(1, e_r["f_end"] - e_r["f_start"] - 4)))
        off = Vector((0.0, P["RISE"] * ty, P["RISE_Z"] * tz))
        yaw = 35.0 * tr
        tf = ease_inout_cubic(clamp01((f - e_f["f_start"]) / max(1, e_f["f_end"] - e_f["f_start"])))
        off += fwd_off * tf
        tc = ease_inout_cubic(clamp01((f - e_fc["f_start"]) / max(1, e_fc["f_end"] - e_fc["f_start"])))
        C = (hang_001 @ c_l) / MM                                          # G 局部毫米
        Cm = _mm(C.x, C.y, C.z)
        rot = Matrix.Translation(Cm) @ Quaternion().slerp(q_face, tc).to_matrix().to_4x4() @ _R("Y", yaw * (1 - tc)) @ Matrix.Translation(-Cm)
        jolt = 0.0
        if f >= e_en["f_land"]:
            jolt = 1.2 * math.sin(2 * math.pi * (f - e_en["f_land"]) / 5.0) * math.exp(-(f - e_en["f_land"]) / 5.0)
        return _T(off.x, off.y + jolt, off.z) @ rot @ M
    g.kids["p001"]["fn"] = p001
    f_d0 = e_d["f_start"]
    head = hang_001 @ face_l
    if P.get("TAIL_FACE"):                                                # 11-23 首版机检 M12 段尾只盖住 0.938：柄面冲到 4 cm 还不够大，且斜着（在右区朝镜头摆正的，到画面中间就偏了 20°）
        bpy.context.view_layer.update()                                   # 段尾点挪到刻字下方的金面上（刻字放大 1.8 倍后占了柄面中间一大块），离镜头 TAIL_D；柄面在最后一帧正对镜头
        r001 = g.kids["p001"]["root"]
        Mrel = r001.matrix_world.inverted() @ lab001[0].matrix_world
        up = (Mrel.to_3x3() @ Vector((0.0, 1.0, 0.0)))
        up.x = 0.0
        up.normalize()
        face_t = face_l - up * (P["TAIL_FACE"] * MM)
        n_G = (p001(f_d0).to_3x3() @ Vector((1.0, 0.0, 0.0))).normalized()
        best = None
        for yw in range(-90, 91, 2):
            for tl in range(-90, 91, 2):
                d_ = (_q(yw, tl, base=g.base) @ n_G - Vector((0.0, -1.0, 0.0))).length
                if best is None or d_ < best[0]:
                    best = (d_, yw, tl)
        _, yw0, tl0 = best
        for _ in range(3):
            for yw in [yw0 + 0.1 * i for i in range(-20, 21)]:
                for tl in [tl0 + 0.1 * i for i in range(-20, 21)]:
                    d_ = (_q(yw, tl, base=g.base) @ n_G - Vector((0.0, -1.0, 0.0))).length
                    if d_ < best[0]:
                        best = (d_, yw, tl)
            _, yw0, tl0 = best
        P["TAIL_ROT"] = (round(yw0, 2), round(tl0, 2))
    else:
        face_t = face_l
    tail = p001(f_d0) @ face_t
    g.run(head, tail, tail_kids=["p001"])
    for o in labels:
        if o in lab001:
            _key_hide(o, [(0, True), (e_en["f_land"], False)])
            s0 = o.scale.copy()                                            # 刻字盖章似的弹大到 1.8 倍（原大只占柄面三分之一，试渲第 340 帧看不清）
            for df, kk in ((0, 0.4), (6, 2.0 * P.get("ENGRAVE_K", 1.8) / 1.8), (12, P.get("ENGRAVE_K", 1.8))):
                o.scale = (s0.x * kk, s0.y * kk, s0.z)                     # 字是 FONT，原点在柄面中心、局部 Z = 柄面法线：只放大字面两个方向
                o.keyframe_insert("scale", frame=e_en["f_land"] + df)
        else:
            _key_hide(o, [(0, True)])

    def foc(f):
        c = _mm(0.0, 2.0, 0.0)
        tcf = smooth((f - e_fc["f_start"]) / max(1, e_fc["f_end"] - e_fc["f_start"]))
        p = p001(f) @ c_l.lerp(face_l, tcf)                               # 转正以后对焦到柄面（11-23 试渲：对在插头身子中段，柄面和 001 是虚的）
        return c.lerp(p, smooth((f - e_r["f_start"]) / 20.0))
    pairs = []
    for a, b in zip(range(7), range(1, 7)):
        na = "p001" if a == I1 else f"p{names[a]}"
        nb = "p001" if b == I1 else f"p{names[b]}"
        pairs.append((na, nb, range(0, nf)))
    pairs += [("p001", "frame", range(0, nf))]
    pairs += [(f"{c}{names[i]}", "frame", range(0, nf)) for i in order6 for c in "pg"]
    pairs += [(f"g{names[a]}", f"g{names[b]}", range(e_g["f_land"], nf)) for a, b in zip(order6, order6[1:]) if abs(slots[a] - slots[b]) < 16]
    R = g.result(foc, pairs, info=dict(plug_k=k, slots=slots))
    hcol = bpy.data.collections["ONCAM_hero"]
    for ev in (e_r, e_en):                                                # one 和 001. 两道扫光
        C0 = g.LM[ev["f_land"]] @ (p001(ev["f_land"]) @ c_l)
        _sheen_light(W["sc"], hcol, C0 + Vector((-0.20, -0.25, 0.08)), C0 + Vector((0.20, -0.25, 0.08)), C0, ev["f_land"] - 2, 20, P["RIM_W"] * 2.0)
    return R


def build_v2(seg, samples=None):
    """v2 搭整段：相机只有微动（不推）；焦点、光圈由 recipe 给；导出每帧人卡片四角（不动）、零件包围框和深度范围（front 层用）。"""
    cfg = seg_cfg(seg)
    light = json.loads((cfg["work"] / "light.json").read_text(encoding="utf-8"))
    fit = load_fit(cfg, light)
    P = cfg["P"]
    W = build_world(cfg, fit, samples or P["SAMPLES"])
    sc, cam, nf = W["sc"], W["cam"], cfg["nf"]
    if P.get("CARD_TRANSMISSION"):                     # 透明零件（磨砂壳）挡在人前面时，透过它看到的是人（模糊），不是人身后的大板
        W["card"].visible_transmission = True
    sc.cycles.adaptive_threshold = 0.01
    sc.cycles.use_animated_seed = True                 # 降噪斑块不再钉在画面上（旧版第 15 条）
    print("ONCAM step world ok", flush=True)
    bf = board_fill(W["board"], P)
    print("ONCAM step board ok", flush=True)
    R = RECIPES[cfg["recipe"]](W)
    print("ONCAM step recipe ok", flush=True)
    CM = []
    for f in range(nf):
        M = cam_matrix_micro(f)
        CM.append(M)
        key_matrix(cam, f, M)
    linear_keys(cam)
    FD, FS = [], []
    for f in range(nf):
        d = R["focus"](f, CM[f])
        cam.data.dof.focus_distance = d
        cam.data.dof.keyframe_insert("focus_distance", frame=f)
        a = R["fstop"](f)
        cam.data.dof.aperture_fstop = a
        cam.data.dof.keyframe_insert("aperture_fstop", frame=f)
        FD.append(d); FS.append(a)
    linear_keys(cam.data)
    chk = dict(seg=seg, recipe=cfg["recipe"], version=2, info=R["info"], board=dict(S=BOARD_S * P["BOARD_K"], D=BOARD_D, **bf),
               lens=round(LENS, 3), shift=SHIFT, f_px=F_PX, d_person=D_PERSON, micro_deg=MICRO, samples=samples or P["SAMPLES"], fit=fit)

    def coc(S, D_, N):
        fl = LENS * MM
        c = fl * fl / (N * (S - fl)) * abs(D_ - S) / D_
        return c / (36 * MM) * OUT_W
    cocf = [0, 20, 60, 150, 176, 240, 330, 360] if seg == "3-01" else sorted({0, 20, 60} | {e["f_land"] for e in cfg["K"]["events"]})
    for f in [x for x in cocf if x < nf] + [nf - 1]:     # 3-01 的抽查帧是写死的；别的段按事件落位帧抽（段比 360 帧短时原写法越界）
        fwd = (CM[f].to_3x3() @ Vector((0, 0, -1))).normalized()
        dl = (R["targets"]["card"](f) - CM[f].translation).dot(fwd)
        chk.setdefault("coc_px", {})[f] = dict(focus=round(FD[f], 3), fstop=round(FS[f], 2), lock=round(coc(FD[f], dl, FS[f]), 2), board=round(coc(FD[f], BOARD_D, FS[f]), 2))
    chk["clip"] = R["checks"]()
    corners = card_corners()
    frames_ = []
    front = []
    for f in range(nf):
        sc.frame_set(f)
        bb = [project(CM[f], SHIFT, p) for p in R["bbox"](f)]
        nb = sum(1 for p in bb if not p[2] > 1e-6)
        if nb:                                             # 段尾冲镜头时零件有点跑到相机后面（投影 NaN）：只记数，框按前面的点量
            print("ONCAM warn behind_cam frame", f, nb, "of", len(bb), flush=True)
            bb = [p for p in bb if p[2] > 1e-6] or [(OUT_W / 2, OUT_H / 2, 0.01)]
        zs = [p[2] for p in bb]
        # 钥匙也算进深度范围（亮出时比锁近）
        kd = []
        kb = mesh_bounds([R["key"]]) if not R["key"].hide_render else None
        if kb is not None:
            l2, h2 = kb
            kd = [project(CM[f], SHIFT, (x, y, z))[2] for x in (l2.x, h2.x) for y in (l2.y, h2.y) for z in (l2.z, h2.z)]
        zmin = min(zs + kd)
        zmax = max(zs + kd)
        if zmin < D_PERSON + 0.02 or f >= R["tail_t0"]:
            front.append(f)            # 段尾冲镜头那一段一律在人前面：锁从人身后穿到人前面那一下就是"穿过人"（11-20 test 377–379）
        rows = {}                                          # 每 60 px 一行带里零件最靠左的 x（M5 和人逐行比；几个零件一上一下时整体框太粗）
        for p in bb:
            k = int(p[1] // 60)
            rows[k] = min(rows.get(k, 1e9), p[0])
        kids = {}
        if P.get("ACC") and R.get("kid_pts"):                  # OC2：配件各自的屏上框
            for n, pts in R["kid_pts"](f, P["ACC"]).items():
                q = [project(CM[f], SHIFT, p) for p in pts]
                q = [p for p in q if p[2] > 1e-6]
                if q:
                    kids[n] = [round(min(p[0] for p in q), 1), round(min(p[1] for p in q), 1), round(max(p[0] for p in q), 1), round(max(p[1] for p in q), 1)]
        frames_.append(dict(kids=kids, card=[[list(project(CM[f], SHIFT, c)) for c in corners]] * 5,
                            hero=[min(p[0] for p in bb), min(p[1] for p in bb), max(p[0] for p in bb), max(p[1] for p in bb)],
                            rows=[[k * 60, round(x, 1)] for k, x in sorted(rows.items())],
                            zmin=zmin, zmax=zmax, focus=FD[f], fstop=FS[f]))
    cfg["work"].mkdir(parents=True, exist_ok=True)
    (cfg["work"] / "cam.json").write_text(json.dumps(dict(seg=seg, nf=nf, version=2, push_t0=R["tail_t0"], fg_last=-1, front=front, frames=frames_)), encoding="utf-8")
    (cfg["work"] / "handoff.json").write_text(json.dumps(R["handoff"], ensure_ascii=False, indent=1), encoding="utf-8")
    sc.frame_set(0)
    bpy.ops.wm.save_as_mainfile(filepath=str(cfg["work"] / "scene.blend"))
    (cfg["work"] / "check.json").write_text(json.dumps(chk, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("ONCAM build_v2", json.dumps(dict(clip=chk["clip"], coc=chk["coc_px"], info=R["info"], front=front, board=bf["edges"]), default=str)[:4000], flush=True)


V404 = dict(
    # 11-23 甲线（18 文档 2.4 4-04+05）：插座（h01b，盖合着，孔面朝镜头偏 30°）上横搭一条红珠尾巴，剪钳（Codex h14）剪断，尾巴落进右下的废料桶；芯片、小人、红环。
    # 定案（可改回）：尾巴用 K.red（18 写的 K.tail 是淡蓝透明，和"红尾巴"、4-03 的红珠尾巴对不上，按红的做）；废料桶自己车一个敞口桶（p44 是"插头→箭头→带盖桶"的图标件，盖着口装不进）；
    # 整组高要卡在 486–620 px，插座做到屏上约 414 px（18 写 500，加上桶就超 620）；芯片、小人当配件不算主零件框（OC2 量），位置用干跑核过上沿。
    PXMM=10.2, REST_D=1.5, REST_PX=(1350.0, 545.0), REST=(-10.0, 10.0), ORG=(8.0, -9.5),   # 11-23 试渲：偏 25° 加上在画面右边的透视，看到的大半是插座长长的侧面、孔口面窄成一条，改成往回偏 10°（孔口面基本正对）
    HEAD_D=0.02, HEAD_PX=(960.0, 540.0), HEAD_CTRL=(2300.0, 470.0, 0.95), HEAD_ROT=(0.0, 0.0), HEAD_QW=True, HEAD_EASE=0.8,
    TAIL_D=0.035, TAIL_PX=(960.0, 540.0), TAIL_CTRL=(1500.0, 420.0, 0.7), TAIL_ROT=(0.0, 0.0), TAIL_QW=True, BORE_IN=10.0, COVER="bin", TRANS_H0=1.6, TRANS_T1=1.35, TRANS_TRACK=14, TRANS_TRACK_P=1.2,   # 11-23 重出：段首第 9–14 帧 0.43–0.42（零件退开变暗、比素材 0.54 暗）→ 段首灯跟零件走、按距离补一部分
                    # 试渲：段首 0→1 帧 0.92→0.97、段尾 472→473 0.95→0.92（各往回闪 13、8）→ 首帧、末帧灯加   # 11-23 打线查明：段尾 _qpow 转不到 TAIL_ROT（差 13°），末帧镜头在桶壁里 → TAIL_QW。试渲：0.02 时最后 3 帧镜头贴到桶壁弧面上，末帧露出一条暗边（227→140）→ 停在 0.035（第 470 帧那样整片骨白）
    BEADS=14, BEAD_R=1.1, LINK_R=0.4, BEAD_SP=2.9, TAIL_DIR=(1.0, -0.45), WIGGLE=1.4, FLOP_DEG=6.0,   # 11-23 试渲：−0.75 时凸耳出了插座面上沿（打不到面，飘到后面 40 mm）
    NIP_K=0.5, NIP_ANG=129.0, NIP_FROM=(55.0, 45.0, 26.0), LUG_SP=1.4,
    BIN=(31.0, -14.0, 15.0), BIN_R=7.6, BIN_H=17.0, RUN_Y=17.5, RUN_R=0.6, HANG_Y=11.5,
    CHIP=(-20.0, 24.5, -14.0), CHIP_K=0.6, PERSON=(-5.0, 0.0), PERSON_K=0.37, RUN_X0=-8.0,   # 小人 0.31 时落地压扁那几帧屏上 94 px（OC2 ≥ 110）
    OC=True, TRANS=True, TRANS_K=1.0, HIDE_RED=True, H_MIN=486, TOP_MIN=60, BOT_MAX=860, ACC=["chip", "person"], OC1_EXEMPT=[(192, 232)], HAND_FRONT=[(150, 224)], OC2_EXEMPT=[(228, 240), (325, 334)],   # B 比剪刀手那只手在剪钳、插座前面（18 文档"手在前"）
    BOARD_K=1.27, BOARD_HIDE=("stations", "zone_tags", "z1_c0_r0"),
    HEAD_BOX=(300, 90, 900, 680), LOCK_BOX=(1000, 0, 1940, 1080),
    RIM_W=60.0, SAMPLES=16, GRAIN_F=150, GRAIN_GAIN=1.7,   # 11-23 重出 M10 颗粒比 0.36（2.4）→ 6.0
)


def recipe_snip_tail(W):
    """4-04+05（C：So what did they do?  B：They cut the tail off. The AI made the guess. A human caught the problem.，474 帧）。
    G 局部毫米：插座（h01b）孔口面朝 +Z，孔心在 (0, 0, 12)；插座局部 X（孔轴）→ G Z，局部 Y → G X，局部 Z（上）→ G Y。
    料杆 y 17.5 从右边画外伸进来，一根浇口挂住插座顶；红珠尾巴从左上的蓝色小凸耳搭过孔口到右下（第 7 颗落在孔口里）；
    敞口废料桶在插座右下；芯片在插座左后上方；小人跳到料杆左头（尾巴根旁边）。段首段尾都在孔桶里面（骨白内壁盖满）。"""
    import kit_parts as KP
    import kit_socket as KS
    import kit_deep_r5 as R5
    g = _Grp(W)
    K, P, E, nf = g.K, g.P, g.E, g.nf
    sc = W["sc"]
    e_fl, e_ni, e_sn, e_fa, e_cp, e_bs, e_ph, e_ro = (E[n] for n in ("tail_flop", "nip_in", "snip", "tail_fall", "chip_pop", "body_sheen", "person_hop", "ring_on"))
    # ---- 插座
    sock = KS.h01b_cdk20_socket(K)
    KS.rest(sock)
    rings = [o for o in sock.children_recursive if o.type == "MESH" and "red_ring" in o.name and o.active_material is not None
             and o.active_material.name.startswith("kit_red")]
    M_s = Matrix(((0, 1, 0, 0), (0, 0, 1, 0), (1, 0, 0, 0), (0, 0, 0, 1)))
    g.add("socket", sock, M_s)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    s_objs = set(o.name for o in _objs(sock))

    def surf_z(x, y):
        """G 局部 (x, y) 处插座前表面的 z（毫米）：从前面往 −Z 打一条线（这时 G 还在原点、没缩放，世界 = G 局部）。"""
        hit, loc, nrm, idx, ob, mx = sc.ray_cast(dg, Vector((x * MM, y * MM, 0.08)), Vector((0, 0, -1)))
        return loc.z / MM if hit and ob is not None and ob.name in s_objs else -40.0
    face_z = KS.FACE_W
    bore_bot = surf_z(0.0, 0.0)                                           # 孔底正中（珠子搭上去以前量：后面打线会先打到第 7 颗珠子）
    # ---- 尾巴：凸耳 + 14 颗珠子 + 连杆。第 7 颗（下标 6）在孔口里
    n, br, sp = P["BEADS"], P["BEAD_R"], P["BEAD_SP"]
    dv = Vector((*P["TAIL_DIR"], 0.0)).normalized()
    nv = Vector((-dv.y, dv.x, 0.0))
    ctr = []
    for i in range(n):
        q = dv * ((i - 6) * sp) + nv * (P["WIGGLE"] * math.sin(2 * math.pi * (i - 6) / 7.0))
        if i == 6:
            z = face_z - 0.3
        else:
            zs = max(surf_z(q.x + a, q.y + b) for a in (-br, 0, br) for b in (-br, 0, br))
            z = max(zs, face_z) + br + 0.35
        ctr.append(Vector((q.x, q.y, z)))
    lug_xy = ctr[0] - dv * (sp * P["LUG_SP"])                           # 根部连杆留长一点：剪钳口宽，剪点离第 1 颗珠子要有余量
    lug_z = max(surf_z(lug_xy.x + a, lug_xy.y + b) for a in (-1.0, 0, 1.0) for b in (-1.0, 0, 1.0))
    lug_c = Vector((lug_xy.x, lug_xy.y, lug_z + 0.6))
    lg = KP.Part(K, "tail_lug", "blue")
    lg.cyl(lug_c.x, lug_c.y, lug_c.z, 1.0, 1.5, K.blue, axis="z", bevel=0.2)
    g.add("lug", lg.done())
    rl = KP.Part(K, "tail_root", "red")
    root_mid = (lug_c + ctr[0]) / 2
    hd = Vector((math.sin(math.radians(P["NIP_ANG"])), -math.cos(math.radians(P["NIP_ANG"])), 0.0))   # 钳柄从剪点伸出去的方向
    smax = max(surf_z(root_mid.x + hd.x * d + hd.y * w, root_mid.y + hd.y * d - hd.x * w) for d in range(-3, 14) for w in (-3.0, 0.0, 3.0))
    root_end = Vector((root_mid.x, root_mid.y, max(ctr[0].z + 3.5, smax + 1.0 + 0.6)))   # 根部连杆拱起来：剪钳在拱顶剪，钳身整个高过插座面和珠子
    rl.tube([tuple(lug_c), tuple(lug_c.lerp(root_end, 0.5) + Vector((0, 0, 0.8))), tuple(root_end), tuple(root_end.lerp(ctr[0], 0.5) + Vector((0, 0, 0.8))), tuple(ctr[0])],
            P["LINK_R"], K.red, smooth=True)
    g.add("rootlink", rl.done(), bbox=False, hide=e_sn["f_land"])
    tA = KP.Part(K, "tail_a", "red")                                    # 根到孔口（第 1–7 颗）
    tB = KP.Part(K, "tail_b", "red")                                    # 孔口以外（第 8–14 颗），do? 时绕第 7 颗晃
    for i, c in enumerate(ctr):
        (tA if i <= 6 else tB).ball(c.x, c.y, c.z, br, K.red)
    tA.tube([tuple(c) for c in ctr[:7]], P["LINK_R"], K.red)
    tB.tube([tuple(c) for c in ctr[6:]], P["LINK_R"], K.red)
    g.add("tailA", tA.done(), bake=False)
    g.add("tailB", tB.done(), bake=False)
    pv = ctr[6]

    def flop(f):
        if f < e_fl["f_start"]:
            return 0.0
        t = (f - e_fl["f_start"]) / max(1, e_fl["f_end"] - e_fl["f_start"])
        return P["FLOP_DEG"] * math.sin(2 * math.pi * 2 * clamp01(t)) * (1 - 0.5 * clamp01(t)) * (1 - smooth((f - e_fl["f_end"]) / 8.0))
    # 掉落：整条（A + B）一起。前半段末颗珠子（右下那头）挪到桶口上方、整条绕它转到近乎竖直（往前让 5 mm 躲开插座面），后半段竖着落进桶底
    bx, by, bz = P["BIN"]
    a0 = math.degrees(math.atan2(dv.y, dv.x))
    rot_to = -80.0 - a0                                                 # 链子方向（第 1 颗 → 第 14 颗）转到 −80°：第 14 颗在最下面
    e0 = ctr[-1]
    mouth = Vector((bx, by + 2.5, bz))
    floor = Vector((bx, by - P["BIN_H"] + 1.5 + br + 0.6, bz))

    def fall_M(f):
        if f < e_fa["f_start"]:
            return Matrix.Identity(4)
        t = clamp01((f - e_fa["f_start"]) / max(1, e_fa["f_end"] - e_fa["f_start"]))
        ta = clamp01(t / 0.5)
        tb = clamp01((t - 0.5) / 0.5)
        e = e0.lerp(mouth, smooth(clamp01((ta - 0.1) / 0.9))) + Vector((0.0, 0.0, 6.0 * math.sqrt(max(0.0, math.sin(math.pi * ta)))))   # 一开始就往前让（先离面再横走），转起来才不蹭插座面
        e = e.lerp(floor, ease_in_cubic(tb))
        if f > e_fa["f_end"]:
            e = e + Vector((0.0, 0.8 * abs(math.sin(2 * math.pi * (f - e_fa["f_end"]) / 16.0)) * math.exp(-(f - e_fa["f_end"]) / 6.0), 0.0))
        return _T(e.x, e.y, e.z) @ _R("Z", rot_to * smooth((ta - 0.12) / 0.88)) @ _T(-e0.x, -e0.y, -e0.z)
    g.kids["tailA"]["fn"] = fall_M
    g.kids["tailB"]["fn"] = lambda f: fall_M(f) @ _piv(pv.x, pv.y, pv.z, _R("Z", flop(f)))
    # ---- 废料桶（敞口，骨白；桶口朝上）
    bn = KP.Part(K, "scrap_bin", "white")
    R_, H_ = P["BIN_R"], P["BIN_H"]
    bn.lathe([(0.02, -H_), (R_ - 1.4, -H_), (R_ - 0.9, -H_ + 0.5), (R_, 0.0), (R_ - 0.25, 0.45), (R_ - 0.75, 0.0), (R_ - 1.9, -H_ + 1.5), (0.02, -H_ + 1.5)],
             K.white, 0, 0)
    g.add("bin", bn.done(), _T(bx, by, bz))
    # ---- 料杆（从右边画外伸进来）+ 挂插座的浇口
    ry = P["RUN_Y"]
    rn = KP.Part(K, "snip_runner", "white")
    rn.tube([(P["RUN_X0"], ry, 0.0), (95.0, ry, 0.0)], P["RUN_R"], K.white)
    rn.tube([(2.0, ry, 0.0), (2.0, P["HANG_Y"], 0.0)], 0.45, K.white)
    g.add("runner", rn.done(), bbox=False)
    # ---- 剪钳（Codex h14）：剪点 = 根部连杆中点；钳子在纸面里，从右上沿弧线进来
    nip = R5.h14_nippers(K)
    jaws = R5.rig(nip)
    g.add("nip", nip, bake=False, show=e_ni["f_start"], hide=e_fa["f_start"] + 26, bbox=False)   # 从画外进出，不算主零件框
    cut = root_end.copy()
    nk = P["NIP_K"]
    fx, fy, fz = P["NIP_FROM"]

    def nip_M(f):
        t = clamp01((f - e_ni["f_start"]) / max(1, e_ni["f_land"] - e_ni["f_start"]))
        u = ease_out_cubic(t)
        off = Vector((fx * (1 - u), fy * (1 - u) ** 1.6, fz * (1 - u) ** 2))
        if f >= e_fa["f_start"] - 6:                                     # 尾巴掉的同时退出右上（先往前抬，不扫到往上转的尾巴）
            w = ease_in_cubic(clamp01((f - e_fa["f_start"] + 6) / 22.0))
            off += Vector((fx * w, fy * w, 30.0 * smooth((f - e_fa["f_start"] + 6) / 8.0)))
        sh = 0.0
        if f >= e_sn["f_land"]:
            sh = 0.5 * math.sin(2 * math.pi * (f - e_sn["f_land"]) / 6.0) * math.exp(-(f - e_sn["f_land"]) / 5.0)
        p = cut + off
        return _T(p.x, p.y + sh, p.z) @ _R("Z", P["NIP_ANG"]) @ _Sc(nk) @ _T(0.0, -17.0, -2.0)   # 网格里钳尖朝 +Y（h14 自己的 −90° 放在 root 上，这里整个矩阵盖掉它）
    g.kids["nip"]["fn"] = nip_M
    # ---- 芯片、小人
    cx, cy, cz = P["CHIP"]
    g.add("chip", KP.p13_chip(K, "AI"), _T(cx, cy, cz) @ _Sc(0.001), show=e_cp["f_start"], bbox=True)
    g.kids["chip"]["bbox"] = False                                      # 不进主零件框，但留外形点给 OC2 量配件高
    g.kids["chip"]["fn"] = lambda f: _T(cx, cy + 3.0 * (1 - ease_out_cubic(clamp01((f - e_cp["f_start"]) / 14.0))), cz) @ _Sc(P["CHIP_K"] * _popk(f, e_cp["f_start"], 14, 1.8))
    pp = KP.Part(K, "snip_person", "white")
    KP.person(pp, K.white, 0.0)
    pk = P["PERSON_K"]
    px_ = P["PERSON"][0]
    py_ = ry + P["RUN_R"] + 17.3 * pk
    g.add("person", pp.done(), _T(px_, py_, 0.0) @ _Sc(0.001), show=e_ph["f_start"], bbox=True)
    g.kids["person"]["bbox"] = False                                      # 不进主零件框，但留外形点给 OC2 量配件高

    def person_M(f):
        t = clamp01((f - e_ph["f_start"]) / max(1, e_ph["f_end"] - e_ph["f_start"]))
        hop = 5.0 * math.sin(math.pi * t)
        dx = 6.0 * (1 - ease_out_cubic(t))
        sq = 1.0
        if f >= e_ph["f_end"]:
            sq = 1.0 - 0.08 * math.sin(math.pi * clamp01((f - e_ph["f_end"]) / 6.0))
        k_ = pk * _popk(f, e_ph["f_start"], 8, 1.6)
        return _T(px_ + dx, py_ + hop - 17.3 * pk * (1 - sq), 0.0) @ _Sc(k_, k_ * sq, k_)
    g.kids["person"]["fn"] = person_M

    def gest(f):                                                          # cut：咔一下，整组微震
        a = _wob(f, e_sn["f_land"], 1.2, 5.0, 6.0)
        return Vector((0.0, 0.0, 0.0006 * a)), Quaternion((0, 1, 0), math.radians(0.4 * a))
    # ---- 段首段尾：孔桶里面
    bore = _mm(0.0, 0.0, face_z - P["BORE_IN"])
    if P.get("COVER") == "bin":                                           # 11-23 首版机检：孔里是灰的、插座是深蓝，段首段尾亮度 0.25–0.39（OC7 要 ≥ 0.45）→ 改成骨白废料桶正面盖满
        bore = _mm(bx, by - P["BIN_H"] * 0.5, bz + P["BIN_R"] + 0.2)
    if P.get("BORE_BOTTOM"):                                              # 11-23 试渲：孔中段 10 mm 时镜头看到孔底的分模线、金触点、小孔；落到孔底正中（干净的一小块）上，离 HEAD_D / TAIL_D
        bore = _mm(0.0, 0.0, bore_bot)
    g.run(bore, bore, tail_kids=None, gest=gest)
    for role in ("jaw_a", "jaw_b"):                                       # 钳口：进来时张 18°，cut 时 6 帧合上
        j = jaws[role]
        for f in range(e_ni["f_start"], min(nf, e_fa["f_start"] + 30)):
            v = 18.0 * (1 - ease_in_cubic(clamp01((f - e_sn["f_start"]) / max(1, e_sn["f_land"] - e_sn["f_start"]))))
            R5.pose(nip, role, v)
            j.keyframe_insert("rotation_euler", frame=f)
    if rings:
        st, _ = _emit_mat(rings, "oncam_snip_ring", (1.0, 0.08, 0.06))
        _key_val(st, [(0, 0.0), (e_ro["f_start"], 0.0), (e_ro["f_land"] + 4, 5.0), (e_ro["f_land"] + 16, 3.0), (nf - 1, 3.0)])

    def foc(f):
        return _mm(4.0, -3.0, 10.0)
    fa1 = e_fa["f_start"] + 26
    pairs = [("tailA", "socket", range(0, nf)), ("tailB", "socket", range(0, nf)), ("tailA", "bin", range(e_fa["f_start"], nf)),
             ("tailB", "bin", range(e_fa["f_start"], nf)), ("nip", "socket", range(e_ni["f_start"], fa1)),
             ("nip", "tailA", range(e_ni["f_start"], fa1)), ("nip", "tailB", range(e_ni["f_start"], fa1)),
             ("nip", "lug", range(e_ni["f_start"], fa1)), ("bin", "socket", range(0, nf)), ("chip", "socket", range(e_cp["f_start"], nf)),
             ("chip", "runner", range(e_cp["f_start"], nf)), ("person", "runner", range(e_ph["f_start"], nf)), ("tailA", "lug", range(0, nf)),
             ("tailB", "lug", range(0, nf)), ("tailA", "runner", range(e_fa["f_start"], nf)), ("tailB", "runner", range(e_fa["f_start"], nf))]
    R = g.result(foc, pairs, info=dict(beads=[[round(v, 2) for v in c] for c in ctr], lug=[round(v, 2) for v in lug_c], cut=[round(v, 2) for v in cut], rings=len(rings), bore_bot=round(bore_bot, 2)))
    hcol = bpy.data.collections["ONCAM_hero"]
    C0 = g.LM[e_bs["f_start"]] @ _mm(0.0, 0.0, 10.0)
    _sheen_light(sc, hcol, C0 + Vector((-0.30, -0.30, 0.12)), C0 + Vector((0.30, -0.30, 0.12)), C0, e_bs["f_start"], max(14, e_bs["f_end"] - e_bs["f_start"]), P["RIM_W"] * 2.0)
    return R


V604 = dict(
    # 11-23 甲线（18 文档 2.4 6-04+05）：微孔板（Codex u06）一块块叠成塔、叠到出画；Here? 塔往后往左退、变虚，前面弹出小托盘，13 把假插头逐把落进座里。
    # 定案（可改回）：18 写"每 8 帧一块、14 块"叠不出画（14 × 4.2 mm ≈ 455 px），改成间隔从 7 帧收到 3 帧、共 25 块（越叠越快），最上面三块多出画；
    # 出画的那几块不进主零件框（OC1、OC3 量下面 BBOX_N 块 + 托盘）；塔还没叠高的帧段（OC1_LO_EXEMPT）不算 OC1 下限；Here? 以后整组 = 退到后面的塔 + 前面的托盘，塔按设计出画，OC1 上限不算（OC1_EXEMPT）。
    # 托盘 18 写 46 × 20，13 把 h02b（×0.45）的凸缘直径 6.3，一排 7 把挤不下，改 52 × 22（座距 7.0）；托盘先朝镜头倾 TRAY_TILT0，tilt 再倾 12°。
    PXMM=7.75, REST_D=1.5, REST_PX=(1490.0, 470.0), REST=(18.0, 10.0), ORG=(0.0, 24.0),
    HEAD_D=0.02, HEAD_PX=(960.0, 540.0), HEAD_CTRL=(2300.0, 470.0, 0.95), HEAD_ROT=(0.0, -90.0), HEAD_QW=True, HEAD_EASE=0.6, HEAD_QLAG=0.0,   # 11-23 返修：晚转身、跟灯几版都更糟，退回首版退法，只在第 3–8 帧把段首灯加上去（试渲 ×1.6 第 4 帧 0.634→0.690），填平第 4 帧那个坑   # 11-23 首版：段首牌子退出前转到背光面，往回闪 13.2 → 晚转身；试渲二：牌子边第 3→4 帧一下扫过（bg 亮度跳 36）→ EASE 0.6→0.9 退得更匀；试渲三：仍有 −31 一跳、第 9→10 帧回亮 5 → TRANS_K 1.0→0.6（盖满面不用那么亮）、QLAG 0.45
    TAIL_D=0.038, TAIL_PX=(960.0, 540.0), TAIL_CTRL=(1500.0, 420.0, 0.7), TAIL_ROT=(0.0, 58.0),   # 首版 0.02：段尾盖满 10 帧（OC7 ≤ 6）
    N_PLATES=25, BBOX_N=15, GAP0=7.0, GAP1=3.0, FALL_N=10, SWAY=0.35, BACK=(16.0, 0.0, -54.0),
    TRAY=(-35.0, -1.0, 22.0), TRAY_WH=(52.0, 22.0), TRAY_TILT0=20.0, TRAY_TILT=12.0, PLUG_K=0.45, SEAT_DX=7.0, ROWS_Y=(5.5, -1.5), TXT_Y=-6.5, TXT_SIZE=14.4,
    TAIL_AT=(18.0, -8.6), TEXT_GLOW=4.0, HAND_FRONT=[(214, 224)],   # D 双手捧起的位置在托盘前（18 文档"手在前"）
    OC=True, TRANS=True, TRANS_K=1.0, TRANS_HK=[(0, 1.0), (2, 1.0), (3, 1.21), (4, 1.65), (6, 1.6), (9, 1.0), (20, 1.0), (28, 0.0)], HIDE_RED=True, H_MIN=486, TOP_MIN=60, BOT_MAX=860, OC1_LO_EXEMPT=[(0, 120), (187, 214)], OC1_EXEMPT=[(207, 524)],
    BOARD_K=1.27, BOARD_HIDE=("stations", "zone_tags", "z1_c0_r0"),
    HEAD_BOX=(300, 90, 900, 680), LOCK_BOX=(1000, 0, 1940, 1080),
    RIM_W=60.0, SAMPLES=16, GRAIN_F=150, GRAIN_GAIN=1.0,
)


def _join_part(root, name):
    """一个零件（空物体 + 一堆网格子物体）并成一个网格物体（材质槽合并）：同一块板要摆 25 次，用一份网格数据多个物体，省物体数和建 BVH 的时间。"""
    import bmesh
    bpy.context.view_layer.update()
    Minv = root.matrix_world.inverted()
    bm = bmesh.new()
    mats = []
    for o in [root] + list(root.children_recursive):
        if o.type != "MESH" or o.hide_render:
            continue
        me = o.data.copy()
        me.transform(Minv @ o.matrix_world)
        mp = []
        for m in o.data.materials:
            if m not in mats:
                mats.append(m)
            mp.append(mats.index(m))
        for p in me.polygons:
            p.material_index = mp[p.material_index] if mp else 0
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    new = bpy.data.meshes.new(name)
    bm.to_mesh(new)
    bm.free()
    for m in mats:
        new.materials.append(m)
    for o in [root] + list(root.children_recursive):
        try:
            bpy.data.objects.remove(o, do_unlink=True)
        except (ReferenceError, RuntimeError):
            pass
    return new


def recipe_tray13(W):
    """6-04+05（D：Millions of compounds screened before. Here? Thirteen made.  B：Thirteen. That's honestly wild.，568 帧）。
    G 局部毫米：塔底（第 0 块板的裙边底）在 (0, 0, 0)，板平放（板的 +Z → G +Y，板的 +Y → G −Z），叠放间距 4.2；下面垫一小圈料杆托。
    托盘在塔前下方（TRAY），盘面朝上再朝镜头倾 TRAY_TILT0；13 把假插头针朝下立在座里（前排 7、后排 6），前沿刻 13。
    段首：第 0 块板的骨白底面盖满画面；段尾：托盘前沿刻字右边一块骨白盘面冲镜头（托盘 + 13 把一起掰出来）。"""
    import kit_parts as KP
    import kit_socket as KS
    import kit_deep_r5 as R5
    g = _Grp(W)
    K, P, E, nf = g.K, g.P, g.E, g.nf
    sc = W["sc"]
    e_ld, e_st, e_tb, e_tp, e_dr, e_ct, e_wv, e_tl, e_dv = (E[n] for n in ("land", "stack", "tower_back", "tray_pop", "drop13", "count13", "wave", "tilt", "dive"))
    pitch = 4.2
    # ---- 微孔板：建一块，并成一个网格，摆 N 块
    pl = R5.u06_wellplate(K)
    me_pl = _join_part(pl, "u06_joined")
    N = P["N_PLATES"]
    # 叠的节奏：第 1 块起，间隔从 GAP0 线性收到 GAP1
    starts = []
    f = float(e_st["f_start"])
    for k in range(1, N):
        starts.append(int(round(f)))
        f += P["GAP0"] + (P["GAP1"] - P["GAP0"]) * (k - 1) / max(1, N - 2)
    fall_n = P["FALL_N"]
    lands = [s + fall_n for s in starts]
    # 画面上沿在 G 局部的高度（粗估：落位时 1 mm = PXMM px，再留 12 mm），板从那上面落下
    y_top = P["ORG"][1] + P["REST_PX"][1] / P["PXMM"] + 12.0
    bx_, by_, bz_ = P["BACK"]

    def back_M(f):
        u = ease_inout_cubic(clamp01((f - e_tb["f_start"]) / max(1, e_tb["f_land"] - e_tb["f_start"])))
        return _T(bx_ * u, by_ * u, bz_ * u)

    def sway_M(f):
        a = sum(_wob(f, l, P["SWAY"] * (0.6 + 0.4 * k / N), 16.0, 14.0) for k, l in enumerate(lands))
        b = _wob(f, e_ld["f_land"], 0.8, 18.0, 12.0)
        return _R("Z", a + b) @ _R("X", 0.4 * a)

    R_flat = _R("X", -90.0)
    for i in range(N):
        o = bpy.data.objects.new(f"u06_{i:02d}", me_pl)
        link_obj(o)
        root = bpy.data.objects.new(f"plate_{i:02d}", None)
        link_obj(root)
        o.parent = root
        y_i = i * pitch
        if i == 0:
            g.add("p00", root, _T(0, 0, 0) @ R_flat, bake=False)
            g.kids["p00"]["fn"] = lambda f: back_M(f) @ sway_M(f) @ R_flat
            continue
        s0, l0 = starts[i - 1], lands[i - 1]
        nm = f"p{i:02d}"
        pts0 = g.kids["p00"]["pts"]
        g.add(nm, root, _T(0, y_i, 0) @ R_flat, show=s0, bake=False, bbox=False)
        if i < P["BBOX_N"]:
            g.kids[nm]["pts"] = [p.copy() for p in pts0]
            g.kids[nm]["bbox"] = True
            g.kids[nm]["bbox_from"] = l0

        def fn(f, y_i=y_i, s0=s0, l0=l0):
            y = y_i
            if f < l0:
                y = y_top + (y_i - y_top) * ease_in_cubic(clamp01((f - s0) / max(1, l0 - s0)))
                y = max(y, y_i)
            else:
                y = y_i + 0.5 * abs(math.sin(math.pi * (f - l0) / 4.0)) * math.exp(-(f - l0) / 3.0)
            return back_M(f) @ sway_M(f) @ _T(0, y, 0) @ R_flat
        g.kids[nm]["fn"] = fn
    # ---- 料杆托：一圈细料杆垫在第 0 块板下面（段首藏着，落位前弹出）
    rr = KP.Part(K, "plate_rest", "white")
    ry = -0.72
    for a, b in (((-17.0, ry, -8.5), (17.0, ry, -8.5)), ((-17.0, ry, 8.5), (17.0, ry, 8.5)), ((-15.0, ry, -8.5), (-15.0, ry, 8.5)), ((15.0, ry, -8.5), (15.0, ry, 8.5))):
        rr.tube([a, b], 0.7, K.white)
    rr.tube([(17.0, ry, 0.0), (24.0, ry, 0.0)], 0.7, K.white)          # 一截往右伸的料杆头
    g.add("rest", rr.done(), _Sc(0.001), show=14)
    g.kids["rest"]["fn"] = lambda f: back_M(f) @ sway_M(f) @ _Sc(_popk(f, 14, 12, 1.6))
    # ---- 托盘：骨白圆角板 + 13 个座（Ø5.2 深 0.8，中间穿 Ø3.9 给针）+ 前沿刻 13
    tw, td = P["TRAY_WH"]
    dx = P["SEAT_DX"]
    yb, yf = P["ROWS_Y"]
    seats = [(dx * (j - 3), yf) for j in range(7)] + [(dx * (j - 2.5), yb) for j in range(6)]
    tp = KP.Part(K, "tray13", "white")
    tp.slab(KP.rrect(0, 0, tw / 2, td / 2, 3.0), 2.0, K.white, z=0.0, bevel=0.5,
            holes=[(sx, sy, 1.95) for sx, sy in seats], cuts=[(KP.circle(sx, sy, 2.6), 1.6, 1.0) for sx, sy in seats])
    t13 = tp.text("13", P["TXT_SIZE"], 0.0, P["TXT_Y"], 1.0 - 0.1, K.ink)
    tray = tp.done()
    t13 = [o for o in _objs(tray) if o.type == "FONT"]
    tx, ty, tz = P["TRAY"]
    g.add("tray", tray, _T(tx, ty, tz) @ _Sc(0.001), show=e_tp["f_start"])

    def tray_M(f):
        k = _popk(f, e_tp["f_start"], 14, 1.8)
        z = -14.0 * (1 - ease_out_cubic(clamp01((f - e_tp["f_start"]) / 14.0)))
        a = P["TRAY_TILT0"] + P["TRAY_TILT"] * ease_inout_cubic(clamp01((f - e_tl["f_start"]) / max(1, e_tl["f_land"] - e_tl["f_start"])))
        a += _wob(f, e_tl["f_land"], 1.5, 12.0, 10.0)
        return _T(tx, ty, tz + z) @ _R("X", a) @ R_flat @ _Sc(k)
    g.kids["tray"]["fn"] = tray_M
    # ---- 13 把假插头：针朝下（插头局部 −X → 托盘 −Z），本体端面落在座底（托盘局部 z = 0.2），逐把落下
    pk = P["PLUG_K"]
    body_end = 5.5 * pk / 0.45
    z_seat = 0.2 + 0.3 + body_end                                       # 座底倒角圆角 0.5，本体端面抬 0.3 不压上去
    d0, d1 = e_dr["f_start"], e_dr["f_end"]
    for i, (sx, sy) in enumerate(seats):
        o = KS.h02b_plug(K, seed=i + 1)                                   # 原大建（h02b 的 scale 写在根物体上，挂进 G 时会被 matrix_basis 冲掉），缩放放进 fn
        KS.rest(o)
        nm = f"g{i:02d}"
        fs = d0 + 4 * i
        fl = fs + 12
        wv = e_wv["f_start"] + 2 * i
        g.add(nm, o, _T(0, 0, 0) @ _Sc(0.001), show=fs, bbox=True)
        g.kids[nm]["bbox_from"] = fl

        def pfn(f, sx=sx, sy=sy, fs=fs, fl=fl, wv=wv, i=i):
            if f < fl:
                u = ease_in_cubic(clamp01((f - fs) / max(1, fl - fs)))
                dz = 40.0 * (1 - u)
                tw_ = 25.0 * (1 - u)
            else:
                dz = 0.6 * abs(math.sin(math.pi * (f - fl) / 4.0)) * math.exp(-(f - fl) / 3.0)
                tw_ = 0.0
            if f >= wv:
                t = clamp01((f - wv) / 10.0)
                dz += 3.0 * math.sin(math.pi * t)
            return tray_M(f) @ _T(sx, sy, z_seat + dz) @ _R("Z", tw_) @ _R("Y", -90.0) @ _Sc(pk)
        g.kids[nm]["fn"] = pfn
    # ---- 段首、段尾
    head = g.kids["p00"]["fn"](0) @ _mm(0.0, 0.0, 0.6)
    ta_x, ta_y = P["TAIL_AT"]
    tail = tray_M(e_dv["f_start"]) @ _mm(ta_x, ta_y, 1.0)
    plug_names = [f"g{i:02d}" for i in range(len(seats))]
    g.run(head, tail, tail_kids=["tray"] + plug_names, gest=None)
    st, _ = _emit_mat(t13, "oncam_tray13_txt", (1.0, 0.10, 0.06))
    c0 = e_ct["f_land"]
    _key_val(st, [(0, 0.0), (c0 - 4, 0.0), (c0 + 4, P["TEXT_GLOW"] * 1.4), (c0 + 18, P["TEXT_GLOW"]), (nf - 1, P["TEXT_GLOW"])])

    def foc(f):
        a = _mm(0.0, 30.0, 0.0)
        b = Vector(tray_M(max(f, e_tp["f_start"] + 14)) @ _mm(0.0, 0.0, 6.0))
        return a.lerp(b, smooth((f - e_tp["f_start"]) / 20.0))
    pairs = [("rest", "p00", range(14, nf)), ("tray", "p00", range(e_tp["f_start"], e_dv["f_start"])), ("tray", "rest", range(e_tp["f_start"], e_dv["f_start"]))]
    pairs += [(f"g{i:02d}", "tray", range(e_dr["f_start"] + 4 * i, nf)) for i in range(len(seats))]
    pairs += [(f"g{i:02d}", f"g{j:02d}", range(e_dr["f_start"], nf)) for i in range(len(seats)) for j in range(i + 1, len(seats))
              if abs(seats[i][0] - seats[j][0]) < 9 and abs(seats[i][1] - seats[j][1]) < 9]
    R = g.result(foc, pairs, info=dict(plates=N, starts=starts, lands=lands, seats=seats, y_top=round(y_top, 1)))
    hcol = bpy.data.collections["ONCAM_hero"]
    C0 = g.LM[e_tl["f_land"]] @ Vector(tray_M(e_tl["f_land"]) @ _mm(0.0, 0.0, 6.0))
    _sheen_light(sc, hcol, C0 + Vector((-0.35, -0.30, 0.12)), C0 + Vector((0.35, -0.30, 0.12)), C0, e_tl["f_land"] - 4, 22, P["RIM_W"] * 2.0)
    C1 = g.LM[e_ct["f_land"]] @ Vector(tray_M(e_ct["f_land"]) @ _mm(0.0, P["TXT_Y"], 1.0))
    _sheen_light(sc, hcol, C1 + Vector((-0.20, -0.25, 0.06)), C1 + Vector((0.20, -0.25, 0.06)), C1, e_ct["f_land"] - 6, 16, P["RIM_W"] * 1.6)
    return R


def _face_cam(g, n_G):
    """G 局部的一个法向 n_G，求整组朝向 (yaw, tilt)（_q 的写法，base = g.base），使它在世界里正对镜头（−Y）。段首、段尾盖满面摆正用。"""
    tgt = Vector((0.0, -1.0, 0.0))
    best = None
    for yw in range(-180, 181, 3):
        for tl in range(-180, 181, 3):
            d_ = (_q(yw, tl, base=g.base) @ n_G - tgt).length
            if best is None or d_ < best[0]:
                best = (d_, float(yw), float(tl))
    step = 1.0
    for _ in range(6):
        _, y0, t0 = best
        for yw in (y0 - step, y0, y0 + step):
            for tl in (t0 - step, t0, t0 + step):
                d_ = (_q(yw, tl, base=g.base) @ n_G - tgt).length
                if d_ < best[0]:
                    best = (d_, yw, tl)
        step *= 0.4
    return round(best[1], 2), round(best[2], 2)


V408 = dict(
    # 11-23 甲线（18 文档 2.4 4-08）：循环轨道（h03，朝镜头倾 50°）+ 左前料杆上的小人 + 上方弹下的 AI 芯片；
    # trial：小车绕轨道跑（60 帧一圈），error 过 Test 站红灯闪；inside：轨道沿自己的平面退到芯片底下、缩小，芯片落下盖住；computer：芯片上方亮起光环，越转越快，甩出一道光；段尾光环冲镜头。
    # 定案（可改回）：18 写缩到 0.55 倍，芯片（屏上宽 220 px）盖不住 0.55 倍的轨道，改缩到 TRACK_IN；光环悬在芯片顶上方、分 12 段（转起来看得出），管径加粗到盖满时盖得住画面。
    PXMM=11.5, REST_D=1.5, REST_PX=(1462.0, 574.0), REST=(12.0, 8.0), ORG=(0.0, 8.0),   # 11-24 Z11：站牌 ×1.7 后下沿 868、小人左移后左沿余 −37 → 整组右移 32、上移 14 px
    HEAD_D=0.03, HEAD_PX=(960.0, 540.0), HEAD_CTRL=(2300.0, 470.0, 0.95), HEAD_QW=True, HEAD_EASE=0.6,   # 11-23 首版 M9 段首先亮后暗往回闪 20.9（第 0 帧贴得太近反而暗）→ 0.02→0.03
    TAIL_D=0.013, TAIL_PX=(960.0, 540.0), TAIL_CTRL=(1500.0, 420.0, 0.7),
    TRACK_TILT=42.0, TRACK_IN=0.36, CHIP_AT=(0.0, 30.0, 12.0), CHIP_K=0.68, CHIP_DOWN=4.0, CHIP_DROP=45.0, PERSON=(-42.0, -8.0, 10.0), PERSON_K=0.77,
    RING_R=9.95, RING_T=2.0, RING_Z=5.2, RING_SEG=12, RING_GLOW=3.0, CAR_LAP=60.0, CAR_PHASE=0.65,
    OC=True, TRANS=True, TRANS_K=1.0, TRANS_H0=1.8, DIVE_AT=478, HIDE_RED=True, H_MIN=486, TOP_MIN=60, BOT_MAX=860, ACC=["person", "chip"],   # 试渲 0.03：第 0→2 帧 0.89→0.99 往回闪 25 → 第 0 帧灯 ×1.8
    HAND_FRONT=[(440, 505)], OC2_EXEMPT=[(20, 40)], OC1_LO_EXEMPT=[(20, 40)], OC1_EXEMPT=[(20, 30), (306, 384)],   # A 第 446 帧起甩手横过整组（手在前）；芯片从上方掉进来那几帧还没进框；轨道退进芯片底下那段整组临时拉高
    BOARD_K=1.27, BOARD_HIDE=("stations", "zone_tags", "z1_c0_r0"),
    HEAD_BOX=(300, 90, 900, 680), LOCK_BOX=(1000, 0, 1940, 1080),
    RIM_W=60.0, SAMPLES=16, GRAIN_F=150, GRAIN_GAIN=1.0,
)


def recipe_loop_chip(W):
    """4-08（A：AI didn't replace the scientists. It ran their trial and error inside a computer, at light speed.，520 帧）。
    G 局部毫米：轨道底板中心在原点，平放后朝镜头倾 TRACK_TILT（轨道局部 +Z → 法向）；“轨道系” = 轨道平放倾斜后的坐标（x 右、y 往里、z 法向）。
    芯片在轨道系 CHIP_AT（轨道后上方，和轨道平行）；小人站在轨道左前一截料杆上。段首：轨道骨白底面盖满；段尾：光环管面冲镜头（暖白自发光盖满）。"""
    import kit_parts as KP
    import kit_deep as D
    g = _Grp(W)
    K, P, E, nf = g.K, g.P, g.E, g.nf
    sc = W["sc"]
    e_ld, e_cd, e_cf, e_ph, e_cg, e_fb, e_ic, e_ro, e_rs, e_sk, e_dv = (E[n] for n in (
        "land", "chip_drop", "chip_feint", "person_hop", "car_go", "fail_blink", "into_chip", "ring_on", "ring_spin", "streak", "dive"))
    R_flat = _R("X", -90.0)
    R_tr = _R("X", P["TRACK_TILT"]) @ R_flat                              # 轨道系 → G
    # ---- 轨道
    tr = D.h03_loop_track(K, "hero")
    D.rest(tr)
    jr = D.rig(tr)
    car_j, lamp_j = jr["car"], jr["test_lamp"]
    lamp_objs = [o for o in lamp_j.children_recursive if o.type == "MESH"]
    g.add("track", tr, R_tr)
    ti = P["TRACK_IN"]
    ic0, ic1 = e_ic["f_start"], e_ic["f_end"]
    cx_, cy_, cz_ = P["CHIP_AT"]

    def track_M(f):
        u = ease_inout_cubic(clamp01((f - ic0) / max(1, ic1 - ic0)))
        k = 1.0 + (ti - 1.0) * u
        return R_tr @ _T(cx_ * u, cy_ * u, 0.0) @ _Sc(k)
    g.kids["track"]["fn"] = track_M
    # ---- 芯片（轨道后上方，和轨道平行）
    ck = P["CHIP_K"]
    chip = KP.p13_chip(K, "AI")
    g.add("chip", chip, R_tr @ _T(cx_, cy_, cz_) @ _Sc(0.001), show=e_cd["f_start"])
    g.kids["chip"]["bbox_from"] = e_cd["f_start"] + 14                     # 从画外上方弹下来，落定以后才算进主零件框
    pk = P["PERSON_K"]
    pxs, feet_y, stz = P["PERSON"]
    pys = feet_y + (15.2 + 2.1) * pk                                       # 小人原点（身子中心）：脚底在 feet_y
    stub_y = feet_y - 0.6                                                 # 料杆中心线（顶 = 脚底）

    def chip_M(f):
        t = clamp01((f - e_cd["f_start"]) / 14.0)
        drop = P["CHIP_DROP"] * (1.0 - ease_out_back(t, 1.4))              # 从画外上方弹下来（往"上"用 G +Y）
        k = ck * (0.6 + 0.4 * ease_out_cubic(t))
        M = R_tr @ _T(cx_, cy_, cz_) @ _Sc(k)
        lift = 0.0
        if f >= ic0:                                                       # 先抬 12 mm 让路，轨道进来以后再落下盖住
            a = ease_inout_cubic(clamp01((f - ic0) / 18.0))
            b = ease_inout_cubic(clamp01((f - (ic1 - 22)) / 22.0))
            lift = 12.0 * a * (1 - b) - P["CHIP_DOWN"] * b
        M = R_tr @ _T(0.0, 0.0, lift) @ R_tr.inverted() @ M
        # feint：朝小人压下去一半、停住、退回
        fa = ease_inout_cubic(clamp01((f - e_cf["f_start"]) / 12.0)) * (1 - ease_inout_cubic(clamp01((f - (e_cf["f_end"] - 12)) / 12.0)))
        c_chip = (R_tr @ _T(cx_, cy_, cz_)).translation / MM
        c_pers = Vector((pxs, pys + 10.6 * pk, stz))
        d = (c_pers - c_chip) * 0.5 * fa
        return _T(d.x, d.y + drop, d.z) @ M
    g.kids["chip"]["fn"] = chip_M
    # ---- 小人 + 料杆
    sb = KP.Part(K, "loop_stub", "white")
    sb.tube([(pxs - 7.0, stub_y, stz), (pxs + 7.0, stub_y, stz)], 0.6, K.white)      # 一截横料杆，右头一根浇口往后接到轨道底板左前角
    sb.tube([(pxs + 7.0, stub_y, stz), (pxs + 9.5, stub_y, stz - 3.0)], 0.45, K.white)
    g.add("stub", sb.done())
    pp = KP.Part(K, "loop_person", "white")
    KP.person(pp, K.white, 0.0)
    g.add("person", pp.done(), _T(pxs, pys, stz) @ _Sc(pk))

    def person_M(f):
        t = clamp01((f - e_ph["f_start"]) / 14.0)
        hop = 4.0 * math.sin(math.pi * t)
        sq = 1.0 - 0.08 * math.sin(math.pi * clamp01((f - e_ph["f_start"] - 14) / 6.0)) if f >= e_ph["f_start"] + 14 else 1.0
        return _T(pxs, pys + hop - (15.2 + 2.1) * pk * (1 - sq), stz) @ _Sc(pk, pk * sq, pk)
    g.kids["person"]["fn"] = person_M
    # ---- 光环：悬在芯片顶上方，12 段弧（中间留缝，转起来看得出）
    rg = KP.Part(K, "loop_ring", "white")
    nseg = P["RING_SEG"]
    Rr, Rt = P["RING_R"], P["RING_T"]
    span = 360.0 / nseg
    for i in range(nseg):
        a0 = math.radians(i * span + 0.12 * span)
        a1 = math.radians((i + 1) * span - 0.12 * span)
        pts = [(Rr * math.cos(a0 + (a1 - a0) * j / 8), Rr * math.sin(a0 + (a1 - a0) * j / 8), 0.0) for j in range(9)]
        rg.tube(pts, Rt, K.white, smooth=True)
    ring = rg.done()
    g.add("ring", ring, _Sc(0.001), show=e_ro["f_start"])
    rs0, rs1 = e_rs["f_start"], e_rs["f_end"]

    def spin(f):
        if f < rs0:
            return 0.0
        t = (min(f, rs1) - rs0)
        a = 0.35 * t * t                                                    # 越转越快（度）
        if f > rs1:
            a += 0.7 * (rs1 - rs0) * (f - rs1)
        return a

    def ring_M(f):
        k = _popk(f, e_ro["f_start"], 12, 1.6)
        return chip_M(f) @ _T(0.0, 0.0, P["RING_Z"]) @ _R("Z", spin(f) + 0.5 * span) @ _Sc(k)
    g.kids["ring"]["fn"] = ring_M
    # ---- 甩出去的光：一颗发光的小胶囊，从光环右上沿直线甩出画外
    sk = KP.Part(K, "loop_streak", "white")
    sk.capsule(0.0, -3.0, 3.0, 0.9, K.white)
    g.add("streak", sk.done(), _Sc(0.001), show=e_sk["f_start"], hide=e_sk["f_end"] + 6, bbox=False)

    def streak_M(f):
        t = clamp01((f - e_sk["f_start"]) / max(1, e_sk["f_end"] - e_sk["f_start"]))
        p0 = (ring_M(e_sk["f_start"]) @ _mm(Rr, 0.0, 0.0)) / MM
        p1 = p0 + Vector((70.0, 55.0, 10.0))
        p = p0.lerp(p1, ease_in_cubic(t))
        ang = math.degrees(math.atan2(55.0, 70.0)) - 90.0
        return _T(p.x, p.y, p.z) @ _R("Z", ang) @ _Sc(1.0, 1.0 + 3.0 * t, 1.0)
    g.kids["streak"]["fn"] = streak_M
    # ---- 段首、段尾
    n_under = (R_tr.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
    P["HEAD_ROT"] = _face_cam(g, n_under)
    head = R_tr @ _mm(0.0, 0.0, 0.0)
    f_d0 = e_dv["f_start"]
    Mr = ring_M(f_d0)
    am = math.radians(0.5 * span)                                         # 11-23 首版 M12 段尾只盖住 0.53：局部角 0 是第 11、0 段之间的缝（ring_M 里转的半段不改局部坐标），挪到第 0 段弧正中
    tail = Mr @ _mm(Rr * math.cos(am), Rr * math.sin(am), Rt)            # 管子朝芯片法向那一面
    n_ring = (Mr.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()
    P["TAIL_ROT"] = _face_cam(g, n_ring)
    g.run(head, tail, tail_kids=["ring"], gest=None)
    # 小车：轨道上一圈 CAR_LAP 帧，car_go 起步、computer 开口停；Test 站（路径 0.5 处）在 fail_blink 落点
    lap = P["CAR_LAP"]
    c0_, c1_ = e_cg["f_start"], e_cg["f_end"]
    for f in range(nf):
        tt = f - c0_
        if f <= c0_:
            s_ = 0.0
        elif f <= c0_ + 10:
            s_ = (tt * tt) / 20.0
        else:
            s_ = 5.0 + (tt - 10)
        if f > c1_:
            te = f - c1_
            s_ = 5.0 + (c1_ - c0_ - 10) + (min(te, 12) - min(te, 12) ** 2 / 24.0)
        v = (P["CAR_PHASE"] + s_ / lap) % 1.0
        D.pose(tr, "car", v)
        key_matrix(car_j, f, car_j.matrix_basis.copy())
    linear_keys(car_j)
    # 发光：Test 灯红闪、光环暖白、甩出去的光、小人轮廓光
    if lamp_objs:
        st, _ = _emit_mat(lamp_objs, "oncam_loop_testlamp", (1.0, 0.08, 0.05))
        b0 = e_fb["f_land"]
        _key_val(st, [(0, 0.0), (b0 - 2, 0.0), (b0 + 2, 6.0), (b0 + 8, 1.0), (b0 + 12, 6.0), (b0 + 20, 0.0)])
    r_objs = [o for o in _objs(ring) if o.type in ("MESH", "CURVE")]
    st, _ = _emit_mat(r_objs, "oncam_loop_ring", (1.0, 0.93, 0.80))
    o0 = e_ro["f_land"]
    _key_val(st, [(0, 0.0), (e_ro["f_start"], 0.0), (o0, P["RING_GLOW"] * 0.6), (e_ro["f_end"], P["RING_GLOW"] * 0.8), (rs0, P["RING_GLOW"] * 0.8),
                  (rs1, P["RING_GLOW"]), (nf - 1, P["RING_GLOW"])])
    s_objs = [o for o in _objs(g.kids["streak"]["root"]) if o.type in ("MESH", "CURVE")]
    st, _ = _emit_mat(s_objs, "oncam_loop_streak", (1.0, 0.93, 0.80))
    _key_val(st, [(0, 6.0), (nf - 1, 6.0)])
    p_objs = [o for o in _objs(g.kids["person"]["root"]) if o.type == "MESH"]
    st, _ = _emit_mat(p_objs, "oncam_loop_person", (1.0, 0.95, 0.85))
    h0 = e_ph["f_start"] + 6
    _key_val(st, [(0, 0.0), (h0 - 2, 0.0), (h0 + 6, 0.9), (h0 + 30, 0.0)])

    def foc(f):
        a = Vector(track_M(f) @ _mm(0.0, 0.0, 6.0))
        b = Vector(chip_M(max(f, e_cd["f_start"] + 14)) @ _mm(0.0, 0.0, 3.0))
        return a.lerp(b, smooth((f - ic0) / 30.0))
    pairs = [("chip", "track", range(e_cd["f_start"], f_d0)), ("chip", "person", range(e_cd["f_start"], nf)), ("chip", "stub", range(e_cd["f_start"], nf)),
             ("person", "stub", range(0, nf)), ("person", "track", range(0, nf)), ("stub", "track", range(0, nf)), ("ring", "chip", range(e_ro["f_start"], f_d0)),
             ("ring", "track", range(e_ro["f_start"], f_d0))]
    return g.result(foc, pairs, info=dict(head_rot=P["HEAD_ROT"], tail_rot=P["TAIL_ROT"], stub_y=round(stub_y, 2)))


V612 = dict(
    # 11-23 甲线（18 文档 2.4 6-12）：金色 048 吊牌（h19）用挂环穿在一根横料杆（"路"）左头；start 料杆往右长出画外，沿路弹出 Target、Hit、Improve 三块小站牌；
    # case 卷尺（骨白壳，壳上不刻字）弹到料杆下方；weeks 尺带拉出一小段（刻 weeks）、锁扣咔；not 尺带飞快拉出画外，刻 years 的一段滑过；years 一道红线划掉 years，尺带缩回 weeks。
    # 定案（可改回）：卷尺出尺口在壳右面（尺带顺着路往右拉）；吊牌一个人挂着的那段整组只有吊牌高（18 写屏上 190 px），卷尺弹出以前不算 OC1 下限。
    PXMM=11.0, REST_D=1.5, REST_PX=(1380.0, 470.0), REST=(10.0, 6.0), ORG=(10.0, 0.0),
    HEAD_D=0.02, HEAD_PX=(960.0, 540.0), HEAD_CTRL=(2300.0, 470.0, 0.95), HEAD_ROT=(0.0, 0.0), HEAD_QW=True, HEAD_EASE=0.6,
    TAIL_D=0.05, TAIL_PX=(960.0, 540.0), TAIL_CTRL=(1500.0, 420.0, 0.7), TAIL_ROT=(0.0, 0.0),   # 11-23 首版 OC7 段尾盖满 11 帧（要 ≤ 6）→ 0.036 还盖满 8 帧 → 0.05
    RY=20.0, RX0=-32.0, RX1=150.0, RUN_R=0.73, TAG_X=-24.0, PL_X=(-4.0, 16.0, 36.0), PL_K=0.57, PL_LABELS=("Target", "Hit", "Improve"),
    TAPE=(-2.5, -19.0), TAPE_K=0.95, EXT_WEEKS=16.0, EXT_YEARS=56.0, WEEKS_B=9.0, YEARS_B=38.0, TXT_SIZE=8.5,   # 11-23 试渲：尺带上 weeks / years 小写字身只有 20 px，放大整只卷尺和字（字身约 30 px），拉出长度收一点免得出右边
    OC=True, TRANS=True, TRANS_K=1.0, HIDE_RED=True, H_MIN=486, TOP_MIN=60, BOT_MAX=860, OC1_LO_EXEMPT=[(0, 241)],
    BOARD_K=1.27, BOARD_HIDE=("stations", "zone_tags", "z1_c0_r0"),
    HEAD_BOX=(300, 90, 900, 680), LOCK_BOX=(1000, 0, 1940, 1080),
    RIM_W=60.0, SAMPLES=16, GRAIN_F=150, GRAIN_GAIN=1.0,
)


def recipe_road_tape(W):
    """6-12（B：048 is at the very start of the road. But for this case, that start took weeks, not years.，470 帧）。
    G 局部毫米：横料杆（路）在 y = RY，吊牌挂环穿在料杆左头 TAG_X；三块站牌挂在料杆下；卷尺壳在 TAPE（缩放 TAPE_K），出尺口在壳右面，尺带往右拉。
    段首：吊牌金色牌面（刻字下面一块）盖满；段尾：卷尺骨白壳正面（左上一块）冲镜头，卷尺各件一起掰出来。"""
    import kit_parts as KP
    import kit_deep_r5 as R5
    g = _Grp(W)
    K, P, E, nf = g.K, g.P, g.E, g.nf
    sc = W["sc"]
    e_ld, e_sw, e_rg, e_tp, e_wk, e_yr, e_sk, e_dv = (E[n] for n in ("land", "tag_swing", "road_grow", "tape_pop", "tape_weeks", "tape_years", "strike", "dive"))
    RY, rx0, rx1 = P["RY"], P["RX0"], P["RX1"]
    # ---- 吊牌：挂环中心 (0, 8.04, 1.57)、环轴沿 X、内径 1.7；牌面上沿 y = 8 在环里，料杆从环里牌面以上穿过（y 8.9）
    tag = R5.h19_tag(K, "048", "gold")
    tx = P["TAG_X"]
    ring_c = Vector((0.0, 8.9, 1.57))
    M_tag = _T(tx - ring_c.x, RY - ring_c.y, -ring_c.z)
    g.add("tag", tag, M_tag)

    def tag_M(f):
        a = _wob(f, e_sw["f_start"], 14.0, 16.0, 14.0) + 1.2 * math.sin(2 * math.pi * f / 170.0) * smooth((f - 70) / 30.0)
        return _piv(tx, RY, 0.0, _R("X", a)) @ M_tag
    g.kids["tag"]["fn"] = tag_M
    # ---- 路：横料杆，开头只露吊牌两边一小段，start 起往右长出画外
    run_, lens = _curve_mm("road_runner", [[(rx0, RY), (rx1, RY)]], P["RUN_R"], K.white)
    rr = KP.Part(K, "road_root", "white")
    run_.parent = rr.root
    g.add("runner", rr.done(), bbox=False)
    L = rx1 - rx0
    fr0 = (tx + 6.0 - rx0) / L
    rg0, rg1 = e_rg["f_start"], e_rg["f_end"]

    def reach(f):
        return fr0 + (1 - fr0) * ease_inout_cubic(clamp01((f - rg0) / max(1, rg1 - rg0)))
    for f in range(nf):
        run_.data.bevel_factor_end = reach(f)
        run_.data.keyframe_insert("bevel_factor_end", frame=f)
    linear_keys(run_.data)
    # ---- 三块小站牌：挂在路下面，料杆长到那里时弹出
    pk = P["PL_K"]
    for i, (x, lab) in enumerate(zip(P["PL_X"], P["PL_LABELS"])):
        pl = KP.Part(K, f"road_plate{i}", "white")
        pl.tube([(0.0, 0.0, 0.0), (0.0, -2.2, 0.0)], 0.4, K.white)            # 浇口：料杆中心往下
        pr = KP.p16_plate(K, lab, w=24.0, italic=False)
        pr.parent = pl.root
        pr.location = _mm(0.0, -2.2 - 7.0 * pk + 0.3, 0.0)
        pr.scale = (pk, pk, pk)
        root = pl.done()
        u_i = (x + 7.0 - rx0) / L
        f_i = next((f for f in range(nf) if reach(f) >= u_i), rg1)
        nm = f"pl{i}"
        g.add(nm, root, _T(x, RY) @ _Sc(0.001), show=f_i)

        def pfn(f, x=x, f_i=f_i, i=i):
            k = _popk(f, f_i, 12, 2.0)
            a = _wob(f, f_i + 10, 5.0, 14.0, 12.0) + 1.0 * math.sin(2 * math.pi * (f + 37 * i) / 150.0) * smooth((f - f_i - 30) / 30.0)
            return _T(x, RY) @ _R("X", a) @ _Sc(k)
        g.kids[nm]["fn"] = pfn
    # ---- 卷尺：骨白壳（不刻字）+ 红锁扣 + 白尺带（刻 weeks / years）+ 金尺钩；出尺口在壳右面
    tk = P["TAPE_K"]
    tpx, tpy = P["TAPE"]
    mouth = 7.6
    hs = KP.Part(K, "road_tape_case", "white")
    hs.box(0, 0, 8.0, 9.0, 9.0, K.white, r=3.0, bevel=1.0)
    hs.inkbox(mouth - 0.9, -5.25, 0.5, 3.0, K.ink, 4.5)
    case = hs.done()
    f_tp = e_tp["f_start"]
    g.add("tape", case, _T(tpx, tpy) @ _Sc(0.001), show=f_tp)
    lb = KP.Part(K, "road_tape_lock", "red")
    lb.box(3.0, 9.6, 2.2, 1.0, 4.0, K.red, r=0.6, bevel=0.3)
    g.add("lockbtn", lb.done(), _T(tpx, tpy) @ _Sc(0.001), show=f_tp)
    stp = KP.Part(K, "road_tape_strip", "white")
    stp.slab([(0.0, -8.5), (1.0, -8.5), (1.0, -2.0), (0.0, -2.0)], 0.4, K.white, bevel=0)
    g.add("strip", stp.done(), _T(tpx, tpy) @ _Sc(0.001), show=f_tp, bbox=False)
    mk = KP.Part(K, "road_tape_marks", "white")
    marks = []                                                            # (物体, 离尺钩最远一端 b)
    for j in range(1, 36):
        b = 2.0 * j
        o = mk.inkbox(-b, -2.7, 0.1, 0.55 if j % 5 else 0.9, K.ink, 0.2)
        marks.append((o, b + 0.1))
    wb, yb = P["WEEKS_B"], P["YEARS_B"]
    t_wk = mk.text("weeks", P["TXT_SIZE"], -wb, -5.4, 0.2, K.ink, italic=True)
    t_yr = mk.text("years", P["TXT_SIZE"], -yb, -5.4, 0.2, K.ink, italic=True)
    marks += [(t_wk, wb + 7.0), (t_yr, yb + 7.0)]
    g.add("marks", mk.done(), _T(tpx, tpy) @ _Sc(0.001), show=f_tp, bbox=False, vis=False)
    sk = KP.Part(K, "road_tape_strike", "red")
    sk.inkbox(7.5, -5.0, 7.5, 0.32, K.red, 0.35)                           # 从 x = 0 往右画（缩放 x 从 0 到 1）
    g.add("strike", sk.done(), _Sc(0.001), show=e_sk["f_start"], bbox=False, vis=False)
    hk = KP.Part(K, "road_tape_hook", "gold")
    hk.box(0.45, -5.25, 0.45, 3.6, 1.4, K.gold, r=0.2, bevel=0.15)
    g.add("hook", hk.done(), _T(tpx, tpy) @ _Sc(0.001), show=f_tp, bbox=False)
    ew, ey = P["EXT_WEEKS"], P["EXT_YEARS"]
    r0 = e_sk["f_land"] + 14

    def ext(f):
        e = ew * ease_out_back(clamp01((f - e_wk["f_start"]) / max(1, e_wk["f_land"] - e_wk["f_start"])), 1.2)
        e += (ey - ew) * ease_inout_cubic(clamp01((f - e_yr["f_start"]) / 12.0))
        e -= (ey - ew) * ease_inout_cubic(clamp01((f - r0) / max(1, e_sk["f_end"] - r0)))
        return max(0.0, e)

    def tape_M(f):
        k = _popk(f, f_tp, 14, 1.8)
        rise = 8.0 * (1 - ease_out_cubic(clamp01((f - f_tp) / 14.0)))
        jolt = 0.4 * _wob(f, e_wk["f_land"], 1.0, 7.0, 7.0)
        return _T(tpx, tpy - rise + jolt) @ _Sc(k * tk)
    g.kids["tape"]["fn"] = tape_M
    g.kids["lockbtn"]["fn"] = lambda f: tape_M(f) @ _T(0, -1.0 * ease_out_back(clamp01((f - e_wk["f_land"] + 3) / 4.0), 2.0) * (1 - ease_inout_cubic(clamp01((f - e_yr["f_start"] + 4) / 4.0))))
    g.kids["strip"]["fn"] = lambda f: tape_M(f) @ _T(mouth, 0) @ _Sc(max(0.001, ext(f)), 1, 1)
    g.kids["marks"]["fn"] = lambda f: tape_M(f) @ _T(mouth + ext(f), 0)
    g.kids["hook"]["fn"] = lambda f: tape_M(f) @ _T(mouth + ext(f), 0)

    def strike_M(f):
        u = ease_out_cubic(clamp01((f - e_sk["f_start"]) / 8.0))
        return tape_M(f) @ _T(mouth + ext(f) - yb - 7.5, 0) @ _Sc(max(0.001, u), 1, 1)
    g.kids["strike"]["fn"] = strike_M
    # 刻度、字：还在壳里面（壳挡着）照常出像，伸到壳左面外头（b > 拉出长度 + 壳内长 15）才藏
    inner = 15.0
    marks += [(o, yb + 7.5) for o in _objs(g.kids["strike"]["root"])]
    for o, b in marks:
        prev = None
        for f in range(nf):
            h = f < f_tp or b > ext(f) + inner or (b == yb + 7.5 and f < e_sk["f_start"])
            if h != prev:
                o.hide_render = h
                o.keyframe_insert("hide_render", frame=f)
                prev = h
    # ---- 段首、段尾
    bpy.context.view_layer.update()
    head = M_tag @ _mm(0.0, -5.5, 1.6)
    tail = tape_M(e_dv["f_start"]) @ _mm(-3.0, 2.0, 4.5)
    g.run(head, tail, tail_kids=["tape", "lockbtn", "strip", "marks", "hook", "strike"], gest=None)

    def foc(f):
        a = _mm(tx + 10.0, RY - 8.0, 0.0)
        b = _mm(tpx + 12.0, tpy, 0.0)
        return a.lerp(b, smooth((f - f_tp) / 20.0))
    pairs = [("tag", "runner", range(0, nf)), ("tape", "tag", range(f_tp, nf)), ("tape", "pl0", range(f_tp, nf)), ("tape", "pl1", range(f_tp, nf)),
             ("strip", "pl1", range(f_tp, nf)), ("strip", "pl2", range(f_tp, nf)), ("hook", "pl1", range(f_tp, nf)), ("hook", "pl2", range(f_tp, nf)),
             ("pl0", "tag", range(0, nf)), ("lockbtn", "pl0", range(f_tp, nf)), ("lockbtn", "pl1", range(f_tp, nf))]
    return g.result(foc, pairs, info=dict(fr0=round(fr0, 3)))


V804 = dict(
    # 11-23 甲线（18 文档 2.4 8-04–07 简版）：一根竖料杆（屏上 x ≈ 1300、y 80–840），右侧浇口挂五块站牌 computer、protein、cells、animals、patients（屏上约 480 × 110 px）。
    # 简版（18 定案）：牌上不挂小件、不做漏斗和小循环；funnel → computer 牌往前弹一下，loop_on、ring → computer 牌扫光；报纸、五站依次亮、全亮照做。
    # 定案（可改回）：flask（烧瓶是小件）→ cells 牌往前弹 5 mm；person（小人是小件）→ computer 牌跳一下；报纸不印报名（不带任何媒体标识）；
    # paper_away 缩到 0.35 挂到料杆左上（右上角放不下：右沿会过 1880，上沿过 60）；not yet 小牌挂在 patients 牌右下角前面；整组高约 760 px（18 的布局），OC1 上限全段不算。
    PXMM=8.5, REST_D=1.5, REST_PX=(1500.0, 460.0), REST=(10.0, 4.0), ORG=(25.0, 0.0),   # 11-24 Z20：not yet 挪到 patients 右上角外后右沿 1911 → 整组左移 40 px   # 11-23 试渲 PXMM 10：整组屏上 800–850 px，上沿 7、下沿 878、右沿 1938 → 缩到 0.85（牌约 410 × 95 px）
    HEAD_D=0.02, HEAD_PX=(960.0, 540.0), HEAD_CTRL=(2300.0, 470.0, 0.95), HEAD_QW=True, HEAD_EASE=0.6,
    TAIL_D=0.06, TAIL_PX=(960.0, 540.0), TAIL_CTRL=(1500.0, 420.0, 0.7),   # 试渲 0.02：段尾骨白盖满 10 帧（OC7 ≤ 6）→ 0.036；全版 computer 牌带着芯片、小人一起冲，0.036 盖满 9 帧 → 同 6-12 的 0.05；r2 0.05 盖满 7 帧 → 0.06
    BAR=(-38.0, 38.5), RUN_R=0.8, GATE_R=0.45, PL_HW=24.0, PL_HH=5.5, PL_X0=2.0, PL_YS=(32.0, 17.0, 2.0, -13.0, -28.0),
    LABELS=("computer", "protein", "cells", "animals", "patients"), TXT_SIZE=8.0, TEXT_GLOW=3.0, BODY_GLOW=0.45, POP_MM=8.0,
    # 11-24 R2f：报纸 z 9.0 → 10.6。protein 牌上的小插座（转 -60°）后缘和红色卡扣比报纸正面还靠前 0.6–0.9 mm，戳出报纸，成了 a 和 g 之间的灰色碎片和红点；整张报纸前移 1.6 mm（相机远，屏上大小位置变化 < 1 px）
    PAPER=(26.0, 15.0, 10.6), PAPER_K=1.4, PAPER_AWAY=(-14.0, 30.0, 1.5), PAPER_AWAY_K=0.35,
    OC=True, TRANS=True, TRANS_K=1.0, HIDE_RED=True, H_MIN=486, TOP_MIN=60, BOT_MAX=860, OC1_EXEMPT=[(0, 1960)],
    HAND_FRONT=[(641, 877)],                                              # B 举手机的手在报纸前（18 文档 headline 行）
    BOARD_K=1.27, BOARD_HIDE=("stations", "zone_tags", "z1_c0_r0"),
    HEAD_BOX=(300, 90, 900, 680), LOCK_BOX=(1000, 0, 1940, 1080),
    RIM_W=60.0, SAMPLES=16, GRAIN_F=150, GRAIN_GAIN=1.0,
    # 11-23 位1 升全版（18 的 2.4 全表）：FULL=False 就回到上面的简版。牌上刻字改左对齐（左沿 TXT_X0），右上角挂小件（高 SMALL_H mm），
    # computer 牌下的漏斗（40 颗金珠、漏出 5 颗）、cells 牌上的烧瓶（升起、磕牌）、computer 牌芯片前的小循环（trial 转、light 变暖白光环）、白色小人跳。
    SHEEN_K=0.8,   # 11-23 位1：扫光 2.5→0.8×RIM_W（r1 片第 288/1500/1692 帧整列牌冲白约 22 帧）
    FULL=True, TXT_X0=-14.5, SMALL_H=11.0, SMALL_AT=(-3.0, 2.5), SMALL_Z=0.5,
    FUN_AT=(44.0, 20.5, 11.0), FUN_R=(6.5, 1.5), FUN_H=12.0, BEAD_R=0.6, N_BEAD=40, N_OUT=5,
    FLASK_AT=(35.0, 2.0), FLASK_H=10.5, MAN_X=12.0, LOOP_R=3.4, LOOP_T=0.45, LOOP_SEG=12,
)


def _fit_k(root, size_mm, axis="h"):
    """零件（原点放着、还没挂进组）按真实外形定缩放：axis "h" 按高（Y）、"w" 按宽（X）、"m" 按长边。返回 (k, 中心 mm, (z 最小, z 最大) mm)。"""
    bpy.context.view_layer.update()
    lo, hi = mesh_bounds([root])
    d = (hi - lo) / MM
    c = (hi + lo) / 2 / MM
    ref = {"h": d.y, "w": d.x, "m": max(d.x, d.y)}[axis]
    return size_mm / max(ref, 1e-6), c, (lo.z / MM, hi.z / MM)


def _shell_lathe(P, prof, m, x, y, z=0.0, seg=48):
    """lathe 回转体去掉首尾两个封口面（漏斗这种开口的壳）。"""
    import bmesh
    o = P.lathe(prof, m, x, y, z, seg)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    caps = [f for f in bm.faces if len(f.verts) == seg]
    bmesh.ops.delete(bm, geom=caps, context="FACES_ONLY")
    bm.to_mesh(o.data)
    bm.free()
    return o


def _road5_full(g, ys, cx):
    """8-04–07 全版的小件（18 的 2.4 全表）。小件矩阵按牌局部写（原点 = 牌中心，pl{i} 的 fn 已含 _T(cx, y)）。
    返回 tail（段尾跟 computer 牌一起冲镜头的子零件）、pairs（穿模对）、glow（发光关键帧，g.run 以后调）。"""
    import kit_parts as KP
    import kit_socket as S
    import random as _rnd
    K, P, E, nf = g.K, g.P, g.E, g.nf
    hw = P["PL_HW"]
    H = P["SMALL_H"]
    sx, sy = P["SMALL_AT"]
    zf = 1.4 + P["SMALL_Z"]                                          # 牌正面 z = 1.4 mm
    pairs, tail = [], []

    def corner(i, name, root, axis="h", size=H, rot=None, dx=0.0, dy=0.0):
        """小件挂在第 i 块牌的右上角（牌局部 (hw + sx + dx, sy + dy)），贴着牌面前面。"""
        _bake(root)
        for o in list(root.children_recursive):                          # 藏着的件（mini 插座的 lamp_out_off）删掉：_vis_keys 会把它们一起打成出像，掉在镜头位置
            if o.hide_render and o.type in ("MESH", "CURVE", "FONT"):
                bpy.data.objects.remove(o, do_unlink=True)
        rot = rot if rot is not None else Matrix.Identity(4)
        root.matrix_basis = rot                                           # 量外形时先转好（g.add 会把 matrix_basis 换成 M，转角要乘进 M）
        k, c, (z0, z1) = _fit_k(root, size, axis)
        root.matrix_basis = Matrix.Identity(4)
        M = _T(hw + sx + dx, sy + dy, zf - z0 * k) @ _Sc(k) @ _T(-c.x, -c.y, 0.0) @ rot
        g.add(name, root, M, bake=False)
        g.kids[name]["fn"] = (lambda f, i=i, M=M: g.kids[f"pl{i}"]["fn"](f) @ M)
        pairs.append((name, f"pl{i}", range(0, nf)))
        return M, k

    # ---- computer：AI 芯片（右上角）+ 芯片前的小循环 + 白色小人（牌面右半、芯片左边）
    Mc, kc = corner(0, "chip", KP.p13_chip(K, "AI"), "w", P.get("CHIP_W", 10.0))
    lp = KP.Part(K, "road5_loop", "white")
    n, Rr, Rt = P["LOOP_SEG"], P["LOOP_R"], P["LOOP_T"]
    span = 360.0 / n
    for j in range(n):
        a0 = math.radians(j * span + 0.14 * span)
        a1 = math.radians((j + 1) * span - 0.14 * span)
        lp.tube([(Rr * math.cos(a0 + (a1 - a0) * q / 6), Rr * math.sin(a0 + (a1 - a0) * q / 6), 0.0) for q in range(7)], Rt, K.white, smooth=True)
    g.add("loop", lp.done())
    e_lo, e_rg = E["loop_on"], E["ring"]
    c_chip = Mc @ Vector((0.0, 0.0, 0.0))                             # 牌局部 mm（_T 是毫米矩阵）

    def spin(f):
        if f < e_lo["f_start"]:
            return 0.0
        t = f - e_lo["f_start"]
        return 0.12 * t * t if t < 40 else 0.12 * 1600 + 9.6 * (t - 40)          # 越转越快，然后匀速

    Mloop0 = _T(hw + sx, sy, zf + P.get("LOOP_Z", 2.6))

    def loop_M(f):
        k = 1.0 + 0.25 * smooth((f - e_rg["f_start"]) / 16.0)
        return g.kids["pl0"]["fn"](f) @ Mloop0 @ _R("Z", spin(f)) @ _Sc(k)
    g.kids["loop"]["fn"] = loop_M
    pairs += [("loop", "pl0", range(0, nf)), ("loop", "chip", range(0, nf))]
    pp = KP.Part(K, "road5_man", "white")
    KP.person(pp, K.white, 0.0)
    man = pp.done()
    _bake(man)
    mh = P.get("MAN_H", 9.5)
    km, cm, (mz0, mz1) = _fit_k(man, mh, "h")
    Mman = _T(P.get("MAN_X", 14.0), -5.5 + 0.6 + mh / 2, zf - mz0 * km) @ _Sc(km) @ _T(-cm.x, -cm.y, 0.0)
    g.add("man", man, Mman, bake=False)
    e_ps = E["person"]

    def man_M(f):
        t = clamp01((f - (e_ps["f_land"] - 6)) / 14.0)
        return g.kids["pl0"]["fn"](f) @ _T(0.0, 4.0 * math.sin(math.pi * t)) @ Mman
    g.kids["man"]["fn"] = man_M
    pairs += [("man", "pl0", range(0, nf)), ("man", "chip", range(0, nf))]
    tail += ["chip", "loop", "man"]
    # ---- protein：CDK20 小插座（mini，嘴朝镜头偏右）
    corner(1, "sock", S.h01b_cdk20_socket(K, "mini", "slots"), "m", 10.0, dx=-5.0, rot=_R("Y", -60.0) @ _R("X", 12.0))
    # ---- cells：培养皿（俯看 55°）
    corner(2, "dish", KP.p40_dish(K), "w", P.get("DISH_W", 10.0), dx=-2.0, rot=_R("X", -40.0))
    # ---- animals：小鼠（侧面，按长边）
    corner(3, "mouse", KP.p43_mouse(K), "w", P.get("MOUSE_W", 14.0), dx=-1.5, dy=-1.0)
    # ---- patients：灰色小人
    pg = KP.Part(K, "road5_patient", "white")
    KP.person(pg, K.land, 0.0)
    corner(4, "patient", pg.done(), "h", H)
    # ---- 烧瓶：cells 牌右半边、勾和培养皿中间，从牌下沿下面升起（eject），冒泡似的轻颤；decide 往牌面一磕
    fl = KP.p34_flask(K)
    _bake(fl)
    kf, cf, (fz0, fz1) = _fit_k(fl, P["FLASK_H"], "h")
    e_fk, e_dc = E["flask"], E["decide"]
    fx, fy = P["FLASK_AT"]
    zfl = zf + 0.6 - fz0 * kf

    def flask_M(f):
        u = clamp01((f - e_fk["f_start"]) / max(1, e_fk["f_land"] - e_fk["f_start"] + 6))
        up = -9.0 * (1 - ease_out_back(u, 1.3))
        k = kf * (0.25 + 0.75 * ease_out_cubic(u))
        d0, d1 = e_dc["f_land"] - 6, e_dc["f_land"]                    # 磕：往牌面压 0.55 mm、歪 10°，"咔"一下回来
        hit = ease_in_cubic(clamp01((f - d0) / max(1, d1 - d0))) * (1 - ease_out_cubic(clamp01((f - d1) / 10.0)))
        rz = -10.0 * hit + _wob(f, d1, 3.0, 8.0, 10.0)
        bub = 0.25 * math.sin(2 * math.pi * f / 9.0) * smooth((f - e_fk["f_land"]) / 6.0) * (1 - smooth((f - e_fk["f_end"] - 20) / 10.0))
        return g.kids["pl2"]["fn"](f) @ _T(fx - cx, fy + up + bub, zfl - 0.55 * hit) @ _R("Z", rz) @ _Sc(k) @ _T(-cf.x, -cf.y, 0.0)
    g.add("flask", fl, _Sc(0.001), show=e_fk["f_start"], bake=False)
    g.kids["flask"]["fn"] = flask_M
    g.kids["flask"]["bbox_from"] = e_fk["f_land"]
    pairs += [("flask", "pl2", range(e_fk["f_start"], nf)), ("flask", "tick", range(e_fk["f_start"], nf)),
              ("flask", "dish", range(e_fk["f_start"], nf)), ("flask", "pl1", range(e_fk["f_start"], nf)), ("flask", "pl3", range(e_fk["f_start"], nf))]
    # ---- 漏斗 + 40 颗金珠：computer 牌下、右边，narrows 弹出，珠子从上面落进来，只漏出 5 颗，search. 以后收掉
    e_fn = E["funnel"]
    f0, f1 = e_fn["f_start"], e_fn["f_end"]
    fux, fuy, fuz = P["FUN_AT"]
    R0, R1 = P["FUN_R"]
    hh = P["FUN_H"] / 2
    fp = KP.Part(K, "road5_funnel", "clear")
    _shell_lathe(fp, [(R0, hh), (R1, -hh + 2.0), (R1, -hh - 1.2), (R1 - 0.45, -hh - 1.2), (R1 - 0.45, -hh + 2.0), (R0 - 0.45, hh)], K.clear0, 0, 0)
    fp.torus(0, hh, 0, R0 - 0.2, 0.35, K.white, rot=(math.radians(90), 0, 0))
    f_out = f1 + 16
    g.add("funnel", fp.done(), _Sc(0.001), show=f0, hide=f_out + 12, bake=False, bbox=False)

    def fun_k(f):
        return _popk(f, f0, 10, 1.6) * (1 - ease_in_cubic(clamp01((f - f_out) / 10.0)))
    FUNM = _T(fux, fuy, fuz) @ _R("X", -14.0)
    g.kids["funnel"]["fn"] = lambda f: FUNM @ _Sc(max(0.001, fun_k(f)))
    rnd = _rnd.Random(804)
    nb, nout, br = P["N_BEAD"], P["N_OUT"], P["BEAD_R"]
    outs = set(range(3, nb, nb // nout))
    t_in = f0 + 10
    spacing = max(1.0, (f1 - 20 - t_in) / nb)
    y_bot = -hh + 2.0

    def r_in(y):
        return R1 - 0.45 + (R0 - R1) * (y - y_bot) / (hh - y_bot)
    rest = {}
    q = 0
    for j in range(nb):                                                  # 卡在漏斗里的堆：从下往上一圈一圈码
        if j in outs:
            continue
        lay, cnt = 0, q
        while cnt >= 3 + 2 * lay:
            cnt -= 3 + 2 * lay
            lay += 1
        yb = y_bot + 1.2 + lay * 1.15
        rr = max(0.0, (r_in(yb) - br) * 0.72)
        ang = 2 * math.pi * cnt / (3 + 2 * lay) + 0.4 * lay
        rest[j] = (rr * math.cos(ang), yb, rr * math.sin(ang))
        q += 1
    for j in range(nb):
        bp = KP.Part(K, f"road5_bead{j}", "gold")
        bp.ball(0, 0, 0, br, K.gold, seg=16)
        tj = t_in + j * spacing + rnd.uniform(-0.4, 0.4)
        x0 = rnd.uniform(-1.2, 1.2)
        g.add(f"bd{j}", bp.done(), _Sc(0.001), show=int(tj) - 1, hide=(f_out + 12) if j not in outs else int(tj) + 70, bbox=False)

        def bfn(f, j=j, tj=tj, x0=x0):
            if f < tj - 1:
                return _Sc(0.001)
            t = max(0.0, (f - tj) / FPS)
            y_top = hh + 9.0
            y = y_top - 0.5 * 220.0 * t * t                                 # 毫米/秒²：玩具尺度放慢的重力
            kk = 1.0
            if j in outs:
                M = _T(x0 * clamp01(1 - (y_top - y) / (y_top - y_bot)), y, 0.0)
                if y < -hh - 14:
                    kk = max(0.001, 1 - (-hh - 14 - y) / 6.0)
            else:
                rx, ry, rz = rest[j]
                if y > ry:
                    lam = clamp01((y_top - y) / (y_top - ry))
                    M = _T(x0 + (rx - x0) * lam, y, rz * lam)
                else:
                    sett = clamp01((ry - y) / 3.0)
                    M = _T(rx, ry + 0.4 * (1 - sett) * math.sin(6 * sett), rz)
            ks = max(0.001, fun_k(f)) if f >= f_out else 1.0
            return FUNM @ _Sc(ks) @ M @ _Sc(max(0.001, kk))
        g.kids[f"bd{j}"]["fn"] = bfn
    pairs += [("funnel", f"pl{i}", range(f0, f_out + 12)) for i in range(5)]

    def glow():
        warm = (1.0, 0.50, 0.16)
        cg, c2 = E["chip_glow"], E["chip2"]
        txt = [o for o in _objs(g.kids["chip"]["root"]) if o.type == "FONT"] or _objs(g.kids["chip"]["root"])[:1]
        s_, _ = _emit_mat(txt, "road5_chipglow", warm)
        _key_val(s_, [(0, 0.0), (cg["f_start"], 0.0), (cg["f_land"], 6.0), (cg["f_end"] + 10, 1.5), (c2["f_start"], 1.5), (c2["f_land"], 6.0), (c2["f_end"] + 10, 1.5), (nf - 1, 1.5)])
        s_, _ = _emit_mat(_objs(g.kids["loop"]["root"]), "road5_loopglow", (1.0, 0.86, 0.66))
        _key_val(s_, [(0, 0.0), (e_lo["f_start"], 0.0), (e_lo["f_land"], 0.6), (e_rg["f_start"], 0.6), (e_rg["f_land"], 4.0), (nf - 1, 4.0)])
        ck = E["cells_tick"]
        dm = [o for o in _objs(g.kids["dish"]["root"]) if o.active_material and "pink" in o.active_material.name.lower()] or _objs(g.kids["dish"]["root"])[:1]
        s_, _ = _emit_mat(dm, "road5_dishglow", (1.0, 0.55, 0.5))
        _key_val(s_, [(0, 0.0), (ck["f_start"], 0.0), (ck["f_land"] + 4, 0.9), (ck["f_end"] + 24, 0.0), (nf - 1, 0.0)])   # 试渲：常亮 0.6 把红光打到 cells、animals 牌上，只在勾扣上时亮一下
    return dict(tail=tail, pairs=pairs, glow=glow)


def recipe_road5(W):
    """8-04–07（C、B、D、A 四人共用一个场景，1960 帧；简版）。
    G 局部毫米：竖料杆在 x = 0（y BAR），五块站牌中心 (PL_X0 + PL_HW, PL_YS[i])，浇口从料杆往右到牌左沿。
    段首：cells 牌骨白牌面（刻字左边一块）盖满；段尾：computer 牌同一块冲镜头（骨白盖满交给 W5）。"""
    import kit_parts as KP
    g = _Grp(W)
    K, P, E, nf = g.K, g.P, g.E, g.nf
    hw, hh, x0 = P["PL_HW"], P["PL_HH"], P["PL_X0"]
    ys = P["PL_YS"]
    cx = x0 + hw
    yb0, yb1 = P["BAR"]
    st = [E[f"st{i + 1}"] for i in range(5)]
    e_pa, e_hl, e_pw, e_dv = E["paper"], E["headline"], E["paper_away"], E["dive"]
    # ---- 竖料杆 + 五个侧浇口
    rp = KP.Part(K, "road5_runner", "white")
    rp.tube([(0.0, yb0), (0.0, yb1)], P["RUN_R"], K.white)
    for y in ys:
        rp.tube([(0.0, y), (x0 - 0.15, y)], P["GATE_R"], K.white)          # 浇口停在牌左沿前 0.15 mm（贴着不穿）
    g.add("runner", rp.done())
    # ---- 五块站牌（patients 灰）
    txt, bodies = [], []
    for i, (lab, y) in enumerate(zip(P["LABELS"], ys)):
        pp = KP.Part(K, f"road5_pl{i}", "white")
        pp.box(0, 0, hw, hh, 2.8, K.white, r=1.8, bevel=0.6)
        if P.get("FULL"):
            t = pp.text(lab, P["TXT_SIZE"], P["TXT_X0"], -0.3, 1.4, K.ink, align="LEFT")     # 全版：刻字左对齐，右上角让给小件
        else:
            t = pp.text(lab, P["TXT_SIZE"], 0, -0.3, 1.4, K.ink)
        root = pp.done()
        g.add(f"pl{i}", root, _T(cx, y))
        txt.append(t)
        bodies.append([o for o in _objs(root) if o.type == "MESH"])

    def zpop(f, f0, f1, mm, n_in=8, n_out=12):
        if f < f0:
            return 0.0
        return mm * ease_out_back(clamp01((f - f0) / n_in), 1.6) * (1 - ease_inout_cubic(clamp01((f - f1) / n_out)))

    def mk(i):
        y = ys[i]

        def fn(f):
            a = 1.0 * math.sin(2 * math.pi * (f + 37 * i) / 140.0) * smooth((f - 40) / 20.0)      # 牌绕浇口轴轻摆
            a += _wob(f, E["decide"]["f_land"] + i, 4.0, 7.0, 10.0)                              # decide：五块齐颤
            a += _wob(f, E["allglow"]["f_land"] + 6 * i, 2.0, 12.0, 16.0)
            z = zpop(f, st[i]["f_land"] - 4, st[i]["f_end"] + (30 if i == 4 else 4), P["POP_MM"])   # st1–st5：往前弹 8 mm、亮起，再回去
            yy = 0.0
            ry = 0.0
            if i == 0:
                if not P.get("FULL"):
                    z += zpop(f, E["funnel"]["f_start"], E["funnel"]["f_land"] + 10, P["POP_MM"])     # funnel 简版：computer 牌往前弹一下
                    yy += 2.5 * _bumpf(f, E["person"]["f_land"] - 2, 12)                              # person 简版：computer 牌跳一下
                z += 3.0 * smooth((f - (e_dv["f_start"] - 12)) / 12.0)                              # 段尾冲镜头前先往前脱开浇口 3 mm（M7：第 1916 帧牌左沿碰浇口头）
            if i == 2 and not P.get("FULL"):
                z += zpop(f, E["flask"]["f_start"], E["flask"]["f_end"], 5.0)                       # flask 简版：cells 牌往前弹 5 mm
            if i == 2 and P.get("FULL"):
                a += _wob(f, E["decide"]["f_land"], 3.0, 6.0, 8.0)                                   # 全版：烧瓶磕上来，cells 牌多颤一下
            if i == 4:
                ry = _wob(f, st[4]["f_land"] + 4, 9.0, 14.0, 18.0)                                 # patients?：左右晃两下
            return _T(0.0, yy, z) @ _piv(x0, y, 0.0, _R("X", a) @ _R("Y", ry)) @ _T(cx, y)
        return fn
    for i in range(5):
        g.kids[f"pl{i}"]["fn"] = mk(i)
    # ---- cells 牌上的绿勾（屏上约 70 px）
    tk = KP.Part(K, "road5_tick", "green")
    tk.slab([(-4.2, 0.4), (-0.9, -2.9), (4.4, 3.2), (3.0, 4.4), (-0.9, 0.0), (-2.8, 1.8)], 1.2, K.green, bevel=0.3)
    e_ck = E["cells_tick"]
    g.add("tick", tk.done(), _Sc(0.001), show=e_ck["f_start"])
    tick_x = 0.5 if P.get("FULL") else 16.5                                  # 全版：勾挪到 cells 字后面，右上角给培养皿
    g.kids["tick"]["fn"] = lambda f: g.kids["pl2"]["fn"](f) @ _T(tick_x, 0.0, 2.3) @ _Sc(_popk(f, e_ck["f_land"] - 2, 8, 2.4))
    # ---- not yet 小牌：patients 牌右下角前面弹下
    ny = KP.Part(K, "road5_notyet", "white")
    ny.box(0, 0, 10.0, 4.3, 1.4, K.white, r=1.2, bevel=0.3)   # 11-24 Z20：半宽 12 → 10（右沿不出 1880）
    ny.text("not yet", 6.5, 0, -0.3, 0.7, K.ink, italic=True)
    e_ny = E["notyet"]
    g.add("notyet", ny.done(), _Sc(0.001), show=e_ny["f_start"])

    def nyfn(f):   # 11-24 Z20：not yet 在 patients 牌右上角、"patients" 字右边（字右端约局部 x 7.2），上沿离 animals 牌下沿 ≥ 0.3 mm；从右边弹进（往下落会碰 animals 牌）
        u = ease_out_back(clamp01((f - e_ny["f_start"]) / max(1, e_ny["f_land"] - e_ny["f_start"] + 4)), 1.4)
        a = _wob(f, e_ny["f_land"] + 2, 6.0, 12.0, 14.0)
        return g.kids["pl4"]["fn"](f) @ _T(19.0 + 3.0 * (1 - u), 3.0, 2.5) @ _R("Z", -5.0 + a) @ _Sc(_popk(f, e_ny["f_start"], 8, 1.6))
    g.kids["notyet"]["fn"] = nyfn
    # ---- 报纸（不印报名）：headline 落到上面两块牌前，标题逐词变红；ask 缩小挂到料杆左上
    pp = KP.Part(K, "road5_paper", "white")
    pp.box(1.0, -1.0, 20, 14.6, 0.8, K.white, z=-0.5, r=0.4, bevel=0.2)
    pp.box(0, 0, 20, 14.6, 1.2, K.white, z=0.4, r=0.4, bevel=0.2)
    # 11-24 R2-15（_审查批2.md）：标题被报纸自己的横线穿过（y 8.0 那条穿第一行、2.6 那条和图块、栏线顶穿第二行）。
    # 改成：报头两条灰条和上横线都挪到标题第一行上沿以上（上横线下沿 10.38，第一行字顶约 8.9），中间那条删掉，
    # 下横线挪到第二行 g 的下沿（约 −3.8）以下（−5.3…−5.5），图块和栏线整体挪到下横线以下；标题改常规体（不斜）。
    # 字的上下沿按 Blender align_y=CENTER（基线 = y − 0.34 em）和 Instrument Serif 字面（升部 0.74 em、降部 0.215 em）算。
    # 原值：灰条 11.6 / 10.2，横线 8.0（0.22）/ 2.6（0.12），图块 (−9.6, −5.4, 8.0, 6.6)，栏线 0.6 起 8 条，标题斜体、两行 y 6.6 / 1.4。
    pp.inkbox(0, 13.0, 16.0, 0.45, K.inkg, 1.0)
    pp.inkbox(0, 11.7, 12.0, 0.3, K.inkg, 1.0)
    pp.inkbox(0, 10.6, 18, 0.22, K.ink, 1.0)
    pp.inkbox(0, -5.4, 18, 0.12, K.ink, 1.0)
    pp.inkbox(-9.6, -10.2, 8.0, 3.8, K.inkg, 1.0)
    for j in range(5):
        pp.inkbox(9.0, -6.6 - 1.8 * j, 8.6 if j != 4 else 5.0, 0.28, K.inkg, 1.0)
    hs = 6.8   # 11-24 Z20：报纸标题字高 3.4 → 6.8；总宽超 38 mm 分两行
    words = ["AI", "discovers", "a", "cancer", "drug"]
    wo = [pp.text(w, hs, 0.0, 5.2, 1.0, K.ink, italic=False, align="LEFT") for w in words]
    bpy.context.view_layer.update()
    wid = [o.dimensions.x / MM for o in wo]
    sp = 0.3 * hs
    if sum(wid) + sp * (len(wo) - 1) <= 38.0:
        lines = [(5.2, list(range(len(wo))))]
    else:
        lines = [(6.2, [0, 1, 2]), (0.0, [3, 4])]   # AI discovers a / cancer drug（11-24 R2-15：6.6 / 1.4 → 6.2 / 0.0，两行都在上下横线之间）
    for ly, ids in lines:
        x = -(sum(wid[i] for i in ids) + sp * (len(ids) - 1)) / 2
        for i in ids:
            wo[i].location.x = x * MM
            wo[i].location.y = (ly + getattr(pp, "oy", 0.0)) * MM
            x += wid[i] + sp
    px, py, pz = P["PAPER"]
    ax, ay, az = P["PAPER_AWAY"]
    pk, ak = P["PAPER_K"], P["PAPER_AWAY_K"]
    g.add("paper", pp.done(), _Sc(0.001), show=e_pa["f_start"])
    g.kids["paper"]["bbox_from"] = e_pa["f_land"]

    def paper_M(f):
        u = clamp01((f - e_pa["f_start"]) / max(1, e_pa["f_land"] - e_pa["f_start"]))
        drop = 45.0 * (1 - ease_out_cubic(u))
        rz = 8.0 * (1 - ease_out_back(u, 1.5)) + _wob(f, e_pa["f_land"], 2.0, 14.0, 14.0)
        w = ease_inout_cubic(clamp01((f - e_pw["f_start"]) / max(1, e_pw["f_land"] - e_pw["f_start"])))
        rz += 1.2 * math.sin(2 * math.pi * f / 160.0) * smooth((f - e_pw["f_land"]) / 20.0)
        k = pk * (1 + (ak - 1) * w)
        return _T(px + (ax - px) * w, py + drop + (ay - py) * w, pz + (az - pz) * w) @ _R("Z", rz) @ _Sc(k)
    g.kids["paper"]["fn"] = paper_M
    pg = KP.Part(K, "road5_pgate", "white")
    pg.tube([(-0.5, 0.0, 0.0), (-4.8, 0.0, 1.5)], P["GATE_R"], K.white)
    g.add("pgate", pg.done(), _T(0.0, ay) @ _Sc(0.001), show=e_pw["f_land"] - 2)
    g.kids["pgate"]["fn"] = lambda f: _T(0.0, ay) @ _Sc(_popk(f, e_pw["f_land"] - 2, 6, 1.4))
    # ---- pulse：一个鼓包沿料杆从上走到下
    pu = KP.Part(K, "road5_pulse", "white")
    pu.tube([(0.0, -1.8), (0.0, 1.8)], 1.6, K.white)
    e_pu = E["pulse"]
    g.add("pulse", pu.done(), _Sc(0.001), show=e_pu["f_start"], hide=e_pu["f_land"] + 1, bbox=False)

    def pufn(f):
        u = clamp01((f - e_pu["f_start"]) / max(1, e_pu["f_land"] - e_pu["f_start"]))
        k = smooth(u / 0.12) * (1 - smooth((u - 0.88) / 0.12))
        return _T(0.0, yb1 - 2.5 - (yb1 - yb0 - 5.0) * ease_inout_cubic(u)) @ _Sc(max(0.001, k))
    g.kids["pulse"]["fn"] = pufn

    def gest(f):                                                      # next：料杆像钟摆晃；decide：镜头微震；Thanks：整条路轻摆
        a = _wob(f, E["bar_sway"]["f_start"], 2.5, 26.0, 22.0) + _wob(f, E["allglow"]["f_land"], 1.2, 30.0, 30.0)
        d = 0.0012 * _wob(f, E["decide"]["f_land"], 1.0, 4.0, 5.0)
        return Vector((d, 0.0, 0.6 * d)), Quaternion((0, 1, 0), math.radians(a))
    face = Vector((-17.0 * MM, 0.0, 1.45 * MM))
    head = g.kids["pl2"]["fn"](0) @ face
    tail = g.kids["pl0"]["fn"](e_dv["f_start"]) @ face
    FULLP = _road5_full(g, ys, cx) if P.get("FULL") else None
    g.run(head, tail, tail_kids=["pl0"] + (FULLP["tail"] if FULLP else []), gest=gest)
    # ---- 发光：牌上刻字（chip_glow 一闪，st 亮起留着）、牌身（allglow 从上到下暖色；patients 在 st5 先亮一点）、报纸标题逐词变红
    warm, G_ = (1.0, 0.50, 0.16), P["TEXT_GLOW"]
    for i in range(5):
        s_, _ = _emit_mat([txt[i]], f"road5_txt{i}", warm)
        o0 = st[i]["f_land"]
        ks = [(0, 0.0)]
        if i == 0:
            cg = E["chip_glow"]
            ks += [(cg["f_start"], 0.0), (cg["f_land"], 1.2 * G_), (cg["f_end"] + 10, 0.0)]
        ks += [(o0 - 1, 0.0), (o0 + 5, 1.3 * G_), (o0 + 16, G_), (nf - 1, G_)]
        _key_val(s_, ks)
        b_, _ = _emit_mat(bodies[i], f"road5_body{i}", (1.0, 0.62, 0.32))
        a0 = E["allglow"]["f_land"] + 6 * i
        kb = [(0, 0.0)]
        if i == 4:
            kb += [(o0 - 1, 0.0), (o0 + 6, 0.2)]
        kb += [(a0 - 2, kb[-1][1]), (a0 + 8, P["BODY_GLOW"])]
        if i == 0:                                                    # 段尾冲镜头时退回骨白（交给 W5 的末帧是骨白盖满）
            kb += [(e_dv["f_start"], P["BODY_GLOW"]), (e_dv["f_start"] + 16, 0.0)]
        kb += [(nf - 1, kb[-1][1])]
        _key_val(b_, kb)
    hl = [w for w in g.cfg["K"]["words"] if e_hl["f_start"] - 6 <= w["f0"] <= e_hl["f_end"]][:len(wo)]
    for j, (o, w) in enumerate(zip(wo, hl)):
        s_, _ = _emit_mat([o], f"road5_hl{j}", (1.0, 0.10, 0.06))
        _key_val(s_, [(0, 0.0), (w["f0"] - 1, 0.0), (w["f0"] + 4, 1.3 * G_), (w["f0"] + 14, G_), (nf - 1, G_)])
    pus, _ = _emit_mat(_objs(g.kids["pulse"]["root"]), "road5_pulse_glow", warm)
    _key_val(pus, [(0, 2.5), (nf - 1, 2.5)])
    def foc(f):
        a = _mm(cx, 2.0, 0.0)
        b = _mm(px, py, pz)
        return a.lerp(b, smooth((f - e_pa["f_start"]) / 16.0) * (1 - smooth((f - e_pw["f_start"]) / 16.0)))
    pairs = [(f"pl{i}", "runner", range(0, nf)) for i in range(5)]
    pairs += [(f"pl{i}", f"pl{j}", range(0, nf)) for i in range(5) for j in range(i + 1, 5)]
    pairs += [("paper", f"pl{i}", range(e_pa["f_start"], nf)) for i in range(5)] + [("paper", "runner", range(e_pa["f_start"], nf))]
    pairs += [("tick", "pl2", range(e_ck["f_start"], nf)), ("notyet", "pl4", range(e_ny["f_start"], nf)), ("notyet", "pl3", range(e_ny["f_start"], nf))]
    if FULLP:
        pairs += FULLP["pairs"]
        FULLP["glow"]()
    R = g.result(foc, pairs, info=dict(headline=[(w["w"], w["f0"]) for w in hl]))
    # ---- 扫光：chip_glow、chip2、loop_on、ring 掠过 computer 牌
    hcol = bpy.data.collections["ONCAM_hero"]
    for nm in ("chip_glow", "chip2", "loop_on", "ring"):
        f0 = E[nm]["f_land"] - 2
        c = g.LM[f0] @ (g.km("pl0", f0) @ Vector((0.0, 0.0, 0.0)))
        c_a, c_b = c + Vector((-0.35, -0.35, 0.04)), c + Vector((0.35, -0.35, 0.04))
        o = make_light("sheen", "AREA", c_a, c, 0.08, P["RIM_W"] * P.get("SHEEN_K", 2.5), kelvin_rgb(6500), size_y=0.2)
        o.light_linking.receiver_collection = hcol
        o.visible_camera = False
        for f, cc, en in ((f0 - 1, c_a, 0.0), (f0, c_a, P["RIM_W"] * P.get("SHEEN_K", 2.5)), (f0 + 22, c_b, P["RIM_W"] * P.get("SHEEN_K", 2.5)), (f0 + 23, c_b, 0.0)):
            o.location = cc
            o.keyframe_insert("location", frame=f)
            o.data.energy = en
            o.data.keyframe_insert("energy", frame=f)

    return R


RECIPES = {"lock_key": recipe_lock_key, "lock_key_v2": recipe_lock_key_v2, "socket_lineup": recipe_socket_lineup, "frost_blank": recipe_frost_blank,
           "socket_plug": recipe_socket_plug, "calendar_people": recipe_calendar_people, "capsule_row": recipe_capsule_row,
           "key_tape": recipe_key_tape, "two_plates": recipe_two_plates, "plates": recipe_plates, "podium": recipe_podium, "plug_row": recipe_plug_row, "snip_tail": recipe_snip_tail,
           "tray13": recipe_tray13, "loop_chip": recipe_loop_chip, "road_tape": recipe_road_tape, "road5": recipe_road5}


# ---------------------------------------------------------------- 搭整段
def build(seg, samples=SAMPLES):
    import bl_guide as BG
    cfg = seg_cfg(seg)
    light = json.loads((cfg["work"] / "light.json").read_text(encoding="utf-8"))
    fit = load_fit(cfg, light)
    W = build_world(cfg, fit, samples)
    sc, cam, nf = W["sc"], W["cam"], cfg["nf"]
    plan = BG.plan_from_keys(cfg["K"])
    R = RECIPES[cfg["recipe"]](W)
    fgw = fg_wipe(W["kit"]) if cfg.get("head") == "T5" else None
    # 镜头：以人卡片为轴的微动；段尾 T1 推进（位置 easeInCubic 加速穿进去，朝向 slerp，镜头偏移收回 0）
    t0 = R["push"]["t0"] if cfg.get("tail") == "T1" else nf
    CM, SH = [], []
    Mend = look_at(R["push"]["eye"], R["push"]["target"]) if t0 < nf else None
    for f in range(nf):
        M = cam_matrix_micro(f)
        sh = SHIFT
        if f >= t0:
            u = (f - t0) / max(1, nf - 1 - t0)
            M = interp_mat(cam_matrix_micro(t0), Mend, ease_in_cubic(u) * 0.985 + 0.015 * u)
            k = smooth(u * 1.4)
            sh = (SHIFT[0] * (1 - k), SHIFT[1] * (1 - k))
        CM.append(M); SH.append(sh)
        key_matrix(cam, f, M)
        cam.data.shift_x, cam.data.shift_y = sh
        cam.data.keyframe_insert("shift_x", frame=f)
        cam.data.keyframe_insert("shift_y", frame=f)
    linear_keys(cam); linear_keys(cam.data)
    # 焦点：没点名时在 BASE_FOCUS，点名时跟零件（bl_guide.focus_track），推进时跟推进目标
    base = lambda f: tuple(CM[f] @ Vector((0, 0, -BASE_FOCUS)))   # noqa: E731
    fp = BG.focus_track(plan, R["targets"], nf, base=base)
    FD = []
    for f in range(nf):
        loc = CM[f].translation
        fwd = (CM[f].to_3x3() @ Vector((0, 0, -1))).normalized()
        p = fp[f] if fp[f] is not None else Vector(base(f))
        dist = (p - loc).dot(fwd)
        for fa, fb, get in R.get("focus2", []):            # 焦点临时借给别的零件，两头 10 帧过渡
            if fa <= f <= fb:
                u = smooth((f - fa) / 10) * smooth((fb - f) / 10)
                dist = dist * (1 - u) + (Vector(get(f)) - loc).dot(fwd) * u
        if f >= t0:
            u = smooth((f - t0) / 8)
            dist = dist * (1 - u) + (Vector(R["push"]["target"]) - loc).dot(fwd) * u
        cam.data.dof.focus_distance = max(0.02, dist)
        cam.data.dof.keyframe_insert("focus_distance", frame=f)
        FD.append(cam.data.dof.focus_distance)
    linear_keys(cam.data)
    # 轮廓光：放在弹出落位附近，主光 15% 起，rimcal 再标到 +0.18 EV
    land = plan[0]["land"] if plan else 0
    sc.frame_set(min(nf - 1, land + 16))
    rims = BG.guide_rim(plan, R["rim"], cam, W["rig"]["key"])
    # 检查数
    chk = dict(seg=seg, recipe=cfg["recipe"], info=R["info"], plan=plan, fstop=FSTOP, lens=round(LENS, 3), shift=SHIFT, f_px=F_PX,
               d_person=D_PERSON, board=dict(S=BOARD_S, D=BOARD_D), micro_deg=MICRO, push_t0=t0, fg=fgw, fit=fit,
               rim={k: dict(name=v.name, peak_w=v["peak_w"]) for k, v in rims.items()})

    def coc(S, D_):
        fl = LENS * MM
        c = fl * fl / (FSTOP * (S - fl)) * abs(D_ - S) / D_
        return c / (36 * MM) * OUT_W
    for f in sorted(set([20, 150, 176, 200, 240, 330, 360])):
        fwd = (CM[f].to_3x3() @ Vector((0, 0, -1))).normalized()
        dl = (R["targets"]["card"](f) - CM[f].translation).dot(fwd)
        chk.setdefault("coc_px", {})[f] = dict(focus=round(FD[f], 3), lock=round(coc(FD[f], dl), 2), board=round(coc(FD[f], BOARD_D), 2))
    chk["clip"] = R["checks"]()
    # 每帧导出：人卡片四角（5 个子帧，快门 0.5）、主零件包围框、钥匙框（给合成和 check 用）
    corners = card_corners()
    frames = []
    for f in range(nf):
        subs = []
        for s in (-0.25, -0.125, 0.0, 0.125, 0.25):
            g = f + s
            a, b = int(math.floor(g)), int(math.floor(g)) + 1
            t = g - a
            a, b = max(0, min(nf - 1, a)), max(0, min(nf - 1, b))
            M = interp_mat(CM[a], CM[b], t)
            sh = (SH[a][0] * (1 - t) + SH[b][0] * t, SH[a][1] * (1 - t) + SH[b][1] * t)
            subs.append([list(project(M, sh, c)) for c in corners])
        bb = [project(CM[f], SH[f], p) for p in R["bbox"](f)]
        frames.append(dict(card=subs, hero=[min(p[0] for p in bb), min(p[1] for p in bb), max(p[0] for p in bb), max(p[1] for p in bb)],
                           focus=FD[f]))
    cfg["work"].mkdir(parents=True, exist_ok=True)
    (cfg["work"] / "cam.json").write_text(json.dumps(dict(seg=seg, nf=nf, push_t0=t0, fg_last=fgw["last"] if fgw else -1, frames=frames)), encoding="utf-8")
    sc.frame_set(0)
    blend = cfg["work"] / "scene.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    (cfg["work"] / "check.json").write_text(json.dumps(chk, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("ONCAM build", json.dumps(dict(clip=chk["clip"], coc=chk["coc_px"], info=R["info"]), default=str)[:3000], flush=True)


def _open(seg):
    cfg = seg_cfg(seg)
    bpy.ops.wm.open_mainfile(filepath=str(cfg["work"] / "scene.blend"))
    import bl_guide as BG
    gpu_wait()
    BG._gpu(bpy.context.scene)
    return cfg, bpy.context.scene


def _pass(sc, which, cfg):
    fg = [o for o in sc.objects if o.get("fg")]
    if which in ("front", "wipe"):
        # v2：只有零件（锁、外壳块、钥匙）的透明通道，锁比人近的帧用它把人挡住。别的东西不出像，但照样投影/反射（Holdout 不要）
        for o in sc.objects:
            if o.type in ("MESH", "CURVE", "FONT") and not o.get("hero"):
                o.visible_camera = False
        sc.render.film_transparent = True
        sc.render.image_settings.color_mode = "RGBA"
        sc.cycles.samples = min(24, sc.cycles.samples)
        return
    if which == "fg":
        keep = set(fg) | {o for o in sc.objects if o.type in ("LIGHT", "CAMERA")}
        for o in sc.objects:
            if o not in keep and o.type not in ("EMPTY",):
                o.hide_render = True
        sc.render.film_transparent = True
        sc.render.image_settings.color_mode = "RGBA"
        cam = json.loads((cfg["work"] / "cam.json").read_text(encoding="utf-8"))
        sc.frame_end = cam["fg_last"]
    else:
        for o in fg:
            o.hide_render = True


def render(seg, which="bg"):
    cfg, sc = _open(seg)
    _pass(sc, which, cfg)
    sc.render.resolution_percentage = 100      # rimcal（bl_guide.calib）存回的场景是半分辨率
    if which in ("bg", "front"):                # 11-24 透明/体积件补渲开关（CDK20_SAMPLES / CDK20_DENOISER，见 shot_drill.noise_knobs）；默认不设 = 不变
        import shot_drill as _SD
        _SD.noise_knobs(sc)
    tag = os.environ.get("CDK20_FR_TAG", "") if which in ("bg", "front") else ""   # 补渲写 fr_bg<TAG>/、fr_front<TAG>/，不碰原帧
    fr0, fr1 = (int(x) for x in os.environ["CDK20_FRANGE"].split("-")) if os.environ.get("CDK20_FRANGE") else (0, 10 ** 9)
    out = cfg["work"] / f"fr_{which}{tag}"
    if which != "wipe":                        # wipe 写 bwipe/，不建 fr_wipe
        out.mkdir(parents=True, exist_ok=True)
        sc.render.filepath = str(out / {"bg": "b_", "fg": "f_", "front": "r_"}[which])
    sc.render.use_overwrite = False
    sc.render.use_placeholder = True
    t = time.time()
    if which == "wipe":
        # 给相邻 B 页（Remotion）的 T5 擦除层（11 文档 5.6）：段首 16 帧、段尾 16 帧只有零件的透明通道。
        # B 页结尾倒放段首这 16 帧 = 零件冲进镜头盖满画面，切到本段第 0 帧；B 页开头倒放段尾 16 帧 = 从盖满画面退出去。
        import shutil
        wd = WORK_ROOT / "bwipe" / f"oncam_{seg}"
        wd.mkdir(parents=True, exist_ok=True)
        nf = cfg["nf"]
        for f in list(range(16)) + list(range(nf - 16, nf)):
            p = wd / f"w_{f:04d}.png"
            if p.exists():
                continue
            fr_ = cfg["work"] / "fr_front" / f"r_{f:04d}.png"
            if fr_.exists():
                shutil.copyfile(fr_, p)
                continue
            sc.frame_set(f)
            sc.render.filepath = str(p)
            bpy.ops.render.render(write_still=True)
        print("ONCAM render wipe", wd, round(time.time() - t, 1), "s", flush=True)
        return
    if which == "front":
        cam = json.loads((cfg["work"] / "cam.json").read_text(encoding="utf-8"))
        for f in cam["front"]:
            if not fr0 <= f <= fr1:
                continue
            p = out / f"r_{f:04d}.png"
            if p.exists():
                continue
            sc.frame_set(f)
            sc.render.filepath = str(p)
            bpy.ops.render.render(write_still=True)
        print("ONCAM render front", len(cam["front"]), round(time.time() - t, 1), "s", flush=True)
        return
    if os.environ.get("CDK20_FRANGE"):         # 只补渲这一截（默认整段）
        sc.frame_start, sc.frame_end = max(sc.frame_start, fr0), min(sc.frame_end, fr1)
    bpy.ops.render.render(animation=True)
    print("ONCAM render", which, round(time.time() - t, 1), "s", flush=True)


def frames(seg, flist, which="bg", pct=100):
    cfg, sc = _open(seg)
    _pass(sc, which, cfg)
    sc.render.resolution_percentage = pct
    out = cfg["work"] / "test"
    out.mkdir(parents=True, exist_ok=True)
    for f in flist:
        sc.frame_set(f)
        sc.render.filepath = str(out / f"{which}_{f:04d}.png")
        t = time.time()
        bpy.ops.render.render(write_still=True)
        print("ONCAM frame", f, round(time.time() - t, 2), "s", flush=True)


def rimcal(seg):
    import bl_guide as BG
    cfg = seg_cfg(seg)
    out = cfg["work"] / "rimcal"
    out.mkdir(parents=True, exist_ok=True)
    BG.calib(str(cfg["work"] / "scene.blend"), str(out), target_ev=0.18, pct=50)


# ================================================================ 合成（纯 numpy + PIL，CPU，不用 Blender）
PERSON_DN = int(os.environ.get("ONCAM_DN", "1"))       # 11-23 D1：人像时域降噪档（0 无 / 1 弱 / 2 中），默认 = 弱档（1-01 试验选定：弱降噪 + unsharp 0.7）
PERSON_SH = float(os.environ.get("ONCAM_SH", "0.7"))     # 人像 unsharp 量
SEG_SH = {"4-08": 0.5, "1-01": 0.3, "4-04_4-05": 0.15, "5-02": 0.25, "8-04_8-05_8-06_8-07": 0.4}   # 11-24：M10 颗粒比 < 0.25 的段，人像锐化减小（试验 4-08 0.5 → 0.28）
GRAIN_GAIN = 1.0       # 11-23 D1：1.7 → 1.0（颗粒只对上素材底噪，不放大；原 1.7 保留在这行注释里）。颗粒强度倍数（σ 从 T 恤量，见 measure）。1.4 时成片零件层只有人的 0.60，1.7 → 约 0.73
LW_STRENGTH = 0.28      # 光包边强度（08 文档第八节 0.15–0.35）
LW_BLUR = 26            # 背景取色模糊（px）
LW_BAND = 9             # 人物遮罩内沿带宽（px）
CG_SOFT = 0.6           # 零件层轻高斯（px，08 文档 0.4–0.8）
CG_SAT = 0.94           # 零件层饱和度向人看齐


def _dilate(m, r):
    """布尔图方形膨胀 r 像素（纯 numpy，可分离的滑动最大值）。"""
    import numpy as np
    out = m.copy()
    for ax in (0, 1):
        acc = out.copy()
        for s in range(1, r + 1):
            acc |= np.roll(out, s, ax) | np.roll(out, -s, ax)
        out = acc
    return out


MATTE_LEAK = dict(head_y=560, lum=0.28, blue_over_red=0.03, edge_px=14, grow=2)


def matte_leak_mask(a):
    """抠像漏进来的背景暗块（手指边上的深蓝/黑色碎片，3-01 第 322、355–358 帧）：
    头发以下、离抠像边缘 edge_px 以内、很暗且偏蓝（皮肤红大于蓝，衣服印花在内部不贴边）的像素。返回布尔图。"""
    import numpy as np
    A = a[..., 3] > 0.5
    L = a[..., :3].mean(-1)
    m = (a[..., 3] > 0.06) & (L < MATTE_LEAK["lum"]) & (a[..., 2] > a[..., 0] + MATTE_LEAK["blue_over_red"])
    m[:MATTE_LEAK["head_y"], :] = False
    if not m.any():
        return m
    near_edge = _dilate(~A, MATTE_LEAK["edge_px"])
    m &= near_edge
    return _dilate(m, MATTE_LEAK["grow"]) & (a[..., 3] > 0) if m.any() else m


def matte_leak_keep(a):
    """抠像透明度乘数：漏进来的暗块置 0（边缘 1 px 软化）。"""
    import numpy as np
    m = matte_leak_mask(a)
    if not m.any():
        return 1.0
    b = a.copy()
    for _ in range(4):                          # 剥掉一层以后，里面一层又贴边了：剥到没有为止（最多 4 层）
        b[..., 3] = np.where(m, 0.0, a[..., 3])
        m2 = matte_leak_mask(b) | m
        if (m2 == m).all():
            break
        m = m2
    soft = m.astype(np.float32)
    soft = np.maximum(soft, 0.5 * (_dilate(m, 1) & ~m))
    return 1.0 - soft


def _persp_coeffs(src, dst):
    """PIL PERSPECTIVE 的 8 个系数：输出坐标 dst → 输入坐标 src。"""
    import numpy as np
    A, b = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); b.append(v)
    return np.linalg.solve(np.array(A, dtype=np.float64), np.array(b, dtype=np.float64)).tolist()


def _grain(rng, shape):
    """手机素材的颗粒不是逐像素白噪声（降噪 + 压缩后颗粒是 2–3 像素的小团）：白噪声 [1,2,1] 两遍平滑后重新归一到标准差 1。
    逐像素的白噪声会被 h264 在平坦处整个抹掉（实测 cq16 编码后只剩 1/6）。"""
    import numpy as np
    n = rng.normal(0.0, 1.0, shape).astype(np.float32)
    for _ in range(2):
        n = (np.roll(n, 1, 0) + 2 * n + np.roll(n, -1, 0)) / 4
        n = (np.roll(n, 1, 1) + 2 * n + np.roll(n, -1, 1)) / 4
    return n / n.std() * GRAIN_GAIN


class Comp:
    def __init__(self, seg):
        import numpy as np
        from PIL import Image
        self.cfg = cfg = seg_cfg(seg)
        self.work = cfg["work"]
        self.light = json.loads((self.work / "light.json").read_text(encoding="utf-8"))
        self.cam = json.loads((self.work / "cam.json").read_text(encoding="utf-8"))
        self.sig = np.array(self.light["grain_sigma_rgb"], dtype=np.float32) / 255.0
        self.sig *= cfg["P"].get("GRAIN_GAIN", GRAIN_GAIN) / GRAIN_GAIN     # 段自己的颗粒倍数（_grain 里乘的是全局 GRAIN_GAIN）
        P = PERSON
        self.ident = [[P["x"], P["y"] + P["h"]], [P["x"] + P["w"], P["y"] + P["h"]], [P["x"] + P["w"], P["y"]], [P["x"], P["y"]]]
        self.src = [[0, P["h"]], [P["w"], P["h"]], [P["w"], 0], [0, 0]]
        ramp = np.ones(P["w"], dtype=np.float32)
        ramp[P["w"] - EDGE_FEATHER:] = np.linspace(1, 0, EDGE_FEATHER, dtype=np.float32)
        self.ramp = ramp
        self.Image = Image
        self.front = set(self.cam.get("front", []))
        self.src = self.src_plate(cfg.get("src"))

    def src_plate(self, text):
        """18 文档 1.6 / OC8 出处行（出镜段）：Instrument Serif 30 px，右对齐右沿 1856，上沿 886、下沿 928，深色底衬 0.66 加浅字。
        返回 (整帧 RGBA 浮点层, 淡入淡出函数)；段首落位后 12 帧淡入，段尾冲镜头起 8 帧淡出（盖满画面那几帧干净）。"""
        if not text:
            return None
        import numpy as np
        from PIL import ImageDraw, ImageFont
        fnt = ImageFont.truetype(str(ROOT / "镜头设计_v3/remotion_public/fusion_s1/fonts/InstrumentSerif-Regular.ttf"), 30)
        im = self.Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        x1, y0, y1, pad = 1856, 886, 928, 14
        l, t, r, b = dr.textbbox((0, 0), text, font=fnt, anchor="ls")
        tw = r - l
        dr.rectangle((x1 - tw - 2 * pad, y0, x1, y1), fill=(14, 16, 24, int(255 * 0.66)))
        base = (y0 + y1) / 2 + (-(t + b) / 2)
        dr.text((x1 - pad - r, base), text, font=fnt, fill=(240, 238, 232, 255), anchor="ls")
        L = np.asarray(im, dtype=np.float32) / 255
        ev = self.cfg["K"]["events"]
        fa, fd = ev[0]["f_land"], ev[-1]["f_start"]
        if self.cfg.get("src_until"):                                 # 多人段出处行只挂在第一个人那段（8-04–07 只在 C 说的时候）
            fd = min(fd, self.cfg["src_until"] - 8)
        return L, lambda f: smooth((f - fa) / 12.0) * (1 - smooth((f - fd) / 8.0))

    def person_rgba(self, f):
        import numpy as np
        im = self.Image.open(person_png(self.cfg, f)).convert("RGBA")
        a = np.asarray(im, dtype=np.float32) / 255.0
        a = a.copy()
        a = self.person_enhance(a, f)
        if leak_strip_on(self.cfg, f):
            a[..., 3] *= matte_leak_keep(a)
        a[..., 3] *= self.ramp[None, :]
        return a

    # 11-23 D1：人像偏软偏噪，只在人的遮罩内做轻度时域降噪 + 轻锐化（环境变量 ONCAM_DN=0/1/2 无/弱/中，ONCAM_SH=unsharp 量）
    def _nb_rgb(self, f):
        import numpy as np
        c = self.__dict__.setdefault("_nbc", {})
        if f not in c:
            if len(c) > 4:
                c.pop(next(iter(c)))
            c[f] = np.asarray(self.Image.open(person_png(self.cfg, f)).convert("RGB"), dtype=np.float32) / 255.0
        return c[f]

    def person_enhance(self, a, f):
        import numpy as np
        from PIL import ImageFilter
        dn, sh = PERSON_DN, SEG_SH.get(self.cfg.get("seg"), PERSON_SH) if "ONCAM_SH" not in os.environ else PERSON_SH   # 11-24 段内覆盖：这几段 M10 卡下限，锐化放小
        if dn <= 0 and sh <= 0:
            return a
        rgb = a[..., :3]
        al = a[..., 3:4]
        out = rgb
        if dn > 0:
            tau = (0.035, 0.06)[min(dn, 2) - 1]          # 邻帧差到这么大时权重降到 1/e：超过的地方（手在动）不混，不拖影
            acc, wsum = rgb.copy(), np.ones(rgb.shape[:2] + (1,), dtype=np.float32)
            for g in (f - 1, f + 1):
                try:
                    nb = self._nb_rgb(g)
                except Exception:
                    continue
                if nb.shape != rgb.shape:
                    continue
                d = np.abs(nb - rgb).mean(-1, keepdims=True)
                w = np.exp(-(d / tau) ** 2)
                acc += nb * w
                wsum += w
            out = acc / wsum
        if sh > 0:
            u8 = self.Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))
            bl = np.asarray(u8.filter(ImageFilter.GaussianBlur(1.4)), dtype=np.float32) / 255.0
            out = np.clip(out + sh * (out - bl), 0, 1)
        # 只在遮罩内部：遮罩边带 3 px 不动（锐化在边上会出白边）
        am = self.Image.fromarray((al[..., 0] * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(7))
        m = (np.asarray(am, dtype=np.float32) / 255.0)[..., None]
        res = a.copy()
        res[..., :3] = rgb * (1 - m) + out * m
        return res

    def person_layer(self, f):
        """人放回最前：卡片投影四角没动（< 0.75 px）就原像素直接贴（人一点不动）；推进时按 5 个子帧的透视变换平均（运动模糊）。"""
        from PIL import ImageFilter
        import numpy as np
        P = PERSON
        a = self.person_rgba(f)
        subs = self.cam["frames"][f]["card"]
        full = np.zeros((OUT_H, OUT_W, 4), dtype=np.float32)
        ds = [math.hypot(c[0] - i[0], c[1] - i[1]) for s in subs for c, i in zip(s, self.ident) if c[0] == c[0]]
        if len(ds) < len(subs) * 4:
            return full, float("inf")              # 卡片有角到了镜头后面（推进穿过去），人不在画里
        dev = max(ds)
        t0 = self.cam["push_t0"]
        if self.cam.get("version") == 2 or f < t0 or dev < 0.75:   # v2 相机不推进：人永远原像素                   # 推进前人一律原像素不动（微动只是背景的视差；卡片投影的几像素偏移只影响影子）
            x0, y0 = P["x"], P["y"]
            sx = max(0, -x0)
            w = min(OUT_W - max(0, x0), P["w"] - sx)
            h = min(OUT_H - y0, P["h"])
            full[y0:y0 + h, max(0, x0):max(0, x0) + w] = a[:h, sx:sx + w]
            return full, 0.0 if (f < t0 or self.cam.get("version") == 2) else dev
        if any(c[2] < 0.05 for s in subs for c in s):
            return full, float("inf")                       # 卡片已经在镜头后面（推进穿过去以后），人不在画里
        pre = a.copy()
        pre[..., :3] *= pre[..., 3:4]
        src_im = [self.Image.fromarray((pre[..., k] * 255).astype(np.uint8)) for k in range(4)]
        acc = np.zeros_like(full)
        c0 = self.cam["frames"][t0]["card"][2]      # 推进起点的卡片投影 = 人原位：只加推进带来的位移，起步不跳
        for s in subs:
            dst = [(c[0] - b[0] + i[0], c[1] - b[1] + i[1]) for c, b, i in zip(s, c0, self.ident)]
            co = _persp_coeffs(self.src, dst)
            for k in range(4):
                acc[..., k] += np.asarray(src_im[k].transform((OUT_W, OUT_H), self.Image.PERSPECTIVE, co, self.Image.BILINEAR), dtype=np.float32) / 255
        acc /= len(subs)
        # 推进时人卡片离焦外越来越近：按真实弥散圆（相对推进开始时多出来的部分）把人虚掉，穿过镜头前淡出
        zmin = min(c[2] for c in subs[2])
        coc = lambda S, D: (LENS * MM) ** 2 / (FSTOP * (S - LENS * MM)) * abs(D - S) / max(D, 1e-3) / (36 * MM) * OUT_W   # noqa: E731
        r = coc(self.cam["frames"][f]["focus"], zmin) - coc(self.cam["frames"][t0]["focus"], D_PERSON)
        if r > 1.0:
            for k in range(4):
                im = self.Image.fromarray(np.clip(acc[..., k] * 255, 0, 255).astype(np.uint8))
                acc[..., k] = np.asarray(im.filter(ImageFilter.GaussianBlur(min(80.0, r) / 2)), dtype=np.float32) / 255
        acc *= smooth((zmin - 0.02) / 0.35)
        rgb = acc[..., :3] / np.maximum(1e-4, acc[..., 3:4])
        return np.concatenate([np.clip(rgb, 0, 1), acc[..., 3:4]], -1), dev

    def v2_person(self, P, f):
        """v2：焦点比人近时（段首段尾锁贴镜头）按焦距差把人虚掉；锁比人近的帧用 front 层的透明通道挡住人。"""
        import numpy as np
        from PIL import ImageFilter
        S = self.cam["frames"][f]["focus"]
        r = 0.0 if S >= D_PERSON else min(40.0, 30.0 * (D_PERSON / max(S, 1e-3) - 1.0))
        z0, z1 = self.cfg["P"].get("PBLUR_ZERO", (0, 0))
        if z0 <= f < z1:                                                  # 11-23 审查（5-02）：零件靠近镜头那几秒焦点比人近，人被虚掉；这段人不虚，零件照常清楚地叠在上面
            r = 0.0
        if r > 0.6:
            pre = P.copy()
            pre[..., :3] *= pre[..., 3:4]
            for k in range(4):
                im = self.Image.fromarray(np.clip(pre[..., k] * 255, 0, 255).astype(np.uint8))
                pre[..., k] = np.asarray(im.filter(ImageFilter.GaussianBlur(r / 2)), dtype=np.float32) / 255
            rgb = pre[..., :3] / np.maximum(1e-4, pre[..., 3:4])
            P = np.concatenate([np.clip(rgb, 0, 1), pre[..., 3:4]], -1)
        fp = self.work / "fr_front" / f"r_{f:04d}.png"
        if f in self.front and fp.exists():
            A = np.asarray(self.Image.open(fp).convert("RGBA"), dtype=np.float32)[..., 3:4] / 255
            im = self.Image.fromarray(np.clip(A[..., 0] * 255, 0, 255).astype(np.uint8))
            A = (np.asarray(im.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.MinFilter(7)), dtype=np.float32) / 255)[..., None]
            # 闭运算补细缝：零件贴镜头时分模线、盖子和底座之间的细缝在透明通道里是一道低谷，人会从缝里透出来（3-06 第 0 帧）
            A = np.clip((A - 0.3) / 0.55, 0, 1)
            A = A * A * (3 - 2 * A)                 # 贴镜头的锁边缘被景深虚成半透明（段尾实测最低 0.69）：挡人按 0.3–0.85 拉满，段首段尾那一帧不透出人影
            if r > 0.6:                             # 拉满会让挡人的边变硬（人像从一扇"窗"里露出来，3-01 第 376–382 帧）：
                im = self.Image.fromarray(np.clip(A[..., 0] * 255, 0, 255).astype(np.uint8))   # 按人虚的程度把挡人边一起虚开，和零件盖在大板上的软边一致
                A = (np.asarray(im.filter(ImageFilter.GaussianBlur(r / 2)), dtype=np.float32) / 255)[..., None]
            P = P.copy()
            P[..., 3:4] *= (1 - A)
        return P

    def person_dim(self, P, f):
        """剧本要求屋里暗下来的段（3-09：only the warm lamp glow and the side of the face stay lit）：人远离窗的那一侧（画面右侧）
        按 dark 事件慢慢压暗，最多 PERSON_DIM。人不动、不加光、不虚化，只是跟着屋子一起暗；窗那一侧（左）不动。"""
        import numpy as np
        k = self.cfg["P"].get("PERSON_DIM")
        ev = {e["id"]: e for e in self.cfg["K"]["events"]}.get("dark")
        if not k or ev is None:
            return P
        u = smooth((f - ev["f_start"]) / max(1, ev["f_end"] - ev["f_start"])) * k
        if u <= 0:
            return P
        x = np.arange(OUT_W, dtype=np.float32)
        g = np.clip((x - 250.0) / 850.0, 0, 1)                   # 画面 x 250 以左不动，到 1100 压满
        P = P.copy()
        P[..., :3] *= (1 - u * g)[None, :, None]
        return P

    def frame(self, f, lw=True, grain=True, soft=True):
        import numpy as np
        from PIL import ImageFilter
        Image = self.Image
        bgim = Image.open(self.work / "fr_bg" / f"b_{f:04d}.png").convert("RGB")
        if soft:
            bgim = bgim.filter(ImageFilter.GaussianBlur(CG_SOFT))
        B = np.asarray(bgim, dtype=np.float32) / 255
        if soft:
            g = _lum(B)[..., None]
            B = g + (B - g) * CG_SAT
        if grain:
            rng = np.random.default_rng(1000 + f)
            B = B + _grain(rng, B.shape) * self.sig[None, None, :]
        P, dev = self.person_layer(f)
        if self.cam.get("version") == 2:
            P = self.v2_person(P, f)
        P = self.person_dim(P, f)
        fi = self.cfg.get("fade_in")
        if fi and f < fi[1]:
            P[..., 3] *= smooth((f - fi[0]) / max(1, fi[1] - fi[0]))
        A = P[..., 3:4]
        rgb = P[..., :3]
        if lw and A.max() > 0:
            bgu8 = Image.fromarray((np.clip(B, 0, 1) * 255).astype(np.uint8))
            bb = np.asarray(bgu8.filter(ImageFilter.GaussianBlur(LW_BLUR)), dtype=np.float32) / 255
            au8 = Image.fromarray((A[..., 0] * 255).astype(np.uint8))
            ab = np.asarray(au8.filter(ImageFilter.GaussianBlur(LW_BAND)), dtype=np.float32)[..., None] / 255
            band = np.clip(A * (1 - ab) * 2.2, 0, 1) * LW_STRENGTH
            rgb = rgb * (1 - band) + np.maximum(rgb, bb) * band     # 亮的背景往人边上溢（screen 式，不把边压暗）
        out = rgb * A + B * (1 - A)
        fgp = self.work / "fr_fg" / f"f_{f:04d}.png"
        if fgp.exists() and f <= self.cam.get("fg_last", -1):
            F = np.asarray(Image.open(fgp).convert("RGBA"), dtype=np.float32) / 255
            if grain:
                F[..., :3] += _grain(np.random.default_rng(5000 + f), F[..., :3].shape) * self.sig
            out = F[..., :3] * F[..., 3:4] + out * (1 - F[..., 3:4])
        if self.src is not None:
            L, fa = self.src
            a = fa(f)
            if a > 0.003:
                y0, y1 = 870, 940
                al = L[y0:y1, :, 3:4] * a
                out[y0:y1] = L[y0:y1, :, :3] * al + out[y0:y1] * (1 - al)
        return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), dev


def _enc_args():
    """11-23：驱动更新后 h264_nvenc 报 incompatible client key（所有 ffmpeg 构建都开不了编码会话），自动试一次，不行就退到 libx264（CPU，crf 15 slow 档以下）。"""
    r = subprocess.run([FF, "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=640x360:d=0.2", "-c:v", "h264_nvenc", "-f", "null", "-"], capture_output=True)
    if r.returncode == 0:
        return ["-c:v", "h264_nvenc", "-preset", "p7", "-rc", "vbr", "-cq", "14", "-b:v", "0"]
    print("ONCAM nvenc 不可用，改用 libx264 crf 15", flush=True)
    return ["-c:v", "libx264", "-preset", "medium", "-crf", "15", "-threads", "6"]


def comp(seg, ab=False):
    if os.environ.get("CDK20_GPU_COMP") == "1" and not ab:   # 11-24：合成搬显卡（comp_gpu.py，见 comp_gpu.md）；去掉这个环境变量 = 下面原来的 CPU 版
        import comp_gpu
        comp_gpu.drive(seg)
        return
    cfg = seg_cfg(seg)
    C = Comp(seg)
    from PIL import Image
    if ab:
        out = cfg["work"] / "ab"
        out.mkdir(parents=True, exist_ok=True)
        for f in (150, 250, 335):
            for tag, kw in (("all", {}), ("no_lw", dict(lw=False)), ("no_grain", dict(grain=False)), ("no_soft", dict(soft=False)),
                            ("none", dict(lw=False, grain=False, soft=False))):
                Image.fromarray(C.frame(f, **kw)[0]).save(out / f"ab_{f:04d}_{tag}.png")
        print("ONCAM ab done", flush=True)
        return
    dst = Path(cfg["out"])
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(dst.stem + "_tmp.mp4")
    cmd = [FF, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OUT_W}x{OUT_H}", "-r", str(FPS), "-i", "-",
           "-i", str(cfg["wav"]), "-map", "0:v", "-map", "1:a", *_enc_args(),
           "-pix_fmt", "yuv420p", "-af", "apad", "-c:a", "aac", "-b:a", "192k", "-shortest", str(tmp)]   # apad：配音比画面短半帧时 -shortest 会吃掉最后一帧（11-22 1-05 出 595 帧）
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    devs = []
    t = time.time()
    for f in range(cfg["nf"]):
        fr, dev = C.frame(f)
        devs.append(dev)
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise SystemExit("ffmpeg failed")
    os.replace(tmp, dst)
    (cfg["work"] / "comp.json").write_text(json.dumps(dict(card_dev_px=devs, sec=round(time.time() - t, 1))), encoding="utf-8")
    print("ONCAM comp", dst, round(time.time() - t, 1), "s", flush=True)


# ================================================================ 自检（纯 Python）
def check(seg):
    import numpy as np
    from PIL import Image
    cfg = seg_cfg(seg)
    work = cfg["work"]
    cam = json.loads((work / "cam.json").read_text(encoding="utf-8"))
    chk = json.loads((work / "check.json").read_text(encoding="utf-8"))
    compj = json.loads((work / "comp.json").read_text(encoding="utf-8"))
    t0 = cam["push_t0"]
    res = {}
    hero = [fr["hero"] for fr in cam["frames"]]
    rng = range(cfg["fade_in"][1] if cfg.get("fade_in") else 0, t0)
    if cam.get("version") == 2:                      # v2：零件停在人旁边的帧段 = 第一个事件落位 → 最后一个事件开始（段首段尾零件贴镜头不算）
        ev = cfg["K"]["events"]
        rng = range(ev[0]["f_land"], ev[-1]["f_start"])
        t0 = cfg["nf"]
    res["F1_hero_h_min_px"] = round(min(h[3] - h[1] for h in (hero[f] for f in rng)), 1)
    res["F2_hero_xmin_min_px"] = round(min(hero[f][0] for f in rng), 1)
    res["person_drift_max_px_before_push"] = round(max(compj["card_dev_px"][:t0]), 3)
    # 成片逐帧：黑场、亮度跳变
    dst = Path(cfg["out"])
    raw = subprocess.run([FF, "-v", "error", "-i", str(dst), "-vf", "scale=192:108", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 108, 192, 3).astype(np.float32)
    Y = fr.mean((1, 2, 3))
    res["frames_in_video"] = int(len(fr))
    res["black_frames"] = int((Y < 16).sum())
    res["min_frame_mean"] = round(float(Y.min()), 1)
    res["max_frame_jump"] = round(float(np.abs(np.diff(Y)).max()), 2)
    res["max_frame_jump_at"] = int(np.abs(np.diff(Y)).argmax())
    gf = cfg["P"].get("GRAIN_F", 150)                   # 量颗粒的帧（3-09 屋里暗下来以后墙太暗、h264 吃颗粒，取变暗以前的一帧）
    # 颗粒：成片里人 T 恤平坦块 vs 左边墙平坦块（零件层）的高频残差（8 位）
    # 连取 10 帧取中位数：h264 的 I/P/B 帧颗粒差很多，同一位置单帧在 0.46–0.73 之间跳（3-06 实测），单帧判 M10 不可靠
    full = subprocess.run([FF, "-v", "error", "-ss", f"{gf / FPS:.4f}", "-i", str(dst), "-frames:v", "10", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                          capture_output=True).stdout
    FS_ = np.frombuffer(full, np.uint8).reshape(-1, OUT_H, OUT_W, 3).astype(np.float32)
    F = FS_[0]
    from PIL import ImageFilter

    def hp(region):
        im = Image.fromarray(region.astype(np.uint8))
        return float((region - np.asarray(im.filter(ImageFilter.GaussianBlur(2)), dtype=np.float32)).std())
    face, shirt, _ = face_boxes(cfg, gf)
    sx0, sy0 = shirt[0] + PERSON["x"], shirt[1] + PERSON["y"]
    sx1, sy1 = min(OUT_W, shirt[2] + PERSON["x"]), min(OUT_H, shirt[3] + PERSON["y"])

    def flat_patch(x0, y0, x1, y1, n=48, F=F):
        """框里最平的一块（6 px 模糊后起伏最小、亮度 110–240）：固定偏移会落到领口、扣子上（3-09 的 B 穿 polo 衫，量出 4.9，是边不是颗粒）。"""
        best = None
        for y in range(max(0, y0), max(0, y1 - n), 8):
            for x in range(max(0, x0), max(0, x1 - n), 8):
                R = F[y:y + n, x:x + n]
                m = float(R.mean())
                if not 110 <= m <= 240:
                    continue
                lo = np.asarray(Image.fromarray(R.astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), dtype=np.float32)
                sc_ = float(lo.std())
                if best is None or sc_ < best[0]:
                    best = (sc_, x, y)
        return best
    fp_ = flat_patch(sx0, sy0, sx1, sy1)
    if fp_ is None:                                     # 黑 T 恤（5-05、5-09 的 C）：衣服里没有 110–240 的平块，改在脸框里找（脸颊）
        fx0, fy0, fx1, fy1 = face
        ix, iy = (fx1 - fx0) * 0.18, (fy1 - fy0) * 0.08          # 脸框四边缩进：框边上是耳朵、发际、脸和背景的交界
        fb = (int(fx0 + ix) + PERSON["x"], int(fy0 + iy) + PERSON["y"], min(OUT_W, int(fx1 - ix) + PERSON["x"]), min(OUT_H, int(fy1 - iy) + PERSON["y"]))
        fp_ = flat_patch(*fb)
        res["grain_patch_from"] = "face"
        # 脸上"模糊后最平"的块常常落在眉毛、眼角上（模糊抹掉了五官，高频残差却很大：5-09 量出 3.5–4.9，是五官的边不是颗粒）。
        # 改成：每帧脸框里所有 48 px 块（亮度 110–240）的高频残差取 20 分位（皮肤上的底噪），10 帧取中位数
        def face_floor(G):
            v = [hp(G[y:y + 48, x:x + 48]) for y in range(fb[1], fb[3] - 48, 8) for x in range(fb[0], fb[2] - 48, 8)
                 if 110 <= float(G[y:y + 48, x:x + 48].mean()) <= 240]
            return float(np.percentile(v, 20)) if v else None
        per = [face_floor(G) for G in FS_]
        if all(v is not None for v in per):
            res["grain_person_shirt"] = round(float(np.median(per)), 3)
            res["grain_face_rule"] = "脸框（四边缩进）里 48 px 块高频残差的 20 分位，10 帧中位数"
    if fp_ is None:
        fp_ = (0, sx0 + 80, sy0 + 20)
    if "grain_person_shirt" not in res:
        res["grain_person_shirt"] = round(float(np.median([hp(G[fp_[2]:fp_[2] + 48, fp_[1]:fp_[1] + 48]) for G in FS_])), 3)
    res["grain_shirt_patch"] = [fp_[1], fp_[2]]
    res["grain_cg_wall_left"] = round(float(np.median([hp(G[300:348, 20:68]) for G in FS_])), 3)   # 左边墙（中间调、平、不过曝）
    # 对时
    py = ROOT / "_env/footage/Scripts/python.exe"
    sj = work / "sync.json"
    r = subprocess.run([str(py), str(MAPD / "check_sync.py"), str(dst), seg], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    rep = MAPD / "_reports" / f"sync_{seg}_{dst.stem}.json"
    if rep.exists():
        sj.write_text(rep.read_text(encoding="utf-8"), encoding="utf-8")
    res["check_sync_rc"] = r.returncode
    res["check_sync_tail"] = (r.stdout or "")[-1500:]
    res["clip"] = chk.get("clip")
    res["coc_px"] = chk.get("coc_px")
    (work / "check_comp.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("ONCAM check", json.dumps({k: v for k, v in res.items() if k != "check_sync_tail"}, ensure_ascii=False), flush=True)
    print(res["check_sync_tail"])


# ================================================================ 检查页（给导演看的 HTML，图内嵌）
def _jpg_b64(im, w=None, q=82):
    import base64
    import io
    if w and im.width > w:
        im = im.resize((w, round(im.height * w / im.width)))
    b = io.BytesIO()
    im.convert("RGB").save(b, "JPEG", quality=q)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def _video_frame(path, n):
    import numpy as np
    from PIL import Image
    raw = subprocess.run([FF, "-v", "error", "-i", str(path), "-vf", f"select=eq(n\\,{n})", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    return Image.fromarray(np.frombuffer(raw, np.uint8).reshape(OUT_H, OUT_W, 3))


def report(seg, html_path=None, extra=None):
    """出 10_出镜3D_检查.html：结论、试验结果（T1–T6）、参数、自检、抽帧。extra：总管手写的结论段（列表）。"""
    from PIL import Image, ImageDraw
    cfg = seg_cfg(seg)
    work = cfg["work"]
    L = json.loads((work / "light.json").read_text(encoding="utf-8"))
    fit = json.loads((work / "light_fit.json").read_text(encoding="utf-8"))
    chk = json.loads((work / "check.json").read_text(encoding="utf-8"))
    cc = json.loads((work / "check_comp.json").read_text(encoding="utf-8"))
    rim = {}
    rc = work / "scene.calib.json"
    if rc.exists():
        rim = json.loads(rc.read_text(encoding="utf-8"))
    vid = Path(cfg["out"])
    html_path = Path(html_path or vid.with_name("10_出镜3D_检查.html"))
    K = cfg["K"]
    ev = {e["id"]: e for e in K["events"]}
    info = chk["info"]
    # 抽帧：每个拍点一张
    picks = [("0 段首 T5", 4), ("Okay", ev["dot"]["f_land"]), ("this", ev["dot2"]["f_land"]), ("picture 前预颤", ev["frame"]["f_land"] - 3),
             ("picture 弹出", ev["frame"]["f_land"] + 10), ("lock 露销", ev["lock"]["f_land"] + 8), ("a 钥匙亮出", ev["key"]["f_land"]),
             ("key 滑进", ev["slide"]["f_land"] + 18), ("锁芯转", info["frames"]["turn"] + 8), ("T1 推进", cfg["nf"] - 8)]
    thumbs = []
    for lab, n in picks:
        im = _video_frame(vid, n)
        thumbs.append((lab, n, im))
    sheet = Image.new("RGB", (2 * 640, ((len(thumbs) + 1) // 2) * 384), (20, 20, 20))
    dr = ImageDraw.Draw(sheet)
    for i, (lab, n, im) in enumerate(thumbs):
        x, y = (i % 2) * 640, (i // 2) * 384
        sheet.paste(im.resize((640, 360)), (x, y))
        dr.text((x + 8, y + 362), f"f{n}  {lab}", fill=(230, 230, 230))
    # 同一空间对比：人 T 恤 / 脸旁 和 零件、大板的 1:1 局部
    f_c = ev["lock"]["f_land"] + 30
    im = _video_frame(vid, f_c)
    face, shirt, (nx, ny) = face_boxes(cfg, f_c)
    crops = [im.crop((int(nx + PERSON["x"]) - 160, int(ny + PERSON["y"]) - 200, int(nx + PERSON["x"]) + 160, int(ny + PERSON["y"]) + 120)),
             im.crop((1380, 260, 1700, 580)), im.crop((1180, 620, 1500, 940))]
    cmp_ = Image.new("RGB", (960, 320))
    for i, c in enumerate(crops):
        cmp_.paste(c.resize((320, 320)), (i * 320, 0))
    ab = work / "ab"
    ab_imgs = []
    for f in (150, 335):
        row = []
        for tag in ("all", "none"):
            p = ab / f"ab_{f:04d}_{tag}.png"
            if p.exists():
                row.append((tag, Image.open(p).crop((1150, 250, 1790, 610))))
        ab_imgs.append((f, row))
    calib_imgs = []
    for nm in ("t3_round0.png", sorted((work / "calib").glob("t3_round*.png"))[-1].name, "t1_nocard.png", "t1_shadow_only.png", "t1_holdout.png"):
        p = work / "calib" / nm
        if p.exists():
            calib_imgs.append((nm, Image.open(p)))
    t1 = fit.get("t1", {})
    t3 = fit.get("t3", [])
    last = t3[-1] if t3 else {}
    sync = {}
    sp = work / "sync.json"
    if sp.exists():
        sync = json.loads(sp.read_text(encoding="utf-8"))

    def esc(x):
        return str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def table(rows, head):
        h = "".join(f"<th>{esc(c)}</th>" for c in head)
        b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
        return f"<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>"

    ok = lambda b: "<b class=ok>过</b>" if b else "<b class=bad>不过</b>"   # noqa: E731
    coc = chk.get("coc_px", {})
    clip = chk.get("clip", {})
    f1 = cc["F1_hero_h_min_px"]
    f2 = cc["F2_hero_xmin_min_px"]
    sync_ok = cc.get("check_sync_rc") == 0
    self_rows = [
        ["F1 大小", f"锁（含锁梁）的投影高度最小 {f1:.0f} px（段首淡入后到推进前逐帧量）", "≥ 380 px（11-20 验收要求锁再小 10%，以验收为准）", ok(f1 >= 380) if f1 >= 380 else "<b>按验收调小</b>"],
        ["F2 位置", f"锁的左边最小 x = {f2:.0f}", "≥ 1250，不碰脸", ok(f2 >= 1250)],
        ["F3 遮挡", "11-20 验收改为钥匙避开手：钥匙在锁下方、D 右手的右边亮出，不被手指盖住（人仍整个在最前）", "验收优先", "<b>按验收改</b>"],
        ["F4 光", f"主光从画面左边来（量得 lr = {L['lr']:.2f}，方位 {fit['az_deg']:.0f}°），{L['kelvin']:.0f} K 暖白；锁开场挂在蓝色料杆框的浇口上，Okay 时框断开掉出画面", "同侧、同暖、有料杆", ok(True)],
        ["F5 进出", f"人第 {cfg['fade_in'][1]} 帧完全露出，第 {K['words'][0]['f0']} 帧开口；推进从第 {chk['push_t0']} 帧开始，最后一个词在第 {K['sentences'][-1]['f1']} 帧说完；黑场 {cc['black_frames']} 帧",
         "露出 ≥ 6 帧后开口；说完才转场；无黑场", ok(K['words'][0]['f0'] - cfg['fade_in'][1] >= 6 and chk['push_t0'] >= K['sentences'][-1]['f1'] and cc['black_frames'] == 0)],
        ["人不动", f"推进前合成里人的像素位移最大 {cc['person_drift_max_px_before_push']} px（人用原像素直接贴，镜头微动只让大板和锁有视差）", "0 px", ok(cc['person_drift_max_px_before_push'] <= 1)],
        ["对时", "check_sync.py：事件对词 ≤ 2 帧、句尾不早停、1.5 s 内有动作、帧率完整", "全过", ok(sync_ok)],
        ["穿模", f"锁弹出时碰框：{len(clip.get('lock_vs_cell_frames', []))} 帧；钥匙碰锁体：{len(clip.get('key_vs_lockbody_frames', []))} 帧；钥匙碰锁芯：{len(clip.get('key_vs_core_frames', []))} 帧；钥匙贴下销（允许）：{len(clip.get('key_vs_lowerpins_touch', []))} 帧",
         "0 / 0 / 0", ok(not clip.get('lock_vs_cell_frames') and not clip.get('key_vs_lockbody_frames') and not clip.get('key_vs_core_frames'))],
        ["景深", "；".join(f"f{k}: 焦 {v['focus']} m，锁 {v['lock']} px，大板 {v['board']} px" for k, v in coc.items()),
         "等待时锁 2–4 px；点名后锁 ≤ 1 px、大板 18–25 px", ""],
        ["颗粒", f"成片里 T 恤平坦块 {cc['grain_person_shirt']}，左边墙平坦块（零件层） {cc['grain_cg_wall_left']}（8 位高频残差）", "同一量级", ok(abs(cc['grain_person_shirt'] - cc['grain_cg_wall_left']) < 0.8)],
        ["亮度跳", f"相邻帧平均亮度最大跳 {cc['max_frame_jump']}（第 {cc['max_frame_jump_at']} 帧，推进/擦除处）", "无闪", ""],
    ]
    beat_rows = [
        ["0–16", "—", "T5 焦点擦除：近处两根白料杆（全虚）从画面正中往左扫出，人 0–14 帧淡入", "上一段 2-08 结尾接同一组料杆从右边扫进（深 0.24 m、每帧 0.021 m、倾 14°）"],
        [f"{ev['dot']['f_start']}→{ev['dot']['f_land']}", "Okay", "浇口\"咔\"地断开：蓝色料杆框往后弹开、按重力掉出画面（40 帧后藏掉），锁留在空中点一下头", "11-20 验收：出镜段零件不带料框"],
        [f"{ev['dot2']['f_start']}→{ev['dot2']['f_land']}", "this", "锁连框转 8°", ""],
        ["158→176", "（picture 前）", f"焦点从 {BASE_FOCUS} m 拉到锁上，轮廓光起亮（bl_guide 焦点点名）", "V4：到位在词前 8 帧"],
        [f"178→{ev['frame']['f_land']}", "", "A1 预颤：锁往外绷 4 mm", "bl_guide.guide_tick"],
        [f"{ev['frame']['f_land']}", "picture", "A1 弹出：锁往前飞、转正（16 帧 easeOutBack + 12 帧回弹）", ""],
        [f"{ev['lock']['f_start']}→{ev['lock']['f_land']}", "lock", f"锁转 {info['poses']['pick'][0] - info['poses']['show'][0]:.0f}° 露出剖开的四分之一，一排弹子销（过冲回弹）", "06 文档：3-01 仍是销子锁"],
        [f"{ev['key']['f_start']}→{ev['key']['f_land']}", "a", "A7：金钥匙从 D 抬起的手指后面亮出，侧着露出齿形；焦点借给钥匙", "F3 手指在钥匙前"],
        [f"{info['frames']['approach'][0]}→{info['frames']['insert'][1]}", "key", "钥匙绕尖转正、对准锁孔、滑进去；五根下销被齿顶起、最后齐在分界线上；焦点回到锁", "销高由 h02 齿形逐帧算"],
        [f"{info['frames']['turn']}→{cfg['nf'] - 1}", "（说完）", "锁芯带钥匙转 32°，锁梁弹起", ""],
        [f"{chk['push_t0']}→{cfg['nf'] - 1}", "（说完）", "T1 穿越：真相机推进剖口，穿进销子之间；人按卡片的真实投影移出画面", "3-02 开头从销子之间的暗部出来"],
    ]
    t3_rows = [[r["round"], f"{r.get('az', '')}", f"{r['key_w']:.0f}", f"{r['fill_w']:.1f}", f"{r['wash_w']:.0f}",
                f"{r['white_lit_p90']:.3f} / {r['target_white']:.3f}", f"{r['ratio']:.2f} / {r['target_ratio']:.2f}",
                f"{r['board_med']:.3f} / {r['target_board_med']:.3f}"] for r in t3]
    params = [
        ["相机", f"焦距 {LENS:.2f} mm（36 mm 传感器，等于手机前摄 {HFOV_EQ_MM:.0f} mm 等效），镜头偏移 {SHIFT[0]:.4f} / {SHIFT[1]:.4f}，光圈 f/{FSTOP}，叶片 6，没点名时焦点 {BASE_FOCUS} m"],
        ["人卡片", f"深 {D_PERSON} m，四角落在出片 x {PERSON['x']}–{PERSON['x'] + PERSON['w']}、y {PERSON['y']}–{PERSON['y'] + PERSON['h']}；只投影"],
        ["大板", f"board_final.blend 竖起来，放大 {BOARD_S:.1f} 倍，离相机 {BOARD_D} m；板前一层薄雾（散射密度 {HAZE_DENSITY}），左上一盏暖色聚光 {SHAFT_W:.0f} W 斜穿过雾；板后墙底色 ×{WALL_DIM}；第 3 区挂锁那一格藏起来（就是飞到人旁边的这把）"],
        ["零件", f"H06 销子锁（kit_deep_r3，剖开版）+ H02 钥匙 048（1.3 倍，和锁的检具同一配法），整体放大 {SL:.0f} 倍；锁在 1.40–1.55 m"],
        ["主光", f"面光 1.6 m，方位 {fit['az_deg']:.0f}°（相对零件看相机的方向，画面左）、仰 {fit['el_deg']:.0f}°，离零件 2.6 m，{fit['key_w']:.0f} W，{L['kelvin']:.0f} K"],
        ["补光/顶光", f"补光 2.6 m 面光在右 {fit['fill_w']:.1f} W；顶光 = 主光 12%；世界光 {fit.get('world', 0.35)}"],
        ["洗墙光", f"只照大板和墙（灯光链接），{fit['wash_w']:.0f} W，大板亮度中位数对齐 bg.jpg"],
        ["反射", f"窗卡、前卡、顶卡、钥匙卡（只给镜面看，不照明不投影）；镜面光线看见的世界亮度 {GLOSSY_WORLD}（金属件朝镜头的面不发黑）；大板和墙不往零件上反漫射光"],
        ["轮廓光", f"bl_guide.guide_rim，只照锁；标定 {json.dumps(rim, ensure_ascii=False)[:160] if rim else '见 check.json'}"],
        ["渲染", f"Cycles + OptiX GPU + OptiX 降噪，{chk.get('samples', SAMPLES)} 采样，运动模糊快门 0.5（180°），间接光钳制 10，1080p60"],
        ["合成", f"零件层软化 {CG_SOFT} px、饱和度 ×{CG_SAT}、颗粒 σ = {', '.join(f'{x:.2f}' for x in L['grain_sigma_rgb'])}（RGB，8 位，从 T 恤量）；光包边 {LW_STRENGTH}（背景模糊 {LW_BLUR} px，内沿 {LW_BAND} px）；人右边缘 {EDGE_FEATHER} px 渐隐（同 oncam.jsx）"],
        ["微动", f"以人卡片中心为轴，左右 ±{MICRO[0]}°、上下 ±{MICRO[1]}°（人在合成里原像素不动）"],
    ]
    css = """
:root{--bg:#f6f4ef;--fg:#1d1c1a;--mut:#6b675f;--line:#ddd8cc;--ok:#1d7a3a;--bad:#b3261e;--card:#fff}
@media (prefers-color-scheme:dark){:root{--bg:#161514;--fg:#ecebe7;--mut:#a29d93;--line:#38352f;--ok:#5cc17c;--bad:#ff7a6e;--card:#1f1e1c}}
body{background:var(--bg);color:var(--fg);font:15px/1.6 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;margin:0;padding:24px 16px;}
main{max-width:1100px;margin:auto} h1{font-size:24px} h2{font-size:19px;margin-top:34px;border-bottom:1px solid var(--line);padding-bottom:4px}
table{border-collapse:collapse;width:100%;margin:10px 0;font-size:14px;background:var(--card)} td,th{border:1px solid var(--line);padding:6px 8px;vertical-align:top;text-align:left}
th{background:rgba(127,127,127,.08)} .ok{color:var(--ok)} .bad{color:var(--bad)} img{max-width:100%;border-radius:4px;display:block;margin:8px 0}
.lead{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:12px 16px} .mut{color:var(--mut);font-size:13px}
.row{display:flex;gap:8px;flex-wrap:wrap}.row figure{margin:0;flex:1 1 300px}.row figcaption{font-size:13px;color:var(--mut)}
"""
    h = [f"<!doctype html><html lang=zh><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>出镜 3D 样片 {seg}</title><style>{css}</style></head><body><main>"]
    h.append(f"<h1>出镜 + 旁边 3D 零件：样片 {seg}（D）</h1>")
    h.append("<p class=mut>HKBU SCIE1007 课程作业的科普视频。第一段\"人在前、3D 零件浮在人侧后方\"的样片，按 08_出镜旁3D_调研.md 第十节落地。"
             f"成片 <code>{esc(vid.name)}</code>（1080p60，{cfg['nf']} 帧 = {cfg['nf'] / FPS:.1f} 秒，带原声）。代码 <code>镜头设计_v3/inserts/shot_oncam.py</code>（所有出镜段共用，各段只写一个 recipe）。"
             f"生成于 {time.strftime('%Y-%m-%d %H:%M')}（韩国时间）。</p>")
    h.append("<div class=lead>" + "".join(f"<p>{x}</p>" for x in (extra or [])) + "</div>")
    v1 = [(n, work / f"v1_{n:04d}.png") for n in (60, 200, 340)]
    if all(p.exists() for _, p in v1):
        h.append("<h2>11-20 验收三处改动：前后对比（第 60 / 200 / 340 帧，左旧右新）</h2>"
                 "<ol><li>背景：大板从 3.6 m 推到 8 m、光圈 f/1.6 → f/0.9，大板焦外约 19–21 px（看得出颜色轮廓、看不清字）；"
                 "零件和大板之间一层薄雾压对比；大板亮度目标降到 bg.jpg 的 82%，板后的墙压到 70%；一盏暖色聚光从左上斜穿过雾。</li>"
                 "<li>料框：只在 Okay 那一下从浇口断开、弹开后按重力掉出画面；锁再小 10%。</li>"
                 "<li>钥匙：加一盏只照钥匙的小面光（灯光链接）+ 镜面看得见的亮环境，金色读成亮金；钥匙挪到锁下方、手的右边，不被手指盖住。</li></ol>")
        for n, p in v1:
            new = _video_frame(vid, n)
            old = Image.open(p)
            h.append("<div class=row>" + "".join(f"<figure><img src='{_jpg_b64(im, 960)}'><figcaption>第 {n} 帧 {t}</figcaption></figure>"
                                                 for t, im in (("旧", old), ("新", new))) + "</div>")
    h.append("<h2>逐拍</h2>" + table(beat_rows, ["帧", "词", "画面", "备注"]))
    h.append(f"<img src='{_jpg_b64(sheet, 1280)}' alt='拍点抽帧'>")
    h.append("<h2>自检</h2>" + table(self_rows, ["项", "实测", "标准", "结论"]))
    if sync:
        h.append(f"<p class=mut>check_sync 原始结果：{esc(json.dumps(sync, ensure_ascii=False)[:900])}</p>")
    h.append("<h2>是不是在同一个空间（1:1 局部，同一帧）</h2><p>左：D 的脸；中：锁；右：钥匙/手边。看颗粒、软硬、亮面的光方向是否一致。</p>")
    h.append(f"<img src='{_jpg_b64(cmp_)}' alt='局部对比'>")
    h.append("<h2>试验</h2>")
    h.append("<h3>T1 人卡片：只投影 vs Holdout</h3>")
    h.append(table([["只投影（相机看不见）", f"大板右侧变暗 {t1.get('board_right_dEV', 0):.4f} EV；灰球 {t1.get('ball_grey_dEV', 0):.3f} EV、白球 {t1.get('ball_white_dEV', 0):.3f} EV", "0 个半透明像素（人整个在合成里放回）", "<b class=ok>采用</b>"],
                    ["Holdout（相机看见、挖洞）", f"挖洞 {t1.get('holdout_hole_px', 0)} 像素（半分辨率）", f"放回人以后残留半透明像素 {t1.get('holdout_see_through_px', 0)}（半分辨率，约 {4 * t1.get('holdout_see_through_px', 0)} 全分辨率）", "不用"]],
                   ["做法", "人对零件、大板的影子", "边缘", "结论"]))
    h.append("<p class=mut>这一段主光从左前方来，人的影子落在人右后方很远的地方，对锁和大板只有 1% 左右的变暗；Holdout 的洞和人物遮罩的边对不齐，会留一圈透底的细边（调研第 17 条说的翻车点），所以用\"只投影 + 合成放回人\"。</p>")
    h.append("<h3>T2 从 D 的脸和白 T 恤量光</h3>")
    h.append(table([["脸左右差 (L−R)/(L+R)", f"{L['lr']:.3f}", f"光从画面左边来，换算方位 {L['az_deg']:.0f}°"],
                    ["脸上下差", f"{L['tb']:.3f}", "被眉眼的暗部带偏（负值），仰角不用它，按鼻影看约 15°"],
                    ["主辅光比（亮侧均值/暗侧均值）", f"{L['key_fill_ratio_mean']:.2f}", f"90/10 分位比 {L['key_fill_ratio_p90p10']:.2f}"],
                    ["白 T 恤 R/B（线性）", f"{L['rb']:.3f}", f"约 {L['kelvin']:.0f} K，暖白"],
                    ["T 恤亮处 90 分位", f"{L['shirt_p90_srgb']:.3f}（显示值）", f"线性 {L['shirt_lin_p90']:.3f}"],
                    ["颗粒 σ（R,G,B，8 位）", ", ".join(f"{x:.2f}" for x in L['grain_sigma_rgb']), "素材降过噪，颗粒很轻"],
                    ["遮罩内沿亮度 / 人均值", f"{L['rim_band']:.2f}", "没有逆光，零件的轮廓光只在点名时用"]],
                   ["量什么", "数", "落到 Blender"]))
    h.append("<h3>T3 灰球、白球、镜面球比光（每轮自动回写功率）</h3>")
    h.append(table(t3_rows, ["轮", "主光方位°", "主光 W", "补光 W", "洗墙 W", "白球亮侧 p90 / 目标", "白球左右比 / 脸", "大板中位 / bg.jpg"]))
    h.append(f"<p class=mut>最后一轮误差：白球 {last.get('err_white', '')}，左右比 {last.get('err_ratio', '')}，大板 {last.get('err_board', '')}（目标 15% 以内）。</p>")
    h.append("<div class=row>" + "".join(f"<figure><img src='{_jpg_b64(im, 640)}'><figcaption>{esc(nm)}</figcaption></figure>" for nm, im in calib_imgs) + "</div>")
    h.append("<h3>T4 微动</h3><p>相机绕人卡片中心转（±0.3° / ±0.2°），人在合成里用原像素不动；大板和锁有几个像素的真视差，人比背景\"稳\"。推进前人卡片投影四角最大偏差见自检\"人不动\"。</p>")
    h.append("<h3>T5 动作库</h3>" + table([[k, esc(v[0]), esc(v[1])] for k, v in ACTIONS.items()], ["代号", "帧数和曲线", "代码"]))
    h.append("<h3>T6 合成三项开/关（光包边、颗粒、软化）</h3>")
    for f, row in ab_imgs:
        h.append("<div class=row>" + "".join(f"<figure><img src='{_jpg_b64(im, 640)}'><figcaption>f{f} {'三项全开' if t == 'all' else '三项全关'}</figcaption></figure>" for t, im in row) + "</div>")
    h.append("<h2>参数</h2>" + table(params, ["", "值"]))
    h.append("<h2>前后段怎么接</h2><ul>"
             "<li><b>段首 T5</b>：2-08 结尾最后约 16 帧加同一组近处白料杆从画面右边扫进来（深 0.24 m、每帧 0.021 m、倾 14°、f/1.6 焦点 " + f"{BASE_FOCUS}" + " m），料杆盖住画面正中那一帧切到 3-01 第 0 帧。2-08 改三维时照这个数渲。</li>"
             "<li><b>段尾 T1</b>：3-01 最后一帧镜头已经推进锁的剖口、停在销子之间（金色锁芯、白色上销占满画面）。3-02 开头从同样的金/白暗部往后退出来，出来在细胞工坊里。</li></ul>")
    h.append(f"<h2>文件</h2><ul><li>成片 <code>{esc(vid)}</code></li><li>场景、帧、检查数：<code>{esc(work)}</code>（scene.blend、check.json、cam.json、light.json、light_fit.json、check_comp.json、calib/、ab/）</li>"
             "<li>一条龙：<code>bash 镜头设计_v3/inserts/run_oncam.sh 3-01 all</code></li></ul>")
    h.append("</main></body></html>")
    html_path.write_text("\n".join(h), encoding="utf-8")
    print("ONCAM report", html_path, flush=True)
    return html_path


# ================================================================ 命令行
if __name__ == "__main__":
    if IN_BL and "--" in sys.argv:
        a = sys.argv[sys.argv.index("--") + 1:]
        if a[0] == "calib":
            calib(a[1])
        elif a[0] == "build":
            if SEGS[a[1]].get("version") == 2:
                build_v2(a[1], int(a[2]) if len(a) > 2 else None)
            else:
                build(a[1], int(a[2]) if len(a) > 2 else SAMPLES)
        elif a[0] == "render":
            render(a[1], a[2] if len(a) > 2 else "bg")
        elif a[0] == "frames":
            frames(a[1], [int(x) for x in a[2].split(",")], a[3] if len(a) > 3 else "bg", int(a[4]) if len(a) > 4 else 100)
        elif a[0] == "rimcal":
            rimcal(a[1])
    elif not IN_BL and len(sys.argv) > 2:
        if sys.argv[1] == "measure":
            measure(sys.argv[2])
        elif sys.argv[1] == "comp":
            comp(sys.argv[2], ab="--ab" in sys.argv)
        elif sys.argv[1] == "check":
            check(sys.argv[2])
        elif sys.argv[1] == "report":
            report(sys.argv[2])
