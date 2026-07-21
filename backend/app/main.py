"""
CEFR Coach — FastAPI backend
=============================

Endpoints:
    POST /classify          → single text → CEFR level + confidence
    POST /classify/session  → adds to rolling window → smoothed level
    POST /retrieve          → RAG retrieval for a learner level + query
    POST /rag/build         → (re)build ChromaDB index
    DELETE /session/{id}    → reset rolling window

D4 (adaptive tutor):
    POST /exercise          → RAG + Groq/LLM exercise generation
    POST /feedback          → LLM feedback on learner answer
    POST /chat              → i+1 conversation turn
    GET  /session/{id}      → learner adaptive-loop state
    DELETE /session/{id}/reset → full adaptive-loop reset
"""

import asyncio
import os
import time
from contextlib import asynccontextmanager
from uuid import uuid4

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models.schemas import (
    ClassifyRequest, ClassifyResponse, HealthResponse,
    RetrieveRequest, RetrieveResponse,
    ExerciseRequest, FeedbackRequest, ChatRequest, SessionStateResponse,
)
from app.services.level_service import classify, LearnerLevelTracker, HF_SPACE as HF_REPO
from app.services.rag_service import retrieve, build_index, _adjacent_levels
from app.services.tutor_service import generate_exercise, give_feedback, conversation_turn
from app.services.adaptive_loop import get_session, reset_session as _reset_adaptive_session
from app.observability import trace_classify

# ── HF Space keep-alive ───────────────────────────────────────────────────────
# HF free Spaces sleep after ~30 min. We ping every 25 min to keep it awake.

_HF_SPACE_URL = "https://" + HF_REPO.replace("/", "-") + ".hf.space"

async def _keepalive_loop():
    await asyncio.sleep(10)  # let startup finish first
    async with httpx.AsyncClient(timeout=15) as client:
        while True:
            try:
                await client.get(_HF_SPACE_URL)
                print(f"[keepalive] pinged {_HF_SPACE_URL}")
            except Exception as e:
                print(f"[keepalive] ping failed: {e}")
            await asyncio.sleep(25 * 60)  # 25 minutes


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(_keepalive_loop())
    yield


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="CEFR Coach API",
    description="Adaptive English tutor powered by a fine-tuned CEFR classifier + GPT-5.6.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

START_TIME = time.time()

# In-process session store (keyed by session_id → LearnerLevelTracker).
# Replace with Redis for multi-worker deployments.
_sessions: dict[str, LearnerLevelTracker] = {}


def _get_tracker(session_id: str) -> LearnerLevelTracker:
    if session_id not in _sessions:
        _sessions[session_id] = LearnerLevelTracker()
    return _sessions[session_id]


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "name":      "CEFR Coach API",
        "version":   "0.1.0",
        "model":     HF_REPO,
        "levels":    ["A1", "A2", "B1", "B2", "C1", "C2"],
        "endpoints": {
            "classify":         "POST /classify",
            "classify_session": "POST /classify/session",
            "health":           "GET /health",
            "docs":             "/docs",
        },
    }


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        model=HF_REPO,
        device="hf-space",
        uptime_s=round(time.time() - START_TIME, 1),
    )


@app.post("/classify", response_model=ClassifyResponse)
def classify_endpoint(request: ClassifyRequest):
    """
    Classify a single text. Does NOT update any rolling window.
    Use this for one-shot queries (e.g. the assessment UI).
    """
    result = classify(request.text)

    if request.session_id:
        trace_classify(request.session_id, request.text, result)

    if result.get("error"):
        # Validation error (word count) — return 422 with the message
        raise HTTPException(status_code=422, detail=result["error"])

    return ClassifyResponse(**result)


@app.post("/classify/session", response_model=ClassifyResponse)
def classify_session_endpoint(request: ClassifyRequest):
    """
    Classify text AND add the result to the rolling window for this session.
    Returns both the raw classification and the smoothed level.
    If session_id is omitted, one is created and returned in the response.

    Also feeds the adaptive-loop LearnerSession so that /session/{id},
    /exercise, /feedback, and /chat all share the same session state.
    """
    session_id = request.session_id or str(uuid4())

    result = classify(request.text)

    if result.get("error"):
        raise HTTPException(status_code=422, detail=result["error"])

    # Feed adaptive-loop session (unified store)
    adaptive_session = get_session(session_id)
    adaptive_session.tracker.add(result)
    smoothed = adaptive_session.tracker.smoothed_level()

    if not smoothed["needs_more_data"] and adaptive_session.level is None:
        from app.services.adaptive_loop import State
        adaptive_session.level = smoothed["level"]
        adaptive_session.state = State.PRACTICE

    trace_classify(session_id, request.text, {**result, "smoothed": smoothed})

    return ClassifyResponse(
        **result,
        smoothed={**smoothed, "session_id": session_id},
    )


