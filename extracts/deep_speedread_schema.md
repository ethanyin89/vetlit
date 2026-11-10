# 深度速读卡片数据（给 deep extract）

站点模板按 `extracts/deep_speedread/batch1.json` 的形状渲染，不要另起一套字段。用 `build_batch.py` 从每篇 `<pmid>.md` 生成该文件；站点用 `scripts/sync_deep_speedread.py` 只同步读者可见字段到 `data/v5/deep_speedread.json`。

## 每篇论文

| 字段 | 说明 |
|---|---|
| `pmid` | 必需，合并键 |
| `title_zh` | 卡片标题（只改该篇文献页，不改首页/专题列表上的旧标题） |
| `citation` | 作者、期刊、年、PMID、DOI。页头已有书目，模板不重复这一行 |
| `design_and_basis` | 设计 + 物种 + 依据（如「设盲……试验（犬）｜依据：全文……」），显示在临床结论上方 |
| `text_basis` | `全文` 或 `摘要……`，供核对；页脚「依据」以站点已有来源字段为准 |
| `section_order` | 节的键名列表，按此顺序渲染 |
| `sections` | `{ 键: { "heading": "中文标题", "markdown": "……" } }` |

`heading` 是读者看到的标题（可带「：中」或「（原文逐字，附 SOR）」）。`markdown` 是读者文本。HTML 注释 `<!-- -->` 为内部说明，模板会去掉。

## 节的键名（与 batch1 `_meta.section_keys` 一致）

临床结论 `clinical_bottom_line` · 临床问题 `clinical_question_pico` · 研究设计与对象 `design_and_subjects` · 范围与方法 `scope_and_methods` · 主要结果 `main_results` · 主要推荐 `main_recommendations` · 结论（作者原话）`authors_conclusion` · 评论 `commentary` · 证据确定性 `certainty` · 资金和利益冲突 `funding_coi`

后两节由站点已有的确定性表和资助栏渲染，不在速读正文里再写一遍。

## markdown 写法

与已批准样稿相同：`**小标题。**` 后接段落或列表；PICO 用两列表格（表头可空）；结果/推荐用多列表格；编号列表可嵌套。不要写「现版卡片」对照表。

## 不要写入读者文本或 `markdown` 的内容

规则号、`_meta`、字段名、流程状态、参与者或评审者姓名。核对清单、引文文件路径、`check` / `certainty_ref` / `source_md` 只留在 `batch1.json` 或 `_quotes.json`，不要进站点数据。

## 渲染须经明确批准

是否渲染只看 `data/v5/deep_speedread_approved.json`，不看一篇是否已出现在 `batch1.json`。`scripts/sync_deep_speedread.py` 也只同步该名单中的文献。Vibe 尚未审完的篇目不要写入批准名单。`26776588` 已批准渲染深度速读，但确定性标签仍显示「暂未评级（仅有摘要）」。
