"""
Controlled offline fixtures and mock data for API robustness and metadata drift testing.
All fixtures are deterministic, local, and require zero network access.
"""

# Benchmark-formatted citation (canonical labeled format)
GENUINE_BENCHMARK_CITATION = (
    'Title: "Attention is All You Need"\n'
    "Authors: Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser, Illia Polosukhin\n"
    "Year: 2017\n"
    "Venue: Advances in Neural Information Processing Systems\n"
    "DOI: 10.5555/3295222.3295349"
)

# Free-text IEEE formatted citation
GENUINE_IEEE_CITATION = (
    "A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A. N. Gomez, L. Kaiser, and I. Polosukhin, "
    "'Attention is all you need,' in Advances in Neural Information Processing Systems, 2017, pp. 5998-6008. "
    "doi: 10.5555/3295222.3295349"
)

# Canonical parsed representation
GENUINE_PARSED = {
    "title": "Attention is All You Need",
    "authors": [
        "Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit",
        "Llion Jones", "Aidan N. Gomez", "Lukasz Kaiser", "Illia Polosukhin"
    ],
    "year": 2017,
    "venue": "Advances in Neural Information Processing Systems",
    "doi": "10.5555/3295222.3295349",
}

# Crossref Mock Payloads
CROSSREF_SUCCESS_PAYLOAD = {
    "status": "ok",
    "message": {
        "items": [
            {
                "title": ["Attention is All You Need"],
                "author": [
                    {"given": "Ashish", "family": "Vaswani"},
                    {"given": "Noam", "family": "Shazeer"},
                    {"given": "Niki", "family": "Parmar"},
                    {"given": "Jakob", "family": "Uszkoreit"},
                    {"given": "Llion", "family": "Jones"},
                    {"given": "Aidan N.", "family": "Gomez"},
                    {"given": "Lukasz", "family": "Kaiser"},
                    {"given": "Illia", "family": "Polosukhin"},
                ],
                "container-title": ["Advances in Neural Information Processing Systems"],
                "issued": {"date-parts": [[2017, 12, 1]]},
                "DOI": "10.5555/3295222.3295349",
                "publisher": "Curran Associates, Inc.",
            }
        ]
    }
}

CROSSREF_EMPTY_PAYLOAD = {
    "status": "ok",
    "message": {
        "items": []
    }
}

CROSSREF_MISSING_TITLE_PAYLOAD = {
    "status": "ok",
    "message": {
        "items": [
            {
                "title": [],
                "author": [{"given": "Ashish", "family": "Vaswani"}],
                "container-title": ["Advances in Neural Information Processing Systems"],
                "issued": {"date-parts": [[2017, 12, 1]]},
                "DOI": "10.5555/3295222.3295349",
            }
        ]
    }
}

CROSSREF_MISSING_AUTHORS_PAYLOAD = {
    "status": "ok",
    "message": {
        "items": [
            {
                "title": ["Attention is All You Need"],
                "author": [],
                "container-title": ["Advances in Neural Information Processing Systems"],
                "issued": {"date-parts": [[2017, 12, 1]]},
                "DOI": "10.5555/3295222.3295349",
            }
        ]
    }
}

CROSSREF_MISSING_VENUE_PAYLOAD = {
    "status": "ok",
    "message": {
        "items": [
            {
                "title": ["Attention is All You Need"],
                "author": [{"given": "Ashish", "family": "Vaswani"}],
                "container-title": [],
                "issued": {"date-parts": [[2017, 12, 1]]},
                "DOI": "10.5555/3295222.3295349",
            }
        ]
    }
}

CROSSREF_MISSING_YEAR_PAYLOAD = {
    "status": "ok",
    "message": {
        "items": [
            {
                "title": ["Attention is All You Need"],
                "author": [{"given": "Ashish", "family": "Vaswani"}],
                "container-title": ["Advances in Neural Information Processing Systems"],
                "DOI": "10.5555/3295222.3295349",
            }
        ]
    }
}

# Semantic Scholar Mock Payloads
SEMANTIC_SCHOLAR_SUCCESS_PAYLOAD = {
    "total": 1,
    "data": [
        {
            "paperId": "204e3073870fae3d05bcbc2f6a8e263c9b72e776",
            "title": "Attention is All you Need",
            "authors": [
                {"name": "Ashish Vaswani"},
                {"name": "Noam Shazeer"},
                {"name": "Niki Parmar"},
                {"name": "Jakob Uszkoreit"},
            ],
            "year": 2017,
            "venue": "Neural Information Processing Systems",
            "externalIds": {
                "DOI": "10.5555/3295222.3295349",
                "ArXiv": "1706.03762"
            }
        }
    ]
}

SEMANTIC_SCHOLAR_EMPTY_PAYLOAD = {
    "total": 0,
    "data": []
}

# OpenAlex Mock Payloads
OPENALEX_SUCCESS_PAYLOAD = {
    "meta": {"count": 1},
    "results": [
        {
            "id": "https://openalex.org/W2963403868",
            "display_name": "Attention Is All You Need",
            "publication_year": 2017,
            "created_date": "2017-06-12",
            "doi": "https://doi.org/10.5555/3295222.3295349",
            "type": "article",
            "primary_location": {
                "source": {
                    "display_name": "Advances in Neural Information Processing Systems"
                }
            },
            "authorships": [
                {"author": {"display_name": "Ashish Vaswani"}},
                {"author": {"display_name": "Noam Shazeer"}},
                {"author": {"display_name": "Niki Parmar"}},
                {"author": {"display_name": "Jakob Uszkoreit"}},
                {"author": {"display_name": "Llion Jones"}},
                {"author": {"display_name": "Aidan N. Gomez"}},
                {"author": {"display_name": "Lukasz Kaiser"}},
                {"author": {"display_name": "Illia Polosukhin"}},
            ],
            "locations": [
                {
                    "landing_page_url": "https://arxiv.org/abs/1706.03762",
                    "source": {"display_name": "arXiv"}
                }
            ]
        }
    ]
}

OPENALEX_EMPTY_PAYLOAD = {
    "meta": {"count": 0},
    "results": []
}

# Mock HTTP Responses for fault injection
class MockResponse:
    def __init__(self, json_data=None, status_code=200, text="", headers=None):
        self._json_data = json_data
        self.status_code = status_code
        self.text = text or ("" if json_data is None else str(json_data))
        self.headers = headers or {"Content-Type": "application/json"}

    def json(self):
        if self._json_data is None:
            import json
            raise json.JSONDecodeError("Expecting value", self.text, 0)
        return self._json_data
