const state = {
  papers: [],
  filter: "all",
  source: "all",
  query: "",
  sortKey: "publication_date",
  sortDirection: "desc",
  expanded: new Set(),
};

const filterNames = {
  all: "全部主题",
  soil: "土壤",
  water: "水体/水生",
  virus: "病毒/噬菌体",
  amg: "AMGs",
  carbon: "碳循环",
  nitrogen: "氮循环",
  sulfur: "硫循环",
  phosphorus: "磷循环",
  sediment: "沉积物",
};

const tagLabels = {
  soil: "土壤",
  water: "水体/水生",
  virus: "病毒/噬菌体",
  amg: "AMGs",
  carbon: "碳",
  nitrogen: "氮",
  sulfur: "硫",
  phosphorus: "磷",
  sediment: "沉积物",
  biogeochemistry: "生物地球化学",
};

const els = {
  lastUpdated: document.querySelector("#last-updated"),
  paperCount: document.querySelector("#paper-count"),
  sourceCount: document.querySelector("#source-count"),
  weekCount: document.querySelector("#week-count"),
  monthCount: document.querySelector("#month-count"),
  yearCount: document.querySelector("#year-count"),
  citationTotal: document.querySelector("#citation-total"),
  pdfCount: document.querySelector("#pdf-count"),
  amgCount: document.querySelector("#amg-count"),
  resultCount: document.querySelector("#result-count"),
  tbody: document.querySelector("#papers-body"),
  empty: document.querySelector("#empty-state"),
  search: document.querySelector("#search"),
  sourceSelect: document.querySelector("#source-filter"),
  chips: document.querySelectorAll(".chip"),
  sortButtons: document.querySelectorAll("[data-sort]"),
};

fetch("data/papers.json", { cache: "no-store" })
  .then((response) => {
    if (!response.ok) {
      throw new Error("Paper data could not be loaded.");
    }
    return response.json();
  })
  .then((data) => {
    state.papers = data.papers || [];
    els.lastUpdated.textContent = formatDate(data.updated_at);
    updateSourceLabel(data);
    updateStats();
    populateSources();
    render();
  })
  .catch(() => {
    els.lastUpdated.textContent = "暂未更新";
    els.resultCount.textContent = "数据读取失败";
    els.empty.hidden = false;
  });

els.search.addEventListener("input", (event) => {
  state.query = event.target.value.trim().toLowerCase();
  render();
});

els.sourceSelect.addEventListener("change", (event) => {
  state.source = event.target.value;
  render();
});

els.chips.forEach((chip) => {
  chip.addEventListener("click", () => {
    state.filter = chip.dataset.filter;
    els.chips.forEach((item) => item.classList.toggle("active", item === chip));
    render();
  });
});

els.sortButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const key = button.dataset.sort;
    if (state.sortKey === key) {
      state.sortDirection = state.sortDirection === "asc" ? "desc" : "asc";
    } else {
      state.sortKey = key;
      state.sortDirection = key === "title" ? "asc" : "desc";
    }
    render();
  });
});

els.tbody.addEventListener("click", (event) => {
  const row = event.target.closest("[data-paper-row]");
  if (!row || event.target.closest("a")) {
    return;
  }
  const id = row.dataset.paperRow;
  if (state.expanded.has(id)) {
    state.expanded.delete(id);
  } else {
    state.expanded.add(id);
  }
  render();
});

function updateSourceLabel(data) {
  const sources = data.sources || [data.source].filter(Boolean);
  els.sourceCount.textContent = sources.join(" + ") || "OpenAlex + Crossref";
}

function populateSources() {
  const sources = [...new Set(state.papers.map((paper) => paper.source).filter(Boolean))].sort();
  els.sourceSelect.innerHTML = [
    '<option value="all">全部来源</option>',
    ...sources.map((source) => `<option value="${escapeHtml(source)}">${escapeHtml(source)}</option>`),
  ].join("");
}

function updateStats() {
  const now = new Date();
  const oneWeekAgo = new Date(now);
  oneWeekAgo.setDate(now.getDate() - 7);
  const oneMonthAgo = new Date(now);
  oneMonthAgo.setMonth(now.getMonth() - 1);
  const oneYearAgo = new Date(now);
  oneYearAgo.setFullYear(now.getFullYear() - 1);

  els.paperCount.textContent = state.papers.length;
  els.weekCount.textContent = countSince(oneWeekAgo);
  els.monthCount.textContent = countSince(oneMonthAgo);
  els.yearCount.textContent = countSince(oneYearAgo);
  els.citationTotal.textContent = formatNumber(
    state.papers.reduce((sum, paper) => sum + Number(paper.citation_count || 0), 0)
  );
  els.pdfCount.textContent = state.papers.filter((paper) => paper.pdf_url).length;
  els.amgCount.textContent = state.papers.filter((paper) => paper.tags.includes("amg")).length;
}

function countSince(date) {
  return state.papers.filter((paper) => {
    const publicationDate = new Date(paper.publication_date);
    return paper.publication_date && !Number.isNaN(publicationDate.getTime()) && publicationDate >= date;
  }).length;
}

function render() {
  const filtered = sortPapers(state.papers.filter(matchesFilters));
  els.resultCount.textContent = `${filterNames[state.filter]} · ${filtered.length} 篇`;
  els.empty.hidden = filtered.length > 0;
  els.tbody.innerHTML = filtered.map(renderPaperRow).join("");
  updateSortIndicators();
}