@app.post("/retrieve", response_model=RetrieveResponse)
def retrieve_endpoint(request: RetrieveRequest):
    """
    Retrieve pedagogical chunks for a learner level + query.
    Metadata pre-filter ensures content never exceeds learner_level + 1.
    Chunk IDs are returned so GPT-5.6 can cite them in exercise generation.
    """
    try:
        chunks = retrieve(
            level=request.level,
            query=request.query,
            skill=request.skill,
            top_k=request.top_k,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return RetrieveResponse(
        level=request.level,
        adjacent_levels=_adjacent_levels(request.level),
        query=request.query,
        chunks=chunks,
    )


@app.post("/rag/build")
def build_index_endpoint(force: bool = False):
    """Build or rebuild the ChromaDB index from the corpus YAML files."""
    try:
        n = build_index(force=force)
        return {"status": "ok", "chunks_indexed": n}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/session/{session_id}")
def reset_session_endpoint(session_id: str):
    """Reset a learner session (clear rolling window)."""
    if session_id in _sessions:
        _sessions[session_id].reset()
    return {"session_id": session_id, "status": "reset"}


# ── D4: Adaptive tutor endpoints ──────────────────────────────────────────────

@app.get("/session/{session_id}", response_model=SessionStateResponse)
def get_session_state(session_id: str):
    """Return the current adaptive-loop state for a learner session."""
    session = get_session(session_id)
    return SessionStateResponse(**session.to_dict())


@app.delete("/session/{session_id}/reset")
def full_reset_session(session_id: str):
    """Full reset: clears adaptive-loop state (level, exercises, streak)."""
    _reset_adaptive_session(session_id)
    if session_id in _sessions:
        del _sessions[session_id]
    return {"session_id": session_id, "status": "full_reset"}


@app.post("/exercise")
def exercise_endpoint(request: ExerciseRequest):
    """
    Generate a CEFR-calibrated exercise for a learner session.

    Flow:
      1. Get learner level from adaptive-loop session (must be in PRACTICE state).
      2. RAG retrieve relevant chunks for the skill gap.
      3. LLM generate exercise grounded in those chunks.
      4. Transition session to EVALUATE state.
    """
    session = get_session(request.session_id)

    if session.level is None:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "level_not_established",
                "message": "Submit at least 2 writing samples via POST /classify/session first.",
                "state": session.state,
            },
        )

    # RAG retrieval
    try:
        chunks = retrieve(
            level=session.level,
            query=request.skill_gap,
            skill=request.skill,
            top_k=request.top_k,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG error: {e}")

    # LLM exercise generation
    try:
        exercise = generate_exercise(
            level=session.level,
            skill_gap=request.skill_gap,
            chunks=chunks,  # already plain dicts from rag_service.retrieve()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {e}")

    # Transition state
    session.start_exercise(exercise, skill_focus=request.skill_gap)

    return {
        "session_id": request.session_id,
        "level":      session.level,
        "exercise":   exercise,
        "chunks_used": len(chunks),
        "state":      session.state,
    }


@app.post("/feedback")
def feedback_endpoint(request: FeedbackRequest):
    """
    Evaluate a learner's answer to the current exercise.

    Flow:
      1. Get session + current exercise.
      2. LLM give_feedback (structured JSON).
      3. Optionally classify the answer text (if ≥20 words).
      4. Transition to ADJUST, then auto-adjust level.
    """
    session = get_session(request.session_id)

    if session.current_exercise is None:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "no_active_exercise",
                "message": "Generate an exercise first via POST /exercise.",
                "state": session.state,
            },
        )
    if session.level is None:
        raise HTTPException(status_code=400, detail="Level not established.")

    # LLM feedback
    try:
        feedback = give_feedback(
            learner_answer=request.learner_answer,
            exercise=session.current_exercise,
            level=session.level,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {e}")

    # Submit answer → ADJUST state
    answer_result = session.submit_answer(feedback, request.learner_answer)

    # Auto-adjust level
    adjust_result = session.adjust_level()

    return {
        "session_id":    request.session_id,
        "feedback":      feedback,
        "streak":        answer_result["streak"],
        "classified":    answer_result["classified"],
        "level":         adjust_result["level"],
        "level_changed": adjust_result["level_changed"],
        "harder":        adjust_result["harder"],
        "state":         session.state,
    }


@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    """
    Conversation turn written at i+1 level (Krashen's comprehensible input).
    Maintains conversation history in the adaptive-loop session.
    """
    session = get_session(request.session_id)
    level   = session.level or "B1"  # default if not yet assessed

    # Append user message to history
    session.history.append({"role": "user", "content": request.message})

    try:
        reply = conversation_turn(history=session.history, level=level)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {e}")

    # Append assistant reply to history
    session.history.append({"role": "assistant", "content": reply})

    return {
        "session_id": request.session_id,
        "level":      level,
        "reply":      reply,
        "turns":      len(session.history) // 2,
    }
