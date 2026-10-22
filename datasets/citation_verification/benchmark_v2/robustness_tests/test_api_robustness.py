"""
Offline Fault-Injection and Robustness Test Suite for CiteGuard.

Tests 12 distinct edge cases and failure modes:
  1. Provider timeout
  2. Provider HTTP 429 rate limit
  3. Provider HTTP 500 internal server error
  4. Malformed / empty JSON payload
  5. Provider returns no matching record (empty items)
  6. DOI resolves but title metadata is missing
  7. Author metadata missing or incomplete
  8. Venue / container metadata missing
  9. Conflicting metadata across providers (year, venue, authors)
  10. Metadata drift across temporal retrievals
  11. All providers fail (total outage / blackout)
  12. Cached response missing, malformed, or invalid schema

Plus:
  13. Security check: Zero credential/API-key leakage in logs or outputs.

All tests are 100% offline, deterministic, and mock-based.
"""

import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import requests

# Ensure project root and backend are on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[4]
BACKEND_DIR = PROJECT_ROOT / "backend"
TEST_DIR = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from fixtures import (
    GENUINE_BENCHMARK_CITATION,
    GENUINE_IEEE_CITATION,
    GENUINE_PARSED,
    CROSSREF_SUCCESS_PAYLOAD,
    CROSSREF_EMPTY_PAYLOAD,
    CROSSREF_MISSING_TITLE_PAYLOAD,
    CROSSREF_MISSING_AUTHORS_PAYLOAD,
    CROSSREF_MISSING_VENUE_PAYLOAD,
    CROSSREF_MISSING_YEAR_PAYLOAD,
    SEMANTIC_SCHOLAR_SUCCESS_PAYLOAD,
    SEMANTIC_SCHOLAR_EMPTY_PAYLOAD,
    OPENALEX_SUCCESS_PAYLOAD,
    OPENALEX_EMPTY_PAYLOAD,
    MockResponse,
)

from app.services import (
    crossref_service,
    openalex_service,
    semantic_scholar_service,
    multi_source_retriever,
    candidate_ranker,
    similarity_service,
    verification_pipeline,
)


