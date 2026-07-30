# Model Benchmark Comparison

Benchmarked on the first 25 questions from the validation set.

| Model | Avg Latency (ms) | Hallucination Rate | Refusal Accuracy | Retrieval Grounding Score |
|-------|------------------|--------------------|------------------|---------------------------|
| qwen2.5:3b | 10392ms | 32.0% | 0.0% | 85.0% |
| llama3.1:8b | 24473ms | 32.0% | 0.0% | 85.0% |
| gemma3:12b | 37707ms | 80.0% | 0.0% | 25.0% |

## Definitions
- **Hallucination Rate**: % of times the model invented an answer not in the context, or ignored context to provide an incorrect answer.
- **Refusal Accuracy**: % of times the model correctly refused to answer when the context lacked the answer.
- **Retrieval Grounding Score**: % of times the model correctly answered when the context *contained* the answer.

## Recommendation
**Recommended Model for Demo:** `qwen2.5:3b`
