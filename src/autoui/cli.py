"""
CLI — run / resume / dry-run сценариев.

    python -m autoui run module:scenario_attr [--vars k=v]
    python -m autoui resume --snapshot path [--scenario module:attr]
    python -m autoui dry-run module:scenario_attr
"""

from __future__ import annotations

import argparse
import importlib
import logging
import sys
from typing import Any

from autoui.drivers.pywinauto_driver import PywinautoDriver
from autoui.logging.journal import JournalHandler
from autoui.core.events import EventBus
from autoui.runtime.runner import AutomationRunner
from autoui.runtime.scenario import Scenario


def _load_scenario(spec: str) -> Scenario:
    """module.path:attribute → Scenario."""
    if ":" not in spec:
        raise SystemExit(f"Invalid scenario spec '{spec}', use module:attr")
    module_name, attr = spec.split(":", 1)
    mod = importlib.import_module(module_name)
    obj = getattr(mod, attr)
    if not isinstance(obj, Scenario):
        raise SystemExit(f"{spec} is not a Scenario instance")
    return obj


def _parse_vars(pairs: list[str] | None) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for p in pairs or []:
        if "=" not in p:
            raise SystemExit(f"Invalid --vars '{p}', use key=value")
        k, v = p.split("=", 1)
        result[k] = v
    return result


def cmd_run(args: argparse.Namespace) -> int:
    scenario = _load_scenario(args.scenario)
    variables = _parse_vars(args.vars)
    bus = EventBus()
    bus.subscribe(JournalHandler(args.log_file))
    driver = PywinautoDriver(uimap=scenario.uimap)
    runner = AutomationRunner(driver, event_bus=bus)
    result = runner.run(scenario, variables=variables, start_from=args.from_step)
    print(f"Run {result.run_id}: {result.state.value}", file=sys.stderr)
    if result.error:
        print(result.error, file=sys.stderr)
    return 0 if result.state.value == "finished" else 1


def cmd_resume(args: argparse.Namespace) -> int:
    if not args.scenario:
        raise SystemExit("--scenario required for resume")
    scenario = _load_scenario(args.scenario)
    variables = _parse_vars(args.vars)
    bus = EventBus()
    bus.subscribe(JournalHandler(args.log_file))
    driver = PywinautoDriver(uimap=scenario.uimap)
    runner = AutomationRunner(driver, event_bus=bus)
    result = runner.resume_from_snapshot(scenario, args.snapshot, variables=variables)
    print(f"Resume {result.run_id}: {result.state.value}", file=sys.stderr)
    return 0 if result.state.value == "finished" else 1


def cmd_dry_run(args: argparse.Namespace) -> int:
    scenario = _load_scenario(args.scenario)
    scenario.validate()
    print(f"Scenario: {scenario.name}")
    print(f"Entry: {scenario.entry}")
    order = scenario.order or list(scenario.steps.keys())
    for i, name in enumerate(order, 1):
        step = scenario.steps[name]
        print(f"  {i}. {name} ({type(step).__name__})")
    return 0


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(prog="autoui", description="autoUI RPA runner")
    parser.add_argument("--log-file", default=".autoui/journal.log")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="Run scenario")
    p_run.add_argument("scenario", help="module.path:scenario_attr")
    p_run.add_argument("--vars", nargs="*", help="key=value variables")
    p_run.add_argument("--from-step", default=None, dest="from_step")
    p_run.set_defaults(func=cmd_run)

    p_resume = sub.add_parser("resume", help="Resume from snapshot")
    p_resume.add_argument("--snapshot", required=True)
    p_resume.add_argument("--scenario", help="module.path:scenario_attr")
    p_resume.add_argument("--vars", nargs="*")
    p_resume.set_defaults(func=cmd_resume)

    p_dry = sub.add_parser("dry-run", help="List steps without execution")
    p_dry.add_argument("scenario", help="module.path:scenario_attr")
    p_dry.set_defaults(func=cmd_dry_run)

    args = parser.parse_args(argv)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
