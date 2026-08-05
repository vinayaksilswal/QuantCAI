"""
Contract tests for settings.TIER_LIMITS.

These are pure unit tests — no database, no Redis, no app fixture — so they run
fast and fail loudly in CI.

Motivation: metering_middleware.py read `tier_limits.get("developer_api_requests_daily", 10)`,
a key that exists in no tier. The `.get()` default swallowed the mistake, so every
paid plan silently received the FREE limit of 10 requests/day and Pro customers
began accruing overage charges at request 11 instead of 501. Nothing failed, no
test caught it, and it was only visible as a billing discrepancy.

The last test below scans the source tree so that any future key drift between
the config and its consumers breaks the build instead of the bill.
"""

import re
from pathlib import Path

import pytest

from core.config import settings

BACKEND_DIR = Path(__file__).resolve().parent.parent

# Keys that billing, metering, or quota enforcement index by name. A missing key
# here is a revenue bug, not a crash, which is exactly why it needs a test.
REVENUE_CRITICAL_KEYS = {
    "max_qubits",
    "max_depth",
    "max_shots",
    "noise_models",
    "statevector_access",
    "daily_circuit_runs",
    "daily_ai_chats",
    "monthly_pqc_scans",
    "daily_api_requests",
    "max_concurrent_jobs",
    "max_api_keys",
}

# Limits that must never decrease as a customer pays more.
MONOTONIC_KEYS = [
    "max_qubits",
    "max_shots",
    "daily_circuit_runs",
    "daily_ai_chats",
    "monthly_pqc_scans",
    "daily_api_requests",
    "max_concurrent_jobs",
    "max_api_keys",
]

UPGRADE_PATH = ["FREE", "PRO", "INSTITUTIONAL"]


def test_every_tier_defines_the_same_keys():
    """A key present in one tier but missing from another is a silent fallback."""
    key_sets = {tier: set(limits) for tier, limits in settings.TIER_LIMITS.items()}
    reference_tier, reference_keys = next(iter(key_sets.items()))

    for tier, keys in key_sets.items():
        assert keys == reference_keys, (
            f"Tier '{tier}' key set differs from '{reference_tier}'. "
            f"Missing: {sorted(reference_keys - keys)}. "
            f"Unexpected: {sorted(keys - reference_keys)}."
        )


@pytest.mark.parametrize("tier", sorted(settings.TIER_LIMITS))
def test_revenue_critical_keys_present(tier):
    """Enforcement code indexes these directly; absence means a wrong bill."""
    missing = REVENUE_CRITICAL_KEYS - set(settings.TIER_LIMITS[tier])
    assert not missing, f"Tier '{tier}' is missing revenue-critical keys: {sorted(missing)}"


@pytest.mark.parametrize("key", MONOTONIC_KEYS)
def test_paid_tiers_are_never_more_restrictive_than_free(key):
    """Catches an inverted or typo'd limit that would throttle paying customers."""
    for lower, higher in zip(UPGRADE_PATH, UPGRADE_PATH[1:]):
        lower_value = settings.TIER_LIMITS[lower][key]
        higher_value = settings.TIER_LIMITS[higher][key]
        assert higher_value >= lower_value, (
            f"'{key}' decreases from {lower} ({lower_value}) to {higher} "
            f"({higher_value}) — a paying customer would get less than a free one."
        )


def test_free_tier_is_actually_limited():
    """The paywall only works if the free tier is genuinely constrained."""
    free = settings.TIER_LIMITS["FREE"]
    assert free["statevector_access"] is False
    assert list(free["noise_models"]) == ["ideal"], (
        "Free tier must not include paid noise models — they are the Pro upgrade hook."
    )
    assert free["max_qubits"] < settings.TIER_LIMITS["PRO"]["max_qubits"]
    assert free["max_shots"] < settings.TIER_LIMITS["PRO"]["max_shots"]


def test_no_consumer_references_an_undefined_tier_limit_key():
    """
    Scan the backend for `tier_limits["x"]` / `tier_limits.get("x")` style access
    and assert every key referenced actually exists in the config.

    This is the guard that would have caught the metering bug at commit time.
    """
    pattern = re.compile(
        r"""(?:tier_limits|plan_limits)\s*(?:\[\s*|\.get\(\s*)['"]([a-zA-Z_][a-zA-Z0-9_]*)['"]"""
    )

    valid_keys = set()
    for limits in settings.TIER_LIMITS.values():
        valid_keys.update(limits)

    offenders: list[str] = []
    for path in BACKEND_DIR.rglob("*.py"):
        # Skip vendored code, migrations, and this test itself.
        parts = set(path.parts)
        if parts & {".venv", "node_modules", "migrations", "__pycache__"}:
            continue
        if path.name == Path(__file__).name:
            continue

        try:
            source = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        for line_no, line in enumerate(source.splitlines(), start=1):
            for key in pattern.findall(line):
                if key not in valid_keys:
                    rel = path.relative_to(BACKEND_DIR)
                    offenders.append(f"{rel}:{line_no} references unknown key '{key}'")

    assert not offenders, (
        "Code references TIER_LIMITS keys that do not exist in core.config.settings:\n  "
        + "\n  ".join(offenders)
    )
