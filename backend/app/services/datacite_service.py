import re
from app.services.cache_service import session

BASE_URL = "https://api.datacite.org/dois"

last_status = {
    "attempted": False,
    "success": True,
    "error": None,
    "status_code": 200,
}


def parse_datacite_author(creator):
    """
    Format DataCite creator object into 'Given Family' or 'Family, Given'.
    """
    if not creator or not isinstance(creator, dict):
        return ""
    given = creator.get("givenName")
    family = creator.get("familyName")
    if given and family:
        return f"{given} {family}".strip()
    name = creator.get("name") or ""
    if "," in name:
        parts = [p.strip() for p in name.split(",", 1)]
        if len(parts) == 2 and parts[1]:
            return f"{parts[1]} {parts[0]}".strip()
    return name.strip()


def search_datacite(title, author=None, limit=10):
    """
    Search DataCite API for works by title and optional author.
    Returns normalized papers with canonical DOI (e.g. 10.48550/arXiv...), authors, year, and venue.
    """
    if not title:
        return []

    last_status["attempted"] = True

    try:
        clean_title = re.sub(r'["\\]', '', str(title)).strip()
        if not clean_title:
            return []

        # Primary query: Exact title in quotes with optional author family name
        if author:
            clean_author = re.sub(r'["\\]', '', str(author)).strip()
            query = f'titles.title:"{clean_title}" AND creators.familyName:{clean_author}'
        else:
            query = f'titles.title:"{clean_title}"'

        headers = {"User-Agent": "CitationGuard/1.0 (Academic Citation Verification)"}
        response = session.get(
            BASE_URL,
            params={"query": query, "rows": limit},
            headers=headers,
            timeout=15,
        )

        last_status["status_code"] = response.status_code
        data = response.json() if response.status_code == 200 else {}
        results = data.get("data", [])

        # Fallback query if exact title yielded no hits
        if not results:
            variant_title = None
            if re.search(r'\bnets\b', clean_title, re.IGNORECASE):
                variant_title = re.sub(r'\bnets\b', 'Networks', clean_title, flags=re.IGNORECASE)
            elif re.search(r'\bnetworks\b', clean_title, re.IGNORECASE):
                variant_title = re.sub(r'\bnetworks\b', 'Nets', clean_title, flags=re.IGNORECASE)

            if variant_title:
                v_query = f'titles.title:"{variant_title}"'
                if author:
                    v_query = f'titles.title:"{variant_title}" AND creators.familyName:{clean_author}'
                response = session.get(
                    BASE_URL,
                    params={"query": v_query, "rows": limit},
                    headers=headers,
                    timeout=15,
                )
                last_status["status_code"] = response.status_code
                if response.status_code == 200:
                    results = response.json().get("data", [])

        if not results:
            if author:
                fallback_query = f'{clean_title} {clean_author}'
            else:
                fallback_query = f'{clean_title}'
            response = session.get(
                BASE_URL,
                params={"query": fallback_query, "rows": limit},
                headers=headers,
                timeout=15,
            )
            last_status["status_code"] = response.status_code
            if response.status_code == 200:
                results = response.json().get("data", [])

        if response.status_code != 200:
            last_status["success"] = (response.status_code == 404)
            last_status["error"] = f"HTTP {response.status_code}"
            return []

        last_status["success"] = True
        last_status["error"] = None

        papers = []
        for item in results:
            attr = item.get("attributes", {})
            titles = attr.get("titles", [])
            item_title = titles[0].get("title") if titles else None
            if not item_title:
                continue

            authors = []
            for creator in attr.get("creators", []):
                name = parse_datacite_author(creator)
                if name:
                    authors.append(name)

            pub_year = attr.get("publicationYear")
            try:
                pub_year = int(pub_year) if pub_year else None
            except (ValueError, TypeError):
                pub_year = None

            alternate_years = [pub_year] if pub_year else []
            for d in attr.get("dates", []):
                d_str = str(d.get("date", ""))
                m = re.search(r"\b(19\d{2}|20\d{2})\b", d_str)
                if m:
                    dy = int(m.group(1))
                    if dy not in alternate_years:
                        alternate_years.append(dy)

            doi = item.get("id", "").strip().lower()

            venue = attr.get("publisher") or ""
            if doi.startswith("10.48550"):
                venue = "arXiv"

            abstract = ""
            for desc in attr.get("descriptions", []):
                if desc.get("description"):
                    abstract = desc["description"]
                    break

            papers.append({
                "title": item_title,
                "authors": authors,
                "year": min(alternate_years) if alternate_years else pub_year,
                "alternate_years": alternate_years,
                "venue": venue,
                "doi": doi,
                "abstract": abstract,
                "publisher": attr.get("publisher", "DataCite"),
                "source": "DataCite",
            })

        return papers

    except Exception as e:
        last_status["success"] = False
        last_status["error"] = str(e)
        last_status["status_code"] = None
        return []


def verify_datacite_doi(doi):
    """
    Direct lookup of a DOI registered in DataCite (e.g. arXiv 10.48550/...).
    """
    if not doi:
        return None

    clean_doi = str(doi).strip().lower()
    clean_doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", clean_doi)
    clean_doi = re.sub(r"^doi:\s*", "", clean_doi).rstrip(".,;/")

    try:
        headers = {"User-Agent": "CitationGuard/1.0 (Academic Citation Verification)"}
        response = session.get(f"{BASE_URL}/{clean_doi}", headers=headers, timeout=15)
        if response.status_code != 200:
            return None

        item = response.json().get("data", {})
        attr = item.get("attributes", {})
        titles = attr.get("titles", [])
        title = titles[0].get("title") if titles else None
        if not title:
            return None

        authors = [parse_datacite_author(c) for c in attr.get("creators", []) if parse_datacite_author(c)]
        pub_year = attr.get("publicationYear")
        try:
            pub_year = int(pub_year) if pub_year else None
        except (ValueError, TypeError):
            pub_year = None

        doi_id = item.get("id", "").strip().lower()
        venue = attr.get("publisher") or ""
        if doi_id.startswith("10.48550"):
            venue = "arXiv"

        abstract = ""
        for desc in attr.get("descriptions", []):
            if desc.get("description"):
                abstract = desc["description"]
                break

        return {
            "title": title,
            "authors": authors,
            "venue": venue,
            "year": pub_year,
            "doi": doi_id,
            "abstract": abstract,
            "publisher": attr.get("publisher", "DataCite"),
            "source": "DataCite",
        }
    except Exception:
        return None
