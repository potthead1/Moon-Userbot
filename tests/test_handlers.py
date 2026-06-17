"""Tests for utils/handlers.py — check_username_or_id."""

import pytest

# conftest.py has already injected the fake modules into sys.modules.

from utils.handlers import check_username_or_id


@pytest.mark.asyncio
class TestCheckUsernameOrId:
    async def test_username_string(self):
        assert await check_username_or_id("someuser") == "channel"

    async def test_username_with_at(self):
        assert await check_username_or_id("@someuser") == "channel"

    async def test_positive_user_id(self):
        assert await check_username_or_id("12345") == "user"

    async def test_negative_chat_id(self):
        assert await check_username_or_id("-100123") == "chat"

    async def test_channel_id(self):
        assert await check_username_or_id("-1001234567890") == "channel"

    async def test_invalid_peer_raises(self):
        with pytest.raises(ValueError, match="Peer id invalid"):
            await check_username_or_id("0")

    async def test_negative_non_numeric_is_channel(self):
        assert await check_username_or_id("-abc") == "channel"
