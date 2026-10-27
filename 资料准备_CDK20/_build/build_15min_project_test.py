from pathlib import Path
import json,re,hashlib,zipfile,sys,textwrap

BASE=Path(__file__).resolve().parent.parent
OLD=BASE/'视频分镜_DS测试版_20261018'
SRC=BASE/'视频内容稿/教师要求补齐版'
OUT=BASE/'十五分钟项目视频测试剧本_20261018';OUT.mkdir(exist_ok=True)
original=json.loads((OLD/'02_完整分镜数据.json').read_text(encoding='utf-8'))
sys.path.insert(0,str(BASE/'_build/script_dependencies'))
from opencc import OpenCC
cc=OpenCC('s2t');tc=lambda s:cc.convert(s).replace('爲','為').replace('纔','才').replace('覈','核')

# Each entry: paragraph / primary medium / concrete 3D-2D interaction / camera and handoff.
design='''P01|3D主导|抽象候选线框悬在深墨空间中；相机越过它，才发现远处有许多同类设计和有限的测试位置；问题文字沿线框的投影边缘出现|贴近→掠过→拉开；不先放封面再黑场切正文。同一设计锚点进入下一段
P02|3D＋2D嵌入|设计对象在空间中前进，它的轨迹在底面变成Design、Test、Improve路线；沿轨迹继续显露Benefits与Evidence，而非依次弹出五张卡片|保持前进方向，路线围着同一对象展开；信息出场跟随对应句子
P03|2D解释，3D承接|空间路径压成简洁工作关系：AI、其他计算、研究者、实验共同围绕Starting point；再从Starting point位置抬起靶点的轮廓|透视逐步减弱→正视关系→从同一锚点恢复深度；不要重新摆一屏方框
P04|2D定位→3D抽象空间|先用清楚的二维人体／肝脏定位说明primary liver cancer，肝脏轮廓扩成画面边界；边界内的抽象细胞空间显露一个待研究组件|沿肝脏轮廓推进；用匹配轮廓交接尺度，不假装是真实显微影像
P05|2D主导|蛋白轮廓和小分子设计的投影并置，Target与Candidate分别贴在各自对象上；标签随对象换位，仍能看出二者不同|短距离侧移，不同时转动两个对象；最后跟Target标签进入证据来源
P06|2D证据关系＋3D底层|已有生物学证据与疾病数据以两条清楚路径汇入CDK20；三维目标始终在后方，证据落在它的前景平面上|沿两条路径汇合方向推进；不显示虚构数据库界面或AI自动成功章
P07|2D关系展开|CDK20周围显露其他因素的概念节点，单一因果箭头退去；镜头再收回到“值得进一步测试的相互作用”这一具体问题|从局部拉远再沿原路径回到目标；不要让所有节点同时飞动
P08|3D主导|同一蛋白轮廓抬升成有遮挡与口袋关系的三维示意，小分子仍停在旁边；视角改变揭示两种结构信息的差别|侧掠凹口→较稳定的斜视角；不能只把钥匙塞入锁孔就当化学解释
P09|2D方法→3D输出|序列、相关序列与学到的结构规律以三个二维输入进入预测位置；同一位置显露预测三维模型；实验测定的位置保持独立|镜头沿信息流接近模型，再停住让Predicted限定可读；不是折叠过程动画
P10|2D主导，3D并置|序列带沿模型旁边展开，二维顺序与三维形状各占一个明确层；关联线连接信息，不把序列带按物理轨迹折成蛋白|先跟序列带横移，再转回同一模型；不制造真实CDK20氨基酸序列
P11|3D检视＋2D判断|模型一端的不确定区域以示意透明度区分；人工选择线在二维覆盖层中圈定它，区域退到旁边Excluded位置|贴近末端→人工选择→回到剩余模型；没有置信数据时不伪造pLDDT色图
P12|2D比较主导|剩余模型的投影与结构引导设计路线相连；另一侧只标本案例起始流程未使用实验结构；新分子的空位置接在后面|相机沿路线前移但不立刻填满空位，让下一个问题自然出现
P13|3D候选生成＋2D约束|空设计位置先形成约束边界，再从该位置长出一组抽象候选；候选的投影保留生成关系；Chemistry42只作小来源标注|围绕生成核心小弧线移动；候选必须从既有对象和规则边界产生，不是粒子凭空爆开
P14|2D性质解释主导|一个3D候选的轮廓展成三条可读性质关系：相互作用、能否合成、其他性质；不同候选在这些关系中显露取舍|从候选表面展开信息→短暂压平→回到候选；不要用虚构分数雷达图
P15|3D＋2D概念|跟随一个设计的线框，旁边的Hypothesis标签由它自己的投影形成；拉远看到多个可能性；实体样品位置仍为空|主体稳定、背景拉开；生成设计与制造物质始终是不同状态
P16|3D姿态主导，2D评分解释|口袋固定，依次展示几个示意预测姿态；姿态投影在侧面形成定性排序；结果保持Predicted，不转换成结合证据|绕口袋换角度，姿态之间明确是备选示意；不播放被误认为真实进入口袋的轨迹
P17|2D协作＋3D流转|已有候选沿研究路径经过AI、其他计算和人的判断，才进入实验区域；工作组件从路径的投影层显露，不做全屏流程图|保持候选的世界坐标连续；镜头跟对象穿过各层，解释时留短暂稳定构图
P18|2D数字主导，3D规模支撑|候选群先在空间显露规模，再压成8,918→54→7的三阶段关系；七个选中位置从二维队列重新抬进待测试空间|拉远揭示规模→压平读数字→跟七个位置前移；数字至少各自清楚停留一次
P19|2D主导|Generated、Prioritised、Selected for testing分别贴在三个阶段的既有对象上；七个仅显示Selected，实验结果区不提前点亮|沿同一三个阶段依次查看；不要给其余设计盖失败章
P20|2D解释＋局部glitch|有限资源位置与候选队列并置；8,918÷7的算式旁显示Not a speed-up measure，只有算式边缘轻微错位后恢复，候选路径不断|镜头不震动；局部glitch约0.12秒，仅强调错误推断被纠正，不影响数字阅读
P21|2D比较主导|两条路线从同一比较边界展开，都拥有知识、计算和判断；相机随后回到它们都需要的实验位置|左右关系从先前空白比较区产生；不能把传统方法做成蒙眼人或瞎猜
P22|2D实验结果主导，3D辅助|七个测试位置进入Tested状态，其中一个概念命中物出现Binding hit；预测线框与实验结果标记保持不同样式|从对象移动过渡到稳定证据呈现；不画假实验曲线，不推断其余六个全部无效
P23|2D时间线主导|30 days仅跨Target selection与First binding hit；时间线右边继续延伸到后续优化，30天范围的右边界固定|沿真实端点横移；绝不把“30天”做成从疾病到患者治愈的一条完成进度条
P24|2D问题区分→3D对象承接|结合结果保持不变，Function区域从同一对象的另一侧显露；“Binding ≠ function”只在旁白解释时短暂出现|两个观察角度之间平滑侧移；不让结合动作直接导致细胞死亡
P25|2D证据主导|两个测量窗口并置：Binding有证据，Enzyme function仍为Weak initial inhibition；它们共同指向下一步改进，不是一个成功一个全盘失败|保持清楚的两层关系；窗口来自上段对象的两个投影，不突然开全新页面
P26|3D反馈主导＋2D数字|实验信息沿既有路径回到设计区域，核心局部重组；后续16 proposed→6 synthesised数字附在这一轮路径；048以独立身份出现|镜头沿反馈弧线回转，不黑场重启；首轮命中物和后续048不是同一结构变身
P27|2D证据分层主导|048旁分开显露Enzyme inhibition与Reduced Huh7 viability两层观察；患者层保持“本研究未提供”的边界|证据层逐步展开，细胞窗口只作明确标注的示意；不造患者疗效或单一靶点因果动画
P28|3D空间比较＋2D限定|048与目标CDK20、其他待检验蛋白保持空间区别；相机拉开后显露细胞模型边界与整个人体边界不是一回事|沿不同空间层移动；其他靶点用未知状态，不伪造激酶面板或安全性结论
P29|3D反馈回路→2D总结|已走过的路径闭成Design→Test→Learn→Revise回路；未完成的选择性、体内表现与毒性评价仍在开放出口|镜头拉开真实已有空间，不在此另造一套流程图；结尾跟开放出口进入收益评价
P30|2D收益分类主导|回路压平后，把结构支持、提出设计、实验确认三项已观察贡献和远端潜在收益分开；不同状态由线型和文字共同表达|相机侧后退揭示类别；不能把潜在收益和已观察结果一起变绿打勾
P31|2D条件推论＋3D资源|条件分支从既有资源位置伸向Validation与Optimisation，比较基线位置仍空着；Achievement与Measured advantage不同|镜头沿If/May路径移动，不能把待测收益演成已经节省金钱
P32|3D资源分配主导|有限实验位置不变，设计在其间重排，仍保留多个不同探索方向；几何动作表达更好的决策而不只是大量删除|镜头在有限位置间穿行；没有“只剩一个就赢了”的英雄特写
P33|2D主导|资源路径展开为Health、Cost、Animal welfare三条潜在收益；标签始终带Potential或Not measured here|信息从既有资源路径产生；不要放康复患者、便宜药价或已减少动物数量的画面
P34|2D资源比较主导＋3D物体锚点|计算电力与实验材料／废物两条资源路径一起进入Same research outcome比较边界；没有净收益数值|用相同锚点把两部分放进同一比较范围；不靠绿色叶子和电力图标暗示已经环保
P35|2D研究设计主导|同一比较框架显露Same target、Similar resources、Same success criteria；随后接上实验反馈与多性质评价|一个框架依次展开条件，不逐条换成三页建议；标Proposed next study
P36|2D来源主导，3D承载|沿已有证据路径查看原始研究／补充材料、方法、综述、书章节；来源名称贴在对应证据上，而非铺满论文封面|镜头沿证据用途浏览；平台团队与独立比较不混同，S07仍标Abstract checked
P37|2D新闻识读主导|示例标题AI discovered a drug?贴着同一证据路径进入；Prediction、Lab hit、Cells、Patients各有位置，指示器只到本案例证据层|局部标题边缘可短促错位一次再恢复，不整屏glitch；明确示例标题而非真实媒体截图
P38|3D主导，2D收束|镜头回到开场抽象设计与路径；问号不消失，只多了实验支撑的起点；最后保留A better-directed search和开放的后续研究方向|回到相似但不完全重复的构图；镜头、对象与音乐共同减速，不以药片或Approved结束'''
visual={}
for row in design.splitlines():
 parts=row.split('|');assert len(parts)==4;visual[parts[0]]=parts[1:]

