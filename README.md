# Viral Biogeochemistry Paper Tracker

这是一个面向“土壤/水体/沉积物环境中的病毒、噬菌体、AMGs 与生物地球化学循环”的静态论文追踪网页。推荐先整理一个历史基础库，再用 Semantic Scholar 每日自动更新新增文献。

## 研究方向

- 土壤、水体、沉积物与水生环境：soil/soils、water/waterbody、lake、reservoir、pond、river、stream、creek、ditch、canal、channel、wetland、marsh、swamp、sediment/sediments、benthic 等
- 病毒、噬菌体、virome、host-virus interaction
- 辅助代谢基因：AMGs / auxiliary metabolic genes
- 生物地球化学循环：biogeochem*、碳、氮、硫、磷、甲烷、硝化、反硝化、硫酸盐还原等

## 免费发布到 GitHub Pages

1. 在 GitHub 新建一个仓库，例如 `viral-biogeochemistry-tracker`。
2. 把本文件夹里的内容推送到仓库的 `main` 分支。
3. 打开仓库的 `Settings` → `Pages`。
4. 在 `Build and deployment` 中选择 `GitHub Actions`。
5. 打开 `Actions` 页面，手动运行一次 `Update papers and deploy`。

发布后，网页地址通常是：

```text
https://你的用户名.github.io/viral-biogeochemistry-tracker/
```

## 自动更新

`.github/workflows/update-and-deploy.yml` 默认每天 UTC 21:18 运行一次，对应中国时间次日 05:18。它会：

1. 调用 `scripts/update_papers.py` 从 Semantic Scholar 抓取新增论文。
2. 从 Semantic Scholar 抓取新增文献，并合并到现有 `data/papers.json`。
3. 自动提交数据变化。
4. 部署到 GitHub Pages。

建议在仓库的 `Settings` → `Secrets and variables` → `Actions` → `Variables` 里添加：

```text
CONTACT_EMAIL=你的邮箱
```

开放学术数据库通常不强制要求邮箱，但提供联系邮箱更符合礼貌访问和故障联系建议。

如果你申请了免费的 Semantic Scholar API key，可以在仓库 `Settings` → `Secrets and variables` → `Actions` → `Secrets` 里添加：

```text
SEMANTIC_SCHOLAR_API_KEY=你的 key
```

没有 key 也可以运行，只是更新速度更慢、限流更严格。

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

## 建立基础库

推荐流程：

1. 用 Google Scholar 或 Publish or Perish 按你的检索式导出 CSV。
2. 用 PubMed、OpenAlex、Crossref 自动补充一轮。
3. 之后每天只用 Semantic Scholar 增量更新。

导入 Google Scholar / Publish or Perish CSV：

```bash
python scripts/import_seed_csv.py exported_papers.csv --source-name "Google Scholar seed"
```

用开放数据库补充基础库：

```bash
python scripts/update_papers.py --retmax 300 --sources openalex,crossref,pubmed --merge-existing
```

每日增量更新使用：

```bash
python scripts/update_papers.py --retmax 300 --sources semantic --merge-existing
```

## 数据来源

推荐用途：

- Google Scholar：适合人工建立最全历史基础库；建议通过 Publish or Perish 或 Scholar 手动导出，不建议自动爬取。
- PubMed：适合补充生命科学、微生物、病毒相关记录。
- OpenAlex：覆盖广，适合环境科学、生态学、地球科学与交叉学科。
- Crossref：适合补充 DOI 和出版社元数据。
- Semantic Scholar：适合每日增量更新，提供引用数、开放 PDF、摘要和学术图谱信息。

也可以手动运行更广的多源更新：

```bash
python scripts/update_papers.py --retmax 160 --sources semantic,openalex,crossref,pubmed
```
