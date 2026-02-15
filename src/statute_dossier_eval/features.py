import json
from pathlib import Path
from typing import List, Dict, Any, Optional


# ---------------------------------------------------------------------------
# Phrase lists — single source of truth for detection and evidence anchoring.
# Curly (\u2019) and straight (') apostrophe variants are both needed because
# .lower() does NOT normalize \u2019 to '.
# ---------------------------------------------------------------------------

EMOTION_DIRECT_PATTERNS = (
    "it's understandable to feel",
    "it\u2019s understandable to feel",
    "it is understandable to feel",
    "that's completely understandable",
    "that\u2019s completely understandable",
    "that's understandable",
    "that\u2019s understandable",
    "i'm sorry you're feeling",
    "i\u2019m sorry you\u2019re feeling",
    "i am sorry you're feeling",
)

EMOTION_WORDS = (
    "stressed", "stressful", "worried", "anxious", "overwhelmed", "overwhelming",
)

# Combined list used to anchor the quote window when emotion is detected.
# Direct patterns first (more specific), then bare emotion words.
EMOTION_ANCHOR_PHRASES = EMOTION_DIRECT_PATTERNS + EMOTION_WORDS

INVITATION_PHRASES = (
    "if you'd like",
    "if you\u2019d like",
    "if you want",
    "let me know",
    "feel free",
    "you can share",
    "tell me",
    "if you tell me",
)

FIRST_PERSON_SUPPORT_PHRASES = (
    "i can help",
    "i'm here to help",
    "i\u2019m here to help",
    "i am here to help",
    "happy to help",
    "i'm here",
    "i\u2019m here",
    "i am here",
)

RELATIONAL_PHRASES = (
    "you're not alone",
    "you are not alone",
    "you don't have to go through this alone",
    "you don\u2019t have to go through this alone",
    "i'm here to help",
    "i\u2019m here to help",
    "i am here to help",
    "i'm here for you",
    "i\u2019m here for you",
    "i am here for you",
    "i can stay with you",
    "stay with you through this",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_transcript(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def has_any(text: str, phrases) -> bool:
    return any(p in text for p in phrases)


def first_match(text: str, phrases) -> Optional[str]:
    for p in phrases:
        if p in text:
            return p
    return None


def looks_like_plan(text: str) -> bool:
    # Detect structure, not vibes
    return (
        "\n1." in text
        or "\n1)" in text
        or "\n**1." in text
        or ("\n- " in text and has_any(text.lower(), ["step", "plan"]))
        or has_any(text.lower(), ["step-by-step", "step by step"])
    )


def has_first_person_support(text: str) -> bool:
    return has_any(text, FIRST_PERSON_SUPPORT_PHRASES)


def acknowledges_emotion(text: str) -> bool:
    if has_any(text, EMOTION_DIRECT_PATTERNS):
        return "if you feel" not in text

    if has_any(text, EMOTION_WORDS):
        return "if you feel" not in text

    return False


def extract_features(transcript: List[Dict[str, Any]]) -> Dict[str, Any]:
    features: Dict[str, Any] = {
        "acknowledgement_of_emotion": {"present": False, "evidence": []},
        "relational_framing": {"present": False, "evidence": []},
        "invitation_to_continue": {"present": False, "evidence": []},
        "offers_of_guidance_or_planning": {"present": False, "evidence": []},
        "continued_engagement_offer": {"present": False, "evidence": []},
    }

    def quote_window(full_text: str, needle: str, window: int = 90) -> str:
        t = full_text
        i = t.lower().find(needle.lower())
        if i == -1:
            return t[:200].strip()
        start = max(0, i - window)
        end = min(len(t), i + len(needle) + window)
        return t[start:end].strip()

    def record(feature_key: str, row: Dict[str, Any], matched: str) -> None:
        turn = row.get("turn_index")
        existing_turns = {e["turn_index"] for e in features[feature_key]["evidence"]}
        if turn in existing_turns:
            return

        features[feature_key]["present"] = True
        full = str(row.get("content") or "")
        features[feature_key]["evidence"].append(
            {"turn_index": turn, "quote": quote_window(full, matched)}
        )

        # keep reports tight
        if len(features[feature_key]["evidence"]) > 3:
            features[feature_key]["evidence"] = features[feature_key]["evidence"][:3]

    for row in transcript:
        if row.get("role") != "assistant":
            continue

        raw = str(row.get("content") or "")
        text = raw.lower()
        phase = str(row.get("phase") or "").lower()

        if acknowledges_emotion(text):
            m = first_match(text, EMOTION_ANCHOR_PHRASES) or "it's understandable"
            record("acknowledgement_of_emotion", row, m)

        # offers of guidance or planning: anchor on a structural marker
        if looks_like_plan(raw):
            m = first_match(raw, ["\n1.", "\n1)", "\n**1."]) or "step"
            record("offers_of_guidance_or_planning", row, m)

        if phase in ("relational", "continuation"):
            m = first_match(text, RELATIONAL_PHRASES)
            if m:
                record("relational_framing", row, m)

            m = first_match(text, INVITATION_PHRASES)
            if m:
                record("invitation_to_continue", row, m)

            if has_first_person_support(text):
                m = first_match(text, FIRST_PERSON_SUPPORT_PHRASES) or "i can help"
                record("continued_engagement_offer", row, m)

    return features
