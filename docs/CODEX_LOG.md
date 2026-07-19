# Codex Usage Log

_Keep this updated from day 1. Do NOT reconstruct at the end._

## D1 — July 14, 2026
- Scaffolded backend structure with Claude Code
- Key decisions:
  - Option B (self-host inference) chosen over HF Space API — full control for judges
  - Rolling window of 5 for smoothing instead of single-sample level changes
  - Langfuse tracing wired from day 1 (not retroactively)

## D2 — July 15, 2026
- Ran 12-probe classifier eval → 6/12 passed (50%)
- KEY FINDING: model has systematic +1 level bias (A2→B1, B1→B2, B2→C1)
- C1/C2 band works perfectly (4/4 pass as Advanced+)
- Smoothing test: 3 B1 texts → window converges at sample 2 (correct)
- Low-confidence A1 probe (conf=0.46) correctly excluded from rolling window
- Wrote 40 corpus chunks: A2 (10) + B1 (15) + B2 (15)
  - Coverage: grammar, vocabulary, writing, reading (TOEIC), listening (TOEIC)
- Probe texts may need recalibration (or model bias noted for adaptation logic)

## D3 — July 16, 2026
- Built RAG pipeline: YAML corpus → ChromaDB (all-MiniLM-L6-v2 ONNX) → metadata pre-filter → vector search
- Key decision: always use ONNX embeddings (not OpenAI) — free, offline, consistent with persisted collection
- Metadata pre-filter guarantees i+1 content: learner at L sees only {L, L+1} chunks
- Index built: 40 chunks (A2: 10, B1: 15, B2: 15)
- New endpoints: POST /retrieve, POST /rag/build
- Probe eval: retrieval returns semantically relevant grammar/vocabulary chunks

## D4 — July 17, 2026
- Implemented `tutor_service.py` (Groq/Llama-3.3-70b-versatile via OpenAI-compat SDK):
  - `generate_exercise()` → JSON-mode structured output, grounded in RAG chunks
  - `give_feedback()` → structured feedback at learner's reading level
  - `conversation_turn()` → i+1 reply (Krashen's comprehensible input)
  - Provider swap: 2 lines to change for OpenAI GPT final submission
- Implemented `adaptive_loop.py` state machine:
  - States: ASSESS → PRACTICE → EVALUATE → ADJUST → PRACTICE
  - Level changes are CLASSIFIER-driven, never LLM-driven (architecture invariant)
  - Streak tracking: 3 correct → harder difficulty hint within same level
- New endpoints: POST /exercise, POST /feedback, POST /chat, GET /session/{id}
- Bug fixed: `classify/session` now feeds adaptive-loop LearnerSession (unified store)
- Bug fixed: ONNX embedding function hardcoded in rag_service (OpenAI key conflict)
- Dev env: USE_MOCK_CLASSIFIER=true for offline testing (HF Space may be blocked)
- Smoke test: full assess→exercise→feedback→chat flow passes end-to-end

## D5 — July 18, 2026
<!-- Frontend (Codex-heavy day) -->

## D6 — July 19, 2026
<!-- Evals complete, corpus to ~120 chunks, docker compose -->

## D7 — July 20, 2026
<!-- Polish, README, demo video -->
