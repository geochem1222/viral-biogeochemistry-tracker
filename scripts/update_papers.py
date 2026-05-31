#!/usr/bin/env python3
"""Update paper metadata from open scholarly databases for the static tracker."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
OPENALEX_BASE = "https://api.openalex.org/works"
CROSSREF_BASE = "https://api.crossref.org/works"
SEMANTIC_SCHOLAR_BASE = "https://api.semanticscholar.org/graph/v1/paper/search"
SEMANTIC_SCHOLAR_BATCH_BASE = "https://api.semanticscholar.org/graph/v1/paper/batch"
SEMANTIC_SCHOLAR_RECOMMENDATIONS_BASE = "https://api.semanticscholar.org/recommendations/v1/papers"

ENVIRONMENT_TERMS = [
    "soil",
    "soils",
    "water",
    "waters",
    "waterbody",
    "waterbodies",
    "water body",
    "water bodies",
    "aquatic",
    "freshwater",
    "river",
    "rivers",
    "stream",
    "streams",
    "creek",
    "creeks",
    "ditch",
    "ditches",
    "canal",
    "canals",
    "channel",
    "channels",
    "drainage ditch",
    "drainage channel",
    "lake",
    "lakes",
    "reservoir",
    "reservoirs",
    "pond",
    "ponds",
    "wetland",
    "wetlands",
    "marsh",
    "swamp",
    "sediment",
    "sediments",
    "sedimentary",
    "benthic",
    "groundwater",
    "estuary",
]

VIRUS_TERMS = [
    "virus",
    "viral",
    "phage",
    "bacteriophage",
    "virome",
    "auxiliary metabolic genes",
    "AMGs",
]

ELEMENT_TERMS = [
    "carbon cycle",
    "nitrogen cycle",
    "sulfur cycle",
    "sulphur cycle",
    "phosphorus cycle",
    "carbon",
    "nitrogen",
    "sulfur",
    "sulphur",
    "phosphorus",
    "methane",
    "nitrification",
    "denitrification",
    "sulfate reduction",
    "phosphate",
]

BIOGEOCHEM_TERMS = [
    "biogeochem*",
    "biogeochemistry",
    "biogeochemical",
    "biogeochemical cycling",
]

ENVIRONMENT_GROUPS = [
    "soil soils",
    "water waters aquatic freshwater waterbody waterbodies",
    "river rivers stream streams creek creeks",
    "ditch ditches canal canals channel channels drainage ditch",
    "lake lakes reservoir reservoirs pond ponds",
    "wetland wetlands marsh swamp",
    "sediment sediments benthic",
    "groundwater estuary",
]

VIRUS_GROUPS = [
    "virus viral virome",
    "phage bacteriophage",
    "auxiliary metabolic genes AMGs",
]

ELEMENT_GROUPS = [
    "carbon cycle carbon methane",
    "nitrogen cycle nitrogen nitrification denitrification",
    "sulfur cycle sulphur cycle sulfur sulfate reduction",
    "phosphorus cycle phosphorus phosphate",
]

SEARCH_QUERIES = [
    f"{environment} {virus} {element} {BIOGEOCHEM_TERMS[(i + j + k) % len(BIOGEOCHEM_TERMS)]}"
    for i, environment in enumerate(ENVIRONMENT_GROUPS)
    for j, virus in enumerate(VIRUS_GROUPS)
    for k, element in enumerate(ELEMENT_GROUPS)
]

PUBMED_QUERY = """
(
  virus[Title/Abstract] OR viruses[Title/Abstract]
  OR "viral ecology"[Title/Abstract] OR phage[Title/Abstract]
  OR bacteriophage[Title/Abstract] OR bacteriophages[Title/Abstract]
  OR virome[Title/Abstract] OR viromes[Title/Abstract]
  OR "auxiliary metabolic gene"[Title/Abstract]
  OR "auxiliary metabolic genes"[Title/Abstract] OR AMG[Title/Abstract] OR AMGs[Title/Abstract]
)
AND
(
  biogeochemistry[Title/Abstract] OR biogeochemical[Title/Abstract]
  OR carbon[Title/Abstract] OR nitrogen[Title/Abstract]
  OR sulfur[Title/Abstract] OR sulphur[Title/Abstract]
  OR phosphorus[Title/Abstract] OR phosphate[Title/Abstract]
  OR methane[Title/Abstract] OR nitrification[Title/Abstract]
  OR denitrification[Title/Abstract] OR "carbon cycle"[Title/Abstract]
  OR "nitrogen cycle"[Title/Abstract] OR "sulfur cycle"[Title/Abstract]
  OR "phosphorus cycle"[Title/Abstract]
)
AND
(
  microbial[Title/Abstract] OR microbiome[Title/Abstract] OR metagenome[Title/Abstract]
  OR metagenomic[Title/Abstract] OR ecosystem[Title/Abstract] OR environmental[Title/Abstract]
  OR marine[Title/Abstract] OR ocean[Title/Abstract] OR seawater[Title/Abstract]
  OR freshwater[Title/Abstract] OR aquatic[Title/Abstract] OR lake[Title/Abstract]
  OR lakes[Title/Abstract] OR river[Title/Abstract] OR rivers[Title/Abstract]
  OR stream[Title/Abstract] OR streams[Title/Abstract] OR creek[Title/Abstract]
  OR creeks[Title/Abstract] OR ditch[Title/Abstract] OR ditches[Title/Abstract]
  OR canal[Title/Abstract] OR canals[Title/Abstract] OR channel[Title/Abstract]
  OR channels[Title/Abstract] OR reservoir[Title/Abstract] OR reservoirs[Title/Abstract]
  OR pond[Title/Abstract] OR ponds[Title/Abstract] OR wetland[Title/Abstract] OR wetlands[Title/Abstract] OR marsh[Title/Abstract]
  OR swamp[Title/Abstract] OR soil[Title/Abstract] OR sediment[Title/Abstract]
  OR sediments[Title/Abstract] OR sedimentary[Title/Abstract] OR benthic[Title/Abstract]
  OR groundwater[Title/Abstract] OR estuary[Title/Abstract] OR wastewater[Title/Abstract]
)
NOT
(
  patient[Title/Abstract] OR clinical[Title/Abstract] OR vaccine[Title/Abstract]
  OR cancer[Title/Abstract] OR tumor[Title/Abstract] OR tumour[Title/Abstract]
  OR transgenic[Title/Abstract] OR GMO[Title/Abstract] OR soybean[Title/Abstract]
)
""".replace("\n", " ")

TAG_RULES = {
    "soil": ["soil", "soils"],
    "water": [
        "water",
        "waters",
        "waterbody",
        "waterbodies",
        "water body",
        "water bodies",
        "aquatic",
        "freshwater",
        "river",
        "rivers",
        "stream",
        "streams",
        "creek",
        "creeks",
        "ditch",
        "ditches",
        "canal",
        "canals",
        "channel",
        "channels",
        "lake",
        "lakes",
        "reservoir",
        "reservoirs",
        "pond",
        "ponds",
        "wetland",
        "wetlands",
        "marsh",
        "swamp",
    ],
    "virus": ["virus", "viral", "virome", "phage", "bacteriophage"],
    "amg": ["auxiliary metabolic gene", "auxiliary metabolic genes", " amg", " amgs"],
    "carbon": ["carbon", "methane", "co2", "organic matter", "carbon pump"],
    "nitrogen": ["nitrogen", "nitrification", "denitrification", "ammonia", "ammonium", "nitrate"],
    "sulfur": ["sulfur", "sulphur", "sulfate", "sulphate", "sulfide"],
    "phosphorus": ["phosphorus", "phosphate", "phosphonate"],
    "sediment": ["sediment", "sediments", "sedimentary", "benthic"],
    "biogeochemistry": [
        "biogeochemistry",
        "biogeochemical",
        "element cycle",
        "nutrient cycle",
        "nutrient cycling",
        "metabolism",
        "microbial ecology",
    ],
}

NOISE_TERMS = [
    "patient",
    "clinical",
    "vaccine",
    "cancer",
    "tumor",
    "tumour",
    "transgenic",
    "gmo",
    "soybean",
]

ENVIRONMENT_KEYWORDS = [
    "soil",
    "soils",
    "water",
    "waters",
    "waterbody",
    "waterbodies",
    "water body",
    "water bodies",
    "aquatic",
    "freshwater",
    "river",
    "rivers",
    "stream",
    "streams",
    "creek",
    "creeks",
    "ditch",
    "ditches",
    "canal",
    "canals",
    "channel",
    "channels",
    "drainage ditch",
    "drainage channel",
    "lake",
    "lakes",
    "reservoir",
    "reservoirs",
    "pond",
    "ponds",
    "wetland",
    "wetlands",
    "marsh",
    "swamp",
    "sediment",
    "sediments",
    "sedimentary",
    "benthic",
    "groundwater",
    "estuary",
]


def request_json(
    url: str,
    params: dict[str, str | int],
    email: str | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    headers = {"User-Agent": build_user_agent(email)}
    if api_key:
        headers["x-api-key"] = api_key
    full_url = f"{url}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(full_url, headers=headers)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=50) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            if error.code == 429 and attempt < 2:
                retry_after = int(error.headers.get("Retry-After", "8"))
                time.sleep(retry_after + attempt * 4)
                continue
            raise
        except urllib.error.URLError:
            if attempt < 2:
                time.sleep(3 + attempt * 4)
                continue
            raise


def request_json_post(
    url: str,
    params: dict[str, str | int],
    payload: dict[str, Any],
    email: str | None = None,
    api_key: str | None = None,
) -> dict[str, Any] | list[Any]:
    headers = {
        "Content-Type": "application/json",
        "User-Agent": build_user_agent(email),
    }
    if api_key:
        headers["x-api-key"] = api_key
    full_url = f"{url}?{urllib.parse.urlencode(params)}"
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(full_url, data=body, headers=headers, method="POST")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            if error.code == 429 and attempt < 2:
                retry_after = int(error.headers.get("Retry-After", "8"))
                time.sleep(retry_after + attempt * 4)
                continue
            raise
        except urllib.error.URLError:
            if attempt < 2:
                time.sleep(3 + attempt * 4)
                continue
            raise


def request_xml(url: str, params: dict[str, str | int], email: str | None = None) -> ET.Element:
    headers = {"User-Agent": build_user_agent(email)}
    full_url = f"{url}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(full_url, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return ET.fromstring(response.read())


def build_user_agent(email: str | None) -> str:
    contact = f" mailto:{email}" if email else ""
    return f"viral-biogeochemistry-tracker/1.0{contact}"


def fetch_openalex(retmax: int, email: str | None, query_limit: int | None = None) -> list[dict[str, Any]]:
    queries = SEARCH_QUERIES[:query_limit] if query_limit else SEARCH_QUERIES
    per_query = max(8, min(50, retmax // max(1, len(queries)) + 5))
    papers: list[dict[str, Any]] = []
    for query in queries:
        params: dict[str, str | int] = {
            "search": query,
            "per-page": per_query,
            "sort": "publication_date:desc",
        }
        if email:
            params["mailto"] = email
        try:
            data = request_json(OPENALEX_BASE, params, email)
        except urllib.error.URLError:
            print(f"OpenAlex request failed for query: {query}")
            continue
        query_tags = classify(query)
        papers.extend(enrich_query_tags(parse_openalex_work(item), query_tags) for item in data.get("results", []))
        time.sleep(0.12)
    return [paper for paper in papers if paper and is_relevant(paper)]


def fetch_semantic_scholar(
    retmax: int,
    email: str | None,
    api_key: str | None,
    query_limit: int | None = None,
) -> list[dict[str, Any]]:
    queries = SEARCH_QUERIES[:query_limit] if query_limit else SEARCH_QUERIES
    per_query = max(8, min(50, retmax // max(1, len(queries)) + 6))
    papers: list[dict[str, Any]] = []
    fields = semantic_fields()
    for query in queries:
        params: dict[str, str | int] = {
            "query": query,
            "limit": per_query,
            "fields": fields,
        }
        try:
            data = request_json(SEMANTIC_SCHOLAR_BASE, params, email, api_key)
        except urllib.error.HTTPError as error:
            if error.code == 429:
                print("Semantic Scholar rate limit reached; continuing with collected and fallback sources.")
                break
            raise
        query_tags = classify(query)
        papers.extend(enrich_query_tags(parse_semantic_scholar_paper(item), query_tags) for item in data.get("data", []))
        time.sleep(0.35 if api_key else 1.05)
    return [paper for paper in papers if paper and is_relevant(paper)]


def parse_semantic_scholar_paper(item: dict[str, Any]) -> dict[str, Any]:
    external_ids = item.get("externalIds") or {}
    journal = item.get("venue") or (item.get("journal") or {}).get("name", "")
    publication_date = item.get("publicationDate") or (f"{item.get('year')}-01-01" if item.get("year") else "")
    doi = normalize_doi(external_ids.get("DOI", ""))
    open_pdf = item.get("openAccessPdf") or {}
    title = item.get("title") or ""
    abstract = item.get("abstract") or ""
    tags = classify(" ".join([title, abstract, journal]))
    return {
        "id": item.get("paperId", ""),
        "source": "Semantic Scholar",
        "pmid": external_ids.get("PubMed", ""),
        "doi": doi,
        "title": title,
        "authors": [author.get("name", "") for author in item.get("authors", []) if author.get("name")],
        "journal": journal,
        "publication_date": publication_date,
        "abstract": abstract,
        "url": item.get("url", "") or (f"https://doi.org/{doi}" if doi else ""),
        "pdf_url": open_pdf.get("url", ""),
        "citation_count": item.get("citationCount", 0),
        "influential_citation_count": item.get("influentialCitationCount", 0),
        "reference_count": item.get("referenceCount", 0),
        "references": parse_semantic_references(item.get("references", [])),
        "similar_papers": [],
        "fields_of_study": item.get("fieldsOfStudy") or [],
        "publication_types": item.get("publicationTypes") or [],
        "tldr": (item.get("tldr") or {}).get("text", ""),
        "metrics_source": "Semantic Scholar",
        "tags": tags,
    }


def semantic_fields() -> str:
    return ",".join(
        [
            "paperId",
            "title",
            "abstract",
            "year",
            "publicationDate",
            "venue",
            "journal",
            "authors",
            "externalIds",
            "fieldsOfStudy",
            "publicationTypes",
            "tldr",
            "url",
            "citationCount",
            "influentialCitationCount",
            "referenceCount",
            "references.title",
            "references.year",
            "references.url",
            "references.externalIds",
            "openAccessPdf",
        ]
    )


def enrich_with_semantic_metadata(
    papers: list[dict[str, Any]],
    email: str | None,
    api_key: str | None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    candidates = [
        paper
        for paper in papers
        if paper.get("doi") or paper.get("pmid")
    ]
    if limit:
        candidates = candidates[:limit]

    by_lookup_id: dict[str, dict[str, Any]] = {}
    ids: list[str] = []
    for paper in candidates:
        lookup_id = semantic_lookup_id(paper)
        if lookup_id and lookup_id not in by_lookup_id:
            by_lookup_id[lookup_id] = paper
            ids.append(lookup_id)

    for batch_ids in chunks(ids, 100):
        try:
            results = request_json_post(
                SEMANTIC_SCHOLAR_BATCH_BASE,
                {"fields": semantic_fields()},
                {"ids": batch_ids},
                email,
                api_key,
            )
        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            print(f"Semantic Scholar metadata enrichment failed for a batch: {error}")
            continue
        for lookup_id, result in zip(batch_ids, results if isinstance(results, list) else []):
            if not result:
                continue
            apply_semantic_metadata(by_lookup_id[lookup_id], result)
        time.sleep(0.35 if api_key else 1.05)

    return papers


def semantic_lookup_id(paper: dict[str, Any]) -> str:
    if paper.get("doi"):
        return f"DOI:{paper['doi']}"
    if paper.get("pmid"):
        return f"PMID:{paper['pmid']}"
    return ""


def apply_semantic_metadata(paper: dict[str, Any], item: dict[str, Any]) -> None:
    external_ids = item.get("externalIds") or {}
    open_pdf = item.get("openAccessPdf") or {}
    doi = normalize_doi(external_ids.get("DOI", ""))
    paper["semantic_scholar_id"] = item.get("paperId", paper.get("semantic_scholar_id", ""))
    paper["semantic_scholar_url"] = item.get("url", paper.get("semantic_scholar_url", ""))
    paper["citation_count"] = item.get("citationCount") or 0
    paper["influential_citation_count"] = item.get("influentialCitationCount") or 0
    paper["reference_count"] = item.get("referenceCount") or 0
    paper["references"] = parse_semantic_references(item.get("references"))
    paper["fields_of_study"] = item.get("fieldsOfStudy") or paper.get("fields_of_study", [])
    paper["publication_types"] = item.get("publicationTypes") or paper.get("publication_types", [])
    paper["tldr"] = (item.get("tldr") or {}).get("text", paper.get("tldr", ""))
    paper["metrics_source"] = "Semantic Scholar"
    if doi and not paper.get("doi"):
        paper["doi"] = doi
    if external_ids.get("PubMed") and not paper.get("pmid"):
        paper["pmid"] = external_ids["PubMed"]
    if open_pdf.get("url"):
        paper["pdf_url"] = open_pdf["url"]


def parse_semantic_references(references: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    if not references:
        return []
    parsed = []
    for reference in references[:8]:
        external_ids = reference.get("externalIds") or {}
        doi = normalize_doi(external_ids.get("DOI", ""))
        parsed.append(
            {
                "title": reference.get("title", ""),
                "year": reference.get("year", ""),
                "url": reference.get("url", "") or (f"https://doi.org/{doi}" if doi else ""),
                "doi": doi,
            }
        )
    return [reference for reference in parsed if reference["title"]]


def enrich_with_semantic_recommendations(
    papers: list[dict[str, Any]],
    email: str | None,
    api_key: str | None,
    limit: int,
    per_paper: int,
) -> list[dict[str, Any]]:
    if limit <= 0 or per_paper <= 0:
        return papers

    candidates = [
        paper
        for paper in papers
        if paper.get("semantic_scholar_id") or paper.get("id", "").startswith("S2")
    ][:limit]
    fields = ",".join(["paperId", "title", "year", "venue", "authors", "externalIds", "url", "citationCount"])

    for paper in candidates:
        paper_id = paper.get("semantic_scholar_id") or paper.get("id")
        try:
            result = request_json_post(
                SEMANTIC_SCHOLAR_RECOMMENDATIONS_BASE,
                {"fields": fields, "limit": per_paper},
                {"positivePaperIds": [paper_id]},
                email,
                api_key,
            )
        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            print(f"Semantic Scholar recommendations failed for {paper_id}: {error}")
            continue
        recommended = result.get("recommendedPapers", []) if isinstance(result, dict) else []
        paper["similar_papers"] = parse_semantic_recommended_papers(recommended, paper_id)
        time.sleep(0.35 if api_key else 1.05)

    return papers


def parse_semantic_recommended_papers(items: list[dict[str, Any]], seed_id: str) -> list[dict[str, Any]]:
    similar = []
    for item in items:
        if item.get("paperId") == seed_id:
            continue
        external_ids = item.get("externalIds") or {}
        doi = normalize_doi(external_ids.get("DOI", ""))
        similar.append(
            {
                "id": item.get("paperId", ""),
                "title": item.get("title", ""),
                "year": item.get("year", ""),
                "journal": item.get("venue", ""),
                "authors": [author.get("name", "") for author in item.get("authors", [])[:3] if author.get("name")],
                "doi": doi,
                "url": item.get("url", "") or (f"https://doi.org/{doi}" if doi else ""),
                "citation_count": item.get("citationCount", 0),
            }
        )
    return [paper for paper in similar if paper["title"]]


def parse_openalex_work(item: dict[str, Any]) -> dict[str, Any]:
    title = item.get("title") or item.get("display_name") or ""
    abstract = abstract_from_inverted_index(item.get("abstract_inverted_index"))
    primary_location = item.get("primary_location") or {}
    journal = (primary_location.get("source") or {}).get("display_name", "")
    authors = [
        authorship.get("author", {}).get("display_name", "")
        for authorship in item.get("authorships", [])
        if authorship.get("author", {}).get("display_name")
    ]
    doi = normalize_doi(item.get("doi", ""))
    tags = classify(" ".join([title, abstract, journal]))
    openalex_id = item.get("id", "")
    return {
        "id": openalex_id,
        "source": "OpenAlex",
        "pmid": "",
        "doi": doi,
        "title": title,
        "authors": authors,
        "journal": journal,
        "publication_date": item.get("publication_date") or "",
        "abstract": abstract,
        "url": item.get("landing_page_url") or item.get("doi") or openalex_id,
        "pdf_url": "",
        "citation_count": item.get("cited_by_count", 0),
        "influential_citation_count": 0,
        "reference_count": 0,
        "references": [],
        "metrics_source": "",
        "tags": tags,
    }


def abstract_from_inverted_index(index: dict[str, list[int]] | None) -> str:
    if not index:
        return ""
    words: list[tuple[int, str]] = []
    for word, positions in index.items():
        words.extend((position, word) for position in positions)
    return " ".join(word for _, word in sorted(words))


def fetch_crossref(retmax: int, email: str | None, query_limit: int | None = None) -> list[dict[str, Any]]:
    queries = SEARCH_QUERIES[:query_limit] if query_limit else SEARCH_QUERIES
    per_query = max(5, min(30, retmax // max(1, len(queries)) + 3))
    papers: list[dict[str, Any]] = []
    for query in queries:
        params: dict[str, str | int] = {
            "query.bibliographic": query,
            "rows": per_query,
            "sort": "published",
            "order": "desc",
            "filter": "type:journal-article",
        }
        if email:
            params["mailto"] = email
        try:
            data = request_json(CROSSREF_BASE, params, email)
        except urllib.error.URLError:
            print(f"Crossref request failed for query: {query}")
            continue
        items = data.get("message", {}).get("items", [])
        query_tags = classify(query)
        papers.extend(enrich_query_tags(parse_crossref_work(item), query_tags) for item in items)
        time.sleep(0.12)
    return [paper for paper in papers if paper and is_relevant(paper)]


def parse_crossref_work(item: dict[str, Any]) -> dict[str, Any]:
    title = first(item.get("title")) or ""
    abstract = clean_crossref_abstract(item.get("abstract", ""))
    journal = first(item.get("container-title")) or ""
    authors = [
        " ".join(part for part in [author.get("given", ""), author.get("family", "")] if part).strip()
        for author in item.get("author", [])
    ]
    authors = [author for author in authors if author]
    doi = normalize_doi(item.get("DOI", ""))
    tags = classify(" ".join([title, abstract, journal]))
    return {
        "id": f"https://doi.org/{doi}" if doi else item.get("URL", ""),
        "source": "Crossref",
        "pmid": "",
        "doi": doi,
        "title": title,
        "authors": authors,
        "journal": journal,
        "publication_date": parse_crossref_date(item),
        "abstract": abstract,
        "url": item.get("URL", "") or (f"https://doi.org/{doi}" if doi else ""),
        "pdf_url": "",
        "citation_count": item.get("is-referenced-by-count", 0),
        "influential_citation_count": 0,
        "reference_count": 0,
        "references": [],
        "metrics_source": "",
        "tags": tags,
    }


def fetch_pubmed(retmax: int, email: str | None) -> list[dict[str, Any]]:
    params: dict[str, str | int] = {
        "db": "pubmed",
        "term": PUBMED_QUERY,
        "retmode": "json",
        "sort": "pub date",
        "retmax": retmax,
    }
    if email:
        params["email"] = email
    data = request_json(f"{PUBMED_BASE}/esearch.fcgi", params, email)
    pmids = data.get("esearchresult", {}).get("idlist", [])
    if not pmids:
        return []
    time.sleep(0.34)
    return fetch_pubmed_details(pmids, email)


def fetch_pubmed_details(pmids: list[str], email: str | None) -> list[dict[str, Any]]:
    papers: list[dict[str, Any]] = []
    for chunk in chunks(pmids, 100):
        params: dict[str, str | int] = {
            "db": "pubmed",
            "id": ",".join(chunk),
            "retmode": "xml",
        }
        if email:
            params["email"] = email
        root = request_xml(f"{PUBMED_BASE}/efetch.fcgi", params, email)
        papers.extend(
            paper
            for paper in (parse_pubmed_article(article) for article in root.findall(".//PubmedArticle"))
            if paper and is_relevant(paper)
        )
        time.sleep(0.34)
    return papers


def chunks(values: list[str], size: int) -> list[list[str]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def parse_pubmed_article(article: ET.Element) -> dict[str, Any] | None:
    pmid = text(article.find(".//PMID"))
    citation = article.find(".//MedlineCitation")
    article_node = citation.find("Article") if citation is not None else None
    if article_node is None or not pmid:
        return None

    title = flatten_text(article_node.find("ArticleTitle"))
    journal = text(article_node.find("Journal/Title")) or text(article_node.find("Journal/ISOAbbreviation"))
    abstract = " ".join(
        flatten_text(node) for node in article_node.findall("Abstract/AbstractText") if flatten_text(node)
    )
    doi = find_pubmed_doi(article)
    tags = classify(" ".join([title, abstract, journal or ""]))
    return {
        "id": f"PMID:{pmid}",
        "source": "PubMed",
        "pmid": pmid,
        "doi": doi,
        "title": title,
        "authors": parse_pubmed_authors(article_node),
        "journal": journal,
        "publication_date": parse_pubmed_publication_date(article, article_node),
        "abstract": abstract,
        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        "pdf_url": "",
        "citation_count": 0,
        "influential_citation_count": 0,
        "reference_count": 0,
        "references": [],
        "metrics_source": "",
        "tags": tags,
    }


def deduplicate(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for paper in sorted(papers, key=lambda item: item.get("publication_date", ""), reverse=True):
        key = paper_key(paper)
        if key in seen:
            continue
        seen.add(key)
        unique.append(paper)
    return unique


def enrich_query_tags(paper: dict[str, Any], query_tags: list[str]) -> dict[str, Any]:
    paper["tags"] = sorted(set(paper.get("tags", []) + query_tags))
    return paper


def paper_key(paper: dict[str, Any]) -> str:
    if paper.get("doi"):
        return f"doi:{paper['doi'].lower()}"
    title = " ".join((paper.get("title") or "").lower().split())
    return f"title:{title[:160]}"


def is_relevant(paper: dict[str, Any]) -> bool:
    text_value = " ".join(
        [
            paper.get("title", ""),
            paper.get("abstract", ""),
            paper.get("journal", ""),
        ]
    ).lower()
    if any(term in text_value for term in NOISE_TERMS):
        return False
    text_tags = classify(text_value)
    has_environment = any(term in text_value for term in ENVIRONMENT_KEYWORDS)
    has_virus = any(tag in text_tags for tag in ["virus", "amg"])
    has_cycle = any(tag in text_tags for tag in ["carbon", "nitrogen", "sulfur", "phosphorus", "biogeochemistry"])
    return bool(paper.get("title")) and has_environment and has_virus and has_cycle


def classify(text_value: str) -> list[str]:
    haystack = f" {text_value.lower()} "
    tags = [
        tag
        for tag, needles in TAG_RULES.items()
        if any(needle in haystack for needle in needles)
    ]
    return tags or ["biogeochemistry"]


def parse_crossref_date(item: dict[str, Any]) -> str:
    for key in ["published-print", "published-online", "published", "created"]:
        date_parts = item.get(key, {}).get("date-parts", [])
        if date_parts and date_parts[0]:
            parts = date_parts[0]
            year = str(parts[0])
            month = str(parts[1]).zfill(2) if len(parts) > 1 else "01"
            day = str(parts[2]).zfill(2) if len(parts) > 2 else "01"
            return f"{year}-{month}-{day}"
    return ""


def clean_crossref_abstract(value: str) -> str:
    return (
        value.replace("<jats:p>", "")
        .replace("</jats:p>", " ")
        .replace("<p>", "")
        .replace("</p>", " ")
        .strip()
    )


def first(value: Any) -> str:
    if isinstance(value, list) and value:
        return str(value[0])
    if isinstance(value, str):
        return value
    return ""


def normalize_doi(value: Any) -> str:
    if not value:
        return ""
    return str(value).replace("https://doi.org/", "").replace("http://dx.doi.org/", "").strip()


def parse_pubmed_authors(article_node: ET.Element) -> list[str]:
    authors = []
    for author in article_node.findall("AuthorList/Author"):
        collective = text(author.find("CollectiveName"))
        if collective:
            authors.append(collective)
            continue
        last = text(author.find("LastName"))
        initials = text(author.find("Initials"))
        if last:
            authors.append(f"{last} {initials}".strip())
    return authors


def parse_pubmed_publication_date(article: ET.Element, article_node: ET.Element) -> str:
    article_date = article_node.find("ArticleDate")
    if article_date is not None:
        parsed = parse_date_node(article_date)
        if parsed:
            return parsed

    for history_date in article.findall(".//PubMedPubDate"):
        if history_date.attrib.get("PubStatus") in {"epublish", "pubmed", "entrez"}:
            parsed = parse_date_node(history_date)
            if parsed:
                return parsed

    return parse_date_node(article_node.find("Journal/JournalIssue/PubDate"))


def parse_date_node(node: ET.Element | None) -> str:
    if node is None:
        return ""
    year = text(node.find("Year")) or text(node.find("MedlineDate"))[:4]
    month = normalize_month(text(node.find("Month")))
    day = text(node.find("Day")) or "01"
    if not year:
        return ""
    return f"{year}-{month}-{day.zfill(2)}"


def normalize_month(value: str) -> str:
    months = {
        "jan": "01",
        "feb": "02",
        "mar": "03",
        "apr": "04",
        "may": "05",
        "jun": "06",
        "jul": "07",
        "aug": "08",
        "sep": "09",
        "oct": "10",
        "nov": "11",
        "dec": "12",
    }
    if value.isdigit():
        return value.zfill(2)
    return months.get(value[:3].lower(), "01")


def find_pubmed_doi(article: ET.Element) -> str:
    for node in article.findall(".//ArticleId"):
        if node.attrib.get("IdType") == "doi" and node.text:
            return node.text.strip()
    return ""


def text(node: ET.Element | None) -> str:
    return "".join(node.itertext()).strip() if node is not None else ""


def flatten_text(node: ET.Element | None) -> str:
    if node is None:
        return ""
    return " ".join("".join(node.itertext()).split())


def write_data(
    papers: list[dict[str, Any]],
    output: Path,
    sources: list[str],
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "sources": sources,
        "queries": SEARCH_QUERIES,
        "papers": papers,
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_existing_papers(output: Path) -> list[dict[str, Any]]:
    if not output.exists():
        return []
    data = json.loads(output.read_text(encoding="utf-8"))
    return data.get("papers", [])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--retmax", type=int, default=160)
    parser.add_argument("--email", default=None)
    parser.add_argument("--output", default="data/papers.json")
    parser.add_argument(
        "--sources",
        default="semantic,openalex",
        help="Comma-separated list: semantic,openalex,crossref,pubmed",
    )
    parser.add_argument("--semantic-api-key", default=None)
    parser.add_argument(
        "--semantic-enrich-limit",
        type=int,
        default=800,
        help="Maximum number of DOI/PMID records to enrich with Semantic Scholar metrics.",
    )
    parser.add_argument(
        "--skip-semantic-enrichment",
        action="store_true",
        help="Do not backfill citation/reference metadata through Semantic Scholar.",
    )
    parser.add_argument(
        "--similar-limit",
        type=int,
        default=60,
        help="Number of papers to enrich with Semantic Scholar recommendations.",
    )
    parser.add_argument(
        "--similar-per-paper",
        type=int,
        default=5,
        help="Recommended similar papers to store per paper.",
    )
    parser.add_argument(
        "--merge-existing",
        action="store_true",
        help="Merge fresh results into the existing data file instead of replacing it.",
    )
    parser.add_argument("--query-limit", type=int, default=36)
    args = parser.parse_args()

    output = Path(args.output)
    sources = [source.strip().lower() for source in args.sources.split(",") if source.strip()]
    all_papers: list[dict[str, Any]] = []
    if "semantic" in sources or "semanticscholar" in sources:
        all_papers.extend(fetch_semantic_scholar(args.retmax, args.email, args.semantic_api_key, args.query_limit))
    if "openalex" in sources:
        all_papers.extend(fetch_openalex(args.retmax, args.email, args.query_limit))
    if "crossref" in sources:
        all_papers.extend(fetch_crossref(args.retmax, args.email, args.query_limit))
    if "pubmed" in sources:
        all_papers.extend(fetch_pubmed(max(20, args.retmax // 2), args.email))

    if args.merge_existing:
        all_papers.extend(load_existing_papers(output))

    papers = deduplicate(all_papers)[: args.retmax]
    if not args.skip_semantic_enrichment:
        papers = enrich_with_semantic_metadata(
            papers,
            args.email,
            args.semantic_api_key,
            args.semantic_enrich_limit,
        )
        papers = enrich_with_semantic_recommendations(
            papers,
            args.email,
            args.semantic_api_key,
            args.similar_limit,
            args.similar_per_paper,
        )
    if not papers and output.exists():
        print("No fresh papers were fetched; keeping the existing data file.")
        return
    source_labels = sorted({paper.get("source", "") for paper in papers if paper.get("source")})
    write_data(papers, output, source_labels)
    print(f"Updated {len(papers)} papers from {', '.join(source_labels)} at {output}")


if __name__ == "__main__":
    main()
