#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug utilities

Centralized, opt-in debug printing with timestamps and consistent formatting.
Only emits output when explicitly enabled (e.g., via --debug CLI flag).
"""

from __future__ import annotations

import datetime as _dt
from typing import Any, Dict

from .colors import Colors

_DEBUG_ENABLED = False


def enable_debug(enabled: bool = True) -> None:
    """Enable or disable debug output globally."""
    global _DEBUG_ENABLED
    _DEBUG_ENABLED = bool(enabled)


def is_enabled() -> bool:
    """Return True if debug output is enabled."""
    return _DEBUG_ENABLED


def dprint(msg: Any, *, tag: str | None = None) -> None:
    """Print a single debug line if enabled.

    - Prefixes with timestamp and optional tag
    - Uses dim/gray color for readability
    """
    if not _DEBUG_ENABLED:
        return
    ts = _dt.datetime.now().strftime('%H:%M:%S')
    prefix = f"[{ts}] [DEBUG]"
    if tag:
        prefix += f"[{tag}]"
    print(Colors.debug(f"{prefix} {msg}"))


def mask_secret(value: str | None, *, shown: int = 0) -> str:
    """Return a masked representation of secrets like passwords/tokens."""
    if not value:
        return "<not set>"
    if shown <= 0:
        return "***"
    head = value[:max(0, shown)]
    return f"{head}***"


def dump_config(config: Dict[str, Any]) -> None:
    """Emit a curated, masked view of the effective configuration for debugging."""
    if not _DEBUG_ENABLED:
        return
    safe = dict(config)
    # Mask sensitive fields
    if 'password' in safe:
        safe['password'] = mask_secret(safe.get('password'))
    # Compose readable lines (avoid dumping huge structures)
    keys_of_interest = [
        'server', 'port', 'use_ssl', 'username', 'password', 'mailbox',
        'search_criteria', 'recursive', 'limit', 'limit_per_folder',
        'total_limit', 'save_metadata', 'organize_by_sender', 'organize_by_date',
        'allowed_extensions', 'excluded_extensions', 'save_path',
    ]
    dprint("Effective configuration:", tag="CFG")
    for k in keys_of_interest:
        if k in safe:
            dprint(f"{k}: {safe[k]}", tag="CFG")

