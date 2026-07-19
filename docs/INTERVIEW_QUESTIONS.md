# Exit-test: answer ALL before submitting

## Fine-tuning (your own model)

1. **What exactly does the PEFT adapter file contain, and why is it ~few MB when the base model is 3GB?**
   > TODO

2. **Why rank 32 / alpha 64? What would change with rank 8?**
   > TODO

3. **Why 4-bit NF4 quantization during training but F16 at inference?**
   > TODO

4. **Why is C2 recall 60%? Show it on the confusion matrix. What data change would fix it?**
   > Confirmed from probe eval: both C1 probes got classified as C2 (conf 0.99, 0.98). The classifier over-predicts C2 for C1 texts and possibly vice-versa. Root cause: synthetic training data for C1 and C2 may be too similar in vocabulary/structure. Fix: add more C1-specific training samples that are clearly distinguishable from C2 — target shorter sentences with complex grammar but less esoteric vocabulary. This is why we treat C1/C2 as "Advanced+" band in the product: the classifier cannot reliably distinguish them.

5. **Why `q_proj`/`v_proj` only and not all linear layers?**
   > TODO

## RAG (built this week)

6. **Why semantic-unit chunking instead of fixed 512-token chunks — show one concrete failure of the latter on your corpus.**
   > TODO

7. **What does the metadata pre-filter do that pure vector similarity cannot?**
   > TODO

8. **Your retrieval returns a wrong chunk for query X — walk through 3 fixes in order of cost.**
   > TODO

9. **What does Ragas context precision actually compute (formula, not vibes)?**
   > TODO

10. **Embedding model A vs B on your 10 test queries — which won and what does that imply?**
    > TODO

## System

11. **Why is level adaptation classifier-driven and not GPT-driven?**
    > GPT-5.6 is a generative model optimised for fluency and helpfulness — it has no reliable calibration for CEFR levels and would hallucinate confidence. The fine-tuned classifier was trained on labelled CEFR data and outputs calibrated probabilities. Letting the LLM decide level would break the system's core guarantee: that difficulty tracks the learner's actual proficiency, not the tutor's self-assessment of what it generated. The separation also prevents a failure mode where the tutor "teaches down" to avoid making errors.

12. **What happens when classifier confidence is 0.45 — and why is that the right product behavior?**
    > Observed in the probe eval: A1 probe 2 got conf=0.46 (just below our 0.6 threshold). The system returns `low_confidence: true` and the `LearnerLevelTracker.add()` method ignores this result — it does NOT enter the rolling window. The UI then asks the learner to write one more sample before deciding. This is right because: (1) a 0.45-confidence classification is barely above random for 6 classes, (2) forcing a level decision from a noisy signal leads to miscalibrated exercises, (3) asking for another sample is a better UX than silently misfiring.
