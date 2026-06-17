"""Tests for utils/module.py — HelpNavigator and ModuleManager singleton."""

import sys

import pytest

# conftest.py has already injected the fake modules into sys.modules.

from utils.module import HelpNavigator, ModuleManager

_modules_help = sys.modules["utils.misc"].modules_help


# ── ModuleManager singleton ──────────────────────────────────────────────


class TestModuleManager:
    def setup_method(self):
        ModuleManager._instance = None

    def test_singleton(self):
        a = ModuleManager.get_instance()
        b = ModuleManager.get_instance()
        assert a is b

    def test_initial_counts(self):
        mm = ModuleManager.get_instance()
        assert mm.success_modules == 0
        assert mm.failed_modules == 0
        assert mm.help_navigator is None


# ── HelpNavigator ────────────────────────────────────────────────────────


class TestHelpNavigator:
    def _populate_modules(self, n):
        _modules_help.clear()
        for i in range(n):
            _modules_help[f"mod{i}"] = {f"cmd{i}": f"desc{i}"}

    def teardown_method(self):
        _modules_help.clear()

    def test_empty_modules(self):
        self._populate_modules(0)
        nav = HelpNavigator()
        assert nav.total_pages == 0
        assert nav.current_page == 1

    def test_single_page(self):
        self._populate_modules(5)
        nav = HelpNavigator()
        assert nav.total_pages == 1
        assert not nav.next_page()
        assert not nav.prev_page()

    def test_multi_page_navigation(self):
        self._populate_modules(25)
        nav = HelpNavigator()
        assert nav.total_pages == 3
        assert nav.current_page == 1

        assert nav.next_page()
        assert nav.current_page == 2
        assert nav.next_page()
        assert nav.current_page == 3
        assert not nav.next_page()  # can't go beyond last page

        assert nav.prev_page()
        assert nav.current_page == 2
        assert nav.prev_page()
        assert nav.current_page == 1
        assert not nav.prev_page()  # can't go below 1

    def test_exact_page_boundary(self):
        self._populate_modules(10)
        nav = HelpNavigator()
        assert nav.total_pages == 1

    def test_page_boundary_plus_one(self):
        self._populate_modules(11)
        nav = HelpNavigator()
        assert nav.total_pages == 2
