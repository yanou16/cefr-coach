"""
Langfuse wiring — all pipeline steps are traced from day 1.

Usage:
    from app.observability import langfuse, trace_classify

    with langfuse.trace(name="exercise-cycle", session_id=sid) as trace:
        span = trace.span(name="classify")
        result = classify(text)
        span.end(output=result)
"""

import os
import functools
import time

from dotenv import load_dotenv

load_dotenv()

_PUBLIC  = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
_SECRET  = os.environ.get("LANGFUSE_SECRET_KEY", "")
_HOST    = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")

# Lazy-import so the app starts even if langfuse isn't installed / creds missing
try:
    from langfuse import Langfuse
    langfuse = Langfuse(public_key=_PUBLIC, secret_key=_SECRET, host=_HOST) if (_PUBLIC and _SECRET) else None
except ImportError:
    langfuse = None


def is_enabled() -> bool:
    return langfuse is not None


def trace_generation(name: str, session_id: str, input_data: dict, output_data: dict, latency_ms: float) -> None:
    """Fire-and-forget trace for a single generation step."""
    if not is_enabled():
        return
    try:
        trace = langfuse.trace(name=name, session_id=session_id)
        trace.generation(
            name=name,
            input=input_data,
            output=output_data,
            metadata={"latency_ms": latency_ms},
        )
    except Exception:
        pass  # never crash the main request path due to observability


def trace_classify(session_id: str, text: str, result: dict) -> None:
    """Trace a /classify call."""
    trace_generation(
        name="classify",
        session_id=session_id or "anonymous",
        input_data={"text": text[:200]},   # truncate PII-adjacent data
        output_data=result,
        latency_ms=result.get("processing_time_ms", 0),
    )
