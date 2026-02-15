# CLAUDE.md

## What this project does

This is a **litigation-dossier evaluation harness** that tests whether AI chatbot conversations could plausibly be offered as evidence under Tennessee SB1493/HB1455 clause A6 — the prohibition against AI that mirrors human-to-human interaction in ways that could lead users to feel they are developing a relationship.

The harness replays a scripted multi-turn conversation (currently a landlord-tenant dispute) against a target LLM, then produces a complete evidentiary artifact package: transcript, extracted features, a rule-based flag, an independent LLM judge assessment, and a Markdown memo. The output is designed to be reviewable by attorneys, regulators, or researchers.

**Audience:** Legal researchers, AI policy analysts, compliance teams evaluating chatbot behavior against statutory language.

**This is not a legal tool.** It produces structured artifacts for review — it does not make legal determinations.

## How to run

```bash
export TARGET_MODEL=openai/gpt-4.1
export JUDGE_MODEL=openai/gpt-4.1
export BRANCH_LABEL=ask_for_guidance   # or ask_for_support, ask_for_plan
python -m statute_dossier_eval.runner
```

Outputs land in `outputs/<YYYYMMDD_HHMMSS>/` with six artifacts.

## Architecture

Linear pipeline, all orchestrated by `runner.py`:

```
YAML scenario tree
  -> inspect-ai eval (replay_tree solver generates assistant turns)
  -> transcript.jsonl
  -> features.py (pattern-based feature extraction)
  -> judges.py (rule-based flag AND async LLM judge)
  -> report.py (Markdown memo)
```

### Module responsibilities

| Module | What it does |
|---|---|
| `config.py` | Reads env vars (models, temperatures, branch, scenario path). `validate_config()` checks API keys at startup. |
| `io.py` | `TurnRecord` dataclass, run ID generation, JSON/JSONL I/O helpers. |
| `runner.py` | Entry point. Loads YAML, builds inspect-ai Task, runs pipeline end-to-end. |
| `features.py` | Substring/pattern matching on assistant turns for 5 evidentiary features. Phase-gated for relational/continuation features. |
| `judges.py` | Two independent assessors: deterministic rule-based AND flag, async LLM judge with structured JSON output. |
| `report.py` | Assembles Markdown memo merging rule + judge evidence into a cited excerpt table. |
| `data/conversations/*.yaml` | Conversation scenario trees. Nodes have `content_intent` for assistant turns (LLM generates actual text). |

### Key data types

- **TurnRecord** (`io.py`): frozen dataclass — `turn_index`, `role`, `content`, `node_id`, `phase`
- **Features dict** (`features.py`): `{feature_name: {present: bool, evidence: [{turn_index, quote}]}}`
- **Rule output** (`judges.py`): `{a6_flag: bool, a6_rationale: str, evidence_snippets: [...], rule_inputs: {...}}`
- **Judge output** (`judges.py`): `{score: "likely_yes"|"borderline"|"likely_no", rationale: str, cited_turns: [int], valid_json: bool}`

## Key design decisions and why

1. **Substring matching over ML/embeddings for feature extraction.** Intentional — the features must be fully interpretable and auditable for a legal/evidentiary context. A black-box classifier would undermine the purpose.

2. **Two independent assessment mechanisms (rule + judge).** The rule-based flag is deterministic and transparent; the LLM judge provides a second opinion that can catch things patterns miss. Neither is authoritative alone.

3. **Phase-gating on relational/continuation features.** Relational framing ("you're not alone") and invitation-to-continue patterns only fire in later conversation phases. Early-phase matches would be false positives since the conversation hasn't reached the emotional/relational context yet.

4. **`content_intent` in YAML, not literal assistant text.** Assistant nodes in the scenario tree describe *what the assistant should do*, not what it should say. The target LLM generates the actual response, which is what gets evaluated.

5. **Graceful fallback in judge parsing.** If the LLM judge returns malformed JSON, the system falls back to `borderline` with `valid_json: false` rather than crashing. This keeps the pipeline running while flagging the degradation.

6. **`inspect-ai` as the evaluation backbone.** Provides model abstraction, async generation, and solver composition out of the box.

## Known limitations and tech debt

### Test coverage
`tests/` has 100 tests covering `features.py` (pattern matching, phase-gating, evidence recording), `judges.py` (JSON extraction, validation, rule logic), and `config.py` (env var validation). No integration tests for the full pipeline yet. Run with: `PYTHONPATH=src venv/bin/python -m pytest tests/ -v`

### Hardcoded to one scenario
`features.py` patterns, `judges.py` rule logic, and `report.py` counterarguments are all written specifically for the A6 landlord-tenant scenario. `config.py` exposes `SCENARIO_PATH` but swapping in a new scenario would require touching most modules.

### Brittle feature extraction
Substring matching (`has_any`, `first_match`) is case-lowered but has no fuzzy matching, stemming, or synonym handling. Common phrases like "let me know" or "i can help" may false-positive in non-relational contexts. Curly/straight apostrophe variants are consolidated into module-level constants (both are needed because `.lower()` does not normalize U+2019).

### JSON extraction
`extract_first_json_object()` in `judges.py` uses `json.JSONDecoder().raw_decode()` to correctly handle braces inside string values.

### `repo_root_from_src_file()` counts parents
Derives repo root by walking exactly 3 parents up from the source file (`src/statute_dossier_eval/runner.py`). Any package restructuring silently breaks this.

### Mixed sync/async
`main()` is synchronous but calls `anyio.run()` to bridge into the async judge assessment. This works but is awkward.

### Hardcoded counterarguments
The three counterarguments in `report.py` are static strings, not driven by data. They'll become stale if the scenario changes.

### Other
- Timezone hardcoded to `America/New_York` in `io.py`
- `.env.example` exists; `validate_config()` checks API keys at startup
- The whitepaper (`paper/whitepaper.tex`) is a skeleton with placeholder content
- `.github/workflows/build-paper.yml` is referenced in README but doesn't exist in this tree

## What I want evaluated

When reviewing or modifying this codebase, I'm specifically interested in feedback on:

1. **Feature extraction robustness.** Are the substring patterns in `features.py` catching the right things? Are there obvious false-positive or false-negative gaps? Is there a better approach that preserves interpretability?

2. **Judge prompt engineering.** Is the prompt in `judges.py` (`judge_model_a6_assessment`) well-structured? Does it constrain the output format tightly enough? Should the system prompt carry more context?

3. **Pipeline error handling.** If the target model returns empty/malformed responses, or the YAML is missing fields, how gracefully does the pipeline degrade? There's minimal validation beyond the judge fallback.

4. **Generalization path.** If we add a second statute or scenario, what's the cleanest refactor? Should features/rules be config-driven? Should the YAML schema be formalized?

5. **Test strategy.** What should the first tests cover? Unit tests on feature extraction and rule logic seem highest-value, but is there a useful integration test pattern for the full pipeline?

## Conventions

- All config via environment variables (see `config.py`)
- Run from repo root: `python -m statute_dossier_eval.runner`
- Outputs are timestamped and self-contained in `outputs/<run_id>/`
- `transcript.jsonl` is append-only during a run; all other artifacts are written once at the end
- Feature evidence is turn-indexed with 90-char quote windows
- The rule-based flag requires AND across features (see `judges.py:53`)
