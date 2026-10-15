import logging
import os
import re

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency guard
    OpenAI = None


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

client = None
if api_key and OpenAI is not None:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        timeout=45.0,
        max_retries=0,
    )


def _extract_topic(prompt: str) -> str:
    match = re.search(r"Research topic:\s*(.+)", prompt, flags=re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()

    match = re.search(r"Research question:\s*(.+)", prompt, flags=re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()

    return "the requested research topic"


def _fallback_response(prompt: str) -> str:
    topic = _extract_topic(prompt)

    if "Generate exactly 5 research questions" in prompt or "research questions" in prompt.lower():
        base = topic if topic else "the requested topic"
        questions = [
            f"What are the major applications of {base}?",
            f"How effective is {base} in real-world use cases and evidence-based settings?",
            f"What are the main risks, limitations, and ethical concerns associated with {base}?",
            f"What are the principal barriers to adoption and implementation of {base}?",
            f"What future developments and regulatory considerations are important for {base}?",
        ]
        return "\n".join(questions)

    return (
        "The model service is unavailable in this environment. "
        "A local fallback response was generated instead of a live model answer."
    )


# ============================================================
# LLM SERVICE
# ============================================================

def ask_llm(prompt: str) -> str:
    if client is None:
        logger.warning(
            "OpenRouter is not configured; returning a fallback response."
        )
        return _fallback_response(prompt)

    try:
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
            temperature=0.2,
        )

        content = response.choices[0].message.content

        if not content:
            logger.warning(
                "OpenRouter returned an empty content field (model=%s, finish_reason=%s).",
                response.model,
                response.choices[0].finish_reason,
            )
            return ""

        return content.strip()
    except Exception as error:
        status_code = getattr(error, "status_code", None)
        logger.error(
            "OpenRouter request failed (error_type=%s, status_code=%s).",
            type(error).__name__,
            status_code if isinstance(status_code, int) else "unknown",
        )
        failure = (
            f"The model service is unavailable "
            f"(OpenRouter {type(error).__name__}"
        )
        if isinstance(status_code, int):
            failure += f", HTTP {status_code}"
        return failure + ")."