# 交接给 Codex：零件库精模（只做建模，不碰内容）

HKBU SCIE1007 课程作业的科普视频。这是本科小组作业：一条英文科普片。全片画面是一整块"拼装模型大板"（高达模型水口板那种：外框、料杆、零件挂在浇口上）。零件由 `镜头设计_v3/inserts/kit_parts.py` 里的函数在 Blender 里程序化建模。现在很多零件建得太粗，这一步只把零件的**造型做精**。

写于 2026-11-19 01:30（韩国时间）。总管：Claude。

## 你的活

新建 `镜头设计_v3/inserts/kit_parts_hd.py`，把下面这些零件重新建模，做得像真的模型套件零件：倒角、厚度、分件线、细节（螺丝孔、刻线、凹槽）、比例对、轮廓一眼认得出。

按优先级：
1. `p03_person`（小人）、`p22_key`（钥匙）、`p21_lock`（锁）、`p34_flask`（烧瓶）
2. `p43_mouse`（小鼠）、`p44_plug_bin`（插头、废料桶）、`p14_buildings`（楼）、`p09_iv_bag`（输液袋）
3. `p10_calendar`、`p11_bill`（钞票）、`p13_chip`（芯片）、`p27_data_disks`（数据盘）、`p46_newspaper`、`p12_medal`、`p15_sample_tube`、`p17_paper_book`、`p18_loupe_checklist`

**不许碰**的零件：`p19_cdk20`、`p20_pocket`、`p24_atp`、`p29_cdk20_unknown`、`p30_aa_chain`、`p31_tail`、`p39_molecules`、`p04_liver`、`p05_lung_gut`，以及任何分子、蛋白、器官。这些是内容，不改。

## 接口（必须兼容）

- 先读 `镜头设计_v3/inserts/kit_README.md` 和 `kit_parts.py`。
- 每个新函数和旧函数**同名、同参数、同返回**（返回零件根物体），`kit_parts_hd.py` 里 `from kit_parts import *` 后覆盖这些函数即可，旧板子换成 `import kit_parts_hd as KP` 就能直接用。
- 零件不超出自己那一格 ±26 × ±16 mm，浇口位置和旧版一致（零件要能挂在料杆上）。
- 材质只用 `Kit` 里现成的三类材质，颜色归类不变。外观要亮面塑料（clearcoat、低粗糙度），不要哑光。
- **不改** `kit_parts.py` 和其他任何现有文件。

## 交付

1. `kit_parts_hd.py`
2. 对比图：每个零件一张，左旧右新，同灯同机位。放 `G:/cdk20/work/kit_hd/compare_<零件名>.png`，再拼一张总表 `G:/cdk20/work/kit_hd/compare_all.png`。
3. 报告 `镜头设计_v3/inserts/kit_hd_报告.md`（中文）：每个零件改了什么、自己看对比图觉得是否更好、有没有放弃的。
4. git 提交并推送：只 `git add` `kit_parts_hd.py` 和 `kit_hd_报告.md`，提交说明中文。绝不 `git add -A` 或 `git add .`，不提交图片和 .blend。

## 环境和限制

- Blender：`G:/software/blender-5.3/blender.exe`，后台模式 `-b --factory-startup -P 脚本`。
- 显卡：先看 `D:/。hkbu/molecular science/_env/queue/` 下有没有 `GPU_HOLD` 或 `GPU_PAUSED` 文件（不带 .off），有就停下等。同时最多 1 个你的 Blender 进程。对比图用 Cycles 64 采样、1600×900 就够。
- 可以用现成的免费 Blender 插件或几何节点资源帮忙建模（Bool Tool、Extra Objects 等），用了就在报告里写名字和许可。
- 不要删除任何文件或目录（钩子会拦）。临时文件放 `G:/cdk20/work/kit_hd/tmp/`。
- 项目路径里有全角句号，命令里整段加引号。
