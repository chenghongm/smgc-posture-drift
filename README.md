# smgc-posture-drift

This repo provides a minimal, reproducible demonstration of **posture drift / attractor shift** in an LLM caused by a small fraction of **role-framing contamination** during LoRA fine-tuning.

We compare:
- **Base**: `mlx-community/Meta-Llama-3-8B-Instruct-4bit`
- **Adapter**: `adapters/A_mix_p0005` (training mix contains ~0.5% observer-style role-framing samples)

On a fully neutral prompt set (no role/persona/dialog cues), the adapter exhibits:
1) **response length collapse**
2) **meta-narrative density inflation** (SAS2)


## Repository Layout

```css
smgc-posture-drift/
├── README.md
├── requirements.txt
├── adapters/
│   └── A_mix_p0005/
│       └── adapter_config.json
├── data/
│   ├── D00.jsonl
│   └── D10.jsonl
├── eval/
│   ├── EPS_neutral.jsonl
│   └── outputs/
│       ├── base.neutral.clean.jsonl
│       ├── base.neutral.clean.metrics.jsonl
│       ├── A_mix_p0005.neutral.clean.jsonl
│       └── A_mix_p0005.neutral.clean.metrics.jsonl
├── scripts/
│   ├── eval_suite.py
│   ├── make_mix.py
│   ├── metrics.py
│   └── posture_eval.py
└── figures/
    └── stage1_examples.md
```

## Prerequisites

- macOS + MLX
- `mlx_lm` installed and available in PATH
- Python 3.10+

---

## Quick Reproduction (Stage-1)

Run posture-drift evaluation:

```bash
python scripts/posture_eval.py \
  --base eval/outputs/base.neutral.clean.jsonl \
  --adapt eval/outputs/A_mix_p0005.neutral.clean.jsonl

To also generate metric-enriched artifacts:

python scripts/posture_eval.py \
  --base eval/outputs/base.neutral.clean.jsonl \
  --adapt eval/outputs/A_mix_p0005.neutral.clean.jsonl \
  --with-metrics

  This will produce:

    eval/outputs/base.neutral.clean.metrics.jsonl
    eval/outputs/A_mix_p0005.neutral.clean.metrics.jsonl

--------------------------------------------------------------
Expected Output (fingerprint)
--------------------------------------------------------------

On EPS_neutral (n = 30, seed = 1):

Base

mean_len ≈ 383.7

p50_len ≈ 431 (p10 143, p90 576)

mean_sas2 ≈ 0.0101

p50_sas2 ≈ 0.0057

max_sas2 ≈ 0.0767

A_mix_p0005

mean_len ≈ 85.3

p50_len ≈ 79 (p10 29, p90 157)

mean_sas2 ≈ 0.0185

p50_sas2 ≈ 0.0117

max_sas2 ≈ 0.0662

Key observation

Median output length collapses ~5.5× (431 → 79)

Meta-narrative density (SAS2) roughly doubles despite much shorter outputs

Interpretation

This Stage-1 experiment demonstrates a stable posture attractor shift:
a small amount of role-framing contamination during fine-tuning induces a
persistent narrative / meta-framing bias and response length collapse,
even when evaluated on fully neutral prompts.
```

### Note on Adapter Weights

This repository does not include the actual LoRA adapter weight files (*.safetensors) due to GitHub file size limits and distribution policy.

The provided adapter_config.json is sufficient to reproduce all results if you re-generate the adapter locally using:

python scripts/make_mix.py
# then train LoRA using your MLX training pipeline on Mix_p0005.jsonl
