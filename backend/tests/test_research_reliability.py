import unittest
from unittest.mock import patch

from app.agents.citation_checker import check_citations
from app.agents.evidence_cleaner import is_low_quality_evidence
from app.agents.topic_normalizer import normalize_research_topic
from app.agents.writer import generate_report
from app.graph.workflow import citation_checker_node


class TopicNormalizationTests(unittest.TestCase):
    def test_removes_explicit_meta_sentence_without_truncating_topic(self):
        result = normalize_research_topic(
            "History of Apollo 11. This is a good test of number accuracy."
        )
        self.assertEqual(result["topic"], "History of Apollo 11.")
        self.assertEqual(
            result["meta"],
            "This is a good test of number accuracy.",
        )

    def test_keeps_periods_when_no_meta_marker_is_present(self):
        result = normalize_research_topic("Research on St. John's mission")
        self.assertEqual(result["topic"], "Research on St. John's mission")

    def test_reads_explicit_topic_and_scope_fields(self):
        result = normalize_research_topic(
            "TOPIC: Apollo missions\nSCOPE: Crewed flights, 1961-1972\nMETA: check numbers"
        )
        self.assertEqual(result["topic"], "Apollo missions")
        self.assertEqual(result["scope"], "Crewed flights, 1961-1972")

    def test_reads_scope_without_a_topic_label(self):
        result = normalize_research_topic(
            "Apollo missions\nSCOPE: Crewed flights"
        )
        self.assertEqual(result["topic"], "Apollo missions")
        self.assertEqual(result["scope"], "Crewed flights")

    def test_does_not_treat_a_research_prompt_as_the_topic(self):
        result = normalize_research_topic(
            "You are a research analyst producing a fact-checked report.\n"
            "STEP 0 - PARSE THE REQUEST\n"
            "TOPIC: the subject to research\nSCOPE: details"
        )
        self.assertEqual(result["topic"], "")


class EvidenceQualityTests(unittest.TestCase):
    def test_keeps_short_numeric_factual_claims(self):
        self.assertFalse(is_low_quality_evidence("Apollo 11 launched July 16, 1969."))

    def test_keeps_claims_with_many_numbers(self):
        claim = "Mission dates are 1, 2, 3, 4, 5, 6, 7, and 8 September."
        self.assertFalse(is_low_quality_evidence(claim))


class RelevanceGateTests(unittest.TestCase):
    def test_irrelevant_claim_is_rejected_before_citation_check(self):
        evidence = [{
            "question": "What were Apollo 11's mission objectives?",
            "findings": [{
                "claim": "A novel explores storytelling techniques.",
                "source_content": "The novel explores storytelling techniques.",
            }],
        }]
        with patch(
            "app.agents.citation_checker.ask_llm",
            return_value="IRRELEVANT | It does not concern Apollo 11.",
        ) as ask_llm:
            result = check_citations(evidence, "Apollo 11")

        finding = result[0]["findings"][0]
        self.assertEqual(finding["relevance_status"], "IRRELEVANT")
        self.assertEqual(finding["status"], "UNSUPPORTED")
        ask_llm.assert_called_once()

    def test_malformed_relevance_response_fails_closed(self):
        evidence = [{
            "question": "Apollo 11 objective",
            "findings": [{
                "claim": "Apollo 11 landed on the Moon.",
                "source_content": "Apollo 11 landed on the Moon.",
            }],
        }]
        with patch(
            "app.agents.citation_checker.ask_llm",
            return_value="The model service is unavailable.",
        ):
            finding = check_citations(evidence, "Apollo 11")[0]["findings"][0]

        self.assertEqual(finding["relevance_status"], "IRRELEVANT")
        self.assertEqual(finding["status"], "UNSUPPORTED")

    def test_relevant_claim_still_requires_citation_support(self):
        evidence = [{
            "question": "Apollo 11 objective",
            "findings": [{
                "claim": "Apollo 11 landed on the Moon.",
                "source_content": "Apollo 11 landed on the Moon.",
            }],
        }]
        with patch(
            "app.agents.citation_checker.ask_llm",
            side_effect=[
                "RELEVANT | Directly concerns the mission.",
                "SUPPORTED",
            ],
        ):
            finding = check_citations(evidence, "Apollo 11")[0]["findings"][0]

        self.assertEqual(finding["relevance_status"], "RELEVANT")
        self.assertEqual(finding["status"], "SUPPORTED")

    def test_workflow_marks_runs_incomplete_when_only_irrelevant_claims_remain(self):
        verified = [{
            "question": "Apollo 11 objectives",
            "findings": [{
                "claim": "A novel explores storytelling techniques.",
                "status": "UNSUPPORTED",
                "relevance_status": "IRRELEVANT",
            }],
        }]
        with patch("app.graph.workflow.check_citations", return_value=verified):
            result = citation_checker_node({
                "cleaned_evidence": verified,
                "topic": "Apollo 11",
            })

        self.assertEqual(result["run_status"], "INCOMPLETE")
        self.assertEqual(result["irrelevant_finding_count"], 1)


class IncompleteReportTests(unittest.TestCase):
    def test_empty_evidence_is_reported_as_incomplete_not_as_findings(self):
        report = generate_report(
            "Apollo 11",
            [{"question": "What were the mission objectives?", "findings": []}],
        )
        self.assertIn("Research status: INCOMPLETE", report)
        self.assertIn("No supported, topic-relevant findings", report)
        self.assertNotIn("identified 0 findings", report)


if __name__ == "__main__":
    unittest.main()
