"""Общие настройки тестов."""
import pytest

from agent import permissions


@pytest.fixture(autouse=True)
def fresh_permissions():
    """Каждый тест начинает с режима default и пустых разрешений сессии."""
    permissions.reset()
    yield
    permissions.reset()
