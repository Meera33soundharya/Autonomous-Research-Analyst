import json
import unittest
from unittest.mock import patch

from app.agents.researcher import analyze_sources
from app.agents.searcher import run_search
from app.graph.workflow import citation_checker_node, researcher_node
from app.services import llm_service
from app.services.query_expander import expand_search_queries
from app.services import search_service


class ResearchExtractionTests(unittest.TestCase):
    question = "What did the study measure?"
    passage = "The study included 240 participants across three hospitals."
    source = {
        "question": question,
        "questions": [question],
        "title": "A clinical study",
        "url": "https://example.org/study",
        "abstract": passage,
        "authors": ["A. Researcher"],
        "year": "2024",
    }

    def _finding_response(self, passage=None):
        return json.dumps({
            "findings": [{
                "source_number": 1,
                "claim": "The study included 240 participants.",
                "supporting_passage": passage or self.passage,
            }],
        })

    @patch("app.agents.researcher.ask_llm")
    def test_extracts_claim_from_exact_source_passage_and_abstract(self, ask_llm):
        ask_llm.return_value = self._finding_response()

        result = analyze_sources(self.question, [self.source])

        self.assertEqual(len(result["findings"]), 1)
        finding = result["findings"][0]
        self.assertEqual(finding["supporting_passage"], self.passage)
        self.assertEqual(finding["source_url"], self.source["url"])
        self.assertEqual(finding["research_question"], self.question)
        self.assertEqual(finding["supporting_source_passage"], self.passage)
        self.assertEqual(finding["source_identifier"], self.source["url"])
        self.assertEqual(finding["extraction_status"], "EXTRACTION_COMPLETED")
        self.assertEqual(
            result["diagnostics"]["status"],
            "EXTRACTION_COMPLETED",
        )
        self.assertEqual(result["diagnostics"]["usable_source_count"], 1)
        prompt = ask_llm.call_args.args[0]
        self.assertIn(self.passage, prompt)
        self.assertIn(self.question, prompt)
        self.assertIn(self.source["url"], prompt)

    @patch("app.agents.researcher.ask_llm")
    def test_rejects_passage_not_present_in_source(self, ask_llm):
        ask_llm.return_value = self._finding_response(
            "The trial enrolled 240 people."
        )

        result = analyze_sources(self.question, [self.source])

        self.assertEqual(result["findings"], [])
        self.assertEqual(
            result["diagnostics"]["rejected_findings"][0]["reason"],
            "supporting_passage_not_found_in_source",
        )

    @patch("app.agents.researcher.ask_llm")
    def test_passage_must_preserve_original_case(self, ask_llm):
        ask_llm.return_value = self._finding_response(
            self.passage.lower()
        )

        result = analyze_sources(self.question, [self.source])

        self.assertEqual(result["findings"], [])
        self.assertEqual(
            result["diagnostics"]["rejected_findings"][0]["reason"],
            "supporting_passage_not_found_in_source",
        )

    @patch("app.agents.researcher.ask_llm")
    def test_empty_source_content_is_extraction_failure(self, ask_llm):
        source = {**self.source, "content": "", "abstract": ""}

        result = analyze_sources(self.question, [source])

        self.assertEqual(result["findings"], [])
        self.assertEqual(
            result["diagnostics"]["status"],
            "EXTRACTION_FAILED",
        )
        self.assertEqual(
            result["diagnostics"]["rejected_sources"][0]["reason"],
            "source_has_no_content_or_abstract",
        )
        ask_llm.assert_not_called()

    @patch(
        "app.agents.researcher.ask_llm",
        return_value='{"findings": []}',
    )
    def test_valid_empty_findings_means_no_relevant_evidence(self, ask_llm):
        result = analyze_sources(self.question, [self.source])

        self.assertEqual(result["findings"], [])
        self.assertEqual(
            result["diagnostics"]["status"],
            "NO_RELEVANT_EVIDENCE",
        )
        self.assertEqual(result["diagnostics"]["error"], "")
        ask_llm.assert_called_once()

    @patch("app.agents.researcher.ask_llm")
    def test_source_without_url_cannot_create_untraceable_finding(self, ask_llm):
        source = {
            "title": "A clinical study",
            "abstract": self.passage,
        }

        result = analyze_sources(self.question, [source])

        self.assertEqual(result["findings"], [])
        self.assertEqual(
            result["diagnostics"]["status"],
            "EXTRACTION_FAILED",
        )
        self.assertEqual(
            result["diagnostics"]["rejected_sources"][0]["reason"],
            "source_has_no_url",
        )
        ask_llm.assert_not_called()

    @patch("app.agents.researcher.ask_llm")
    def test_retries_malformed_json_once(self, ask_llm):
        ask_llm.side_effect = ["not JSON", self._finding_response()]

        result = analyze_sources(self.question, [self.source])

        self.assertEqual(len(result["findings"]), 1)
        self.assertEqual(result["diagnostics"]["retry_count"], 1)
        self.assertEqual(ask_llm.call_count, 2)

    @patch("app.agents.researcher.ask_llm", return_value="not JSON")
    def test_malformed_json_is_explicitly_invalid_after_retry(self, ask_llm):
        result = analyze_sources(self.question, [self.source])

        self.assertEqual(result["findings"], [])
        self.assertEqual(result["diagnostics"]["status"], "INVALID_LLM_RESPONSE")
        self.assertEqual(result["diagnostics"]["request_attempt_count"], 2)
        self.assertEqual(result["diagnostics"]["retry_count"], 1)
        self.assertEqual(ask_llm.call_count, 2)

    @patch(
        "app.agents.researcher.ask_llm",
        return_value=json.dumps({
            "findings": [{
                "source_number": 1,
                "claim": "",
                "supporting_passage": "A passage.",
                "unexpected": "field",
            }],
        }),
    )
    def test_schema_invalid_findings_are_rejected_and_diagnosed(self, ask_llm):
        result = analyze_sources(self.question, [self.source])

        self.assertEqual(result["findings"], [])
        self.assertEqual(result["diagnostics"]["status"], "INVALID_LLM_RESPONSE")
        self.assertEqual(
            result["diagnostics"]["rejected_findings"][0]["reason"],
            "invalid_finding_schema",
        )
        self.assertEqual(ask_llm.call_count, 2)

    @patch("app.agents.researcher.ask_llm")
    def test_valid_claim_survives_missing_title_metadata(self, ask_llm):
        source = {
            "url": self.source["url"],
            "abstract": self.passage,
        }
        ask_llm.return_value = self._finding_response()

        result = analyze_sources(self.question, [source])

        self.assertEqual(len(result["findings"]), 1)
        self.assertEqual(result["findings"][0]["source_title"], "")
        self.assertEqual(
            result["findings"][0]["source_identifier"],
            self.source["url"],
        )

    @patch("app.agents.researcher.ask_llm", side_effect=TimeoutError("secret"))
    def test_timeout_is_explicitly_a_request_failure_without_error_body(self, ask_llm):
        result = analyze_sources(self.question, [self.source])

        self.assertEqual(result["findings"], [])
        self.assertEqual(result["diagnostics"]["status"], "LLM_REQUEST_FAILED")
        self.assertEqual(result["diagnostics"]["error"], "TimeoutError")
        self.assertNotIn("secret", str(result["diagnostics"]))
        ask_llm.assert_called_once()

    @patch("app.agents.researcher.ask_llm")
    def test_duplicate_claims_keep_one_finding_and_corroborating_source(self, ask_llm):
        second_source = {
            **self.source,
            "title": "Another clinical study",
            "url": "https://example.org/another-study",
            "abstract": self.passage,
        }
        ask_llm.return_value = json.dumps({
            "findings": [
                {
                    "source_number": 1,
                    "claim": "The study included 240 participants.",
                    "supporting_passage": self.passage,
                },
                {
                    "source_number": 2,
                    "claim": "The study included 240 participants.",
                    "supporting_passage": self.passage,
                },
            ],
        })

        result = analyze_sources(
            self.question,
            [self.source, second_source],
        )

        self.assertEqual(len(result["findings"]), 1)
        self.assertEqual(
            len(result["findings"][0]["corroborating_sources"]),
            1,
        )
        self.assertEqual(
            result["diagnostics"]["rejected_findings"][0]["reason"],
            "duplicate_claim_deduplicated",
        )

    @patch("app.agents.researcher.ask_llm")
    def test_bounds_extraction_context_and_reports_omitted_sources(self, ask_llm):
        sources = [
            {
                **self.source,
                "title": f"Study {index}",
                "url": f"https://example.org/study-{index}",
                "content": f"Evidence {index}. " + ("x" * 3000),
                "abstract": "",
            }
            for index in range(8)
        ]
        ask_llm.return_value = self._finding_response("Evidence 0.")

        result = analyze_sources(self.question, sources)

        self.assertEqual(len(result["findings"]), 1)
        self.assertEqual(result["diagnostics"]["eligible_source_count"], 8)
        self.assertEqual(result["diagnostics"]["usable_source_count"], 4)
        self.assertEqual(result["diagnostics"]["omitted_source_count"], 4)
        self.assertEqual(result["diagnostics"]["truncated_source_count"], 4)
        prompt = ask_llm.call_args.args[0]
        self.assertIn("Study 3", prompt)
        self.assertNotIn("Study 4", prompt)
        self.assertLessEqual(prompt.count("CONTENT:"), 4)

    @patch("app.agents.researcher.ask_llm")
    def test_limits_findings_per_question_and_records_overflow(self, ask_llm):
        source = {
            **self.source,
            "content": " ".join(f"Finding {index}." for index in range(5)),
            "abstract": "",
        }
        ask_llm.return_value = json.dumps({
            "findings": [
                {
                    "source_number": 1,
                    "claim": f"Finding {index}.",
                    "supporting_passage": f"Finding {index}.",
                }
                for index in range(5)
            ],
        })

        result = analyze_sources(self.question, [source])

        self.assertEqual(len(result["findings"]), 3)
        rejected = result["diagnostics"]["rejected_findings"]
        self.assertEqual(len(rejected), 2)
        self.assertTrue(
            all(item["reason"] == "per_question_finding_limit" for item in rejected)
        )

    @patch("app.agents.researcher.ask_llm")
    def test_reports_unavailable_model_instead_of_fake_findings(self, ask_llm):
        ask_llm.return_value = "The model service is unavailable."

        result = analyze_sources(self.question, [self.source])

        self.assertEqual(result["findings"], [])
        self.assertIn("unavailable", result["diagnostics"]["error"])
        self.assertEqual(result["diagnostics"]["status"], "LLM_REQUEST_FAILED")
        ask_llm.assert_called_once()

    @patch(
        "app.agents.researcher.ask_llm",
        return_value=(
            "The model service is unavailable "
            "(OpenRouter RateLimitError, HTTP 429)."
        ),
    )
    def test_rate_limit_status_is_preserved_without_provider_body(self, ask_llm):
        result = analyze_sources(self.question, [self.source])

        self.assertEqual(result["diagnostics"]["status"], "LLM_REQUEST_FAILED")
        self.assertEqual(result["diagnostics"]["error_type"], "RateLimitError")
        self.assertEqual(result["diagnostics"]["http_status"], 429)
        self.assertIn("HTTP 429", result["diagnostics"]["error"])
        ask_llm.assert_called_once()

    @patch("app.agents.researcher.ask_llm", return_value="")
    def test_empty_model_content_is_retried_and_reported(self, ask_llm):
        result = analyze_sources(self.question, [self.source])

        self.assertEqual(result["findings"], [])
        self.assertEqual(result["diagnostics"]["retry_count"], 1)
        self.assertEqual(result["diagnostics"]["status"], "INVALID_LLM_RESPONSE")
        self.assertIn("empty content", result["diagnostics"]["error"])
        self.assertEqual(ask_llm.call_count, 2)

    @patch("app.agents.researcher.ask_llm")
    def test_rejects_sources_assigned_to_a_different_question(self, ask_llm):
        result = analyze_sources("A different question?", [self.source])

        self.assertEqual(result["findings"], [])
        self.assertEqual(
            result["diagnostics"]["rejected_sources"][0]["reason"],
            "source_question_mismatch",
        )
        ask_llm.assert_not_called()


