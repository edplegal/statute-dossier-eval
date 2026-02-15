import os

TARGET_MODEL = os.getenv("TARGET_MODEL", "openai/gpt-4.1")
TEMPERATURE_TARGET = float(os.getenv("TEMPERATURE_TARGET", "0"))
BRANCH_LABEL = os.getenv("BRANCH_LABEL", "ask_for_guidance")

JUDGE_MODEL = os.getenv("JUDGE_MODEL", "openai/gpt-4.1")
TEMPERATURE_JUDGE = float(os.getenv("TEMPERATURE_JUDGE", "0"))

# Path to a conversation scenario YAML, relative to the repository root by default
SCENARIO_PATH = os.getenv(
    "SCENARIO_PATH",
    "src/statute_dossier_eval/data/conversations/a6_landlord_tenant_tree.yaml",
)

# Map model provider prefixes to the env var they require.
_PROVIDER_API_KEYS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
}


def validate_config() -> None:
    """Check that required env vars are set. Call at startup to fail fast."""
    missing = []

    for model_name in (TARGET_MODEL, JUDGE_MODEL):
        provider = model_name.split("/")[0] if "/" in model_name else None
        env_var = _PROVIDER_API_KEYS.get(provider)
        if env_var and not os.getenv(env_var):
            missing.append(env_var)

    if missing:
        # Deduplicate (target and judge may use the same provider)
        unique = sorted(set(missing))
        raise EnvironmentError(
            f"Missing required environment variable(s): {', '.join(unique)}. "
            f"Set them or create a .env file. See .env.example."
        )
