# 证据评价方法（v4）

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
| 诊断准确性研究 | QUADAS-2 | 4 域（病例选择、待评试验、参考标准、流程与时间）Low/High/Unclear | Whiting PF et al. Ann Intern Med 2011;155:529-36，https://doi.org/10.7326/0003-4819-155-8-201110180-00009 |
| 系统综述/Meta分析 | AMSTAR 2 | High/Moderate/Low/Critically low 置信度 | Shea BJ et al. BMJ 2017;358:j4008，https://doi.org/10.1136/bmj.j4008 ；PMC 全文 https://pmc.ncbi.nlm.nih.gov/articles/PMC5833365/ （原 amstar.ca/Amstar-2.php 链接已 404，v4 删除） |
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

## 4b. 报告规范补充（v4）
- 诊断准确性研究用 STARD 2015：Bossuyt PM et al. BMJ 2015;351:h5527，https://doi.org/10.1136/bmj.h5527 ；PMC 全文 https://pmc.ncbi.nlm.nih.gov/articles/PMC4623764/
- 犬猫 RCT 一律用 CONSORT 2010，不用 REFLECT（REFLECT 针对畜牧/食品动物）。

## 5. GRADE
GRADE 评价的是**某一主题的整体证据体**的确定性，不适用于单篇文献。单篇不赋 GRADE；字段 `grade_certainty_topic` 预留为空，待按主题做证据汇总时填写。https://www.gradeworkinggroup.org/

## 6. 其他字段
资助方、勘误与更正、论文内部矛盾、核实状态（全文已核/摘要级）、一句话中文结论、临床可用性照旧保留，与上述评价相互独立。


## 7. v4 新增规则

### 7.1 许可证与全文翻译（license / fulltext_translation_allowed）
- 来源：Europe PMC REST API（resultType=core）的 `isOpenAccess` 和 `license` 字段，2026-11-02 抓取。
- `fulltext_translation_allowed = true` 只限 CC BY、CC BY-SA、CC0。这些许可证允许改编（翻译属于改编），条件是署名，CC BY-SA 还要求以相同许可证共享。许可证文本：https://creativecommons.org/licenses/by/4.0/
- 以下情况一律为 false：
  - **CC BY-NC**：允许改编，但不得商业使用。我们无法保证用途非商业，所以设为 false；如果确定用途非商业，可另行人工评估。
  - **CC BY-ND / CC BY-NC-ND**：禁止发布改编作品，全文翻译不可发布。
  - 非 OA。
  - OA 但 Europe PMC 未标注许可证（记为"未核"）。
  - 非期刊文件，例如 IRIS 官网文件，版权归发布机构。
- 摘要级的中文一句话结论属于我们自己的概括，不受此字段限制。

### 7.2 诊断准确性研究
- RoB 工具用 QUADAS-2，报告规范用 STARD 2015（见第 2 节和 4b 节）。
- v3 中的诊断行（如 25231385、28152671）已在 v4 改用这套工具。

### 7.3 主题层 GRADE
- 只对 topics.json 中 status=pilot 的主题（ckd、fip）做 GRADE 草稿，见 topics/ckd.md 和 topics/fip.md。
- 均为单人草稿，未经第二人复核。
- 每行的 grade_certainty_topic 是所属主题的摘要。单篇研究不给 GRADE。

### 7.4 主题分类（topics.json）
- 顶层按 AVMA ABVS 认可专科和 ACVIM 专科划分，下级主题用 MeSH 主题词。
- 每个主题的 pubmed_query 都 AND 犬猫过滤（"Cats"[MeSH] OR "Dogs"[MeSH] 及 tiab 同义词）。
- 研究人群不是犬猫的文献，移到 seed_library_v4_excluded.json，不删除。

### 7.5 链接核查（2026-11-02）
- 本文所有链接都用 curl 逐一核查过。
- 返回 200 的链接直接保留。
- doi.org 上的 BMJ、ACP 等链接和 cebm.ox.ac.uk 返回 403，原因是站点拒绝自动抓取。DOI 句柄已经通过 doi.org handle API 解析正常；CEBM 页面通过 Web Archive 存档核对。
- amstar.ca 链接 404，已替换为上面的 DOI 和 PMC 链接。
