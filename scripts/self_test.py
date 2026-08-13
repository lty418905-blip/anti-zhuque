#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    base = Path(__file__).resolve().parent
    skill_root = base.parent
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

    human_root = skill_root / "references" / "human-writing"
    required_human_files = {
        human_root / "SKILL.md",
        human_root / "LICENSE",
        human_root / "VERSION",
        human_root / "references" / "forum-prose.md",
        human_root / "references" / "reality.md",
        human_root / "references" / "fiction.md",
        human_root / "references" / "formats.md",
        human_root / "references" / "revision.md",
        human_root / "scripts" / "check_prose.py",
    }
    missing_human_files = sorted(
        str(path.relative_to(skill_root))
        for path in required_human_files
        if not path.is_file()
    )
    if missing_human_files:
        raise SystemExit(f"missing embedded Human Writing files: {missing_human_files}")
    if (human_root / "VERSION").read_text(encoding="utf-8").strip() != "1.1.0":
        raise SystemExit("unexpected embedded Human Writing version")

    human_run = subprocess.run(
        [
            sys.executable,
            str(human_root / "scripts" / "check_prose.py"),
            str(base / "fixtures" / "human_writing_hard_failure.txt"),
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    if human_run.returncode != 1:
        raise SystemExit(
            f"embedded Human Writing checker returned {human_run.returncode}, expected 1"
        )
    if "需要修改" not in human_run.stdout or "禁用翻案句" not in human_run.stdout:
        raise SystemExit("embedded Human Writing checker did not report expected findings")
    print("SELF_TEST=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
