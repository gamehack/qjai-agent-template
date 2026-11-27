"""One-shot task entry point."""
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone, date

from .job import execute


def main() -> int:
    started = time.monotonic()
    mode = os.getenv("AGENT_MODE", "smoke")
    record = {
        "run_id": os.getenv("RUN_ID") or str(uuid.uuid4()),
        "agent_name": os.getenv("AGENT_NAME", "qjai-agent-template"),
        "business_date": os.getenv("BUSINESS_DATE") or datetime.now(timezone.utc).date().isoformat(),
        "mode": mode,
    }
    try:
        date.fromisoformat(record["business_date"])
        record["output"] = execute(mode, os.getenv("AGENT_INPUT", "Reply with a short health check message."))
        record["status"] = "succeeded"
        code = 0
    except Exception as exc:
        record["status"] = "failed"
        record["error_type"] = type(exc).__name__
        print(type(exc).__name__, file=sys.stderr)
        code = 1
    record["duration_ms"] = round((time.monotonic() - started) * 1000)
    print(json.dumps(record, ensure_ascii=False), flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
