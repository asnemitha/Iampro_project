from app.services.cache_service import session

BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

FIELDS = (
    "title,"
    "authors,"
    "year,"
    "venue,"
    "externalIds"
)


# Provider telemetry status
last_status = {
    "attempted": False,
    "success": True,
    "error": None,
    "status_code": 200,
}


def search_semantic_scholar(title, limit=10):
    """
    Search Semantic Scholar by paper title.

    Returns a list of normalized papers.
    """

    if not title:
        return []

    last_status["attempted"] = True

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

        last_status["status_code"] = response.status_code

        if response.status_code != 200:
            last_status["success"] = (response.status_code == 404)
            last_status["error"] = f"HTTP {response.status_code}"
            return []

        last_status["success"] = True
        last_status["error"] = None
        data = response.json()

        papers = []

        for paper in data.get("data", []):

            doi = None

            if paper.get("externalIds"):

                doi = paper["externalIds"].get("DOI")
                if not doi and paper["externalIds"].get("ArXiv"):
                    doi = f"10.48550/arXiv.{paper['externalIds']['ArXiv']}"

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

    except Exception as e:
        last_status["success"] = False
        last_status["error"] = str(e)
        last_status["status_code"] = None
        return []