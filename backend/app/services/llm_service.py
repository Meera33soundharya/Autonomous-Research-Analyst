from ollama import chat


MODEL = "qwen3:8b"


def ask_llm(prompt: str) -> str:

    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a reliable research AI agent. "
                    "Follow the user's instructions exactly. "
                    "Return the requested research content."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0.2
        }
    )

    content = response["message"]["content"]

    if not content:
        return "No response generated."

    return content.strip()