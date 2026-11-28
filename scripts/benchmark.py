"""Run independent OCI samples and aggregate sanitized measurements."""
import argparse
import json
import math
import os
import statistics
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

if __package__:
    from .check_naming import validate_project, test_container_name
else:
    from check_naming import validate_project, test_container_name

METRICS = ("container_wall_ms", "business_wall_ms", "agent_duration_ms",
           "cpu_seconds", "container_memory_peak_bytes", "child_max_rss_bytes")
USAGE_KEYS = ("requests", "input_tokens", "output_tokens", "total_tokens")


def summarize(samples):
    successful = [s for s in samples if s["status"] == "succeeded"]
    metrics = {}
    for key in METRICS:
        values = sorted(s[key] for s in successful if s.get(key) is not None)
        metrics[key] = {
            "n": len(values),
            "mean": round(statistics.mean(values), 3) if values else None,
            "max": max(values) if values else None,
            # Small samples do not justify a P95 estimate.
            "p95": values[math.ceil(len(values)*0.95)-1] if len(values) >= 20 else None,
        }
    usage_totals = {}
    for key in USAGE_KEYS:
        values = [s.get("usage", {}).get(key) for s in successful]
        usage_totals[key] = sum(values) if len(values) == len(samples) and values and all(v is not None for v in values) else None
    return {"samples": len(samples), "succeeded": len(successful),
            "failed": len(samples)-len(successful), "metrics": metrics,
            "usage_totals": usage_totals}


def run_sample(args, image_id):
    run_id = "bench-" + uuid.uuid4().hex
    name = test_container_name(args.project_name, run_id)
    mode = args.mode
    cmd = ["docker", "run", "--rm", "--pull", "never", "--name", name,
           "--cpus", str(args.cpus), "--memory", f"{args.memory_mib}m",
           "--memory-swap", f"{args.memory_mib}m",
           "-e", f"AGENT_MODE={mode}", "-e", f"RUN_ID={run_id}",
           "-e", f"BUSINESS_DATE={args.business_date}", "-e", "AGENT_BENCHMARK=1",
           "-e", "OPENAI_AGENTS_DISABLE_TRACING=1"]
    if mode == "smoke":
        cmd += ["--network", "none"]
    else:
        cmd += ["-e", "OPENAI_MODEL", "-e", "OPENAI_API_KEY"]
    cmd += [image_id, "python", "-m", "qjai_agent.benchmark"]
    start = time.monotonic()
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=args.timeout_seconds, check=False)
        elapsed = round((time.monotonic()-start)*1000, 3)
        try:
            raw = json.loads(proc.stdout)
            if not isinstance(raw, dict):
                raise ValueError("invalid metrics")
        except (ValueError, UnicodeError):
            raw = {}
        valid = (proc.returncode == 0 and raw.get("status") == "succeeded"
                 and raw.get("run_id") == run_id and raw.get("mode") == mode)
        record = {"status": "succeeded" if valid else "failed", "run_id": run_id,
                  "container_wall_ms": elapsed, "exit_code": proc.returncode}
        if valid:
            # Allow-list fields rather than serializing the worker's raw output.
            for k in METRICS[1:]:
                value = raw.get(k)
                record[k] = value if type(value) in (int, float) and math.isfinite(value) and value >= 0 else None
            u = raw.get("usage", {})
            record["usage"] = {k: u.get(k) if isinstance(u, dict) and type(u.get(k)) is int and u[k] >= 0 else None for k in USAGE_KEYS}
        return record
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "run_id": run_id,
                "container_wall_ms": round((time.monotonic()-start)*1000, 3)}
    finally:
        subprocess.run(["docker", "rm", "-f", name], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=30, check=False)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--image", required=True)
    p.add_argument("--project-name", default=os.getenv("PROJECT_NAME") or os.getenv("GITHUB_REPOSITORY", "gamehack/qjai-agent-template").split("/")[-1])
    p.add_argument("--mode", choices=["smoke", "live"], default="smoke")
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--timeout-seconds", type=int, default=60)
    p.add_argument("--cpus", type=float, default=1)
    p.add_argument("--memory-mib", type=int, default=512)
    p.add_argument("--business-date", default=datetime.now(timezone.utc).date().isoformat())
    p.add_argument("--report", default="benchmark-report.json")
    p.add_argument("--allow-live", action="store_true")
    a = p.parse_args()
    try:
        validate_project(a.project_name, "agent")
    except ValueError as exc:
        p.error(str(exc))
    if not (1 <= a.repeats <= 20 and 1 <= a.timeout_seconds <= 14400
            and a.repeats*(a.timeout_seconds+30) <= 18000
            and 0.25 <= a.cpus <= 4 and 128 <= a.memory_mib <= 8192):
        p.error("Invalid sample/resource limits or total timeout budget (>5h)")
    if a.mode == "live" and (not a.allow_live or not os.getenv("OPENAI_API_KEY") or not os.getenv("OPENAI_MODEL")):
        p.error("Live requires explicit --allow-live and configured model credentials")
    datetime.strptime(a.business_date, "%Y-%m-%d")
    image_id = subprocess.check_output(["docker", "image", "inspect", "--format", "{{.Id}}", a.image], text=True).strip()
    samples = []
    report = {"schema_version": 1, "project_name": a.project_name, "mode": a.mode, "image_id": image_id,
              "git_sha": os.getenv("GITHUB_SHA"), "business_date": a.business_date,
              "limits": {"docker_cpus": a.cpus, "memory_mib": a.memory_mib, "sample_timeout_seconds": a.timeout_seconds},
              "samples": samples}
    # Preserve partial numeric results even if a subsequent sample fails.
    for _ in range(a.repeats):
        sample = run_sample(a, image_id)
        samples.append(sample)
        report["summary"] = summarize(samples)
        Path(a.report).write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(sample), flush=True)
        if sample["status"] != "succeeded":
            break
    print(json.dumps(report["summary"]), flush=True)
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write("### Agent benchmark (" + a.mode + ")\n\n")
            f.write("| Metric | n | Mean | Max | P95 (n>=20) |\n|---|---:|---:|---:|---:|\n")
            for k, v in report["summary"]["metrics"].items():
                f.write(f"| {k} | {v['n']} | {v['mean']} | {v['max']} | {v['p95']} |\n")
            f.write("\nSuccessful samples: " + str(report["summary"]["succeeded"]) + "/" + str(a.repeats) + "\n")
    return 0 if report["summary"]["succeeded"] == a.repeats else 1


if __name__ == "__main__":
    sys.exit(main())
