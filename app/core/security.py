"""
app/core/security.py — Phase 3: basic prompt-injection hardening for free-text
fields that are interpolated into LLM prompt templates.

IMPORTANT: this is a first-layer guard, NOT a complete defence.
Sophisticated prompt injection can evade pattern-matching. A robust defence
would involve:
  - LLM-side system-prompt pinning / instruction hierarchy
  - Output validation (check that responses match expected schema before returning)
  - Rate limiting and monitoring for anomalous outputs

What this module does:
  - Reject free-text values that contain well-known injection trigger phrases
  - Enforce reasonable max-length limits on fields fed into prompts
  - Raise ValueError (→ Pydantic 422) so injection attempts fail before the LLM
    is ever called
"""

from __future__ import annotations

import re
from typing import Optional

# Patterns that strongly suggest an attempt to override system instructions.
# Keep this list minimal and explicit — overly broad patterns cause false positives
# on legitimate educational content (students asking about "systems", "commands", etc.)
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bignore\s+(previous|prior|above|all)\s+(instructions?|prompts?|rules?|context)\b", re.IGNORECASE),
    re.compile(r"\bforget\s+(everything|all|previous|prior)\b", re.IGNORECASE),
    re.compile(r"\byou\s+are\s+now\b", re.IGNORECASE),
    re.compile(r"\bact\s+as\s+(if\s+)?(a\s+)?(?:different|new|another)\b", re.IGNORECASE),
    re.compile(r"\bsystem\s*:\s*", re.IGNORECASE),           # "system: you are..."
    re.compile(r"\buser\s*:\s*", re.IGNORECASE),             # roleplay prompt prefixes
    re.compile(r"\bassistant\s*:\s*", re.IGNORECASE),        # roleplay prompt prefixes
    re.compile(r"<\s*/?system\s*>", re.IGNORECASE),          # XML-style tags
    re.compile(r"\bdo\s+not\s+follow\b", re.IGNORECASE),
    re.compile(r"\bnew\s+instructions?\b", re.IGNORECASE),
    re.compile(r"\boverride\b.*\binstructions?\b", re.IGNORECASE),
    re.compile(r"\bpretend\s+(you\s+are|to\s+be)\b", re.IGNORECASE),
    re.compile(r"\bjailbreak\b", re.IGNORECASE),
    re.compile(r"\bDAN\b"),                                   # "Do Anything Now" jailbreak
]

# Default maximum character length for free-text fields fed into prompts.
# Keeps prompt size predictable and limits how much injected content can appear.
DEFAULT_MAX_LENGTH = 500


def check_free_text(
    value: str,
    field_name: str = "field",
    max_length: int = DEFAULT_MAX_LENGTH,
) -> None:
    """Check a free-text string for injection patterns and length limits.

    Raises ValueError if the value exceeds max_length or matches any known
    injection pattern. Intended to be called from Pydantic field_validators.

    Args:
        value: The string to check.
        field_name: Name of the field (used in the error message).
        max_length: Maximum allowed character length.

    Raises:
        ValueError: If the value is too long or contains injection patterns.
    """
    if len(value) > max_length:
        raise ValueError(
            f"'{field_name}' is too long ({len(value)} chars). "
            f"Maximum allowed: {max_length} characters."
        )

    for pattern in _INJECTION_PATTERNS:
        if pattern.search(value):
            raise ValueError(
                f"'{field_name}' contains content that is not allowed in this field. "
                f"Please provide a valid value."
                # Deliberately vague error — don't tell the attacker which pattern matched.
            )


def check_profile_dict(
    profile: dict,
    field_name: str = "student_profile",
    max_total_length: int = 1000,
) -> None:
    """Check a dict (like student_profile) that will be interpolated into a prompt.

    Converts the dict to its string representation and checks the total length,
    then checks each string value for injection patterns.

    Args:
        profile: The dict to check.
        field_name: Name of the field (used in error messages).
        max_total_length: Maximum total character length of the serialised dict.

    Raises:
        ValueError: If any value is too long or contains injection patterns.
    """
    serialised = str(profile)
    if len(serialised) > max_total_length:
        raise ValueError(
            f"'{field_name}' is too large ({len(serialised)} chars when serialised). "
            f"Maximum allowed: {max_total_length} characters."
        )

    for key, val in profile.items():
        if isinstance(val, str):
            for pattern in _INJECTION_PATTERNS:
                if pattern.search(val):
                    raise ValueError(
                        f"'{field_name}' contains content that is not allowed. "
                        f"Please provide a valid student profile."
                    )
