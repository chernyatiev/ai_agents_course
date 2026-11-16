"""Тесты многострочного ввода: input() и признак вставки подменяются."""
import builtins

import pytest

from agent.console import read_message


def feed(monkeypatch, lines):
    """Подменяет input(): по очереди отдаёт строки, затем EOFError."""
    it = iter(lines)

    def fake_input(prompt=""):
        try:
            return next(it)
        except StopIteration:
            raise EOFError

    monkeypatch.setattr(builtins, "input", fake_input)


def test_single_line(monkeypatch):
    feed(monkeypatch, ["Сколько будет 2+2?"])
    assert read_message(ready=lambda: False) == "Сколько будет 2+2?"


def test_pasted_lines_are_joined(monkeypatch):
    feed(monkeypatch, ["На 100 рублей купили 100 птиц. Петух стоит 5 рублей, курица 3 рубля,",
                       "три цыплёнка 1 рубль. Сколько купили петухов, кур и цыплят?"])
    pending = iter([True, False])  # после первой строки в терминале есть ещё одна
    msg = read_message(ready=lambda: next(pending))
    assert msg.endswith("Сколько купили петухов, кур и цыплят?")
    assert msg.count("\n") == 1


def test_block_mode(monkeypatch):
    feed(monkeypatch, ['"""', "строка 1", "", "строка 3", '"""'])
    assert read_message(ready=lambda: False) == "строка 1\n\nстрока 3"


def test_eof_exits(monkeypatch):
    feed(monkeypatch, [])
    with pytest.raises(EOFError):
        read_message(ready=lambda: False)


def test_main_module_imports():
    """main.py не покрыт другими тестами — проверяем хотя бы, что он импортируется."""
    import agent.main  # noqa: F401