function matchesFilters(paper) {
  const text = [
    paper.title,
    paper.abstract,
    paper.journal,
    paper.authors?.join(" "),
      paper.doi,
      paper.pmid,
      paper.source,
      paper.citation_count,
      paper.reference_count,
      paper.tags?.join(" "),
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  const matchesText = !state.query || text.includes(state.query);
  const matchesTag = state.filter === "all" || paper.tags.includes(state.filter);
  const matchesSource = state.source === "all" || paper.source === state.source;
  return matchesText && matchesTag && matchesSource;
}

function sortPapers(papers) {
  return [...papers].sort((a, b) => {
    const left = getSortValue(a, state.sortKey);
    const right = getSortValue(b, state.sortKey);
    const result = left.localeCompare(right, undefined, { numeric: true, sensitivity: "base" });
    return state.sortDirection === "asc" ? result : -result;
  });
}

function getSortValue(paper, key) {
  if (key === "authors") {
    return paper.authors?.[0] || "";
  }
  if (key === "citation_count") {
    return String(Number(paper.citation_count || 0)).padStart(8, "0");
  }
  if (key === "reference_count") {
    return String(Number(paper.reference_count || 0)).padStart(8, "0");
  }
  return String(paper[key] || "");
}

function renderPaperRow(paper) {
  const id = paper.id || paper.doi || paper.pmid || paper.title;
  const authors = paper.authors?.slice(0, 3).join(", ") || "作者待更新";
  const moreAuthors = paper.authors?.length > 3 ? " 等" : "";
  const tags = (paper.tags || [])
    .map((tag) => `<span class="tag">${tagLabels[tag] || tag}</span>`)
    .join("");
  const expanded = state.expanded.has(id);
  const doiLink = paper.doi ? `https://doi.org/${encodeURIComponent(paper.doi)}` : "";
  const primaryUrl = paper.url || doiLink;

  return `
    <tr class="paper-row" data-paper-row="${escapeHtml(id)}" aria-expanded="${expanded}">
      <td class="date-cell">${escapeHtml(formatDate(paper.publication_date))}</td>
      <td>
        <strong class="paper-title">${escapeHtml(paper.title || "Untitled")}</strong>
        <div class="paper-tags">${tags}</div>
      </td>
      <td>${escapeHtml(authors + moreAuthors)}</td>
      <td>${escapeHtml(paper.journal || "Unknown")}</td>
      <td class="citation-cell">${escapeHtml(formatNumber(paper.citation_count || 0))}</td>
      <td class="citation-cell">${escapeHtml(formatNumber(paper.reference_count || 0))}</td>
      <td><span class="source-pill">${escapeHtml(paper.source || "Unknown")}</span></td>
      <td class="link-cell">
        ${primaryUrl ? `<a href="${primaryUrl}" target="_blank" rel="noreferrer">打开</a>` : ""}
        ${paper.pdf_url ? `<a href="${paper.pdf_url}" target="_blank" rel="noreferrer">PDF</a>` : ""}
        ${doiLink && doiLink !== primaryUrl ? `<a href="${doiLink}" target="_blank" rel="noreferrer">DOI</a>` : ""}
      </td>
    </tr>
    <tr class="detail-row ${expanded ? "open" : ""}">
      <td colspan="8">
        <div class="detail-panel">
          <p>${escapeHtml(paper.abstract || "暂无摘要。")}</p>
          <dl>
            <div><dt>DOI</dt><dd>${renderDoi(paper.doi)}</dd></div>
            <div><dt>PMID</dt><dd>${escapeHtml(paper.pmid || "无")}</dd></div>
            <div><dt>高影响引用</dt><dd>${escapeHtml(formatNumber(paper.influential_citation_count || 0))}</dd></div>
            <div><dt>数据库 ID</dt><dd>${escapeHtml(paper.id || "暂无")}</dd></div>
          </dl>
          ${renderReferences(paper.references || [])}
        </div>
      </td>
    </tr>
  `;
}

function renderReferences(references) {
  if (!references.length) {
    return "";
  }
  return `
    <div class="reference-list">
      <h4>代表性参考文献</h4>
      <ol>
        ${references
          .map((reference) => {
            const title = escapeHtml(reference.title || "Untitled");
            const year = reference.year ? ` (${escapeHtml(reference.year)})` : "";
            const label = `${title}${year}`;
            return `<li>${reference.url ? `<a href="${reference.url}" target="_blank" rel="noreferrer">${label}</a>` : label}</li>`;
          })
          .join("")}
      </ol>
    </div>
  `;
}

function renderDoi(doi) {
  if (!doi) {
    return "暂无";
  }
  const safeDoi = escapeHtml(doi);
  return `<a href="https://doi.org/${encodeURIComponent(doi)}" target="_blank" rel="noreferrer">${safeDoi}</a>`;
}

function formatNumber(value) {
  return new Intl.NumberFormat("zh-CN").format(Number(value || 0));
}

function updateSortIndicators() {
  els.sortButtons.forEach((button) => {
    const active = button.dataset.sort === state.sortKey;
    button.dataset.active = String(active);
    button.querySelector("span").textContent = active ? (state.sortDirection === "asc" ? "↑" : "↓") : "";
  });
}

function formatDate(value) {
  if (!value) {
    return "日期待更新";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
