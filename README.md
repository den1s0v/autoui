# autoUI

Workflow execution engine для **детерминированной** автоматизации Windows desktop-приложений.
Проверяемые шаги, политики preconditions, ветвление, сожительство с пользователем.

## Назначение

Не «скрипт кликов», а движок сценариев:

```
when (preconditions) → action → expect (postconditions) → retry / recovery / goto
```

Успех шага определяется **postconditions**, не фактом вызова action.

## Три слоя

| Слой | Содержимое |
|------|------------|
| **runtime** | AutomationRunner, StepPipeline, политики — без знания ОС |
| **drivers** | PywinautoDriver — UIA, окна, элементы |
| **uimap** | Логические имена → Locator (pipeline локаторов) |
| **locators** | LocatorExecutor, ops — без знания ОС |

## PreconditionPolicy

Отдельно от retry/recovery для **expect**.

| mode | Поведение при невыполнении `when` |
|------|-----------------------------------|
| `required` | StepFailed |
| `skip` | Шаг SKIPPED, action не выполняется |
| `wait` | Poll до `wait_timeout`, затем `on_timeout` |

### PreconditionOutcome

| Значение | Действие runner |
|----------|-----------------|
| `proceed` | К action (или on_met у ProbeStep) |
| `skip` | SKIPPED |
| `fail` | StepFailed → ERROR |
| `goto` | Переход на `goto_step` |
| `retry_wait` | Ещё один цикл poll (только WAIT) |

`on_timeout` — константа или callback `(ctx, driver, step) -> PreconditionOutcome`.

## PostconditionRecovery

Только для **expect** после исчерпания RetryPolicy. Не путать с `on_timeout`.

Задаётся в `ActionStep.postcondition_recovery`: action (напр. закрыть диалог) + `then`: retry_step | skip | goto | fail.

## IStep

- **ActionStep** — when → action → expect
- **ProbeStep** — без action, `on_met` после when
- **BranchStep** — when → then_steps или `else_goto`

Сценарий: `dict[str, IStep]` + `entry`.

## IDriver

- `connect_running_app(selector)` → AppHandle
- `attach_window(app, title=...)` → WindowHandle
- `set_primary(app, window)` — кеш для режима одного приложения
- `resolve(Locator)` → **UIElement | None** (not-found → `None`)
- `exists(...)` → **bool** (not-found → `False`)
- `click("uimap_key")` — resolve + click; при not-found → `DriverError`

## UIMap / Locator

**Locator** — immutable pipeline операций поиска (не строка). **UIElement** — click, get_text.
При смене UI правится UIMap, не сценарий.

### Pipeline

Локатор — последовательность ops над `IElementTree` (драйвер предоставляет примитивы):

| op | Назначение |
|----|------------|
| `child` | N-й прямой потомок |
| `find_descendants` | обход потомков + фильтр `where`; опционально `depth` (max-глубина, 1=children; в pywinauto — нативно) и `limit` (ранняя остановка после N совпадений, BFS в executor) |
| `filter` | фильтр текущего множества |
| `take` | выбор N-го из множества |

Shorthand: `Locator.find(name="OK")` → `find_descendants` + `take(0)`.

### JSON

```json
{
  "ops": [
    {"op": "child", "index": 1},
    {"op": "find_descendants", "where": {"control_type": "Button", "name": "Экспорт"}, "depth": 2, "limit": 5},
    {"op": "take", "index": 0}
  ]
}
```

Компактная форма: `{"find": {"name": "OK"}}`.

### where: открытые поля и операторы

Поля **не ограничены** — любой ключ из `properties()` драйвера. В pywinauto: сначала `element_info` (name, rich_text, class_name, …), затем `get_properties()` (`friendly_class_name`, `texts`, …).

| Значение в where | Семантика |
|------------------|-----------|
| `"Button"` / `true` / `null` | точное равенство |
| `{"$eq": "Button"}` | явное равенство |
| `{"$contains": "logo-btn"}` | подстрока в `str` или в любом элементе `list` (`texts`) |
| `{"$word": "logo-btn"}` | токен по пробелам в `class_name` |

Узел без запрошенного ключа в properties — **пропускается** (не ошибка). Неверный синтаксис where — ошибка при создании op.

```json
{"where": {
  "friendly_class_name": "Button",
  "class_name": {"$contains": "logo-btn"},
  "rich_text": {"$contains": "Cursor"}
}}
```

### Not-found

- **LocatorExecutor** бросает `LocatorNotFoundError` с `LocatorTrace` (in/out counts на каждом шаге).
- **resolve** ловит → `None`; **exists** → `False`.
- **click** / **set_text** при not-found → `DriverError`.
- Подробная диагностика: `trace.format_diagnostic()` или `verbose_locators` / `locator_trace_hook` в драйвере.

### Query vs resolve (один элемент vs множество)

| API | Зачем | Результат при N кандидатах без `Take` |
|-----|-------|----------------------------------------|
| `LocatorExecutor.execute_all()` | Отладка, подбор индекса | Все N узлов |
| `LocatorExecutor.execute()` | Сценарии, `driver.resolve` | Первый + `truncated_from=N` в trace и warning в лог |
| `ExplorerSession.query_locator()` | Jupyter: список совпадений | Все controls |
| `ExplorerSession.try_locator()` / `resolve()` | Проверка как в UIMap | Первый + предупреждение |

## CoexistenceGuard

Mouse hook: пауза при активности пользователя, auto-resume после 30 с idle.
`ctx.automation_active` — фильтр «своих» кликов агента.

## CLI

```bash
python -m autoui run examples.double_commander_demo:demo_scenario
python -m autoui resume --snapshot .autoui/runs/<run_id>.json
python -m autoui dry-run examples.double_commander_demo:demo_scenario
```

## Explore playground (Jupyter)

Интерактивный подбор локаторов: [`src/examples/exploring.ipynb`](src/examples/exploring.ipynb).

```python
from autoui.explore import ExplorerSession

session = ExplorerSession("Notepad++")
session.connect()

# все кандидаты (pipeline без Take)
candidates = session.query_locator(LOCATOR_QUERY)
session.list_indexed(candidates)

# один элемент, как в сценарии (с Take или Locator.find)
element = session.try_locator(LOCATOR_SINGLE)
```

## Control Inspector (PySide6 GUI)

Desktop → окно → контролы; codegen `Locator` для копирования в сценарий.

```bash
pip install -e ".[explore]"
python -m autoui.explore.inspector
```

- Слева: иерархия от **Desktop** (список окон → дети окна → …)
- Стрелки: навигация PATH/CHILDREN; **→** на ребёнке фиксирует сегмент path
- **Space** / двойной клик — подсветка control в целевом приложении (`HighlightManager`)
- Справа: свойства узла и панель селектора (Generated / Custom, Test, Copy)

## Roadmap

- Test-rebuild HierarchyView из locator (частичный resolve)
- YAML loader
- Другие драйверы (Playwright, vision)
