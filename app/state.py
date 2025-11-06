from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional

from .config import settings


@dataclass
class RunState:
    last_global_oldest_ts: float = 0.0
    per_channel_last_ts: Dict[str, float] = field(default_factory=dict)

    @staticmethod
    def load(path: Optional[Path] = None) -> "RunState":
        state_path = path or settings.state_file_path
        if not state_path.exists():
            return RunState()
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                data: Dict[str, Any] = json.load(f)
            return RunState(
                last_global_oldest_ts=float(data.get("last_global_oldest_ts", 0.0)),
                per_channel_last_ts={
                    k: float(v) for k, v in data.get("per_channel_last_ts", {}).items()
                },
            )
        except Exception:
            return RunState()

    def save(self, path: Optional[Path] = None) -> None:
        state_path = path or settings.state_file_path
        payload = {
            "last_global_oldest_ts": self.last_global_oldest_ts,
            "per_channel_last_ts": self.per_channel_last_ts,
        }
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def update_channel_ts(self, channel_id: str, newest_ts: float) -> None:
        prev = self.per_channel_last_ts.get(channel_id, 0.0)
        if newest_ts > prev:
            self.per_channel_last_ts[channel_id] = newest_ts
        if newest_ts > self.last_global_oldest_ts:
            self.last_global_oldest_ts = newest_ts

    def get_oldest_for_channel(self, channel_id: str) -> float:
        return self.per_channel_last_ts.get(
            channel_id, self.last_global_oldest_ts or 0.0
        )
