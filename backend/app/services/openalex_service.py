import re
from app.services.cache_service import session

BASE_URL = "https://api.openalex.org/works"


last_status = {
    "attempted": False,
    "success": True,
    "error": None,
    "status_code": 200,
}


def reconstruct_openalex_abstract(inverted_index):
    """
    Reconstruct full text abstract from OpenAlex abstract_inverted_index.
    """
    if not inverted_index or not isinstance(inverted_index, dict):
        return None
    try:
        positions = {}
        for word, idx_list in inverted_index.items():
            for idx in idx_list:
                positions[idx] = word
        return " ".join(positions[i] for i in sorted(positions.keys()))
    except Exception:
        return None


def search_openalex(title, author=None, limit=10):
    """
    Search OpenAlex using paper title and optional author.

    Returns normalized paper metadata including abstract where indexed.
    """

    if not title:
        return []

    search_query = f"{title} {author}".strip() if author else title
    last_status["attempted"] = True

    try:

        response = session.get(
            BASE_URL,
            params={
                "search": search_query,
                "per-page": limit,
            },
            timeout=15,
        )

        last_status["status_code"] = response.status_code

        if response.status_code != 200:
            last_status["success"] = (response.status_code == 404)
            last_status["error"] = f"HTTP {response.status_code}"
            return []

        last_status["success"] = True
        last_status["error"] = None
        data = response.json()

        papers = []

        for work in data.get("results", []):

            authors = []

            for author_item in work.get("authorships", []):
                if author_item.get("author"):
                    name = author_item["author"].get("display_name")
                    if name:
                        authors.append(name)

            venue = ""
            if work.get("primary_location") and work["primary_location"].get("source"):
                venue = work["primary_location"]["source"].get("display_name", "")

            if not venue:
                for loc in work.get("locations", []):
                    src = loc.get("source")
                    if src and src.get("display_name"):
                        venue = src["display_name"]
                        break

            doi = None
            if work.get("doi"):
                doi = work["doi"].replace("https://doi.org/", "").strip().lower()

            # Inspect locations for canonical publisher or arXiv DOIs, bypassing dead predatory mirrors (e.g. 10.65215)
            loc_dois = []
            for loc in work.get("locations", []):
                for u in [loc.get("landing_page_url"), loc.get("pdf_url")]:
                    if u and "doi.org/10." in str(u).lower():
                        m_doi = re.search(r"doi\.org/(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)", str(u), re.IGNORECASE)
                        if m_doi:
                            clean_d = m_doi.group(1).lower().rstrip(".,")
                            if clean_d not in loc_dois:
                                loc_dois.append(clean_d)

            # If work.get("doi") is missing or is a known dead mirror (e.g. 10.65215), prefer canonical DOI
            if not doi or "10.65215" in doi:
                better_dois = [d for d in loc_dois if not d.startswith("10.65215")]
                if better_dois:
                    # Prefer arXiv DOI (10.48550) or recognized publisher DOIs
                    arxiv_dois = [d for d in better_dois if d.startswith("10.48550/arxiv")]
                    doi = arxiv_dois[0] if arxiv_dois else better_dois[0]
            elif loc_dois:
                # If current DOI is not arXiv but an official 10.48550 arXiv DOI is registered in locations
                arxiv_dois = [d for d in loc_dois if d.startswith("10.48550/arxiv")]
                if arxiv_dois and (doi.startswith("10.65215") or not doi.startswith("10.")):
                    doi = arxiv_dois[0]

            pub_year = work.get("publication_year")
            alternate_years = [pub_year] if pub_year else []

            if work.get("created_date"):
                try:
                    c_year = int(str(work["created_date"])[:4])
                    if c_year and c_year not in alternate_years:
                        alternate_years.append(c_year)
                except Exception:
                    pass

            for loc in work.get("locations", []):
                for u in [loc.get("landing_page_url"), loc.get("pdf_url")]:
                    if u:
                        m = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{2})\d{2}\.", str(u), re.IGNORECASE)
                        if m:
                            ar_year = 2000 + int(m.group(1))
                            if ar_year not in alternate_years:
                                alternate_years.append(ar_year)

            year = min(alternate_years) if (work.get("type") == "preprint" and alternate_years) else pub_year
            # If pub_year is an obvious later reprint / re-registration year compared to earliest alternate year
            if alternate_years and min(alternate_years) < (pub_year or 9999):
                year = min(alternate_years)

            if not venue and doi and doi.startswith("10.48550"):
                venue = "arXiv"

            abstract = reconstruct_openalex_abstract(work.get("abstract_inverted_index"))

            papers.append({
                "title": work.get("display_name"),
                "authors": authors,
                "year": year,
                "alternate_years": alternate_years,
                "venue": venue,
                "doi": doi,
                "abstract": abstract,
                "publisher": "OpenAlex",
                "source": "OpenAlex",
            })

        return papers

    except Exception as e:
        last_status["success"] = False
        last_status["error"] = str(e)
        last_status["status_code"] = None
        return []
