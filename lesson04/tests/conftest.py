"""Общие настройки тестов."""
import pytest

from agent import permissions


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    """Каждый тест: свой пустой банк, свой файл настроек, режим default.

    Переменные окружения наследуют дочерние процессы песочницы, поэтому
    подмена работает и для инструментов, которые выполняются в spawn-процессе.
    """
    monkeypatch.setenv("BANK_DIR", str(tmp_path / "bank"))
    monkeypatch.setenv("AGENT_SETTINGS", str(tmp_path / "settings.json"))
    permissions.reset()
    yield
    permissions.reset()
