#!/usr/bin/env python
from __future__ import annotations

import argparse
import subprocess
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser(description="Run repeated read-only weather discovery, scoring, and rule audits.")
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--sleep-seconds", type=int, default=60)
    parser.add_argument("--limit", type=int, default=40)
    parser.add_argument("--event-limit", type=int, default=80)
    args = parser.parse_args()

    for index in range(args.iterations):
        print(f"weather_replay_iteration={index + 1}/{args.iterations}")
        run_step(
            [
                sys.executable,
                "scripts/discover_weather_markets.py",
                "--limit",
                str(args.limit),
                "--event-limit",
                str(args.event_limit),
                "--obsidian",
            ]
        )
        run_step([sys.executable, "scripts/score_weather_forecasts.py", "--limit", str(args.limit), "--obsidian"])
        run_step([sys.executable, "scripts/verify_weather_resolution_rules.py", "--limit", str(args.limit), "--obsidian"])
        if index < args.iterations - 1:
            time.sleep(args.sleep_seconds)
    return 0


def run_step(command: list[str]) -> None:
    print(f"running: {' '.join(command)}")
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
