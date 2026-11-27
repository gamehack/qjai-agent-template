"""Modal adapter for the independently built OCI image; smoke only for initial acceptance."""
import datetime
import json
import os
import re
import subprocess
import uuid

import modal

image_ref = os.environ["QJAI_AGENT_IMAGE"]
if not re.fullmatch(r"ghcr\.io/[^\s@]+@sha256:[0-9a-f]{64}", image_ref):
    raise ValueError("QJAI_AGENT_IMAGE must be a GHCR image pinned by SHA256 digest")

app_name = os.getenv("QJAI_MODAL_APP", "qjai-agent-template")
app = modal.App(app_name)
# Modal imports this module again in the remote container.
# Deployment configuration must be available there too.
image = modal.Image.from_registry(image_ref).env({
    "QJAI_AGENT_IMAGE": image_ref,
    "QJAI_MODAL_APP": app_name,
})

@app.function(
    image=image, cpu=(0.25, 1.0), memory=(512, 1024),
    timeout=120, min_containers=0, max_containers=1,
    scaledown_window=2, retries=0,
)
def run_smoke(run_id: str = "", business_date: str = "") -> dict:
    run_id = run_id or str(uuid.uuid4())
    business_date = business_date or datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    datetime.date.fromisoformat(business_date)
    env = dict(os.environ, AGENT_MODE="smoke", RUN_ID=run_id, BUSINESS_DATE=business_date)
    proc = subprocess.run(
        ["python", "-m", "qjai_agent"], cwd="/app", env=env,
        capture_output=True, text=True, timeout=60, check=False,
    )
    if proc.returncode:
        raise RuntimeError(f"Agent smoke exited with code {proc.returncode}")
    result = json.loads(proc.stdout)
    if result.get("status") != "succeeded" or result.get("mode") != "smoke" or result.get("run_id") != run_id:
        raise RuntimeError("Invalid smoke result")
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return result
