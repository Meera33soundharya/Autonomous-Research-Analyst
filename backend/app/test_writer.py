from app.agents.writer import generate_report


topic = "Artificial Intelligence in Healthcare"

verified_evidence = """
Claim: AI is used for diagnostic imaging.

Status: SUPPORTED

Evidence:
AI systems can assist clinicians in analyzing medical images
and identifying potential abnormalities.

Source:
Cleveland Clinic
https://example.com
"""

report = generate_report(topic, verified_evidence)

print("\n===== FINAL RESEARCH REPORT =====\n")
print(report)