# Reproducible research chain

Every agent run should record:
- task id, prompt file path and SHA-256;
- source URLs and original content hashes, if captured;
- agent name, model identifier, provider/local backend and quantization if known;
- inference configuration (temperature, context, seed if supported), tool permissions;
- repo HEAD SHA, program/script versions;
- packet SHA-256; timestamps; validation commands and outputs;
- human review state with separate evidence.

Do not treat LLM bit-for-bit output reproducibility as guaranteed. Preserve the exact original model output for audit and replay deterministic downstream transforms. Never send confidential data to an external model without explicit authorization.

For local retrieval use chunk indices with precise citations and source hash, rather than embedding a whole country corpus in each prompt. Cache unchanged source-derived text. Do not paraphrase the source before the evidence extraction step.
