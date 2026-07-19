"""
Ragas evaluation of the CEFR Coach RAG pipeline.

Metrics:
  - context_precision   : are retrieved chunks relevant to the question?
  - context_recall      : does the retrieved context cover the ground truth answer?
  - faithfulness        : is the generated answer grounded in the retrieved context?
  - answer_relevancy    : does the answer actually address the question asked?

Usage:
  cd cefr-coach
  pip install ragas datasets openai  # or groq-compatible
  python evals/ragas_rag_eval.py

Set OPENAI_API_KEY (or LLM_BASE_URL + LLM_API_KEY for Groq) in .env before running.
"""

import os, sys, json
from pathlib import Path

# ── Ensure backend package is importable ─────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    context_precision,
    context_recall,
    faithfulness,
    answer_relevancy,
)
from ragas.llms import LangchainLLMWrapper
from langchain_openai import ChatOpenAI

# ── Configure LLM for Ragas judge ────────────────────────────────────────────
BASE_URL = os.getenv("LLM_BASE_URL")  # None → OpenAI; set for Groq
API_KEY  = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
MODEL    = os.getenv("LLM_MODEL", "gpt-4o")

llm_kwargs = dict(model=MODEL, api_key=API_KEY, temperature=0)
if BASE_URL:
    llm_kwargs["base_url"] = BASE_URL

ragas_llm = LangchainLLMWrapper(ChatOpenAI(**llm_kwargs))

# ── Ground-truth test set ─────────────────────────────────────────────────────
# Each entry: question the RAG would receive, ground-truth answer, target level
TEST_CASES = [
    # A1 retrieval
    {
        "question": "How do I use 'there is' and 'there are' correctly?",
        "ground_truth": (
            "Use 'there is' with singular or uncountable nouns and 'there are' with plural nouns. "
            "Contractions: There's = There is. Negative: There isn't / There aren't. "
            "Questions: Is there...? / Are there...?"
        ),
        "target_level": "A1",
    },
    {
        "question": "What is the difference between 'a' and 'an'?",
        "ground_truth": (
            "Use 'a' before consonant sounds and 'an' before vowel sounds. "
            "Examples: a book, a university (u = /juː/), an apple, an hour (h is silent). "
            "Both are indefinite articles used for one unspecified thing."
        ),
        "target_level": "A1",
    },
    # A2 retrieval
    {
        "question": "When do I use the simple past versus the present perfect?",
        "ground_truth": (
            "Use the simple past for completed actions at a specific past time (yesterday, last week, in 2020). "
            "Use the present perfect for actions with present relevance, no specific past time, "
            "or with 'ever', 'never', 'already', 'just', 'yet'. "
            "Example: 'I visited Paris last year.' vs 'I have visited Paris three times.'"
        ),
        "target_level": "A2",
    },
    {
        "question": "How do I form comparatives and superlatives?",
        "ground_truth": (
            "Short adjectives (1 syllable): add -er / -est. 'tall → taller → tallest'. "
            "Long adjectives (2+ syllables): use more / most. 'beautiful → more beautiful → most beautiful'. "
            "Irregular: good→better→best, bad→worse→worst, far→further→furthest."
        ),
        "target_level": "A2",
    },
    # B1 retrieval
    {
        "question": "Explain the difference between present perfect and past simple with examples.",
        "ground_truth": (
            "Past simple: completed action at a specific past time. 'I visited Rome in 2019.' "
            "Present perfect: action with present relevance or indefinite past time. 'I have visited Rome.' "
            "Key signal words: past simple uses specific time markers (yesterday, in 2019); "
            "present perfect uses ever, never, already, just, yet, recently, since, for."
        ),
        "target_level": "B1",
    },
    {
        "question": "What are modal verbs and how are they used?",
        "ground_truth": (
            "Modal verbs (can, could, may, might, must, shall, should, will, would) express ability, "
            "possibility, permission, obligation, and advice. They do not change for he/she/it "
            "and are followed by the base verb without 'to'. "
            "Examples: 'She can swim.' 'You must submit by Friday.' 'It might rain tomorrow.'"
        ),
        "target_level": "B1",
    },
    # B2 retrieval
    {
        "question": "How do I use the passive voice and when is it appropriate?",
        "ground_truth": (
            "Form: be + past participle. The agent (by + person) is optional. "
            "Use passive when: the agent is unknown, unimportant, or deliberately suppressed; "
            "to foreground the patient as topic; in formal/academic writing to sound objective. "
            "Example: 'The report was submitted on time.' vs 'He submitted the report on time.'"
        ),
        "target_level": "B2",
    },
    {
        "question": "Explain conditional sentences in English.",
        "ground_truth": (
            "Zero conditional (always true): If + present simple, present simple. 'If you heat water to 100°C, it boils.' "
            "First conditional (real future): If + present simple, will + base verb. 'If it rains, I'll stay home.' "
            "Second conditional (unreal present): If + past simple, would + base verb. 'If I had more time, I would study more.' "
            "Third conditional (unreal past): If + past perfect, would have + past participle. 'If I had studied, I would have passed.'"
        ),
        "target_level": "B2",
    },
    # C1 retrieval
    {
        "question": "What is inversion and how is it used for emphasis?",
        "ground_truth": (
            "Inversion places the auxiliary verb before the subject for emphasis, common in formal writing. "
            "Used with negative adverbials: 'Never have I seen such dedication.' 'Rarely does she make mistakes.' "
            "With 'only': 'Only then did I realise.' 'Only after the investigation was the truth revealed.' "
            "The auxiliary inverts, not the main verb."
        ),
        "target_level": "C1",
    },
    {
        "question": "What is nominalisation and why is it used in academic writing?",
        "ground_truth": (
            "Nominalisation converts verbs and adjectives into nouns. "
            "Examples: decide→decision, analyse→analysis, significant→significance. "
            "It creates formal, dense academic prose. "
            "'We analysed the data' becomes 'Analysis of the data was conducted.' "
            "Overuse creates impenetrable prose — balance with active verbs."
        ),
        "target_level": "C1",
    },
    # C2 retrieval
    {
        "question": "What is the difference between 'imply' and 'infer'?",
        "ground_truth": (
            "The speaker or writer implies — they encode implicit meaning without stating it directly. "
            "The listener or reader infers — they decode or interpret that implicit meaning. "
            "'Her tone implied impatience.' / 'I inferred from her tone that she was impatient.' "
            "Confusing the two is a common error even among advanced speakers."
        ),
        "target_level": "C2",
    },
    {
        "question": "Explain the difference between 'mustn't' and 'don't have to'.",
        "ground_truth": (
            "'Mustn't' expresses prohibition — you are not allowed to do something. "
            "'Don't have to' expresses absence of obligation — it is not necessary but is allowed. "
            "'You mustn't sign anything.' (prohibited) vs 'You don't have to sign anything.' (optional). "
            "These are not interchangeable."
        ),
        "target_level": "C2",
    },
]

