import json
import logging
import re
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, ValidationError

from app.services.llm_service import ask_llm


logger = logging.getLogger(__name__)

MAX_EXTRACTION_SOURCES = 4
MAX_SOURCE_CONTENT_CHARACTERS = 1600
MAX_FINDINGS_PER_QUESTION = 3

NO_RELEVANT_EVIDENCE = "NO_RELEVANT_EVIDENCE"
LLM_REQUEST_FAILED = "LLM_REQUEST_FAILED"
INVALID_LLM_RESPONSE = "INVALID_LLM_RESPONSE"
EXTRACTION_FAILED = "EXTRACTION_FAILED"
EXTRACTION_COMPLETED = "EXTRACTION_COMPLETED"


class FindingCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_identifier: str | None = Field(default=None, min_length=1)
    source_number: int | None = Field(default=None, ge=1)
    claim: str = Field(min_length=1)
    supporting_source_passage: str = Field(
        validation_alias=AliasChoices(
            "supporting_source_passage",
            "supporting_passage",
        ),
        min_length=1,
    )


class FindingEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_question: str = Field(min_length=1)
    claim: str = Field(min_length=1)
    supporting_source_passage: str = Field(min_length=1)
    source_title: str
    source_url: str = Field(min_length=1)
    source_identifier: str = Field(min_length=1)
    extraction_status: Literal["EXTRACTION_COMPLETED"]


class FindingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    findings: list[Any]


