#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


ROOT_REQUIRED = {
    "schema", "task_id", "task_mode", "language", "user_request",
    "source_contract", "fact_contract", "character_and_pov", "scenes",
    "event_contract", "positive_style_requirements", "length_contract",
    "output_contract", "completion_conditions", "generation_input_scope",
}
FORBIDDEN_KEYS = {
    "audit_checklist", "audit_findings", "detector_report", "detector_score",
    "risk_threshold", "high_risk_spans", "word_blacklist", "ai_rate",
    "event_library", "full_event_library", "candidate_library", "seed_library",
    "rejected_events",
}
TASK_MODES = {
    "FICTION_CHAPTER", "FICTION_SCENE", "NARRATIVE_NONFICTION",
    "NONFICTION_ARTICLE", "SCRIPT", "CUSTOM",
}
TITLE_POLICIES = {"NONE", "USER_PROVIDED", "AGENT_PROPOSED", "PRESERVE_SOURCE"}
OUTPUT_FORMATS = {"PLAIN_TEXT", "MARKDOWN", "SCRIPT", "CUSTOM"}


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def string_list(value: object, minimum: int = 1) -> bool:
    return isinstance(value, list) and len(value) >= minimum and all(nonempty(x) for x in value)


def find_forbidden_keys(value: object, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key.lower() in FORBIDDEN_KEYS:
                errors.append(f"forbidden field in generation input: {child_path}")
            errors.extend(find_forbidden_keys(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(find_forbidden_keys(child, f"{path}[{index}]"))
    return errors


def validate_length(contract: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(contract, dict):
        return ["length_contract must be an object"]
    if set(contract) != {"source", "instruction", "parsed"}:
        errors.append("length_contract must contain only source, instruction, and parsed")
        return errors
    source = contract.get("source")
    instruction = contract.get("instruction")
    parsed = contract.get("parsed")
    if not isinstance(parsed, dict) or set(parsed) != {"min", "max", "unit"}:
        errors.append("length_contract.parsed must contain min, max, and unit")
        return errors
    minimum, maximum, unit = parsed["min"], parsed["max"], parsed["unit"]
    if source == "UNSPECIFIED":
        if instruction != "UNSPECIFIED":
            errors.append("unspecified length requires instruction=UNSPECIFIED")
        if minimum is not None or maximum is not None or unit is not None:
            errors.append("unspecified length must keep min, max, and unit null")
        return errors
    if source != "USER_NATURAL_LANGUAGE":
        errors.append("length source must be USER_NATURAL_LANGUAGE or UNSPECIFIED")
        return errors
    if not nonempty(instruction) or instruction == "UNSPECIFIED":
        errors.append("user-specified length requires the preserved natural-language instruction")
        return errors
    for label, value in (("min", minimum), ("max", maximum)):
        if value is not None:
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                errors.append(f"length {label} must be a non-negative integer or null")
            elif not re.search(rf"(?<!\d){value}(?!\d)", instruction):
                errors.append(f"length {label}={value} does not occur in the preserved user instruction")
    if unit is not None and not nonempty(unit):
        errors.append("length unit must be a non-empty string or null")
    if minimum is not None and maximum is not None and minimum > maximum:
        errors.append("length min must not exceed max")
    return errors


def validate_events(contract: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(contract, dict):
        return ["event_contract must be an object"]
    required = {
        "source", "selected_event_cards", "seed_library_included",
        "full_candidate_library_included", "rejected_events_included",
    }
    missing = sorted(required - contract.keys())
    if missing:
        return [f"event_contract missing fields: {', '.join(missing)}"]
    for flag in ("seed_library_included", "full_candidate_library_included", "rejected_events_included"):
        if contract.get(flag) is not False:
            errors.append(f"event_contract.{flag} must be false")
    cards = contract.get("selected_event_cards")
    if not isinstance(cards, list):
        return errors + ["selected_event_cards must be an array"]
    source = contract.get("source")
    if source == "NONE" and cards:
        errors.append("event source NONE requires an empty selected_event_cards array")
    elif source == "SCENE_EVENT_WEAVER_SELECTED_ONLY":
        if not cards:
            errors.append("selected event source requires at least one selected event card")
    else:
        if source not in {"NONE", "SCENE_EVENT_WEAVER_SELECTED_ONLY"}:
            errors.append("invalid event source")
    for index, card in enumerate(cards):
        if not isinstance(card, dict):
            errors.append(f"selected event card {index} must be an object")
            continue
        if card.get("status") != "SELECTED":
            errors.append(f"selected event card {index} must have status SELECTED")
        if not nonempty(card.get("event_id")):
            errors.append(f"selected event card {index} requires event_id")
    return errors


def validate(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return ["root must be a JSON object"]
    errors = find_forbidden_keys(payload)
    missing = sorted(ROOT_REQUIRED - payload.keys())
    if missing:
        errors.append(f"root missing fields: {', '.join(missing)}")
        return errors
    if payload["schema"] != "STRUCTURED_WRITING_INPUT_V1":
        errors.append("schema must be STRUCTURED_WRITING_INPUT_V1")
    if not nonempty(payload["task_id"]):
        errors.append("task_id must be non-empty")
    if payload["task_mode"] not in TASK_MODES:
        errors.append("invalid task_mode")
    if not nonempty(payload["language"]):
        errors.append("language must be non-empty")

    request = payload["user_request"]
    if not isinstance(request, dict) or not all(nonempty(request.get(k)) for k in ("original_instruction", "intended_audience", "purpose")):
        errors.append("user_request requires original_instruction, intended_audience, and purpose")

    sources = payload["source_contract"]
    if not isinstance(sources, dict) or not isinstance(sources.get("materials"), list) or sources.get("unlisted_sources_allowed") is not False:
        errors.append("source_contract requires materials array and unlisted_sources_allowed=false")
    else:
        for index, source in enumerate(sources["materials"]):
            if not isinstance(source, dict) or not all(nonempty(source.get(k)) for k in ("source_id", "path_or_label", "authority", "permitted_use")):
                errors.append(f"source material {index} requires source_id, path_or_label, authority, and permitted_use")

    facts = payload["fact_contract"]
    if not isinstance(facts, dict) or not string_list(facts.get("immutable_facts")) or not string_list(facts.get("prohibited_inferences")):
        errors.append("fact_contract requires non-empty immutable_facts and prohibited_inferences")

    pov = payload["character_and_pov"]
    if not isinstance(pov, dict) or not nonempty(pov.get("pov")) or not nonempty(pov.get("narrator")) or not isinstance(pov.get("participants"), list) or not string_list(pov.get("knowledge_boundaries")):
        errors.append("character_and_pov requires pov, narrator, participants array, and knowledge_boundaries")

    scenes = payload["scenes"]
    if not isinstance(scenes, list) or not scenes:
        errors.append("scenes must be a non-empty array")
    else:
        for index, scene in enumerate(scenes):
            if not isinstance(scene, dict) or not all(nonempty(scene.get(k)) for k in ("scene_id", "setting", "immediate_goal")) or not string_list(scene.get("required_beats")) or not string_list(scene.get("forbidden_changes")):
                errors.append(f"scene {index} requires identity, setting, goal, required beats, and forbidden changes")

    if not string_list(payload["positive_style_requirements"]):
        errors.append("positive_style_requirements must be a non-empty string array")
    errors.extend(validate_length(payload["length_contract"]))
    errors.extend(validate_events(payload["event_contract"]))

    output = payload["output_contract"]
    if not isinstance(output, dict) or output.get("format") not in OUTPUT_FORMATS or output.get("title_policy") not in TITLE_POLICIES or not isinstance(output.get("additional_requirements"), list):
        errors.append("output_contract has invalid format, title policy, or additional requirements")
    elif output["title_policy"] == "USER_PROVIDED" and not nonempty(output.get("title")):
        errors.append("USER_PROVIDED title policy requires a title")
    if not string_list(payload["completion_conditions"]):
        errors.append("completion_conditions must be a non-empty string array")
    if payload["generation_input_scope"] != "POSITIVE_WRITING_ONLY":
        errors.append("generation_input_scope must be POSITIVE_WRITING_ONLY")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a generic structured writing input")
    parser.add_argument("input", type=Path)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        errors = validate(payload)
    except (OSError, json.JSONDecodeError) as exc:
        errors = [f"input error: {exc}"]
    result = {
        "schema": "STRUCTURED_WRITING_INPUT_VALIDATION_V1",
        "status": "PASS" if not errors else "FAIL",
        "input": str(args.input.resolve()),
        "error_count": len(errors),
        "errors": errors,
        "note": "PASS verifies structure and boundary declarations, not literary quality or factual truth.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=None if args.compact else 2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
