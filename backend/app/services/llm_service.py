import os

from dotenv import load_dotenv
from openai import OpenAI


# Load .env
load_dotenv()


# ============================================================
# OPENROUTER CONFIGURATION
# ============================================================

api_key = os.getenv(
    "OPENROUTER_API_KEY"
)

model = os.getenv(
    "OPENROUTER_MODEL",
    "openai/gpt-oss-20b:free"
)


if not api_key:
    raise RuntimeError(
        "OPENROUTER_API_KEY is not set in .env"
    )


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)


# ============================================================
# LLM SERVICE
# ============================================================

def ask_llm(prompt: str) -> str:

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a reliable research AI agent. "
                    "Generate accurate, topic-specific research "
                    "content. Follow the requested format exactly. "
                    "Do not invent sources or facts."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    content = response.choices[0].message.content

    if not content:
        return "No response generated."

    return content.strip()