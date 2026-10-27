from pathlib import Path
import csv
import hashlib
import json
import logging
import xml.etree.ElementTree as ET
from pypdf import PdfReader

BASE = Path(__file__).resolve().parent.parent
DATE = '2026-10-03'
URLS = {
    'S01': 'https://www.cancer.gov/types/liver',
    'S02': 'https://doi.org/10.1039/D2SC05709C',
    'S02-SI': 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9906638/supplementaryFiles',
    'S03': 'https://doi.org/10.3390/ph16020253',
    'S04': 'https://doi.org/10.1038/s41586-021-03819-2',
    'S05': 'https://doi.org/10.1021/acs.jcim.2c01191',
    'S06': 'https://doi.org/10.1038/s41591-024-03434-4',
    'S07': 'https://doi.org/10.1038/s41573-026-01496-2',
    'S08': 'https://www.jci.org/articles/view/45967',
    'S09': 'https://doi.org/10.1007/978-3-031-76718-0',
    'S10': 'https://application.wiley-vch.de/books/sample/3527312781_c01.pdf',
    'T01': 'D:/。hkbu/molecular science/Group Project Introduction.pdf',
}
FIELDS = ['证据编号','主张','来源编号','定位','研究阶段','方法','样本或对照','结果或原文信息','单位与误差','支持的表述','推论边界','局限','核查层级','来源URL','核查日期']
ROWS = []

def add(n, claim, source, locator, stage, method, controls, result, units, wording, boundary, limit, level='正式发表全文核查'):
    ROWS.append(dict(zip(FIELDS, [f'E{n:02d}',claim,source,locator,stage,method,controls,result,units,wording,boundary,limit,level,URLS.get(source.split(';')[0],''),DATE])))

