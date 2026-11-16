"""Конвейер разрешений: проверка ПЕРЕД выполнением инструмента.

Главная идея занятия 3: безопасность нельзя строить на доверии к модели
(«в промпте же написано не делать import»). Её обеспечивает код harness.

Каждый вызов проходит три ворот в фиксированном порядке:

    1. Deny  — жёсткий запрет. Код в аргументах разбирается в AST и проверяется:
               никаких __dunder__, import опасных модулей, open/exec/getattr...
               Совпало -> отказ, без вопросов пользователю.
    2. Rules — правила «когда спросить человека»: запуск скрипта, большой
               перебор, долгий таймаут. Совпало -> ворота 3.
    3. Ask   — вопрос пользователю: y (да), n (нет), a (всегда для этого
               инструмента до конца сессии).

Ни одни ворота не сработали -> выполняем сразу. Так проходит большинство
вызовов: sympy_solve, z3_check, короткий python_eval.

Режимы (как permission modes в Claude Code, упрощённо):
    default — спрашивать на воротах 3;
    auto    — на воротах 3 разрешать без вопроса (ворота 1 всё равно работают);
    strict  — на воротах 3 отказывать без вопроса.
"""
import ast
import json
import re
from dataclasses import dataclass

MODES = ("default", "auto", "strict")

# Состояние сессии — как таблица в реестре инструментов: на уровне модуля.
_state = {"mode": "default", "always_allow": set()}


@dataclass
class Decision:
    behavior: str          # "allow" | "deny" | "ask"
    reason: str = ""

    @property
    def allowed(self) -> bool:
        return self.behavior == "allow"


# ======================= Ворота 1: жёсткий запрет (AST) =======================

# Имена, через которые обходят ограничения eval: доступ к объектам интерпретатора,
# выполнение произвольного кода, файлы.
BANNED_NAMES = {
    "eval", "exec", "compile", "open", "input", "breakpoint", "help",
    "getattr", "setattr", "delattr", "globals", "locals", "vars", "dir",
    "type", "object", "memoryview", "__import__", "__builtins__",
}

# Модули, которые можно импортировать в python_run. Всё остальное — запрет.
ALLOWED_MODULES = {
    "math", "itertools", "functools", "collections", "fractions", "decimal",
    "random", "statistics", "string", "re", "heapq", "bisect", "operator",
    "sympy", "z3",
}

# В каких аргументах инструмента лежит код, который потом выполнится.
# Инструмент, которого здесь нет, считается безопасным на воротах 1.
CODE_ARGS = {
    "python_eval": ("expression",),
    "python_run": ("code",),
    "sympy_solve": ("equations",),
    "sympy_simplify": ("expression",),
    "z3_check": ("constraints", "minimize", "maximize"),
}

# Одиночный "=" в уравнениях SymPy ('x + 1 = 3') — не Python. Делим по нему.
_EQUALS = re.compile(r"(?<![<>=!])=(?!=)")


def find_violation(code: str, mode: str = "eval") -> str | None:
    """Ищет запрещённую конструкцию в коде. Возвращает причину или None.

    mode="eval" — одно выражение (python_eval, z3, SymPy): import запрещён совсем;
    mode="exec" — скрипт (python_run): разрешён import из ALLOWED_MODULES.
    """
    try:
        tree = ast.parse(code, mode=mode)
    except SyntaxError:
        # Не наш вопрос: синтаксическую ошибку покажет сам инструмент.
        # Но строку с "__" не пропускаем даже нераспарсенной.
        return "двойное подчёркивание (__) запрещено" if "__" in code else None

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            return f"обращение к скрытому атрибуту .{node.attr}"
        if isinstance(node, ast.Name) and (node.id in BANNED_NAMES or node.id.startswith("__")):
            return f"запрещённое имя {node.id}"
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and "__" in node.value:
            return "строка с двойным подчёркиванием (обход через format/getattr)"
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if mode == "eval":
                return "import внутри выражения запрещён"
            modules = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            for module in modules:
                if module.split(".")[0] not in ALLOWED_MODULES:
                    return f"импорт модуля {module} запрещён (разрешены: {', '.join(sorted(ALLOWED_MODULES))})"
        if isinstance(node, (ast.Global, ast.Nonlocal)):
            return "global/nonlocal запрещены"
    return None


