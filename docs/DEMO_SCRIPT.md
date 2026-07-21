# Demo Script — CEFR Coach

Target length: 2:30–2:50
Submission requirement: voiceover must explain what was built, how Codex was used, and how GPT-5.6 was used.

## 0:00–0:20 — Problem

Hi, I’m Rayane. I built CEFR Coach because most language apps either give everyone the same lessons or use a placement test once and then stop adapting.

As a TOEIC learner, I wanted a tutor that can answer one practical question every day: what is my English level right now, and what should I practice next?

## 0:20–0:55 — Landing + Live Level Detection

This is CEFR Coach. I write a short English sample, and the app sends it to my fine-tuned CEFR classifier.

The classifier returns a CEFR level from A1 to C2 with confidence. I use a rolling window of predictions, so one noisy answer cannot immediately change the learner’s level.

The key idea is simple: the small fine-tuned model measures; GPT-5.6 teaches.

## 0:55–1:35 — Adaptive Exercise

After the level is established, the backend retrieves pedagogical chunks from a CEFR-tagged corpus.

The retrieval is filtered by level, so a B1 learner only receives B1 or B2 content. That implements Krashen’s i+1 principle: the exercise should be one step above the learner, not too easy and not too hard.

GPT-5.6 then receives the retrieved chunks and generates a structured exercise as JSON: instruction, task, expected level, rubric, and answer.

## 1:35–2:10 — Feedback + Chat

Now I answer the exercise. GPT-5.6 gives feedback at the learner’s level: score, strengths, errors, corrections, and the next focus.

The learner can also ask follow-up questions in chat. The tutor keeps the response calibrated to the current CEFR level.

Importantly, the level is still controlled by the classifier, not by the LLM. GPT-5.6 teaches and explains, but the fine-tuned classifier decides the level.

## 2:10–2:40 — Architecture + Codex Usage

The app has a React frontend, a FastAPI backend, a Hugging Face classifier service, ChromaDB retrieval, and GPT-5.6 for generation and feedback.

I used Codex to help finalize the production app: reviewing the repository, preparing the README and deployment structure, cleaning provider configuration, and producing this demo script and submission checklist.

GPT-5.6 is used inside the product as the tutor engine for exercise generation, feedback, and level-calibrated conversation.

## 2:40–2:55 — Closing

CEFR Coach is not just a chatbot. It separates measurement from teaching: a specialized classifier measures proficiency, and GPT-5.6 turns that measurement into the next best exercise.
