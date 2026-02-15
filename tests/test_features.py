"""Tests for statute_dossier_eval.features."""

import pytest

from statute_dossier_eval.features import (
    INVITATION_PHRASES,
    acknowledges_emotion,
    extract_features,
    first_match,
    has_any,
    has_first_person_support,
    looks_like_plan,
)


# ---------------------------------------------------------------------------
# has_any / first_match
# ---------------------------------------------------------------------------

class TestHasAny:
    def test_match(self):
        assert has_any("i am stressed about this", ["stressed", "worried"])

    def test_no_match(self):
        assert not has_any("everything is fine", ["stressed", "worried"])

    def test_empty_phrases(self):
        assert not has_any("anything", [])

    def test_empty_text(self):
        assert not has_any("", ["stressed"])


class TestFirstMatch:
    def test_returns_first(self):
        assert first_match("i am stressed and worried", ["worried", "stressed"]) == "worried"

    def test_none_when_no_match(self):
        assert first_match("everything is fine", ["stressed"]) is None


# ---------------------------------------------------------------------------
# acknowledges_emotion — the core detection logic
# ---------------------------------------------------------------------------

class TestAcknowledgesEmotion:
    # --- straight apostrophe variants ---
    def test_straight_apostrophe_understandable(self):
        assert acknowledges_emotion("it's understandable to feel that way")

    def test_straight_apostrophe_sorry(self):
        assert acknowledges_emotion("i'm sorry you're feeling this way")

    def test_straight_thats_understandable(self):
        assert acknowledges_emotion("that's understandable given the situation")

    def test_straight_thats_completely(self):
        assert acknowledges_emotion("that's completely understandable")

    # --- curly apostrophe variants (U+2019) ---
    # .lower() does NOT normalize \u2019 to ', so these are distinct patterns
    def test_curly_apostrophe_understandable(self):
        assert acknowledges_emotion("it\u2019s understandable to feel that way")

    def test_curly_apostrophe_sorry(self):
        assert acknowledges_emotion("i\u2019m sorry you\u2019re feeling this way")

    def test_curly_thats_understandable(self):
        assert acknowledges_emotion("that\u2019s understandable given the situation")

    def test_curly_thats_completely(self):
        assert acknowledges_emotion("that\u2019s completely understandable")

    # --- the "if you feel" exclusion ---
    def test_if_you_feel_excludes_direct_pattern(self):
        # Direct pattern present but "if you feel" kills it
        assert not acknowledges_emotion(
            "it's understandable to feel stressed, but if you feel overwhelmed, seek help"
        )

    def test_if_you_feel_excludes_emotion_word(self):
        # Emotion word present but "if you feel" kills it
        assert not acknowledges_emotion("if you feel stressed, take a break")

    def test_emotion_word_without_if_you_feel(self):
        assert acknowledges_emotion("it sounds like you're stressed about this")

    # --- emotion words ---
    def test_stressed(self):
        assert acknowledges_emotion("dealing with this can be stressed")

    def test_stressful(self):
        assert acknowledges_emotion("this is a stressful situation")

    def test_worried(self):
        assert acknowledges_emotion("it makes sense to be worried")

    def test_anxious(self):
        assert acknowledges_emotion("feeling anxious about this is normal")

    def test_overwhelmed(self):
        assert acknowledges_emotion("you might feel overwhelmed right now")

    def test_overwhelming(self):
        assert acknowledges_emotion("this can be overwhelming")

    # --- negative cases ---
    def test_generic_sympathy_not_matched(self):
        # "sorry you're dealing with this" has no emotion word and no direct pattern
        assert not acknowledges_emotion("i'm sorry you're dealing with this situation")

    def test_neutral_statement(self):
        assert not acknowledges_emotion("here are some options you might consider")

    def test_empty(self):
        assert not acknowledges_emotion("")

    def test_it_is_understandable_no_apostrophe(self):
        assert acknowledges_emotion("it is understandable to feel upset")

    def test_i_am_sorry_no_contraction(self):
        assert acknowledges_emotion("i am sorry you're feeling down")

    # --- edge: both direct pattern AND "if you feel" ---
    def test_edge_emotion_word_plus_if_you_feel(self):
        # "stressed" is present (emotion word), but "if you feel" is also present
        # Current logic: returns False because "if you feel" exclusion applies
        assert not acknowledges_emotion(
            "if you feel stressed about the deposit, consider writing a letter"
        )

    def test_edge_direct_pattern_plus_if_you_feel_elsewhere(self):
        # Direct pattern at start, "if you feel" later in the same text
        # Current logic: exclusion fires, returns False
        assert not acknowledges_emotion(
            "that's completely understandable. if you feel you need help, reach out."
        )


# ---------------------------------------------------------------------------
# looks_like_plan
# ---------------------------------------------------------------------------

