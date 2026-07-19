"""
Level Service — CEFR classifier inference + learner-level smoothing.

Serving: Option A — HF Space `yanou16/cefr-english-classifier` via gradio_client.
  - api_name="/run"  (the Space's submit handler)
  - Returns a markdown string like "**🟡 Intermediate** (B1)  —  confidence 94.1%"
  - We parse level + confidence from that string; other class probs are not available
    from the Space (only top-1 is returned). Set USE_MOCK=true for local dev without
    Space access.

Option B (local transformers) is available once disk space allows:
  pip install torch transformers accelerate → uncomment the classify_local path.

Rules from model card:
  - Input: 20–150 words
  - C2 recall ~60% (C1/C2 confusion) → show "Advanced+" band for adaptation decisions
  - Confidence < 0.6 → request another sample; don't update rolling window
  - Rolling window of 5 samples, confidence-weighted majority vote
"""

import os
import re
import time
from collections import deque
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

LABELS    = ["A1", "A2", "B1", "B2", "C1", "C2"]
HF_SPACE  = os.environ.get("CEFR_SPACE", "yanou16/cefr-english-classifier")
WINDOW    = 5
CONF_MIN  = 0.6
USE_MOCK  = os.environ.get("USE_MOCK_CLASSIFIER", "false").lower() == "true"

# ── Gradio client (lazy singleton) ────────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_client():
    from gradio_client import Client
    print(f"[level_service] Connecting to HF Space: {HF_SPACE}…")
    client = Client(HF_SPACE, verbose=False)
    print(f"[level_service] Connected.")
    return client


# ── Response parser ───────────────────────────────────────────────────────────
# Space returns: "**🟡 Intermediate** (B1)  —  confidence 94.1%"

_LEVEL_RE = re.compile(r'\(([A-C][12])\)')
_CONF_RE  = re.compile(r'confidence\s+([\d.]+)%')


def _parse_space_response(raw: str) -> tuple[str, float]:
    level_match = _LEVEL_RE.search(raw)
    conf_match  = _CONF_RE.search(raw)
    level = level_match.group(1) if level_match else "B1"
    conf  = round(float(conf_match.group(1)) / 100, 4) if conf_match else 0.0
    return level, conf


# ── Input validation ──────────────────────────────────────────────────────────

def _word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def _validate(text: str) -> str | None:
    wc = _word_count(text)
    if wc < 20:
        return f"Text too short ({wc} words). Write at least 20 words."
    if wc > 150:
        return f"Text too long ({wc} words). Keep it under 150 words."
    return None


# ── Mock (for dev without Space access) ───────────────────────────────────────

def _mock_classify(text: str) -> dict:
    """Deterministic mock: word count heuristic for local testing."""
    import random
    wc = _word_count(text)
    avg_word_len = sum(len(w) for w in text.split()) / max(wc, 1)
    idx = min(int((avg_word_len - 3) * 1.2), 5)
    idx = max(0, idx)
    level = LABELS[idx]
    conf  = round(0.7 + random.uniform(0, 0.25), 4)
    probs = {l: round(0.05, 4) for l in LABELS}
    probs[level] = conf
    return {
        "level":              level,
        "confidence":         conf,
        "probabilities":      probs,
        "processing_time_ms": 5.0,
        "low_confidence":     conf < CONF_MIN,
        "advanced_plus":      level in ("C1", "C2"),
        "mock":               True,
        "error":              None,
    }


# ── Single-sample classification ──────────────────────────────────────────────

def classify(text: str) -> dict:
    """
    Classify a single text. Returns level + confidence.
    Falls back to mock if USE_MOCK=true.
    """
    err = _validate(text)
    if err:
        return {"error": err, "level": None, "confidence": None,
                "probabilities": None, "processing_time_ms": None,
                "low_confidence": False, "advanced_plus": False, "mock": False}

    if USE_MOCK:
        return _mock_classify(text)

    t0 = time.time()
    try:
        client = _get_client()
        raw    = client.predict(text, api_name="/run")
    except Exception as e:
        return {"error": f"Classifier error: {e}", "level": None, "confidence": None,
                "probabilities": None, "processing_time_ms": None,
                "low_confidence": False, "advanced_plus": False, "mock": False}

    elapsed = round((time.time() - t0) * 1000, 1)
    level, conf = _parse_space_response(str(raw))

    # Space only returns top-1 probability; set others to small equal share
    probs = {l: round((1 - conf) / 5, 4) for l in LABELS}
    probs[level] = conf

    return {
        "level":              level,
        "confidence":         conf,
        "probabilities":      probs,
        "processing_time_ms": elapsed,
        "low_confidence":     conf < CONF_MIN,
        "advanced_plus":      level in ("C1", "C2"),
        "mock":               False,
        "error":              None,
    }


# ── Rolling-window level tracker (per learner session) ────────────────────────

class LearnerLevelTracker:
    """
    Confidence-weighted majority vote over a rolling window of WINDOW samples.
    Classifier-driven: level changes are never decided by the LLM.
    """

    def __init__(self):
        self._window: deque[dict] = deque(maxlen=WINDOW)

    def add(self, result: dict) -> None:
        if result.get("error") or result.get("low_confidence"):
            return
        self._window.append(result)

    def smoothed_level(self) -> dict:
        if len(self._window) < 2:
            return {
                "level":           None,
                "band":            None,
                "confidence":      None,
                "samples_used":    len(self._window),
                "needs_more_data": True,
            }

        scores: dict[str, float] = {l: 0.0 for l in LABELS}
        for r in self._window:
            scores[r["level"]] += r["confidence"]

        winner   = max(scores, key=lambda l: scores[l])
        total    = sum(scores.values())
        agg_conf = round(scores[winner] / total, 4) if total > 0 else 0.0
        band     = "Advanced+" if winner in ("C1", "C2") else winner

        return {
            "level":           winner,
            "band":            band,
            "confidence":      agg_conf,
            "samples_used":    len(self._window),
            "needs_more_data": False,
        }

    def reset(self) -> None:
        self._window.clear()

    @property
    def sample_count(self) -> int:
        return len(self._window)
