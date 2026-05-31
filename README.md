# Viral Biogeochemistry Paper Tracker

这是一个面向“土壤/水体/沉积物环境中的病毒、噬菌体、AMGs 与生物地球化学循环”的静态论文追踪网页。当前主流程使用 Semantic Scholar API 每日自动更新文献，并保留 OpenAlex、Crossref、PubMed 作为可选补充来源。

## 研究方向

- 土壤、水体、沉积物与水生环境：soil/soils、water/waterbody、lake、reservoir、pond、river、stream、creek、ditch、canal、channel、wetland、marsh、swamp、sediment/sediments、benthic 等
- 病毒、噬菌体、virome、host-virus interaction
- 辅助代谢基因：AMGs / auxiliary metabolic genes
- 生物地球化学循环：biogeochem*、碳、氮、硫、磷、甲烷、硝化、反硝化、硫酸盐还原等

## 免费发布到 GitHub Pages

1. 在 GitHub 新建一个仓库，例如 `viral-biogeochemistry-tracker`。
2. 把本文件夹里的内容推送到仓库的 `main` 分支。
3. 打开仓库的 `Settings` → `Pages`。
4. 在 `Build and deployment` 中选择 `Deploy from a branch`。
5. Branch 选择 `gh-pages`，Folder 选择 `/ (root)`。
6. 打开 `Actions` 页面，手动运行一次 `Update papers and deploy`。

发布后，网页地址通常是：

```text
https://你的用户名.github.io/viral-biogeochemistry-tracker/
```

## 自动更新

`.github/workflows/update-and-deploy.yml` 默认每天 UTC 21:18 运行一次，对应中国时间次日 05:18。它会：

1. 调用 `scripts/update_papers.py` 从 Semantic Scholar 抓取新增论文。
2. 将新增文献合并到现有 `data/papers.json`。
3. 自动提交数据变化。
4. 将静态网页发布到 `gh-pages` 分支。

建议在仓库的 `Settings` → `Secrets and variables` → `Actions` → `Variables` 里添加：

```text
CONTACT_EMAIL=你的邮箱
```

开放学术数据库通常不强制要求邮箱，但提供联系邮箱更符合礼貌访问和故障联系建议。

如果你申请了免费的 Semantic Scholar API key，可以在仓库 `Settings` → `Secrets and variables` → `Actions` → `Secrets` 里添加：

```text
SEMANTIC_SCHOLAR_API_KEY=你的 key
```

建议提供 key。没有 key 也可以运行，但更新速度更慢、限流更严格。

## 本地预览

在本文件夹运行：

```bash
python -m http.server 8000
```

然后打开：

```text
http://localhost:8000
```

## 调整检索式

如果想扩大或收窄论文范围，编辑 `scripts/update_papers.py` 里的 `ENVIRONMENT_TERMS`、`VIRUS_TERMS`、`ELEMENT_TERMS` 和 `BIOGEOCHEM_TERMS`。

## 基础库

现在不必须使用 Google Scholar。Semantic Scholar API 已经可以自动持续更新，OpenAlex、Crossref、PubMed 可用于手动补充历史文献。

可选补充流程：

1. 用 Semantic Scholar 每日自动更新作为主数据流。
2. 需要扩大历史覆盖时，手动运行 OpenAlex、Crossref、PubMed 多源补充。
3. 如果你已经有 Google Scholar 或 Publish or Perish 导出的 CSV，可以作为人工补充导入。

导入已有 CSV：

```bash
python scripts/import_seed_csv.py exported_papers.csv --source-name "Manual seed"
```

用开放数据库补充历史库：

```bash
python scripts/update_papers.py --retmax 300 --sources openalex,crossref,pubmed --merge-existing
```

每日增量更新使用：

```bash
python scripts/update_papers.py --retmax 300 --sources semantic --merge-existing
```

## 数据来源与致谢

本项目使用开放学术数据服务构建文献追踪页面。感谢这些服务提供 API、元数据和开放学术基础设施：

- Semantic Scholar：主更新来源，并统一回填引用数、参考文献数、代表性参考文献、开放 PDF、摘要和学术图谱信息。
- OpenAlex：可选补充来源，主要用于发现环境科学、生态学、地球科学与交叉学科文献及 DOI。
- Crossref：可选补充来源，主要用于发现 DOI 和出版社元数据。
- PubMed：适合补充生命科学、微生物、病毒相关记录及 PMID。
- Google Scholar：不作为自动数据源；如需使用，建议通过人工导出 CSV 后导入，不建议自动爬取。

引用数、参考文献数和代表性参考文献统一以 Semantic Scholar 回填结果为准。OpenAlex、Crossref、PubMed 主要用于扩展发现范围，避免不同数据库的引用统计口径混用。

也可以手动运行更广的多源更新：

```bash
python scripts/update_papers.py --retmax 160 --sources semantic,openalex,crossref,pubmed
```
