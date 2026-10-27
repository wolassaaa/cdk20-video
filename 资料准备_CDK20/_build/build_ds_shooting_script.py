from pathlib import Path
import csv,hashlib,json,re,zipfile

BASE=Path(__file__).resolve().parent.parent
SRC=BASE/'视频内容稿/教师要求补齐版'
OUT=BASE/'视频分镜_DS测试版_20261018';OUT.mkdir(exist_ok=True)
d=json.loads((SRC/'双语内容主稿.json').read_text(encoding='utf-8'))
paragraphs=[dict(p,chapter_id=s['id'],chapter_title=s['title_en']) for s in d['sections'] for p in s['paragraphs']]

# Content is retained verbatim. The following rows are visual directions, not new research results.
spec='''P01|从一颗抽象分子设计的线框近景开始，慢慢后退|前段：线框悬在纸面与屏幕交界处，还没有实体样品；中段：视野扩成许多待验证设计，只有少量空的实验位置；末段：镜头停在一个设计旁的问号，不让它直接变成药片|Worth testing? / 值得測試嗎？|相同线框留在画面右侧，承接下一段|抽象设计必须标Illustrative design；不是本研究的实际化合物。A真实出镜先占主画面约6秒，然后切为持续可辨认的画中画。
P02|继续后退并沿一条弯曲研究路径缓慢前移|前段：已有数据碎片汇入候选设计区；中段：同一设计经过Design、Test、Improve三个位置；末段：路径延长到Benefits与Evidence，保持终点未定|Design → Test → Improve|沿路径抵达研究目标的位置|工具输出只是建议；不得出现Approved、Cure或成功率数值。
P03|镜头从路径侧面靠近研究任务的空白中心|前段：电脑、研究者判断、实验三个组件共同围住候选；中段：候选停在Starting point标记旁；末段：空白中心出现What should it do，镜头移向它|A useful starting point|候选退到边缘，下一段从目标任务进入|研究者用中性图标，不虚构具体研究人员或对话。
P04|从简化人体轮廓的肝脏位置推近，止于抽象细胞层|前段：肝脏高亮，其余人体退后；中段：标签展开为Hepatocellular carcinoma / HCC；末段：一个蛋白工作组件从细胞示意中被单独框出|HCC: primary liver cancer|锁住蛋白组件，过渡到目标和候选的区分|画面为解剖和细胞示意，不把HCC等同于所有肝癌；不出现患者治疗影像。
P05|保持蛋白居中，左右轻微环绕以展示它和小分子的尺度关系|前段：大组件标Target: CDK20；中段：先前的小线框停在旁边标Candidate molecule；末段：两者保持独立，建立下一步研究关系|Target ≠ candidate|镜头沿Target标签移向它背后的既有证据|蛋白与候选不画成同一物体，不把抽象大小当实际比例。
P06|镜头横移，揭示目标后面已经存在的文献与数据层|前段：Earlier research节点先出现；中段：Disease data analysis节点与其汇合；末段：两条证据线共同指向CDK20，选中标记由人工判断环节确认|Earlier evidence + disease data|保留多条证据线，下一段将它们展开为多个研究问题|不表现成AI凭空发现CDK20或单一分数自动确定靶点；文献节点不是伪造论文封面。
P07|拉远看见CDK20之外仍有其他生物因素，随后回到具体研究问题|前段：CDK20仍高亮，但周围保持其他因素；中段：治疗患者的远端位置保留未证实标记；末段：聚焦Can a molecule interact with this target|A focused question, not the only cause|候选与蛋白轮廓一起进入下一章空间|其他因素只作概念节点，不伪造具体机制网络；不要把CDK20画成肝癌唯一开关。
P08|围绕蛋白轮廓缓慢侧移，揭示一个凹口与候选的不同形状|前段：同时标明Protein structure和Molecule design；中段：镜头改变视角显露三维关系；末段：候选停在口袋外，等待结构信息|Two structures, two jobs|保留凹口位置，让预测模型信息逐步出现|不能只靠钥匙锁洞解释全部化学；未取得真实模型时标Protein schematic。
P09|镜头从序列与相关信息层平移到预测三维模型|前段：Sequence、Related sequences、Learned patterns汇入模型；中段：模型作为输出被展开；末段：旁边出现Predicted，实验测定的独立位置暂空|Predicted structure ≠ experimental measurement|模型停在原位，镜头转向序列信息|不把模型做成蛋白照片，不表现AlphaFold逐帧模拟真实折叠轨迹。
P10|序列带与三维模型并置，镜头在两种信息之间小幅往返|前段：序列用无具体残基含义的符号带表示；中段：一条信息关联线连接三维示意；末段：模型下方出现More focused design question|Sequence / Folded structure|返回同一个三维模型，准备检视不确定性|序列带不在镜头里物理折叠成真实过程；不伪造CDK20实际氨基酸序列。B真实出镜转换安排在下一段开始。
P11|镜头靠近模型一端，以不同透明度展示局部置信差异|前段：B真实出镜约6秒，主画面同步停在待检查的模型；中段：低置信度末端区域被人工选出；末段：该区域退到旁边的Excluded for design位置，剩余模型不移动|Model uncertainty → human judgement|保留处理后的模型中心，交给下一段|无原始结构与置信数据时只画概念末端，不伪造精确残基或真实pLDDT色图。
P12|从处理后的模型拉开，显露由它支持的设计路径|前段：Predicted structure支路连向Structure-guided design；中段：Experimental structure位置显示未用于本起始流程；末段：镜头靠近仍空着的新分子位置|Enables a starting workflow|空位置周围逐渐出现候选设计的边界|不显示虚构的节省天数；没有实验结构指本案例起始流程，不概括全部蛋白研究。
P13|从同一个空设计位置向周围展开候选家族|前段：约束边框先建立，再出现不同抽象候选；中段：分支数量增加，展示提出新结构而非仅排序；末段：Chemistry42标签只作为小注释出现|Generate candidate designs|保留一批候选的对象ID，下一段检视不同要求|不要把随机图形说成真实生成结构；不使用平台logo替代机制解释。
P14|镜头环绕同一批候选，依次显露相互作用、可合成性和其他性质三个维度|前段：有的候选只在形状方向靠前；中段：其他约束使其位置重新分布；末段：没有一个自动变成全绿最优物体|More than shape matching|镜头跟住几个不同权衡的设计|颜色只表达概念状态，不是论文的实际合成难度、毒性或活性评分。
P15|跟住一个抽象候选，镜头后退显示其他同样值得提出的假设|前段：该候选旁出现Might be worth testing；中段：其他候选保留不同优缺点；末段：实体样品位置仍为空|Design = hypothesis, not a manufactured drug|转向其中一个设计与蛋白口袋之间的空间|不以唯一发光分子暗示正确答案；不让生成动作直接制造出实体样品。
P16|保持口袋固定，用镜头换角度展示几种候选姿态|前段：抽象分子在多个预测姿态间切换；中段：评分只作Qualitative ranking标签；末段：姿态被保存为预测，不给实验确认章|Docking pose ≠ binding proof|姿态信息随候选一起进入人工选择区|标Pose illustration, not a binding trajectory；不画穿行口袋的真实结合动力学，不造对接分数。
P17|拉开成四方协作空间：AI、其他计算、研究者判断、实验|前段：候选从生成区抵达评价区；中段：研究者判断让少量对象进入待合成队列；末段：实验区仍在路径后方等待|AI + computation + people + experiments|镜头沿队列方向推进到筛选全过程|不将AI与所有计算画等号；实验结果不能在合成前被标成已知。
P18|大幅拉远展示候选规模，再沿景深跟随被优先考虑的对象|前段：抽象设计群上方显示8,918 generated；中段：优先队列显示54 prioritised；末段：七个明确位置进入Synthesis and testing队列|8,918 → 54 → 7|七个位置保留连续ID TEST_01–TEST_07|数字来自原论文；可用粒子群示意规模，不冒充展示全部实际结构；七个是选定测试对象。
P19|镜头依次停在三个阶段边界，而不是向单一成功奖杯推进|前段：Generated、Prioritised、Selected for testing标签逐一对齐；中段：七个位置只出现Selected状态；末段：实验结果区暂时不点亮|Selected ≠ successful|七个对象移动到实验边界前暂停|不要把七个都标有效，也不要把其余设计全部画成失败。
P20|跟随七个位置前移，侧面保留实验资源的有限容量|前段：资源图标表示有限实验机会，不显示金额；中段：8,918÷7的示意算式被标Not a speed-up measure；末段：镜头停在相同任务比较的空白框|Prioritisation, not a speed-up factor|空白比较框延续到传统方法的说明|不声称传统路线必须合成8,918个，不显示效率倍数。B的口述块结束，不额外添加交接台词。
P21|从空白比较框拉开，显露两条都拥有知识与计算工具的路线|前段：C真实出镜约6秒；中段：AI-assisted与Alternative approach并列，不赋予优劣动画；末段：相机回到共同需要回答的Binding test|Comparable conditions matter|镜头跨入实验区域，七个测试位置继续保留|传统路线不能画成蒙眼或乱猜；这只是未来比较示意，不是论文完成的对照实验。
P22|近景从设计图标转向实验测量结果的独立标记|前段：七个位置进入Tested状态；中段：其中一个概念命中物旁出现Binding hit；末段：实验确认标签与先前预测标签并列|Experimentally confirmed binding hit|保留HIT_01，进入30天里程碑|除论文确认的命中外，其他位置不自行填失败/成功结论；实验仪器画成示意，不能伪称真实实验录像。
P23|镜头沿一段限定时间轴从Target selection滑向First binding hit|前段：起点与终点完整露出；中段：30 days只覆盖这两个端点之间；末段：后续优化路线在右侧继续延伸，不被30天框住|30 days: target selection → first binding hit|镜头越过里程碑，抵达尚未完成的功能任务|不从零训练AI开始计时，不把批准上市、细胞或全部后续优化纳入30天。
P24|镜头由结合结果转向蛋白功能状态，保持两个测量区分开|前段：Binding证据维持已确认；中段：Function区出现另一个待回答问题；末段：镜头停在功能评价区，不发放治疗成功标记|Binding ≠ changing function|同一个HIT_01移到功能区旁，保持对象身份|不制造与其他方法的耗时对照值；结合后不直接播放细胞死亡。
P25|并置两个独立观察窗口，镜头只在它们之间平移|前段：Binding窗口保留确认状态；中段：Enzyme function窗口显示Weak initial inhibition；末段：两者连接到Need improvement|One answer, another question|将改进需求作为下一轮设计输入|弱功能用文字定性说明，不画未给出的精确曲线、IC50值或抑制比例。
P26|沿反馈弧线返回设计区，但不回到片头|前段：实验信息与预测姿态回到已有设计对象旁；中段：后续一轮出现16 proposed与6 synthesised；末段：一个后续对象标ISM042-2-048，走向更深入评价|Later work: 16 → 6|048保留独立ID，不与首轮命中物混成同一个结构|不把后续六个说成首轮七个；改善结合与全性质改善分开；不重启30天计时。
P27|镜头缓慢穿过酶、细胞两个分开的证据层，止于患者边界前|前段：048连接到CDK20 enzyme inhibition证据；中段：另一个窗口显示Reduced Huh7 cell viability；末段：Patients区域保持No evidence in this study标记|Enzyme result / Cell result / Not patient evidence|048留在细胞层边缘，镜头转去看其他潜在靶点|不能伪造患者好转或人体治愈；细胞效果不被画成仅由CDK20引发的已证实因果链。
P28|围绕048与多个抽象蛋白组件展开空间关系|前段：目标CDK20可辨认；中段：其他蛋白维持待检验状态；末段：细胞模型的边框与人体边框保持清晰距离|Selectivity still needs testing|镜头沿模型边界退后，揭示研发循环与未完成区域|不虚构激酶选择性面板或安全性；不能把更强结合绘成所有其他靶点都不结合。
P29|从已有对象拉出一个闭合但向外延伸的研究循环|前段：Design、Test、Learn、Revise由同一条反馈线连起；中段：Selectivity、Body exposure、Toxicity位于后续待评价区域；末段：循环旁保留No animal/patient trials in the 2023 case|Progress, with unfinished questions|循环横向展开成为收益评价的共同底图|待评价不是失败；不把未报告画成无效。C口述结束，下一段交给D。
P30|镜头沿循环缓慢后退，让观众看到哪些部分已被证据支撑|前段：D真实出镜约6秒；中段：结构支持设计、生成设计、实验命中与改进各自挂上对应证据标记；末段：远端治疗结果仍未连接|Observed contribution / Possible wider benefit|沿已观察与潜在收益两条分支移动|观察到的贡献和潜在收益使用不同视觉编码，不能一起打勾。
P31|镜头沿潜在收益支路推进，同时让比较证据位置保持空白|前段：Useful designs earlier只显示条件性箭头；中段：精力流向Validation与Optimisation；末段：Comparable baseline位置标Not measured here|Achievement ≠ measured advantage|研究资源图标进入下一段容量比较|不显示节省百分比、总成本或几倍加速；条件箭头旁保留If / May。
P32|从有限实验位置拉开成资源分配空间，避免只做漏斗消失动画|前段：可用实验位置固定；中段：更有用的候选可能占据部分位置；末段：仍保留多个不同方向的探索分支|Better decisions, not simply fewer designs|不同分支引向更广泛的收益类别|不鼓励把清单删到只剩一个，不暗示未选结构都无价值。
P33|由资源分支扩展出健康、成本、动物福利三个平行区域|前段：Health、Cost、Animal welfare各自带Potential标记；中段：动物图标只连接到需要合适验证的替代方案；末段：三个区域下方统一出现Not measured in this case|Potential, not demonstrated here|镜头继续漂移到环境资源分支|不出现康复患者、已减少动物数量、便宜药价等已实现画面；T02是课程指导而非实验数据。
P34|镜头分出计算与实验两条资源路径，再合到一个比较边界|前段：实验侧展示材料与废物图标，计算侧展示电力图标；中段：两条路径共同进入Same research outcome边界；末段：边界外出现Evidence needed，不给净收益数值|Count computing + laboratory resources|比较边界成为下一段研究设计的框架|不把少做合成直接变成总体环保或低成本结论；不虚构碳排/耗电数值或绿色认证。
P35|围绕比较框架缓慢移动，先揭示条件，再揭示反馈与多性质|前段：Same target、Similar resources、Same success criteria对齐；中段：实验反馈回到模型检查；末段：Binding、Selectivity、Other properties并列，不只突出一个分数|Fair comparison / Feedback / Multiple properties|框架收束到支撑这些判断的来源层|整个框架标Proposed next study；不得表现成已完成并证明AI获胜的实验。
P36|镜头扫过三种不同用途的来源层，不把整篇论文铺满画面|前段：Original study + supplement对应实验；中段：Methods、Reviews、Book chapter对应方法和背景；末段：Platform developer与Independent comparison之间保留区别|Different sources, different jobs|来源层只留下关键证据阶段，接到新闻识读|引用真实来源编号；S07只标Abstract checked，不显示全文已核查；不要伪造论文截图或作者背书。
P37|一个简短新闻标题框从同一证据路径边缘进入，镜头跟随它核对所处阶段|前段：标题只写AI discovered a drug?，明确是示例不是新闻截图；中段：Prediction、Lab hit、Cells、Patients逐个被问到；末段：指示器停在本案例实际达到的实验层，不越过患者边界|What stage does the headline mean?|镜头返回片头的抽象设计位置，仍保留真实证据路径|不能做成某家真实媒体的伪造报道；不把所有AI药物新闻都归为同一阶段。
P38|回到同一设计线框的近景，再慢慢拉开看完整研究路径|前段：开场问号仍在，但旁边出现Evidence-guided predictions；中段：实验节点亮起，后续研究路径保持开放；末段：D真实出镜画面适度放大，同一研究路径停在A better-directed search|A better-directed search, not a finished medicine|自然停留后进入参考文献；不再增加新的口播结论|不以药片、患者治愈或Approved作结束画面；末尾保留方法收益与幅度待验证的区别。'''
rows=[line.split('|') for line in spec.splitlines()]
assert len(rows)==38 and all(len(r)==6 for r in rows)
lookup={r[0]:r for r in rows}