# Sentence-aligned Chinese translations for subtitle preparation. These clarify segmentation,
# not change the scientific script. Final cue-internal timing must be checked against narration.
zh='''P01|一个分子还没做出来，我们能先预测它值不值得测试吗？|这个问题很重要，因为电脑里有希望的设计，仍要变成真实的物质。|研究者得想办法合成它、做出样品，再测试它的实际作用。|我们很难给每个可能的设计同样多的关注。
P02|AI提供一种可能：利用已有数据中学到的规律，提出值得探索的设计。|但提出一个结构，还不等于得到实验确认的命中物。|我们会追踪一项肝癌研究中的设计、测试和改进，再问AI贡献了什么、哪些收益只是潜力，以及还需要什么证据。
P03|我们不是在问电脑能否独自完成药物研发。|我们要问，算法能否帮助研究者找到更有用的起点。|但在讨论怎样设计分子前，得先知道希望它做什么。
P04|本案例研究肝细胞癌，简称HCC，是成人原发性肝癌最常见的类型。|原发性表示癌症从肝脏起始。|我们不覆盖所有癌症或所有治疗。|我们聚焦一个早期任务：寻找可能影响CDK20蛋白的分子。
P05|蛋白是细胞内的工作组件之一。|研究者选定希望分子作用的蛋白时，称它为靶点。|靶点和候选分子不是同一件事。|CDK20是希望影响的对象，候选物则是准备测试的化学设计。
P06|CDK20并不是因为被AI选中，才突然有研究意义。|较早研究已发现它与HCC有关，并研究改变它的活动或表达后，实验模型会怎样变化。|2023年研究利用疾病数据分析安排靶点优先级，再结合已有生物学证据选择CDK20。
P07|这不表示CDK20是肝癌唯一原因，也不证明抑制它能治疗患者。|它提出一个具体问题：能否找到与靶点作用、值得继续研究的分子？|靶点名称让任务更明确。|但名字本身不能告诉我们分子该是什么形状。
P08|分子在三维空间中相互作用。|有用的设计不只要在纸上好看，还要与靶点形成合适的相互作用。|蛋白形状能帮助研究者判断小分子可能在哪里、怎样结合。|这里要区分两种结构：靶点蛋白的形状，与正在设计的分子结构。
P09|团队使用AlphaFold数据库里的CDK20预测结构。|简单说，AlphaFold利用蛋白序列、相关序列信息和已知结构中学到的规律，预测三维模型。|这不同于实验测定结构。|输出是预测，不是蛋白的直接照片。
P10|序列是组成蛋白的基本单位的排列顺序。|知道顺序，与知道折叠后的形状，是不同的信息。|结构预测帮助连接两者。|研究者不是让模型发现疾病或发明CDK20。|他们利用结构信息，提出更具体的化学问题。
P11|研究者也检查了模型的不确定性。|继续设计前，他们移除了末端一个低置信度区域。|我们不必记住它的位置。|关键是模型没有消除判断的必要。|研究者仍要决定，哪些信息足够有用，能进入下一步。
P12|团队在起始流程里没有实验测定的CDK20结构，预测结构帮助他们开展结构引导设计。|这是具体贡献。|但它没有精确说明，这条路线比所有替代方案节省多少时间。|更重要的是，知道靶点形状后仍有大问题：该尝试什么新分子？
P13|这里，分子生成进入故事。|生成模型不只给现成分子排序，还能提出候选结构。|它从化学数据学习规律，结合设计信息与评价要求探索可能性。|本研究使用Chemistry42平台支持这项工作。
P14|这不只是形状配对游戏。|化学相互作用同样重要，研究者也需要真正能做出、能研究的结构。|一个设计可能在某方面有希望，在另一方面不合适。|所以提出和评价多个结构必须连接起来，而不是机器宣布一个完美答案。
P15|可以把它理解为提出化学假设。|假设说，这种结构可能有值得测试的性质。|它没有说，这就是唯一正确的药物。|许多不同结构都可能与靶点作用，各有优点和不足。|而且，生成设计不等于制造物质。
P16|团队接着用计算评价，包括分子对接。|对接探索分子在靶点口袋里的可能姿态，帮助判断优先考虑哪些设计。|预测姿态和分数是线索，不是真实结合的证明。|电脑里看起来合适的设计，仍要接受实验检验。
P17|首轮设计中，算法在实验前就有贡献，但没有取代实验室。|AI提供结构预测与新建议。|其他计算帮助评价。|研究者结合化学与生物学判断，决定做什么。|有趣的问题是，这种协作能否把大量可能性变成有用的实验起点。
P18|首轮团队生成了8,918个结构。|他们没有把全部结构都合成出来。|通过计算评价、对接与聚类，他们优先考虑54个，再选7个合成测试。|聚类整理相关设计，而不是把每个建议当成完全独立的对象。
P19|这些数字表示不同阶段，不是不同成功指标。|8,918是生成结构。|54是优先候选。|7是选中的实验对象。|选了7个，不表示得到7种成功药物，甚至不表示7个都是确认命中物。|选择说明研究者准备查什么，不说明实验最终会找到什么。
P20|这里，效率的潜在价值变具体了。|合成与测试分子需要资源。|更好的建议，可能帮助研究者把资源用在有用的实验和后续工作。|但不能用8,918除以7，就当作提速倍数。|没有人证明，一条可比的替代路线必须合成所有生成结构。
P21|传统发现也不是盲目猜测。|它同样使用已有知识、计算与专家判断。|公平的问题是，相同可比条件下，AI路线能否产生更有用的结果。|但比较前，团队先要回答更基本的问题：选中的分子真的结合CDK20了吗？
P22|实验确实找到了结合命中物：在报告条件下，表现出与CDK20结合的分子。|这很重要，故事已经超出计算评分。|团队做出了分子，也得到实验结果。|预测推进成了现实中可以继续调查的对象。
P23|论文报告，从靶点选择到首次实验确认的结合命中物，用了30天。|这就是亮眼数字对应的里程碑。|它不是30天得到批准药物，也不包含全部后续优化。|这个时间也不表示团队在30天内从零搭建数据资源与AI平台。
P24|因此可以说，这条流程在报告的较短时间内取得早期结果。|但还不能说它比另一条路线快多少倍。|这需要同任务、相近起点的比较。|而且真实结合也带来新问题：结合蛋白，不等于明显改变蛋白的功能。
P25|首次命中物在酶测试里的功能抑制仍较弱。|这没有抹去结合结果。|它表示团队回答了一个问题，却还没达到想要的表现。|区别很重要：结合测试问是否相互作用，功能测试问是否改变靶点活动。
P26|研究者结合实验信息与预测结合姿态，指导下一轮设计。|他们提出16个结构，合成6个测试。|后续分子中出现结合表现改善的对象。|其中一个还接受了酶与细胞评价。|这些是后续工作，不属于首个30天里程碑。
P27|后续分子简称048，它抑制CDK20酶活性，也在实验里降低Huh7肝癌细胞的活力。|这是更多证据，但细胞结果仍不是患者结果。|它本身也不能证明，细胞里每种变化都只来自CDK20作用。|不同实验回答不同问题，不能合并成一句治疗成功。
P28|这里还有一个有用概念：选择性。|它问，分子作用于想要的靶点，还是也影响其他靶点。|与一个蛋白结合更强，没有回答这个问题。|同样，细胞实验研究的是特定条件下的模型，不是完整人体。|这些是继续研究命中物的理由，不是否定已有进展。
P29|有价值的是这个循环：提出设计、测试、找不足，再修改设计。|首次不理想之处变成下一次决策的信息。|研究者仍要研究选择性、分子进入体内后的表现，以及可能的毒性。|2023年候选物研究没有报告这些分子的动物或患者试验。
P30|这些实验让我们有依据讨论收益。|预测蛋白结构支持设计，AI辅助生成提出分子，实验找到命中物并支持进一步改进。|这是对早期发现的贡献，不是完成治疗药物的证明。|要把实际成果与希望进一步带来的好处分开。
P31|这连接到我们关心的效率问题。|如果算法更早提供有用的设计，研究者就可能减少低价值尝试，把精力放到验证与优化。|这是有意义的潜在收益。|但单项研究没有量出，相比同等资源的替代路线节省多少时间或金钱。|取得成果，与优势多大，是两个不同问题。
P32|即使后续研发仍困难，前期节省精力也有价值。|团队的实验能力有限。|有用设计更早出现，可能腾出空间测试其他方案，从失败中学习。|价值不只是清单上的分子更少。|而是用现有资源做更好决策，同时保留足够多样的选择，避免漏掉有希望的方向。
P33|更广泛的期待包括健康、成本和动物福利。|更早找到有用候选物，可能支持未来治疗；减少低价值实验，也可能节省资源。|更好的预测还可能帮助考虑某些动物实验的替代方法。|这些是可能性，不是本案例已测出的结果。|需要实际节省投入的证据和合适验证，不能只看清单变短。
P34|环境收益也要同样谨慎。|减少不必要的合成可能减少材料和废物，但电脑也耗电。|应在取得相近研究成果的条件下，比较计算与实验两部分的资源。|缺少这种比较，就不能断言AI总体更便宜、减少动物使用或更加环保。
P35|更强的后续研究，可以在同一靶点，用相近信息、资源和成功标准比较方法。|它应记录首次确认命中的时间与实验投入，包括失败尝试。|第二个方向是用新实验反馈检查、修正预测。|第三个是同时评价多项性质，避免更好结合掩盖选择性或其他问题。
P36|资料也各有用途。|原始研究和补充材料支撑案例数字与实验。|方法论文解释工具。|学术书和综述帮助解释概念与背景。|平台开发者介绍自身研究是有用证据，但不等于独立比较。|要评价资料，而不只是数参考文献。
P37|这也与实验室外的生活有关。|听到AI发现新药，可以先问标题具体指什么。|是预测结构、实验命中物、细胞结果，还是患者证据？|理解阶段，能帮助我们既不忽视真实进展，也不期待尚未证实的治疗。
P38|现在可以回答开场问题。|分子还没做出来，我们能先预测它值不值得测试吗？|能提出有依据的预测，但必须用实验检验。|本案例中，算法帮人提出和优先考虑设计，实验引导下一步。|潜力在于让探索更有方向。|到底快多少、最终能否带来有用药物，仍要进一步证据。'''
sentences_zh={}
for row in zh.splitlines():
 p=row.split('|');sentences_zh[p[0]]=[tc(s) for s in p[1:]]

