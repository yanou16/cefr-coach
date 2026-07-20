# CEFR Coach

> Adaptive English tutor powered by a fine-tuned CEFR classifier and Krashen's **i+1** method.
> Write two short samples → the AI pins your level → exercises target exactly one step ahead.

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![HuggingFace](https://img.shields.io/badge/🤗%20Model-yanou16%2Fcefr--english--classifier-FFD21F)
![License](https://img.shields.io/badge/License-MIT-green)

---

## What is CEFR Coach?

CEFR Coach is an end-to-end adaptive English learning app built for **Build Week 2026**.

Instead of a generic placement quiz, it watches **how you write** — grammar patterns, vocabulary range, clause complexity — and runs your text through a fine-tuned language model that outputs one of six CEFR levels (A1 → C2). Every exercise is then generated at exactly **L+1** (one level above yours), following Krashen's *Input Hypothesis*: comprehensible challenge, not frustration.

The feedback loop is continuous:
1. **You write** → classifier reads your grammar
2. **Level is pinned** → RAG retrieves i+1 corpus chunks
3. **LLM generates** a targeted exercise
4. **You answer** → LLM scores and explains errors
5. **Level re-evaluates** → loop repeats at your current edge

---

## AI / ML Pipeline

![AI Pipeline](docs/ai-pipeline.svg)

### How the classifier works

The heart of the system is **`yanou16/cefr-english-classifier`** — a [Qwen2.5-1.5B](https://huggingface.co/Qwen/Qwen2.5-1.5B) base model fine-tuned with **QLoRA** on a balanced CEFR corpus.

| Component | Detail |
|---|---|
| Base model | `Qwen/Qwen2.5-1.5B` |
| Fine-tuning | QLoRA (4-bit quantization, r=16) |
| Task | 6-class sequence classification (A1/A2/B1/B2/C1/C2) |
| Accuracy | **84.9%** on held-out test set |
| Serving | HuggingFace Space · `gradio_client.Client` |
| Fallback | `USE_MOCK_CLASSIFIER=true` for offline dev |

### Why a rolling window?

A single classification call on 30 words is noisy. `LearnerLevelTracker` keeps a **deque of the last 5 predictions**, each weighted by its confidence score, and takes a confidence-weighted majority vote. This prevents a single outlier response from jumping the learner up or down a level.

> **Critical rule:** the LLM never sets the level. Only the fine-tuned classifier does. The LLM generates content only.

### RAG retrieval

Before calling the LLM, the backend retrieves relevant pedagogical context:

1. The query is embedded locally with **`all-MiniLM-L6-v2` (ONNX)** — no API call, no latency
2. **ChromaDB** pre-filters the 82-chunk corpus to only `level == L` and `level == L+1` documents
3. Cosine similarity selects the top-K chunks
4. Chunks are injected into the LLM system prompt

This keeps exercises grounded in real CEFR-aligned grammar explanations rather than generic LLM output.

---

## System Architecture

![System Architecture](docs/architecture.svg)

### Backend services (`backend/app/services/`)

| Service | Route(s) | Responsibility |
|---|---|---|
| `level_service.py` | `POST /classify` | Calls HF Space, runs rolling window smoother |
| `rag_service.py` | internal | Embeds query (ONNX), queries ChromaDB, returns chunks |
| `tutor_service.py` | `POST /exercise` `POST /feedback` | Builds prompt + RAG context, calls LLM, parses JSON |
| `adaptive_loop.py` | `GET /session/status` | Tracks phase, streak, exercise count |

### Frontend state machine (`frontend/src/hooks/useAppReducer.ts`)

```
landing → assess → practice → exercise → feedback → chat
                   └─────────────────────────────────┘
                         repeats after each exercise
```

The reducer owns all app state: `phase`, `level`, `sessionId`, `streak`, `exercises[]`. API calls are fired in `App.tsx` on phase transitions.

### LLM swap (July 21)

The backend uses an OpenAI-compatible client. Switching from Groq to OpenAI on demo day requires only three `.env` changes:

```bash
LLM_BASE_URL=                  # empty → uses OpenAI default
LLM_MODEL=gpt-4o
LLM_API_KEY=<openai-key>
```

---

## Tech Stack

| Layer | Technology | Why chosen |
|---|---|---|
| **Classifier** | Qwen2.5-1.5B + QLoRA | Compact enough to fine-tune on consumer GPU; strong multilingual base for grammar patterns |
| **Classifier serving** | HuggingFace Space (Gradio) | Free hosting; `gradio_client` gives a clean Python API; no inference server to manage |
| **Level stability** | Rolling window (deque, n=5) | One noisy prediction shouldn't shift the UX; weighted vote handles varying confidence |
| **Embeddings** | `all-MiniLM-L6-v2` (ONNX) | Runs fully locally, no API latency, good quality for semantic similarity at sentence level |
| **Vector store** | ChromaDB | Zero-ops local store; metadata pre-filtering by level makes retrieval precision much higher |
| **Pedagogy** | Krashen i+1 | Target one level above → comprehensible challenge without demotivating frustration |
| **LLM** | Groq → GPT-4o | Groq for dev speed (fast inference, free); OpenAI GPT-4o for demo reliability |
| **Backend** | FastAPI (Python 3.13) | Async, fast, clean Pydantic models; easy to add routes |
| **Frontend** | React 18 + TypeScript + Vite | Type-safe, fast dev loop; `useReducer` maps cleanly to the phase state machine |
| **Deploy** | Docker Compose + Nginx | Single `docker compose up` for the full stack; Nginx serves the Vite build as static files |

---

## MLOps & Evals

### Classifier probes (`backend/evals/classifier_probes.py`)

12 fixed reference texts — 2 per CEFR level — run against the live `/classify` endpoint:

```bash
python backend/evals/classifier_probes.py --api http://localhost:8001
# Exit 0 = all probes pass, Exit 1 = failures printed
```

Scoring: exact match, with C1/C2 both accepted as "Advanced+" for borderline cases.

### RAG quality (`evals/ragas_rag_eval.py`)

Four [Ragas](https://docs.ragas.io/) metrics evaluated on a 10-question test set:

| Metric | What it measures |
|---|---|
| `faithfulness` | Is the answer grounded in the retrieved context? |
| `answer_relevancy` | Does the answer actually address the question? |
| `context_precision` | Are the retrieved chunks relevant to the question? |
| `context_recall` | Does the context cover what's needed to answer? |

```bash
python evals/ragas_rag_eval.py
# Results written to evals/ragas_results.json
```

---

## Quick Start (local dev)

### Prerequisites

- Python 3.11+
- Node 18+
- A Groq API key (free at [console.groq.com](https://console.groq.com))

### 1 — Clone and configure

```bash
git clone https://github.com/yanou16/cefr-coach.git
cd cefr-coach
cp .env.example .env   # then fill in your keys
```

`.env` required variables:

```bash
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
LLM_API_KEY=<your-groq-key>

# Optional — set true to skip HF Space calls during development
USE_MOCK_CLASSIFIER=false
```

### 2 — Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
uvicorn app.main:app --port 8001 --reload
```

### 3 — Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### 4 — Docker (full stack)

```bash
docker compose up --build
# Frontend: http://localhost
# Backend:  http://localhost:8001/docs
```

---

## Project Structure

```
cefr-coach/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, CORS, routers
│   │   ├── routers/                 # HTTP route definitions
│   │   └── services/
│   │       ├── level_service.py     # Classifier + rolling window
│   │       ├── rag_service.py       # ChromaDB + MiniLM ONNX
│   │       ├── tutor_service.py     # LLM exercise + feedback
│   │       └── adaptive_loop.py     # Session state tracking
│   ├── corpus/                      # YAML exercise corpus (82 chunks)
│   ├── evals/
│   │   └── classifier_probes.py     # 12 fixed-text probes
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx                  # Phase routing + API calls
│   │   ├── hooks/useAppReducer.ts   # State machine
│   │   ├── api/client.ts            # fetch wrappers
│   │   ├── components/
│   │   │   ├── LandingPage.tsx      # Landing + live mini-demo
│   │   │   ├── ExerciseCard.tsx     # Exercise display + answer
│   │   │   ├── FeedbackCard.tsx     # Score ring + error list
│   │   │   └── ChatWindow.tsx       # Tutor chat
│   │   └── index.css                # Design tokens + all styles
│   └── package.json
├── evals/
│   └── ragas_rag_eval.py            # RAG quality (4 Ragas metrics)
├── docs/
│   ├── ai-pipeline.svg              # ML pipeline diagram
│   └── architecture.svg             # System architecture diagram
├── docker-compose.yml
└── .gitignore
```

---

## Deploy

### Frontend → Vercel

```bash
cd frontend
npm run build
# Connect the /frontend folder to a Vercel project
# Set VITE_API_URL=https://your-backend-url in Vercel env vars
```

### Backend → Railway

Railway supports `docker-compose.yml` directly:

1. Push repo to GitHub
2. New Railway project → "Deploy from GitHub repo"
3. Set environment variables (same as `.env`)
4. The `fastapi` service in `docker-compose.yml` is auto-detected

---

## License

MIT — see [LICENSE](LICENSE).

---

*Built during **Build Week 2026** · Qwen2.5-1.5B + QLoRA · Krashen i+1 · ChromaDB RAG · LLaMA 3.3-70B → GPT-4o*
