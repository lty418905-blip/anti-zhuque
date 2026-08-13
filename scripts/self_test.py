#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    base = Path(__file__).resolve().parent
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    run = subprocess.run(
        [
            sys.executable,
            str(base / "audit_prose.py"),
            str(base / "fixtures" / "model_regular_sample.txt"),
            "--mode",
            "fiction",
            "--structure",
            "--compact",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    result = json.loads(run.stdout)
    kinds = {item["type"] for item in result["findings"]}
    required = {
        "transition_cluster_candidate",
        "reversal_template",
        "epistemic_limiter_cluster",
        "cognitive_audit_cycle_candidate",
        "question_answer_unit_test_run",
        "action_argument_pair_run",
        "ending_dense_closure_candidate",
    }
    missing = sorted(required - kinds)
    if missing:
        raise SystemExit(f"missing expected findings: {missing}")
    if result["verdict"] != "warnings_only_no_authorship_or_detector_claim":
        raise SystemExit("verdict boundary changed")
    if any("score" in item or "probability" in item for item in result["findings"]):
        raise SystemExit("findings must not emit scores or probabilities")
    allowed_actions = {
        "review_in_context",
        "read_aloud_then_keep_or_rephrase",
        "review_semantic_function",
        "review_flag",
    }
    if any(item.get("action") not in allowed_actions for item in result["findings"]):
        raise SystemExit("unexpected automatic action")
    print("SELF_TEST=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
