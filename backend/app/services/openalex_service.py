from app.services.cache_service import session

BASE_URL = "https://api.openalex.org/works"


def search_openalex(title, limit=10):
    """
    Search OpenAlex using paper title.

    Returns normalized paper metadata.
    """

    if not title:
        return []

    try:

        response = session.get(

            BASE_URL,

            params={

                "search": title,

                "per-page": limit,

            },

            timeout=15,

        )

        if response.status_code != 200:

            return []

        data = response.json()

        papers = []

        for work in data.get("results", []):

            authors = []

            for author in work.get("authorships", []):

                if author.get("author"):

                    name = author["author"].get("display_name")

                    if name:
                        authors.append(name)

            venue = ""

            if work.get("primary_location"):

                source = work["primary_location"].get("source")

                if source:

                    venue = source.get("display_name", "")

            doi = None

            if work.get("doi"):

                doi = work["doi"].replace(
                    "https://doi.org/",
                    ""
                )

            papers.append({

                "title": work.get("display_name"),

                "authors": authors,

                "year": work.get("publication_year"),

                "venue": venue,

                "doi": doi,

                "publisher": "OpenAlex",

                "source": "OpenAlex",

            })

        return papers

    except Exception:

        return []