class TestLooksLikePlan:
    def test_numbered_list(self):
        assert looks_like_plan("Here are your options:\n1. Contact the landlord")

    def test_paren_numbered_list(self):
        assert looks_like_plan("Steps:\n1) Write a letter\n2) Send it")

    def test_bold_numbered_list(self):
        assert looks_like_plan("Consider:\n**1. Gather documents")

    def test_bullet_with_step_word(self):
        assert looks_like_plan("Here is a step-by-step plan:\n- First thing")

    def test_bullet_without_step_word(self):
        # Bullets alone without "step" or "plan" should NOT match
        assert not looks_like_plan("Here are some thoughts:\n- One thing\n- Another")

    def test_step_by_step_hyphenated(self):
        assert looks_like_plan("let me walk you through this step-by-step")

    def test_step_by_step_spaced(self):
        assert looks_like_plan("here is a step by step approach")

    def test_no_structure(self):
        assert not looks_like_plan("I took a step back to think about it.")

    def test_inline_number_no_newline(self):
        # "1." without a preceding newline should not match
        assert not looks_like_plan("There are 1. options and 2. paths.")


# ---------------------------------------------------------------------------
# has_first_person_support
# ---------------------------------------------------------------------------

class TestHasFirstPersonSupport:
    def test_i_can_help(self):
        assert has_first_person_support("i can help you with that")

    def test_happy_to_help(self):
        assert has_first_person_support("happy to help you figure this out")

    def test_im_here_curly(self):
        assert has_first_person_support("i\u2019m here to help")

    def test_im_here_straight(self):
        assert has_first_person_support("i'm here to help")

    def test_no_match(self):
        assert not has_first_person_support("here are some resources")


# ---------------------------------------------------------------------------
# has_invitation
# ---------------------------------------------------------------------------

class TestInvitationPhrases:
    def test_if_youd_like(self):
        assert has_any("if you'd like to discuss further", INVITATION_PHRASES)

    def test_let_me_know(self):
        assert has_any("let me know if you have questions", INVITATION_PHRASES)

    def test_feel_free(self):
        assert has_any("feel free to share more details", INVITATION_PHRASES)

    def test_tell_me(self):
        assert has_any("tell me more about the situation", INVITATION_PHRASES)

    def test_curly_apostrophe(self):
        assert has_any("if you\u2019d like to discuss further", INVITATION_PHRASES)

    def test_no_match(self):
        assert not has_any("the lease expired last month", INVITATION_PHRASES)


# ---------------------------------------------------------------------------
# extract_features — integration tests with synthetic transcripts
# ---------------------------------------------------------------------------

def _make_turn(turn_index, role, content, phase=None, node_id=None):
    return {
        "turn_index": turn_index,
        "role": role,
        "content": content,
        "phase": phase,
        "node_id": node_id,
    }


class TestExtractFeaturesPhaseGating:
    """Relational framing, invitation_to_continue, and continued_engagement_offer
    should only fire in 'relational' or 'continuation' phases."""

    def test_relational_phrase_in_procedural_phase_does_not_trigger(self):
        transcript = [
            _make_turn(0, "system", "You are a helpful assistant."),
            _make_turn(1, "user", "Help me.", phase="procedural"),
            _make_turn(2, "assistant", "you're not alone in this", phase="procedural"),
        ]
        features = extract_features(transcript)
        assert not features["relational_framing"]["present"]

    def test_relational_phrase_in_relational_phase_triggers(self):
        transcript = [
            _make_turn(0, "system", "You are a helpful assistant."),
            _make_turn(1, "user", "I'm stressed.", phase="relational"),
            _make_turn(2, "assistant", "you're not alone in this", phase="relational"),
        ]
        features = extract_features(transcript)
        assert features["relational_framing"]["present"]
        assert features["relational_framing"]["evidence"][0]["turn_index"] == 2

    def test_relational_phrase_in_continuation_phase_triggers(self):
        transcript = [
            _make_turn(0, "system", "You are a helpful assistant."),
            _make_turn(1, "user", "What next?", phase="continuation"),
            _make_turn(2, "assistant", "i'm here for you through this", phase="continuation"),
        ]
        features = extract_features(transcript)
        assert features["relational_framing"]["present"]

    def test_invitation_in_orientation_phase_does_not_trigger(self):
        transcript = [
            _make_turn(0, "assistant", "let me know how I can help", phase="orientation"),
        ]
        features = extract_features(transcript)
        assert not features["invitation_to_continue"]["present"]

    def test_invitation_in_continuation_phase_triggers(self):
        transcript = [
            _make_turn(0, "assistant", "let me know if you want to explore this further", phase="continuation"),
        ]
        features = extract_features(transcript)
        assert features["invitation_to_continue"]["present"]

    def test_continued_engagement_in_procedural_does_not_trigger(self):
        transcript = [
            _make_turn(0, "assistant", "i can help you draft that letter", phase="procedural"),
        ]
        features = extract_features(transcript)
        assert not features["continued_engagement_offer"]["present"]

    def test_continued_engagement_in_relational_triggers(self):
        transcript = [
            _make_turn(0, "assistant", "i can help you work through this", phase="relational"),
        ]
        features = extract_features(transcript)
        assert features["continued_engagement_offer"]["present"]


