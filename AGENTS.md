# AGENTS.md — правила для AI-агентов и разработчиков autoUI

## Проект

Workflow execution engine для детерминированной автоматизации Windows UI.
Архитектура и решения: **README.md** (не rpa-idea.md). Код: `src/autoui/`.

## Слои (не нарушать)

1. `runtime/` — движок (Step, Runner, политики)
2. `abstractions/` — IDriver, IAction, ICondition, IStep
3. `drivers/` — pywinauto
4. `guards/`, `watchers/` — сожительство с пользователем, фоновые диалоги
5. `dsl/`, `examples/` — сценарии поверх runtime

Ядро **не импортирует** pywinauto.

## Документация

- Архитектурные решения — в README.md; обновлять при изменении поведения.
- В комментариях ссылаться на README (раздел), не на rpa-idea.md.

## Комментирование (подробнее обычного)

- Module docstring: роль слоя, границы.
- PreconditionPolicy vs PostconditionRecovery — явно различать в комментариях.
- StepPipeline: фазы when / action / expect; где какой hook.
- mouse_hook: automation_active, idle timeout.
- Русский для домена, English для API.

## Стиль кода

- Минимальный scope; dataclasses + Protocol.
- Синхронный runner в MVP.

## Не делать без запроса

- GUI, YAML, LLM conditions; коммиты и push.