add(1,'HCC 是成人原发性肝癌最常见类型','S01','网页开头 Liver and Bile Duct Cancer','疾病背景','官方疾病概念说明','非研究实验','NCI 明确说明 HCC 的疾病定位','不适用','研究具体疾病为肝细胞癌','不涉及所有肝癌类型或转移性肝癌','不用于推导 CDK20 的治疗疗效','官方网页核查')
add(2,'CDK20 是本案例选择的潜在作用靶点','S02','CDK20 as a promising target for cancer treatment; Target selection and identification','靶点假设','整合疾病关联及既有机制文献','现有数据与文献，不是新开展患者治疗试验','CDK20/CCRK 被选择开展小分子设计','不适用','研究者选择值得进一步检验的靶点','关联不等于治疗因果性；不是新发现疾病或蛋白','已有证据的解释与选择受筛选条件影响')
add(3,'早期命中物与完整研发分属不同阶段','S03','PDF第1页 Introduction 抗癌研发流程段落','研发阶段','叙述性综述','背景资料','流程包括命中探索、优化、临床前及临床研究','不适用','本案例主要评价早期发现','不将早期命中等同于上市药物','综述检索截止2022年12月；不是最新疗法指南','本地正式全文核查')
add(4,'计算辅助方法可用于缩小候选范围','S03','PDF第2页 Introduction CADD 段落','计算筛选背景','叙述性综述','不是统一条件的比较实验','综述描述将大候选库筛选为预测活性集合','不适用','计算帮助安排实验优先级','不从概括性描述推导本案例具体时间或成本收益','概括性综述；具体效应需原始研究','本地正式全文核查')
add(5,'既有发现方法也使用计算与专业判断','S03','PDF第1–2页 Introduction','方法背景','CADD 与多学科药物设计','不适用','综述说明已有计算辅助及多学科研究','不适用','AI 是对已有方法的补充或改善','不把比较对象描绘为盲目随机试错','本条用于概念澄清，不报告提速幅度','本地正式全文核查')
add(6,'AlphaFold 预测三维坐标而非完整模拟折叠历程','S04','The AlphaFold network; Fig.1; Methods 输入说明','结构预测','神经网络，序列及相关进化信息','原始研究有 CASP14 等结构评价，不是 CDK20 效率对照','网络利用序列、MSA、相关特征及模板信息预测结构','结构误差与置信度不是药物效果','计算结构是可检验的研究模型','不将预测坐标当作真实测定或完整生物系统模拟','结构置信度和局部构象需单独评价')
add(7,'Chemistry42 将生成模型和评价模块结合','S05','Overview of the Generative Capabilities of the Chemistry42 Platform; Fig.1–2','生成方法背景','生成模型集成，评分、过滤与反馈','平台一般方法，不是本案例各组件消融对照','2023平台文章描述多类生成器、评分和规则模块','平台版本相关；不报告本案例算力或模型数','生成不等于只用聊天模型写配方','平台一般功能不代表主案例全部使用；不是独立重复验证','完整平台为商业系统，与主案例团队重叠')
add(8,'PandaOmics 提出并排序靶点假设，研究者选择 CDK20','S02','Target selection and identification; Materials and methods / Target ID and target proposal','靶点选择','疾病数据与文献信息整合、筛选、人工审阅','作者报告10个数据集，1133 disease samples 与674 healthy controls；非新患者干预','形成靶点优先级并选定 CDK20','聚合数据样本；不视为临床试验受试者','数据整合帮助提出靶点研究假设','不称全部过程无人参与或疾病关联即因果','平台打分、筛选条件与既有信息会影响选择')
add(9,'低置信度结构区域经过处理','S02','Generation of novel hits targeting CDK20 by using AlphaFold predicted structures; Fig.4A','结构处理','AlphaFold DB 已有模型及结构处理','无原始实验结构的同任务对照','去掉低置信度 C 端，使用 Met1–Ile302 区域用于生成','模型为 AF-Q8IZL9-F1-model_v1；当时模型','研究者使用并处理预测信息，而非直接接受整个模型','不声称当今仍没有该靶点实验结构；不称处理已被晶体结构证实','结构处理本身引入假设；整体置信度不保证局部正确')
add(10,'主案例为结构引导候选物生成','S02','Generation of novel hits targeting CDK20 by using AlphaFold predicted structures; Fig.3–4','分子生成','结合口袋形状与约束指导 Chemistry42 生成','生成设计信息，不是化合物的物理样本','利用处理后的预测结构与结合区域信息提出结构','设计约束不是测定结果','AI 与结构信息协同提出候选结构','不宣称全部结构均易合成、安全或有实验活性','平台方法细节不完全公开')
add(11,'8918、54、7 对应不同阶段','S02','Generation of novel hits targeting CDK20 by using AlphaFold predicted structures; Fig.5','首轮筛选与合成','生成、对接、聚类、选择','没有同候选库同预算非AI分支','生成8918个，优先考虑54个，合成选择7个','计数；不是7个全部成功','先计算探索，再合成选定集合','不计算8918/7为提速倍数、实验减少比例或全部成功率','缺少比较流程及未选择对象的统一实验结果')
add(12,'补充材料记录真实合成及分子表征','S02-SI','PDF共16页；Synthesis of compounds；ISM042-2-001 及 ISM042-2-048 条目','化学验证','合成与 NMR/LCMS 等表征记录','同一研究的化学补充材料','存在对应分子的合成与表征描述','16页；不作为生物疗效统计','设计结构有真实化学实验支持','补充材料不是独立研究、患者试验或提速对照','原始PDF的交叉引用指针需宽容解析；文本已逐页提取','原始补充PDF逐页文本核查')
add(13,'30天终点为首个实验确认结合命中物','S02','Abstract; Introduction 末段; Results and discussion 首段','首次命中','平台整合与实验','没有同任务的传统流程时间对照','从 target selection 到 first hit 的作者报告耗时','30天；不是第二轮及后续完整周期','较快获得早期实验命中物','不称30天上市、完整优化、端到端从零建模或提速若干倍','基础数据、预训练与平台建设成本未用该数字衡量')
add(14,'首轮 ISM042-2-001 的结合结果','S02','Results and discussion 首段; Fig.6A caption','蛋白结合','CDK20 kinase binding assay / KINOMEscan','3次独立实验；示例曲线点为一次实验重复孔均值','Kd 9.2 ± 0.5 μM','均值±SD；n=3','首轮获得实验确认的结合命中物','结合不等于强功能抑制、细胞效果或患者效果','具体测定条件影响读出')
add(15,'首轮结合命中不代表强功能抑制','S02','Results and discussion 首段','蛋白功能','CDK20 kinase activity assay','与首轮分子结合结果分开解读','ISM042-2-001 IC50 >6000 nM','不等式；该界值不额外补造SD','首次命中物仍需优化','不称首轮已经获得强效抗癌药物','结合与功能指标和实验条件不同')
add(16,'首轮结合图的重复与误差有明确含义','S02','Fig.6A caption','统计解释','独立实验与重复孔区分','3次独立实验；代表性曲线为一次实验','Kd 为三次独立实验均值±SD','不能将代表性曲线重复孔作为独立实验数','明确解释 n 与误差含义','不把所有图的点都称为合并n=3均值','不同图注需分别核对')
add(17,'第二轮结合实验信息与预测姿势进行设计','S02','Results and discussion 第二轮段落; Fig.7','迭代设计','实验数据和预测结合姿势指导结构修改','与首轮阶段分开记录','16个新设计，其中6个合成测试','计数；独立于首轮7个','计算与实验构成继续优化的反馈','不把第二轮全部结果放入首次30天时间终点','没有完整报告同任务替代迭代流程耗时')
add(18,'第二轮 ISM042-2-048 结合能力改善','S02','Results and discussion; Fig.7–8A caption','蛋白结合','CDK20 binding assay','3次独立实验；均值±SD','Kd 566.7 ± 256.2 nM','nM；n=3；1 μM=1000 nM','后续分子结合更强，但保留误差','不作为效率倍数；不用预印本210 nM值替换','误差不可省略；比较限于对应指标')
add(19,'048 不是正文所有分子中最低 Kd','S02','Results and discussion 第二轮段落; Fig.7','候选物评价','结合测定与后续评价范围区分','第二轮048与049','ISM042-2-049 Kd 360.0 ± 14.1 nM','均值±SD；正文/图7第二轮实验','选择048作叙事对象是因有后续功能与细胞证据','不称048全球最强或最低Kd即综合最佳','049与048的后续评价证据不完全相同')
add(20,'048 的蛋白功能抑制有独立实验','S02','Results and discussion; Fig.9A caption; Materials and methods / CDK20 kinase activity assay','酶功能','放射性激酶活性测定','背景和无抑制剂活性对照；3次独立实验','IC50 33.4 ± 22.6 nM','均值±SD；n=3','048有目标酶功能抑制证据','不与Kd或细胞IC50混成同一药效尺度','未等同于全激酶组选择性或体内效果')
add(21,'细胞模型对048的敏感性不同','S02','Results and discussion; Fig.9B; Materials and methods / Cell viability assay','细胞评价','CellTiter-Glo 细胞活力读出','Huh7与counter-screen HEK293；两种模型','Huh7 IC50 208.7 ± 3.3 nM；HEK293 1706.7 ± 670.0 nM','保留原文误差；不额外给其SD计算规则补造解释','不同细胞模型有不同实验敏感性','HEK293不是正常肝细胞；不是人体治疗窗或安全性','多个模型差异；靶点特异的因果作用仍需证据')
add(22,'细胞图注与独立实验结果应分开读','S02','Fig.9B caption','统计解释','示例曲线与独立实验区分','一次实验中的重复孔均值；3次独立实验结果相似','图注说明代表性点及独立重复','正文给IC50误差，但图注未逐点称合并3次均值','按原图注描述，不替作者扩充统计设计','不把所有示例曲线点解释为三次独立实验平均','统计口径需要与具体图一致')
add(23,'完整药物要求及患者证据仍未覆盖','S02','Results and discussion 最后段; Conclusions; Materials and methods','证据边界','已报告实验范围审阅','没有本研究的动物或患者试验分支','作者把 ADME 和 kinase selectivity 评价列为后续工作','未报告而非证明无效','候选物需要继续评价','不称已证明患者疗效、安全或全面选择性','不把未报告当作否定结果；不概括2026年全部后续研究状态')
add(24,'生物测定对照不是研发方法对照','S02','Materials and methods / binding assay; kinase activity assay','实验对照','溶剂、背景和无抑制剂活性对照','DMSO对照；无激酶背景；无抑制剂活性','控制测定背景和正常化读出','不适用','这些对照支持生物测定解释','不作为AI相对传统发现效率的对照','两类对照解决不同问题')
add(25,'缺少同任务效率比较，提速幅度未知','S02','全正文，尤其Introduction、Results、Materials and methods','效率归因','研究设计审阅','无同目标同预算非AI路线；无逐组件效率消融','报告成功流程与30天，但没有可比提速分母','无可计算的效率倍数','展示快速早期发现能力，但幅度尚待比较','不把生成数/合成数、亲和力变化当作时间或总效率倍率','属于对已报告设计的评价，非作者另测出负面结果','全文设计核查加本资料分析')
add(26,'研究者参与选择、合成、对接与测定','S02','Author contributions; Fig.3–5 对应正文','人类参与','作者工作记录','非完全自主对照','作者贡献明确列出 compound selection/synthesis、docking、assays','不适用','计算与研究者实验协作','不称端到端全自动，无人选择或无人合成','贡献说明不量化各组件的独立贡献')
add(27,'模型评价与真实研发决策改善不同','S07','公开Abstract 最后句','领域评价','Perspective','不是独立药物发现比较实验','倡议评价工具改善决策的能力，而不止模型验证','不适用','用该区别审查本案例效率论证','不从摘要推导正文新数字或具体案例数据','公开摘要层级；观点不是直接实验','公开摘要核查')
add(28,'主案例有企业参与及利益披露','S02','Conflicts of interest; Code availability','来源质量','披露与可复现性审阅','不是失效或作假判断','Insilico相关参与，完整平台商业化，部分算法公开','不适用','记录利益与复现边界，并回到实验细节','不因利益披露直接否定结果，也不当作完全独立验证','商业流程不等同于仅凭公开脚本完全复现')
add(29,'平台方法论文与主案例不独立','S05','Author information / financial interests; Data Availability Statement','来源质量','团队、平台及引用关系审阅','与主案例有作者和平台重叠','声明作者为平台开发公司工作人员','不适用','平台论文解释机制，不充作独立重复成功','不以两篇相关论文冒充两次独立验证','开发者叙述须结合原始结果及披露')
add(30,'未来效率比较与质量检验方案','S02;S07','本资料第七节；针对E23与E25所识别缺口','未来研究','同目标同预算比较、组件比较及多性质验证','拟议设计，尚未实施','事先固定实验终点和活性标准；记录全投入与不确定性','不设虚构已完成实验阈值','作为具体可检验的研究方向','不称这些实验已完成或必然证明提速','是我们的建议；不是论文已观察结果','作者建议与本资料分析明确区分')

