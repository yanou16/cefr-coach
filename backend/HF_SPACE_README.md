---
title: CEFR Coach API
emoji: 🎓
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_port: 7860
---

# CEFR Coach — FastAPI Backend

FastAPI backend for the CEFR Coach adaptive English tutor.

- **POST /classify/session** — CEFR classification via a QLoRA fine-tuned classifier (HF Space)
- **POST /exercise** — RAG-grounded exercise generation (OpenAI GPT-5.6)
- **POST /feedback** — Structured feedback on learner answer
- **POST /chat** — i+1 tutor conversation
- **GET /session/{id}** — Adaptive loop state

Docs: `https://yanou16-cefr-coach-api.hf.space/docs`
