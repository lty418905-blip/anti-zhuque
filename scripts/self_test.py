#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_unicode_layer_a(base: Path, env: dict[str, str]) -> None:
    layer_script = base / "unicode_layer_a.py"
    fixture_text = "\ufeff甲\u200b乙\u2060丙\u00ad丁\u202e戊\ufeff己\u200c庚\u200d辛\ufe0f"
    temp_root = base / f".layer-a-self-test-{os.getpid()}"
    if temp_root.exists():
        raise SystemExit(f"Layer A self-test path already exists: {temp_root}")
    temp_root.mkdir()
    source = temp_root / "source.txt"
    output = temp_root / "source.layer-a-clean.txt"
    try:
        source.write_text(fixture_text, encoding="utf-8")
        source_before = source.read_bytes()

        inspect_run = subprocess.run(
            [sys.executable, str(layer_script), "inspect", str(source), "--compact"],
            check=True, capture_output=True, text=True, encoding="utf-8", env=env,
        )
        inspected = json.loads(inspect_run.stdout)
        if inspected["scan"]["high_confidence_total"] != 5:
            raise SystemExit("Layer A inspect missed removable controls")
        if inspected["scan"]["preserved_semantic_total"] != 3:
            raise SystemExit("Layer A inspect missed preserved semantic controls")
        if inspected["scan"]["initial_bom_preserved"] != 1:
            raise SystemExit("Layer A inspect did not preserve initial BOM")

        clean_run = subprocess.run(
            [sys.executable, str(layer_script), "clean", str(source), "--compact"],
            check=True, capture_output=True, text=True, encoding="utf-8", env=env,
        )
        cleaned = json.loads(clean_run.stdout)
        if source.read_bytes() != source_before or cleaned["source_modified"]:
            raise SystemExit("Layer A clean modified the source")
        if Path(cleaned["output"]) != output.resolve():
            raise SystemExit("Layer A clean did not use the non-in-place default output")
        if cleaned["removed_total"] != 5:
            raise SystemExit("Layer A clean removed unexpected count")
        if cleaned["post_clean_scan"]["high_confidence_total"] != 0:
            raise SystemExit("Layer A post-clean scan is not zero")
        output_text = output.read_text(encoding="utf-8")
        for preserved in ("\u200c", "\u200d", "\ufe0f"):
            if preserved not in output_text:
                raise SystemExit("Layer A clean removed a semantic control")
        if not output_text.startswith("\ufeff"):
            raise SystemExit("Layer A clean removed the initial BOM")

        in_place_run = subprocess.run(
            [
                sys.executable, str(layer_script), "clean", str(source),
                "--output", str(source), "--compact",
            ],
            check=False, capture_output=True, text=True, encoding="utf-8", env=env,
        )
        if in_place_run.returncode == 0 or "refusing in-place clean" not in in_place_run.stderr:
            raise SystemExit("Layer A did not refuse in-place output")
    finally:
        source.unlink(missing_ok=True)
        output.unlink(missing_ok=True)
        temp_root.rmdir()