add(31,'既有患者组织关联支持进一步研究CCRK/CDK20','S08;S02','S08 Results / Overexpression of CCRK is associated with poor prognosis of HCC patients; Fig.10; S02确认CCRK别名','靶点依据：观察性关联','配对组织表达及预后分析','52对肿瘤与配对非肿瘤组织；不是给药试验','36/52（69.2%）表达升高；与分期及较短总生存关联','研究队列；不是全部肝癌人群比例','早于AI案例已有疾病关联证据','观察性关联不证明抑制该靶点改善患者生存','样本量与单项研究适用性有限；2011年数据不作为当前流行病学','正式发表官方HTML全文核查')
add(32,'表达干预和下游救援补充模型层面机制依据','S08','Results / Oncogenic properties of CCRK in HCC; Active β-catenin signaling is required...; Fig.5C及Fig.7E–F','靶点依据：模型干预','降低CCRK表达及下游信号救援','PLC5细胞shCCRK与对照；β-catenin/TCF活化救援','降低表达影响细胞周期；下游活化减轻集落形成受抑制','Fig.7为3次独立实验，均值+SD；不补造总体作用量','有干预证据支持靶点研究，而不止相关性','基因表达干预不等于药物抑制；不证明2023分子全部细胞作用均由CDK20引起','模型结果和特定条件不可直接推广为患者疗效','正式发表官方HTML全文核查')
add(33,'2011靶点模型实验不是2023分子验证','S08;S02','S08 Fig.5D及Fig.8; S02 Results / Conclusions / Materials and methods','研究之间证据分界','研究对象和干预方式比较','2011遗传表达干预模型与2023小分子实验分别记录','2011含动物模型；2023主案例未报告这些候选分子的动物或患者试验','不同研究、对象及终点，不合并数据','前期靶点依据与后期分子证据各归其研究','不能将2011动物结果标为2023候选物已通过动物试验','靶点可干预性、药物特异性和临床有效性仍是不同问题','两项正式全文核查与本资料分析')

