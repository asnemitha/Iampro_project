from app.services.cache_service import session

BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

FIELDS = (
    "title,"
    "authors,"
    "year,"
    "venue,"
    "externalIds"
)


def search_semantic_scholar(title, limit=10):
    """
    Search Semantic Scholar by paper title.

    Returns a list of normalized papers.
    """

    if not title:
        return []

    try:

        response = session.get(

            BASE_URL,

            params={

                "query": title,

                "limit": limit,

                "fields": FIELDS,

            },

            timeout=15,

        )

        if response.status_code != 200:

            return []

        data = response.json()

        papers = []

        for paper in data.get("data", []):

            doi = None

            if paper.get("externalIds"):

                doi = paper["externalIds"].get("DOI")

            authors = []

            for author in paper.get("authors", []):

                if author.get("name"):

                    authors.append(author["name"])

            papers.append({

                "title": paper.get("title"),

                "authors": authors,

                "year": paper.get("year"),

                "venue": paper.get("venue"),

                "doi": doi,

                "publisher": "Semantic Scholar",

                "source": "Semantic Scholar",

            })

        return papers

    except Exception:

        return []