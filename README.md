# Statute Dossier Evaluation Harness

This repository implements a small, reproducible evaluation harness for generating **litigation-style evidentiary dossiers** from realistic multi-turn chatbot conversations.

The harness is designed to log, structure, and preserve conversational artifacts that *could plausibly be examined as evidence* under statutory or regulatory analysis.  
The current implementation uses **Statute A6** as a pilot scenario.

This project is an **evaluation and logging tool only**.  
It does **not** provide legal advice and does **not** make claims about constitutionality, liability, or policy merits.

---

## What the system produces

For a single deterministic conversation run, the system generates:

1. A full multi-turn transcript (`transcript.jsonl`)
2. Structured feature extraction with turn-indexed excerpts (`features.json`)
3. A rule-based evidentiary flag (`a6_rule.json`)
4. An independent judge-model assessment with structured JSON output (`a6_judge.json`)
5. A neutral evidentiary memo citing turn numbers and excerpts (`memo.md`)

All outputs are written to a timestamped run directory under `outputs/`.

---

## What this evaluates (pilot scope)

The harness operationalizes whether a **realistic multi-turn chatbot conversation** could plausibly be offered as evidence of:

1. Acknowledgement of user emotion or stress  
2. Invitations to continue or disclose more information  
3. Procedural or step-by-step guidance  
4. Offers of continued engagement or assistance  

These elements are evaluated via two independent mechanisms:

1. **Simple, interpretable presence checks**
   - Pattern-based feature detection
   - Turn-indexed excerpts for traceability

2. **An independent judge model**
   - Reads the full transcript
   - Returns a structured JSON assessment and rationale

The goal is **not** to decide legality.  
The goal is to produce **high-fidelity, reviewable artifacts** that could be examined by attorneys, regulators, auditors, or researchers.

---

## Repository structure

```
repo_root/
README.md
requirements.txt or pyproject.toml

src/
  statute_dossier_eval/
    __init__.py
    config.py
    runner.py
    features.py
    judges.py
    report.py
    io.py
    data/
      conversations/
        a6_landlord_tenant_tree.yaml

outputs/
  <run_id>/
    transcript.jsonl
    run_meta.json
    features.json
    a6_rule.json
    a6_judge.json
    memo.md

paper/
  whitepaper.tex
  whitepaper.pdf

.github/
  workflows/
    build-paper.yml
```

The `outputs/` directory is generated automatically.

---

## Conversation scenario (current pilot)

The implemented scenario is a **landlord–tenant dispute** in which a user is deciding how to respond to a withheld security deposit.

The conversation is modeled as a deterministic tree with the following phases:

1. Orientation  
2. Clarification  
3. Procedural follow-up  
4. Relational cue  
5. Continuation request  

A single branch is selected deterministically via an environment variable.

---

## One-command quickstart

### Requirements

- Python 3.10+
- An Inspect-compatible model backend
- Access to a target model and a judge model

### Environment variables

Set these from the repository root:

```bash
export TARGET_MODEL=openai/gpt-4.1
export TEMPERATURE_TARGET=0

export JUDGE_MODEL=openai/gpt-4.1
export TEMPERATURE_JUDGE=0

export BRANCH_LABEL=ask_for_guidance
```

### Run the harness

```bash
python -m statute_dossier_eval.runner
```

A new directory will be created under `outputs/` containing the transcript, extracted features, rule flag, judge assessment, and evidentiary memo.

---

## Whitepaper

The `paper/` directory contains a LaTeX whitepaper describing:

- The evaluation pipeline
- Artifact design choices
- Limitations and non-claims
- An example evidentiary excerpt table

Build the PDF locally with:

```bash
cd paper
latexmk -pdf whitepaper.tex
```

A GitHub Action is included to compile the PDF automatically on push.

---

## Scope and limitations

- This repository demonstrates a **pilot evaluation harness**, not a comprehensive legal analysis system.
- Only one statute-inspired scenario (A6) is implemented.
- Feature extraction is intentionally simple and interpretable.
- Judge outputs are advisory signals, not determinations.

The primary contribution is **artifact fidelity and reproducibility**, not legal correctness or normative conclusions.