class SearchQuestionAssociationTests(unittest.TestCase):
    @patch("app.agents.searcher.search_web")
    @patch("app.agents.searcher.expand_search_queries")
    def test_deduplicates_source_without_losing_its_question_links(
        self, expand_queries, search_web
    ):
        question_a = "What is the architecture?"
        question_b = "What are the limitations?"
        expand_queries.return_value = {
            question_a: ["shared search"],
            question_b: ["shared search"],
        }
        search_web.return_value = [{
            "title": "A shared source",
            "url": "https://example.org/shared",
            "content": "Evidence shared by both questions.",
        }]

        results = run_search("Research topic", [question_a, question_b])

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["questions"], [question_a, question_b])
        self.assertEqual(
            results[0]["source_identifier"],
            "https://example.org/shared",
        )
        search_web.assert_called_once()

    @patch("app.services.query_expander.get_related_memory", return_value=[])
    @patch(
        "app.services.query_expander.ask_llm",
        return_value="The model service is unavailable.",
    )
    def test_combined_voice_complaint_topic_gets_targeted_queries(
        self, _ask_llm, _get_related_memory
    ):
        topic = (
            "AI-Powered Voice Assistant Complaint Registration and "
            "Automatic Field Officer Assignment System"
        )
        questions = [
            "What evidence evaluates speech-to-text complaint registration?",
            "How do multilingual voice interfaces support citizen grievance registration?",
            "How are grievances automatically classified?",
            "How are field officers assigned?",
        ]

        queries = expand_search_queries(topic, questions)
        self.assertIn(
            "multilingual voice interfaces",
            queries[questions[1]][0],
        )
        self.assertIn(
            "field officer assignment",
            queries[questions[3]][0],
        )
        all_queries = " ".join(
            query
            for question_queries in queries.values()
            for query in question_queries
        ).casefold()

        self.assertIn("voice-based complaint registration", all_queries)
        self.assertIn("multilingual voice interfaces", all_queries)
        self.assertIn("automated complaint classification", all_queries)
        self.assertIn("field officer assignment", all_queries)

    @patch("app.services.query_expander.get_related_memory", return_value=[])
    @patch(
        "app.services.query_expander.ask_llm",
        return_value="The model service is unavailable.",
    )
    def test_query_expansion_fallback_is_recorded(
        self, _ask_llm, _get_related_memory
    ):
        question = "How is evidence collected?"
        diagnostics = []

        queries = expand_search_queries(
            "Research topic",
            [question],
            diagnostics,
        )

        self.assertEqual(len(queries[question]), 2)
        self.assertTrue(diagnostics)
        self.assertIn("unavailable", diagnostics[0]["error"])

    @patch("app.services.search_service.search_scholarly", return_value=[])
    def test_missing_tavily_key_is_reported_without_crashing(self, _search_scholarly):
        with patch.object(search_service, "client", None):
            diagnostics = []
            results = search_service.search_web(
                "research query",
                diagnostics=diagnostics,
            )

        self.assertEqual(results, [])
        self.assertEqual(diagnostics[0]["provider"], "Tavily")
        self.assertIn("not configured", diagnostics[0]["error"])


