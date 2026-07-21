from pydantic import BaseModel, Field


class ClassifyRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        example="In my opinion, social media has both advantages and disadvantages for young people today.",
    )
    session_id: str | None = Field(
        default=None,
        description="Learner session ID for rolling-window smoothing. Omit for one-shot classification.",
    )


class ClassifyResponse(BaseModel):
    level:              str | None
    confidence:         float | None
    probabilities:      dict[str, float] | None
    processing_time_ms: float | None
    low_confidence:     bool
    advanced_plus:      bool
    error:              str | None
    # smoothed level (only when session_id provided)
    smoothed:           dict | None = None


class HealthResponse(BaseModel):
    status:   str
    model:    str
    device:   str
    uptime_s: float


class RetrieveRequest(BaseModel):
    level: str = Field(..., example="B1", description="Learner's current CEFR level")
    query: str = Field(..., example="present perfect vs past simple", min_length=3)
    skill: str | None = Field(default=None, description="Filter by skill: grammar|vocabulary|reading|listening|writing")
    top_k: int = Field(default=5, ge=1, le=10)


class ChunkResult(BaseModel):
    id:         str
    cefr_level: str
    skill:      str
    topic:      str
    content:    str
    distance:   float
    rank:       int


class RetrieveResponse(BaseModel):
    level:          str
    adjacent_levels: list[str]
    query:          str
    chunks:         list[ChunkResult]


# ── D4: Exercise generation & feedback ───────────────────────────────────────

class ExerciseRequest(BaseModel):
    session_id: str = Field(..., description="Learner session ID")
    skill_gap:  str = Field(
        default="general grammar",
        example="present perfect vs past simple",
        description="The specific skill or grammar point to target",
    )
    skill:      str | None = Field(
        default=None,
        description="Broad skill filter for RAG: grammar|vocabulary|reading|writing",
    )
    top_k:      int = Field(default=5, ge=1, le=10, description="RAG chunks to retrieve")


class FeedbackRequest(BaseModel):
    session_id:     str = Field(..., description="Learner session ID")
    learner_answer: str = Field(..., min_length=1, max_length=3000)
    # Fallbacks used if the in-memory session was lost (e.g. free-tier restart)
    exercise:       dict | None = Field(default=None, description="Client copy of the current exercise")
    level:          str  | None = Field(default=None, description="Client copy of the learner level")


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Learner session ID")
    message:    str = Field(..., min_length=1, max_length=2000)


class SessionStateResponse(BaseModel):
    session_id:      str
    state:           str
    level:           str | None
    streak:          int
    total_exercises: int
    skill_focus:     str | None
    samples_used:    int
    created_at:      str
