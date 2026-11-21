```python
    "7-02": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 7-02（页面 btier/B702.jsx）。第 1 块编号牌落到路上 048 吊牌旁，048 吊牌往前挪一步到 Cells 站插一面小旗；"
             "挂在 048 吊牌上的小挂锁弹开（public），旁边出现白色小人（anyone）；画面让位，一组肝癌细胞培养皿（p40）一变二、二变四，"
             "旁边正常肝细胞培养皿也展开；小鼠零件（p43）亮起；两块小牌（Plate）刻 ADME、selectivity 依次弹出；"
             "最后来源卡 Ren et al. 2023 出现，三张步进卡同时打勾。",
        zone=7, trans_in="T5 runner（上一段 7-01 是出镜 A 段，1 号牌飞入）", trans_out="T2 甩镜往左（下一段 7-03 是 B 页）",
        ev=[
            ("p1", "appear", "one#1", 0, 7, "w:048#1", "One：1 号编号牌落到路旁", None),
            ("walk", "move", "048#1", 0, 38, "s", "walk 048 further：048 吊牌往前挪一步，Cells 站插一面小旗", None),
            ("unlock", "snap", "public#1", 0, 9, "w:anyone#1", "public：吊牌上挂的小挂锁弹开", None),
            ("anyone", "appear", "try#1", 0, 13, "s", "anyone could try：路旁出现几个白色小人剪影", None),
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
        note="HKBU SCIE1007 课程作业的科普视频：B 档 7-03（页面 btier/B703.jsx）。2 号牌落位；蓝色预测 CDK20 模型转正（AlphaFold DB v6）；"
             "同样外形的磨砂幽灵外壳从上方慢慢落下罩在模型上，轮廓对不准处留一道缝，标 measured structure? 与红色问号并缓慢半透明闪烁；"
             "模型与外壳让到左边，一排金钥匙与几把灰色打叉的失败钥匙沿料杆依次流回 Chemistry42 芯片，芯片内部小轨道转一圈开启下一轮。",
        zone=7, trans_in="T2 甩进（上一段 7-02 是 B 页）", trans_out="T2 甩镜往左（下一段 7-04 是 B 页）",
        ev=[
            ("p2", "appear", "two#1", 0, 7, "w:alphafold#1", "Two：2 号编号牌落位", None),
            ("af", "grow", "alphafold#1", 0, 13, "w:model#1", "AlphaFold：蓝色预测 CDK20 模型落位转正", "af"),
            ("aflbl", "appear", "model#1", 0, 9, "w:lab-measured#1", "model：标 predicted model (AlphaFold DB)", None),
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
        note="HKBU SCIE1007 课程作业的科普视频：B 档 7-04（页面 btier/B704.jsx）。3 号牌落位；两条并排跑道（h22）和两块秒表亮起；"
             "上道刻 AI route，下道刻 classic route；起跑线上三块小牌 same target、same budget、same definition of a hit 依次翻起，"
             "每翻一块两道上各亮一个相同图标；两块小吊牌起跑，两块秒表开始走，终点线上一个红色问号。",
        zone=7, trans_in="T2 甩进（上一段 7-03 是 B 页）", trans_out="T5 runner（下一段 8-01 是出镜 C 段）",
        ev=[
            ("p3", "appear", "three#1", 0, 7, "w:race#1", "Three：3 号编号牌落位", None),
            ("tracks", "grow", "race#1", 0, 13, "s", "race them：两条并排跑道（h22）与两块秒表亮起", "tracks"),
            ("ai", "appear", "ai#1", 0, 10, "w:classic#1", "AI route：上道刻字 AI route，蓝标就位", None),
            ("classic", "appear", "classic#1", 0, 10, "w:route#2", "classic：下道刻字 classic route，骨白标就位", None),
            ("clbl", "appear", "route#2", 0, 9, "w:target#1", "route：两条跑道起跑线对齐对齐框", None),
            ("t1", "snap", "target#1", 0, 13, "w:budget#1", "same target：第一块小牌翻起，两道各亮一个靶标", "conds"),
            ("t2", "snap", "budget#1", 0, 13, "w:definition#1", "same budget：第二块小牌翻起，两道各亮一个预算标", None),
            ("t3", "snap", "definition#1", 0, 13, "w:hit#1", "same definition：第三块小牌翻起，两道各亮一个命中标", None),
            ("t3_lbl", "appear", "hit#1", 0, 9, "s", "hit：三块同条件牌锁齐高亮", None),
            ("ready", "move", "know#1", 0, 13, "w:faster#1", "know：两块小吊牌在起跑线蓄势，秒表清零", None),
            ("run", "move", "faster#1", 0, 30, "w:is#1", "faster：两块吊牌沿跑道起跑，两块秒表开始走", "race"),
            ("q", "appear", "is#1", 0, 10, "s", "is：终点线上红色问号亮起", None),
        ]),
    "8-02": dict(
        note="HKBU SCIE1007 课程作业的科普视频：B 档 8-02（页面 btier/B802.jsx）。目标牌 1 落位带红色问号，随后让到左上角，主料杆和路展开；"
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
            ("obj", "appear", "objective#1", 0, 10, "w:met#1", "objective：目标牌 1 框高亮待命", None),
            ("met", "snap", "met#1", 0, 13, "w:case#2", "met：目标牌 1 刻出绿色勾，T7 一抖", None),
            ("sub", "appear", "case#2", 0, 9, "s", "for this case：目标牌下方刻小字 for this case", None),
        ]),
```