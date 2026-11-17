# SPEC — помощник преподавателя (состояние на занятие 4)

## Назначение
Консольный агент, который помогает преподавателю математики составлять
олимпиадные задачи для 5–9 классов. Конечная цель курса: банк задач, где каждая
задача проверена инструментом и подтверждена преподавателем.

## Что умеет сейчас
- Ведёт диалог в REPL, история `messages` хранится в памяти процесса.
- Сам выбирает инструмент для вычисления или проверки ответа.
- Получает ошибки инструментов как текст и исправляет вызов.
- Для задач в z3 сообщает, единственно ли решение, и показывает второе решение.
- Перед каждым вызовом инструмента проверяет разрешения; опасное не выполняет,
  подозрительное выполняет только после подтверждения пользователя.
- Выполняет код модели в отдельном процессе с таймаутом; зависание не роняет REPL.
- Хранит задачи в банке на диске: они переживают `/reset` и перезапуск.
- Сам перепроверяет ответ при сохранении задачи; `verified` ставит harness, `approved` —
  только преподаватель.
- Помнит разрешения «всегда» между запусками.

## Инструменты
| Имя | Аргументы | Результат | Таймаут |
| --- | --- | --- | --- |
| `python_eval` | `expression: str` | строка со значением | 5 с |
| `python_run` | `code: str`, `timeout?: int = 5` (1–30) | `{"stdout", "stderr", "returncode", "timed_out"}` | `timeout` |
| `sympy_solve` | `equations: list[str]`, `variables: list[str]`, `domain?: real/integer/natural/complex` | `{"kind": "equations", "count", "solutions": [{var: value}]}` или `{"kind": "inequality", "solution"}` | 15 с |
| `sympy_simplify` | `expression: str` | строка | 15 с |
| `z3_check` | `variables: {name: Int/Bool/Real}`, `constraints: list[str]`, `minimize?`, `maximize?`, `check_unique?=true` | `{"status", "solution", "objective_value"?, "unique", "another_solution"?}` | 30 с |
| `save_problem` | `title`, `grade: 5–9`, `topic`, `statement`, `answer: object`, `solution`, `verification: {tool, arguments}`, `id?` | `{"id", "status", "verification": {"ok", "reason"}}` | — |
| `list_problems` | `grade?`, `topic?` (подстрока), `status?` | `{"count", "problems": [{id, title, grade, topic, status}], "broken_files"?}` | — |
| `get_problem` | `id` | полная запись задачи | — |

## Банк задач
- Папка `BANK_DIR` (по умолчанию `bank/`), одна задача — файл `P-NNNN.json`.
- id: `P-\d{4}`, выдаётся как максимальный существующий + 1. Путь строит только `bank.py`.
- Запись атомарная: временный файл `.P-NNNN.json.tmp` → `os.replace`.
- Испорченный файл пропускается и попадает в `broken_files`.
- Статусы: `draft`, `verified`, `approved`, `rejected`.

| Переход | Кто |
| --- | --- |
| → `verified` / `draft` | harness при каждом `save_problem` (по результату проверки) |
| `verified` → `approved` | преподаватель, `/approve` |
| любой → `rejected` | преподаватель, `/reject <id> <причина>`; комментарий в `review` |
| изменение задачи | статус пересчитывается, `review` сбрасывается |

### Воспроизводимая проверка (`verify.run`)
- Инструменты: `python_eval`, `sympy_solve`, `z3_check`.
- Вызов идёт через `permissions.check(..., ask=None)` → `tools.call`: ворота 1 действуют,
  вызов, требующий подтверждения, отклоняется.
- `python_eval`: `str(result) == str(answer["value"])`.
- `z3_check`: `status == "sat"`, `unique is True`, каждое `answer[k]` совпадает с `solution[k]` (как строки).
- `sympy_solve`: `kind == "equations"`, `count == 1`, сравнение как у z3. Неравенства не проверяются.
- В `answer` можно перечислить не все переменные решения (вспомогательные пропускаются).

### Оглавление в системном промпте
Перед каждым ходом `main.py` заменяет `messages[0]` на `SYSTEM_PROMPT` + `bank.summary()`.

## Контракт реестра
- `register(name, description, parameters, func, timeout=None)` — регистрация при импорте модуля.
  Если `timeout` задан, `func` выполняется через `sandbox.run_isolated`.
- `schemas()` — список описаний в формате OpenAI tools.
- `call(name, arguments_json) -> str` — никогда не бросает исключение:
  неизвестный инструмент, некорректный JSON, исключение и таймаут в инструменте
  возвращаются строкой, начинающейся с `Ошибка`.
- Результат-словарь сериализуется в JSON (`ensure_ascii=False`).

## Модель безопасности

### Конвейер разрешений (`permissions.check(name, arguments, ask) -> Decision`)
Порядок фиксирован, первое совпадение решает:
1. **Deny.** Строки с кодом (`CODE_ARGS`: `expression`, `code`, `equations`,
   `constraints`, `minimize`, `maximize`) разбираются `ast.parse`. Запрещены:
   атрибуты, начинающиеся с `_`; имена из `BANNED_NAMES` и начинающиеся с `__`;
   строковые константы с `__`; `global`/`nonlocal`; `import` модулей не из
   `ALLOWED_MODULES` (только в `python_run`). Нераспарсенная строка с `__` тоже отказ.
2. **Rules** (`RULES`): `python_run` — всегда; `python_run` с `timeout > 5`;
   `python_eval`/`python_run` с целой константой (в т.ч. `a**b`) больше 10⁷;
   `save_problem` с `id` (перезапись).
3. **Ask.** Режим `auto` или инструмент в «разрешено всегда» → allow;
   режим `strict` или `ask is None` → deny; иначе `ask(name, args, reason)`:
   `"y"` → allow, `"a"` → allow и записать инструмент в `AGENT_SETTINGS`
   (по умолчанию `.agent/settings.json`, формат `{"always_allow": [...]}`), иначе deny.
   При старте `load_settings()` подхватывает файл; `/forget` удаляет его.

Отказ передаётся модели как результат инструмента: `Отказано: <причина>`.
Некорректный JSON аргументов пропускается: ошибку вернёт реестр.

### Песочница
- `run_isolated`: `forkserver` с предзагрузкой `agent.tools` (Windows: `spawn`),
  таймаут по часам, лимит CPU = 2·timeout + 1 с.
- `run_python`: `python -I -c`, `env={}`, `cwd` — временная папка, вывод ≤ 4000 символов,
  лимит CPU = 2·timeout + 1 с; остановка за лимит CPU тоже считается `timed_out`.
- POSIX: `RLIMIT_CPU`, `RLIMIT_FSIZE` = 1 МБ, `RLIMIT_AS` = 1 ГБ (в macOS не применяется).
- Windows: только таймаут.

### Чего модель безопасности НЕ гарантирует
AST-проверка и процесс с правами пользователя — учебные меры. Код в песочнице может
читать файлы пользователя, если обойдёт ворота 1. Сеть не ограничена на уровне ОС.

## Вызов LLM
- OpenAI-совместимый `POST {LLM_BASE_URL}/chat/completions` с полем `tools`.
- Настройки в `.env`: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`.

## Не входит в занятие 4
Хуки, независимая проверка формализации, поиск дубликатов, блокировки файлов, лимит шагов.
