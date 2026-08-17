#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def fixture() -> dict:
    return {
        "schema": "STRUCTURED_WRITING_INPUT_V1",
        "task_id": "TEST-STORY",
        "task_mode": "FICTION_SCENE",
        "language": "zh-CN",
        "user_request": {
            "original_instruction": "写一段两位旧友在停电咖啡馆重逢的短篇场景。",
            "intended_audience": "普通成年读者",
            "purpose": "呈现客气话下面尚未解决的误会",
        },
        "source_contract": {"materials": [], "unlisted_sources_allowed": False},
        "fact_contract": {
            "immutable_facts": ["停电发生在两人见面之前", "不声称任何外部事实已被核验"],
            "prohibited_inferences": ["不得确认误会由第三人故意制造"],
        },
        "character_and_pov": {
            "pov": "第三人称限知",
            "narrator": "跟随先到咖啡馆的人",
            "participants": ["旧友甲", "旧友乙"],
            "knowledge_boundaries": ["视角人物不知道对方是否看过旧信"],
        },
        "scenes": [{
            "scene_id": "SCENE-01",
            "setting": "停电后的咖啡馆",
            "immediate_goal": "在照明恢复前决定是否提起旧信",
            "required_beats": ["两人认出彼此", "谈话留下未决余波"],
            "forbidden_changes": ["不得让两人当场彻底和解"],
        }],
        "event_contract": {
            "source": "NONE",
            "selected_event_cards": [],
            "seed_library_included": False,
            "full_candidate_library_included": False,
            "rejected_events_included": False,
        },
        "positive_style_requirements": ["对白保留礼貌与迟疑之间的落差"],
        "length_contract": {
            "source": "UNSPECIFIED",
            "instruction": "UNSPECIFIED",
            "parsed": {"min": None, "max": None, "unit": None},
        },
        "output_contract": {
            "format": "PLAIN_TEXT",
            "title_policy": "NONE",
            "title": None,
            "additional_requirements": [],
        },
        "completion_conditions": ["场景以一个仍会影响下次见面的动作结束"],
        "generation_input_scope": "POSITIVE_WRITING_ONLY",
    }


def run_case(validator: Path, path: Path, payload: dict, expected: tuple[str, ...], should_pass: bool) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    run = subprocess.run(
        [sys.executable, str(validator), str(path), "--compact"],
        capture_output=True, text=True, encoding="utf-8", env=env,
    )
    result = json.loads(run.stdout)
    if should_pass and (run.returncode != 0 or result["status"] != "PASS"):
        raise SystemExit(f"positive case failed: {result}")
    if not should_pass:
        if run.returncode == 0 or result["status"] != "FAIL":
            raise SystemExit("negative case unexpectedly passed")
        joined = "\n".join(result["errors"])
        for needle in expected:
            if needle not in joined:
                raise SystemExit(f"negative case missed expected error: {needle}")


def main() -> int:
    base = Path(__file__).resolve().parent
    validator = base / "validate_structured_writing_input.py"
    root = base / f".structured-input-self-test-{os.getpid()}"
    if root.exists():
        raise SystemExit(f"self-test directory already exists: {root}")
    root.mkdir()
    try:
        run_case(validator, root / "valid-unspecified.json", fixture(), (), True)

        template = json.loads(
            (base.parent / "assets" / "structured-writing-input-template.json").read_text(encoding="utf-8")
        )
        run_case(
            validator,
            root / "bad-unfilled-template.json",
            template,
            ("unresolved template placeholder",),
            False,
        )

        explicit = fixture()
        explicit["user_request"]["original_instruction"] = "请写1200到1800字，保留开放结尾。"
        explicit["length_contract"] = {
            "source": "USER_NATURAL_LANGUAGE",
            "instruction": "请写1200到1800字，保留开放结尾。",
            "parsed": {"min": 1200, "max": 1800, "unit": "字"},
        }
        run_case(validator, root / "valid-explicit.json", explicit, (), True)

        no_length_with_number = fixture()
        no_length_with_number["length_contract"]["parsed"]["min"] = 1000
        run_case(validator, root / "bad-unspecified-number.json", no_length_with_number, ("must keep min, max, and unit null",), False)

        inferred = fixture()
        inferred["length_contract"] = {
            "source": "AGENT_INFERRED",
            "instruction": "适合短篇",
            "parsed": {"min": 1000, "max": None, "unit": "字"},
        }
        run_case(validator, root / "bad-inferred.json", inferred, ("length source must be",), False)

        full_library = fixture()
        full_library["event_contract"]["full_candidate_library_included"] = True
        run_case(validator, root / "bad-library.json", full_library, ("full_candidate_library_included must be false",), False)

        hidden_library = fixture()
        hidden_library["event_library"] = [{"event_id": "EV-CANDIDATE", "status": "CANDIDATE"}]
        run_case(validator, root / "bad-hidden-library.json", hidden_library, ("forbidden field in generation input",), False)

        rejected = fixture()
        rejected["event_contract"]["source"] = "SCENE_EVENT_WEAVER_SELECTED_ONLY"
        rejected["event_contract"]["selected_event_cards"] = [{"event_id": "EV-1", "status": "REJECTED"}]
        run_case(validator, root / "bad-rejected.json", rejected, ("must have status SELECTED",), False)

        missing_facts = fixture()
        missing_facts["fact_contract"]["immutable_facts"] = []
        run_case(validator, root / "bad-facts.json", missing_facts, ("requires non-empty immutable_facts",), False)

        leaked_audit = fixture()
        leaked_audit["audit_checklist"] = ["逐项检测句式"]
        run_case(validator, root / "bad-audit.json", leaked_audit, ("forbidden field in generation input",), False)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print("STRUCTURED_INPUT_SELF_TEST=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
