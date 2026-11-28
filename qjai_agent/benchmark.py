"""Isolated benchmark worker. Emits only allow-listed numeric metrics."""
import json
import os
import resource
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CGROUP = Path("/sys/fs/cgroup")
USAGE_KEYS = ("requests", "input_tokens", "output_tokens", "total_tokens")


def nonnegative_int(value):
    return value if type(value) is int and value >= 0 else None


def cpu_usage_usec():
    try:
        return int(dict(line.split() for line in (CGROUP / "cpu.stat").read_text().splitlines())["usage_usec"])
    except (OSError, ValueError, KeyError):
        return None


def memory_peak_bytes():
    try:
        return int((CGROUP / "memory.peak").read_text())
    except (OSError, ValueError):
        return None


def main():
    start_cpu = cpu_usage_usec()
    started = time.monotonic()
    mode = os.environ.get("AGENT_MODE", "smoke")
    run_id = os.environ["RUN_ID"]
    # The child is the real production entry point, not a different benchmark implementation.
    # Never expose model output or stderr in CI artifacts.
    with tempfile.TemporaryFile() as output:
        proc = subprocess.run([sys.executable, "-m", "qjai_agent"], stdout=output,
                              stderr=subprocess.DEVNULL, check=False)
        wall_ms = round((time.monotonic() - started) * 1000, 3)
        end_cpu = cpu_usage_usec()
        peak = memory_peak_bytes()
        child = resource.getrusage(resource.RUSAGE_CHILDREN)
        output.seek(0)
        try:
            raw = output.read(4 * 1024 * 1024 + 1)
            if len(raw) > 4 * 1024 * 1024:
                raise ValueError("oversized result")
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise ValueError("invalid result")
        except (ValueError, UnicodeError):
            result = {}
    valid = (proc.returncode == 0 and result.get("status") == "succeeded"
             and result.get("run_id") == run_id and result.get("mode") == mode
             and result.get("business_date") == os.environ.get("BUSINESS_DATE"))
    usage = result.get("usage")
    if not isinstance(usage, dict):
        usage = {}
    record = {
        "status": "succeeded" if valid else "failed",
        "run_id": run_id,
        "mode": mode,
        "business_wall_ms": wall_ms,
        "agent_duration_ms": nonnegative_int(result.get("duration_ms")),
        "cpu_seconds": round((end_cpu-start_cpu)/1e6, 6)
            if start_cpu is not None and end_cpu is not None else None,
        "cpu_metric": "cgroup_v2_delta",
        "container_memory_peak_bytes": peak,
        "child_max_rss_bytes": child.ru_maxrss * 1024,
        "usage": {key: nonnegative_int(usage.get(key)) for key in USAGE_KEYS},
    }
    print(json.dumps(record), flush=True)
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
