# Modal Functions smoke acceptance

Status: adapter code only until authenticated deployment and remote execution are verified.

## Prerequisites

Create a Modal Starter workspace and inspect its Usage & Billing. Confirm the available compute credit and set a conservative workspace budget and an out-of-pocket spend limit if supported. No cloud credentials belong in this repository. Authenticate locally with `modal setup`. The first smoke does not use any LLM or model secret.

## Deploy and run

Run from the repository root using Python 3.12:

```bash
python -m venv .venv-modal
source .venv-modal/bin/activate
pip install -r requirements-modal.txt
modal setup
export QJAI_AGENT_IMAGE=ghcr.io/gamehack/qjai-agent-template@sha256:0c40fe793befe1d99c74ab5e30848c8af1ad55af80e27d1e349c14126e9e84a3
export QJAI_MODAL_APP=qjai-agent-template
modal deploy modal_app.py
python modal_client.py submit
```

The image is the successfully verified public image from [CI run 45961697596](https://github.com/gamehack/qjai-agent-template/actions/runs/45961697596). Use a new verified digest when releasing business changes. Copy the returned call_id, then:

```bash
python modal_client.py poll <call_id>
```

Expected: succeeded with matching run_id, mode=smoke and status=succeeded in the nested result. pending means check again; unknown means investigate the call before resubmitting. Do not blindly retry ambiguous submissions.

The adapter has no schedule or public endpoint. Resources: 0.25 requested physical CPU core (limit 1), 512 MiB memory (limit 1024), 120s timeout, 0 warm containers, at most 1 concurrent container, 2s scaledown, no application-level retries. Modal infrastructure may still reschedule inputs. Actual costs, runtime compatibility and scaling are unverified until deployment.

After acceptance, inspect Modal usage and logs. n8n integration, live mode, credential injection and persistent idempotency are separate future steps.
