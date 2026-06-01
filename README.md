# Viral Biogeochemistry Paper Tracker

这是一个面向“土壤/水体/沉积物环境中的病毒、噬菌体、AMGs 与生物地球化学循环”的静态论文追踪网页。当前主流程只使用 Semantic Scholar API，并通过 bulk search 尽量完整地回溯和每日更新文献。

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

1. 使用 Semantic Scholar bulk search 发现和回溯论文。
2. 用 Semantic Scholar batch API 回填引用数、参考文献数、开放 PDF、代表性参考文献和相似文章。
3. 将新增文献合并到现有 `data/papers.json`。
4. 自动提交数据变化。
5. 将静态网页发布到 `gh-pages` 分支。

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

现在不必须使用 Google Scholar。Semantic Scholar bulk search 已经用于默认历史回溯和每日更新。

可选补充流程：

1. 用 Semantic Scholar 每日自动更新作为主数据流。
2. 需要强制收录某些经典论文时，把 DOI 加入脚本中的种子列表或手动导入 CSV。
3. 如果你已经有 Google Scholar 或 Publish or Perish 导出的 CSV，可以作为人工补充导入。

导入已有 CSV：

```bash
python scripts/import_seed_csv.py exported_papers.csv --source-name "Manual seed"
```

默认每日更新使用：

```bash
python scripts/update_papers.py --retmax 5000 --sources semantic --semantic-search-mode bulk --merge-existing
```

可选：如果以后想临时启用多源补充，可手动运行：

```bash
python scripts/update_papers.py --retmax 800 --sources semantic,openalex,crossref,pubmed --merge-existing
```

## 数据来源与致谢

本项目使用开放学术数据服务构建文献追踪页面。感谢这些服务提供 API、元数据和开放学术基础设施：

- Semantic Scholar：默认唯一数据源；使用 bulk search 发现文献，并统一回填引用数、参考文献数、代表性参考文献、开放 PDF、摘要和学术图谱信息。
- Semantic Scholar Recommendations API：为部分论文预计算相似文章，用于网页详情区推荐延伸阅读。
- OpenAlex、Crossref、PubMed：当前不作为默认数据源；如以后需要扩大覆盖，可手动启用。
- Google Scholar：不作为自动数据源；如需使用，建议通过人工导出 CSV 后导入，不建议自动爬取。

引用数、参考文献数和代表性参考文献统一以 Semantic Scholar 回填结果为准，避免不同数据库的引用统计口径混用。

网页不会在浏览器端直接调用 Semantic Scholar API，因此不会暴露 API key。相似文章、引用指标和参考文献信息都由 GitHub Actions 在后台预计算后写入 `data/papers.json`。

也可以手动运行更广的多源更新：

```bash
python scripts/update_papers.py --retmax 800 --sources semantic,openalex,crossref,pubmed
```