def main() -> int:
    base = Path(__file__).resolve().parent
    script = base / "audit_prose.py"
    path = base / "self_test_fixture.txt"
    scene_path = base / "self_test_scene_fixture.txt"
    child_env = os.environ.copy()
    child_env["PYTHONIOENCODING"] = "utf-8"
    run = subprocess.run(
        [sys.executable, str(script), str(path), "--mode", "fiction", "--structure", "--compact"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=child_env,
    )
    result = json.loads(run.stdout)
    if result.get("schema") != "natural_prose_audit_v3":
        raise SystemExit("audit schema identity changed unexpectedly")
    kinds = {item["type"] for item in result["findings"]}
    required = {
        "transition", "author_metaphor", "reversal_template", "repeated_sentence_start",
        "epistemic_limiter_cluster", "cognitive_audit_cycle_candidate",
        "dialogue_unit_test_run", "action_argument_pair_run",
        "action_immediate_interpretation_run", "exclusion_space_closure_candidate",
        "paragraph_tail_closure_run", "ending_dense_closure_candidate",
        "functional_micro_loop_candidate",
    }
    missing = sorted(required - kinds)
    if missing:
        raise SystemExit(f"missing expected findings: {missing}")
    if result["verdict"] != "warnings_only_no_detector_claim":
        raise SystemExit("verdict boundary changed")
    if any("score" in item for item in result["findings"]):
        raise SystemExit("structure proxies must not emit scores")
    if any(item.get("action") not in {
        "review_in_context", "read_aloud_then_keep_or_rephrase",
        "keep_if_scene_pressure_supports_it", "review_semantic_function", "review_flag",
    } for item in result["findings"]):
        raise SystemExit("unexpected automatic action")

    scene_run = subprocess.run(
        [sys.executable, str(script), str(scene_path), "--mode", "fiction", "--structure", "--compact"],
        check=True, capture_output=True, text=True, encoding="utf-8", env=child_env,
    )
    scene_result = json.loads(scene_run.stdout)
    scene_kinds = {item["type"] for item in scene_result["findings"]}
    scene_required = {
        "adjacent_paragraph_overlap_candidate",
        "assembly_blank_gap_candidate",
        "late_unestablished_quote_candidate",
        "narrative_negation_proof_cluster_candidate",
        "background_foreground_beat_alignment_candidate",
        "dialogue_narration_syntax_convergence_candidate",
    }
    scene_missing = sorted(scene_required - scene_kinds)
    if scene_missing:
        raise SystemExit(f"missing scene-level regression findings: {scene_missing}")
    if any(item.get("action") != "review_flag" for item in scene_result["findings"] if item["type"] in scene_required):
        raise SystemExit("new scene-level findings must remain review-only")

    exemption_path = base / f".audit-exemptions-self-test-{os.getpid()}.json"
    try:
        exemption_path.write_text(json.dumps({
            "schema": "natural_prose_audit_exemptions_v1",
            "source": str(scene_path.resolve()),
            "exemptions": [{
                "line_start": 1,
                "line_end": 200,
                "finding_types": ["narrative_negation_proof_cluster_candidate"],
                "reason": "object_layer_test",
            }],
        }, ensure_ascii=False), encoding="utf-8")
        exempt_run = subprocess.run(
            [
                sys.executable, str(script), str(scene_path), "--mode", "fiction", "--structure",
                "--exemptions", str(exemption_path), "--compact",
            ],
            check=True, capture_output=True, text=True, encoding="utf-8", env=child_env,
        )
        exempted = json.loads(exempt_run.stdout)
        exempted_kinds = {item["type"] for item in exempted["findings"]}
        if "narrative_negation_proof_cluster_candidate" in exempted_kinds:
            raise SystemExit("line-bound object-layer exemption was not applied")
        if exempted.get("suppressed_finding_count", 0) < 1:
            raise SystemExit("exemption suppression was not recorded")
    finally:
        exemption_path.unlink(missing_ok=True)

    compare_run = subprocess.run(
        [
            sys.executable, str(script), str(path), "--mode", "fiction", "--structure",
            "--baseline", str(path),
            "--target-finding-type", "functional_micro_loop_candidate", "--compact",
        ],
        check=True, capture_output=True, text=True, encoding="utf-8", env=child_env,
    )
    compared = json.loads(compare_run.stdout)
    comparison = compared.get("comparison", {})
    if comparison.get("primary_finding_resolution") != "PRIMARY_FINDING_UNRESOLVED":
        raise SystemExit("baseline comparison failed to preserve unresolved target finding")
    if comparison.get("target_finding_count_before") != comparison.get("target_finding_count_after"):
        raise SystemExit("baseline comparison target counts changed unexpectedly")
    test_unicode_layer_a(base, child_env)
    print("SELF_TEST=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
