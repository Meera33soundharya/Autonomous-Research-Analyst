import re


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_evidence_text(text: str) -> str:

    if not text:
        return ""

    # Normalize Unicode dashes
    text = text.replace("-", "-")
    text = text.replace("–", "-")
    text = text.replace("—", "-")

    # Fix common joined words
    replacements = {
        "ArtificialIntelligence": "Artificial Intelligence",
        "artificialintelligence": "artificial intelligence",

        "healthcareAI": "healthcare AI",
        "AItechnologies": "AI technologies",

        "medicalinformation": "medical information",
        "medicalimaging": "medical imaging",
        "medicaldevice": "medical device",

        "healthcareorganizations": "healthcare organizations",
        "healthcareinstitutions": "healthcare institutions",
        "healthcaresystems": "healthcare systems",
        "healthcareproviders": "healthcare providers",

        "patientcare": "patient care",
        "patientmonitoring": "patient monitoring",
        "patientoutcomes": "patient outcomes",
        "patientprivacy": "patient privacy",
        "patientrecords": "patient records",
        "patientpopulations": "patient populations",

        "clinicaldecision": "clinical decision",
        "clinicalpractice": "clinical practice",
        "clinicalsettings": "clinical settings",

        "drugdiscovery": "drug discovery",
        "treatmentplanning": "treatment planning",
        "treatmentapproaches": "treatment approaches",
        "diagnosticmethods": "diagnostic methods",
        "diagnostictools": "diagnostic tools",
        "diseaseareas": "disease areas",

        "regulatoryframeworks": "regulatory frameworks",
        "ethicalframeworks": "ethical frameworks",
        "technicaladoption": "technical adoption",
        "implementationchallenges": "implementation challenges",

        "dataquality": "data quality",
        "dataprivacy": "data privacy",
        "safetyrisks": "safety risks",
        "safeeffective": "safe effective",
        "safeethical": "safe ethical",

        "workforcechallenges": "workforce challenges",
        "financialconstraints": "financial constraints",
        "trustissues": "trust issues",

        "integrationwith": "integration with",
        "internationalcollaboration": "international collaboration",

        "sourcecontent": "source content",
        "theevidence": "the evidence",
        "Theautonomous": "The autonomous",

        "barriershave": "barriers have",
        "barriersaffect": "barriers affect",
        "promiseto": "promise to",
        "guidanceon": "guidance on",
        "eighteenmonths": "eighteen months",
        "equitableuse": "equitable use",
        "developmentin": "development in",
        "ethicalcompliance": "ethical compliance",
        "adoptionof": "adoption of",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Fix joined AI expressions
    text = re.sub(
        r"(?i)\bofAI\b",
        "of AI",
        text
    )

    text = re.sub(
        r"(?i)\bwithAI\b",
        "with AI",
        text
    )

    text = re.sub(
        r"(?i)\bandAI\b",
        "and AI",
        text
    )

    # Remove common webpage headings
    heading_patterns = [
        r"\bWHAT WE COVER\b",
        r"\bKEY TAKEAWAYS\b",
        r"\bQUICK ANSWER\b",
        r"\bBEST PRACTICES\b",
        r"\bFREQUENTLY ASKED QUESTIONS\b",
        r"\bFAQ\b",
        r"\bBOTTOM LINE\b",
        r"\bCONCLUSION\b",
        r"\bOVERVIEW\b",
        r"\bTITLE:\b",
        r"\bKEYWORDS:\b",
        r"\bCITATION:\b",
    ]

    for pattern in heading_patterns:
        text = re.sub(
            pattern,
            " ",
            text,
            flags=re.IGNORECASE
        )

    # Remove common webpage noise
    noise_phrases = [
        "Manage Subscriptions",
        "Featured Image",
        "Company Logo",
        "Globe Newswire",
        "Read more",
        "Sign up",
        "Subscribe",
        "Cookie Policy",
        "Privacy Policy",
        "Terms of Use",
        "Advertisement",
        "Newsletter",
        "Claim Your Free Demo",
        "Let’s Make It Happen",
    ]

    for phrase in noise_phrases:
        text = re.sub(
            re.escape(phrase),
            " ",
            text,
            flags=re.IGNORECASE
        )

    # Remove obvious bullet-list markers
    text = re.sub(
        r"[•●▪◦]",
        ". ",
        text
    )

    # Remove malformed percentage fragments
    text = re.sub(
        r"\b(?:was|were|is|are|of)\s+%",
        " ",
        text,
        flags=re.IGNORECASE
    )

    # Remove broken citations
    text = re.sub(
        r"\([^)]*\bet al\.\s*$",
        " ",
        text,
        flags=re.IGNORECASE
    )

    # Normalize punctuation spacing
    text = re.sub(
        r"\s+([,.!?;:])",
        r"\1",
        text
    )

    text = re.sub(
        r"([,.!?;:])([A-Za-z])",
        r"\1 \2",
        text
    )

    # Fix lowercase + uppercase joined words
    text = re.sub(
        r"([a-z])([A-Z][a-z]+)",
        r"\1 \2",
        text
    )

    # Normalize whitespace
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# LOW QUALITY CHECK
# ============================================================

def is_low_quality_evidence(text: str) -> bool:

    if not text:
        return True

    text = text.strip()
    lower = text.lower()

    # Too short
    if len(text) < 80:
        return True

    if len(text.split()) < 12:
        return True

    # Webpage noise
    bad_patterns = [
        "manage subscriptions",
        "company logo",
        "featured image",
        "globe newswire",
        "read more",
        "sign up",
        "subscribe",
        "cookie policy",
        "privacy policy",
        "terms of use",
        "advertisement",
        "newsletter",
        "claim your free demo",
        "let’s make it happen",
        "keywords:",
        "citation:",
        "title:",
        "quick answer",
        "best practices",
        "frequently asked questions",
        "faq",
        "bottom line",
        "what we cover",
    ]

    for pattern in bad_patterns:
        if pattern in lower:
            return True

    # URL
    if "http://" in lower or "https://" in lower:
        return True

    # Broken reference
    if re.search(
        r"\d{3,}-\d+/fulltext",
        lower
    ):
        return True

    # Broken percentage
    if re.search(
        r"\b(?:was|were|is|are|of)\s+%",
        lower
    ):
        return True

    # Broken citation
    if "et al _." in lower:
        return True

    if re.search(
        r"\bet al\.\s*$",
        lower
    ):
        return True

    # Incomplete ending
    incomplete_endings = (
        "including",
        "such as",
        "because",
        "although",
        "however",
        "and",
        "or",
        "with",
        "from",
        "to",
        "of",
        "for",
        "between",
        "among",
    )

    stripped = text.rstrip(" .,:;")

    if stripped.lower().endswith(incomplete_endings):
        return True

    # Broken parentheses
    if text.count("(") != text.count(")"):
        return True

    # Excessive numbers
    number_count = len(
        re.findall(
            r"\b\d+(?:\.\d+)?\b",
            text
        )
    )

    if number_count >= 8:
        return True

    return False


# ============================================================
# CLEAN EVIDENCE
# ============================================================

def clean_evidence(
    evidence: list[dict]
) -> list[dict]:

    cleaned_evidence = []

    for item in evidence:

        cleaned_findings = []

        for finding in item.get(
            "findings",
            []
        ):

            claim = clean_evidence_text(
                finding.get(
                    "claim",
                    ""
                )
            )

            if is_low_quality_evidence(
                claim
            ):
                continue

            cleaned_finding = dict(
                finding
            )

            cleaned_finding["claim"] = claim

            cleaned_findings.append(
                cleaned_finding
            )

        cleaned_item = dict(item)

        cleaned_item["findings"] = (
            cleaned_findings
        )

        cleaned_evidence.append(
            cleaned_item
        )

    return cleaned_evidence