add(34,'学术书章节区分选择靶点与选择作用分子','S10','Lengauer 2007 Vol.1 Chapter1 / The Molecular Approach to Curing Diseases，印刷第7页','基础概念','学术书公开章节','概念说明，不是AI效率实验','章节分别提出选择蛋白靶点和选择作用分子的问题','不适用','解释研究先确定作用对象再寻找分子','不引用书中旧统计为当前研发状态；不是2023案例结果','2007年基础书章节，不能支撑现代生成模型性能','出版社公开章节核查')
add(35,'选择性与结合能力是不同评价问题','S10;S02','S10印刷第7页；S02 Results 最后段','候选物质量背景','学术书概念与主案例后续计划区分','没有新增药物试验','书章节提及针对目标与避免其他蛋白作用；主案例计划后续激酶选择性评价','不适用','解释结合更强并不等于整体候选物质量已全面改善','不把书中一般原则当作本分子的选择性数据','选择性及其它性质需真实测定；章节不是最新综述','出版社公开章节与主案例全文核查')

with (BASE/'证据清单.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(ROWS)

logging.getLogger('pypdf').setLevel(logging.ERROR)
si=PdfReader(BASE/'sources/SC-014-D2SC05709C-s001.pdf')
page_index=[]
for i,p in enumerate(si.pages,1):
    t=p.extract_text() or ''
    ids=[x for x in ['ISM042-2-001','ISM042-2-048','ISM042-2-049'] if x in t]
    page_index.append({'page':i,'characters':len(t),'tracked_compounds':ids})
(BASE/'sources/补充材料页索引.json').write_text(json.dumps(page_index,ensure_ascii=False,indent=2),encoding='utf-8')

manifest=[]
for p in sorted((BASE/'sources').iterdir()):
    if p.is_file() and p.name!='source_manifest.json':
        manifest.append({'file':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(BASE/'sources/source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

print(f'CREATED evidence_rows={len(ROWS)} columns={len(FIELDS)} encoding=UTF-8-BOM')
print('SUPPLEMENT pages=16 page_index_saved=true')