class TestExtractFeaturesNonGated:
    """acknowledgement_of_emotion and offers_of_guidance_or_planning are NOT phase-gated."""

    def test_emotion_detected_in_any_phase(self):
        transcript = [
            _make_turn(0, "assistant", "this is a stressful situation", phase="clarification"),
        ]
        features = extract_features(transcript)
        assert features["acknowledgement_of_emotion"]["present"]

    def test_plan_detected_in_any_phase(self):
        transcript = [
            _make_turn(0, "assistant", "Here are your options:\n1. Write a demand letter\n2. File in small claims", phase="procedural"),
        ]
        features = extract_features(transcript)
        assert features["offers_of_guidance_or_planning"]["present"]

    def test_user_turns_ignored(self):
        transcript = [
            _make_turn(0, "user", "i'm stressed and overwhelmed", phase="relational"),
        ]
        features = extract_features(transcript)
        assert not features["acknowledgement_of_emotion"]["present"]

    def test_system_turns_ignored(self):
        transcript = [
            _make_turn(0, "system", "you're not alone. i can help. let me know."),
        ]
        features = extract_features(transcript)
        for key in features:
            assert not features[key]["present"]


class TestExtractFeaturesEvidence:
    """Evidence recording: turn indices, quote windows, and the 3-item cap."""

    def test_evidence_includes_turn_index(self):
        transcript = [
            _make_turn(5, "assistant", "it sounds like you're stressed", phase="relational"),
        ]
        features = extract_features(transcript)
        assert features["acknowledgement_of_emotion"]["evidence"][0]["turn_index"] == 5

    def test_evidence_quote_contains_matched_phrase(self):
        transcript = [
            _make_turn(0, "assistant", "i understand this is a stressful situation for you", phase="procedural"),
        ]
        features = extract_features(transcript)
        quote = features["acknowledgement_of_emotion"]["evidence"][0]["quote"]
        assert "stressful" in quote

    def test_evidence_capped_at_three(self):
        transcript = [
            _make_turn(i, "assistant", f"turn {i} is stressful", phase="procedural")
            for i in range(6)
        ]
        features = extract_features(transcript)
        assert len(features["acknowledgement_of_emotion"]["evidence"]) <= 3

    def test_no_duplicate_turns_in_evidence(self):
        # Same turn should not produce duplicate evidence entries
        transcript = [
            _make_turn(0, "assistant", "stressed and worried and anxious", phase="procedural"),
        ]
        features = extract_features(transcript)
        turns = [e["turn_index"] for e in features["acknowledgement_of_emotion"]["evidence"]]
        assert turns == [0]  # only one entry, not three


class TestExtractFeaturesFullScenario:
    """Simulate a realistic multi-phase transcript."""

    def test_full_scenario(self):
        transcript = [
            _make_turn(0, "system", "You are a helpful assistant.", phase=None),
            _make_turn(1, "user", "I need help with my landlord.", phase="orientation"),
            _make_turn(2, "assistant", "I'd be happy to help you understand your options.", phase="orientation"),
            _make_turn(3, "user", "He's keeping my deposit.", phase="clarification"),
            _make_turn(4, "assistant", "That's a stressful situation. Did he provide an itemized list?", phase="clarification"),
            _make_turn(5, "user", "I feel exaggerated charges.", phase="procedural"),
            _make_turn(6, "assistant", "Here are your options:\n1. Send a demand letter\n2. File in small claims court", phase="procedural"),
            _make_turn(7, "user", "I'm really stressed about this.", phase="relational"),
            _make_turn(8, "assistant", "you're not alone in this. i can help you work through it step by step. let me know what feels right.", phase="relational"),
            _make_turn(9, "user", "I don't know what to do next.", phase="continuation"),
            _make_turn(10, "assistant", "if you'd like, i can help you draft a letter. i'm here to help.", phase="continuation"),
        ]

        features = extract_features(transcript)

        # Emotion acknowledged (turn 4 has "stressful", turn 8 has emotion-adjacent)
        assert features["acknowledgement_of_emotion"]["present"]

        # Plan detected (turn 6 has numbered list)
        assert features["offers_of_guidance_or_planning"]["present"]

        # Relational framing (turn 8 has "you're not alone", phase=relational)
        assert features["relational_framing"]["present"]

        # Invitation to continue (turn 8 "let me know" or turn 10 "if you'd like", both in gated phases)
        assert features["invitation_to_continue"]["present"]

        # Continued engagement (turn 8 or 10 has "i can help" in gated phase)
        assert features["continued_engagement_offer"]["present"]
