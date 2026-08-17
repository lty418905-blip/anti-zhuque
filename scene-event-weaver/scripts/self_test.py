#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def candidate(event_id: str, status: str = "CANDIDATE") -> dict:
    return {
        "schema": "SCENE_EVENT_CANDIDATE_V1",
        "event_id": event_id,
        "scene_id": "SCENE-01",
        "title": "杯盖卡住后改变交谈节奏",
        "source_mode": "SEED_ADAPTED",
        "origin_seed_id": "SEED-OBJECT-001",
        "domain": "OBJECT",
        "scale": "MICRO_BEAT",
        "scene_anchors": ["保温杯", "十分钟休息"],
        "trigger": "人物准备喝水时现有杯盖卡住",
        "immediate_need": "在休息结束前喝到水并继续谈话",
        "visible_behavior": "停下半句话，换手拧杯盖，再把问题缩短",
        "reaction_branches": ["同伴递来纸巾但不代为处理", "人物先放下杯子继续说"],
        "immediate_cost": "短暂停顿和一句没说完的话",
        "residue": "后续回答更短，杯子仍放在手边",
        "aftereffect_window": "REST_OF_SCENE",
        "pov_gate": "只写可见动作与听见的话",
        "function_tags": ["PACING_RELEASE", "BODY_OR_OBJECT_PRESSURE"],
        "variation_axes": ["谁先回应", "杯盖是否打开"],
        "forbidden_results": ["不得由杯中物暴露秘密"],
        "dedupe_signature": f"cup-lid-talk-{event_id}",
        "fact_status": "PROPOSAL_NOT_FACT",
        "status": status,
        "selection_reason": "直接改变谈话节奏" if status == "SELECTED" else "",
        "rejection_reason": "" if status == "SELECTED" else "与前场重复",
        "chain": "NONE",
    }


def main() -> int:
    base = Path(__file__).resolve().parent
    validator = base / "validate_scene_event_library.py"
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    root = base / f".self-test-{os.getpid()}"
    if root.exists():
        raise SystemExit(f"self-test directory already exists: {root}")
    root.mkdir()
    try:
        profile = {
            "schema": "SCENE_EVENT_PROFILE_V1",
            "work_id": "TEST-WORK",
            "scene_ids": ["SCENE-01"],
            "source_paths": ["test.md"],
            "genre": "fiction",
            "fiction_status": "FICTION",
            "scene_anchors": ["保温杯", "十分钟休息", "会议室门口", "未说完的问题"],
            "participants": [{
                "id": "A",
                "immediate_goal": "问完问题",
                "pressure": "休息时间很短",
                "knowledge_limit": "不知道对方是否愿意继续谈",
                "visible_behavior_range": "可见动作和直接对白",
            }],
            "available_objects": ["保温杯"],
            "available_spaces": ["会议室门口"],
            "time_window": "十分钟休息",
            "missing_functions": ["PACING_RELEASE"],
            "immutable_facts": ["问题尚未回答"],
            "forbidden_outcomes": ["不得建立新承诺"],
            "recent_mechanisms": ["NONE"],
            "max_selected_events": 5,
        }
        profile_path = root / "profile.json"
        library_path = root / "library.jsonl"
        profile_path.write_text(json.dumps(profile, ensure_ascii=False), encoding="utf-8")

        valid_items = [
            candidate(f"EV-{index:03d}", "SELECTED" if index <= 3 else "CANDIDATE")
            for index in range(1, 7)
        ]
        library_path.write_text(
            "\n".join(json.dumps(item, ensure_ascii=False) for item in valid_items) + "\n",
            encoding="utf-8",
        )

        valid = subprocess.run(
            [sys.executable, str(validator), str(library_path), "--scene-profile", str(profile_path), "--compact"],
            capture_output=True, text=True, encoding="utf-8", env=env,
        )
        if valid.returncode != 0:
            raise SystemExit(valid.stdout + valid.stderr)
        valid_result = json.loads(valid.stdout)
        if (
            valid_result["status"] != "PASS"
            or valid_result["candidate_count"] != 6
            or valid_result["selected_count"] != 3
        ):
            raise SystemExit("valid fixture did not pass")

        invalid_cases: list[tuple[str, list[dict], tuple[str, ...]]] = []

        wrong_anchor = candidate("EV-ANCHOR")
        wrong_anchor["scene_anchors"] = ["保温杯", "不存在的窗台"]
        invalid_cases.append(("unknown-anchor", [wrong_anchor], ("anchors not found in profile",)))

        invalid_cases.append((
            "duplicate-id",
            [candidate("EV-DUP"), candidate("EV-DUP")],
            ("duplicate event_id", "duplicate dedupe_signature"),
        ))

        too_many_selected = [candidate(f"EV-CAP-{index}", "SELECTED") for index in range(1, 7)]
        invalid_cases.append(("selection-cap", too_many_selected, ("exceeds profile cap",)))

        chain_without_residue = candidate("EV-CHAIN")
        chain_without_residue["chain"] = {
            "mode": "ROOT_SEEDED_CHAIN",
            "goal": "让停顿产生直接可见的后续动作",
            "steps": [
                {
                    "step_id": "STEP-1",
                    "visible_action": "人物拧动杯盖",
                    "state_in": "杯盖卡住",
                    "state_out": "杯子被放到桌边",
                },
                {
                    "step_id": "STEP-2",
                    "visible_action": "人物缩短问题后继续交谈",
                    "state_in": "杯子在桌边且问题未完",
                    "state_out": "问题已缩短并说出口",
                },
            ],
            "state_handshakes": ["桌边的杯子仍在视野内"],
            "abort_options": ["人物不再处理杯盖，直接继续交谈"],
            "settlement_point": "问题以较短版本说出口",
            "carrying_residue": "",
            "independent_coincidences": 0,
            "forbidden_results": ["不得让杯子泄露秘密"],
        }
        invalid_cases.append(("chain-residue", [chain_without_residue], ("chain carrying_residue must be non-empty",)))

        for case_name, invalid_items, expected_errors in invalid_cases:
            library_path.write_text(
                "\n".join(json.dumps(item, ensure_ascii=False) for item in invalid_items) + "\n",
                encoding="utf-8",
            )
            invalid = subprocess.run(
                [sys.executable, str(validator), str(library_path), "--scene-profile", str(profile_path), "--compact"],
                capture_output=True, text=True, encoding="utf-8", env=env,
            )
            if invalid.returncode == 0:
                raise SystemExit(f"invalid fixture unexpectedly passed: {case_name}")
            invalid_result = json.loads(invalid.stdout)
            joined = "\n".join(invalid_result["errors"])
            for expected_error in expected_errors:
                if expected_error not in joined:
                    raise SystemExit(f"validator missed {case_name}: {expected_error}")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print("SELF_TEST=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
