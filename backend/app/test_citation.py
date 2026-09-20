from app.agents.citation_checker import check_citations


evidence = """
Claim: AI is used for diagnostic imaging.

Source: Cleveland Clinic
URL: https://example.com

Evidence: AI systems can assist clinicians in analyzing medical images
and identifying potential abnormalities.
"""

result = check_citations(evidence)

print("\n===== CITATION VERIFICATION =====\n")
print(result)