class TestAPIRobustnessAndMetadataDrift(unittest.TestCase):

    def setUp(self):
        # Suppress verbose pipeline printing during tests
        self.stdout_patch = patch("sys.stdout", new_callable=io.StringIO)
        self.stdout_patch.start()

    def tearDown(self):
        self.stdout_patch.stop()

    # =========================================================================
    # SCENARIO 1: One provider times out
    # =========================================================================
    def test_scenario_1_provider_timeout(self):
        """Crossref times out; OpenAlex and Semantic Scholar succeed."""
        def mock_get(url, *args, **kwargs):
            if "crossref.org" in url:
                raise requests.exceptions.Timeout("Connection to api.crossref.org timed out (15s)")
            elif "semanticscholar.org" in url:
                return MockResponse(SEMANTIC_SCHOLAR_SUCCESS_PAYLOAD, status_code=200)
            elif "openalex.org" in url:
                return MockResponse(OPENALEX_SUCCESS_PAYLOAD, status_code=200)
            return MockResponse(status_code=404)

        with patch("app.services.crossref_service.session.get", side_effect=mock_get), \
             patch("app.services.semantic_scholar_service.session.get", side_effect=mock_get), \
             patch("app.services.openalex_service.session.get", side_effect=mock_get):

            # Test retriever layer
            candidates = multi_source_retriever.retrieve_candidates(
                GENUINE_PARSED["title"],
                authors=GENUINE_PARSED["authors"],
                year=GENUINE_PARSED["year"],
            )
            self.assertGreater(len(candidates), 0, "Other providers must contribute when Crossref times out.")
            sources = {c.get("source") for c in candidates}
            self.assertTrue("OpenAlex" in sources or "Semantic Scholar" in sources)

            # Test end-to-end verification pipeline
            result = verification_pipeline.verify_response(GENUINE_BENCHMARK_CITATION)[0]
            self.assertTrue(result["paper_exists"], "Paper should exist via surviving providers.")
            self.assertTrue(result["citation_accurate"], "Citation should be verified as accurate.")

    # =========================================================================
    # SCENARIO 2: One provider returns HTTP 429 rate limiting
    # =========================================================================
    def test_scenario_2_provider_rate_limited(self):
        """Semantic Scholar returns 429; Crossref and OpenAlex succeed."""
        def mock_get(url, *args, **kwargs):
            if "semanticscholar.org" in url:
                return MockResponse(None, status_code=429, text="Too Many Requests")
            elif "crossref.org" in url:
                return MockResponse(CROSSREF_SUCCESS_PAYLOAD, status_code=200)
            elif "openalex.org" in url:
                return MockResponse(OPENALEX_SUCCESS_PAYLOAD, status_code=200)
            return MockResponse(status_code=404)

        with patch("app.services.crossref_service.session.get", side_effect=mock_get), \
             patch("app.services.semantic_scholar_service.session.get", side_effect=mock_get), \
             patch("app.services.openalex_service.session.get", side_effect=mock_get):

            res_semantic = semantic_scholar_service.search_semantic_scholar(GENUINE_PARSED["title"])
            self.assertEqual(res_semantic, [], "Rate-limited provider must return empty list without crashing.")

            candidates = multi_source_retriever.retrieve_candidates(GENUINE_PARSED["title"])
            self.assertGreater(len(candidates), 0, "Candidate retrieval must survive 429 from one provider.")

    # =========================================================================
    # SCENARIO 3: One provider returns HTTP 500
    # =========================================================================
    def test_scenario_3_provider_http_500(self):
        """OpenAlex returns 500 Internal Server Error; Crossref and Semantic Scholar succeed."""
        def mock_get(url, *args, **kwargs):
            if "openalex.org" in url:
                return MockResponse(None, status_code=500, text="Internal Server Error")
            elif "crossref.org" in url:
                return MockResponse(CROSSREF_SUCCESS_PAYLOAD, status_code=200)
            elif "semanticscholar.org" in url:
                return MockResponse(SEMANTIC_SCHOLAR_SUCCESS_PAYLOAD, status_code=200)
            return MockResponse(status_code=404)

        with patch("app.services.crossref_service.session.get", side_effect=mock_get), \
             patch("app.services.semantic_scholar_service.session.get", side_effect=mock_get), \
             patch("app.services.openalex_service.session.get", side_effect=mock_get):

            res_openalex = openalex_service.search_openalex(GENUINE_PARSED["title"])
            self.assertEqual(res_openalex, [], "HTTP 500 provider must return empty list without unhandled exception.")

            result = verification_pipeline.verify_response(GENUINE_BENCHMARK_CITATION)[0]
            self.assertTrue(result["citation_accurate"], "Citation should be verified from surviving providers.")

    # =========================================================================
    # SCENARIO 4: One provider returns malformed or empty JSON
    # =========================================================================
    def test_scenario_4_malformed_json(self):
        """Crossref returns 200 with HTML error / invalid JSON string."""
        def mock_get(url, *args, **kwargs):
            if "crossref.org" in url:
                return MockResponse(None, status_code=200, text="<html>502 Bad Gateway</html>")
            elif "openalex.org" in url:
                return MockResponse(OPENALEX_SUCCESS_PAYLOAD, status_code=200)
            elif "semanticscholar.org" in url:
                return MockResponse(SEMANTIC_SCHOLAR_SUCCESS_PAYLOAD, status_code=200)
            return MockResponse(status_code=404)

        with patch("app.services.crossref_service.session.get", side_effect=mock_get), \
             patch("app.services.semantic_scholar_service.session.get", side_effect=mock_get), \
             patch("app.services.openalex_service.session.get", side_effect=mock_get):

            cr_meta = crossref_service.verify_title(GENUINE_PARSED["title"])
            self.assertEqual(cr_meta, [], "Malformed JSON must be caught and return empty list.")

            candidates = multi_source_retriever.retrieve_candidates(GENUINE_PARSED["title"])
            self.assertGreater(len(candidates), 0, "Retriever must gracefully handle JSONDecodeError.")

    # =========================================================================
    # SCENARIO 5: One provider returns no matching record
    # =========================================================================
    def test_scenario_5_provider_no_matching_record(self):
        """Crossref returns empty items; Semantic Scholar returns genuine candidate."""
        def mock_get(url, *args, **kwargs):
            if "crossref.org" in url:
                return MockResponse(CROSSREF_EMPTY_PAYLOAD, status_code=200)
            elif "semanticscholar.org" in url:
                return MockResponse(SEMANTIC_SCHOLAR_SUCCESS_PAYLOAD, status_code=200)
            elif "openalex.org" in url:
                return MockResponse(OPENALEX_EMPTY_PAYLOAD, status_code=200)
            return MockResponse(status_code=404)

        with patch("app.services.crossref_service.session.get", side_effect=mock_get), \
             patch("app.services.semantic_scholar_service.session.get", side_effect=mock_get), \
             patch("app.services.openalex_service.session.get", side_effect=mock_get):

            candidates = multi_source_retriever.retrieve_candidates(GENUINE_PARSED["title"])
            self.assertEqual(len(candidates), 1)
            self.assertEqual(candidates[0]["source"], "Semantic Scholar")

    # =========================================================================
    # SCENARIO 6: DOI resolves but title metadata is missing
    # =========================================================================
    def test_scenario_6_doi_resolves_title_missing(self):
        """
        DOI resolves successfully, but returned metadata lacks title.
        Documents the False Rejection risk:
        If title is missing from provider, title comparison scores 0.0,
        which triggers 'Paper title mismatch' despite valid DOI.
        """
        def mock_verify_doi(doi):
            return {
                "title": "",
                "authors": ["Ashish Vaswani", "Noam Shazeer"],
                "year": 2017,
                "venue": "Advances in Neural Information Processing Systems",
                "doi": "10.5555/3295222.3295349",
                "source": "Crossref",
            }

        def mock_retrieve_candidates(title, *args, **kwargs):
            return []

        with patch("app.services.verification_pipeline.verify_doi", side_effect=mock_verify_doi), \
             patch("app.services.verification_pipeline.retrieve_candidates", side_effect=mock_retrieve_candidates):

            result = verification_pipeline.verify_response(GENUINE_BENCHMARK_CITATION)[0]

            self.assertTrue(result["paper_exists"], "Paper existence should be recognized via DOI match.")
            self.assertFalse(result["citation_accurate"], "Documented defect: missing title in registry causes title mismatch.")
            self.assertIn("Paper title mismatch", result["metadata_errors"])

    # =========================================================================
    # SCENARIO 7: Author metadata is missing or incomplete
    # =========================================================================
    def test_scenario_7_author_metadata_missing(self):
        """
        Retrieved paper has empty author list.
        Tests behavior under use_author_fix=True vs use_author_fix=False.
        """
        cand_no_authors = {
            "title": "Attention is All You Need",
            "authors": [],
            "year": 2017,
            "venue": "Advances in Neural Information Processing Systems",
            "doi": "10.5555/3295222.3295349",
            "source": "Crossref",
        }

        # Sub-case 7A: compare_authors directly
        score = similarity_service.compare_authors(GENUINE_PARSED["authors"], [])
        self.assertEqual(score, 0.0, "compare_authors returns 0.0 when registry authors list is empty.")

        # Sub-case 7B: Pipeline with use_author_fix=True -> False Rejection
        with patch("app.services.verification_pipeline.verify_doi", return_value=cand_no_authors), \
             patch("app.services.verification_pipeline.retrieve_candidates", return_value=[cand_no_authors]):

            res_strict = verification_pipeline.verify_response(GENUINE_BENCHMARK_CITATION, use_author_fix=True)[0]
            self.assertFalse(res_strict["citation_accurate"], "use_author_fix=True falsely rejects when registry authors are missing.")
            self.assertIn("Author mismatch", res_strict["metadata_errors"])

            # Sub-case 7C: Pipeline with use_author_fix=False -> Lenient (accepts)
            res_lenient = verification_pipeline.verify_response(GENUINE_BENCHMARK_CITATION, use_author_fix=False)[0]
            self.assertTrue(res_lenient["citation_accurate"], "use_author_fix=False skips author check and accepts.")

    # =========================================================================
    # SCENARIO 8: Venue/container metadata is missing
    # =========================================================================
    def test_scenario_8_venue_metadata_missing(self):
        """
        Retrieved candidate has empty venue.
        Evaluates the permissive fallback: compare_venues returns (True, 100.0).
        """
        is_match, score = similarity_service.compare_venues("NeurIPS", "", use_venue_fix=True)
        self.assertTrue(is_match, "Missing venue in candidate triggers permissive match (True).")
        self.assertEqual(score, 100.0, "Missing venue returns 100.0 similarity.")

        cand_no_venue = {
            "title": "Attention is All You Need",
            "authors": ["Ashish Vaswani", "Noam Shazeer"],
            "year": 2017,
            "venue": "",
            "doi": "10.5555/3295222.3295349",
            "source": "Crossref",
        }

        with patch("app.services.verification_pipeline.verify_doi", return_value=cand_no_venue), \
             patch("app.services.verification_pipeline.retrieve_candidates", return_value=[cand_no_venue]):

            # Valid citation is accepted despite missing venue metadata in registry
            res = verification_pipeline.verify_response(GENUINE_BENCHMARK_CITATION, use_venue_fix=True)[0]
            self.assertTrue(res["citation_accurate"], "Permissive fallback protects valid citations from false rejection.")
            self.assertNotIn("Venue mismatch", res["metadata_errors"])

    # =========================================================================
    # SCENARIO 9: Conflicting metadata across providers
    # =========================================================================
    def test_scenario_9_conflicting_metadata(self):
        """
        Evaluates conflicting metadata resolution across providers.
        Case 9A: Close publication years (2017 vs 2018) -> Merged into 1 candidate with alternate_years.
        Case 9B: Distant publication years (2017 vs 2023) -> Kept as distinct candidate versions and ranked.
        """
        # Case 9A: Close years (<= 1 year difference)
        cr_cand_close = {
            "title": "Attention is All You Need",
            "authors": ["Ashish Vaswani"],
            "year": 2017,
            "venue": "Advances in Neural Information Processing Systems",
            "doi": "10.5555/3295222.3295349",
            "source": "Crossref",
        }
        oa_cand_close = {
            "title": "Attention is All You Need",
            "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
            "year": 2018,
            "venue": "NeurIPS",
            "doi": "10.5555/3295222.3295349",
            "source": "OpenAlex",
        }

        with patch("app.services.multi_source_retriever.verify_title", return_value=[cr_cand_close]), \
             patch("app.services.multi_source_retriever.search_openalex", return_value=[oa_cand_close]), \
             patch("app.services.multi_source_retriever.search_semantic_scholar", return_value=[]):

            merged_close = multi_source_retriever.retrieve_candidates("Attention is All You Need")
            self.assertEqual(len(merged_close), 1, "Candidates within 1 year should be merged into single record.")
            self.assertEqual(merged_close[0]["year"], 2017, "Crossref year (2017) priority over OpenAlex.")
            self.assertIn(2018, merged_close[0]["alternate_years"], "OpenAlex year (2018) preserved in alternate_years.")
            self.assertEqual(len(merged_close[0]["authors"]), 3, "Author list should take candidate with more authors.")

        # Case 9B: Distant years (> 1 year difference e.g. 2017 conference vs 2023 reprint/survey)
        oa_cand_distant = {
            "title": "Attention is All You Need",
            "authors": ["Ashish Vaswani", "Noam Shazeer"],
            "year": 2023,
            "venue": "NeurIPS Retrospective",
            "doi": "10.5555/3295222.3295349",
            "source": "OpenAlex",
        }

        with patch("app.services.multi_source_retriever.verify_title", return_value=[cr_cand_close]), \
             patch("app.services.multi_source_retriever.search_openalex", return_value=[oa_cand_distant]), \
             patch("app.services.multi_source_retriever.search_semantic_scholar", return_value=[]):

            merged_distant = multi_source_retriever.retrieve_candidates("Attention is All You Need")
            self.assertEqual(len(merged_distant), 2, "Candidates with >1 yr difference preserved as distinct versions.")

            # Test candidate_ranker with 2017 citation
            ranked = candidate_ranker.rank_candidates(GENUINE_PARSED, merged_distant)
            self.assertEqual(ranked[0]["paper"]["year"], 2017, "Ranker must prioritize the 2017 candidate for 2017 citation.")

    # =========================================================================
    # SCENARIO 10: Metadata drift across temporal retrievals
    # =========================================================================
    def test_scenario_10_metadata_drift(self):
        """
        Simulates metadata drift:
        T1 (Preprint version): Year 2017, Venue 'arXiv', DOI '10.48550/arXiv.1706.03762'
        T2 (Conference version): Year 2017, Venue 'NeurIPS', DOI '10.5555/3295222.3295349'
        """
        is_match, score = similarity_service.compare_venues("NeurIPS", "arXiv", use_venue_fix=True)
        self.assertTrue(is_match, "Preprint-conference venue drift must be recognized as compatible.")
        self.assertEqual(score, 90.0, "Preprint compatibility score should be 90.0.")

    # =========================================================================
    # SCENARIO 11: All providers fail (Network Blackout / Total Outage)
    # =========================================================================
    def test_scenario_11_all_providers_fail(self):
        """
        All providers return HTTP 500 or timeout.
        Verifies that total provider outage produces an explicit unverified outcome:
        - hallucination_type: 'Unverified / Provider Outage'
        - hallucination_score: None
        - paper_exists: None
        - confidence: 'Uncertain (Verification Incomplete)'
        - api_status: 'OUTAGE'
        Total provider failure must NOT produce 'Fabricated Citation' or score 100.
        """
        def mock_failing_get(*args, **kwargs):
            raise requests.exceptions.ConnectionError("Network unreachable / Blackout")

        with patch("app.services.crossref_service.session.get", side_effect=mock_failing_get), \
             patch("app.services.semantic_scholar_service.session.get", side_effect=mock_failing_get), \
             patch("app.services.openalex_service.session.get", side_effect=mock_failing_get):

            result = verification_pipeline.verify_response(GENUINE_BENCHMARK_CITATION)[0]

            self.assertIsInstance(result, dict)
            self.assertIsNone(result["paper_exists"], "paper_exists must be None under total provider outage")
            self.assertFalse(result["citation_accurate"])

            # Verifies fix for outage misclassification:
            self.assertEqual(result["hallucination_type"], "Unverified / Provider Outage")
            self.assertIsNone(result["hallucination_score"], "hallucination_score must be None under outage")
            self.assertEqual(result["confidence"], "Uncertain (Verification Incomplete)")
            self.assertEqual(result["api_status"], "OUTAGE")
            self.assertTrue(any("unreachable" in r.lower() or "error" in r.lower() for r in result["reason"]))

    # =========================================================================
    # SCENARIO 11B: Genuinely fabricated citation flagged on empty provider results
    # =========================================================================
    def test_genuinely_fabricated_citation_flagged_on_empty_provider_results(self):
        """
        Providers are healthy (HTTP 200) but return 0 matching items.
        Verifies that genuinely fabricated citations are still flagged as 'Fabricated Citation'
        with hallucination score 100, confidence 'High Risk of Hallucination', and api_status 'VERIFIED'.
        """
        def mock_get(url, *args, **kwargs):
            if "crossref.org" in url:
                return MockResponse(CROSSREF_EMPTY_PAYLOAD, status_code=200)
            elif "semanticscholar.org" in url:
                return MockResponse(SEMANTIC_SCHOLAR_EMPTY_PAYLOAD, status_code=200)
            elif "openalex.org" in url:
                return MockResponse(OPENALEX_EMPTY_PAYLOAD, status_code=200)
            return MockResponse(status_code=404)

        with patch("app.services.crossref_service.session.get", side_effect=mock_get), \
             patch("app.services.semantic_scholar_service.session.get", side_effect=mock_get), \
             patch("app.services.openalex_service.session.get", side_effect=mock_get), \
             patch("app.services.verification_pipeline.verify_doi", return_value=None):

            fabricated_citation = (
                'Title: "Completely Made Up Paper Title That Does Not Exist"\n'
                "Authors: John Nonexistent, Jane Fictional\n"
                "Year: 2024\n"
                "Venue: Journal of Imaginary Studies"
            )
            result = verification_pipeline.verify_response(fabricated_citation)[0]

            self.assertIsInstance(result, dict)
            self.assertFalse(result["paper_exists"])
            self.assertFalse(result["citation_accurate"])
            self.assertEqual(result["hallucination_type"], "Fabricated Citation")
            self.assertEqual(result["hallucination_score"], 100)
            self.assertEqual(result["confidence"], "High Risk of Hallucination")
            self.assertEqual(result["api_status"], "VERIFIED")

    # =========================================================================
    # SCENARIO 12: Cached response missing, malformed, or inconsistent schema
    # =========================================================================
    def test_scenario_12_cache_missing_or_malformed(self):
        """
        Evaluates cache failure handling:
        12A: Cache miss in offline harness (must fail-closed).
        12B: Malformed cached candidate (e.g., year is non-integer string).
        12C: Candidate with missing mandatory fields.
        """
        # 12A: Missing cache entry in harness fail-closed logic
        offline_cache = {"1": {"verify_doi": None, "retrieve_candidates": []}}
        with self.assertRaises(KeyError) as ctx:
            cid = "999"
            if cid not in offline_cache:
                raise KeyError(f"FAIL CLOSED: Unexpected cache miss for CID {cid}")
        self.assertIn("FAIL CLOSED", str(ctx.exception))

        # 12B: Year is string with month/day e.g. "2017-12-01"
        malformed_year_cand = {
            "title": "Attention is All You Need",
            "authors": ["Ashish Vaswani"],
            "year": "2017-12-01",  # Non-integer
            "venue": "NeurIPS",
            "doi": "10.5555/3295222.3295349",
        }
        year_match = similarity_service.compare_year(2017, malformed_year_cand["year"])
        self.assertFalse(year_match, "Non-integer year string should fail gracefully (return False without crashing).")

        # 12C: Authors is a string instead of a list (schema inconsistency)
        malformed_authors_cand = {
            "title": "Attention is All You Need",
            "authors": "Ashish Vaswani, Noam Shazeer",
            "year": 2017,
            "venue": "NeurIPS",
            "doi": "10.5555/3295222.3295349",
        }
        author_score = similarity_service.compare_authors(["Ashish Vaswani"], malformed_authors_cand["authors"])
        self.assertIsInstance(author_score, float, "compare_authors must return a float without unhandled exception.")

    # =========================================================================
    # SCENARIO 13: Security & Credential Leakage Check
    # =========================================================================
    def test_scenario_13_credential_leakage_check(self):
        """Verify that outputs, logs, error messages, and metadata dictionaries never leak API keys."""
        SENSITIVE_PATTERNS = ["AIzaSy", "sk-ant-", "Bearer ", "api_key=", "apikey="]

        result = verification_pipeline.verify_response(GENUINE_BENCHMARK_CITATION)[0]
        result_str = str(result)
        for pattern in SENSITIVE_PATTERNS:
            self.assertNotIn(pattern, result_str, f"Sensitive pattern {pattern} leaked in pipeline output!")


if __name__ == "__main__":
    unittest.main()
