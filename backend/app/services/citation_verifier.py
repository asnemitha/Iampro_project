import requests
import re


def verify_doi(doi: str):
    """
    Verify DOI using Crossref.
    """

    url = f"https://api.crossref.org/works/{doi}"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()["message"]

            return {
                "exists": True,
                "title": data.get("title", [""])[0],
                "publisher": data.get("publisher", ""),
                "year": data.get("published", {})
                            .get("date-parts", [[None]])[0][0],
                "doi": doi,
            }

        return {
            "exists": False,
            "doi": doi,
        }

    except Exception as e:
        return {
            "exists": False,
            "doi": doi,
            "error": str(e),
        }


def verify_text(text: str):
    """
    Extract DOI from text and verify it.
    """

    doi_pattern = r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+"

    match = re.search(doi_pattern, text)

    if not match:
        return {
            "exists": False,
            "reason": "No DOI Found"
        }

    doi = match.group()

    return verify_doi(doi)