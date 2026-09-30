"""Shared HTML parsing utilities for job source adapters.

This module provides safe, deterministic parsing helpers used by HTML-based
source adapters. It does NOT implement any scraping logic — callers pass
already-fetched HTML and extract specific elements.

All parsing is done with BeautifulSoup (lxml parser) and respects:
- No CAPTCHA bypass
- No anti-bot evasion
- No rate-limit circumvention
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from bs4 import BeautifulSoup


def parse_html(html: str) -> BeautifulSoup:
    """Parse HTML content into a BeautifulSoup tree."""
    return BeautifulSoup(html, "lxml")


def clean_text(text: Optional[str]) -> Optional[str]:
    """Strip whitespace, normalize newlines, and collapse spaces in text."""
    if not text:
        return None
    cleaned = " ".join(text.split())
    return cleaned if cleaned else None


def parse_date_flexible(text: Optional[str]) -> Optional[datetime]:
    """Attempt to parse a date string in multiple common formats.

    Returns a timezone-aware UTC datetime or None if parsing fails.
    This is intentionally conservative — returns None rather than
    guessing wrong.
    """
    if not text:
        return None

    text = text.strip()
    formats = [
        "%d %b %Y",          # 15 Jan 2024
        "%d %B %Y",          # 15 January 2024
        "%Y-%m-%d",           # 2024-01-15
        "%d/%m/%Y",           # 15/01/2024
        "%m/%d/%Y",           # 01/15/2024
        "%d-%m-%Y",           # 15-01-2024
        "%B %d, %Y",          # January 15, 2024
        "%b %d, %Y",          # Jan 15, 2024
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(text, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return None