def _normalized_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def _normalized_passage(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _parse_findings(response: str) -> list[Any] | None:
    decoder = json.JSONDecoder()
    for index, character in enumerate(response):
        if character != "{":
            continue
        try:
            payload, _ = decoder.raw_decode(response[index:])
        except json.JSONDecodeError:
            continue
        try:
            return FindingResponse.model_validate(payload).findings
        except ValidationError:
            return None
    return None


def _source_identifier(source: dict, index: int) -> str:
    return str(
        source.get("source_identifier")
        or source.get("doi")
        or source.get("url")
        or f"source-{index + 1}"
    ).strip()


def _base_diagnostics(source_count: int) -> dict:
    return {
        "status": NO_RELEVANT_EVIDENCE,
        "source_count": source_count,
        "eligible_source_count": 0,
        "usable_source_count": 0,
        "omitted_source_count": 0,
        "truncated_source_count": 0,
        "extracted_finding_count": 0,
        "response_findings_count": 0,
        "rejected_sources": [],
        "rejected_findings": [],
        "retry_count": 0,
        "request_attempt_count": 0,
        "response_character_count": 0,
        "error_type": "",
        "http_status": None,
        "error": "",
    }


def _result(question: str, findings: list[dict], diagnostics: dict) -> dict:
    diagnostics["extracted_finding_count"] = len(findings)
    return {
        "question": question,
        "findings": findings,
        "diagnostics": diagnostics,
    }


def analyze_sources(
    question: str,
    sources: list[dict],
    topic: str = "",
    scope: str = "",
) -> dict:
    diagnostics = _base_diagnostics(len(sources))
    tagged_sources = [
        source for source in sources
        if source.get("question") or source.get("questions")
    ]
    if tagged_sources:
        question_sources = [
            source for source in tagged_sources
            if (
                source.get("question") == question
                or question in source.get("questions", [])
            )
        ]
        diagnostics["rejected_sources"].extend(
            {
                "source_identifier": (
                    source.get("source_identifier")
                    or source.get("doi")
                    or source.get("url", "")
                ),
                "reason": "source_question_mismatch",
            }
            for source in tagged_sources
            if (
                source.get("question") != question
                and question not in source.get("questions", [])
            )
        )
    else:
        question_sources = sources

    eligible_sources = []
    for source_index, source in enumerate(question_sources):
        content = str(source.get("content") or source.get("abstract") or "").strip()
        if not content:
            diagnostics["rejected_sources"].append({
                "source_identifier": _source_identifier(source, source_index),
                "reason": "source_has_no_content_or_abstract",
            })
            continue
        if not str(source.get("url", "")).strip():
            diagnostics["rejected_sources"].append({
                "source_identifier": _source_identifier(source, source_index),
                "reason": "source_has_no_url",
            })
            continue
        eligible_sources.append((source, content, source_index))

    diagnostics["eligible_source_count"] = len(eligible_sources)
    diagnostics["omitted_source_count"] = max(
        0,
        len(eligible_sources) - MAX_EXTRACTION_SOURCES,
    )
    usable_sources = eligible_sources[:MAX_EXTRACTION_SOURCES]
    source_blocks = []
    source_index_by_identifier = {}

    for prompt_index, (source, content, source_index) in enumerate(
        usable_sources,
        start=1,
    ):
        if len(content) > MAX_SOURCE_CONTENT_CHARACTERS:
            content = content[:MAX_SOURCE_CONTENT_CHARACTERS]
            diagnostics["truncated_source_count"] += 1

        identifier = _source_identifier(source, source_index)
        source_index_by_identifier[identifier] = prompt_index - 1
        source_blocks.append(
            f"""
SOURCE {prompt_index}
Source identifier: {identifier}
Title: {source.get("title", "")}
URL: {source.get("url", "")}
Authors: {source.get("authors", [])}
Year: {source.get("year", "")}
DOI: {source.get("doi", "")}

CONTENT:
{content}
"""
        )

    diagnostics["usable_source_count"] = len(usable_sources)
    if not usable_sources:
        source_text_unavailable = any(
            item["reason"] in {
                "source_has_no_content_or_abstract",
                "source_has_no_url",
            }
            for item in diagnostics["rejected_sources"]
        )
        if source_text_unavailable:
            diagnostics["status"] = EXTRACTION_FAILED
            diagnostics["error"] = (
                "Retrieved sources lack usable text or traceable URLs."
            )
        else:
            diagnostics["status"] = NO_RELEVANT_EVIDENCE
        logger.info(
            "Research extraction skipped: status=%s source_count=%d eligible=%d",
            diagnostics["status"],
            len(sources),
            diagnostics["eligible_source_count"],
        )
        return _result(question, [], diagnostics)

    prompt = f"""
You are the Evidence Researcher Agent.

RESEARCH QUESTION:
{question}

RESEARCH TOPIC:
{topic}

RESEARCH SCOPE:
{scope or "No additional scope specified"}

The topic may describe a combined application made from several components.
Extract evidence about a component only when it materially answers the stated
research question. A source about an unrelated voice assistant or an unrelated
government service is not relevant merely because it shares a keyword.

You are given only the source material below.

SOURCE MATERIAL:
{"".join(source_blocks)}

TASK:
Extract factual findings that directly answer the research question.
Extract only as many as the sources support; return an empty findings array
when the supplied sources contain no relevant evidence.

STRICT RULES:
1. Use ONLY the supplied source material. Never use outside knowledge.
2. Never invent facts, numbers, dates, statistics, or sources.
3. Every finding must be directly supported by its assigned source.
4. Do not combine multiple sources into one finding.
5. Each claim must contain one clear factual statement.
6. Include a supporting passage copied verbatim from that source's CONTENT.
7. Use the exact source identifier shown in the source block.
8. Do not treat general similarity as evidence for the integrated system.

Return only valid JSON in this shape:
{{
  "findings": [
    {{
      "source_identifier": "exact source identifier",
      "claim": "One factual claim supported by the source.",
      "supporting_source_passage": "An exact passage copied from the source."
    }}
  ]
}}
"""

    parsed_findings = None
    schema_rejections = []
    last_response = ""
    for attempt in range(2):
        diagnostics["request_attempt_count"] += 1
        logger.info(
            "Research extraction request started: sources=%d content_characters=%d attempt=%d",
            len(usable_sources),
            sum(len(content) for _, content, _ in usable_sources),
            attempt + 1,
        )
        try:
            last_response = ask_llm(
                prompt if attempt == 0 else (
                    prompt
                    + "\nYour previous response was invalid. "
                    "Return the required JSON object only."
                ),
            ) or ""
        except Exception as error:
            diagnostics["status"] = LLM_REQUEST_FAILED
            diagnostics["error"] = f"{type(error).__name__}"
            logger.error(
                "Research extraction request failed: error_type=%s",
                type(error).__name__,
            )
            return _result(question, [], diagnostics)

        diagnostics["response_character_count"] = len(last_response)
        if "model service is unavailable" in last_response.casefold():
            diagnostics["status"] = LLM_REQUEST_FAILED
            error_type = re.search(
                r"OpenRouter\s+([A-Za-z][A-Za-z0-9_]*)",
                last_response,
            )
            http_status = re.search(r"HTTP\s+(\d{3})", last_response)
            diagnostics["error_type"] = (
                error_type.group(1) if error_type else "ServiceUnavailable"
            )
            diagnostics["http_status"] = (
                int(http_status.group(1)) if http_status else None
            )
            diagnostics["error"] = (
                f"LLM service unavailable ({diagnostics['error_type']}"
                + (
                    f", HTTP {diagnostics['http_status']})"
                    if diagnostics["http_status"]
                    else ")"
                )
            )
            logger.warning(
                "Research extraction request failed: error_type=%s http_status=%s",
                diagnostics["error_type"],
                diagnostics["http_status"] or "unknown",
            )
            return _result(question, [], diagnostics)

        if not last_response.strip():
            diagnostics["error"] = "LLM returned empty content."

        parsed_findings = _parse_findings(last_response)
        if parsed_findings is not None:
            schema_rejections = []
            candidates = []
            for finding_index, item in enumerate(parsed_findings):
                try:
                    candidates.append(FindingCandidate.model_validate(item))
                except (ValidationError, TypeError, ValueError) as error:
                    schema_rejections.append({
                        "index": finding_index,
                        "reason": "invalid_finding_schema",
                        "error_type": type(error).__name__,
                    })
            if candidates or not parsed_findings:
                parsed_findings = candidates
                break
            parsed_findings = None
        else:
            schema_rejections = []

        if attempt == 0:
            diagnostics["retry_count"] += 1

    if parsed_findings is None:
        diagnostics["status"] = INVALID_LLM_RESPONSE
        diagnostics["error"] = diagnostics["error"] or (
            "LLM response did not match the required JSON schema."
        )
        diagnostics["rejected_findings"].extend(schema_rejections)
        logger.warning(
            "Research extraction response invalid: response_characters=%d attempts=%d",
            diagnostics["response_character_count"],
            diagnostics["request_attempt_count"],
        )
        return _result(question, [], diagnostics)

    diagnostics["response_findings_count"] = len(parsed_findings)
    if not parsed_findings:
        diagnostics["status"] = NO_RELEVANT_EVIDENCE
        logger.info(
            "Research extraction completed without relevant evidence: usable_sources=%d",
            diagnostics["usable_source_count"],
        )
        return _result(question, [], diagnostics)

    diagnostics["rejected_findings"].extend(schema_rejections)
    findings = []
    seen_claims = {}
    for finding_index, candidate in enumerate(parsed_findings):
        if candidate.source_identifier:
            source_index = source_index_by_identifier.get(
                candidate.source_identifier
            )
        elif candidate.source_number is not None:
            source_index = candidate.source_number - 1
        else:
            source_index = None

        if source_index is None or not 0 <= source_index < len(usable_sources):
            diagnostics["rejected_findings"].append({
                "index": finding_index,
                "reason": "unknown_source_identifier",
            })
            continue

        source, source_content, original_source_index = usable_sources[source_index]
        passage = candidate.supporting_source_passage.strip()
        if (
            _normalized_passage(passage)
            not in _normalized_passage(source_content)
        ):
            diagnostics["rejected_findings"].append({
                "index": finding_index,
                "reason": "supporting_passage_not_found_in_source",
            })
            continue

        identifier = _source_identifier(source, original_source_index)
        claim = candidate.claim.strip()
        claim_key = _normalized_text(claim)
        if claim_key in seen_claims:
            primary_finding = findings[seen_claims[claim_key]]
            primary_finding["corroborating_sources"].append({
                "source_identifier": identifier,
                "source_title": str(source.get("title") or ""),
                "source_url": str(source.get("url") or ""),
                "supporting_source_passage": passage,
            })
            diagnostics["rejected_findings"].append({
                "index": finding_index,
                "reason": "duplicate_claim_deduplicated",
            })
            continue
        if len(findings) >= MAX_FINDINGS_PER_QUESTION:
            diagnostics["rejected_findings"].append({
                "index": finding_index,
                "reason": "per_question_finding_limit",
            })
            continue

        validated_finding = FindingEvidence.model_validate({
            "research_question": question,
            "claim": claim,
            "supporting_source_passage": passage,
            "source_title": str(source.get("title") or ""),
            "source_url": str(source.get("url") or ""),
            "source_identifier": identifier,
            "extraction_status": EXTRACTION_COMPLETED,
        }).model_dump()
        validated_finding.update({
            "question": question,
            "supporting_passage": passage,
            "source_content": source_content,
            "source_quality": source.get("source_quality", 0),
            "authors": source.get("authors", []),
            "year": source.get("year", ""),
            "doi": source.get("doi", ""),
            "source_number": source_index + 1,
            "corroborating_sources": [],
        })
        seen_claims[claim_key] = len(findings)
        findings.append(validated_finding)

    diagnostics["status"] = (
        EXTRACTION_COMPLETED
        if findings
        else EXTRACTION_FAILED
    )
    if not findings:
        diagnostics["error"] = (
            "The LLM returned claims, but none passed source-provenance validation."
        )
    logger.info(
        "Research extraction finished: status=%s response_findings=%d accepted=%d rejected=%d",
        diagnostics["status"],
        diagnostics["response_findings_count"],
        len(findings),
        len(diagnostics["rejected_findings"]),
    )
    return _result(question, findings, diagnostics)
