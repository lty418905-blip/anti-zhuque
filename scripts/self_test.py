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
    required_manual_review = {
        "blind_full_text_read_before_detector_report",
        "single_primary_finding",
        "localized_surface_vs_distributed_voice_vs_structural",
        "detector_independent_reason",
        "target_alignment_and_full_text_regression",
    }
    if set(result.get("manual_review_required", [])) != required_manual_review:
        raise SystemExit("manual primary-finding review contract changed")

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

    detector_reference = (
        skill_root / "references" / "detector-evidence-workflow.md"
    ).read_text(encoding="utf-8")
    required_detector_terms = {
        "PRIMARY_FINDING",
        "LOCALIZED_SURFACE",
        "DISTRIBUTED_VOICE",
        "STRUCTURAL",
        "DETECTOR_INDEPENDENT_REASON",
        "AUTHOR_LEVEL_REWRITE",
        "TARGET_ALIGNMENT",
        "FULL_TEXT_REGRESSION_CHECK",
        "PRIMARY_FINDING_UNRESOLVED",
    }
    missing_detector_terms = sorted(
        term for term in required_detector_terms if term not in detector_reference
    )
    if missing_detector_terms:
        raise SystemExit(
            f"detector evidence reference missing terms: {missing_detector_terms}"
        )

    public_text_files = [
        path for path in skill_root.rglob("*")
        if (path.is_file()
            and path.suffix.lower() in {".md", ".xml", ".yaml", ".py"}
            and path.name != "self_test.py")
    ]
    public_text = "\n".join(path.read_text(encoding="utf-8") for path in public_text_files)
    forbidden_project_terms = {
        "林砚舟", "赫敏", "D:\\shipinzhizuo", "科研顾问", "世界观审查",
        "GEMINI_PRIMARY", "NEXAPI", "speed.toter.me",
    }
    leaked_terms = sorted(term for term in forbidden_project_terms if term in public_text)
    if leaked_terms:
        raise SystemExit(f"project-specific terms leaked into public skill: {leaked_terms}")

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

    template = (skill_root / "assets" / "structured-single-model-input-v1.xml").read_text(
        encoding="utf-8"
    )
    replacements = {
        "MODE": "GENERATE_THEN_AUDIT",
        "GENRE": "小说章节",
        "REALITY_CONTRACT": "FICTION",
        "DELIVERABLE": "FINAL_TEXT_ONLY",
        "LENGTH_UNIT": "zh_characters",
        "TARGET_MIN": "1000",
        "TARGET_MAX": "2000",
        "OUTPUT_FORMAT": "纯正文",
        "MUST_INCLUDE": "人物作出一次选择",
        "MUST_NOT_INCLUDE": "创作过程",
        "SPEAKER": "第一人称叙述者",
        "KNOWLEDGE_BASIS": "只知道亲历与已获知内容",
        "CURRENT_REASON_TO_WRITE": "记录当天发生的冲突",
        "READER": "普通中文读者",
        "DESIRED_EFFECT": "清楚而有生活感",
        "SOURCE_STATUS": "FICTION_AUTHORIZED",
        "SOURCE_MATERIAL": "人物、场景与事件大纲",
        "KNOWN_UNKNOWNS": "次要人物后续反应未知",
        "RESEARCH_PERMISSION": "不需要外部研究",
        "FROZEN_FACTS_AND_EVIDENCE": "时间地点与事件顺序",
        "FROZEN_CAUSALITY_AND_POSITION": "选择导致关系变化",
        "FROZEN_VOICE_OR_CHARACTER_KNOWLEDGE": "第一人称且不得全知",
        "FROZEN_EXAMPLES_OR_PLOT_BEATS": "进入、冲突、选择、离场",
        "VOICE": "日常、具体、克制",
        "TONE": "轻松中带一点压力",
        "POINT_OF_VIEW": "第一人称",
        "FORM_CONSTRAINTS": "连续叙事，不输出标题",
        "HIGHLIGHTS_TO_PRESERVE": "笨拙但真实的幽默",
        "UNIT_1_LENGTH": "1500",
        "UNIT_1_FUNCTION": "完成冲突与选择",
        "UNIT_1_MATERIAL_OR_ACTION": "对话、误解和具体动作",
        "UNIT_1_CHANGE_OR_CONSEQUENCE": "双方距离发生小幅变化",
        "UNIT_1_EXIT": "在一个未解决的小问题处停下",
        "REVISION_SCOPE": "只修表达、节奏和重复功能",
        "DO_NOT_CHANGE": "事实、因果、人物知识和结尾接口",
        "SOURCE_TEXT_OR_NOT_APPLICABLE": "NOT_APPLICABLE",
    }
    filled = template
    for key, value in replacements.items():
        filled = filled.replace("{{" + key + "}}", value)
    if "{{" in filled:
        raise SystemExit("structured input test did not fill every placeholder")

    test_temp_root = base / f".self-test-{os.getpid()}"
    if test_temp_root.exists():
        raise SystemExit(f"self-test path already exists: {test_temp_root}")
    test_temp_root.mkdir()
    valid_path = test_temp_root / "valid.xml"
    invalid_path = test_temp_root / "invalid.xml"
    try:
        valid_path.write_text(filled, encoding="utf-8")
        valid_run = subprocess.run(
            [sys.executable, str(base / "validate_structured_input.py"), str(valid_path)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )
        if valid_run.returncode != 0 or "STRUCTURED_INPUT_VALID=PASS" not in valid_run.stdout:
            raise SystemExit(
                "structured input validator rejected valid fixture: " + valid_run.stderr
            )

        invalid_path.write_text(
            filled.replace("<suggested_length>1500</suggested_length>", "<suggested_length>2500</suggested_length>"),
            encoding="utf-8",
        )
        invalid_run = subprocess.run(
            [sys.executable, str(base / "validate_structured_input.py"), str(invalid_path)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )
        if invalid_run.returncode != 1 or "sum of structure unit suggested_length" not in invalid_run.stderr:
            raise SystemExit("structured input validator did not reject invalid length budget")
    finally:
        if valid_path.exists():
            valid_path.unlink()
        if invalid_path.exists():
            invalid_path.unlink()
        test_temp_root.rmdir()

    split_template = (
        skill_root / "assets" / "structured-single-model-input-v2-split.xml"
    ).read_text(encoding="utf-8")
    for required_phase in (
        "<detector_evidence_phase>",
        "<post_revision_phase>",
    ):
        if required_phase not in split_template:
            raise SystemExit(f"split template missing phase: {required_phase}")
    split_replacements = dict(replacements)
    split_replacements.update(
        {
            "GENERATION_SCOPE": "PART_2",
            "WORK_ID": "TEST-WORK-001",
            "DRAFT_ROUND_ID": "TEST-DRAFT-001",
            "FULL_WORK_TARGET_MIN": "2000",
            "FULL_WORK_TARGET_MAX": "4000",
            "SPLIT_MODE": "TWO_PART_CONTINUATION",
            "PART_SEQUENCE": "2_OF_2",
            "PRIOR_PART_STATUS": "COMPLETE_SAME_MODEL_SAME_DRAFT",
            "PLANNED_ENTRY": "承接上半部最后一个动作",
            "PLANNED_EXIT": "完成冲突并留下一个实际后果",
            "LAST_VISIBLE_ACTION": "叙述者把未读完的纸放回桌面",
            "TIME_PLACE_AND_BODY": "同一天下午，同一房间，人物仍坐在桌边",
            "KNOWLEDGE_AND_RELATIONSHIP": "双方只知道已经说出口的内容，关系仍有保留",
            "OBJECTS_AND_OPEN_THREADS": "纸在桌上，一个问题尚未回答",
            "DO_NOT_REPEAT": "不重复人物介绍、房间介绍和上半部争论",
            "SAME_DRAFT_PRIOR_PART_OR_NOT_APPLICABLE": "这是同一模型同一草稿轮次已经完成的完整上半部。",
        }
    )
    split_filled = split_template
    for key, value in split_replacements.items():
        split_filled = split_filled.replace("{{" + key + "}}", value)
    if "{{" in split_filled:
        raise SystemExit("split structured input test did not fill every placeholder")

    split_temp_root = base / f".self-test-split-{os.getpid()}"
    if split_temp_root.exists():
        raise SystemExit(f"self-test path already exists: {split_temp_root}")
    split_temp_root.mkdir()
    split_valid_path = split_temp_root / "valid-part2.xml"
    split_invalid_path = split_temp_root / "invalid-part2.xml"
    try:
        split_valid_path.write_text(split_filled, encoding="utf-8")
        split_valid_run = subprocess.run(
            [sys.executable, str(base / "validate_structured_input.py"), str(split_valid_path)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )
        if split_valid_run.returncode != 0 or "STRUCTURED_INPUT_VALID=PASS" not in split_valid_run.stdout:
            raise SystemExit(
                "structured input validator rejected valid PART_2 fixture: "
                + split_valid_run.stderr
            )

        split_invalid_path.write_text(
            split_filled.replace(
                "这是同一模型同一草稿轮次已经完成的完整上半部。",
                "NOT_APPLICABLE",
            ),
            encoding="utf-8",
        )
        split_invalid_run = subprocess.run(
            [sys.executable, str(base / "validate_structured_input.py"), str(split_invalid_path)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )
        if split_invalid_run.returncode != 1 or "PART_2 requires complete same_draft_prior_part" not in split_invalid_run.stderr:
            raise SystemExit("structured input validator did not reject PART_2 without prior fulltext")
    finally:
        if split_valid_path.exists():
            split_valid_path.unlink()
        if split_invalid_path.exists():
            split_invalid_path.unlink()
        split_temp_root.rmdir()

    print("SELF_TEST=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
