import re
from app.services.cache_service import session

BASE_URL = "https://api.crossref.org/works"

HEADERS = {
    "User-Agent": "CiteGuard/1.0 (Citation Verification Research Project)"
}

TIMEOUT = 15


# ==========================================================
# Internal Request & Provider Telemetry
# ==========================================================

last_status = {
    "attempted": False,
    "success": True,
    "error": None,
    "status_code": 200,
}


def _request(url, params=None):
    last_status["attempted"] = True
    try:

        response = session.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=TIMEOUT,
        )

        last_status["status_code"] = response.status_code

        if response.status_code != 200:
            last_status["success"] = (response.status_code == 404)
            last_status["error"] = f"HTTP {response.status_code}"
            return None

        last_status["success"] = True
        last_status["error"] = None
        return response.json()

    except Exception as e:
        last_status["success"] = False
        last_status["error"] = str(e)
        last_status["status_code"] = None
        return None


# ==========================================================
# Metadata Extraction
# ==========================================================

def extract_crossref_metadata(item):

    if not item:
        return None

    title = ""
    if item.get("title"):
        if isinstance(item["title"], list):
            title = item["title"][0] if len(item["title"]) > 0 else ""
        else:
            title = str(item["title"]).strip()

    authors = []

    for author in item.get("author", []):
        given = author.get("given", "").strip()
        family = author.get("family", "").strip()
        full = f"{given} {family}".strip()
        if full:
            authors.append(full)

    venue = ""
    if item.get("container-title"):
        if isinstance(item["container-title"], list):
            venue = item["container-title"][0] if len(item["container-title"]) > 0 else ""
        else:
            venue = str(item["container-title"]).strip()

    year = None

    for key in [
        "published-print",
        "published-online",
        "issued",
        "created",
    ]:
        try:
            year = item[key]["date-parts"][0][0]
            break
        except Exception:
            pass

    doi = item.get("DOI")

    if doi:
        doi = doi.lower().strip()

    publisher = item.get("publisher", "")

    abstract = None
    if item.get("abstract"):
        try:
            abstract = re.sub(r"<[^>]+>", " ", str(item["abstract"])).strip()
            abstract = re.sub(r"\s+", " ", abstract)
        except Exception:
            abstract = None

    return {
        "title": title,
        "authors": authors,
        "venue": venue,
        "year": year,
        "doi": doi,
        "abstract": abstract,
        "publisher": publisher,
        "source": "Crossref",
    }


# ==========================================================
# DOI Search
# ==========================================================

def verify_doi(doi):

    if not doi:
        return None

    from app.services.metadata_normalizer import normalize_doi
    doi = normalize_doi(doi)
    if not doi:
        return None

    # Step 1: Direct Crossref works lookup
    url = f"{BASE_URL}/{doi}"
    data = _request(url)

    if data is not None and data.get("message"):
        meta = extract_crossref_metadata(data.get("message"))
        if meta and meta.get("title") and len(meta["title"].strip()) > 3:
            meta["source"] = "Crossref"
            return meta

    # Step 2: Fallback to doi.org content negotiation (resolves DataCite, arXiv, mEDRA, etc.)
    try:
        csl_headers = {
            "Accept": "application/vnd.citationstyles.csl+json, application/json",
            "User-Agent": HEADERS["User-Agent"]
        }
        res = session.get(f"https://doi.org/{doi}", headers=csl_headers, timeout=TIMEOUT)
        if res.status_code == 200:
            csl_data = res.json()
            meta = extract_crossref_metadata(csl_data)
            if meta and meta.get("title"):
                meta["source"] = "Crossref"
                return meta
    except Exception:
        pass

    return None


# ==========================================================
# Title Search
# ==========================================================

def verify_title(title, author=None, rows=10):

    if not title:
        return []

    params = {
        "query.title": title,
        "rows": rows,
    }

    if author:
        params["query.author"] = author

    data = _request(
        BASE_URL,
        params=params,
    )

    if data is None:
        return []

    items = data.get(
        "message",
        {},
    ).get(
        "items",
        [],
    )

    papers = []

    for item in items:

        paper = extract_crossref_metadata(item)

        if paper and paper.get("title"):
            paper["source"] = "Crossref"
            papers.append(paper)

    return papers
