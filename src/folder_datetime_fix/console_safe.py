"""Console encoding helpers -- keep CLI output safe on legacy code pages.

Windows' default console code page (cp1252 / cp437) cannot encode emoji or
box-drawing glyphs; printing them raises UnicodeEncodeError and crashes the
CLI. These helpers fall back to an ASCII alternative when the active stdout
stream cannot encode a given glyph, while keeping the nicer glyph on UTF-8
terminals (Windows Terminal, macOS, Linux).
"""
import sys


def stream_can_encode(text, stream=None):
    """Return True if ``text`` can be encoded by ``stream`` (default sys.stdout)."""
    if stream is None:
        stream = sys.stdout
    encoding = getattr(stream, "encoding", None) or "ascii"
    try:
        text.encode(encoding)
        return True
    except (UnicodeEncodeError, LookupError):
        return False


def icon(glyph, ascii_fallback, force_ascii=False):
    """Return ``glyph`` if stdout can encode it (and not ``force_ascii``), else ``ascii_fallback``."""
    if force_ascii:
        return ascii_fallback
    return glyph if stream_can_encode(glyph) else ascii_fallback
