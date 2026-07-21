"""
Tutor Service — LLM exercise generation, feedback, and conversation.

Provider swap (2 lines to change for final submission):
  Dev  → Groq + llama-3.3-70b-versatile  (free, fast)
  Prod → OpenAI + gpt-4o or gpt-5.6      (change LLM_BASE_URL + LLM_MODEL)

Three functions:
  generate_exercise(level, skill_gap, chunks) → Exercise
  give_feedback(answer, exercise, level)       → Feedback
  conversation_turn(history, level)            → str (reply at i+1 level)

Architecture rule: this service TEACHES only.
Level decisions are made by the classifier (level_service.py), never here.
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

# ── Provider config — reads from env, falls back to Groq for local dev ────────
LLM_API_KEY  = (os.environ.get("LLM_API_KEY")
                or os.environ.get("OPENAI_API_KEY")
                or os.environ.get("GROQ_API_KEY", ""))
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.groq.com/openai/v1") or None
LLM_MODEL    = os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")

# ── Client ────────────────────────────────────────────────────────────────────

from functools import lru_cache

@lru_cache(maxsize=1)
def _client():
    from openai import OpenAI
    kwargs = {"api_key": LLM_API_KEY}
    if LLM_BASE_URL:
        kwargs["base_url"] = LLM_BASE_URL
    return OpenAI(**kwargs)


# ── Temperature policy ─────────────────────────────────────────────────────────
# generate_exercise: low temp → deterministic, structured, reliable rubric
# give_feedback:     low temp → precise grammar corrections, no hallucination
# conversation_turn: higher temp → natural, varied, engaging dialogue
TEMP_EXERCISE    = 0.3
TEMP_FEEDBACK    = 0.2
TEMP_CONVERSATION= 0.7


# ── 1. generate_exercise ──────────────────────────────────────────────────────

EXERCISE_SYSTEM = """You are an expert English language teacher who creates CEFR-calibrated exercises.
Your exercises are always grounded in the pedagogical content provided — never invent grammar rules.
Return ONLY valid JSON, no markdown, no explanation outside the JSON."""

EXERCISE_USER = """Create one English exercise for a {level} learner targeting: {skill_gap}

Use ONLY information from these pedagogical chunks (cite the chunk IDs you use):
{chunks_text}

Return this exact JSON structure:
{{
  "exercise_type": "fill_in_the_blank" | "error_correction" | "sentence_transformation" | "short_writing",
  "instruction": "Clear instruction for the learner (written at {level} level)",
  "content": "The exercise content (question, sentences, or writing prompt)",
  "expected_level": "{level}",
  "target_skill": "{skill_gap}",
  "rubric": {{
    "key_points": ["point 1", "point 2"],
    "common_errors_to_watch": ["error 1", "error 2"]
  }},
  "model_answer": "A sample correct answer",
  "chunk_ids_used": ["id1", "id2"]
}}"""


def generate_exercise(level: str, skill_gap: str, chunks: list[dict]) -> dict:
    """
    Generate a CEFR-calibrated exercise grounded in retrieved corpus chunks.
    Temperature 0.3 — deterministic, structured.
    """
    chunks_text = "\n\n---\n\n".join(
        f"[{c['id']}] {c['topic']}\n{c['content'][:600]}"
        for c in chunks
    )

    prompt = EXERCISE_USER.format(
        level=level,
        skill_gap=skill_gap,
        chunks_text=chunks_text,
    )

    response = _client().chat.completions.create(
        model=LLM_MODEL,
        temperature=TEMP_EXERCISE,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": EXERCISE_SYSTEM},
            {"role": "user",   "content": prompt},
        ],
    )

    raw = response.choices[0].message.content
    exercise = json.loads(raw)
    exercise["_model"] = LLM_MODEL
    return exercise


# ── 2. give_feedback ──────────────────────────────────────────────────────────

FEEDBACK_SYSTEM = """You are a supportive English teacher giving precise, actionable feedback.
Write your feedback at the learner's CEFR level — simple vocabulary for A2, richer for B2.
Focus on errors relevant to the exercise target. Be encouraging but honest.
Return ONLY valid JSON."""

FEEDBACK_USER = """A {level} learner answered this exercise:

EXERCISE: {exercise_instruction}
CONTENT: {exercise_content}
TARGET SKILL: {target_skill}

LEARNER'S ANSWER:
{learner_answer}

MODEL ANSWER:
{model_answer}

Return this exact JSON:
{{
  "correct": true | false,
  "score": 0-100,
  "summary": "One sentence overall assessment (written at {level} reading level)",
  "errors": [
    {{"error": "what they wrote", "correction": "what it should be", "explanation": "why (at {level} level)"}}
  ],
  "strengths": ["what they did well"],
  "next_focus": "One specific thing to practise next"
}}"""


def give_feedback(learner_answer: str, exercise: dict, level: str) -> dict:
    """
    Give structured feedback on a learner's answer.
    Temperature 0.2 — precise corrections, minimal creativity.
    """
    prompt = FEEDBACK_USER.format(
        level=level,
        exercise_instruction=exercise.get("instruction", ""),
        exercise_content=exercise.get("content", ""),
        target_skill=exercise.get("target_skill", ""),
        learner_answer=learner_answer,
        model_answer=exercise.get("model_answer", ""),
    )

    response = _client().chat.completions.create(
        model=LLM_MODEL,
        temperature=TEMP_FEEDBACK,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": FEEDBACK_SYSTEM},
            {"role": "user",   "content": prompt},
        ],
    )

    raw = response.choices[0].message.content
    feedback = json.loads(raw)
    feedback["_model"] = LLM_MODEL
    return feedback


# ── 3. conversation_turn ──────────────────────────────────────────────────────

CONVERSATION_SYSTEM = """You are a friendly English tutor having a conversation with a learner.
CRITICAL RULE: Write your replies at exactly ONE sub-level above the learner's level.
This is Krashen's i+1 principle — comprehensible input just beyond their current level.

Level guide for YOUR output (not the learner's):
  Learner A1 → You write A2: short sentences, basic vocabulary, very clear
  Learner A2 → You write B1: simple connectors, common expressions
  Learner B1 → You write B2: varied sentences, some phrasal verbs, moderate complexity
  Learner B2 → You write C1: complex sentences, precise vocabulary, discourse markers
  Learner C1/C2 → You write C2: sophisticated, nuanced, natural native-like prose

Keep replies conversational, warm, and under 80 words. Ask a follow-up question."""


def conversation_turn(history: list[dict], level: str) -> str:
    """
    Generate a tutor reply written at i+1 level (Krashen).
    history: list of {"role": "user"|"assistant", "content": "..."}
    Temperature 0.7 — natural, varied dialogue.
    """
    messages = [{"role": "system", "content": CONVERSATION_SYSTEM.replace("{level}", level)}]

    # Inject level context into the first user message if history is short
    if history and history[0]["role"] == "user":
        ctx = f"[Learner level: {level}] {history[0]['content']}"
        messages.append({"role": "user", "content": ctx})
        messages.extend(history[1:])
    else:
        messages.extend(history)

    response = _client().chat.completions.create(
        model=LLM_MODEL,
        temperature=TEMP_CONVERSATION,
        max_tokens=200,
        messages=messages,
    )

    return response.choices[0].message.content.strip()
