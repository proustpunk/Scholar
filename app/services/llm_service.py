import json
import logging
import os

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

current_dir = os.getcwd()
file_dir = os.path.join(current_dir, "goldensets")
baseline_json = os.path.join(file_dir, "baseline.json")

print(current_dir)
print(file_dir)

#os.makedirs(file_dir, exist_ok=True)  # so writes below can never fail on missing dir

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


def compare_baseline_and_judge(baseline: dict, judge: dict, path: str) -> bool:
    fail = False
    for key in baseline:
        if key == "notes":
            continue
        try:
            if judge.get(key) < baseline[key]:
                fail = True
        except TypeError:
            pass
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"Verdict": not fail}, f, indent=4)
    return not fail


def judge_note_background(note_id: int, source_text: str, notes_content: str):
    """Fire-and-forget LaaJ pass, scheduled after the note is committed."""
    db = SessionLocal()
    score = None

    try:
        judge_prompt = JUDGE_PROMPT.format(source=source_text, notes=notes_content)
        response = retries_and_backoff_gen(judge_prompt, "low", model=JUDGE_MODEL)
        content = response.choices[0].message.content

        try:
            score = json.loads(content)
        except json.JSONDecodeError:
            score = {"error": "unparseable", "raw": content}

        db.add(JudgeResult(note_id=note_id, score=score))
        db.commit()
    except Exception as e:
        logger.error(f"Judge failed for note {note_id}: {e}", exc_info=True)
        db.close()
        return
    finally:
        db.close()

    if score is None or "error" in score:
        return

    try:
        with open(os.path.join(file_dir, f"{note_id}.json"), "w", encoding="utf-8") as f:
            json.dump(score, f, indent=2)
    except OSError as e:
        logger.error(f"Failed to write score file for note {note_id}: {e}", exc_info=True)

    try:
        with open(baseline_json, "r", encoding="utf-8-sig") as f:
            baseline = json.load(f)

            print(repr(open(baseline_json, "rb").read()))
        verdict = os.path.join(file_dir, f"{note_id}verdict.json")
        with open(verdict, 'r') as f:
            compare_baseline_and_judge(baseline, score, f)
    except FileNotFoundError:
        logger.error(f"baseline.json not found at {baseline_json} - skipping floor check for note {note_id}")
    except Exception as e:
        logger.error(f"Baseline comparison failed for note {note_id}: {e}", exc_info=True)