#!/usr/bin/env python3
"""Cron entry point for writer agent 1-hour iteration.

This script is called by the openclaw cron scheduler every hour.
It delegates to skills/iterate.py::run_once().
"""
import sys
from pathlib import Path

# Ensure the agent dir is on the path so skills imports resolve
AGENT_DIR = Path(__file__).parent
sys.path.insert(0, str(AGENT_DIR))

from skills.iterate import run_once

if __name__ == "__main__":
    report = run_once()
    # Exit non-zero if any tasks failed (CI-friendly)
    sys.exit(1 if report.tasks_failed > 0 else 0)
