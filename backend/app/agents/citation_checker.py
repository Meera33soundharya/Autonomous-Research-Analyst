import re


STOP_WORDS = {
    "this", "that", "with", "from", "which", "their", "there",
    "these", "those", "about", "have", "been", "were", "will",
    "into", "using", "used", "such", "more", "than", "also",
    "they", "what", "does", "how", "main", "major", "some",
    "many", "very", "most", "much", "other", "where", "when",
    "topic", "research", "according", "following", "could",
    "would", "should", "might", "among", "between"
}


def normalize_text(text: str) -> list[str]:
    if not text:
        return []

    words = re.findall(
        r"[a-zA-Z]{4,}",
        text.lower()
    )

    return [
        word
        for word in words
        if word not in STOP_WORDS
    ]


def calculate_overlap(
    claim: str,
    source_content: str
) -> float:

    claim_words = set(
        normalize_text(claim)
    )

    source_words = set(
        normalize_text(source_content)
    )

    if not claim_words or not source_words:
        return 0.0

    common_words = (
        claim_words.intersection(
            source_words
        )
    )

    return (
        len(common_words)
        / len(claim_words)
    )


def validate_source_url(url: str) -> bool:

    if not url:
        return False

    url = url.strip().lower()

    return (
        url.startswith("https://")
        or url.startswith("http://")
    )


def has_malformed_spacing(text: str) -> bool:
    """
    Detect words accidentally joined together by webpage extraction.
    """

    if not text:
        return False

    patterns = [
        r"[a-z]{3,}(?:patient|outcomes|healthcare|medical|"
        r"artificial|intelligence|regulatory|framework|"
        r"implementation|effectiveness|algorithm|system|"
        r"data|privacy|security)[a-z]{2,}",

        r"\b(?:improve|increase|reduce|enhance|enable|"
        r"support|provide|develop|create|use|using)"
        r"(?:patient|patients|healthcare|medical|clinical|"
        r"outcomes|costs|effectiveness|accuracy)",

        r"\b(?:the|of|in|for|with|to|and|or|from)"
        r"(?:use|role|impact|implementation|adoption|"
        r"effectiveness|framework|regulation|system|data)",
    ]

    for pattern in patterns:

        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        ):
            return True

    # General detection:
    # lowercase letter immediately followed by a long word
    joined_word_count = len(
        re.findall(
            r"\b[a-z]{3,}(?:[A-Z][a-z]{2,})",
            text
        )
    )

    return joined_word_count >= 2


def has_incomplete_ending(text: str) -> bool:

    if not text:
        return True

    lower = text.strip().lower()

    bad_endings = (
        "with",
        "and",
        "or",
        "the",
        "to",
        "of",
        "for",
        "from",
        "by",
        "than",
        "as",
        "such as",
        "including",
        "based on",
        "according to",
        "however",
        "although",
        "because",
        "while",
        "that",
        "which",
        "where",
        "when",
        "through",
        "via",
        "into",
        "between",
        "among",
        "without",
        "within",
        "despite",
        "case",
        "implementation",
        "clinical",
        "outcomes",
        "warranting",
        "streamlining",
    )

    return lower.endswith(
        bad_endings
    )


def has_broken_citation(text: str) -> bool:

    if not text:
        return True

    lower = text.lower()

    # Example:
    # "(Bajwa et al."
    if re.search(
        r"\([a-zA-Z]+\s+et al\.\s*$",
        lower
    ):
        return True

    # Example:
    # "Bajwa et al."
    if re.search(
        r"\bet al\.\s*$",
        lower
    ):
        return True

    # Unbalanced parentheses
    if text.count("(") != text.count(")"):
        return True

    # Unbalanced quotation marks
    if text.count('"') % 2 != 0:
        return True

    return False


def contains_table_or_chart_reference(
    text: str
) -> bool:

    if not text:
        return False

    return bool(
        re.search(
            r"\b(?:table|figure|fig\.|chart)"
            r"\s*\d+[a-z]?\b",
            text,
            flags=re.IGNORECASE
        )
    )