class WorkflowExtractionStatusTests(unittest.TestCase):
    @patch("app.graph.workflow.analyze_sources")
    def test_llm_failure_reaches_workflow_as_failed_research(self, analyze):
        question = "How is evidence collected?"
        analyze.return_value = {
            "question": question,
            "findings": [],
            "diagnostics": {
                "status": "LLM_REQUEST_FAILED",
                "error": "LLM request failed (RateLimitError, HTTP 429)",
            },
        }

        researcher_result = researcher_node({
            "topic": "Research topic",
            "research_questions": [question],
            "search_results": [{"url": "https://example.org"}],
        })

        self.assertEqual(
            researcher_result["extraction_status"],
            "LLM_REQUEST_FAILED",
        )
        self.assertEqual(
            researcher_result["pipeline_diagnostics"]["extraction"]["errors"][0]["detail"],
            "LLM request failed (RateLimitError, HTTP 429)",
        )

        with patch(
            "app.graph.workflow.check_citations",
            return_value=[],
        ):
            citation_result = citation_checker_node({
                "topic": "Research topic",
                "cleaned_evidence": [],
                "pipeline_diagnostics": researcher_result["pipeline_diagnostics"],
            })

        self.assertEqual(citation_result["run_status"], "FAILED")


class LLMServiceFailureTests(unittest.TestCase):
    def test_rate_limit_is_reported_without_returning_provider_body(self):
        class SimulatedRateLimitError(Exception):
            status_code = 429

            def __str__(self):
                return "private provider response body"

        with patch.object(llm_service, "client") as client:
            client.chat.completions.create.side_effect = SimulatedRateLimitError()

            response = llm_service.ask_llm("test prompt")

        self.assertIn("HTTP 429", response)
        self.assertIn("SimulatedRateLimitError", response)
        self.assertNotIn("private provider response body", response)


if __name__ == "__main__":
    unittest.main()
