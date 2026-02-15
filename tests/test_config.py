"""Tests for statute_dossier_eval.config.validate_config."""

import os

import pytest


def test_validate_config_passes_when_key_set(monkeypatch):
    monkeypatch.setattr("statute_dossier_eval.config.TARGET_MODEL", "openai/gpt-4.1")
    monkeypatch.setattr("statute_dossier_eval.config.JUDGE_MODEL", "openai/gpt-4.1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    from statute_dossier_eval.config import validate_config
    validate_config()  # should not raise


def test_validate_config_raises_when_key_missing(monkeypatch):
    monkeypatch.setattr("statute_dossier_eval.config.TARGET_MODEL", "openai/gpt-4.1")
    monkeypatch.setattr("statute_dossier_eval.config.JUDGE_MODEL", "openai/gpt-4.1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    from statute_dossier_eval.config import validate_config
    with pytest.raises(EnvironmentError, match="OPENAI_API_KEY"):
        validate_config()


def test_validate_config_unknown_provider_does_not_raise(monkeypatch):
    monkeypatch.setattr("statute_dossier_eval.config.TARGET_MODEL", "custom/my-model")
    monkeypatch.setattr("statute_dossier_eval.config.JUDGE_MODEL", "custom/my-model")

    from statute_dossier_eval.config import validate_config
    validate_config()  # unknown provider, no key to check


def test_validate_config_no_slash_in_model_does_not_raise(monkeypatch):
    monkeypatch.setattr("statute_dossier_eval.config.TARGET_MODEL", "local-model")
    monkeypatch.setattr("statute_dossier_eval.config.JUDGE_MODEL", "local-model")

    from statute_dossier_eval.config import validate_config
    validate_config()  # no provider prefix, nothing to validate


def test_validate_config_anthropic_key(monkeypatch):
    monkeypatch.setattr("statute_dossier_eval.config.TARGET_MODEL", "anthropic/claude-3")
    monkeypatch.setattr("statute_dossier_eval.config.JUDGE_MODEL", "anthropic/claude-3")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    from statute_dossier_eval.config import validate_config
    with pytest.raises(EnvironmentError, match="ANTHROPIC_API_KEY"):
        validate_config()
