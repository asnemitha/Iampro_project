from app.services.cache_service import session

BASE_URL = "https://api.crossref.org/works"

HEADERS = {
    "User-Agent": "CiteGuard/1.0 (Citation Verification Research Project)"
}

TIMEOUT = 15


# ==========================================================
# Internal Request
# ==========================================================

def _request(url, params=None):
    try:

        response = session.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=TIMEOUT,
        )

        if response.status_code != 200:
            return None

        return response.json()

    except Exception:
        return None


# ==========================================================
# Metadata Extraction
# ==========================================================

def extract_crossref_metadata(item):

    if not item:
        return None

    title = ""

    if item.get("title"):

        if len(item["title"]) > 0:
            title = item["title"][0]

    authors = []

    for author in item.get("author", []):

        given = author.get("given", "").strip()

        family = author.get("family", "").strip()

        full = f"{given} {family}".strip()

        if full:
            authors.append(full)

    venue = ""

    if item.get("container-title"):

        if len(item["container-title"]) > 0:
            venue = item["container-title"][0]

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

    return {

        "title": title,

        "authors": authors,

        "venue": venue,

        "year": year,

        "doi": doi,

        "publisher": publisher,

    }


# ==========================================================
# DOI Search
# ==========================================================

def verify_doi(doi):

    if not doi:
        return None

    doi = doi.strip().lower()

    url = f"{BASE_URL}/{doi}"

    data = _request(url)

    if data is None:
        return None

    return extract_crossref_metadata(
        data.get("message")
    )


# ==========================================================
# Title Search
# ==========================================================

def verify_title(title, rows=10):

    if not title:
        return []

    params = {

        "query.title": title,

        "rows": rows,

    }

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

        if paper:

            papers.append(paper)

    return papers