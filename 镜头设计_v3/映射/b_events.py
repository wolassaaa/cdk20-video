"""HKBU SCIE1007 课程作业的科普视频：B 档第一批 7 页的事件表，一处写全，生成 映射/events/<段>.json。

改动作时只改这里，再跑：python 镜头设计_v3/映射/b_events.py [段 ...]（不给段就全写），然后 b_page.py render <段>。
旧的 v9 说明书页事件表留在 events/_v9/（resolve 不读子文件夹）。
每行：(id, verb, 词, off, lead, until, 意思, 引导目标)
  until："w:词" 到那个词说完；"s" 到句尾；"d:N" 落点后 N 帧；None 在落点结束。
  引导目标：页面上 <Layer id=…> 的名字，None 不引导。
lead 的习惯（gsapFrame.RULE）：落位动作 13（预备 6 + back.out 第一次到位 7），计数 36–60，淡入 10。
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

PAGES = {
    "5-10": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 5-10（Remotion + SVG + GSAP，页面 btier/B510.jsx）。路上三站，048 插头跳到第三站（big step），"
             "第三站的培养皿变成 Huh7 皿；三天、048 投进皿里；皿里细胞插满 CDK20 小插座；信号表掉一半；剂量条滚到 210 nM。"
             "HEK293 皿从右边进来，剂量条长到 1,700 nM；八段 Huh7 长度铺满 HEK 的条（roughly eight times）。",
        zone=5, trans_in="T5 socket（上一段 W4 是 A 段）", trans_out="T2 甩镜往左（下一段 6-01 是 B 页）",
        ev=[
            ("road", "grow", "then#1", 0, 9, "w:step#1", "Then：路和三站从料杆上长出来（前两站打勾）", None),
            ("hop", "move", "step#1", 0, 30, "w:step#1", "big step：048 插头从第二站一大步跳到第三站", None),
            ("cells", "grow", "living#1", 0, 7, "s", "living cells：第三站的培养皿长出来，里面是活细胞", "huh7"),
            ("shift", "move", "after#1", 0, 24, "w:days#1", "After：路往左滑走，第三站的皿移到画面中间当 Huh7 皿", None),
            ("cal", "appear", "three#1", 0, 16, "w:days#1", "three days：日历进来，翻三下，落在 days", None),
            ("dose", "move", "048#1", 0, 36, "w:048#1", "048：048 插头插进皿里", "plug"),
            ("huh7", "appear", "huh7#1", 0, 10, "w:cells#2", "Huh7：皿上方标 Huh7", None),
            ("liver", "appear", "liver#1", 0, 0, "w:cells#2", "liver cancer cells：手写批注", None),
            ("packed", "grow", "packed#1", 0, 7, "w:cdk20#1", "packed with CDK20：皿里的细胞一个个插满小插座", None),
            ("lost", "appear", "lost#1", 0, 13, "w:their#1", "lost：信号表开始往下掉，细胞一半变灰", "gauge"),
            ("half", "move", "half#1", 0, 0, "w:signal#1", "half：信号表停在一半，标 half；living-cell signal 手写", None),
            ("d210", "grow", "210#1", 0, 60, "w:nanomolar#1", "at about 210：剂量条长出来，数字轮停在 210", "bars"),
            ("nm", "appear", "nanomolar#1", 0, 8, "s", "nanomolar：数字后面刻上 nM", None),
            ("hek", "move", "comparison#1", 0, 30, "w:cells#3", "Comparison cells：Huh7 一组往左让，HEK293 皿从右边滑进来", "hek"),
            ("hekl", "appear", "hek293#1", 0, 10, "w:hek293#1", "HEK293：标 HEK293", None),
            ("hneed", "move", "needed#1", 0, 36, "w:about#2", "needed：048 插进 HEK 皿，它的信号表也掉到一半", None),
            ("d1700", "grow", "1,700#1", 0, 90, "s", "about 1,700：HEK 的剂量条长到 1,700", "bars"),
            ("eight", "grow", "eight#1", 0, 30, "w:times#1", "eight：八段 Huh7 的长度依次铺满 HEK 的条", None),
            ("more", "appear", "times#1", 0, 0, "s", "times more：手写 ≈ 8×", None),
        ]),
    "3-05": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 3-05（页面 btier/B305.jsx）。Why this lock：CDK20 插座加红色问号；香港地图（Hong Kong team）；"
             "52 个样本孔，36 个变蓝，计数停在 36，of 52；玻璃肝；肿瘤和旁边正常组织两根条，肿瘤高；两块牌子 later-stage tumours、shorter survival；"
             "最后小插座的旋钮往下拧，肝癌细胞的分裂节拍从 60 帧变 120 帧（灯一直亮，不是药堵住）。",
        zone=3, trans_in="T5 socket（上一段 3-04 是 A 段插座）", trans_out="T5 runner（下一段 3-06 是出镜段，段首是料杆擦除）",
        ev=[
            ("sock", "grow", "why#1", 0, 9, "w:lock#1", "Why this lock：CDK20 插座落位", None),
            ("q", "appear", "lock#1", 0, 0, "s", "lock?：红色问号手写", None),
            ("rem", "move", "remember#1", 0, 13, "w:the#1", "Remember：插座缩到左边让位", None),
            ("hk", "move", "hong#1", 0, 13, "w:team#1", "Hong Kong team：香港地图滑进来，标 Hong Kong team", "hk"),
            ("tray", "move", "in#1", 0, 24, "w:36#1", "In：样本盘从右边滑进来，地图和插座出去", None),
            ("n36", "grow", "36#1", 0, 34, "w:of#1", "36：样本孔一个个变蓝，计数停在 36", None),
            ("of52", "appear", "52#1", 0, 8, "w:52#1", "of 52：刻上 of 52，剩下的孔亮一下", None),
            ("liver", "grow", "liver#1", 0, 7, "w:tumours#1", "liver tumours：玻璃肝长出来", "liver"),
            ("hi", "grow", "higher#1", 0, 60, "w:than#1", "CDK20 was higher：肿瘤那根蓝条长高", "bars"),
            ("near", "grow", "nearby#1", 0, 13, "s", "nearby non-tumour tissue：旁边正常组织的灰条（矮）", None),
            ("high", "appear", "high#1", 0, 6, "w:levels#1", "High levels：蓝条亮一下", None),
            ("late", "eject", "later-stage#1", 0, 13, "w:tumours#2", "later-stage tumours：第一块牌子从料杆上弹下来", "plaques"),
            ("surv", "eject", "shorter#1", 0, 7, "s", "shorter survival：第二块牌子", None),
            ("clear", "move", "and#2", 0, 20, "w:turning#1", "And：前面的东西往左滑走", None),
            ("knob", "grow", "turning#1", 0, 13, "w:cdk20#2", "turning CDK20：小插座和旋钮进来，右边肝癌细胞照常分裂（60 帧一拍）", None),
            ("down", "move", "down#1", 0, 30, "w:down#1", "down：旋钮往下拧", "knob"),
            ("cellsL", "appear", "liver#2", 0, 10, "w:cells#1", "liver cancer cells：标 liver cancer cells", "cells"),
            ("slow", "move", "slowed#1", 0, 0, "s", "slowed their growth：分裂节拍变 120 帧，手写 slowed", None),
        ]),
    "5-01": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 5-01（页面 btier/B501.jsx，第 5 章第一页，T6 光扫）。moment of truth：CDK20 插座落位；"
             "seven real molecules：料杆上挂着七个金插头（001 和 A–F，字母只是画面代号）；real lab：烧瓶；Do any grab：001 飞到插座口前停住，红色问号；"
             "Kd：十个小插座，烧瓶里的插头一个个飞进去，第五个插上时是 half；Lower means tighter：Kd 刻度往下，插上的五个压紧。",
        zone=5, trans_in="T5 runner（上一段 4-11+12 是出镜段）+ T6 光扫（第 5 章第一页）", trans_out="T5 runner（下一段 5-02 是出镜段）",
        ev=[
            ("sweep", "appear", "so#1", 0, 9, "d:30", "So：T6 光扫过", None),
            ("sock", "grow", "moment#1", 0, 13, "w:truth#1", "the moment of truth：CDK20 插座落位，灯一闪", None),
            ("rack", "grow", "seven#1", 0, 13, "w:molecules#1", "Seven real molecules：插座让到右边，料杆上七个金插头依次落位", "rack"),
            ("made", "appear", "made#1", 0, 0, "w:lab#1", "made in a real lab：手写批注", None),
            ("flask", "grow", "lab#1", 0, 13, "s", "lab：烧瓶长出来", "flask"),
            ("any", "appear", "any#1", 0, 6, "w:actually#1", "any：七个插头挨个抖一下", None),
            ("try", "move", "grab#1", 0, 90, "w:cdk20#1", "grab：001 从料杆上掰下来，飞到插座口前停住", "sock"),
            ("q", "appear", "cdk20#1", 0, 0, "s", "CDK20?：红色问号", None),
            ("clear", "move", "grip#1", 0, 10, "w:is#1", "Grip：插座和料杆出去，烧瓶移到左边", None),
            ("kd", "appear", "kd#1", 0, 10, "w:roughly#1", "Kd：刻 Kd 和刻度", None),
            ("grid", "grow", "roughly#1", 0, 13, "w:how#1", "roughly：十个小插座依次落位", "grid"),
            ("much", "grow", "much#1", 0, 13, "w:molecule#1", "how much molecule：烧瓶抖一下，瓶口冒出插头", "flask"),
            ("fly", "move", "half#1", 0, 80, "w:the#2", "it takes to grab：插头一个个飞进小插座", None),
            ("half", "snap", "half#1", 0, 0, "w:protein#1", "half：第五个插上（十个里五个），T7 一抖，手写 half", "grid"),
            ("lower", "move", "lower#1", 0, 13, "w:means#1", "Lower：Kd 刻度上的标往下走", None),
            ("tight", "snap", "tighter#1", 0, 6, "s", "tighter：插上的五个压紧一下，手写 lower = tighter", None),
        ]),
    "5-03": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 5-03（页面 btier/B503.jsx）。Kd 横尺（左低右高，越往左越紧）：001 的真分子（我们的重对接图）和金插头，"
             "插头沿尺走到 9.2，数字轮停在 9.2 µM；另外六个插头在右上角排开，30 的立柱升起，六个都落在 30 右边，变灰往下沉（much weaker）；"
             "wild part：尺往左滑走，日历落下（T7）；30 days：数字轮停在 30；从 PandaOmics 芯片（选靶）弹出一个小插座，沿路走到 001（第一个确认的命中），打勾。",
        zone=5, trans_in="T5 runner（上一段 5-02 是出镜段）", trans_out="T5 socket（下一段 5-04 是 A 段插座）",
        ev=[
            ("mol", "appear", "001's#1", 0, 9, "w:kd#1", "001's：001 的分子和金插头出现", None),
            ("p001", "move", "9.2#1", 0, 50, "w:9.2#1", "Kd 9.2：插头沿尺走到 9.2，数字轮停在 9.2", "p001"),
            ("um", "appear", "micromolar#1", 0, 8, "s", "micromolar：刻 µM", None),
            ("six", "grow", "six#1", 0, 13, "s", "The other six：右上角六个插头依次落位", "six"),
            ("post", "grow", "above#1", 0, 13, "w:30#1", "above 30：30 的立柱升起", None),
            ("drop", "move", "30#1", 0, 13, "s", "30：六个插头落到尺上 30 右边", None),
            ("weak", "move", "weaker#1", 0, 13, "s", "Much weaker：六个变灰、往下沉，手写 much weaker", None),
            ("clear", "move", "and#1", 0, 6, "w:here's#1", "And：尺和插头往左滑走，001 留下", None),
            ("wild", "snap", "wild#1", 0, 13, "s", "wild part：日历落下，T7 一抖", "cal"),
            ("clock", "appear", "clock#1", 0, 6, "w:read#1", "The clock：日历翻一下", None),
            ("n30", "grow", "30#2", 0, 60, "w:days#1", "30 days：数字轮停在 30，刻 days", None),
            ("pick", "eject", "picking#1", 0, 13, "w:the#4", "picking：PandaOmics 芯片弹出一个小插座", None),
            ("target", "appear", "target#1", 0, 13, "w:target#1", "the target：标 target", "road"),
            ("travel", "move", "hit#1", 0, 110, "s", "to this first confirmed hit：小插座沿路走到 001", None),
            ("hit", "snap", "hit#1", 0, 0, "s", "hit：001 打勾，标 first confirmed hit", "hit"),
        ]),
    "5-08": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 5-08（页面 btier/B508.jsx）。料杆上一排金插头，一个抬起来，变成 048（标 048）；"
             "grabbed：048 飞到 Kd 横尺上 0.6 处（001 在 9.2）；fifteen times：0 到 9.2 之间铺出 15 段，每段一个 048 的距离；"
             "enzyme test：十个小插座（灯亮 = 酶在干活）；001 needed more than 6,000：对数表盘的针一路转到 6,000 以外；"
             "048 needed just 33.4：新针只转到 33.4，十个里五个插座被 048 卡死（拧 90°、红卡扣、灯灭），T7 一抖。",
        zone=5, trans_in="T2 甩进（上一段 5-07 是 B 页）", trans_out="T5 runner（下一段 5-09 是出镜段）",
        ev=[
            ("row", "grow", "and#1", 0, 9, "w:them#1", "And：料杆上一排金插头和 Kd 横尺（001 在 9.2）", None),
            ("one", "move", "one#1", 0, 13, "w:them#1", "one of them：一个插头抬起来", None),
            ("k48", "morph", "048#1", 0, 6, "w:048#1", "048：抬起的插头刻上 048，标 048", "row"),
            ("grab", "move", "grabbed#1", 0, 40, "w:about#1", "grabbed：048 飞到 Kd 横尺 0.6 处", "rail"),
            ("fif", "grow", "fifteen#1", 0, 60, "w:times#1", "fifteen times：0 到 9.2 之间铺出 15 段", None),
            ("tig", "appear", "tighter#1", 0, 0, "s", "tighter：手写 ≈ 15× tighter", None),
            ("clear", "move", "then#1", 0, 6, "w:the#1", "Then：尺和料杆往左滑走", None),
            ("grid", "grow", "enzyme#1", 0, 7, "w:test#1", "enzyme：十个小插座依次落位，灯亮", "grid"),
            ("lab", "appear", "test#1", 0, 10, "s", "test：标 enzyme test", None),
            ("dial", "grow", "remember#1", 0, 13, "w:001#1", "Remember：对数表盘落位", None),
            ("p001", "appear", "001#1", 0, 13, "w:needed#1", "001：001 插头靠到表盘边", None),
            ("sweep", "move", "6,000#1", 0, 83, "w:6,000#1", "needed more than 6,000：针一路转到 6,000 以外，数字轮停在 6,000", "dial"),
            ("nm", "appear", "nanomolar#1", 0, 8, "s", "nanomolar：刻 nM", None),
            ("p48", "appear", "048#2", 0, 13, "w:048#2", "048：001 的针变灰留着，048 插头换上来", None),
            ("need", "move", "33.4#1", 0, 52, "s", "needed just 33.4：新针只转一点，停在 33.4", None),
            ("clamp", "snap", "33.4#1", 0, 0, "s", "33.4：十个里五个插座被卡死，灯灭，T7 一抖", "grid"),
        ]),
    "8-03": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 8-03（页面 btier/B803.jsx）。our second?：目标牌 2 落位加红色问号；"
             "These methods：目标牌缩到左上角，三块芯片（PandaOmics、Chemistry42、AlphaFold）依次落位，候选插头在下面的料杆上快速走过（fast）；"
             "Screening by the millions：一大盘料珠，手写 millions；became thirteen：十三个插头掉进盘里，数字轮停在 13，标 molecules made；"
             "a road measured in years：一条长路带刻度，手写 years；first hit in 30 days：001 落在路的起点附近，标 30 days；"
             "round two made the key turn：048 插进小插座、拧 90°、红卡扣、灯灭（T7），左上角目标牌 2 打勾。",
        zone=8, trans_in="T2 甩进（上一段 8-02 是 B 页）", trans_out="T5 runner（下一段 8-04–07 是出镜段）",
        ev=[
            ("goal", "grow", "second#1", 0, 7, "s", "our second：目标牌 2 落位", "goal"),
            ("q", "appear", "second#1", 0, 0, "s", "second?：红色问号", None),
            ("badge", "move", "these#1", 0, 13, "w:methods#1", "These：目标牌缩到左上角", None),
            ("chips", "grow", "methods#1", 0, 13, "w:helped#1", "methods：三块芯片依次落位", "chips"),
            ("conv", "move", "assess#1", 0, 20, "w:candidates#1", "assess candidates：候选插头在料杆上走过芯片", None),
            ("fast", "appear", "fast#1", 0, 0, "s", "fast：手写 fast", None),
            ("pile", "grow", "screening#1", 0, 13, "w:by#1", "Screening：芯片出去，一大盘料珠长出来", None),
            ("mil", "appear", "millions#1", 0, 0, "w:became#1", "millions：手写 millions", None),
            ("n13", "grow", "thirteen#1", 0, 52, "w:molecules#1", "became thirteen：十三个插头掉进盘里，数字轮停在 13", "tray"),
            ("made", "appear", "made#1", 0, 10, "s", "molecules made：标 molecules made", None),
            ("road", "grow", "and#2", 0, 6, "w:road#1", "And on a road：料珠和盘出去，一条长路带刻度", None),
            ("years", "appear", "years#1", 0, 0, "w:years#1", "years：手写 years", None),
            ("hit", "move", "hit#1", 0, 7, "w:came#1", "the first hit：001 落在路的起点附近", "road"),
            ("d30", "appear", "30#1", 0, 10, "w:days#1", "30 days：标 30 days", None),
            ("r2", "move", "made#2", 0, 50, "w:key#1", "round two made：048 飞进小插座口", "socket"),
            ("turn", "snap", "turn#1", 0, 12, "s", "the key turn：048 拧 90°、红卡扣、灯灭（T7），目标牌 2 打勾", None),
        ]),
    "4-03": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 4-03（页面 btier/B403.jsx）。左边 AlphaFold 预测模型（按可信度上色，红色是低可信度的尾巴），"
             "look closer：放大镜扣到尾巴上（放大镜里是同一张贴图按原图分辨率显示，不做位图推拉）；右边 CDK20 插座正面，"
             "One end：插座边上长出一串红珠子（尾巴），floppy 时晃；low confidence：标；in the model it lay across the keyhole：尾巴横搭过插孔；"
             "one building block sitting inside the ATP pocket：一颗珠子落进孔里，标 ATP pocket；cut keys for a blocked door：左下冲出三个金插头，"
             "一个飞向插孔被尾巴挡回来（T7）。",
        zone=4, trans_in="T2 甩进（上一段 4-02 是 B 页）", trans_out="T5 runner（下一段 4-04+05 是出镜段）",
        ev=[
            ("af", "appear", "but#1", 0, 9, "w:look#1", "But：预测模型", None),
            ("closer", "move", "closer#1", 0, 13, "s", "look closer：放大镜扣到红色尾巴上", "af"),
            ("sock", "move", "one#1", 0, 7, "w:end#1", "One：插座正面从右边滑进来", None),
            ("tail", "grow", "end#1", 0, 13, "w:protein#1", "One end of the protein：插座边上长出一串红珠子", "tail"),
            ("floppy", "move", "floppy#1", 0, 6, "w:tail#1", "a floppy tail：尾巴晃", None),
            ("low", "appear", "confidence#1", 0, 10, "s", "really low confidence：标 low confidence", None),
            ("model", "appear", "model#1", 0, 10, "w:model#1", "in the model：放大镜里的尾巴亮一下", None),
            ("lay", "move", "keyhole#1", 0, 46, "w:keyhole#1", "lay across the keyhole：尾巴横搭过插孔", "tail"),
            ("block", "appear", "block#1", 0, 13, "w:block#1", "one building block：一颗珠子鼓一下", None),
            ("inside", "snap", "inside#1", 0, 28, "w:the#4", "sitting inside：这颗珠子落进孔里", None),
            ("atp", "appear", "pocket#1", 0, 10, "s", "the ATP pocket：标 ATP pocket", "socket"),
            ("trust", "move", "trust#1", 0, 6, "w:blindly#1", "Trust it blindly：放大镜收起", None),
            ("cut", "grow", "cut#1", 0, 7, "w:keys#1", "cut keys：左下冲出三个金插头", "keys"),
            ("go", "snap", "blocked#1", 0, 46, "s", "for a blocked door：一个插头飞向插孔，被尾巴挡回来（T7）", None),
        ]),
    # ------------------------------------------------------------------ B 第 2 批（11_铺开排序.md：3-08、4-01、4-09、4-10、5-07、1-04、1-08、1-11）
    "1-04": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 1-04（btier/B104.jsx）。一线药换过一次：骨白药座上先是胶囊（Nexavar），combo 时胶囊被顶走，两袋输液落座（atezolizumab + bevacizumab）；"
             "three in ten：十个小人，五年后只亮三个，日历 5 years；the study we follow：论文书落下，手写 huge unmet need。",
        zone=1, trans_in="T5 capsule（上一段 1-03 是出镜段，胶囊）", trans_out="T5 runner（下一段 1-05 是出镜段）",
        ev=[
            ("stand", "appear", "standard#1", 0, 7, "w:treatment#1", "standard first treatment：骨白药座升起，胶囊落座", "stand"),
            ("liver", "appear", "liver#1", 0, 7, "w:cancer#1", "advanced liver cancer：右边玻璃肝", None),
            ("changed", "appear", "changed#1", 0, 6, "w:once#1", "changed once：手写", None),
            ("nex", "appear", "nexavar#1", 0, 10, "w:nexavar#1", "Nexavar：胶囊标名", None),
            ("combo", "eject", "combo#1", 0, 13, "w:combo#1", "a combo：胶囊被顶出去，两袋输液落座", "stand"),
            ("atezo", "appear", "atezolizumab#1", 0, 10, "w:atezolizumab#1", "atezolizumab：左袋标名", None),
            ("beva", "appear", "bevacizumab#1", 0, 10, "s", "plus bevacizumab：右袋标名", None),
            ("clear", "move", "but#1", 0, 6, "w:here#1", "But：药座退到左边变小", None),
            ("three", "appear", "three#1", 0, 30, "w:three#1", "three：数字轮 3", None),
            ("ten", "appear", "ten#1", 0, 7, "w:patients#1", "in ten patients：十个小人一个个落位", "people"),
            ("alive", "move", "alive#1", 0, 13, "w:alive#1", "alive：七个变灰下沉，三个留着", None),
            ("years", "appear", "five#1", 0, 7, "s", "five years on：日历落下，标 5 years", None),
            ("study", "appear", "study#1", 0, 7, "w:follow#1", "The study we follow：论文书落下", "book"),
            ("calls", "move", "calls#1", 0, 13, "w:calls#1", "calls it：书翻开一下", None),
            ("huge", "appear", "huge#1", 0, 6, "s", "a huge unmet need：手写", None),
        ]),
    "1-08": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 1-08（btier/B108.jsx）。一条带年份刻度的长路：born 那头站一个小人，胶囊沿路慢慢走到 now；"
             "2.8 billion：钞票一张张落成一摞，数字轮 2.8；one in ten：十粒胶囊在路上，九粒掉下去，一粒走到奖章（market）。",
        zone=1, trans_in="T5 runner（上一段 1-07 是出镜段）", trans_out="T5 runner（下一段 1-09 是 C 档三维大板）",
        ev=[
            ("road", "grow", "start#1", 0, 9, "w:search#1", "Start the search：长路从左往右铺开，胶囊在起点", "road"),
            ("year", "appear", "year#1", 0, 7, "w:year#1", "the year：路起点立一块日历", None),
            ("born", "appear", "born#1", 0, 7, "w:born#1", "we were born：小人站在起点，标 born", None),
            ("walk", "move", "might#1", 0, 6, "w:now#1", "it might only be ready：胶囊沿路走", None),
            ("now", "appear", "now#1", 0, 10, "s", "now：走到头，标 now", None),
            ("cost", "appear", "cost#1", 0, 7, "w:almost#1", "It can cost：清场，钞票开始落", "bills"),
            ("n28", "appear", "2.8#1", 0, 36, "w:2.8#1", "2.8：数字轮", None),
            ("bil", "appear", "billion#1", 0, 10, "s", "billion US dollars：标签", None),
            ("drugs", "appear", "drugs#1", 0, 7, "w:tested#1", "of drugs：清场，十粒胶囊排上路", "caps"),
            ("people", "appear", "people#1", 0, 7, "w:people#1", "tested in people：路边小人", None),
            ("one", "appear", "one#1", 0, 10, "w:one#1", "one：一粒亮", None),
            ("drop", "move", "ten#1", 0, 13, "w:reaches#1", "in ten：九粒掉下去", None),
            ("market", "appear", "market#1", 0, 30, "s", "reaches the market：那一粒走到奖章", None),
        ]),
    "1-11": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 1-11（btier/B111.jsx）。AI 芯片落下，胶囊沿几块踏步跳（first steps），手写 faster?；"
             "one real case：论文书；AI tools：三块芯片；liver cancer：玻璃肝；right here, in Hong Kong：香港地图落下，一点亮起，标 Hong Kong。",
        zone=1, trans_in="T5 runner（上一段 1-10 是 C 档三维大板）", trans_out="T5 runner（下一段 1-12）",
        ev=[
            ("ai", "appear", "ai#1", 0, 7, "w:walk#1", "can AI：芯片落位", "chip"),
            ("steps", "move", "steps#1", 0, 30, "w:steps#1", "walk the first steps：胶囊沿踏步跳", None),
            ("faster", "appear", "faster#1", 0, 6, "s", "faster?：手写", None),
            ("case", "appear", "case#1", 0, 7, "w:case#1", "one real case：清场，论文书落下", "book"),
            ("tools", "appear", "tools#1", 0, 7, "w:took#1", "AI tools：三块芯片依次落位", None),
            ("liver", "appear", "liver#1", 0, 7, "s", "liver cancer：玻璃肝", "liver"),
            ("starts", "move", "starts#1", 0, 13, "w:starts#1", "part of it starts：清场", None),
            ("here", "appear", "here#1", 0, 7, "w:here#1", "right here：香港地图落下", "map"),
            ("hk", "appear", "hong#1", 0, 10, "s", "in Hong Kong：一点亮起，标 Hong Kong", None),
        ]),
    "3-08": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 3-08（btier/B308.jsx）。要做插头，得先看清插座：空插头在左，插座在右但是磨砂、虚焦；"
             "no one had measured：红问号；hard lab work：烧瓶和样本管；only a small fraction：四十台小插座，只有三台是清楚的；"
             "Without a 3D shape：磨砂插座回来，芯片去算，插头对不准；expensive（钞票）、slow（日历）、difficult（问号）。",
        zone=3, trans_in="T2 甩进（上一段 3-07 是 B 页）", trans_out="T5 runner（下一段 3-09 是出镜段）",
        ev=[
            ("prob", "appear", "problem#1", 0, 6, "s", "But here's the problem：手写 problem", None),
            ("key", "appear", "key#1", 0, 7, "w:need#1", "To design a key：空插头落位", "plug"),
            ("lock", "appear", "lock#1", 0, 7, "s", "see the lock：插座出现，磨砂看不清", "socket"),
            ("nobody", "move", "no#1", 0, 13, "w:measured#1", "no one had measured：插座更虚", None),
            ("q", "appear", "shape#1", 0, 6, "s", "CDK20's shape：红问号", None),
            ("takes", "move", "takes#1", 0, 13, "w:takes#1", "That takes：插头和插座往右退场", None),
            ("lab", "appear", "lab#1", 0, 7, "w:work#1", "hard lab work：清场，烧瓶和样本管", "lab"),
            ("work", "move", "work#1", 0, 13, "w:work#1", "work：烧瓶晃", None),
            ("grid", "appear", "small#1", 0, 7, "w:fraction#1", "only a small fraction：四十台磨砂小插座铺开", "grid"),
            ("prot", "appear", "proteins#1", 0, 10, "w:proteins#1", "of proteins：标 proteins", None),
            ("meas", "appear", "measured#2", 0, 13, "s", "have ever been measured：三台变清楚、灯亮", None),
            ("noshape", "appear", "without#1", 0, 7, "w:shape#2", "Without a 3D shape：清场，磨砂插座回到中间", "socket"),
            ("comp", "appear", "computer#1", 0, 7, "w:predictions#1", "computer predictions：芯片落位", None),
            ("bind", "move", "binding#1", 0, 30, "w:get#1", "of binding：插头去试，对不准", None),
            ("exp", "appear", "expensive#1", 0, 7, "w:expensive#1", "expensive：钞票", None),
            ("slow", "appear", "slow#1", 0, 7, "w:slow#1", "slow：日历", None),
            ("diff", "appear", "difficult#1", 0, 6, "s", "difficult：问号", None),
        ]),
    "4-01": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 4-01（btier/B401.jsx）。三个小人（team），手写 science fiction；AI 芯片 + 磨砂插座和问号（guess the shape）；"
             "蛋白 = 一串积木珠子，一字排开，再折起来，化成 AlphaFold 预测模型；sequence：珠子上是 CDK20 真实序列的前 16 个字母；"
             "AlphaFold 从数据库架学；Give it one：序列条进芯片，出来模型，按把握上色，图例 sure / unsure，手写圈住红尾巴。",
        zone=4, trans_in="T5 socket（上一段 W2 是 A 段）", trans_out="T2 甩镜往左（下一段 4-02 是 B 页）",
        ev=[
            ("team", "appear", "team#1", 0, 7, "w:did#1", "So the team：三个小人", "team"),
            ("some", "move", "something#1", 0, 13, "w:once#1", "did something：小人往左让开", None),
            ("scifi", "appear", "science#1", 0, 6, "s", "science fiction：手写", None),
            ("ai", "appear", "ai#1", 0, 7, "w:guess#1", "asked an AI：AlphaFold 芯片落位", "chip"),
            ("guess", "appear", "shape#1", 0, 7, "s", "guess the shape：磨砂插座和问号", None),
            ("prot", "appear", "protein#1", 0, 7, "w:as#1", "Imagine a protein：清场", None),
            ("chain", "grow", "chain#1", 0, 13, "w:of#1", "as a chain：珠子一颗颗排出来", "chain"),
            ("blocks", "appear", "blocks#1", 0, 13, "w:blocks#1", "building blocks：珠子挨个鼓一下", None),
            ("folds", "move", "folds#1", 0, 13, "w:into#1", "that folds：链折起来", None),
            ("shape3d", "appear", "shape#2", 0, 13, "s", "into a 3D shape：化成预测模型", None),
            ("order", "move", "order#1", 0, 13, "w:order#1", "The order：模型退到右边，链重新排直", "chain"),
            ("letters", "appear", "blocks#2", 0, 10, "w:blocks#2", "of the blocks：珠子上出字母", None),
            ("seq", "appear", "sequence#1", 0, 10, "s", "is the sequence：标 sequence", None),
            ("af", "appear", "alphafold#1", 0, 7, "w:learned#1", "AlphaFold：芯片落到中间", "chip"),
            ("known", "appear", "structures#1", 0, 7, "w:structures#1", "known structures：数据库架落下", None),
            ("learn", "move", "how#1", 0, 13, "s", "how sequences fold：数据沿料杆流进芯片", None),
            ("give", "move", "one#1", 0, 30, "w:one#1", "Give it one：序列条送进芯片", None),
            ("predicts", "move", "predicts#1", 0, 13, "w:predicts#1", "it predicts：芯片一震、灯亮", None),
            ("pred", "appear", "shape#3", 0, 13, "w:shape#3", "it predicts the shape：模型出来", "model"),
            ("sure", "appear", "sure#1", 0, 10, "w:is#2", "how sure：图例 sure / unsure", None),
            ("part", "appear", "part#1", 0, 6, "s", "each part：手写圈住红尾巴", None),
        ]),
    "4-09": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 4-09（btier/B409.jsx）。Chemistry42 芯片拿到口袋的形状（插座正面），one rule：插头要卡住插孔边上的 hinge（铰点亮，手写 hinge）；"
             "filters：筛子，插头往下落；reactive / toxic 的被甩出去；score：两块表盘 drug-like、easy to make 指针摆到高处。",
        zone=4, trans_in="T5 runner（上一段 4-08 是出镜段）", trans_out="T5 chip（下一段 W3 是 A 段芯片）",
        ev=[
            ("chip", "appear", "gave#1", 0, 7, "w:it#1", "The team gave it：Chemistry42 芯片落位", "chip"),
            ("pocket", "appear", "shape#1", 0, 7, "w:shape#1", "the pocket's shape：插座正面落位", "socket"),
            ("rule", "appear", "rule#1", 0, 10, "w:rule#1", "one rule：标 one rule", None),
            ("key", "move", "key#1", 0, 30, "w:must#1", "every key：插头飞到插孔前", None),
            ("grip", "snap", "grip#1", 0, 13, "w:spot#1", "must grip a spot：插头卡住一边", None),
            ("hinge", "appear", "hinge#1", 0, 6, "s", "called the hinge：铰点亮，手写 hinge", None),
            ("filt", "appear", "filters#1", 0, 7, "w:built#1", "Its filters：清场，筛子落位", "sieve"),
            ("toss", "move", "toss#1", 0, 13, "w:designs#1", "to toss：插头往下落", None),
            ("react", "eject", "reactive#1", 0, 13, "w:reactive#1", "reactive：一个被甩出去", None),
            ("toxic", "eject", "toxic#1", 0, 13, "w:groups#1", "possibly toxic groups：又一个被甩出去", None),
            ("score", "appear", "score#1", 0, 7, "w:how#1", "to score：两块表盘", "dials"),
            ("drug", "move", "drug-like#1", 0, 13, "w:drug-like#1", "how drug-like：左表指针摆高", None),
            ("easy", "move", "easy#1", 0, 13, "s", "easy to make：右表指针摆高", None),
        ]),
    "4-10": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 4-10（btier/B410.jsx）。8,918：数字轮转到 8,918，一大片小插头铺满；way too many：手写；"
             "a virtual lock：一个插头出来，蓝色线框的插座；docking：插头进孔，表盘打分；grouped：插头按形状聚成几堆；54：数字轮停 54；"
             "chemists pick just seven：小人，七个插头进托盘，烧瓶。",
        zone=4, trans_in="T5 chip（上一段 W3 是 A 段芯片）", trans_out="T5 runner（下一段 4-11+12 是出镜段）",
        ev=[
            ("n8918", "appear", "8,918#1", 0, 60, "w:designs#1", "8,918：数字轮转到 8,918", None),
            ("pile", "appear", "brand-new#1", 0, 7, "s", "brand-new designs：小插头一片片铺满", "pile"),
            ("many", "appear", "many#1", 0, 6, "s", "Way too many to make：手写", None),
            ("each", "move", "key#1", 0, 13, "w:tried#1", "each key：一个插头升起来", None),
            ("vlock", "appear", "virtual#1", 0, 7, "s", "a virtual lock：线框插座", "socket"),
            ("dock", "appear", "docking#1", 0, 10, "w:docking#1", "That's docking：标 docking", None),
            ("comp", "move", "computer#1", 0, 13, "w:computer#1", "the computer：线框插座扫一遍", None),
            ("mol", "move", "molecule#1", 0, 13, "w:molecule#1", "a molecule：插头转向插孔", None),
            ("sit", "move", "sit#1", 0, 40, "w:pocket#1", "might sit in the pocket：插头进孔", None),
            ("scorefit", "move", "scores#1", 0, 13, "s", "scores the fit：表盘指针", "dial"),
            ("group", "move", "grouped#1", 0, 13, "w:grouped#1", "Similar designs get grouped：插头聚成几堆", "pile"),
            ("n54", "appear", "54#1", 0, 40, "w:shortlist#1", "54：数字轮停 54，只剩一小片", None),
            ("chem", "appear", "chemists#1", 0, 7, "w:pick#1", "chemists：小人", None),
            ("seven", "move", "seven#1", 0, 30, "w:to#2", "pick just seven：七个插头进托盘", None),
            ("make", "appear", "make#3", 0, 7, "s", "to make：烧瓶", None),
        ]),
    "5-07": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 5-07（btier/B507.jsx）。Not at all（手写）；the loop：设计循环圈落下转起来，lab data：烧瓶里的数据点倒进圈；"
             "went back in：数据沿圈走；predicted pose of how 001 sat：小插座插着 001，标 predicted pose；Sixteen：十六个新插头；Six made and tested：六个进烧瓶；"
             "30 days：日历，数字轮 30，001 打勾。",
        zone=5, trans_in="T5 runner（上一段 5-05+06 是出镜段）", trans_out="T2 甩镜往左（下一段 5-08 是 B 页）",
        ev=[
            ("not", "appear", "not#1", 0, 6, "s", "Not at all：手写", None),
            ("loop", "appear", "loop#1", 0, 7, "w:kicks#1", "the loop：循环圈落下", "loop"),
            ("kick", "move", "kicks#1", 0, 13, "w:again#1", "kicks in again：圈转起来", None),
            ("now", "move", "now#1", 0, 13, "w:with#1", "now with：圈亮一下", None),
            ("data", "appear", "lab#1", 0, 7, "w:data#1", "real lab data：烧瓶落下", None),
            ("inside", "move", "inside#1", 0, 30, "s", "inside：数据点倒进圈里", None),
            ("results", "move", "results#1", 0, 13, "w:back#1", "The results went back in：数据点沿圈走", None),
            ("pose", "appear", "predicted#1", 0, 7, "w:pose#1", "a predicted pose：小插座插着 001", "pose"),
            ("p001", "appear", "001#1", 0, 10, "w:001#1", "001：标 001", None),
            ("pocket", "move", "pocket#1", 0, 13, "s", "sat in the pocket：插头往里一推、灯亮", None),
            ("n16", "appear", "sixteen#1", 0, 7, "s", "Sixteen new designs：十六个新插头", "new"),
            ("six", "move", "six#1", 0, 13, "s", "Six made and tested：六个进烧瓶", None),
            ("d30", "appear", "30#1", 0, 40, "w:days#1", "within 30 days：日历，数字轮 30", "cal"),
            ("hit", "appear", "hit#1", 0, 7, "s", "that first hit：001 打勾", None),
        ]),
    # ------------------------------------------------------------------ B 第 3 批（11_铺开排序.md：2-01、2-05、2-06、2-07、3-07、4-02、4-06、4-07）
    "2-01": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 2-01（btier/B201.jsx）。香港地图落下；2011 年份牌、中大团队、肝肿瘤样本、威尔斯亲王医院；"
             "六支样本管剖面里的蓝色液柱一支支高过灰线（raised），CCRK = CDK20；年份牌滚到 2023，论文书和同一个小插座，合著者在科学园。",
        zone=2, trans_in="T5 runner（上一段 1-12 不是 B 页）", trans_out="T5 runner（下一段 2-02 是出镜段）",
        ev=[
            ("map", "appear", "first#1", 0, 7, "w:first#1", "香港地图从浇口落位", "map"),
            ("y2011", "appear", "2011#1", 0, 7, "w:2011#1", "年份牌翻到 2011", "year"),
            ("team", "appear", "team#1", 0, 7, "w:team#1", "机位沿着地图滑到沙田", None),
            ("cuhk", "appear", "university#1", 0, 10, "w:kong#2", "中大图钉和名牌", None),
            ("tum", "appear", "tumours#1", 0, 7, "w:tumours#1", "地图缩到左侧，肝与红结节落位", "samples"),
            ("pat", "appear", "patients#1", 0, 7, "w:patients#1", "样本来源：镜头移向肝", None),
            ("pwh", "appear", "hospital#1", 0, 10, "s", "医院图钉和名牌", None),
            ("prot", "move", "protein#1", 0, 13, "w:protein#1", "肝缩向左侧，三对样本管排开", None),
            ("raised", "grow", "raised#1", 0, 30, "w:raised#1", "三对样本管内肿瘤管液面升高", "tubes"),
            ("ccrk", "appear", "ccrk#1", 0, 7, "w:ccrk#1", "同一块翻牌显示 CCRK", None),
            ("cdk20", "appear", "cdk20#1", 0, 10, "s", "翻牌翻到 CDK20，小插座落位", None),
            ("ff", "grow", "2023#1", 0, 36, "w:2023#1", "年份牌翻到 2023", "year"),
            ("ai", "appear", "ai#1", 0, 7, "w:drug-discovery#1", "三对样本管退回托盘", None),
            ("study", "appear", "study#1", 0, 7, "w:study#1", "论文牌落位", None),
            ("same", "move", "same#1", 0, 30, "w:protein#2", "同一插座滑到论文牌旁", "book"),
            ("coauth", "appear", "co-authors#1", 0, 7, "w:co-authors#1", "论文牌作者栏扫光", None),
            ("ins", "appear", "insilico#1", 0, 10, "w:medicine's#1", "合著者机构名牌贴在作者栏", None),
            ("hk3", "move", "science#1", 0, 13, "w:park#1", "地图回到正中，路线亮", None),
            ("sp", "appear", "park#1", 0, 10, "s", "科学园图钉落位", None),
        ]),
    "2-05": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 2-05（btier/B205.jsx）。两个目标上下两栏：编号牌 1、放大镜扫过三块 AI 芯片、玻璃肝（cancer drug discovery）；"
             "编号牌 2、小人、五个金插头沿料杆走过检测门，各长一根分数条，最好的打勾。导演 11-18 看二维样片时要求加说明文字：两栏各一行 Aim 1 / Aim 2。",
        zone=2, trans_in="T5 runner（上一段 2-04 是出镜段）", trans_out="T2 甩镜往左（下一段 2-06 是 B 页）",
        ev=[
            ("aim1", "appear", "one#1", 0, 7, "w:one#1", "One：编号牌 1 落下，标 Aim 1", "aim1"),
            ("identify", "move", "identify#1", 0, 13, "w:identify#1", "identify：放大镜从左扫过来", None),
            ("methods", "appear", "computer-aided#1", 0, 7, "w:methods#1", "computer-aided methods：三块芯片依次落位", "chips"),
            ("cancer", "appear", "cancer#1", 0, 7, "s", "used in cancer drug discovery：玻璃肝落下", None),
            ("aim2", "appear", "two#1", 0, 7, "w:two#1", "Two：编号牌 2 落下，标 Aim 2", "aim2"),
            ("eval", "grow", "evaluate#1", 0, 13, "w:evaluate#1", "evaluate：下栏料杆和检测门长出来", None),
            ("these", "move", "methods#2", 0, 13, "w:methods#2", "these methods：上栏三块芯片一块块亮一下", None),
            ("sci", "appear", "scientists#1", 0, 7, "w:scientists#1", "help scientists：小人落下", None),
            ("assess", "move", "assess#1", 0, 13, "w:assess#1", "assess：金插头沿料杆走过检测门，各长一根分数条", None),
            ("cands", "appear", "candidates#1", 0, 7, "s", "potential drug candidates：五个插头排好，最好的打勾", None),
        ]),
    "2-06": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 2-06（btier/B206.jsx）。红问号；We read：一本书；A lot：书一本本摞起来；没有自己的实验：烧瓶变灰打叉；literature review；"
             "主论文落到料杆框中心，挂 Ren et al. 名牌，下面数据架（supplementary data）；六根料杆往外长，六张来源卡依次挂上；Perspective 那张大半磨砂（只读了摘要）。",
        zone=2, trans_in="T2 甩进（上一段 2-05 是 B 页）", trans_out="T2 甩镜往左（下一段 2-07 是 B 页）",
        ev=[
            ("q", "appear", "check#1", 0, 0, "s", "how did we check all this?：红问号", None),
            ("read", "appear", "read#1", 0, 7, "s", "We read：一本书落下", "books"),
            ("lot", "grow", "lot#1", 0, 7, "s", "A lot：书一本本摞起来", None),
            ("lab", "appear", "lab#1", 0, 7, "w:work#1", "No lab work：烧瓶落下", None),
            ("nolab", "move", "own#1", 0, 13, "w:own#1", "of our own：烧瓶变灰，画叉", None),
            ("review", "appear", "literature#1", 0, 10, "s", "literature review：标 literature review", None),
            ("centre", "grow", "centre#1", 0, 13, "w:centre#1", "At the centre：清场，中心一块底座", None),
            ("study", "appear", "original#1", 0, 7, "w:study#1", "one original study：主论文落到中心", "main"),
            ("ren", "appear", "ren#1", 0, 10, "w:2023#1", "Ren … 2023：名牌", None),
            ("supp", "appear", "supplementary#1", 0, 7, "s", "supplementary data：数据架落下，浇口连上", None),
            ("around", "grow", "around#1", 0, 13, "w:it#1", "Around it：六根料杆从中心往外长", "frame"),
            ("hk", "appear", "earlier#1", 0, 7, "w:study#2", "the earlier Hong Kong study：第一张卡", None),
            ("papers", "grow", "papers#1", 0, 7, "w:behind#1", "papers：左边两根料杆尖上长出空卡位", None),
            ("tools", "appear", "two#1", 0, 7, "w:tools#1", "papers behind two AI tools：两张卡", None),
            ("rev", "appear", "2023#2", 0, 7, "w:review#2", "a 2023 review：第四张卡", None),
            ("text", "appear", "textbook#1", 0, 7, "w:chapter#1", "a textbook chapter：第五张卡", None),
            ("persp", "appear", "2026#1", 0, 7, "w:perspective#1", "a 2026 expert Perspective：第六张卡", "card6"),
            ("abs", "move", "only#1", 0, 13, "s", "read only as an abstract：第六张卡大半变磨砂", None),
        ]),
    "2-07": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 2-07（btier/B207.jsx）。左边七张来源卡，放大镜一张张扫过；右边核对表五行逐条写出打勾；"
             "主论文：八个作者里六个站上 Insilico Medicine 底板，两块芯片也落在底板上（它造的 AI 工具）；论文上 declared 名牌打勾；useful evidence，手写 not an independent check。",
        zone=2, trans_in="T2 甩进（上一段 2-06 是 B 页）", trans_out="T2 甩镜往左（下一段 2-08 是 B 页）",
        ev=[
            ("src", "appear", "source#1", 0, 7, "w:source#1", "For every source：七张来源卡落下", "cards"),
            ("asked", "move", "asked#1", 0, 13, "w:asked#1", "we asked：放大镜落到第一张卡上，核对表底板滑进来", None),
            ("kind", "appear", "kind#1", 0, 10, "w:it#1", "what kind is it：核对表第一行", None),
            ("much", "appear", "much#1", 0, 10, "w:read#1", "how much did we read：第二行", None),
            ("strong", "appear", "strong#1", 0, 10, "s", "how strong is the evidence：第三行", "list"),
            ("who", "appear", "who#1", 0, 10, "s", "Who did the work?：第四行", None),
            ("ctrl", "appear", "controls#1", 0, 10, "s", "Were there controls and repeats?：第五行", None),
            ("worth", "move", "one#1", 0, 13, "w:knowing#1", "One thing worth knowing：清场，主论文落到左边", "main"),
            ("authors", "appear", "authors#1", 0, 7, "w:study#1", "most authors of the main study：一排八个小人", None),
            ("ins", "move", "insilico#1", 0, 13, "w:medicine#1", "work for Insilico Medicine：底板滑进来，六个小人跳上去", "ins"),
            ("built", "appear", "built#1", 0, 7, "s", "which built its AI tools：两块芯片落到底板上", None),
            ("open", "appear", "openly#1", 0, 7, "s", "They say so openly：论文挂 declared 名牌，打勾", None),
            ("useful", "appear", "useful#1", 0, 7, "w:evidence#2", "Useful evidence：标 useful evidence", None),
            ("notind", "appear", "not#1", 0, 0, "s", "not an independent check：手写", None),
        ]),
    "3-07": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 3-07（btier/B307.jsx）。2023 年份牌，PandaOmics 芯片，CDK20 小插座打勾（hunch）；"
             "十个数据架依次落下，数据沿料杆流进芯片；1,133 个肿瘤样本（蓝点）、674 个健康样本（灰点）；论文飞进芯片；"
             "Top 20 表一行行画出、小人逐行打勾，CDK20 那一行升到第一；胶囊变灰画斜杠，手写 no approved drug yet。",
        zone=3, trans_in="T5 runner（上一段 3-06 是出镜段）", trans_out="T2 甩镜往左（下一段 3-08 是 B 页）",
        ev=[
            ("y23", "appear", "2023#1", 0, 7, "w:2023#1", "In 2023：年份牌落下", "year"),
            ("panda", "appear", "pandaomics#1", 0, 7, "w:pandaomics#1", "PandaOmics：芯片落下", None),
            ("hunch", "appear", "backed#1", 0, 10, "s", "backed that hunch：小插座落下打勾，手写 hunch", "chip"),
            ("ten", "grow", "ten#1", 0, 7, "w:sets#1", "ten liver cancer data sets：十个数据架依次落下，数字轮 10", "sets"),
            ("tum", "grow", "thousand#1", 0, 36, "w:samples#1", "over a thousand tumour samples：蓝点长满，数字轮 1,133", None),
            ("hl", "grow", "hundreds#1", 0, 36, "w:ones#1", "hundreds of healthy ones：灰点长满，数字轮 674", None),
            ("papers", "move", "plus#1", 0, 13, "s", "plus research papers：一叠论文飞进芯片", None),
            ("people", "appear", "people#1", 0, 7, "w:checked#1", "People checked：清场，两个小人落下", None),
            ("top20", "grow", "top#1", 0, 13, "w:hand#1", "its top 20 by hand：表格一行行画出，逐行打勾", "table"),
            ("cdkl", "move", "cdk20#1", 0, 13, "w:cdk20#1", "and CDK20：蓝色那一行亮一下", None),
            ("cdk", "move", "came#1", 0, 13, "w:top#2", "CDK20 came out on top：蓝色那一行升到第一", None),
            ("nodrug", "appear", "no#1", 0, 7, "s", "no approved drug against it yet：胶囊变灰画斜杠，手写", None),
        ]),
    "4-02": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 4-02（btier/B402.jsx）。左栏 Before：烧瓶、日历翻页、进度条慢慢爬（lab-measured structure）；"
             "右栏 Now?：数据架，抽出一张预测模型卡，进度条一下满格，价签 free，public database；论文书，手写 first time，AlphaFold 芯片，001 插头打勾。",
        zone=4, trans_in="T2 甩进（上一段 4-01 是 B 页）", trans_out="T2 甩镜往左（下一段 4-03 是 B 页）",
        ev=[
            ("need", "appear", "need#1", 0, 7, "w:need#1", "you'd need：日历落下", None),
            ("lab", "appear", "lab-measured#1", 0, 7, "w:structure#1", "lab-measured：烧瓶落下，进度条开始慢慢爬", "before"),
            ("struct", "appear", "structure#1", 0, 10, "s", "structure：标 lab-measured structure", None),
            ("now", "appear", "now#1", 0, 7, "s", "Now?：右栏数据架落下，手写 Now?", "now"),
            ("dl", "move", "downloaded#1", 0, 13, "w:prediction#1", "downloaded a prediction：抽出预测模型卡，进度条一下满格", "model"),
            ("free", "appear", "free#1", 0, 7, "w:free#1", "for free：价签 free", None),
            ("db", "appear", "public#1", 0, 10, "s", "from a public database：标 public database", None),
            ("paper", "appear", "paper#1", 0, 7, "w:paper#1", "According to the paper：清场，论文书落下", "paper"),
            ("this", "move", "this#1", 0, 13, "w:was#1", "this was：论文书一抖，翻开", None),
            ("first", "appear", "first#1", 0, 0, "w:time#1", "first time：手写", None),
            ("af", "appear", "alphafold#1", 0, 7, "w:alphafold#1", "AlphaFold：芯片落下", None),
            ("used", "move", "used#1", 0, 13, "w:used#1", "had been used：预测模型卡从芯片里滑出来", None),
            ("hit", "appear", "hit#1", 0, 7, "s", "find a hit：001 插头落下打勾", None),
        ]),
    "4-06": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 4-06（btier/B406.jsx）。一圈骨白料杆环，四站牌 Imagine / Make / Test / Tweak；"
             "化学家小人，一个金插头沿环走：Make 烧瓶、Test 小插座插不进弹回变灰（fails）、Tweak 换形、回到第一站；"
             "every single round：插头越跑越快，每过顶站掉一张钞票、日历翻一页。",
        zone=4, trans_in="T5 runner（上一段 4-04+05 是出镜段）", trans_out="T2 甩镜往左（下一段 4-07 是 B 页，同一个环接着用）",
        ev=[
            ("part", "grow", "next#1", 0, 13, "w:part#1", "this next part：圆环料杆画出来", "loop"),
            ("mind", "move", "blew#1", 0, 7, "s", "blew my mind：环一亮一抖（T7）", None),
            ("chem", "appear", "chemists#1", 0, 7, "w:chemists#1", "chemists：小人落下", None),
            ("key", "appear", "key#1", 0, 7, "s", "found a key：金插头落在环顶", "key"),
            ("imag", "appear", "imagine#1", 0, 7, "s", "Imagine：第一站牌弹出", None),
            ("make", "move", "make#1", 0, 13, "s", "Make it：插头走到第二站，烧瓶落下", None),
            ("test", "move", "test#1", 0, 13, "s", "Test it：走到第三站，小插座落下", None),
            ("fail", "snap", "fails#1", 0, 7, "s", "It fails：插头顶不进，弹回变灰（T7）", None),
            ("tweak", "move", "tweak#1", 0, 13, "s", "Tweak it：走到第四站，插头换个形状", None),
            ("again", "move", "try#1", 0, 13, "s", "Try again：回到第一站", None),
            ("round", "move", "every#1", 0, 13, "w:round#1", "every single round：插头绕环越跑越快", None),
            ("cost", "grow", "costs#1", 0, 7, "s", "costs time and money：每过顶站掉一张钞票、日历翻一页", "costs"),
        ]),
    "4-07": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 4-07（btier/B407.jsx）。4-06 的圆环接着在；Chemistry42 芯片落下，环缩小飞进芯片；"
             "芯片上方 36 个小环一个个长出来一起转（dozens of AI models），底板 known chemistry；金插头从芯片冒出、右边插座落下、每个插头长分数条，"
             "分数沿料杆流回小环（learn），再来一批；new structures within hours。",
        zone=4, trans_in="T2 甩进（上一段 4-06 是 B 页）", trans_out="T5 runner（下一段 4-08 是出镜段）",
        ev=[
            ("chip", "appear", "ai#1", 0, 7, "w:ai#1", "Generative AI：Chemistry42 芯片落下", None),
            ("takes", "move", "takes#1", 0, 13, "w:loop#1", "takes that loop：圆环被拎起来", "loop"),
            ("inside", "move", "moves#1", 0, 30, "w:computer#1", "moves it inside a computer：圆环缩小飞进芯片", "chip"),
            ("plat", "move", "platform#1", 0, 13, "w:chemistry42#1", "The platform here, Chemistry42：芯片挪到左下", None),
            ("dozens", "grow", "dozens#1", 0, 7, "w:models#1", "dozens of AI models：36 个小环一个个长出来", "grid"),
            ("side", "move", "side#1", 0, 13, "w:side#2", "side by side：小环一起转", None),
            ("known", "appear", "known#1", 0, 7, "s", "built on known chemistry：底板滑进来", None),
            ("invent", "grow", "invent#1", 0, 7, "w:molecules#1", "invent new molecules：金插头从芯片冒出来", None),
            ("key", "appear", "keyhole#1", 0, 7, "w:keyhole#1", "this exact keyhole：右边插座落下", "socket"),
            ("score", "grow", "score#1", 0, 13, "w:them#1", "score them：每个插头旁边长一根分数条", None),
            ("learn", "move", "learn#1", 0, 13, "w:scores#1", "learn from the scores：分数沿料杆流回小环", None),
            ("again", "move", "go#1", 0, 13, "s", "go again：小环转快，换一批插头", None),
            ("makers", "appear", "makers#1", 0, 10, "w:say#1", "Its makers say：芯片下面挂 makers' claim 名牌", None),
            ("new", "grow", "new#2", 0, 7, "w:structures#1", "new structures：插头一批批冒出来", "new"),
            ("hours", "appear", "hours#1", 0, 10, "s", "within hours：标 within hours", None),
        ]),
    # ------------------------------------------------------------------ B 第 4 批（第 6 章 7 页 + 7-02、7-03、7-04、8-02）
    "6-01": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 6-01（btier/B601.jsx，第 6 章第一页，T6 光扫）。"
             "第 6 章共用一块实体翻牌记分板组件（6-01/02/03/06/07/08，骨白外壳 + 炭黑翻牌槽 + 克莱因蓝高亮）："
             "顶栏大标题翻牌 HOW MUCH DID COMPUTERS HELP?；主体 4 行 × 3 列（左窄列为行名 TASK，中列为 BEFORE 翻牌区 + 左小凹位零件槽，"
             "右列为 NOW 翻牌区 + 右小凹位零件槽），底部预留 6-08 引文落牌槽。"
             "四行预设内容：Row 1 SEEING THE LOCK（HARD LAB EXPERIMENTS / EXPENSIVE·SLOW·DIFFICULT vs FREE PREDICTION / PUBLIC DATABASE）；"
             "Row 2 FINDING A HIT（MILLIONS SCREENED / COSTLY BOTTLENECK vs 8,918 DESIGNS / 13 MOLECULES MADE）；"
             "Row 3 TIME（10–17 YEARS / HIT = OPENING STRETCH vs 30 DAYS (1ST HIT) / +30 DAYS (BETTER KEY)）；"
             "Row 4 IMPROVING THE KEY（ANOTHER COSTLY LAB ROUND vs 16 GUIDED DESIGNS / ~15× TIGHTER GRIP）。"
             "本段 6-01：记分板立起，翻出顶栏标题与 BEFORE / NOW 两栏表头，四行空位翻牌轻抖待命，随后镜头推向第 1 行。",
        zone=6, trans_in="T2 甩进（上一段 5-10 是 B 页）+ T6 光扫（第 6 章第一页）", trans_out="T2 甩镜往左（下一段 6-02 是 B 页，记分板推入第 1 行）",
        ev=[
            ("sweep", "appear", "so#1", 0, 9, "d:24", "So：T6 光扫过（第 6 章第一页）", None),
            ("board", "grow", "question#1", 0, 13, "s", "the big question：实体翻牌记分板从第 6 区大板上立起", None),
            ("title", "snap", "computers#1", 0, 28, "w:actually#1", "the computers：顶栏标题翻牌哗啦翻出 HOW MUCH DID COMPUTERS HELP?", "header"),
            ("help", "appear", "help#1", 0, 10, "s", "actually help?：标题末尾红问号翻牌定格", None),
            ("cols", "grow", "line#1", 0, 13, "w:before#1", "Let's line up：4 行 × 3 列翻牌框与左右小凹位展开", "cols"),
            ("before", "snap", "before#1", 0, 13, "w:now#1", "before：中栏表头翻出 BEFORE，左侧四行空翻牌轻抖待命", None),
            ("now", "snap", "now#1", 0, 10, "s", "and now：右栏表头翻出克莱因蓝框 NOW，右侧四行空翻牌轻抖待命", None),
        ]),
    "6-02": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 6-02（btier/B602.jsx，复用第 6 章翻牌记分板组件）。"
             "填第 1 行：行名翻出 1. SEEING THE LOCK；BEFORE 左凹位升起磨砂 CDK20 轮廓件，主翻牌翻出 HARD LAB EXPERIMENTS，"
             "副行三枚小翻牌依次翻出 EXPENSIVE、SLOW、DIFFICULT；NOW 右凹位升起 4-02 同款克莱因蓝 CDK20 预测卡片，"
             "主翻牌翻出 FREE PREDICTION，卡片旁亮出公共数据库小机柜，副翻牌翻出 PUBLIC DATABASE（注 AlphaFold DB v6）。",
        zone=6, trans_in="T2 甩进（上一段 6-01 是 B 页）", trans_out="T2 甩镜往左（下一段 6-03 是 B 页）",
        ev=[
            ("row1", "snap", "seeing#1", 0, 9, "w:lock#1", "Seeing：第 1 行行名翻出 1. SEEING THE LOCK", None),
            ("focus1", "move", "lock#1", 0, 7, "s", "the lock：镜头推近第 1 行，左右小凹位框亮起", None),
            ("bef", "appear", "before#1", 0, 7, "w:experiments#1", "Before：左凹位升起磨砂 CDK20 轮廓件", "before1"),
            ("lab", "snap", "experiments#1", 0, 28, "w:and#1", "hard lab experiments：BEFORE 主翻牌翻出 HARD LAB EXPERIMENTS", None),
            ("no3d", "move", "without#1", 0, 13, "w:shape#1", "without a 3D：左凹位磨砂轮廓发虚并亮起红问号", None),
            ("shape", "appear", "shape#1", 0, 10, "w:expensive#1", "shape：标出缺少三维形状示意", None),
            ("exp", "snap", "expensive#1", 0, 13, "w:slow#1", "expensive：副行第 1 枚小翻牌翻出 EXPENSIVE", "tags1"),
            ("slow", "snap", "slow#1", 0, 13, "w:difficult#1", "slow：副行第 2 枚小翻牌翻出 SLOW", None),
            ("diff", "snap", "difficult#1", 0, 10, "s", "difficult：副行第 3 枚小翻牌翻出 DIFFICULT", None),
            ("now", "grow", "now#1", 0, 13, "w:prediction#1", "Now：右凹位升起 4-02 同款蓝色 CDK20 预测卡片", "now1"),
            ("pred", "snap", "prediction#1", 0, 13, "w:downloaded#1", "free prediction：NOW 主翻牌翻出 FREE PREDICTION", None),
            ("dl", "move", "downloaded#1", 0, 28, "w:public#1", "downloaded：数据流小图标落向 CDK20 卡片", None),
            ("pub", "grow", "public#1", 0, 13, "w:database#1", "public：卡片旁亮出公共数据库小机柜图标", None),
            ("db", "snap", "database#1", 0, 10, "s", "database：NOW 副翻牌翻出 PUBLIC DATABASE（注 AlphaFold DB v6）", None),
        ]),
    "6-03": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 6-03（btier/B603.jsx，复用第 6 章翻牌记分板组件，第 1 行保持已填）。"
             "填第 2 行：行名翻出 2. FINDING A HIT；BEFORE 左凹位升起透明料斗（h23），满满细珠倾泻下流，主翻牌翻出 MILLIONS SCREENED，"
             "细珠在细颈堵塞，副翻牌翻出 COSTLY BOTTLENECK（旁注 2023 review）；NOW 右侧数字轮滚到 8,918，主翻牌翻出 8,918 DESIGNS，"
             "右凹位小托盘只落下 13 颗珠子，副翻牌翻出 13 MOLECULES MADE；段尾料斗向右飞出衔接 6-04+05 出镜。",
        zone=6, trans_in="T2 甩进（上一段 6-02 是 B 页）", trans_out="T5 runner（下一段 6-04+05 是出镜 A 段，料斗飞向右侧接出镜）",
        ev=[
            ("row2", "snap", "finding#1", 0, 9, "w:hit#1", "Finding：第 2 行行名翻出 2. FINDING A HIT", None),
            ("focus2", "move", "hit#1", 0, 7, "s", "a hit：镜头下移对准第 2 行，左右凹位亮起", None),
            ("bef", "grow", "before#1", 0, 13, "w:compounds#1", "Before：左凹位升起透明料斗（h23）", "hopper"),
            ("comp", "appear", "compounds#1", 0, 10, "w:millions#1", "real compounds：满槽细珠在料斗上方聚齐", None),
            ("mil", "move", "millions#1", 0, 28, "w:approach#1", "by the millions：细珠倾泻下流，BEFORE 主翻牌翻出 MILLIONS SCREENED", None),
            ("appr", "move", "approach#1", 0, 13, "w:2023#1", "an approach：细珠涌向料斗细颈口开始拥堵", None),
            ("rev", "appear", "2023#1", 0, 10, "w:says#1", "a 2023 review：2023 review 小引用牌亮起", None),
            ("says", "move", "says#1", 0, 13, "w:costly#1", "says has hit：细颈处细珠彻底卡死堆积", "jam"),
            ("costly", "appear", "costly#1", 0, 10, "w:bottleneck#1", "costly：细颈红环警示亮起", None),
            ("bn", "snap", "bottleneck#1", 0, 13, "s", "bottleneck：BEFORE 副翻牌翻出 COSTLY BOTTLENECK", None),
            ("now", "appear", "now#1", 0, 10, "w:8,918#1", "Now：右凹位切入数字计数轮与小托盘", "now2"),
            ("n8918", "grow", "8,918#1", 0, 28, "w:designs#1", "8,918：右侧数字轮滚停在 8,918", None),
            ("des", "snap", "designs#1", 0, 13, "w:computer#1", "designs：NOW 主翻牌翻出 8,918 DESIGNS", None),
            ("comp2", "appear", "computer#1", 0, 10, "w:13#1", "inside a computer：芯片轮廓框在数字轮旁亮起", None),
            ("n13", "eject", "13#1", 0, 28, "w:molecules#1", "just 13：右凹位小托盘只落下 13 颗珠子，排成一行", "tray13"),
            ("made", "snap", "made#1", 0, 13, "s", "actually made：NOW 副翻牌翻出 13 MOLECULES MADE（T7 轻抖）", None),
        ]),
    "6-06": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 6-06（btier/B606.jsx，复用第 6 章翻牌记分板组件，第 1、2 行保持已填，第 2 行托盘保留 13 颗珠子）。"
             "填第 3 行：行名翻出 3. TIME；BEFORE 左凹位卷尺（h18）大幅拉长，主翻牌翻出 10–17 YEARS，卷尺最前面一小段变红高亮，"
             "副翻牌翻出 HIT = OPENING STRETCH；NOW 右凹位 Calendar1 日历先翻至 30，主翻牌翻出 30 DAYS (1ST HIT)，"
             "随后 048 钥匙图标展开、日历再翻 30，副翻牌翻出 +30 DAYS (BETTER KEY)。",
        zone=6, trans_in="T5 runner（上一段 6-04+05 是出镜 A 段，13 颗珠子飞回第 2 行）", trans_out="T2 甩镜往左（下一段 6-07 是 B 页）",
        ev=[
            ("row3", "snap", "time#1", 0, 9, "s", "Time：第 3 行行名翻出 3. TIME，镜头对准第 3 行", None),
            ("bef", "appear", "before#1", 0, 7, "w:ten-to-seventeen-year#1", "Before：左凹位卷尺底座（h18）落位", "tape"),
            ("tape", "grow", "ten-to-seventeen-year#1", 0, 36, "w:road#1", "ten-to-seventeen-year：卷尺大幅拉长，BEFORE 主翻牌翻出 10–17 YEARS", None),
            ("road", "move", "road#1", 0, 13, "w:hit#1", "road：卷尺沿左槽铺展成带年份刻度的长路", None),
            ("hit", "appear", "hit#1", 0, 13, "w:opening#1", "finding a hit：卷尺最前端一小段标出切分线", None),
            ("open", "snap", "opening#1", 0, 13, "w:stretch#1", "opening：卷尺最前端一小段描红高亮", "stretch"),
            ("strch", "snap", "stretch#1", 0, 10, "s", "stretch：BEFORE 副翻牌翻出 HIT = OPENING STRETCH", None),
            ("now", "appear", "now#1", 0, 10, "w:30#1", "Now：右凹位 Calendar1 日历落位", "cal"),
            ("d30a", "grow", "30#1", 0, 20, "w:days#1", "30 days：日历翻到 30，NOW 主翻牌翻出 30 DAYS (1ST HIT)", None),
            ("hit1", "snap", "hit#2", 0, 13, "w:key#1", "first hit：001 小钥匙图标在日历旁打勾", None),
            ("bkey", "appear", "key#1", 0, 13, "w:30#2", "a better key：048 金钥匙图标在下方展开", None),
            ("d30b", "snap", "30#2", 0, 20, "s", "another 30：日历再翻 30，NOW 副翻牌翻出 +30 DAYS (BETTER KEY)", None),
        ]),
    "6-07": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 6-07（btier/B607.jsx，复用第 6 章翻牌记分板组件，前 3 行保持已填）。"
             "填第 4 行：行名翻出 4. IMPROVING THE KEY；BEFORE 左凹位小循环轨道落位，硬币掉进轨道转一圈，翻牌翻出 ANOTHER COSTLY LAB ROUND；"
             "NOW 右凹位升起 5-07 同款 001 预测位姿浮雕卡片，卡片下扇形散开 16 把小钥匙，主翻牌翻出 16 GUIDED DESIGNS；"
             "一根 1→15× 刻度尺游标推至约 15×，副翻牌翻出 ~15× TIGHTER GRIP。",
        zone=6, trans_in="T2 甩进（上一段 6-06 是 B 页）", trans_out="T2 甩镜往左（下一段 6-08 是 B 页）",
        ev=[
            ("row4", "snap", "improving#1", 0, 9, "w:key#1", "Improving：第 4 行行名翻出 4. IMPROVING THE KEY", None),
            ("focus4", "move", "key#1", 0, 7, "s", "the key：镜头下移对准第 4 行，左右凹位亮起", None),
            ("bef", "appear", "before#1", 0, 7, "w:change#1", "Before：左凹位小循环轨道落位", "loop4"),
            ("chg", "move", "change#1", 0, 13, "w:costly#1", "every change：硬币落进循环轨道起动", None),
            ("cost", "move", "costly#1", 0, 24, "w:round#1", "costly：硬币沿小循环轨道转满一圈，烧瓶小标亮起", None),
            ("rnd", "snap", "round#1", 0, 13, "s", "lab round：BEFORE 翻牌翻出 ANOTHER COSTLY LAB ROUND", None),
            ("now", "appear", "now#1", 0, 10, "w:picture#1", "Now：右凹位切入 001 位姿卡片槽", "now4"),
            ("pic", "grow", "picture#1", 0, 24, "w:key#2", "predicted picture：5-07 同款 001 浮雕位姿卡片升起", None),
            ("k1", "appear", "key#2", 0, 10, "w:sixteen#1", "the first key：卡片上 001 位姿高亮标注", None),
            ("n16", "grow", "sixteen#1", 0, 24, "w:designs#1", "sixteen：卡片下方扇形散开 16 把小钥匙", "fan16"),
            ("des", "snap", "designs#1", 0, 13, "w:grip#1", "designs：NOW 主翻牌翻出 16 GUIDED DESIGNS", None),
            ("grip", "appear", "grip#1", 0, 10, "w:fifteen#1", "the grip：右凹位下方伸出 1→15× 横向刻度尺", "ruler15"),
            ("n15", "move", "fifteen#1", 0, 36, "w:times#1", "about fifteen：刻度游标从 1× 推到约 15×", None),
            ("tight", "snap", "tighter#1", 0, 13, "s", "tighter：NOW 副翻牌翻出 ~15× TIGHTER GRIP（T7 轻抖）", None),
        ]),
    "6-08": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 6-08（btier/B608.jsx，复用第 6 章翻牌记分板组件，四行全部填满）。"
             "镜头后拉看整块记分板：BEFORE 与 NOW 两栏之间刻出的虚线槽由上至下亮起，旁侧 Caveat 手写批注 different studies；"
             "右栏四格翻牌依次轻轻翻一下（不闪光）呼应 scale and speed；Caveat 手写批注 not one race；"
             "最后记分板底部落下一块刻字引文牌：“cost- and time-efficient” — Ren et al. 2023。",
        zone=6, trans_in="T2 甩进（上一段 6-07 是 B 页）", trans_out="T2 甩镜往左（下一段 6-09 是 B 页）",
        ev=[
            ("wide", "move", "to#1", 0, 9, "w:pairs#1", "To be fair：镜头后拉展示四行填满的整块记分板", None),
            ("pairs", "appear", "pairs#1", 0, 10, "w:different#1", "these pairs：四组 BEFORE / NOW 对应行轻亮配对框", None),
            ("seam", "grow", "different#1", 0, 13, "w:studies#1", "different：两栏之间刻出的虚线槽由上至下亮起", "seam"),
            ("note1", "appear", "studies#1", 0, 6, "w:scale#1", "studies：虚线槽旁 Caveat 手写批注 different studies", None),
            ("scale", "snap", "scale#1", 0, 13, "w:speed#1", "scale：右栏第 1、2 格翻牌依次轻翻一下（不闪光）", "nowcol"),
            ("speed", "snap", "speed#1", 0, 13, "w:race#1", "speed：右栏第 3、4 格翻牌依次轻翻一下", None),
            ("race", "appear", "race#1", 0, 6, "w:side#2", "not one race：Caveat 手写批注 not one race", None),
            ("side", "move", "side#2", 0, 13, "s", "side by side：两栏轻微错拍，强调并非同场并跑", None),
            ("paper", "appear", "paper#1", 0, 10, "w:calls#1", "the paper：记分板底部引文槽口打开", "quote"),
            ("calls", "move", "calls#1", 0, 13, "w:cost#1", "calls the work：刻字引文牌从下方槽口滑出就位", None),
            ("cost", "snap", "cost#1", 0, 13, "w:time-efficient#1", "cost-：引文牌刻亮 cost-", None),
            ("timeef", "snap", "time-efficient#1", 0, 13, "s", "time-efficient：引文牌刻全 “cost- and time-efficient” — Ren et al. 2023（T7 轻抖）", None),
        ]),
    "6-09": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 6-09（btier/B609.jsx）。第 6 区主料杆向前延伸（注意本段音频首句从 further down the road 起）："
             "路边四个“可能的好处”磨砂半透明图标依次亮起（表示可能、尚未实测）：珠子堆（p42，Fewer failed molecules）、"
             "钞票（Lower costs）、小鼠（p43，Fewer animal tests）、废料桶（Less chemical waste）；"
             "随后插头与闪电图标（p44，Electricity cost）亮起代表算力代价；路尽头清晰亮起一粒胶囊和一个小人（New treatments for patients）。",
        zone=6, trans_in="T2 甩进（上一段 6-08 是 B 页）", trans_out="T2 甩镜往左（下一段 6-10 是 B 页）",
        ev=[
            ("road", "move", "further#1", 0, 9, "s", "further down the road：主料杆沿第 6 区向前延伸，镜头沿料杆前推", None),
            ("b1", "grow", "molecules#1", 0, 13, "w:lower#1", "Fewer failed molecules：磨砂半透明珠子堆（p42）亮起", "b1"),
            ("b2", "grow", "costs#1", 0, 13, "w:fewer#2", "lower costs：磨砂半透明钞票图标亮起", None),
            ("b3", "grow", "animal#1", 0, 13, "w:less#1", "fewer animal tests：磨砂半透明小鼠（p43）亮起", "b3"),
            ("b4", "grow", "chemical#1", 0, 13, "w:waste#1", "less chemical：磨砂半透明废料桶图标亮起", "b4"),
            ("b4l", "appear", "waste#1", 0, 9, "s", "waste：四个磨砂好处图标排齐并标出对应短标签", None),
            ("elec", "grow", "electricity#1", 0, 28, "w:too#1", "Computing costs electricity：路旁插头与闪电图标（p44）亮起，代表算力代价", "elec"),
            ("too", "appear", "too#1", 0, 10, "s", "too：标 Electricity cost", None),
            ("prize", "move", "prize#1", 0, 20, "s", "the real prize?：镜头沿料杆推到路尽头，尽头展位亮起带问号", None),
            ("treat", "grow", "treatments#1", 0, 13, "w:patients#1", "New treatments：路尽头一粒暖色胶囊清晰亮起", None),
            ("pat", "snap", "patients#1", 0, 13, "s", "for patients：胶囊旁小人清晰亮起，标 New treatments for patients", None),
        ]),
    "7-02": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 7-02（btier/B702.jsx）。第 1 块编号牌落到路上 048 吊牌旁，048 吊牌往前挪一步到 Cells 站插一面小旗；"
             "挂在 048 吊牌上的小挂锁弹开（public），旁边出现白色小人（anyone）；画面让位，一组肝癌细胞培养皿（p40）一变二、二变四，"
             "旁边正常肝细胞培养皿也展开；小鼠零件（p43）亮起；两块小牌（Plate）刻 ADME、selectivity 依次弹出；"
             "最后来源卡 Ren et al. 2023 出现，三张步骤卡同时打勾。",
        zone=7, trans_in="T5 runner（上一段 7-01 是出镜 A 段，1 号牌飞入）", trans_out="T2 甩镜往左（下一段 7-03 是 B 页）",
        ev=[
            ("p1", "appear", "one#1", 0, 7, "w:walk#1", "One：1 号编号牌落到路旁", None),
            ("walk", "move", "walk#1", 0, 13, "w:048#1", "walk：048 吊牌从 Cells 站起动往前滑", None),
            ("tag48", "snap", "048#1", 0, 13, "s", "048 further：048 吊牌挪一步到位，Cells 站插一面小旗", "tag48"),
            ("unlock", "snap", "public#1", 0, 9, "w:anyone#1", "public：吊牌上挂的小挂锁弹开", None),
            ("anyone", "appear", "anyone#1", 0, 13, "s", "anyone could try：路旁出现几个白色小人剪影", None),
            ("clear", "move", "test#1", 0, 9, "w:cancer#1", "Test：路往左让位，培养皿组进来", None),
            ("dishes", "grow", "cancer#1", 0, 13, "w:normal#1", "liver cancer cells：肝癌细胞培养皿一变二、二变四", "dishes"),
            ("norm", "grow", "normal#1", 0, 13, "w:cells#2", "normal liver cells：正常肝细胞培养皿也亮起展开", None),
            ("dish_l", "appear", "cells#2", 0, 9, "w:animals#1", "cells：两排培养皿分别标上 cancer / normal", None),
            ("mouse", "grow", "animals#1", 0, 13, "w:check#1", "animals：小鼠零件落位亮起", "mouse"),
            ("chk", "appear", "check#1", 0, 9, "w:handles#1", "check：小牌槽位出现", None),
            ("adme", "eject", "handles#1", 0, 13, "w:else#1", "how the body handles it：第一块小牌弹出，刻 ADME", "cards"),
            ("sel", "eject", "else#1", 0, 13, "w:hits#1", "what else：第二块小牌弹出，刻 selectivity", None),
            ("hits", "snap", "hits#1", 0, 9, "s", "hits：两块小牌锁定高亮", None),
            ("src", "appear", "authors#1", 0, 9, "w:listed#1", "The authors：Ren et al. 2023 出处牌落位", None),
            ("ticks", "snap", "listed#1", 0, 13, "w:steps#1", "already listed：三张步骤卡同时打勾", None),
            ("steps", "appear", "steps#1", 0, 9, "s", "these steps：批注 next steps", None),
        ]),
    "7-03": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 7-03（btier/B703.jsx）。2 号牌落位；蓝色预测 CDK20 模型转正（AlphaFold DB v6）；"
             "同样外形的磨砂幽灵外壳从上方慢慢落下罩在模型上，轮廓对不准处留一道缝，标 measured structure? 与红色问号并缓慢半透明闪烁；"
             "模型与外壳让到左边，一排金钥匙与几把灰色打叉的失败钥匙沿料杆依次流回 Chemistry42 芯片，芯片内部小轨道转一圈开启下一轮。",
        zone=7, trans_in="T2 甩进（上一段 7-02 是 B 页）", trans_out="T2 甩镜往左（下一段 7-04 是 B 页）",
        ev=[
            ("p2", "appear", "two#1", 0, 7, "w:alphafold#1", "Two：2 号编号牌落位", None),
            ("af", "grow", "alphafold#1", 0, 13, "w:model#1", "AlphaFold：蓝色预测 CDK20 模型落位转正", "af"),
            ("aflbl", "appear", "model#1", 0, 9, "w:lab-measured#1", "model：标 predicted model (AlphaFold DB v6)", None),
            ("ghost_in", "appear", "lab-measured#1", 0, 10, "w:structure#1", "lab-measured：磨砂幽灵外壳在上方现身", None),
            ("ghost", "move", "structure#1", 0, 44, "w:once#1", "structure：幽灵外壳慢慢落下罩在模型上，对不准处留一道缝", "ghost"),
            ("once", "appear", "once#1", 0, 9, "w:exists#1", "once：外壳半透明慢闪，标 measured structure?", None),
            ("q", "appear", "exists#1", 0, 9, "s", "exists：缝隙旁出现红色问号", None),
            ("shift", "move", "feed#1", 0, 13, "w:result#1", "feed：模型与外壳左移，Chemistry42 芯片与料杆进来", None),
            ("keys", "move", "result#1", 0, 28, "w:failures#1", "every result：一排金钥匙沿料杆流回 Chemistry42 芯片", "keys"),
            ("fail", "move", "failures#1", 0, 30, "w:back#1", "failures：几把灰色打叉的钥匙也一起流回", "fail"),
            ("back", "move", "back#1", 0, 13, "w:round#1", "back into：所有钥匙汇入芯片入口", None),
            ("loop", "snap", "round#1", 0, 13, "s", "next round：芯片内小轨道转一圈，准备下一轮", None),
        ]),
    "7-04": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 7-04（btier/B704.jsx）。3 号牌落位；两条并排跑道（h22）和两块秒表亮起；"
             "上道刻 AI route，下道刻 classic route；起跑线上三块小牌 same target、same budget、same definition of a hit 依次翻起，"
             "每翻一块两道上各亮一个相同图标；两块小吊牌起跑，两块秒表开始走，终点线上一个红色问号。",
        zone=7, trans_in="T2 甩进（上一段 7-03 是 B 页）", trans_out="T5 runner（下一段接 AI 插段 / 8-01 出镜 C 段）",
        ev=[
            ("p3", "appear", "three#1", 0, 7, "w:race#1", "Three：3 号编号牌落位", None),
            ("tracks", "grow", "race#1", 0, 13, "s", "race them：两条并排跑道（h22）与两块秒表亮起", "tracks"),
            ("ai", "appear", "ai#1", 0, 10, "w:classic#1", "AI route：上道刻字 AI route，蓝标就位", None),
            ("classic", "appear", "classic#1", 0, 10, "w:route#2", "classic：下道刻字 classic route，骨白标就位", None),
            ("clbl", "appear", "route#2", 0, 9, "w:target#1", "route：两条跑道起跑线对齐框亮起", None),
            ("t1", "snap", "target#1", 0, 13, "w:budget#1", "same target：第一块小牌翻起，两道各亮一个靶标", "conds"),
            ("t2", "snap", "budget#1", 0, 13, "w:definition#1", "same budget：第二块小牌翻起，两道各亮一个预算标", None),
            ("t3", "snap", "definition#1", 0, 13, "w:hit#1", "same definition：第三块小牌翻起，两道各亮一个命中标", None),
            ("t3_lbl", "appear", "hit#1", 0, 9, "s", "hit：三块同条件牌锁齐高亮", None),
            ("ready", "move", "know#1", 0, 13, "w:faster#1", "know：两块小吊牌在起跑线蓄势，秒表清零", None),
            ("run", "move", "faster#1", 0, 30, "w:ai#2", "faster：两块吊牌沿跑道起跑，两块秒表开始走", "race"),
            ("q", "appear", "is#1", 0, 10, "s", "is：终点线上红色问号亮起", None),
        ]),
    "8-02": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 8-02（btier/B802.jsx）。目标牌 1 落位带红色问号，随后让到左上角，主料杆和路展开；"
             "路的第一段上挂起四个工具节点：PandaOmics 芯片、AlphaFold 芯片、Chemistry42 芯片、打分排名条（不用圆表盘）。"
             "Picking a target：PandaOmics 亮并闪出 Top 20 牌；Predicting the lock's shape：AlphaFold 亮并升起蓝色 CDK20；"
             "Designing new keys：Chemistry42 亮并吐出一把金钥匙；ranking：排名刻度条游标推动选中要合成的钥匙。"
             "最后目标牌 1 回到画面中央，刻上绿色勾（T7），加小字 for this case。",
        zone=8, trans_in="T5 runner（上一段 8-01 是出镜 C 段）", trans_out="T2 甩镜往左（下一段 8-03 是 B 页）",
        ev=[
            ("goal1", "appear", "how#1", 0, 7, "w:computer-aided#1", "How：目标牌 1 落位，带红色问号", None),
            ("road", "grow", "computer-aided#1", 0, 13, "w:methods#1", "computer-aided：主料杆与路在下方展开", None),
            ("badge", "move", "methods#1", 0, 13, "w:scientists#1", "methods：目标牌 1 让到左上角", None),
            ("sci", "appear", "scientists#1", 0, 9, "w:find#1", "scientists：科学家路标在起点亮起", None),
            ("find", "appear", "find#1", 0, 10, "w:assess#1", "find：寻找位亮起", "road"),
            ("assess", "appear", "assess#1", 0, 10, "w:candidates#1", "assess：评估位亮起", None),
            ("cand", "grow", "candidates#1", 0, 13, "s", "candidates：小分子候选插头沿路排开", None),
            ("case_in", "move", "case#1", 0, 13, "w:points#1", "In this case：路的第一段推近居中", None),
            ("pts", "grow", "points#1", 0, 24, "s", "four points：四个工具节点（PandaOmics、AlphaFold、Chemistry42、排名条）挂上路", "pts"),
            ("panda", "snap", "target#1", 0, 13, "w:data#1", "target：PandaOmics 芯片亮，闪出 Top 20 牌", "panda"),
            ("data", "appear", "data#1", 0, 9, "s", "data：标 Top 20 / CDK20 数据牌", None),
            ("af", "snap", "predicting#1", 0, 10, "w:lock's#1", "Predicting：AlphaFold 芯片亮", "af"),
            ("lock_in", "appear", "lock's#1", 0, 9, "w:shape#1", "lock's：蓝色支架升起", None),
            ("shape", "grow", "shape#1", 0, 30, "s", "shape：蓝色 CDK20 模型在芯片上方升起", None),
            ("chem42", "snap", "designing#1", 0, 10, "w:keys#1", "Designing：Chemistry42 芯片亮", "chem42"),
            ("key", "eject", "keys#1", 0, 13, "s", "keys：芯片吐出一把金钥匙", None),
            ("rank", "grow", "ranking#1", 0, 13, "w:make#1", "ranking：打分排名条长出，游标推向高分端", "rank"),
            ("make", "snap", "make#1", 0, 13, "s", "make：选出靠前的两把钥匙高亮", None),
            ("focus", "move", "first#1", 0, 30, "w:objective#1", "first：四个工具收拢连线，目标牌 1 回到中间", None),
            ("obj", "appear", "objective#1", 0, 10, "w:met#1", "objective：目标牌 1 框高亮待命", "goal1"),
            ("met", "snap", "met#1", 0, 13, "w:case#2", "met：目标牌 1 刻出绿色勾，T7 一抖", None),
            ("sub", "appear", "case#2", 0, 9, "s", "for this case：目标牌下方刻小字 for this case", None),
        ]),
}


def until(u):
    if u is None:
        return None
    if u == "s":
        return {"sentence_end": True}
    k, v = u.split(":", 1)
    return {"word": v} if k == "w" else {"dur": int(v)}


def build(seg):
    P = PAGES[seg]
    evs = []
    for (i, verb, w, off, lead, u, means, g) in P["ev"]:
        e = {"id": i, "obj": i, "verb": verb, "at": {"word": w, "off": off}, "lead": lead, "means": means, "tool": "remotion",
             "guide": {"kind": "focus", "target": [g]} if g else {"kind": "none"}}
        if u:
            e["until"] = until(u)
        evs.append(e)
    doc = {"schema": "cdk20.events/1", "group": seg, "tool": "remotion", "note": P["note"], "tier": "B", "zone": P["zone"],
           "trans_in": P["trans_in"], "trans_out": P["trans_out"], "holds": [], "events": evs}
    out = HERE / "events" / f"{seg}.json"
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("→", out)


if __name__ == "__main__":
    for s in sys.argv[1:] or list(PAGES):
        build(s)
