#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from urllib import request


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a note creation payload to the FastAPI automation API.")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--secret", default="")
    parser.add_argument("--folder", default="Ideas")
    parser.add_argument("--title", required=True)
    parser.add_argument("--body", required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    payload = {
        "folder": args.folder,
        "title": args.title,
        "body": args.body,
        "metadata": {"source": "webhook_automation.py"},
        "overwrite": args.overwrite,
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if args.secret:
        headers["x-automation-secret"] = args.secret

    req = request.Request(
        url=f"{args.api_url.rstrip('/')}/automation/notes",
        data=data,
        headers=headers,
        method="POST",
    )
    with request.urlopen(req, timeout=30) as response:
        print(response.read().decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

