# 证据评价方法（v3）

本站**不自创评价标准**，每篇文献只记录业内公认工具的结果，各维度分开呈现，不合成单一"总分/等级"。

## 1. 证据水平：Oxford CEBM 2011 Levels of Evidence
- 来源：OCEBM Levels of Evidence Working Group. *The Oxford 2011 Levels of Evidence*. Oxford Centre for Evidence-Based Medicine. https://www.cebm.ox.ac.uk/resources/levels-of-evidence/ocebm-levels-of-evidence （官方表 PDF：https://www.cebm.ox.ac.uk/files/levels-of-evidence/cebm-levels-of-evidence-2-1.pdf ，2026-11-02 经 Web Archive 存档核对原文）
- 按"临床问题类型"定级：患病率、诊断、预后、治疗获益、治疗危害、筛查。例：治疗获益——Level 1 随机试验的系统综述；Level 2 随机试验或效应极显著的观察性研究；Level 3 非随机对照队列/随访研究；Level 4 病例系列、病例对照或历史对照；Level 5 基于机制的推理。预后——Level 2 起始队列；Level 3 队列研究或RCT对照组；Level 4 病例系列、病例对照或质量差的预后队列。
- OCEBM 表注允许按研究质量、不精确、间接性等下调或因效应量大上调。**本站不做任何下调/上调**，只记录按设计得出的原始 Level；质量问题见第 2 节。
- 指南/共识、叙述性综述、无临床问题的基础/行为学研究：标"不适用"。

## 2. 偏倚风险（rob_tool / rob_judgement）
| 研究类型 | 工具 | 判断档位 | 官方来源 |
|---|---|---|---|
| 随机对照试验 | Cochrane RoB 2 | Low / Some concerns / High | https://www.riskofbias.info/welcome/rob-2-0-tool |
| 非随机干预研究 | ROBINS-I | Low / Moderate / Serious / Critical | https://www.riskofbias.info/welcome/home |
| 预后因素研究 | QUIPS（6 个领域：研究参与、失访、预后因素测量、结局测量、混杂、统计分析与报告） | 各领域 Low/Moderate/High | Hayden JA et al. Ann Intern Med 2013;158:280-6. https://doi.org/10.7326/0003-4819-158-4-201302190-00009 |
| 实验动物研究 | SYRCLE RoB（10 项；官方不设总分） | 逐项 Yes/No/Unclear | Hooijmans CR et al. BMC Med Res Methodol 2014;14:43. https://doi.org/10.1186/1471-2288-14-43 |
| 系统综述/Meta分析 | AMSTAR 2 | High/Moderate/Low/Critically low 置信度 | https://amstar.ca/Amstar-2.php ；Shea BJ et al. BMJ 2017;358:j4008 |
| 指南/共识 | AGREE II（评价工具） | 6 领域评分 | https://www.agreetrust.org/resource-centre/agree-ii/ |
| 无干预的描述性/横断面研究 | 无对应通用工具 | "未评" | — |

规则：只依据已读到的内容判断；只有摘要时一律标 **"未评（仅摘要）"**，不猜测。提前终止、替代终点、厂商资助、失访分别作为偏倚领域考虑或间接性/利益冲突信息单列（资助方字段），**不再做自定义降级**。

## 3. 指南推荐强度（guideline_recommendation）
直接引用指南自身使用的分级体系，不用 CEBM 覆盖。例如 ACVIM 2019 MMVD 指南（Keene 等）采用改编自 AHA 的 Class I–IV + 证据质量；ACVIM 2020 猫心肌病声明（Luis Fuentes 等）采用 high/medium/low 证据等级 + "is recommended / should be considered / may be considered / is not recommended"。指南未分级的照实写"未分级"；尚未读原文的写"未核"。

## 4. 报告规范（reporting_checklist）
- RCT（含犬猫临床试验）：CONSORT 2010 https://www.consort-statement.org/ （REFLECT 面向畜牧/食品安全试验，本库不用）
- 观察性研究：STROBE-Vet https://doi.org/10.1111/jvim.14592 （Sargeant JM 等, JVIM 2016）
- 动物实验：ARRIVE 2.0 https://arriveguidelines.org/
- 系统综述：PRISMA 2020 https://www.prisma-statement.org/
- 指南：AGREE 报告清单 / RIGHT https://www.agreetrust.org/ ；https://www.equator-network.org/reporting-guidelines/right-statement/
（列出的是"适用的清单"，不代表已逐项核对符合度。）

## 5. GRADE
GRADE 评价的是**某一主题的整体证据体**的确定性，不适用于单篇文献。单篇不赋 GRADE；字段 `grade_certainty_topic` 预留为空，待按主题做证据汇总时填写。https://www.gradeworkinggroup.org/

## 6. 其他字段
资助方、勘误与更正、论文内部矛盾、核实状态（全文已核/摘要级）、一句话中文结论、临床可用性照旧保留，与上述评价相互独立。
