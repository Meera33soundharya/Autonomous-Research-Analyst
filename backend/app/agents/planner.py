from app.services.llm_service import ask_llm


def create_research_plan(topic: str) -> list[str]:

    topic = topic.strip()

    if not topic:
        return []

    prompt = f"""
You are an autonomous research planning agent.

CURRENT USER RESEARCH TOPIC:
{topic}

IMPORTANT RULES:
- Create questions ONLY about the CURRENT USER RESEARCH TOPIC above.
- Every question must explicitly relate to the current topic.
- Do NOT use questions from previous research.
- Do NOT assume the topic is healthcare, artificial intelligence,
  cybersecurity, IoT, or any other topic unless it appears in the
  CURRENT USER RESEARCH TOPIC.
- Generate exactly 5 research questions.
- Do not answer the questions.
- Return ONLY the 5 numbered questions.

The questions must cover:

1. Major applications or uses of the current topic
2. Benefits, effectiveness, or impact of the current topic
3. Risks, limitations, or challenges of the current topic
4. Adoption, implementation, or practical challenges
5. Future developments, opportunities, standards, or regulation

Required format:

1. question
2. question
3. question
4. question
5. question
"""

    response = ask_llm(prompt)

    questions = []

    for line in response.splitlines():

        line = line.strip()

        if not line:
            continue

        question = None

        # Supports:
        # 1. question
        # 1) question
        # 1 question

        if len(line) >= 3 and line[0].isdigit():

            if line[1] == ".":
                question = line[2:].strip()

            elif line[1] == ")":
                question = line[2:].strip()

            elif line[1] == " ":
                question = line[2:].strip()

        if question and "?" in question:
            questions.append(question)

    return questions[:5]