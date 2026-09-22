import re


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text: str) -> str:
    """Clean scraped webpage text."""

    if not text:
        return ""

    # Remove Markdown images
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

    # Convert Markdown links to normal text
    text = re.sub(
        r'\[([^\]]+)\]\([^)]+\)',
        r'\1',
        text
    )

    # Remove URL/reference fragments
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

    # Remove Markdown headings
    text = re.sub(
        r'#{1,6}\s*',
        ' ',
        text
    )

    # Remove common webpage noise
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

    # Fix common scraping errors
    replacements = {
        "of fer": "offer",
        "of ten": "often",
        "the mselves": "themselves",
        "the ir": "their",
        "canbe": "can be",
        "anddeployment": "and deployment",
        "healthcareproviders": "healthcare providers",
        "patientcare": "patient care",
        "poweredby": "powered by",
        "drugdiscovery": "drug discovery",
        "real-timemonitoring": "real-time monitoring",
        "waysto": "ways to",
        "issuesof": "issues of",
        "essentialto": "essential to",
        "systemis": "system is",
        "safetymanagement": "safety management",
        "the y": "they",
        "iteasier": "it easier",
        "inhealthcare": "in healthcare",
        "areincredibly": "are incredibly",
        "andTreatment": "and Treatment",
        "hasbeen": "has been",
        "healthcareAI": "healthcare AI",
        "ambientAI": "ambient AI",
        "privacyand": "privacy and",
        "legaland": "legal and",
        "therole": "the role",
        "safetysystems": "safety systems",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove section numbering
    text = re.sub(
        r'\b\d+\.\d+\b',
        ' ',
        text
    )

    # Remove brackets
    text = re.sub(
        r'[\[\]]',
        ' ',
        text
    )

    # Remove repeated punctuation
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

    # Normalize spaces
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

    # Too short
    if len(sentence) < 60:
        return False

    # Too few words
    words = re.findall(
        r"[A-Za-z]{3,}",
        sentence
    )

    if len(words) < 10:
        return False

    lower = sentence.lower()

    # Webpage noise
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

    # Broken URLs
    if re.search(
        r'\d{3,}-\d+/fulltext',
        lower
    ):
        return False

    if "http://" in lower:
        return False

    if "https://" in lower:
        return False

    # Bad sentence endings
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
        "human",
        "humans",
        "such as",
        "including",
        "based on",
        "according to",
        "with .",
        "and .",
        "to .",
        "of .",
        "for .",
        "by .",
        "than .",
    )

    if lower.endswith(bad_endings):
        return False

    # Scraped headings
    bad_starts = (
        "edit ",
        "applications:",
        "applications ",
        "diagnosis and treatment applications",
        "key takeaways",
        "introduction:",
        "conclusion:",
    )

    if lower.startswith(bad_starts):
        return False

    # Broken fragments
    broken_fragments = (
        "with .",
        "and .",
        "to .",
        "of .",
        "for .",
        "human .",
        "than human",
        "warranting .",
        "implementation .",
    )

    if any(
        fragment in lower
        for fragment in broken_fragments
    ):
        return False

    # Too many symbols
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
    """Extract sentences relevant to the research question."""

    cleaned = clean_text(content)

    if not cleaned:
        return ""

    # Extract important words from question
    question_words = set(
        re.findall(
            r"[a-zA-Z]{4,}",
            question.lower()
        )
    )

    # Remove generic words
    question_words -= {
        "what",
        "what's",
        "how",
        "main",
        "major",
        "used",
        "using",
        "about",
        "from",
        "with",
        "healthcare",
        "artificial",
        "intelligence",
    }

    # Healthcare-related concepts
    healthcare_terms = {
        "diagnosis",
        "diagnostic",
        "treatment",
        "medical",
        "imaging",
        "radiology",
        "disease",
        "drug",
        "clinical",
        "patient",
        "surgery",
        "discovery",
        "monitoring",
        "prediction",
        "screening",
        "therapy",
        "hospital",
        "medicine",
        "cancer",
        "electronic",
        "records",
        "trial",
        "trials",
    }

    # Split into sentences
    sentences = re.split(
        r'(?<=[.!?])\s+',
        cleaned
    )

    scored_sentences = []

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

        # Question keyword overlap
        overlap = len(
            question_words.intersection(
                sentence_words
            )
        )

        # Healthcare concept overlap
        healthcare_overlap = len(
            healthcare_terms.intersection(
                sentence_words
            )
        )

        # Ignore completely unrelated sentences
        if overlap == 0 and healthcare_overlap == 0:
            continue

        # Calculate relevance score
        score = (
            overlap * 2
            + healthcare_overlap
        )

        # Prefer reasonable sentence length
        length_penalty = (
            abs(len(sentence) - 220)
            / 1000
        )

        score -= length_penalty

        scored_sentences.append(
            (
                score,
                sentence
            )
        )

    # Highest score first
    scored_sentences.sort(
        key=lambda x: x[0],
        reverse=True
    )

    selected = []

    for score, sentence in scored_sentences:

        # Avoid duplicate evidence
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

    evidence = " ".join(selected)

    # Maximum evidence length
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
    """Analyze sources belonging to a research question."""

    # Find sources assigned to this question
    matching_sources = [
        source
        for source in sources
        if source.get("question") == question
    ]

    findings = []

    # Analyze sources
    for source in matching_sources:

        content = source.get(
            "content",
            ""
        )

        evidence = extract_relevant_sentences(
            question,
            content
        )

        # Skip sources without useful evidence
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

        # Maximum 5 findings
        if len(findings) >= 5:
            break

    return {
        "question": question,
        "findings": findings
    }