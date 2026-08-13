#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


SCHEMA = "NATURAL_PROSE_STRUCTURED_INPUT_V1"
MODES = {
    "GENERATE_ONLY",
    "GENERATE_THEN_AUDIT",
    "AUDIT_AND_REVISE",
    "WHOLE_REWRITE_THEN_AUDIT",
}
REALITY_CONTRACTS = {"REAL", "FICTION", "MIXED"}
SOURCE_STATUSES = {"USER_PROVIDED", "VERIFIED_SOURCE", "FICTION_AUTHORIZED"}
LENGTH_UNITS = {"zh_characters", "approx_words", "seconds", "lines"}
EXPECTED_CONSTRAINTS = {f"NPA-{index:02d}" for index in range(1, 15)}
PLACEHOLDER = re.compile(r"\{\{[A-Z0-9_]+\}\}")


def fail(message: str) -> int:
    print(f"STRUCTURED_INPUT_INVALID: {message}", file=sys.stderr)
    return 1


def text_at(root: ET.Element, path: str) -> str:
    node = root.find(path)
    return "" if node is None or node.text is None else node.text.strip()


def positive_int(value: str, label: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be an integer") from exc
    if number <= 0:
        raise ValueError(f"{label} must be positive")
    return number


def validate(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8")
    errors: list[str] = []
    placeholders = sorted(set(PLACEHOLDER.findall(raw)))
    if placeholders:
        errors.append("unfilled placeholders: " + ", ".join(placeholders))

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        return errors + [f"XML parse error: {exc}"]

    if root.tag != "natural_prose_request":
        errors.append("root element must be natural_prose_request")
    if root.attrib.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA}")

    required_paths = [
        "./task_identity/mode",
        "./task_identity/genre",
        "./task_identity/reality_contract",
        "./output_contract/deliverable",
        "./output_contract/length_unit",
        "./output_contract/target_min",
        "./output_contract/target_max",
        "./output_contract/format",
        "./output_contract/must_include",
        "./output_contract/must_not_include",
        "./speaker_and_reader/speaker",
        "./speaker_and_reader/knowledge_basis",
        "./speaker_and_reader/current_reason_to_write",
        "./speaker_and_reader/reader",
        "./speaker_and_reader/desired_effect",
        "./materials/known_unknowns",
        "./materials/research_permission",
        "./freeze_contract/facts_and_evidence",
        "./freeze_contract/causality_and_position",
        "./freeze_contract/voice_or_character_knowledge",
        "./freeze_contract/required_examples_or_plot_beats",
        "./voice_and_form/voice",
        "./voice_and_form/tone",
        "./voice_and_form/point_of_view",
        "./voice_and_form/form_constraints",
        "./voice_and_form/highlights_to_preserve",
        "./revision_contract/revision_scope",
        "./revision_contract/do_not_change",
        "./source_text",
        "./final_silent_check",
    ]
    for required in required_paths:
        if not text_at(root, required):
            errors.append(f"missing or empty field: {required}")

    mode = text_at(root, "./task_identity/mode")
    if mode not in MODES:
        errors.append("unsupported mode")
    reality = text_at(root, "./task_identity/reality_contract")
    if reality not in REALITY_CONTRACTS:
        errors.append("unsupported reality_contract")
    length_unit = text_at(root, "./output_contract/length_unit")
    if length_unit not in LENGTH_UNITS:
        errors.append("unsupported length_unit")

    try:
        target_min = positive_int(text_at(root, "./output_contract/target_min"), "target_min")
        target_max = positive_int(text_at(root, "./output_contract/target_max"), "target_max")
        if target_min > target_max:
            errors.append("target_min must not exceed target_max")
    except ValueError as exc:
        errors.append(str(exc))
        target_min = target_max = 0

    sources = root.findall("./materials/source")
    if not sources:
        errors.append("at least one material source is required")
    source_ids: set[str] = set()
    for source in sources:
        source_id = (source.attrib.get("id") or "").strip()
        status = (source.attrib.get("status") or "").strip()
        content = (source.text or "").strip()
        if not source_id or source_id in source_ids:
            errors.append("material source ids must be nonempty and unique")
        source_ids.add(source_id)
        if status not in SOURCE_STATUSES:
            errors.append(f"unsupported source status for {source_id or 'unnamed source'}")
        if not content:
            errors.append(f"empty source material: {source_id or 'unnamed source'}")

    units = root.findall("./structure_plan/unit")
    if not units:
        errors.append("at least one structure unit is required")
    unit_ids: set[str] = set()
    unit_total = 0
    for unit in units:
        unit_id = (unit.attrib.get("id") or "").strip()
        if not unit_id or unit_id in unit_ids:
            errors.append("structure unit ids must be nonempty and unique")
        unit_ids.add(unit_id)
        for child in ("suggested_length", "function", "material_or_action", "change_or_consequence", "exit"):
            node = unit.find(child)
            value = "" if node is None or node.text is None else node.text.strip()
            if not value:
                errors.append(f"unit {unit_id or '?'} missing {child}")
        try:
            unit_total += positive_int(
                "" if unit.find("suggested_length") is None or unit.find("suggested_length").text is None else unit.find("suggested_length").text.strip(),
                f"unit {unit_id or '?'} suggested_length",
            )
        except ValueError as exc:
            errors.append(str(exc))
    if target_min and target_max and not target_min <= unit_total <= target_max:
        errors.append("sum of structure unit suggested_length must be within target_min and target_max")

    constraint_ids = {
        (node.attrib.get("id") or "").strip()
        for node in root.findall("./positive_generation_constraints/constraint")
    }
    if constraint_ids != EXPECTED_CONSTRAINTS:
        errors.append("positive generation constraints must contain exactly NPA-01 through NPA-14")

    source_text = text_at(root, "./source_text")
    source_modes = {"AUDIT_AND_REVISE", "WHOLE_REWRITE_THEN_AUDIT"}
    if mode in source_modes and source_text == "NOT_APPLICABLE":
        errors.append(f"{mode} requires source_text")
    if mode in MODES - source_modes and source_text != "NOT_APPLICABLE":
        errors.append(f"{mode} requires source_text=NOT_APPLICABLE")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a filled Natural Prose structured input without network access.")
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    if not args.input.is_file():
        return fail(f"file not found: {args.input}")
    errors = validate(args.input)
    if errors:
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return fail(f"{len(errors)} error(s)")
    print("STRUCTURED_INPUT_VALID=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
