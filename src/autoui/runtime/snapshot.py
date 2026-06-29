"""Snapshot после успешного шага — resume с того же места."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class RunSnapshot:
    run_id: str
    scenario_name: str
    current_step_name: str
    variables: dict[str, Any]
    saved_at: str


class SnapshotStore:
    """JSON-снимки в .autoui/runs/."""

    def __init__(self, base_dir: str | Path = ".autoui/runs") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        run_id: str,
        scenario_name: str,
        step_name: str,
        variables: dict[str, Any],
    ) -> Path:
        snap = RunSnapshot(
            run_id=run_id,
            scenario_name=scenario_name,
            current_step_name=step_name,
            variables=dict(variables),
            saved_at=datetime.now(timezone.utc).isoformat(),
        )
        path = self.base_dir / f"{run_id}.json"
        path.write_text(json.dumps(asdict(snap), indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def load(self, path: str | Path) -> RunSnapshot:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return RunSnapshot(**data)
