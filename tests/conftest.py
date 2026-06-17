"""Shared fixtures and module stubs for the test suite.

All heavy external dependencies (Telegram client, git repo, .env config, live DB)
are replaced with lightweight fakes so unit tests run fast and offline.
"""

import sys
import types as _types

# ---------------------------------------------------------------------------
# Build fake modules ONCE and inject them into sys.modules so every test file
# shares the same instances.
# ---------------------------------------------------------------------------

_fake_config = _types.ModuleType("utils.config")
_fake_config.db_type = "sqlite3"
_fake_config.db_name = ":memory:"
_fake_config.db_url = ""
_fake_config.api_id = 0
_fake_config.api_hash = ""
_fake_config.STRINGSESSION = ""
_fake_config.second_session = ""
_fake_config.apiflash_key = ""
_fake_config.rmbg_key = ""
_fake_config.vt_key = ""
_fake_config.gemini_key = ""
_fake_config.cohere_key = ""
_fake_config.pm_limit = 4
_fake_config.test_server = False
_fake_config.modules_repo_branch = "master"
sys.modules["utils.config"] = _fake_config


class _FakeDB:
    """Minimal in-memory stub that satisfies db.get / db.set calls at import."""

    def get(self, *a, **kw):
        return kw.get("default", a[2] if len(a) > 2 else None)

    def set(self, *a, **kw):
        pass


_fake_db_mod = _types.ModuleType("utils.db")
_fake_db_mod.db = _FakeDB()
# Keep a reference so tests that need the real SqliteDatabase can still import it
_fake_db_mod.SqliteDatabase = None  # will be lazily filled on first real import
sys.modules["utils.db"] = _fake_db_mod

_fake_misc = _types.ModuleType("utils.misc")
_fake_misc.modules_help = {}
_fake_misc.requirements_list = []
_fake_misc.prefix = "."
_fake_misc.python_version = "3.10.0"
_fake_misc.gitrepo = None
_fake_misc.userbot_version = "2.5.0"
sys.modules["utils.misc"] = _fake_misc
