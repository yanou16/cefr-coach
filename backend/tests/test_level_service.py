import pytest

from app.services.level_service import (
    LearnerLevelTracker,
    _parse_space_response,
    _validate,
    _word_count,
)


def words(n: int) -> str:
    return " ".join(f"word{i}" for i in range(n))


def result(level: str, confidence: float, *, error: str | None = None, low_confidence: bool = False) -> dict:
    return {
        "level": level,
        "confidence": confidence,
        "probabilities": {},
        "processing_time_ms": 1.0,
        "low_confidence": low_confidence,
        "advanced_plus": level in ("C1", "C2"),
        "error": error,
    }


def test_parse_space_response_extracts_level_and_confidence_from_real_response():
    raw = "**🟡 Intermediate** (B1)  —  confidence 94.1%"

    level, confidence = _parse_space_response(raw)

    assert level == "B1"
    assert confidence == 0.941


def test_parse_space_response_malformed_response_falls_back_to_b1_zero_confidence():
    level, confidence = _parse_space_response("not a classifier response")

    assert level == "B1"
    assert confidence == 0.0


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", 0),
        ("hello", 1),
        ("hello   world\nagain", 3),
        (" punctuation, still-counts! ", 2),
    ],
)
def test_word_count_counts_non_whitespace_tokens(text, expected):
    assert _word_count(text) == expected


@pytest.mark.parametrize(
    ("count", "expected_error"),
    [
        (19, "Text too short (19 words). Write at least 20 words."),
        (20, None),
        (150, None),
        (151, "Text too long (151 words). Keep it under 150 words."),
    ],
)
def test_validate_word_count_boundaries(count, expected_error):
    assert _validate(words(count)) == expected_error


def test_tracker_needs_more_data_with_fewer_than_two_samples():
    tracker = LearnerLevelTracker()

    empty = tracker.smoothed_level()
    assert empty["needs_more_data"] is True
    assert empty["samples_used"] == 0
    assert empty["level"] is None

    tracker.add(result("B1", 0.9))
    single = tracker.smoothed_level()
    assert single["needs_more_data"] is True
    assert single["samples_used"] == 1
    assert single["level"] is None


def test_tracker_skips_low_confidence_and_error_results():
    tracker = LearnerLevelTracker()

    tracker.add(result("C2", 0.99, low_confidence=True))
    tracker.add(result("A1", 0.99, error="Classifier error"))

    smoothed = tracker.smoothed_level()
    assert smoothed["samples_used"] == 0
    assert smoothed["needs_more_data"] is True


def test_tracker_weighted_majority_returns_b1():
    tracker = LearnerLevelTracker()

    tracker.add(result("B1", 0.8))
    tracker.add(result("B1", 0.7))
    tracker.add(result("A2", 0.6))

    smoothed = tracker.smoothed_level()

    assert smoothed["level"] == "B1"
    assert smoothed["band"] == "B1"
    assert smoothed["samples_used"] == 3
    assert smoothed["needs_more_data"] is False
    assert smoothed["confidence"] == round((0.8 + 0.7) / (0.8 + 0.7 + 0.6), 4)


def test_tracker_rolling_window_keeps_last_five_samples():
    tracker = LearnerLevelTracker()

    tracker.add(result("A1", 0.99))
    tracker.add(result("A2", 0.99))
    tracker.add(result("B1", 0.9))
    tracker.add(result("B1", 0.9))
    tracker.add(result("B1", 0.9))
    tracker.add(result("B2", 0.95))

    smoothed = tracker.smoothed_level()

    assert smoothed["samples_used"] == 5
    assert smoothed["level"] == "B1"
