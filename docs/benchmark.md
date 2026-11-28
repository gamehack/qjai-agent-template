# Agent performance benchmark

## Scope and safety

The default benchmark is smoke, with networking disabled, no model calls and no secrets. CI automatically tests the worker and report generator against the same newly built OCI image before publishing. Manual workflow **Agent performance benchmark** builds locally and does not publish or deploy; it has no schedule. It accepts repeat count and per-sample timeout. No Modal calls are made.

Live runs require manual confirmation, repository secret BENCHMARK_OPENAI_API_KEY and repository variable BENCHMARK_OPENAI_MODEL. The current template uses only a fixed health-check prompt and an Agent without tools or external business writes. Each downstream business must implement and test a separate safe fixture/dry-run behavior when AGENT_BENCHMARK=1 before enabling live benchmarks, with publication, mutations and other external side effects disabled. This flag is a contract, not a sandbox; it does not itself prevent future tools from writing. Use a dedicated least-privilege model credential. Do not run live automatically on pushes, pull requests or schedules.

## Metrics

- container_wall_ms: host elapsed time around docker run, including container startup/exit, excluding build/pull.
- business_wall_ms: wall time for the actual Python entry-point child, including its startup; agent_duration_ms: timer within the business entry point.
- cpu_seconds: cgroup v2 usage_usec delta including worker and descendants during measurement; not CPU quota or peak parallelism.
- container_memory_peak_bytes: cgroup v2 memory.peak for this fresh container including worker/child and cgroup-accounted memory; not process RSS. child_max_rss_bytes: Linux maximum RSS of waited-for children (not aggregate container peak). Missing cgroup data remains null.
- usage: SDK-reported requests/input/output/total tokens; zero for smoke, null for unavailable values. Provider fees are not inferred from token counts; use actual model gateway invoices/prices, including caching and tool fees. Report contains no raw business output or prompts.
- mean, max and nearest-rank P95 over successful measurements, P95 only for >=20 samples. Failed/timeout samples are visible and fail the workflow; no zero substitution or automatic retry.

Default baseline: one Docker CPU quota, 512 MiB memory, fresh independent container per sample, no swap. CPU quota on GitHub is not equivalent to Modal physical-core allocation. Local CLI supports --cpus and --memory-mib. Compare identical image/fixture and resource profile. Sample timeout includes Docker startup, and timed-out containers are forcibly removed. GitHub-hosted jobs have a 6-hour limit; this workflow permits at most a 5-hour aggregate sample budget (including cleanup allowances), leaving time for image build and reporting. Longer jobs need separate runs.

## Run locally

    docker build --platform linux/amd64 -t qjai-benchmark:local .
    python scripts/benchmark.py --image qjai-benchmark:local --repeats 3 --timeout-seconds 60

Reports are written to benchmark-report.json; GitHub Actions uploads the sanitized file for 30 days and renders metric summary in the run.

## Promotion checklist

1. Unit tests and offline OCI smoke pass.
2. Run representative, non-mutating business fixtures in GitHub Actions (different dates/data volumes; record fixture and model configuration separately without secrets). Start with a small sample; use >=20 independent samples for an initial P95 if cost/time permit. Report failures, not only successful durations.
3. Deploy the exact accepted OCI digest to a separate Modal test Function; re-measure end-to-end latency, startup, memory/CPU and real billed usage on Modal. GitHub results are a baseline, not a Modal performance guarantee.
4. Choose CPU/memory, Function timeout, and n8n poll_interval_seconds/timeout_seconds from measurements and business deadline, with explicit queue/cold-start margin. Do not use one common production timeout or set Function timeout equal to n8n deadline.
5. Register the Agent in Gateway and run an isolated n8n acceptance before enabling its production schedule. Validate durable waits, cancellation, idempotency and failure recovery for long tasks.

Sources: https://openai.github.io/openai-agents-python/usage/ ; https://docs.github.com/en/actions/reference/limits