def _code_fragments(name: str, args: dict):
    """Достаёт из аргументов все строки с кодом: (фрагмент, режим разбора)."""
    for arg in CODE_ARGS.get(name, ()):
        value = args.get(arg)
        values = value if isinstance(value, list) else [value]
        for text in values:
            if not isinstance(text, str):
                continue
            if name == "python_run":
                yield text, "exec"
            elif name.startswith("sympy_"):
                yield from ((part, "eval") for part in _EQUALS.split(text))
            else:
                yield text, "eval"


def check_deny(name: str, args: dict) -> str | None:
    for code, mode in _code_fragments(name, args):
        reason = find_violation(code, mode)
        if reason:
            return reason
    return None


# ======================= Ворота 2: правила «спросить» =======================

BIG_RANGE = 10**7        # перебор больше этого — спрашиваем
LONG_TIMEOUT = 5         # секунд; python_run дольше — спрашиваем


def _max_int_constant(code: str) -> int:
    """Наибольшая целая константа в коде, включая 10**8 и 10_000_000."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return 0
    biggest = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            biggest = max(biggest, node.value)
        if (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow)
                and isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant)
                and isinstance(node.left.value, int) and isinstance(node.right.value, int)
                and 0 <= node.right.value < 100):
            biggest = max(biggest, node.left.value ** node.right.value)
    return biggest


# Каждое правило: для каких инструментов, условие, сообщение пользователю.
RULES = [
    {
        "tools": ["python_run"],
        "check": lambda args: True,
        "message": "Запуск скрипта Python",
    },
    {
        "tools": ["python_run"],
        "check": lambda args: (args.get("timeout") or 0) > LONG_TIMEOUT,
        "message": f"Долгий запуск (больше {LONG_TIMEOUT} с)",
    },
    {
        "tools": ["python_eval", "python_run"],
        "check": lambda args: _max_int_constant(args.get("expression") or args.get("code") or "") > BIG_RANGE,
        "message": f"Большой перебор (константа больше {BIG_RANGE:,})".replace(",", " "),
    },
]


def check_rules(name: str, args: dict) -> str | None:
    """Все сработавшие правила одной строкой — чтобы пользователь видел все причины."""
    reasons = [r["message"] for r in RULES if name in r["tools"] and r["check"](args)]
    return "; ".join(reasons) or None


# ======================= Всё вместе =======================

def evaluate(name: str, args: dict) -> Decision:
    """Ворота 1 и 2: чистая функция без ввода-вывода (удобно тестировать)."""
    reason = check_deny(name, args)
    if reason:
        return Decision("deny", f"запрещено политикой: {reason}")
    reason = check_rules(name, args)
    if reason:
        return Decision("ask", reason)
    return Decision("allow")


def check(name: str, arguments: str, ask=None) -> Decision:
    """Окончательное решение по вызову: только "allow" или "deny".

    ask(name, args, reason) -> "y" | "n" | "a" — вопрос пользователю.
    Передаётся параметром (как chat в run_turn), чтобы тесты не ждали клавиатуру.
    """
    try:
        args = json.loads(arguments or "{}")
    except json.JSONDecodeError:
        return Decision("allow")  # кривой JSON — реестр сам вернёт модели ошибку
    if not isinstance(args, dict):
        return Decision("allow")

    decision = evaluate(name, args)
    if decision.behavior != "ask":
        return decision

    # Ворота 3.
    if name in _state["always_allow"] or _state["mode"] == "auto":
        return Decision("allow", decision.reason)
    if _state["mode"] == "strict":
        return Decision("deny", f"режим strict не разрешает: {decision.reason}")
    if ask is None:
        return Decision("deny", f"нужно подтверждение пользователя, но спросить некого: {decision.reason}")

    answer = ask(name, args, decision.reason)
    if answer == "a":
        _state["always_allow"].add(name)
        return Decision("allow", decision.reason)
    if answer == "y":
        return Decision("allow", decision.reason)
    return Decision("deny", f"пользователь отклонил вызов ({decision.reason})")


# ======================= Управление сессией =======================

def set_mode(mode: str) -> None:
    if mode not in MODES:
        raise ValueError(f"Режим должен быть одним из {MODES}")
    _state["mode"] = mode


def get_mode() -> str:
    return _state["mode"]


def always_allowed() -> list[str]:
    return sorted(_state["always_allow"])


def reset(mode: str = "default") -> None:
    set_mode(mode)
    _state["always_allow"].clear()
