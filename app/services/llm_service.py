import json
import logging

from groq import Groq, GroqError
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.judge_result import JudgeResult
from app.services.eval import (
    EXTRACTION_PROMPT,
    JUDGE_PROMPT,
    choose_prompt,
    retries_and_backoff_extract,
    retries_and_backoff_gen,
)

logger = logging.getLogger(__name__)

client = Groq(api_key=settings.GROQ_API_KEY)
MIN_CHARS = 100

PRODUCTION_MODEL = "qwen/qwen3.6-27b"
JUDGE_MODEL = "openai/gpt-oss-120b"


def generate_notes(chunks: list, api_key: str) -> str:
    combined_text = "\n\n".join(chunks)
    if len(combined_text.strip()) < MIN_CHARS:
        raise ValueError("The chunk is way too less!")

    extraction_prompt = f"{EXTRACTION_PROMPT}\n\n<source_text>\n{combined_text}\n</source_text>"
    classification_response = retries_and_backoff_extract(extraction_prompt, "none")
    classification_text = classification_response.choices[0].message.content

    system_prompt = choose_prompt(classification_text)
    generation_prompt = f"{system_prompt}\n\n<source_text>\n{combined_text}\n</source_text>"
    response = retries_and_backoff_gen(generation_prompt, "none", model=PRODUCTION_MODEL)

    return response.choices[0].message.content


def judge_note_background(note_id: int, source_text: str, notes_content: str):
    """Fire-and-forget LaaJ pass, scheduled after the note is committed."""
    db = SessionLocal()
    try:
        judge_prompt = JUDGE_PROMPT.format(source=source_text, notes=notes_content)
        response = retries_and_backoff_gen(judge_prompt,"low", model=JUDGE_MODEL)
        content = response.choices[0].message.content

        try:
            score = json.loads(content)
        except json.JSONDecodeError:
            score = {"error": "unparseable", "raw": content}

        result = JudgeResult(note_id=note_id, score=score)
        db.add(result)
        db.commit()

    except Exception as e:
        logger.error(f"Judge failed for note {note_id}: {e}")
    finally:
        db.close()