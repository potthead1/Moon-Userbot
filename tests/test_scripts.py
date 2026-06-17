"""Tests for utils/scripts.py — pure/utility functions."""

import sys
from io import BytesIO
from types import SimpleNamespace

import pytest
from PIL import Image

# conftest.py has already injected the fake modules into sys.modules.

from utils.scripts import (
    META_COMMENTS,
    ReplyCheck,
    format_module_help,
    format_small_module_help,
    get_text,
    humanbytes,
    parse_meta_comments,
    resize_image,
    text,
    time_formatter,
)

# Grab the shared modules_help dict that scripts.py imported at load time.
_modules_help = sys.modules["utils.misc"].modules_help


# ── time_formatter ────────────────────────────────────────────────────────


class TestTimeFormatter:
    def test_zero(self):
        assert time_formatter(0) == ""

    def test_only_milliseconds(self):
        assert time_formatter(500) == "500 millisecond(s)"

    def test_seconds(self):
        result = time_formatter(5000)
        assert "5 second(s)" in result

    def test_minutes(self):
        result = time_formatter(90_000)  # 1 min 30 s
        assert "1 minute(s)" in result
        assert "30 second(s)" in result

    def test_hours(self):
        result = time_formatter(3_661_000)  # 1h 1m 1s
        assert "1 hour(s)" in result
        assert "1 minute(s)" in result
        assert "1 second(s)" in result

    def test_days(self):
        result = time_formatter(86_400_000)  # exactly 1 day
        assert "1 day(s)" in result

    def test_composite(self):
        ms = (2 * 86400 + 3 * 3600 + 4 * 60 + 5) * 1000 + 678
        result = time_formatter(ms)
        assert "2 day(s)" in result
        assert "3 hour(s)" in result
        assert "4 minute(s)" in result
        assert "5 second(s)" in result
        assert "678 millisecond(s)" in result


# ── humanbytes ────────────────────────────────────────────────────────────


class TestHumanbytes:
    def test_zero(self):
        assert humanbytes(0) == ""

    def test_none(self):
        assert humanbytes(None) == ""

    def test_bytes(self):
        assert humanbytes(500) == "500 B"

    def test_kibibytes(self):
        result = humanbytes(2048)
        assert "KiB" in result

    def test_mebibytes(self):
        result = humanbytes(2 * 1024 * 1024)
        assert "MiB" in result

    def test_gibibytes(self):
        result = humanbytes(5 * 1024 ** 3)
        assert "GiB" in result

    def test_tebibytes(self):
        result = humanbytes(2 * 1024 ** 4)
        assert "TiB" in result


# ── get_text ──────────────────────────────────────────────────────────────


def _make_message(text_val):
    msg = SimpleNamespace()
    msg.text = text_val
    return msg


class TestGetText:
    def test_none_text(self):
        assert get_text(_make_message(None)) is None

    def test_no_space(self):
        assert get_text(_make_message(".ping")) is None

    def test_with_args(self):
        assert get_text(_make_message(".cmd arg1 arg2")) == "arg1 arg2"

    def test_trailing_space_returns_none(self):
        # str.split(None, 1) on ".cmd " produces [".cmd"] → IndexError → None
        assert get_text(_make_message(".cmd ")) is None


# ── text() helper ─────────────────────────────────────────────────────────


class TestTextHelper:
    def test_returns_text(self):
        msg = SimpleNamespace(text="hello", caption=None)
        assert text(msg) == "hello"

    def test_returns_caption(self):
        msg = SimpleNamespace(text=None, caption="cap")
        assert text(msg) == "cap"

    def test_prefers_text(self):
        msg = SimpleNamespace(text="txt", caption="cap")
        assert text(msg) == "txt"


# ── parse_meta_comments ──────────────────────────────────────────────────


class TestParseMetaComments:
    def test_empty(self):
        assert parse_meta_comments("print('hello')") == {}

    def test_single_meta(self):
        code = "# meta requires : requests aiohttp\n"
        result = parse_meta_comments(code)
        assert result == {"requires": "requests aiohttp"}

    def test_no_match(self):
        code = "# this is just a comment"
        assert parse_meta_comments(code) == {}


# ── format_module_help / format_small_module_help ────────────────────────


class TestFormatModuleHelp:
    def setup_method(self):
        _modules_help["testmod"] = {
            "cmd1": "does thing one",
            "cmd2 [arg]": "does thing two",
        }

    def teardown_method(self):
        _modules_help.pop("testmod", None)

    def test_format_module_help_full(self):
        result = format_module_help("testmod", full=True)
        assert "|testmod|" in result
        assert ".cmd1" in result
        assert ".cmd2" in result
        assert "does thing one" in result

    def test_format_module_help_not_full(self):
        result = format_module_help("testmod", full=False)
        assert "|testmod|" not in result
        assert "Usage:" in result

    def test_format_small_module_help_full(self):
        result = format_small_module_help("testmod", full=True)
        assert "|testmod|" in result
        assert ".cmd1" in result

    def test_format_small_module_help_not_full(self):
        result = format_small_module_help("testmod", full=False)
        assert "|testmod|" not in result


# ── resize_image ─────────────────────────────────────────────────────────


class TestResizeImage:
    @staticmethod
    def _create_image(w, h, fmt="PNG"):
        buf = BytesIO()
        Image.new("RGB", (w, h), color="red").save(buf, fmt)
        buf.seek(0)
        return buf

    def test_square_image(self):
        inp = self._create_image(1024, 1024)
        out = resize_image(inp)
        img = Image.open(out)
        assert img.size == (512, 512)

    def test_landscape_image(self):
        inp = self._create_image(1024, 512)
        out = resize_image(inp)
        img = Image.open(out)
        assert img.size[0] == 512
        assert img.size[1] == 256

    def test_portrait_image(self):
        inp = self._create_image(512, 1024)
        out = resize_image(inp)
        img = Image.open(out)
        assert img.size[0] == 256
        assert img.size[1] == 512

    def test_custom_size(self):
        inp = self._create_image(200, 200)
        out = resize_image(inp, size=256)
        img = Image.open(out)
        assert img.size == (256, 256)

    def test_explicit_size2(self):
        inp = self._create_image(200, 200)
        out = resize_image(inp, size=100, size2=200)
        img = Image.open(out)
        assert img.size == (100, 200)


# ── ReplyCheck ───────────────────────────────────────────────────────────


class TestReplyCheck:
    def test_with_reply(self):
        reply = SimpleNamespace(id=42)
        msg = SimpleNamespace(reply_to_message=reply, from_user=SimpleNamespace(is_self=True))
        assert ReplyCheck(msg) == 42

    def test_without_reply_from_self(self):
        msg = SimpleNamespace(reply_to_message=None, from_user=SimpleNamespace(is_self=True))
        assert ReplyCheck(msg) is None

    def test_without_reply_from_other(self):
        msg = SimpleNamespace(reply_to_message=None, from_user=SimpleNamespace(is_self=False), id=99)
        assert ReplyCheck(msg) == 99