def words(s):return len(re.findall(r"[A-Za-z0-9]+(?:[’'-][A-Za-z0-9]+)*",s))
def clock(t):return f'{int(t)//60:02d}:{int(t)%60:02d}'
def srt_time(ms):
 ms=int(ms);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000);return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
def split_zh(s,n):
 # Prefer punctuation near each proportional break. This is a planned draft, not forced alignment.
 s=s.strip();parts=[]
 for left in range(n,1,-1):
  target=round(len(s)/left);options=[i+1 for i,c in enumerate(s) if c in '，、；：' and max(2,target-8)<=i+1<=target+8]
  cut=min(options,key=lambda x:abs(x-target)) if options else target
  parts.append(s[:cut]);s=s[cut:]
 parts.append(s);return parts
def wrap_zh(s,width=24):return '\n'.join(s[i:i+width] for i in range(0,len(s),width))

shots=[];cues=[];cum=0;totalwords=sum(words(s['narration_en']) for s in original['shots'])
for old in original['shots']:
 sid=old['shot_id'];w=words(old['narration_en']);start=round(cum/totalwords*870000);cum+=w;end=round(cum/totalwords*870000)
 medium,interaction,camera=visual[sid];new=dict(old)
 for k in ['planned_start_seconds','planned_end_seconds','planned_duration_seconds','beats']:new.pop(k,None)
 new.update(start_ms=start,end_ms=end,primary_medium=medium,continuous_interaction=interaction,camera_and_handoff=camera,planning_status='provisional; align to actual narration')
 english_sentences=re.split(r'(?<=[.!?])\s+',old['narration_en']);zs=sentences_zh[sid];assert len(english_sentences)==len(zs),(sid,len(english_sentences),len(zs))
 local=[]
 for se,sz in zip(english_sentences,zs):
  toks=se.split();n=max(1,(len(toks)+12)//13);splits=[round(i*len(toks)/n) for i in range(n+1)];zhparts=split_zh(sz,n)
  for i in range(n):local.append((' '.join(toks[splits[i]:splits[i+1]]),zhparts[i]))
 denominator=sum(words(x[0]) for x in local);passed=0;shotcues=[]
 for en,zt in local:
  a=start+round(passed/denominator*(end-start));passed+=words(en);b=start+round(passed/denominator*(end-start))
  cue={'id':len(cues)+1,'paragraph_id':sid,'start_ms':a,'end_ms':b,'en':en,'zh_hant':zt,'timing':'PREPLANNED; not audio-aligned'};cues.append(cue);shotcues.append(cue['id'])
 new['subtitle_cue_ids']=shotcues;shots.append(new)

prompt='''# 直接交给DS：导出15分钟项目测试视频

请用随附的完整剧本、分镜JSON和字幕草稿，制作并**导出一份可播放的MP4测试视频**。目标约15分钟：不是五分钟无口播风格片，也不是前45秒预览。

## 唯一主任务
主题为Computer-aided drug discovery and its benefits，以2023年HCC／CDK20研究为主案例。需要英文讲述、英文＋繁中字幕、适当音乐，以及连续的2D／3D混合动画。最终交付是视频文件，不要只给网页、幻灯片、截图或源代码，然后说视频完成了。

## 正式视频的流畅标准
不要按段落做PPT：上一段的具体对象、轨迹、轮廓或证据状态必须产生下一段画面。遵照每段primary_medium与continuous_interaction字段：需要空间才上3D，需要读清数字、逻辑、证据和比较时用2D。3D对象的投影可以展成2D关系，二维边缘可以重新抬升为三维结构；不要为了炫技每隔几秒随机换风格。
镜头有惯性，物体有方向；保持身份和空间连续。可以在讲清关键证据时稳定构图，但不要整段二十多秒停一张图。每段约3–5个有意义的视觉动作，跟随对应句子，而不是所有东西同时晃动。
不做手绘，不做无意义HUD，不不停闪烁。局部glitch只在误读被纠正或新闻标题被检视时短促出现，不能损害数字、旁白理解或字幕阅读。

## 讲述不是念书
英文按narration_en讲，不朗读章节号、证据号或整屏标题。像给聪明但零基础的同学讲一个研究过程：问题要有期待，实验结果处留理解空间，证据限定清楚而不机械。不得删除“细胞不是患者”“30天不是药物获批”“缺少公平效率比较”等关键限定来挤时长。
A/B/C/D是四段讲述身份；测试阶段缺真人素材时可使用一位清晰的临时英文声音，但必须标注测试配音。不要伪造组员真实出镜或本人录音。最终课程版仍须四人实际出镜并英文口述。

## 时间与字幕
900秒是预排目标：0–870秒正文，870–900秒参考文献／致谢。正文2233词，平均约154词/分钟（包含正常停顿）才装得下。先试配音再定时；如果技术术语导致理解吃力，先报告超时与拟议精简，不用粗暴加速或截掉结尾。
SRT文件是测试用预排，不是已对齐录音。英文已按句义拆为短字幕；繁中有句级对照，句内分块仍须核查。以真实配音做强制对齐／时间校正，逐条复核繁中是否与同一英文短句对应；必要时重拆行或重分短句。不要直接把草稿当作最终同步通过。
成片烧录英文＋繁中字幕，两种语言层级清楚，不重叠关键数字与图注；不要三语同屏。字幕应是口播，不应包含镜头指令。最终SRT另存一份，与视频一起交付。

## 科学画面边界
不编造真实蛋白坐标、化合物结构、实验曲线、实验纪录片影像或患者疗效。没有原始结构素材时，用明确示意；保持预测、结合、功能、细胞、患者五类证据的不同含义。七个是选中测试对象，不是七种成功药物。首次命中物与后续048不能用同一形态冒充同一实际分子。
新增伦理与环境讨论是潜力与比较建议，不是本研究量出的成本／动物／碳排收益。S07仍仅依据公开摘要。

## 音乐与导出
配乐有发展但服务讲述；解释段降低存在感，在过渡与空间展开时加强。不要套用无口播五分钟片的全程强鼓音量。缺音乐或配音时明确报告缺项，不把静音视频称为带声音成片。
导出MP4，建议H.264视频＋AAC音频、1920×1080、30fps；若环境实际只能更低规格，明确记录，不冒报。导出画面不带播放器控制条、调试面板或时间轴。
交付实际MP4、最终对齐字幕与简短导出检查。核对时长、音轨、分辨率、字幕、开头中段结尾和章节交接。能真实生成多少就报告多少；网页预览和截图不是视频文件。
'''
(OUT/'03_给DS的导出任务.md').write_text(prompt,encoding='utf-8')
film={'title':'Can AI help design a molecule worth testing?','version':'2026-10-18-15min-test-script','duration_target_ms':900000,'narration_budget_ms':870000,'credits_ms':30000,'narration_en_words':totalwords,'approximate_wpm_including_pauses':round(totalwords/14.5,1),'actual_voice_or_video_created':False,'subtitle_status':'Preplanned sentence-aligned translation and proportional timing; cue-level semantic and audio alignment pending','voiceover_language':'English','subtitle_languages':['en','zh-Hant'],'no_hand_drawn':True,'shots':shots,'credits':{'start_ms':870000,'end_ms':900000,'narration':None,'display':'3 readable source groups; 10sec each; complete sources also included in script'}}
(OUT/'02_十五分钟分镜与字幕数据.json').write_text(json.dumps(film,ensure_ascii=False,indent=2),encoding='utf-8')

for name,mode in [('04_英文字幕_预排.srt','en'),('05_繁中字幕_预排.srt','zh'),('06_双语字幕_预排.srt','both')]:
 entries=[]
 for c in cues:
  en=textwrap.fill(c['en'],width=48,break_long_words=False,break_on_hyphens=False);zt=wrap_zh(c['zh_hant'])
  body=en if mode=='en' else zt if mode=='zh' else en+'\n'+zt
  entries.append(f'{c["id"]}\n{srt_time(c["start_ms"])} --> {srt_time(c["end_ms"])}\n{body}')
 (OUT/name).write_text('\n\n'.join(entries)+'\n',encoding='utf-8-sig')

intro='''# 15分钟项目视频测试剧本：连贯的讲述，连贯的2D／3D

**本次交付只有剧本、字幕草稿与给DS的导出任务，没有制作视频。** 这次恢复项目英文讲述，不沿用五分钟纯视觉／无口播要求。DS的目标是导出正式形态的约15分钟测试MP4。

## 内容和形式
主线：研究需求 → 靶点 → 预测结构 → 生成设计 → 优先筛选 → 实验 → 反馈 → 收益与边界 → 结论。
观众跟随问题与证据推进，不看人在念标题，也不看一张图撑完整段落。

- 正文保留已经核查的38段英文，共2,233词；中文简体用于组内理解，繁中是最终字幕语言之一。
- 预排正文14分30秒，片尾30秒。完整900秒是测试目标，不是实际试配、配音或成片验证结果。
- 要保持15分钟，正文平均约154词/分钟。术语段需以听懂为先；实际配音后调整，不靠粗暴加速。
- 四位讲述身份的段落分配保留；测试配音不等于四位组员已真实出镜口述。

## 贯穿全片的视觉语法
**3D负责空间、姿态、遮挡、规模和对象变化；2D负责概念区分、证据层级、数字、比较与时间。** 每段明确谁主谁辅，不要求每秒都同时出现3D和2D。

保留抽象设计锚点、目标蛋白、首轮测试对象、首次命中物和后续048的不同身份。三维投影展开成二维信息时，保留对应锚点；二维关系重新进入空间时，沿原边缘或轨迹抬升，不另开一页。

风格采用深墨空间、钛银／青绿轮廓与珊瑚橙路径；解释数字时可以局部转暖灰白平面，主体身份和信息位置不随意改变。没有手绘，没有整屏glitch，没有不停出现的仪表盘。文字用于点题和限定，不把口播贴满画面。

**动效很多但有层级：**每段安排约3–5个有意义的小动作。先主动作，再相机揭示，再局部信息响应；不要让所有层同时乱动。镜头速度和方向在段落间延续；读关键数字、证据和限定时允许局部稳定。动效密度不等于一直高速。

相机可推近、侧掠、回转、压平、进入纵深，但每一次都要揭示新关系。不得每段都回到全景、重新入场、淡出清空。允许自然剪辑到真实组员，空间动画本身仍需连贯。

## 字幕怎么使用
包内SRT是**预排草稿**：英文、繁中、双语各一份。句级翻译已按英文语义整理；句内短块与时间按长度预分配，不能称为已经完成音画同步。DS须按实际配音校正时间和句内对应、字号、行数，最终烧录双语字幕并另交最终SRT。

## 完整内容与镜头设计
'''
md=[intro]
for s in shots:
 md += [f'### {s["shot_id"]}｜{clock(s["start_ms"]/1000)}–{clock(s["end_ms"]/1000)}｜讲述{s["speaker"]}｜{s["primary_medium"]}','',
 '**英文口播：**',s['narration_en'],'','**简中理解：**',s['translation_zh_sc'],'','**繁中理解／整段字幕底稿：**',s['subtitle_base_zh_tc'],'',
 '**2D／3D怎样交互：**'+s['continuous_interaction'],'','**镜头与交接：**'+s['camera_and_handoff'],'',
 '**本段的动作层次（跟对应句子，不机械等分时间）：**','- 承接：保留上一段的主体、路径或证据状态，不能清屏。','- 发展：按本段讲述逐项揭示空间或关系，每次只突出一个主动作。','- 澄清：关键数字、限定与证据状态出现时，局部画面放稳供理解。','- 交接：由本段的具体边缘、轨迹或对象带出下一段。','',
 '**屏幕短字参考：**'+s['screen_text'],'','**科学与制作边界：**'+s['scientific_and_production_boundary'],'',
 '**内部证据编号：**'+', '.join(s['evidence_ids']),'']

previous=(OLD/'01_完整视频剧本_含镜头设计.md').read_text(encoding='utf-8')
refs=previous.split('## 4．结尾参考文献与致谢',1)[1].split('## 5．交给DS怎么用',1)[0]
refs=re.sub(r'\*\*规划时间：.*?\*\*','**本版预排时间：14:30–15:00，共30秒，无新增口播。**',refs,count=1)
refs=refs.replace('共36秒','共30秒').replace('各约12秒','各约10秒')
md += ['## 片尾：参考文献与致谢',refs,'## 复制给DS的导出任务',prompt]
full='\n'.join(md);(OUT/'01_十五分钟项目测试剧本_含字幕与镜头.md').write_text(full,encoding='utf-8')
(OUT/'证据索引.csv').write_bytes((SRC/'证据索引.csv').read_bytes())
readme='''先把01、02和字幕文件04–06发给DS，再粘贴03。
目标是约15分钟的项目测试MP4：英文讲述、英文＋繁中字幕、音乐、连续2D／3D混合动画。
本包没有制作视频或音频。SRT是预排稿，DS须按实际配音对齐并核查短句翻译。
01中旧版边界对四人真实出镜的要求是最终课程要求；本轮无真人素材时仅作测试，不能宣称已满足。
之前五分钟无口播、手绘设想、45秒预览均不是本版要求。本包不改变原科研内容稿。
'''
(OUT/'先读我.txt').write_text(readme,encoding='utf-8')

checks={
 '38段英文逐字不变':len(shots)==38 and all(a['narration_en']==b['narration_en'] for a,b in zip(shots,original['shots'])),
 '原简中繁中底稿保留':all(a['translation_zh_sc']==b['translation_zh_sc'] and a['subtitle_base_zh_tc']==b['subtitle_base_zh_tc'] for a,b in zip(shots,original['shots'])),
 '2233词':totalwords==2233,
 '时间线870秒正文加30秒片尾':shots[0]['start_ms']==0 and shots[-1]['end_ms']==870000 and film['credits']['end_ms']==900000,
 '镜头连续无重叠':all(a['end_ms']==b['start_ms'] for a,b in zip(shots,shots[1:])),
 '38段独立媒介与交互设计':all(s['primary_medium'] and s['continuous_interaction'] and s['camera_and_handoff'] for s in shots),
 '字幕完整保留所有英文词':re.sub(r'\s+',' ',' '.join(c['en'] for c in cues)).strip()==re.sub(r'\s+',' ',' '.join(s['narration_en'] for s in shots)).strip(),
 '字幕时间连续且正时长':all(c['end_ms']>c['start_ms'] for c in cues) and all(a['end_ms']==b['start_ms'] for a,b in zip(cues,cues[1:])),
 '字幕每条英文至多13词':all(len(c['en'].split())<=13 for c in cues),
 '每条字幕均有繁中且属于一段':all(c['zh_hant'] and c['paragraph_id'] in visual for c in cues),
 '要求导出MP4而非网页替代':'最终交付是视频文件' in prompt and 'H.264' in prompt and 'AAC' in prompt,
 '字幕预排而非伪称已对齐':'不是已对齐录音' in prompt and '未制作' not in film.get('version',''),
 '范围为15分钟项目讲述测试':'不是五分钟无口播风格片' in prompt,
 '文件重新打开':json.loads((OUT/'02_十五分钟分镜与字幕数据.json').read_text(encoding='utf-8'))==film and (OUT/'01_十五分钟项目测试剧本_含字幕与镜头.md').read_text(encoding='utf-8')==full,
}
assert all(checks.values()),checks
for p in OUT.glob('*.srt'):
 blocks=p.read_text(encoding='utf-8-sig').strip().split('\n\n');assert len(blocks)==len(cues)
 assert blocks[0].startswith('1\n00:00:00,000') and '00:14:30,000' in blocks[-1]
(OUT/'07_剧本与字幕核查.json').write_text(json.dumps({'checks':checks,'result':f'{len(checks)}/{len(checks)} PASS','cue_count':len(cues),'voiceover_words':totalwords,'approx_wpm':film['approximate_wpm_including_pauses'],'audio_alignment':'PENDING','cue_internal_semantic_check':'PENDING','video_export':'NOT PERFORMED BY THIS TASK','scientific_narration':'UNCHANGED'},ensure_ascii=False,indent=2),encoding='utf-8')
files=[p for p in OUT.iterdir() if p.is_file() and p.suffix!='.zip'];zpath=OUT/'15分钟项目测试_剧本字幕与导出任务.zip'
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,p.name)
with zipfile.ZipFile(zpath) as z:
 assert z.testzip() is None
 for p in files:assert hashlib.sha256(z.read(p.name)).digest()==hashlib.sha256(p.read_bytes()).digest()
print('CHECKS',len(checks),'PASS',sum(checks.values()),'CUES',len(cues),'WORDS',totalwords,'TARGET_SECONDS',900)
print('ZIP_AND_SRT_REOPEN=PASS; NO_VIDEO_CREATED')
print(OUT)
