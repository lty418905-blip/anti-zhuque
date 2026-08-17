#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


PROFILE_REQUIRED = {
    "schema", "work_id", "scene_ids", "source_paths", "genre", "fiction_status",
    "scene_anchors", "participants", "available_objects", "available_spaces",
    "time_window", "missing_functions", "immutable_facts", "forbidden_outcomes",
    "recent_mechanisms", "max_selected_events",
}

CANDIDATE_REQUIRED = {
    "schema", "event_id", "scene_id", "title", "source_mode", "origin_seed_id",
    "domain", "scale", "scene_anchors", "trigger", "immediate_need",
    "visible_behavior", "reaction_branches", "immediate_cost", "residue",
    "aftereffect_window", "pov_gate", "function_tags", "variation_axes",
    "forbidden_results", "dedupe_signature", "fact_status", "status",
    "selection_reason", "rejection_reason", "chain",
}

PARTICIPANT_REQUIRED = {
    "id", "immediate_goal", "pressure", "knowledge_limit", "visible_behavior_range",
}

CHAIN_REQUIRED = {
    "mode", "goal", "steps", "state_handshakes", "abort_options",
    "settlement_point", "carrying_residue", "independent_coincidences",
    "forbidden_results",
}

STEP_REQUIRED = {"step_id", "visible_action", "state_in", "state_out"}


def nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def nonempty_string_list(value: object, minimum: int = 1) -> bool:
    return (
        isinstance(value, list)
        and len(value) >= minimum
        and all(nonempty_string(item) for item in value)
    )


def load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("scene profile must be a JSON object")
    return payload


def load_jsonl(path: Path) -> tuple[list[dict], list[str]]:
    items: list[dict] = []
    errors: list[str] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            item = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_number}: invalid JSON: {exc.msg}")
            continue
        if not isinstance(item, dict):
            errors.append(f"line {line_number}: entry must be an object")
            continue
        item["_line"] = line_number
        items.append(item)
    return items, errors


def validate_profile(profile: dict) -> list[str]:
    errors: list[str] = []
    missing = sorted(PROFILE_REQUIRED - profile.keys())
    if missing:
        errors.append(f"profile missing fields: {', '.join(missing)}")
        return errors
    if profile["schema"] != "SCENE_EVENT_PROFILE_V1":
        errors.append("profile schema must be SCENE_EVENT_PROFILE_V1")
    for key in ("work_id", "genre", "fiction_status", "time_window"):
        if not nonempty_string(profile[key]):
            errors.append(f"profile {key} must be a non-empty string")
    for key, minimum in (
        ("scene_ids", 1), ("source_paths", 1), ("scene_anchors", 4),
        ("available_objects", 1), ("available_spaces", 1),
        ("missing_functions", 1), ("immutable_facts", 1),
        ("forbidden_outcomes", 1), ("recent_mechanisms", 1),
    ):
        if not nonempty_string_list(profile[key], minimum):
            errors.append(f"profile {key} must contain at least {minimum} non-empty strings")
    if not isinstance(profile["participants"], list) or not profile["participants"]:
        errors.append("profile participants must be a non-empty array")
    else:
        for index, participant in enumerate(profile["participants"], 1):
            if not isinstance(participant, dict):
                errors.append(f"participant {index} must be an object")
                continue
            missing_participant = sorted(PARTICIPANT_REQUIRED - participant.keys())
            if missing_participant:
                errors.append(f"participant {index} missing fields: {', '.join(missing_participant)}")
            for key in PARTICIPANT_REQUIRED & participant.keys():
                if not nonempty_string(participant[key]):
                    errors.append(f"participant {index} {key} must be non-empty")
    if not isinstance(profile["max_selected_events"], int) or not 0 <= profile["max_selected_events"] <= 20:
        errors.append("profile max_selected_events must be an integer from 0 through 20")
    return errors


def validate_chain(chain: object, line: int) -> list[str]:
    if chain == "NONE":
        return []
    errors: list[str] = []
    if not isinstance(chain, dict):
        return [f"line {line}: chain must be NONE or an object"]
    missing = sorted(CHAIN_REQUIRED - chain.keys())
    if missing:
        errors.append(f"line {line}: chain missing fields: {', '.join(missing)}")
        return errors
    if chain["mode"] != "ROOT_SEEDED_CHAIN":
        errors.append(f"line {line}: chain mode must be ROOT_SEEDED_CHAIN")
    steps = chain["steps"]
    if not isinstance(steps, list) or not 2 <= len(steps) <= 6:
        errors.append(f"line {line}: chain steps must contain 2 through 6 entries")
        steps = []
    for index, step in enumerate(steps, 1):
        if not isinstance(step, dict) or STEP_REQUIRED - step.keys():
            errors.append(f"line {line}: chain step {index} is missing required fields")
            continue
        if not all(nonempty_string(step[key]) for key in STEP_REQUIRED):
            errors.append(f"line {line}: chain step {index} fields must be non-empty")
    handshakes = chain["state_handshakes"]
    expected_handshakes = max(0, len(steps) - 1)
    if not nonempty_string_list(handshakes, expected_handshakes) or len(handshakes) != expected_handshakes:
        errors.append(f"line {line}: chain requires exactly {expected_handshakes} state handshakes")
    if not nonempty_string_list(chain["abort_options"], 1):
        errors.append(f"line {line}: chain requires at least one abort option")
    for key in ("goal", "settlement_point", "carrying_residue"):
        if not nonempty_string(chain[key]):
            errors.append(f"line {line}: chain {key} must be non-empty")
    if chain["independent_coincidences"] not in (0, 1):
        errors.append(f"line {line}: independent_coincidences must be 0 or 1")
    if not nonempty_string_list(chain["forbidden_results"], 1):
        errors.append(f"line {line}: chain forbidden_results must not be empty")
    return errors


