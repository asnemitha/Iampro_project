import re
from app.services.cache_service import session

BASE_URL = "https://api.openalex.org/works"


last_status = {
    "attempted": False,
    "success": True,
    "error": None,
    "status_code": 200,
}


def search_openalex(title, author=None, limit=10):
    """
    Search OpenAlex using paper title and optional author.

    Returns normalized paper metadata.
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

            papers.append({
                "title": work.get("display_name"),
                "authors": authors,
                "year": year,
                "alternate_years": alternate_years,
                "venue": venue,
                "doi": doi,
                "publisher": "OpenAlex",
                "source": "OpenAlex",
            })

        return papers

    except Exception as e:
        last_status["success"] = False
        last_status["error"] = str(e)
        last_status["status_code"] = None
        return []