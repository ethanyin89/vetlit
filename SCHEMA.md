# VetLit 数据 Schema（v3，2026-11-02）

One JSON file per paper: `data/papers/<id>.json`, where `<id>` = `pmid-<PMID>` (or `x-<slug>` when there is no PMID, e.g. IRIS online guidelines).
**Canonical field names = Vibe Feline `seed_library_v3.json`.** Deliveries are merged **by PMID** (`scripts/merge_import.py`); the build reads the canonical fields through an adapter (`view()` in `build.py`), so the data can be swapped wholesale.

## A. Canonical fields (Vibe Feline `seed_library_v3.json`)
| field | values | meaning |
|---|---|---|
| specialty | `/`-separated: 肾脏, 心脏, 内分泌, 营养, 行为/认知, 流行病学（日本） … | 专科（显示映射：肾脏→肾病，心脏→心血管，行为/认知→行为与认知，流行病学（日本）→日本流行病学） |
| species | 猫 / 犬 / 猫/犬 | 物种 |
| title, first_author, year, journal, doi | string | 书目（英文原文） |
| pmid | string; "" if none | **merge key** |
| source | PubMed/Europe PMC or URL | 书目来源 |
| oa | 是 / 否 / 未核 | 开放获取 |
| doc_type | 原始研究、RCT、回顾性队列、系统综述/Meta分析、指南/共识、叙述性综述 … | 文献类型 |
| recommendation_basis | 不适用 / 部分基于专家意见 / 主要基于专家意见 … | 推荐依据（指南） |
| sample_size_analysed | free text; 未核 / 不适用 | 实际分析样本量 |
| multicenter | free text; may contain “推断” | 多中心（“推断”在页面高亮） |
| funding | free text; 未核 | 资助方（独立信息，不影响评价） |
| errata | erratum PMID(s) or "" | 勘误与更正 |
| internal_inconsistency | free text or "" | 论文内部矛盾 |
| one_line_conclusion_zh | free text | 一句话中文结论 |
| clinical_utility | 改变诊疗 / 提示性 / 背景 | 临床可用性 |
| verified | yes / partial | yes → “全文已核”；partial → “摘要级” |
| japan_source | 是 / 否 | 日本来源 |
| **cebm_question** | 治疗获益 / 治疗危害 / 预后 / 诊断 / 患病率 / 筛查 / 病因 …; “—” if none | CEBM 定级所针对的临床问题 |
| **cebm_level** | "1"–"5"; or 不适用（…）text | Oxford CEBM 2011 原始 Level（不作上/下调） |
| **cebm_basis** | free text | 定级依据（设计） |
| **rob_tool** | Cochrane RoB 2 / ROBINS-I / QUIPS / SYRCLE / AMSTAR 2 / AGREE II（评价工具） / 未评（…） / 不适用 | 偏倚风险或质量评价工具 |
| **rob_judgement** | in the tool's own categories (RoB 2: Low / Some concerns / High; ROBINS-I: Low / Moderate / Serious / Critical; AMSTAR 2: High / Moderate / Low / Critically low; QUIPS: per-domain Low/Moderate/High; SYRCLE: no overall), or **未评（仅摘要）** / 不适用 | 判断；页面逐字显示 |
| **rob_rationale** | free text, per domain | 分领域理由 |
| **guideline_recommendation** | verbatim from the guideline's own system, or 未分级 / 未核 / 不适用 | 指南推荐强度（原文） |
| **reporting_checklist** | CONSORT 2010（犬猫 RCT；REFLECT 仅用于畜牧/食品安全，不用）/ STROBE-Vet / ARRIVE 2.0 / PRISMA 2020 / AGREE 报告清单 / RIGHT / 无（…） | 适用报告规范（不代表已核对符合度） |
| **grade_certainty_topic** | 高 / 中 / 低 / 极低 / "" | GRADE 仅用于**专题证据体**；单篇保持为空 |

**Removed (v3):** `evidence_grade`, `grade_v1`, `grade_reason`, `downgrade_tags` — no custom A–D/共识 grades or downgrade rules anywhere. The importer and build drop them if present.
Evaluation method and official tool sources: `content/_rules.md` (= /workspace/vetlit/grading_method.md), rendered as the 证据评价方法 page.
Missing evaluation fields display as **待评**; values such as 未评（仅摘要）/ 不适用 display exactly as in the data.

## B. Site / deep-extract extension fields (optional)
| field | type | meaning |
|---|---|---|
| id | string | file id (`pmid-…`) |
| title_zh | string | 中文标题 |
| date | YYYY-MM-DD | 出版日期（排序“最新”用；缺省用 year） |
| pmcid | string | Europe PMC 全文链接 |
| status | 已收录 / 待处理 / 已处理 | 待处理 = 每日检索新条目，未核 |
| detail | filename in `content/` | deep extract 速读页 markdown |
| fulltext_status | 全文 / 仅摘要 | deep extract 读到的材料 |
| errata_detail | [{type, pmid?, doi?, date?, note}] | 勘误详情（优先于 errata） |
| internal_inconsistency_detail | [string] | 内部矛盾逐条（优先于 internal_inconsistency） |
| recommendation_basis_detail | string | 哪些推荐主要基于专家经验 |
| recommendation_strength | string | 推荐强度 |
| scope, core_recommendations, evidence_gaps, changes_vs_previous | string or [string] | 指南模板：适用范围 / 核心推荐（附推荐强度）/ 证据薄弱点 / 与旧版相比的变化 |
| detail_md | string (import only) | 速读页 markdown；导入时写入 content/<id>.md |
| provenance | [string] | 数据来源（vibe-feline-v2, deep-extract, site-curated, ingest） |
| ingested_at, publication_types, mesh | ingest only | 每日检索元数据 |

## C. Deep-extract reading page (markdown, `content/<id>.md`)
Sections: 1 一句话结论 + 证据等级 · 2 研究卡片（指南用模板）· 3 关键结果 · 4 方法学审读 · 5 四阶段整理 / 能说明·不能说明 · 6 中英对照翻译（仅 OA）· 7 术语对照 · 勘误、内部矛盾。
Legacy “证据等级：A–D” lines inside reading pages are stripped at build time (`strip_legacy_grades`); new pages should not contain them.

## D. Merge rules (`scripts/merge_import.py`)
- Key: `pmid` (Chinese aliases such as 资助方/勘误/内部矛盾/推荐依据/文献类型 are normalised to canonical names).
- Non-empty incoming values overwrite; empty values never erase; `*_detail` lists are unioned.
- Unknown PMIDs create new files with `status: 待处理`.
