import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

class EventLogger:
    def __init__(self, events_path: Path):
        self.events_path = Path(events_path)
        self.events_path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(
        self,
        event: str,
        node_id: str,
        payload: Dict[str, Any],
        actor: str = "agent"
    ) -> None:
        """Appends an event record atomically to the events.jsonl file."""
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "node_id": node_id,
            "actor": actor,
            "payload": payload,
        }
        with open(self.events_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
