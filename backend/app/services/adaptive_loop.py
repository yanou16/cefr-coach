"""
Adaptive Loop — learner session state machine.

States:
  ASSESS   → learner writes 2+ texts → classifier builds initial level
  PRACTICE → RAG retrieves chunks → LLM generates exercise
  EVALUATE → classifier runs on answer + LLM gives feedback
  ADJUST   → rolling window updated → level decision → back to PRACTICE

Key rule: level changes are CLASSIFIER-driven, never LLM-driven.
The fine-tuned model measures; the LLM teaches.

Session state is stored in-process (dict keyed by session_id).
Replace with Redis for multi-worker deployments.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from app.services.level_service import LearnerLevelTracker, classify


class State(str, Enum):
    ASSESS   = "assess"
    PRACTICE = "practice"
    EVALUATE = "evaluate"
    ADJUST   = "adjust"


@dataclass
class LearnerSession:
    session_id:      str
    state:           State                 = State.ASSESS
    level:           str | None           = None   # current smoothed level
    tracker:         LearnerLevelTracker  = field(default_factory=LearnerLevelTracker)
    current_exercise: dict | None         = None   # last generated exercise
    streak:          int                  = 0      # consecutive correct answers
    total_exercises: int                  = 0
    history:         list[dict]           = field(default_factory=list)  # conversation history
    created_at:      str                  = field(default_factory=lambda: datetime.utcnow().isoformat())
    skill_focus:     str | None           = None   # current gap being targeted

    # ── State transitions ──────────────────────────────────────────────────────

    def submit_writing_sample(self, text: str) -> dict:
        """
        ASSESS state: classify the text, add to rolling window.
        Returns the classification result + smoothed level if ready.
        """
        result   = classify(text)
        self.tracker.add(result)
        smoothed = self.tracker.smoothed_level()

        if not smoothed["needs_more_data"]:
            self.level = smoothed["level"]
            self.state = State.PRACTICE

        return {
            "raw":      result,
            "smoothed": smoothed,
            "state":    self.state,
            "ready":    not smoothed["needs_more_data"],
        }

    def start_exercise(self, exercise: dict, skill_focus: str) -> None:
        """PRACTICE state: store the generated exercise, transition to EVALUATE."""
        self.current_exercise = exercise
        self.skill_focus      = skill_focus
        self.state            = State.EVALUATE
        self.total_exercises += 1

    def submit_answer(self, feedback: dict, learner_text: str) -> dict:
        """
        EVALUATE state: process feedback + run classifier on the answer.
        Transition to ADJUST.
        """
        correct = feedback.get("correct", False)
        score   = feedback.get("score", 0)

        # Update streak
        if correct or score >= 70:
            self.streak += 1
        else:
            self.streak = 0

        # Classify the learner's answer text (if long enough)
        classification = None
        word_count = len(learner_text.split())
        if word_count >= 20:
            classification = classify(learner_text)
            self.tracker.add(classification)

        self.state = State.ADJUST
        return {
            "feedback":       feedback,
            "streak":         self.streak,
            "classified":     classification is not None,
            "classification": classification,
        }

    def adjust_level(self) -> dict:
        """
        ADJUST state: update smoothed level from rolling window.
        Transition back to PRACTICE.
        3 correct in a row → increase difficulty within level.
        Level change only via classifier evidence.
        """
        smoothed = self.tracker.smoothed_level()
        old_level = self.level

        if not smoothed["needs_more_data"]:
            self.level = smoothed["level"]

        level_changed = (self.level != old_level)

        # Streak-based difficulty hint (not a level change — stays within level)
        harder = self.streak >= 3

        self.state = State.PRACTICE
        self.streak = 0 if level_changed else self.streak

        return {
            "level":         self.level,
            "level_changed": level_changed,
            "old_level":     old_level,
            "harder":        harder,
            "smoothed":      smoothed,
            "state":         self.state,
        }

    def to_dict(self) -> dict:
        return {
            "session_id":      self.session_id,
            "state":           self.state,
            "level":           self.level,
            "streak":          self.streak,
            "total_exercises": self.total_exercises,
            "skill_focus":     self.skill_focus,
            "samples_used":    self.tracker.sample_count,
            "created_at":      self.created_at,
        }


# ── In-process session store ──────────────────────────────────────────────────

_sessions: dict[str, LearnerSession] = {}


def get_session(session_id: str) -> LearnerSession:
    if session_id not in _sessions:
        _sessions[session_id] = LearnerSession(session_id=session_id)
    return _sessions[session_id]


def reset_session(session_id: str) -> None:
    _sessions.pop(session_id, None)
