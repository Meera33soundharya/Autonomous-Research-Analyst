import re


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text: str) -> str:
    """Clean scraped webpage text without changing normal words."""

    if not text:
        return ""

    # --------------------------------------------------------
    # Remove Markdown images
    # --------------------------------------------------------

    text = re.sub(
        r'!\[\[.*?\]\]',
        ' ',
        text,
        flags=re.DOTALL
    )

    text = re.sub(
        r'!\[.*?\]\(.*?\)',
        ' ',
        text,
        flags=re.DOTALL
    )

    # --------------------------------------------------------
    # Convert Markdown links to visible text
    # Example:
    # [Quantum Computing](https://example.com)
    # becomes:
    # Quantum Computing
    # --------------------------------------------------------

    text = re.sub(
        r'\[([^\]]+)\]\([^)]+\)',
        r'\1',
        text
    )

    # --------------------------------------------------------
    # Remove URLs
    # --------------------------------------------------------

    text = re.sub(
        r'https?://\S+',
        ' ',
        text,
        flags=re.IGNORECASE
    )

    # --------------------------------------------------------
    # Remove broken URL/reference fragments
    # --------------------------------------------------------

    text = re.sub(
        r'\b[\w-]+/\d+-\d+/fulltext\)?',
        ' ',
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r'\b\d{3,}-\d+/fulltext\)?',
        ' ',
        text,
        flags=re.IGNORECASE
    )

    # --------------------------------------------------------
    # Remove Markdown headings
    # --------------------------------------------------------

    text = re.sub(
        r'#{1,6}\s*',
        ' ',
        text
    )

    # --------------------------------------------------------
    # Remove common webpage noise
    # --------------------------------------------------------

    noise_patterns = [
        r'Featured Image',
        r'Quote Icon',
        r'Company Logo',
        r'Globe Newswire',
        r'Key takeaways',
        r'Read more',
        r'\d+\s*min read',
        r'In Conclusion',
        r'Cookie Policy',
        r'Privacy Policy',
        r'Terms of Use',
        r'Subscribe',
        r'Sign Up',
        r'Login',
    ]

    for pattern in noise_patterns:
        text = re.sub(
            pattern,
            ' ',
            text,
            flags=re.IGNORECASE
        )

    # --------------------------------------------------------
    # Fix only known scraping errors
    # --------------------------------------------------------

    replacements = {
        "of fer": "offer",
        "of ten": "often",
        "the mselves": "themselves",
        "the ir": "their",
        "canbe": "can be",
        "anddeployment": "and deployment",
        "poweredby": "powered by",
        "real-timemonitoring": "real-time monitoring",
        "waysto": "ways to",
        "issuesof": "issues of",
        "essentialto": "essential to",
        "systemis": "system is",
        "the y": "they",
        "hasbeen": "has been",
        "privacyand": "privacy and",
        "legaland": "legal and",
        "therole": "the role",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # --------------------------------------------------------
    # Remove section numbering
    # --------------------------------------------------------

    text = re.sub(
        r'\b\d+\.\d+\b',
        ' ',
        text
    )

    # --------------------------------------------------------
    # Remove square brackets
    # --------------------------------------------------------

    text = re.sub(
        r'[\[\]]',
        ' ',
        text
    )

    # --------------------------------------------------------
    # Remove repeated punctuation
    # --------------------------------------------------------

    text = re.sub(
        r'\.{2,}',
        '.',
        text
    )

    text = re.sub(
        r',{2,}',
        ',',
        text
    )

    # --------------------------------------------------------
    # Normalize whitespace
    # --------------------------------------------------------

    text = re.sub(
        r'\s+',
        ' ',
        text
    )

    return text.strip(" -:;,.()")


# ============================================================
# SENTENCE VALIDATION
# ============================================================

def is_valid_sentence(sentence: str) -> bool:
    """Check whether a sentence looks like useful evidence."""

    sentence = sentence.strip()

    # Minimum character length
    if len(sentence) < 60:
        return False

    # Minimum number of words
    words = re.findall(
        r"[A-Za-z]{3,}",
        sentence
    )

    if len(words) < 10:
        return False

    lower = sentence.lower()

    # --------------------------------------------------------
    # Reject common webpage noise
    # --------------------------------------------------------

    noise = [
        "company logo",
        "featured image",
        "globe newswire",
        "min read",
        "read more",
        "sign up",
        "subscribe",
        "cookie policy",
        "privacy policy",
        "terms of use",
    ]

    if any(item in lower for item in noise):
        return False

    # --------------------------------------------------------
    # Reject broken references
    # --------------------------------------------------------

    if re.search(
        r'\d{3,}-\d+/fulltext',
        lower
    ):
        return False

    # --------------------------------------------------------
    # Reject URLs
    # --------------------------------------------------------

    if "http://" in lower or "https://" in lower:
        return False

    # --------------------------------------------------------
    # Reject incomplete sentence endings
    # --------------------------------------------------------

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
        "such as",
        "including",
        "based on",
        "according to",
    )

    if lower.endswith(bad_endings):
        return False

    # --------------------------------------------------------
    # Reject scraped headings
    # --------------------------------------------------------

    bad_starts = (
        "edit ",
        "applications:",
        "applications ",
        "key takeaways",
        "introduction:",
        "conclusion:",
        "table of contents",
        "contents:",
    )

    if lower.startswith(bad_starts):
        return False

    # --------------------------------------------------------
    # Reject sentences with excessive symbols
    # --------------------------------------------------------

    symbol_count = len(
        re.findall(
            r'[+|=\[\]{}]',
            sentence
        )
    )

    if symbol_count >= 4:
        return False

    return True