def validate_candidate(item: dict, profile: dict) -> list[str]:
    line = int(item.get("_line", 0))
    errors: list[str] = []
    missing = sorted(CANDIDATE_REQUIRED - item.keys())
    if missing:
        errors.append(f"line {line}: missing fields: {', '.join(missing)}")
        return errors
    if item["schema"] != "SCENE_EVENT_CANDIDATE_V1":
        errors.append(f"line {line}: schema must be SCENE_EVENT_CANDIDATE_V1")
    for key in (
        "event_id", "scene_id", "title", "origin_seed_id", "domain", "scale",
        "trigger", "immediate_need", "visible_behavior", "immediate_cost", "residue",
        "pov_gate", "dedupe_signature",
    ):
        if not nonempty_string(item[key]):
            errors.append(f"line {line}: {key} must be a non-empty string")
    if item["source_mode"] not in {"SCENE_DERIVED", "SEED_ADAPTED", "USER_PROVIDED"}:
        errors.append(f"line {line}: invalid source_mode")
    if item["fact_status"] != "PROPOSAL_NOT_FACT":
        errors.append(f"line {line}: fact_status must be PROPOSAL_NOT_FACT")
    if item["status"] not in {"CANDIDATE", "SELECTED", "REJECTED"}:
        errors.append(f"line {line}: invalid status")
    if item["scene_id"] not in profile["scene_ids"]:
        errors.append(f"line {line}: scene_id is not declared by the scene profile")
    anchors = item["scene_anchors"]
    if not nonempty_string_list(anchors, 2):
        errors.append(f"line {line}: at least two scene anchors are required")
    else:
        unknown = sorted(set(anchors) - set(profile["scene_anchors"]))
        if unknown:
            errors.append(f"line {line}: anchors not found in profile: {', '.join(unknown)}")
    for key, minimum in (
        ("reaction_branches", 2), ("function_tags", 1),
        ("variation_axes", 2), ("forbidden_results", 1),
    ):
        if not nonempty_string_list(item[key], minimum):
            errors.append(f"line {line}: {key} requires at least {minimum} non-empty values")
    if item["aftereffect_window"] not in {"NEXT_ACTION", "REST_OF_SCENE", "REST_OF_CHAPTER", "CROSS_SCENE"}:
        errors.append(f"line {line}: invalid aftereffect_window")
    if item["status"] == "SELECTED" and not nonempty_string(item["selection_reason"]):
        errors.append(f"line {line}: selected event requires selection_reason")
    if item["status"] == "REJECTED" and not nonempty_string(item["rejection_reason"]):
        errors.append(f"line {line}: rejected event requires rejection_reason")
    errors.extend(validate_chain(item["chain"], line))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a scene-specific event library")
    parser.add_argument("library", type=Path)
    parser.add_argument("--scene-profile", type=Path, required=True)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    try:
        profile = load_json(args.scene_profile)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        profile = {}
        errors.append(f"profile error: {exc}")
    if profile:
        errors.extend(validate_profile(profile))

    try:
        items, load_errors = load_jsonl(args.library)
        errors.extend(load_errors)
    except OSError as exc:
        items = []
        errors.append(f"library error: {exc}")

    if not items:
        errors.append("library contains no event candidates")
    if profile and not validate_profile(profile):
        for item in items:
            errors.extend(validate_candidate(item, profile))

    event_ids = [item.get("event_id") for item in items if nonempty_string(item.get("event_id"))]
    signatures = [item.get("dedupe_signature") for item in items if nonempty_string(item.get("dedupe_signature"))]
    if len(event_ids) != len(set(event_ids)):
        errors.append("duplicate event_id found")
    if len(signatures) != len(set(signatures)):
        errors.append("duplicate dedupe_signature found")

    selected = [item for item in items if item.get("status") == "SELECTED"]
    if profile and isinstance(profile.get("max_selected_events"), int) and len(selected) > profile["max_selected_events"]:
        errors.append(
            f"selected event count {len(selected)} exceeds profile cap {profile['max_selected_events']}"
        )

    result = {
        "schema": "SCENE_EVENT_LIBRARY_VALIDATION_V1",
        "status": "PASS" if not errors else "FAIL",
        "profile": str(args.scene_profile.resolve()),
        "library": str(args.library.resolve()),
        "candidate_count": len(items),
        "selected_count": len(selected),
        "error_count": len(errors),
        "errors": errors,
        "note": "Mechanical validation does not establish literary fitness or fact authorization.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=None if args.compact else 2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
