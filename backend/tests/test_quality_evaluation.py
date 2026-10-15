import unittest

from app.agents.writer import generate_report
from app.services.quality_evaluator import (
    REQUIRED_REPORT_SECTIONS,
    QUALITY_WEIGHTS,
    evaluate_research_quality,
)
from app.services.source_ranker import score_source


class SourceCredibilityTests(unittest.TestCase):
    def test_search_index_label_does_not_imply_peer_review_quality(self):
        index_only = score_source({
            "url": "https://example.com/paper",
            "source_type": "Crossref Scholarly",
        })
        with_metadata = score_source({
            "url": "https://example.com/paper",
            "source_type": "Crossref Scholarly",
            "doi": "10.1234/example",
            "authors": ["A. Researcher"],
            "venue": "Research Journal",
            "year": "2024",
        })

        self.assertLess(index_only, 0.5)
        self.assertGreater(with_metadata, index_only)

    def test_official_government_domain_ranks_above_unverified_blog(self):
        official = score_source({"url": "https://history.nasa.gov/apollo"})
        blog = score_source({"url": "https://medium.com/example"})

        self.assertGreater(official, blog)


class ResearchQualityTests(unittest.TestCase):
    def test_zero_verified_findings_cannot_pass(self):
        result = evaluate_research_quality(
            topic="Apollo",
            questions=["When did Apollo 11 launch?"],
            verified_evidence=[],
            report="# Apollo",
            run_status="INCOMPLETE",
        )

        self.assertEqual(result["score_out_of_10"], 0.0)
        self.assertFalse(result["passing"])
        self.assertIn("No verified", result["gate_reason"])
        self.assertEqual(result["weights_sum"], 1.0)
        for metric_name in (
            "citation_accuracy",
            "topic_relevance",
            "source_credibility",
            "factual_consistency",
            "report_quality",
        ):
            self.assertIsNone(result["metrics"][metric_name]["score"])
            self.assertEqual(
                result["metrics"][metric_name]["status"],
                "NOT_EVALUATED",
            )

    def test_failed_status_is_preserved_without_findings(self):
        result = evaluate_research_quality(
            topic="Apollo",
            questions=["When did Apollo 11 launch?"],
            verified_evidence=[],
            report="# Apollo",
            run_status="FAILED",
        )

        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["score_out_of_10"], 0.0)

    def test_rubric_is_weighted_and_auditable(self):
        report = "\n".join(f"## {section.title()}" for section in REQUIRED_REPORT_SECTIONS)
        evidence = [{
            "question": "When did Apollo 11 launch?",
            "findings": [{
                "question": "When did Apollo 11 launch?",
                "claim": "Apollo 11 launched on July 16, 1969.",
                "supporting_passage": "Apollo 11 launched on July 16, 1969.",
                "source_url": "https://www.nasa.gov/apollo",
                "source_quality": 0.9,
                "status": "SUPPORTED",
                "relevance_status": "RELEVANT",
            }],
        }]

        result = evaluate_research_quality(
            topic="Apollo 11",
            questions=["When did Apollo 11 launch?"],
            verified_evidence=evidence,
            report=report,
            run_status="COMPLETED",
        )

        evaluated = [
            metric
            for metric in result["metrics"].values()
            if metric["score"] is not None
        ]
        expected = round(
            sum(metric["score"] * metric["weight"] for metric in evaluated)
            / sum(metric["weight"] for metric in evaluated),
            2,
        )
        self.assertEqual(result["score_out_of_10"], min(expected, 8.9))
        self.assertEqual(result["metrics"]["report_quality"]["score"], 5)
        self.assertEqual(result["metrics"]["factual_consistency"]["score"], 10)
        self.assertEqual(sum(QUALITY_WEIGHTS.values()), 1.0)
        self.assertFalse(result["independent_review_completed"])
        self.assertLessEqual(result["score_out_of_10"], 8.9)
        self.assertFalse(result["passing"])
        self.assertEqual(
            result["metrics"]["report_quality"]["status"],
            "EVALUATED",
        )

    def test_workflow_error_reduces_reliability_metric(self):
        result = evaluate_research_quality(
            topic="Apollo",
            questions=["When did Apollo 11 launch?"],
            verified_evidence=[{
                "question": "When did Apollo 11 launch?",
                "findings": [{
                    "question": "When did Apollo 11 launch?",
                    "claim": "Apollo 11 launched on July 16, 1969.",
                    "supporting_passage": "Apollo 11 launched on July 16, 1969.",
                    "source_url": "https://www.nasa.gov/apollo",
                    "source_quality": 0.9,
                    "status": "SUPPORTED",
                    "relevance_status": "RELEVANT",
                }],
            }],
            report="\n".join(
                f"## {section.title()}"
                for section in REQUIRED_REPORT_SECTIONS
            ),
            run_status="COMPLETED",
            pipeline_diagnostics={
                "searcher": {"errors": [{"provider": "Tavily"}]},
            },
        )

        self.assertEqual(
            result["metrics"]["workflow_reliability"]["score"],
            5.0,
        )


class ReportGenerationTests(unittest.TestCase):
    def test_report_has_required_sections_and_cited_supporting_passage(self):
        finding = {
            "claim": "Apollo 11 launched on July 16, 1969.",
            "supporting_passage": "Apollo 11 launched on July 16, 1969.",
            "source_title": "Apollo 11 Mission Overview",
            "source_url": "https://www.nasa.gov/apollo",
            "authors": ["NASA"],
            "year": "2019",
            "source_quality": 0.95,
            "status": "SUPPORTED",
            "relevance_status": "RELEVANT",
        }
        report = generate_report(
            "History of the Apollo Space Program",
            [{
                "question": "When did Apollo 11 launch?",
                "findings": [finding],
            }],
            "COMPLETED",
        )

        self.assertIn("**Claim [1]:**", report)
        self.assertIn("**Supporting passage:**", report)
        self.assertIn("## 12. References", report)
        for section in REQUIRED_REPORT_SECTIONS:
            self.assertIn(section, report.casefold())

    def test_writer_never_calls_zero_findings_successful(self):
        report = generate_report("Apollo", [], "COMPLETED")

        self.assertIn("Research status: **INCOMPLETE**", report)
        self.assertIn("No substantive conclusion is drawn", report)


if __name__ == "__main__":
    unittest.main()