def words(s):return len(re.findall(r"[A-Za-z0-9]+(?:[’'-][A-Za-z0-9]+)*",s))
def stamp(t):
 t=int(round(t));return f'{t//60:02d}:{t%60:02d}'
timeline=[];t=0
for p in paragraphs:
 r=lookup[p['id']];n=int(p['id'][1:]);speaker='A' if n<=10 else 'B' if n<=20 else 'C' if n<=29 else 'D'
 dur=round(words(p['en'])*60/130+1.5,1)
 beats=[s.strip() for s in r[2].split('；')]
 assert len(beats)==3
 shot=dict(shot_id=p['id'],chapter_id=p['chapter_id'],speaker=speaker,planned_start_seconds=round(t,1),planned_end_seconds=round(t+dur,1),planned_duration_seconds=dur,camera=r[1],beats=[{'start_offset_seconds':round(dur*k/3,1),'end_offset_seconds':round(dur*(k+1)/3,1),'direction':s} for k,s in enumerate(beats)],screen_text=r[3],transition=r[4],scientific_and_production_boundary=r[5],narration_en=p['en'],translation_zh_sc=p['zh_sc'],subtitle_base_zh_tc=p['zh_tc'],evidence_ids=p['refs'])
 timeline.append(shot);t+=dur
credit_start=round(t,1);total=round(t+36,1)
manifest={'title':'Can AI help design a molecule worth testing?','version':'shooting-script-2026-10-18','purpose':'DS input brief and complete content/camera script; not a generated video','source_canonical_sha256':hashlib.sha256((SRC/'双语内容主稿.json').read_bytes()).hexdigest(),'timing_status':'Planning estimates only. Replace with recorded voice timing. No SRT or audio alignment is claimed.','planned_narration_rate_wpm':130,'planned_hold_per_paragraph_seconds':1.5,'planned_total_seconds':total,'canvas':{'width':1920,'height':1080,'fps':30,'subtitle_languages':['en','zh-TW'],'internal_translation':'zh-CN'},'shots':timeline,'credits':{'start_seconds':credit_start,'end_seconds':total,'duration_seconds':36,'narration':None,'pages':3,'seconds_per_page':12,'note':'Show complete reference information in three readable groups; no new spoken content. Actual legibility must be tested.'}}
(OUT/'02_完整分镜数据.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

prompt='''# 给DS的生成指令（先做45秒测试，再扩展全片）

你要根据随附的《01_完整视频剧本_含镜头设计.md》和《02_完整分镜数据.json》，实现一个英文科学解释视频的代码动画工程。不是生成PPT，也不是把每个段落变成一张自动切换的图表。

## 本次先交付什么
先实现前45秒测试段，按JSON的时间顺序只播放这个范围，45秒时可以停在一段话中间；不得压缩或跳过前38段来假装展示全片。其余内容只建立完整时间轴骨架，清楚标出尚未实现。测试通过后再逐段扩展到完整视频。

## 内容唯一依据
- narration_en是最终英文口播，不改数字、顺序、事实、证据边界，也不自动缩写。
- 中文简体是内部理解稿；成片字幕为英文＋繁体中文。不要三种语言同时叠在画面里。
- 主案例是2023年CDK20早期候选物研究，非上市药或患者试验。8,918→54→7、首次结合命中的30天、后续16→6和048细胞结果必须区分。
- 每个镜头的boundary字段约束画面含义，不只是文字免责声明。禁止让画面暗示比旁白更强的疗效或成功率。
- 原剧本的E编号可在内部追踪；观众画面用短来源，例如Ren et al., 2023，而非只出现无法理解的E编号。

## 呈现方式
- 16:9、1920×1080、30fps；建议Three.js承担空间对象，HTML/SVG承担可读文字和字幕；具体依赖版本在工程中固定并记录。
- 同一条研究路径贯穿：设计→目标→预测结构→生成→选择→实验→反馈→评价→返回开场问题。
- 相机推拉、环绕、视差和对象变换必须解释信息。不要每段都先清空屏幕，再淡入一块标题卡。
- 对象ID持续存在。示意设计不随意变成论文的真实命中物；首次命中物HIT_01和后续048分开。
- 画面采用克制的深蓝/灰白科学解释风格，清楚的轮廓、明亮可读文字；不要堆满霓虹光线、飞行粒子和无意义HUD。
- 允许自然剪辑到四位真实组员的画面，不为了追求“一镜到底”而牺牲出镜要求。科学动画内部保持空间连贯。
- 使用绝对时间t决定镜头和对象状态，可暂停、拖动、定位、重播；随机效果固定种子。
- 生成本地可运行工程、依赖清单与启动/预览/导出说明。真实导出成功才说已生成MP4；HTML预览不是已交付视频。

## 必须预留的真实素材
- presenter_A/B/C/D.mp4：四位组员各自真实出镜并用英文讲述分配段落的录像。每位开始可全画面约6秒，随后保持可辨认的画中画，不遮字幕和数据。
- 如果没有这些录像，显示明确的“真实出镜素材待替换”占位；不能用AI人物、克隆声音或名单冒充四个人完成出镜口述。
- 没有音轨可先做无声画面测试并保留字幕；如临时用TTS预听，标记为测试音轨，不能声称是真实组员录音。
- 没有真实蛋白或化合物结构文件时，采用明确标为示意的抽象对象。禁止编造SMILES、CDK20序列、原子坐标或假实验图。

## 字幕、文字与声音
- 原始段落不是一条长字幕。按实际音频切分短句：英文每条约8–14词，通常不超过两行；繁中与同一语义同步，通常不超过两行。
- 字幕放在下方安全区，先英文后繁中；1920×1080起始字号英文约38–42px、繁中约40–44px，须按实际画面测试调整。
- 主题标签放在字幕区以外；关键数字停留足够时间，不与字幕争抢阅读。
- 不假设比例分配的镜头时间已经完成语音对齐。最终字幕时间由真实录音确定，输出SRT/VTT前要核对。
- 旁白优先，音乐可省略。不要用音效掩盖术语和数字。

## 验收方式
1. 隐去大部分文字，是否仍看得懂对象怎样从上一步进入下一步？
2. 连续播放时，是否像电影中的研究过程，而非依次播放的幻灯片？
3. 暂停和拖动是否能精确定位，不依赖上一次播放留下的状态？
4. 是否有未标明的示意、虚构的实验/数字、过强的药效暗示？
5. 字幕、真实出镜位置与关键数字是否相互遮挡？
6. 明确报告“已实现哪段、使用哪些占位、是否有真实音轨、是否真的导出、哪些尚未验证”。

请先给出45秒测试工程及真实验证结果，不要一次性生成18分钟的低质量成片后宣称完成。
'''
(OUT/'03_复制给DS的指令.md').write_text(prompt,encoding='utf-8')

lines=['# 完整视频剧本：Can AI help design a molecule worth testing?','',
'**英文口播＋简中理解＋繁中字幕底稿｜含镜头、动作、转场和真实出镜位置**','',
'版本日期：2026-10-18。沿用教师要求补齐版的38段英文，未增删口播事实。本文件是制作剧本，不是已生成的视频。','',
'## 先看这几条','',
'- 建议制作路线：连续空间的科学解释动画＋四位真实组员出镜口述。动画负责帮助理解，不取代组员呈现。',
f'- 规划长度约 **{stamp(total)}**：英文2,233词，按130词/分钟加每段1.5秒停留及36秒参考文献估算。实际录音和成片需重新计时，完整视频须在15–20分钟。',
'- 38个段落是38个叙事单元，不是38个静止画面；每个单元有3个视觉节拍，相机与对象在单元内部持续变化。',
'- 镜头时间是规划，不是已录制音轨的时间码。每个镜头的3个等分节拍仅供初版制作，最终需随对应句子调整。',
'- 成片只显示英文＋繁中字幕；简中留在剧本里帮助组员理解。标题和数据不必朗读。',
'- 真实组员录像、真实语音、模型文件和化学结构目前未作为本次素材提供；需要的地方均按待补素材处理。','',
'## 1．四人出镜与口述安排','',
'|组员占位|口述段落|英文词数|要求|','|---|---|---:|---|']
loads={}
for speaker in 'ABCD':
 shots=[s for s in timeline if s['speaker']==speaker];w=sum(words(s['narration_en']) for s in shots);loads[speaker]=w
 lines.append(f'|{speaker}|{shots[0]["shot_id"]}–{shots[-1]["shot_id"]}|{w}|本人真实出镜并英文口述，不能只放姓名或AI人物|')
lines+=['','四个人的词数接近，不另加机械交接台词；A提出问题，B解释设计，C追踪实验，D评价收益与结论。每位开始处可先给约6秒主画面，随后与科学动画共同呈现。画中画建议约占画面宽度22%–26%，位置随数据布局调整，面部应清楚，不能被压成装饰性小头像。最终老师要求的是每人出镜且口头讲述，画中画的具体样式是我们的设计建议。','',
'## 2．贯穿全片的视觉规则','',
'保留一条弯曲的“研究路径”和可追踪对象。青蓝色虚线/线框表示预测或设计，实线证据标记表示实验观察；潜在收益用条件分支而非绿色成功章。颜色之外同时用文字与线型区分，避免只靠颜色。','',
'**对象不是同一个分子变成所有结果：**片头DESIGN_SKETCH是抽象设计锚点；CDK20_TARGET是作用对象；TEST_01–07是首轮选中测试位置；HIT_01是首次结合命中的示意；FOLLOWUP_048是后续分子，不能混用身份。没有真实结构文件时，以上均用清楚标注的示意图形，不伪称实际分子结构。','',
'连续转化链：抽象设计与研究资源 → 明确研究目标 → 检视预测结构 → 提出候选 → 计算与人工优先级 → 实验确认 → 反馈改进 → 收益和证据评价 → 返回最初的问题。','',
'引用展示规则：正文E编号供内部核查；观众画面中案例镜头显示“Ren et al., 2023”，方法镜头使用“Jumper et al., 2021 / Ivanenkov et al., 2023”，其他来源按文末清单。不要把课程课件当作已证明收益的实验研究。','',
'## 3．完整逐段分镜','']
last=None
for s in timeline:
 p=next(p for p in paragraphs if p['id']==s['shot_id'])
 if s['chapter_id']!=last:
  lines += ['### '+s['chapter_id']+' — '+p['chapter_title'],''];last=s['chapter_id']
 lines += [f'#### {s["shot_id"]}｜{stamp(s["planned_start_seconds"])}–{stamp(s["planned_end_seconds"])}｜组员{s["speaker"]}｜约{s["planned_duration_seconds"]}秒','',
 '**英文口播（照此录制）：**',s['narration_en'],'',
 '**简中理解：**',s['translation_zh_sc'],'',
 '**繁中字幕底稿（制作时须拆短句）：**',s['subtitle_base_zh_tc'],'',
 '**镜头：**'+s['camera'],'',
 '**画面节拍：**']
 for b in s['beats']:lines += [f'- +{b["start_offset_seconds"]:.1f}–{b["end_offset_seconds"]:.1f}秒：{b["direction"]}']
 lines += ['', '**屏幕短字：**'+s['screen_text'],'', '**转场与承接：**'+s['transition'],'', '**边界／制作注意：**'+s['scientific_and_production_boundary'],'', '**证据核对：**'+', '.join(s['evidence_ids']),'']
lines+=['## 4．结尾参考文献与致谢','',f'**规划时间：{stamp(credit_start)}–{stamp(total)}，共36秒，无新增口播。** 分三组各约12秒显示，保留浅色的研究路径作为背景，不做快速滚动字幕。全部信息还应随提交材料提供，实际画面字号和可读性需测试。','',
'第一组：主案例与前期靶点依据','- Ren F, et al. AlphaFold accelerates artificial intelligence powered drug discovery: efficient discovery of a novel CDK20 small molecule inhibitor. Chemical Science. 2023;14:1443–1452. DOI:10.1039/D2SC05709C. 另列其Supporting Information。','- Feng H, et al. Cell cycle-related kinase is a direct androgen receptor-regulated gene that drives β-catenin/T cell factor-dependent hepatocarcinogenesis. J Clin Invest. 2011;121:3159–3175. DOI:10.1172/JCI45967.','',
'第二组：方法和背景','- Jumper J, et al. Highly accurate protein structure prediction with AlphaFold. Nature. 2021;596:583–589. DOI:10.1038/s41586-021-03819-2.','- Ivanenkov YA, et al. Chemistry42: An AI-Driven Platform for Molecular Design and Optimization. J Chem Inf Model. 2023;63:695–701. DOI:10.1021/acs.jcim.2c01191.','- Wang L, et al. Advances of Artificial Intelligence in Anti-Cancer Drug Design: A Review of the Past Decade. Pharmaceuticals. 2023;16:253. DOI:10.3390/ph16020253.','',
'第三组：评价、书籍与疾病背景','- Bender A, et al. Artificial intelligence in drug discovery — what it is, where we stand and the path forward. Nature Reviews Drug Discovery. 2026. DOI:10.1038/s41573-026-01496-2. 本项目仅核查公开摘要与元数据。','- Lengauer T, ed. Bioinformatics — From Genomes to Therapies. Vol.1. Wiley-VCH, 2007. Public Chapter 1, pp.1–24.','- National Cancer Institute. Liver and Bile Duct Cancer. https://www.cancer.gov/types/liver','',
'片尾组员姓名、实际图源、音乐来源和AI辅助用途按真实素材填写；不要预先声称全部图像都是原创、已获许可或全程由组员制作。教师文件用于课程要求核对，不用伪装成支持医学结论的科研论文。','',
'## 5．交给DS怎么用','',
'直接把本文件和02_完整分镜数据.json一起发给DS，再粘贴03_复制给DS的指令.md。先看前45秒测试的镜头、字幕、对象连续性与真人位置，再决定是否生成完整工程。测试只覆盖前45秒，不能代表已经验证全片。','',prompt]
full='\n'.join(lines)
(OUT/'01_完整视频剧本_含镜头设计.md').write_text(full,encoding='utf-8')
checks=[]
def check(n,v):checks.append({'check':n,'pass':bool(v)})
check('38 shots match 38 paragraphs',len(timeline)==38 and [s['shot_id'] for s in timeline]==[p['id'] for p in paragraphs])
check('English narration unchanged',all(s['narration_en']==p['en'] for s,p in zip(timeline,paragraphs)))
check('Both Chinese versions unchanged',all(s['translation_zh_sc']==p['zh_sc'] and s['subtitle_base_zh_tc']==p['zh_tc'] for s,p in zip(timeline,paragraphs)))
check('2233 English words',sum(words(s['narration_en']) for s in timeline)==2233)
check('Four presenters assigned all paragraphs',set(loads)==set('ABCD') and max(loads.values())-min(loads.values())<=30)
check('Time range 15-20 minutes',900<=total<=1200)
check('Contiguous timeline',all(abs(timeline[i]['planned_end_seconds']-timeline[i+1]['planned_start_seconds'])<.11 for i in range(37)))
check('Every shot has camera, 3 beats, transition, boundary, evidence',all(s['camera'] and len(s['beats'])==3 and s['transition'] and s['scientific_and_production_boundary'] and s['evidence_ids'] for s in timeline))
check('Every paragraph in Markdown verbatim',all(p['en'] in full and p['zh_sc'] in full and p['zh_tc'] in full for p in paragraphs))
check('No actual media production claimed',manifest['purpose'].endswith('not a generated video'))
check('P18-P19 selection stage not efficacy',all('selected' in s['narration_en'].lower() for s in timeline[17:19]))
check('30-day endpoint retained','first experimentally confirmed binding hit' in timeline[22]['narration_en'])
check('Patient result boundary retained','not a patient result' in timeline[26]['narration_en'])
check('Environmental net benefit not asserted','does not establish' in timeline[33]['narration_en'])
check('S07 abstract-only disclosure retained','仅核查公开摘要' in full)
check('No fake presenter substitution','不能用AI人物' in prompt)
check('JSON reopens',json.loads((OUT/'02_完整分镜数据.json').read_text(encoding='utf-8'))['shots']==timeline)
assert all(c['pass'] for c in checks),checks
audit={'date':'2026-10-18','checks':checks,'result':f'{len(checks)}/{len(checks)} PASS','presenter_word_counts':loads,'planned_duration_seconds':total,'planned_duration_mmss':stamp(total),'actual_recording':'NOT PROVIDED','actual_video_generation':'NOT PERFORMED','actual_audio_alignment':'NOT PERFORMED','source_file_changed':False}
(OUT/'04_剧本核查记录.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
shutil_note='''本次只交付分镜剧本和生成指令，没有生成视频、录像、音轨或已对齐字幕。规划时长不是实测时长。原双语内容稿未修改。证据编号对应随包的证据索引.csv。
推荐操作：把01和02发给DS，粘贴03；先生成前45秒，核查后再扩展。四位组员的真实出镜英文口述是最终作业要求，占位或AI人物不能代替。
'''
(OUT/'先读我.txt').write_text(shutil_note,encoding='utf-8')
(OUT/'证据索引.csv').write_bytes((SRC/'证据索引.csv').read_bytes())
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.is_file() and p.suffix!='.zip'}
zpath=OUT/'DS视频剧本_含完整分镜.zip'
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
 for name in hashes:z.write(OUT/name,name)
 z.writestr('SHA256.json',json.dumps(hashes,ensure_ascii=False,indent=2))
with zipfile.ZipFile(zpath) as z:
 assert z.testzip() is None
 for name,h in hashes.items():assert hashlib.sha256(z.read(name)).hexdigest()==h
assert (OUT/'01_完整视频剧本_含镜头设计.md').read_text(encoding='utf-8')==full
assert hashlib.sha256((SRC/'双语内容主稿.json').read_bytes()).hexdigest()==manifest['source_canonical_sha256']
print(audit['result'],'WORDS',sum(loads.values()),'LOADS',loads,'PLANNED_DURATION',stamp(total))
print('REOPEN_AND_ZIP_HASH_CHECK=PASS')
print('OUTPUT',OUT)