def validate_claim(
    claim: str
) -> tuple[bool, str]:

    if not claim:
        return False, "Claim is empty."

    claim = claim.strip()

    # ---------------------------------------------------------
    # Length
    # ---------------------------------------------------------

    if len(claim) < 80:
        return False, "Claim is too short."

    words = re.findall(
        r"[A-Za-z]{3,}",
        claim
    )

    if len(words) < 12:
        return False, "Claim contains too few words."

    lower = claim.lower()

    # ---------------------------------------------------------
    # Webpage noise
    # ---------------------------------------------------------

    noise_patterns = [
        "company logo",
        "featured image",
        "globe newswire",
        "read more",
        "sign up",
        "subscribe",
        "cookie policy",
        "privacy policy",
        "terms of use",
        "login",
        "navigation",
        "key takeaways",
        "min read",
        "advertisement",
        "newsletter",
    ]

    for pattern in noise_patterns:

        if pattern in lower:

            return (
                False,
                "Claim contains webpage noise."
            )

    # ---------------------------------------------------------
    # URLs
    # ---------------------------------------------------------

    if (
        "http://" in lower
        or "https://" in lower
    ):
        return (
            False,
            "Claim contains a URL."
        )

    # ---------------------------------------------------------
    # Broken references
    # ---------------------------------------------------------

    if re.search(
        r"\d{3,}-\d+/fulltext",
        lower
    ):
        return (
            False,
            "Claim contains broken reference text."
        )

    # ---------------------------------------------------------
    # Table / figure / chart
    # ---------------------------------------------------------

    if contains_table_or_chart_reference(
        claim
    ):
        return (
            False,
            "Claim contains table or chart reference."
        )

    # ---------------------------------------------------------
    # Broken citation
    # ---------------------------------------------------------

    if has_broken_citation(
        claim
    ):
        return (
            False,
            "Claim contains an incomplete citation."
        )

    # ---------------------------------------------------------
    # Incomplete ending
    # ---------------------------------------------------------

    if has_incomplete_ending(
        claim
    ):
        return (
            False,
            "Claim appears to end before the sentence is complete."
        )

    # ---------------------------------------------------------
    # Malformed spacing
    # ---------------------------------------------------------

    if has_malformed_spacing(
        claim
    ):
        return (
            False,
            "Claim contains malformed word spacing."
        )

    # ---------------------------------------------------------
    # Chart / percentage noise
    # ---------------------------------------------------------

    percentage_count = len(
        re.findall(
            r"\b\d{1,3}\s*%",
            claim
        )
    )

    if percentage_count >= 3:
        return (
            False,
            "Claim contains chart or statistical noise."
        )

    # ---------------------------------------------------------
    # Excessive numbers
    # ---------------------------------------------------------

    number_count = len(
        re.findall(
            r"\b\d+(?:\.\d+)?\b",
            claim
        )
    )

    if number_count >= 8:
        return (
            False,
            "Claim contains excessive numerical data."
        )

    # ---------------------------------------------------------
    # Obvious chart fragments
    # ---------------------------------------------------------

    bad_fragments = [
        "top 3",
        "overall 30",
        "overall 40",
        "overall 50",
        "overall 60",
        "0 60 40 20",
        "30 10 0",
    ]

    if any(
        fragment in lower
        for fragment in bad_fragments
    ):
        return (
            False,
            "Claim contains chart text."
        )

    # ---------------------------------------------------------
    # Repeated punctuation
    # ---------------------------------------------------------

    if re.search(
        r"[!?]{3,}",
        claim
    ):
        return (
            False,
            "Claim contains malformed punctuation."
        )

    # ---------------------------------------------------------
    # Empty punctuation gaps
    # ---------------------------------------------------------

    if re.search(
        r"\s+[,.]\s*[,.]?",
        claim
    ):
        return (
            False,
            "Claim contains malformed punctuation."
        )

    return True, "Claim structure is valid."


def check_citations(
    evidence: list[dict]
) -> list[dict]:

    verified = []

    for item in evidence:

        question = item.get(
            "question",
            ""
        )

        verified_findings = []

        for finding in item.get(
            "findings",
            []
        ):

            claim = finding.get(
                "claim",
                ""
            ).strip()

            source_title = finding.get(
                "source_title",
                ""
            ).strip()

            source_url = finding.get(
                "source_url",
                ""
            ).strip()

            source_content = finding.get(
                "source_content",
                ""
            ).strip()

            # -------------------------------------------------
            # Validate claim
            # -------------------------------------------------

            claim_valid, claim_reason = (
                validate_claim(claim)
            )

            if not claim_valid:

                verified_findings.append({
                    "claim": claim,
                    "source": source_title,
                    "url": source_url,
                    "status": "UNSUPPORTED",
                    "score": 0.0,
                    "reason": claim_reason
                })

                continue

            # -------------------------------------------------
            # Validate source URL
            # -------------------------------------------------

            if not validate_source_url(
                source_url
            ):

                verified_findings.append({
                    "claim": claim,
                    "source": source_title,
                    "url": source_url,
                    "status": "UNSUPPORTED",
                    "score": 0.0,
                    "reason": (
                        "Valid source URL is missing."
                    )
                })

                continue

            # -------------------------------------------------
            # Validate source content
            # -------------------------------------------------

            if not source_content:

                verified_findings.append({
                    "claim": claim,
                    "source": source_title,
                    "url": source_url,
                    "status": "PARTIALLY_SUPPORTED",
                    "score": 0.35,
                    "reason": (
                        "Source content unavailable "
                        "for direct comparison."
                    )
                })

                continue

            # -------------------------------------------------
            # Text overlap
            # -------------------------------------------------

            overlap = calculate_overlap(
                claim,
                source_content
            )

            # -------------------------------------------------
            # Strong support
            # -------------------------------------------------

            if overlap >= 0.60:

                status = "SUPPORTED"
                score = overlap

                reason = (
                    "The claim has strong textual "
                    "support in the source."
                )

            # -------------------------------------------------
            # Partial support
            # -------------------------------------------------

            elif overlap >= 0.35:

                status = "PARTIALLY_SUPPORTED"
                score = overlap

                reason = (
                    "The claim has partial textual "
                    "support in the source."
                )

            # -------------------------------------------------
            # Unsupported
            # -------------------------------------------------

            else:

                status = "UNSUPPORTED"
                score = overlap

                reason = (
                    "The claim has insufficient "
                    "textual support."
                )

            verified_findings.append({
                "claim": claim,
                "source": source_title,
                "url": source_url,
                "status": status,
                "score": round(
                    score,
                    2
                ),
                "reason": reason
            })

        verified.append({
            "question": question,
            "findings": verified_findings
        })

    return verified