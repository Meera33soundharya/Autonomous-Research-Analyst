import re


STOP_WORDS = {
    "what", "what's", "how", "why", "when", "where", "which",
    "does", "are", "is", "the", "and", "for", "with", "from",
    "into", "that", "this", "these", "those", "their", "there",
    "about", "could", "would", "should", "main", "major", "key",
    "current", "future", "likely", "associated", "related",
    "primary", "technical", "practical", "different"
}


def clean_text(text):
    if not text:
        return ""

    text = str(text)

    text = re.sub(
        r"https?://\S+",
        " ",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"!\[.*?\]\(.*?\)",
        " ",
        text
    )

    text = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r"\1",
        text
    )

    text = re.sub(
        r"#{1,6}\s*",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def tokenize(text):
    words = re.findall(
        r"[a-zA-Z]{4,}",
        text.lower()
    )

    return {
        word
        for word in words
        if word not in STOP_WORDS
    }


def quality_check(claim):

    if not claim:
        return False, "No claim was extracted."

    cleaned = clean_text(claim)

    if len(cleaned) < 50:
        return False, "Claim is too short."

    words = re.findall(
        r"[A-Za-z]{3,}",
        cleaned
    )

    if len(words) < 8:
        return False, "Claim contains too little meaningful text."

    bad_patterns = [
        "company logo",
        "featured image",
        "read more",
        "subscribe",
        "sign up",
        "cookie policy",
        "privacy policy",
        "terms of use",
        "globe newswire"
    ]

    lower = cleaned.lower()

    for pattern in bad_patterns:
        if pattern in lower:
            return False, "Claim contains webpage noise."

    return True, ""


def calculate_relevance(question, claim, source):

    question_words = tokenize(question)

    claim_words = tokenize(claim)

    source_words = tokenize(source)

    if not question_words:
        return 0.0

    claim_overlap = (
        len(question_words.intersection(claim_words))
        / len(question_words)
    )

    source_overlap = (
        len(question_words.intersection(source_words))
        / len(question_words)
    )

    score = (
        claim_overlap * 0.80
        + source_overlap * 0.20
    )

    return min(score, 1.0)


def classify(score):

    if score >= 0.55:
        return "SUPPORTED"

    if score >= 0.25:
        return "PARTIALLY_SUPPORTED"

    return "UNSUPPORTED"


def check_citations(evidence):

    verified = []

    print("\n=== Citation Checker ===")

    for item in evidence:

        question = item.get(
            "question",
            ""
        ).strip()

        verified_findings = []

        for finding in item.get(
            "findings",
            []
        ):

            claim = finding.get(
                "claim",
                ""
            ).strip()

            source = finding.get(
                "source_title",
                ""
            ).strip()

            url = finding.get(
                "source_url",
                ""
            ).strip()

            quality_ok, quality_reason = quality_check(
                claim
            )

            if not quality_ok:

                verified_findings.append({
                    "claim": claim,
                    "source": source,
                    "url": url,
                    "status": "UNSUPPORTED",
                    "score": 0.0,
                    "reason": quality_reason
                })

                continue

            if not url:

                verified_findings.append({
                    "claim": claim,
                    "source": source,
                    "url": url,
                    "status": "UNSUPPORTED",
                    "score": 0.0,
                    "reason": "Source URL is missing."
                })

                continue

            score = calculate_relevance(
                question,
                claim,
                source
            )

            status = classify(score)

            verified_findings.append({
                "claim": claim,
                "source": source,
                "url": url,
                "status": status,
                "score": round(score, 2),
                "reason": (
                    "Relevance calculated from semantic "
                    "keyword overlap between the research "
                    "question, extracted claim, and source title."
                )
            })

            print(
                f"[Citation Checker] "
                f"{status} ({score:.2f}) - {source}"
            )

        verified.append({
            "question": question,
            "findings": verified_findings
        })

    return verified