# ── Run RAG retrieval for each test case ─────────────────────────────────────
from app.services.rag_service import retrieve

questions, contexts, answers, ground_truths = [], [], [], []

print(f"Running RAG retrieval for {len(TEST_CASES)} test cases…")
for i, tc in enumerate(TEST_CASES):
    q  = tc["question"]
    lv = tc["target_level"]
    gt = tc["ground_truth"]

    chunks = retrieve(query=q, level=lv, top_k=4)
    ctx    = [c["content"] for c in chunks]

    # Build a simple concatenated answer from chunks (no LLM generation here —
    # we evaluate retrieval quality; faithfulness uses the retrieved context directly)
    answer = " ".join(ctx[:2])[:800]  # first two chunks, truncated

    questions.append(q)
    contexts.append(ctx)
    answers.append(answer)
    ground_truths.append(gt)
    print(f"  [{i+1}/{len(TEST_CASES)}] {lv}: {q[:60]}… → {len(chunks)} chunks")

# ── Build Ragas Dataset ───────────────────────────────────────────────────────
dataset = Dataset.from_dict({
    "question":   questions,
    "contexts":   contexts,
    "answer":     answers,
    "ground_truth": ground_truths,
})

# ── Evaluate ─────────────────────────────────────────────────────────────────
print("\nRunning Ragas evaluation…")
result = evaluate(
    dataset=dataset,
    metrics=[context_precision, context_recall, faithfulness, answer_relevancy],
    llm=ragas_llm,
    raise_exceptions=False,
)

# ── Print results ─────────────────────────────────────────────────────────────
print("\n── Ragas RAG Evaluation Results ──────────────────────────────────────")
df = result.to_pandas()
print(df[["question", "context_precision", "context_recall",
          "faithfulness", "answer_relevancy"]].to_string(index=False))

means = df[["context_precision", "context_recall", "faithfulness", "answer_relevancy"]].mean()
print("\n── Aggregate Scores ──────────────────────────────────────────────────")
for metric, val in means.items():
    bar = "█" * int(val * 20) + "░" * (20 - int(val * 20))
    print(f"  {metric:<22} {bar}  {val:.3f}")

# ── Save JSON report ──────────────────────────────────────────────────────────
out = Path(__file__).parent / "ragas_results.json"
report = {
    "aggregate": means.to_dict(),
    "per_sample": df.to_dict(orient="records"),
}
out.write_text(json.dumps(report, indent=2, default=str))
print(f"\nFull report saved to {out}")
