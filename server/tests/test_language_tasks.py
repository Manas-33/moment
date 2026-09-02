"""Unit tests for pure helper functions in Components/LanguageTasks.py.

These functions do only JSON parsing and list filtering. They make no network
calls, touch no files, and never invoke Claude, ffmpeg, or the Django ORM.
"""

from Components.LanguageTasks import (
    extract_times,
    _extract_multiple_highlights,
    _deduplicate_highlights,
)


def test_extract_times_parses_first_object():
    payload = '[{"start": "12.9", "end": "42.1", "content": "hi"}]'
    assert extract_times(payload) == (12, 42)


def test_extract_times_returns_zeros_on_bad_json():
    # Malformed input should be handled gracefully, not raise.
    assert extract_times("not-json") == (0, 0)


def test_extract_multiple_highlights_sorts_and_drops_invalid():
    payload = (
        '[{"start": 90, "end": 120}, '
        '{"start": 10, "end": 40}, '
        '{"start": 50, "end": 50}]'  # start == end -> dropped
    )
    assert _extract_multiple_highlights(payload) == [(10, 40), (90, 120)]


def test_deduplicate_highlights_removes_near_duplicates():
    highlights = [(0, 30), (35, 60), (200, 230)]
    # (35, 60) starts only 5s after the first ends, below the 10s min gap.
    assert _deduplicate_highlights(highlights, min_gap_seconds=10) == [
        (0, 30),
        (200, 230),
    ]


def test_deduplicate_highlights_empty_input():
    assert _deduplicate_highlights([]) == []
