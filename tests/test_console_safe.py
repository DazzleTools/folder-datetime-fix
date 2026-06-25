"""Regression tests for cp1252-safe console output.

The CLI printed emoji (📁 📄 💡) and Unicode box-drawing chars (├── └── │).
On a legacy Windows console (cp1252/cp437) those raise UnicodeEncodeError and
crash the tool. console_safe falls back to ASCII when the active stdout stream
cannot encode a glyph. These tests fake the stream encoding so they verify the
fallback deterministically on any platform/Python.
"""
import sys

from folder_datetime_fix.console_safe import icon, stream_can_encode


class _FakeStream:
    """Minimal stdout stand-in with a fixed encoding (or None)."""
    def __init__(self, encoding):
        self.encoding = encoding


def test_stream_can_encode_utf8():
    assert stream_can_encode("📁", _FakeStream("utf-8")) is True
    assert stream_can_encode("├── ", _FakeStream("utf-8")) is True


def test_stream_can_encode_cp1252_rejects_glyphs():
    assert stream_can_encode("📁", _FakeStream("cp1252")) is False
    assert stream_can_encode("├── ", _FakeStream("cp1252")) is False
    # Plain ASCII still encodes fine on cp1252.
    assert stream_can_encode("[DIR]", _FakeStream("cp1252")) is True


def test_stream_can_encode_handles_missing_encoding():
    # encoding=None must be treated as ascii, not crash.
    assert stream_can_encode("📁", _FakeStream(None)) is False
    assert stream_can_encode("plain", _FakeStream(None)) is True


def test_icon_keeps_glyph_on_utf8(monkeypatch):
    monkeypatch.setattr(sys, "stdout", _FakeStream("utf-8"))
    assert icon("📁", "[DIR]") == "📁"


def test_icon_falls_back_on_cp1252(monkeypatch):
    monkeypatch.setattr(sys, "stdout", _FakeStream("cp1252"))
    assert icon("📁", "[DIR]") == "[DIR]"
    assert icon("💡 ", "") == ""


def test_icon_force_ascii_overrides():
    assert icon("📁", "[DIR]", force_ascii=True) == "[DIR]"


def test_tree_visualizer_falls_back_to_ascii_on_cp1252(monkeypatch):
    """TreeVisualizer(use_unicode=True) must still emit ASCII box chars when the
    console can't encode the Unicode ones -- otherwise the tree output crashes."""
    monkeypatch.setattr(sys, "stdout", _FakeStream("cp1252"))
    from folder_datetime_fix.tree_visualizer import TreeVisualizer
    tv = TreeVisualizer(use_unicode=True)
    assert tv.chars == TreeVisualizer.TREE_CHARS_ASCII


def test_tree_visualizer_uses_unicode_on_utf8(monkeypatch):
    monkeypatch.setattr(sys, "stdout", _FakeStream("utf-8"))
    from folder_datetime_fix.tree_visualizer import TreeVisualizer
    tv = TreeVisualizer(use_unicode=True)
    assert tv.chars == TreeVisualizer.TREE_CHARS
