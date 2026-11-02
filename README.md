# VetLit · 宠物医学文献速读（犬猫，专业版）

面向兽医、研究者与行业从业者的犬猫文献参考站：中文界面、英文原文，逐篇注明证据水平（Oxford CEBM 2011）、偏倚风险工具与判断、适用报告规范、指南原文推荐强度。**不构成临床诊疗建议。**

## 结构
- `data/papers/<id>.json`：每篇一个 JSON，字段见 **[SCHEMA.md](SCHEMA.md)**（规范字段 = Vibe Feline `seed_library_v3.json`）。
- `content/*.md`：deep extract 速读页；`content/_rules.md` 评价方法（= grading_method.md）；`content/_about.md` 方法与声明。
- `build.py`：零依赖静态生成 → `dist/`（首页 最新/重要、搜索、物种/专科/文献类型/CEBM/OA 筛选；详情页；BibTeX/RIS 单篇与批量；`feed.xml`；`papers.json`）。
- `scripts/ingest.py`：NCBI E-utilities 每日检索（目标期刊 × 猫/犬 MeSH × 排除评论/社论/勘误等），新条目写为 `status: 待处理`，不评定。
- `scripts/seed_import.py`：从 v3 JSON 全量导入并叠加站点扩展字段（速读页、勘误详情等）。
- `scripts/merge_import.py <file|dir> --source NAME`：按 PMID 合并新交付（Vibe Feline / deep extract），中文字段名自动映射。
- `scripts/check_links.py`：内部链接与 viewport 检查。
- `.github/workflows/daily.yml`：每日 10:30 UTC 检索 → 提交数据 → 构建 → 部署 GitHub Pages。

## 本地
```
python3 scripts/seed_import.py /path/to/seed_library_v3.json   # 可选：全量替换
python3 scripts/ingest.py
python3 build.py && python3 scripts/check_links.py
python3 -m http.server -d dist 8000
```
可选 Secrets：`NCBI_API_KEY`、`NCBI_EMAIL`。Pages 需在仓库设置中把 Source 设为 GitHub Actions。
