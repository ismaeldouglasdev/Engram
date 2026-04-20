# Fine-tuning NLI Model for Code-domain Contradictions

This guide explains how to fine-tune the NLI cross-encoder model for better code-domain contradiction detection.

## Current Model

The default model is `cross-encoder/nli-MiniLM2-L6-H768`, a general-purpose NLI model trained on SNLI/MNLI.

## Why Fine-tune?

The default model may miss code-domain contradictions like:
- "rate limit is 1000" vs "rate limit is 2000"
- `TIMEOUT_MS = 5000` vs `TIMEOUT = 500`
- "JWT expires in 1h" vs "JWT token valid for 3600s"

## Using a Fine-tuned Model

Set the `ENGRAM_NLI_MODEL` environment variable:

```bash
export ENGRAM_NLI_MODEL=cross-encoder/my-code-nli-model
```

Or in your workspace config:
```python
engine = Engine(workspace_id=..., nli_model_name="cross-encoder/my-code-nli-model")
```

## Fine-tuning Steps

1. **Collect contradiction pairs** from your workspace:
```python
from engram.storage import Storage
conflicts = await storage.get_conflicts(status="resolved")
# conflicts now contains fact_a_content and fact_b_content pairs
```

2. **Create training data** in the format:
```
{"text": "fact A [SEP] fact B", "label": "contradiction"}
{"text": "fact A [SEP] fact C", "label": "entailment"}
```

3. **Fine-tune** using sentence-transformers:
```python
from sentence_transformers import CrossEncoder, InputExample
from sentence_transformers import EvaluationPipeline

model = CrossEncoder('cross-encoder/nli-MiniLM2-L6-H768')
train_examples = [InputExample(texts=[...], label=0)]  # 0=contradiction

model.fit(train_examples, epochs=3)
model.save('cross-encoder/my-code-nli-model')
```

4. **Deploy** with `ENGRAM_NLI_MODEL=cross-encoder/my-code-nli-model`

## Evaluation

Run detection diagnostics:
```bash
engram doctor --load-nli
```

Check conflict detection stats:
```bash
engram conflicts
```