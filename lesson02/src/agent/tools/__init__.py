"""Инструменты агента.

Импорт модуля инструмента регистрирует его в реестре. Чтобы добавить новый
инструмент: создать модуль с вызовом register(...) и импортировать его здесь.
"""
from agent.tools import eval_tool, sympy_tool, z3_tool  # noqa: F401
from agent.tools.registry import call, names, schemas  # noqa: F401
