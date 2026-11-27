"""Authenticated CLI for a deployed smoke Function; suitable for scheduler integration tests."""
import argparse
import datetime
import json
import os
import uuid

import modal
from modal import exception


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    submit = sub.add_parser("submit")
    submit.add_argument("--run-id", default=None)
    submit.add_argument("--business-date", default=None)
    poll = sub.add_parser("poll")
    poll.add_argument("call_id")
    args = parser.parse_args()
    if args.command == "submit":
        run_id = args.run_id or str(uuid.uuid4())
        business_date = args.business_date or datetime.datetime.now(datetime.timezone.utc).date().isoformat()
        datetime.date.fromisoformat(business_date)
        fn = modal.Function.from_name(os.getenv("QJAI_MODAL_APP", "qjai-agent-template"), "run_smoke")
        call = fn.spawn(run_id, business_date)
        result = {"status": "submitted", "call_id": call.object_id, "run_id": run_id, "business_date": business_date}
    else:
        call = modal.FunctionCall.from_id(args.call_id)
        try:
            result = {"status": "succeeded", "call_id": args.call_id, "result": call.get(timeout=0)}
        except (exception.FunctionTimeoutError, exception.OutputExpiredError) as exc:
            result = {"status": "failed", "call_id": args.call_id, "error_type": type(exc).__name__}
        except (exception.TimeoutError, TimeoutError):
            result = {"status": "pending", "call_id": args.call_id}
        except Exception as exc:
            result = {"status": "unknown", "call_id": args.call_id, "error_type": type(exc).__name__}
    print(json.dumps(result, ensure_ascii=False))
    return 1 if result["status"] in ("failed", "unknown") else 0


if __name__ == "__main__":
    raise SystemExit(main())
