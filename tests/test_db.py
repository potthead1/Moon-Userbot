"""Tests for utils/db.py — SqliteDatabase."""

import json
import sqlite3

import pytest

# conftest.py has set up fake utils.config in sys.modules.
# We import the real SqliteDatabase class directly from the source file
# to avoid the module-level `db = ...` instantiation in utils/db.py.
import importlib
import sys

# Force-reload utils.db so we get the real SqliteDatabase class (conftest put a
# stub in sys.modules to satisfy other imports at collection time).
_saved = sys.modules.pop("utils.db", None)
import utils.db as _real_db_mod

SqliteDatabase = _real_db_mod.SqliteDatabase
# Restore the fake so other tests keep working
if _saved is not None:
    sys.modules["utils.db"] = _saved


@pytest.fixture()
def db(tmp_path):
    db_file = str(tmp_path / "test.db")
    return SqliteDatabase(db_file)


# ── Basic get / set / remove ──────────────────────────────────────────────


class TestBasicOperations:
    def test_get_default(self, db):
        assert db.get("core.test", "missing") is None
        assert db.get("core.test", "missing", "fallback") == "fallback"

    def test_set_and_get_string(self, db):
        db.set("core.test", "key1", "hello")
        assert db.get("core.test", "key1") == "hello"

    def test_set_and_get_int(self, db):
        db.set("core.test", "key2", 42)
        assert db.get("core.test", "key2") == 42

    def test_set_and_get_bool_true(self, db):
        db.set("core.test", "flag", True)
        assert db.get("core.test", "flag") is True

    def test_set_and_get_bool_false(self, db):
        db.set("core.test", "flag", False)
        assert db.get("core.test", "flag") is False

    def test_set_and_get_json(self, db):
        data = {"a": [1, 2], "b": "c"}
        db.set("core.test", "payload", data)
        assert db.get("core.test", "payload") == data

    def test_set_overwrites(self, db):
        db.set("core.test", "k", "v1")
        db.set("core.test", "k", "v2")
        assert db.get("core.test", "k") == "v2"

    def test_remove(self, db):
        db.set("core.test", "k", "v")
        db.remove("core.test", "k")
        assert db.get("core.test", "k") is None

    def test_remove_nonexistent(self, db):
        db.remove("core.test", "nope")  # should not raise


# ── get_collection ────────────────────────────────────────────────────────


class TestGetCollection:
    def test_empty_collection(self, db):
        assert db.get_collection("core.test") == {}

    def test_populated_collection(self, db):
        db.set("core.test", "a", 1)
        db.set("core.test", "b", "two")
        coll = db.get_collection("core.test")
        assert coll == {"a": 1, "b": "two"}

    def test_invalid_module_name(self, db):
        with pytest.raises(ValueError):
            db.get_collection("invalid_module")


# ── _parse_row static ────────────────────────────────────────────────────


class TestParseRow:
    @staticmethod
    def _row(type_val, val):
        return {"type": type_val, "val": val}

    def test_bool_true(self):
        assert SqliteDatabase._parse_row(self._row("bool", "1")) is True

    def test_bool_false(self):
        assert SqliteDatabase._parse_row(self._row("bool", "0")) is False

    def test_int(self):
        assert SqliteDatabase._parse_row(self._row("int", "99")) == 99

    def test_str(self):
        assert SqliteDatabase._parse_row(self._row("str", "hello")) == "hello"

    def test_json(self):
        payload = json.dumps({"x": [1, 2]})
        assert SqliteDatabase._parse_row(self._row("json", payload)) == {"x": [1, 2]}


# ── _execute validation ──────────────────────────────────────────────────


class TestExecuteValidation:
    def test_rejects_invalid_module_prefix(self, db):
        with pytest.raises(ValueError, match="Invalid module name"):
            db.set("badprefix.mod", "k", "v")


# ── Chat-history helpers ─────────────────────────────────────────────────


class TestChatHistory:
    def test_empty_history(self, db):
        assert db.get_chat_history(12345) == []

    def test_add_and_get_history(self, db):
        db.add_chat_history(12345, {"role": "user", "text": "hi"})
        db.add_chat_history(12345, {"role": "bot", "text": "hello"})
        hist = db.get_chat_history(12345)
        assert len(hist) == 2
        assert hist[0]["text"] == "hi"


# ── AI user helpers ───────────────────────────────────────────────────────


class TestAiUsers:
    def test_add_ai_user(self, db):
        db.addaiuser(100)
        assert 100 in db.getaiusers()

    def test_add_duplicate_ai_user(self, db):
        db.addaiuser(100)
        db.addaiuser(100)
        assert db.getaiusers().count(100) == 1

    def test_remove_ai_user(self, db):
        db.addaiuser(100)
        db.remaiuser(100)
        assert 100 not in db.getaiusers()

    def test_remove_nonexistent_ai_user(self, db):
        db.remaiuser(999)  # should not raise

    def test_get_ai_users_empty(self, db):
        assert db.getaiusers() == []


# ── close ─────────────────────────────────────────────────────────────────


class TestClose:
    def test_close_does_not_raise(self, db):
        db.set("core.test", "k", "v")
        db.close()