# ============================================================
# RELEVANCE EXTRACTION
# ============================================================

def extract_relevant_sentences(
    question: str,
    content: str,
    max_sentences: int = 2
) -> str:
    """
    Extract sentences that are relevant to the current
    research question.
    """

    cleaned = clean_text(content)

    if not cleaned:
        return ""

    # --------------------------------------------------------
    # Extract meaningful words from question
    # --------------------------------------------------------

    question_words = set(
        re.findall(
            r"[a-zA-Z]{4,}",
            question.lower()
        )
    )

    # --------------------------------------------------------
    # Remove generic question words
    # --------------------------------------------------------

    generic_words = {
        "what",
        "what's",
        "how",
        "when",
        "where",
        "which",
        "why",
        "does",
        "major",
        "main",
        "used",
        "using",
        "about",
        "from",
        "with",
        "into",
        "than",
        "that",
        "this",
        "these",
        "those",
        "their",
        "there",
        "across",
        "current",
        "likely",
        "practical",
        "technical",
        "key",
    }

    question_words -= generic_words

    if not question_words:
        return ""

    # --------------------------------------------------------
    # Split text into sentences
    # --------------------------------------------------------

    sentences = re.split(
        r'(?<=[.!?])\s+',
        cleaned
    )

    scored_sentences = []

    # --------------------------------------------------------
    # Score every sentence
    # --------------------------------------------------------

    for sentence in sentences:

        sentence = sentence.strip()

        if not is_valid_sentence(sentence):
            continue

        sentence_words = set(
            re.findall(
                r"[a-zA-Z]{4,}",
                sentence.lower()
            )
        )

        # Count matching research-question terms
        overlap = len(
            question_words.intersection(
                sentence_words
            )
        )

        # Ignore completely unrelated sentences
        if overlap == 0:
            continue

        # Higher overlap = higher relevance
        score = overlap * 3

        # Prefer medium-length evidence
        length_penalty = (
            abs(len(sentence) - 220) / 1000
        )

        score -= length_penalty

        scored_sentences.append(
            (
                score,
                sentence
            )
        )

    # --------------------------------------------------------
    # Sort by relevance
    # --------------------------------------------------------

    scored_sentences.sort(
        key=lambda item: item[0],
        reverse=True
    )

    selected = []

    # --------------------------------------------------------
    # Select unique sentences
    # --------------------------------------------------------

    for score, sentence in scored_sentences:

        duplicate = any(
            sentence.lower() in existing.lower()
            or existing.lower() in sentence.lower()
            for existing in selected
        )

        if duplicate:
            continue

        selected.append(sentence)

        if len(selected) >= max_sentences:
            break

    if not selected:
        return ""

    # --------------------------------------------------------
    # Combine selected evidence
    # --------------------------------------------------------

    evidence = " ".join(selected)

    # --------------------------------------------------------
    # Limit evidence size
    # --------------------------------------------------------

    if len(evidence) > 900:

        evidence = evidence[:900]

        last_period = evidence.rfind(".")

        if last_period > 300:
            evidence = evidence[
                :last_period + 1
            ]

    return evidence.strip()


# ============================================================
# RESEARCHER AGENT
# ============================================================

def analyze_sources(
    question: str,
    sources: list[dict]
) -> dict:
    """
    Analyze sources belonging to one research question.
    """

    # --------------------------------------------------------
    # Select sources belonging to this question
    # --------------------------------------------------------

    matching_sources = [
        source
        for source in sources
        if source.get("question") == question
    ]

    findings = []

    # --------------------------------------------------------
    # Extract evidence from each source
    # --------------------------------------------------------

    for source in matching_sources:

        content = source.get(
            "content",
            ""
        )

        evidence = extract_relevant_sentences(
            question,
            content
        )

        if not evidence:
            continue

        findings.append({
            "claim": evidence,
            "source_title": source.get(
                "title",
                ""
            ),
            "source_url": source.get(
                "url",
                ""
            )
        })

        # Maximum 5 findings per question
        if len(findings) >= 5:
            break

    # --------------------------------------------------------
    # Return structured research evidence
    # --------------------------------------------------------

    return {
        "question": question,
        "findings": findings
    }