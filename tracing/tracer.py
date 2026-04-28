<<<<<<< Updated upstream
"""
tracer.py
---------
Centralised structured logging / tracing for the Customer Support MAS.

Usage
-----
    from tracing.tracer import get_tracer

    tracer = get_tracer("my_agent")
    tracer.info("TOOL_CALL", extra={"tool": "classify_ticket", "input": "..."})

Log records are written to:
  • STDOUT  (human-readable format)
  • logs/mas_trace.jsonl  (one JSON object per line — machine-readable)

Each JSONL record contains:
  timestamp, level, agent, event, and any extra fields passed in.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "mas_trace.jsonl")

# ---------------------------------------------------------------------------
# Ensure log directory exists at import time
# ---------------------------------------------------------------------------
os.makedirs(LOG_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Custom JSON log handler — writes one JSON object per line
# ---------------------------------------------------------------------------

class _JsonlHandler(logging.Handler):
    """Appends structured JSON log records to a .jsonl file."""

    def __init__(self, filepath: str) -> None:
        super().__init__()
        self.filepath = filepath

    def emit(self, record: logging.LogRecord) -> None:
        try:
            entry: Dict[str, Any] = {
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "level": record.levelname,
                "agent": getattr(record, "agent", "unknown"),
                "event": getattr(record, "event", record.getMessage()),
            }
            # Merge any extra fields
            extra: Dict[str, Any] = getattr(record, "extra_payload", {})
            entry.update(extra)

            with open(self.filepath, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        except Exception:  # noqa: BLE001
            self.handleError(record)


# ---------------------------------------------------------------------------
# Custom stdout handler — readable, prefixed format
# ---------------------------------------------------------------------------

class _PrettyHandler(logging.Handler):
    """Prints a human-readable trace line to stdout."""

    LEVEL_PREFIX = {
        "DEBUG":    "⚙",
        "INFO":     "ℹ",
        "WARNING":  "⚠",
        "ERROR":    "✗",
        "CRITICAL": "☠",
    }

    def emit(self, record: logging.LogRecord) -> None:
        try:
            prefix = self.LEVEL_PREFIX.get(record.levelname, "•")
            agent = getattr(record, "agent", "?")
            event = getattr(record, "event", record.getMessage())
            extra: Dict[str, Any] = getattr(record, "extra_payload", {})
            ts = datetime.now().strftime("%H:%M:%S")

            line = f"[{ts}] {prefix} [{agent}] {event}"
            if extra:
                # Print concise key=value pairs for the most important fields
                kv = "  |  ".join(f"{k}={v!r}" for k, v in list(extra.items())[:4])
                line += f"  →  {kv}"
            print(line)
        except Exception:  # noqa: BLE001
            self.handleError(record)


# ---------------------------------------------------------------------------
# AgentTracer — thin wrapper that injects agent name into every record
# ---------------------------------------------------------------------------

class AgentTracer:
    """
    Structured tracer bound to a specific agent.

    Parameters
    ----------
    agent_name : str
        Identifier used in every log record (e.g. ``"ticket_classifier_agent"``).
    """

    def __init__(self, agent_name: str, logger: logging.Logger) -> None:
        self._agent = agent_name
        self._logger = logger

    def _log(
        self,
        level: int,
        event: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        record = self._logger.makeRecord(
            name=self._logger.name,
            level=level,
            fn="",
            lno=0,
            msg=event,
            args=(),
            exc_info=None,
        )
        record.agent = self._agent          # type: ignore[attr-defined]
        record.event = event                # type: ignore[attr-defined]
        record.extra_payload = extra or {}  # type: ignore[attr-defined]
        self._logger.handle(record)

    # Public convenience methods -------------------------------------------

    def debug(self, event: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log a DEBUG-level trace event."""
        self._log(logging.DEBUG, event, extra)

    def info(self, event: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log an INFO-level trace event."""
        self._log(logging.INFO, event, extra)

    def warning(self, event: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log a WARNING-level trace event."""
        self._log(logging.WARNING, event, extra)

    def error(self, event: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log an ERROR-level trace event."""
        self._log(logging.ERROR, event, extra)

    def critical(self, event: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log a CRITICAL-level trace event."""
        self._log(logging.CRITICAL, event, extra)


# ---------------------------------------------------------------------------
# Factory — returns an AgentTracer for the given agent name
# ---------------------------------------------------------------------------

def get_tracer(agent_name: str) -> AgentTracer:
    """
    Return a configured :class:`AgentTracer` for *agent_name*.

    Calling this multiple times with the same name returns a new wrapper
    around the same underlying logger (handlers are not duplicated).

    Parameters
    ----------
    agent_name : str
        A short identifier for the component being traced.

    Returns
    -------
    AgentTracer
    """
    logger_name = f"mas.{agent_name}"
    logger = logging.getLogger(logger_name)

    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        # JSONL file handler
        jsonl_handler = _JsonlHandler(LOG_FILE)
        jsonl_handler.setLevel(logging.DEBUG)
        logger.addHandler(jsonl_handler)

        # Pretty stdout handler
        pretty_handler = _PrettyHandler()
        pretty_handler.setLevel(logging.DEBUG)
        logger.addHandler(pretty_handler)

    return AgentTracer(agent_name=agent_name, logger=logger)
=======
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import json


TRACE_FILE = Path(__file__).resolve().parent / "agent_trace.log"


def _write_log_line(payload: Dict[str, Any]) -> None:
	TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)
	with TRACE_FILE.open("a", encoding="utf-8") as file:
		file.write(json.dumps(payload, ensure_ascii=True) + "\n")


def trace_event(agent_name: str, event: str, data: Optional[Dict[str, Any]] = None) -> None:
	"""Write a structured trace event to console and local log file."""
	payload = {
		"timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
		"agent": agent_name,
		"event": event,
		"data": data or {},
	}
	print(f"[{agent_name}] {event}: {payload['data']}")
	_write_log_line(payload)


def log_agent_input(agent_name: str, ticket_text: str) -> None:
	trace_event(agent_name, "agent_input", {"ticket_text": ticket_text})


def log_tool_call(agent_name: str, tool_name: str, inputs: Dict[str, Any]) -> None:
	trace_event(agent_name, "tool_call", {"tool": tool_name, "inputs": inputs})


def log_tool_output(agent_name: str, tool_name: str, output: Dict[str, Any]) -> None:
	trace_event(agent_name, "tool_output", {"tool": tool_name, "output": output})


def log_final_output(agent_name: str, output: Dict[str, Any]) -> None:
	trace_event(agent_name, "final_output", output)
>>>>>>> Stashed changes
