#!/usr/bin/env python3
"""Emit conservative, non-blocking shape warnings for Chinese prose.

The script never edits input, never calls a network service, and never claims
to detect authorship or reproduce a commercial AIGC detector.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from pathlib import Path


TRANSITIONS = (
    "首先", "其次", "最后", "此外", "另外", "与此同时", "综上所述",
    "值得注意的是", "需要指出的是", "从某种意义上说",
)

EPISTEMIC_LIMITERS = (
    "我不知道", "我不确定", "判断不了", "无法判断", "不能证明", "证明不了",
    "只能说明", "只说明", "不代表", "不等于", "不能推出", "无法推出",
    "不声称", "只能确认", "仅能确认", "至多说明", "不能据此",
)

ENUMERATION_MARKERS = (
    "一种可能", "另一种可能", "还有一种", "两个解释", "三种解释",
    "第一种", "第二种", "三个版本", "几种解释",
)

RETURN_TO_EVIDENCE = (
    "能确认", "只能确认", "只能说明", "只剩", "至少能", "证据", "事实是",
)

ANSWER_CLOSURE_MARKERS = (
    "意思是", "也就是说", "指的是", "定义", "只能", "不等于", "不能证明",
    "证明不了", "可以确认", "不能推出",
)

ACTION_MARKERS = (
    "抬眼", "抬头", "低头", "看着", "看了", "停手", "放下", "敲了",
    "点了点", "转过身", "往前", "后退", "站在", "挪了", "收回手",
)

ARGUMENT_MARKERS = (
    "所以", "说明", "证明", "意味着", "只能", "不等于", "不是", "但是", "但",
)

ENDING_CLOSURE_MARKERS = (
    "所以", "原来", "这意味着", "这才", "终于", "我明白", "问题", "答案",
)


def split_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[。！？!?…])", text) if part.strip()]


def visible_length(sentence: str) -> int:
    return len(re.sub(r"\s|[，。！？!?；;：:\"'“”‘’（）()《》〈〉…]", "", sentence))


def line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def lexical_findings(text: str) -> list[dict]:
    findings: list[dict] = []
    for term in TRANSITIONS:
        starts = [match.start() for match in re.finditer(re.escape(term), text)]
        if starts:
            findings.append({
                "type": "transition_cluster_candidate",
                "term": term,
                "count": len(starts),
                "lines": [line_for_offset(text, pos) for pos in starts[:12]],
                "action": "review_in_context",
            })
    return findings


def rhythm_findings(sentences: list[str]) -> list[dict]:
    findings: list[dict] = []
    lengths = [visible_length(sentence) for sentence in sentences]

    for index in range(max(0, len(lengths) - 4)):
        window = lengths[index:index + 5]
        mean = statistics.fmean(window)
        if mean and statistics.pstdev(window) / mean < 0.12:
            findings.append({
                "type": "uniform_sentence_window",
                "sentence_range": [index + 1, index + 5],
                "lengths": window,
                "action": "read_aloud_then_keep_or_rephrase",
            })

    for index in range(max(0, len(sentences) - 2)):
        starts = [re.sub(r"^[\s\"'“”‘’（(]+", "", sentence)[:2]
                  for sentence in sentences[index:index + 3]]
        if starts[0] and len(set(starts)) == 1:
            findings.append({
                "type": "repeated_sentence_start",
                "sentence_range": [index + 1, index + 3],
                "start": starts[0],
                "action": "review_in_context",
            })
    return findings


def template_findings(text: str) -> list[dict]:
    patterns = {
        "reversal_template": r"不是[^。！？\n]{0,45}(?:而是|是)[^。！？\n]{0,45}",
        "three_step_transition": r"首先[^。！？\n]{0,120}其次[^。！？\n]{0,120}最后",
    }
    findings: list[dict] = []
    for kind, pattern in patterns.items():
        for match in re.finditer(pattern, text):
            findings.append({
                "type": kind,
                "line": line_for_offset(text, match.start()),
                "excerpt": match.group(0)[:100],
                "action": "review_semantic_function",
            })
    return findings


def structure_findings(text: str, sentences: list[str], paragraphs: list[str]) -> list[dict]:
    findings: list[dict] = []

    last_end = -1
    for index in range(max(0, len(sentences) - 5)):
        joined = "".join(sentences[index:index + 6])
        hits = [term for term in EPISTEMIC_LIMITERS if term in joined]
        total = sum(joined.count(term) for term in EPISTEMIC_LIMITERS)
        if total >= 3 and len(hits) >= 2 and index > last_end:
            findings.append({
                "type": "epistemic_limiter_cluster",
                "sentence_range": [index + 1, index + 6],
                "terms": hits[:8],
                "action": "review_flag",
                "note": "Keep limiters required for evidence strength or technical accuracy.",
            })
            last_end = index + 5

    enumeration = "|".join(re.escape(term) for term in ENUMERATION_MARKERS)
    return_to_evidence = "|".join(
        re.escape(term) for term in EPISTEMIC_LIMITERS + RETURN_TO_EVIDENCE
    )
    cycle_pattern = re.compile(rf"(?:{enumeration})[^\n]{{0,260}}?(?:{return_to_evidence})")
    for match in list(cycle_pattern.finditer(text))[:12]:
        findings.append({
            "type": "cognitive_audit_cycle_candidate",
            "line": line_for_offset(text, match.start()),
            "excerpt": match.group(0)[:140],
            "action": "review_flag",
            "note": "Keep full reasoning when it changes risk, relationship, resources, or action.",
        })

    question_pairs: list[int] = []
    for index, sentence in enumerate(sentences):
        if "？" not in sentence and "?" not in sentence:
            continue
        answer = "".join(sentences[index + 1:index + 3])
        if any(marker in answer for marker in ANSWER_CLOSURE_MARKERS):
            question_pairs.append(index)
    for start in range(len(question_pairs)):
        run = [item for item in question_pairs[start:] if item - question_pairs[start] <= 12]
        if len(run) >= 3:
            findings.append({
                "type": "question_answer_unit_test_run",
                "sentence_range": [run[0] + 1, run[2] + 3],
                "closure_pairs": len(run),
                "action": "review_flag",
                "note": "Check delayed answers and human priorities without weakening accuracy.",
            })
            break

    paired: list[int] = []
    for index, sentence in enumerate(sentences):
        nearby = "".join(sentences[index:index + 2])
        if (any(action in sentence for action in ACTION_MARKERS)
                and any(marker in nearby for marker in ARGUMENT_MARKERS)):
            paired.append(index)
    for start in range(len(paired)):
        run = [item for item in paired[start:] if item - paired[start] <= 10]
        if len(run) >= 3:
            findings.append({
                "type": "action_argument_pair_run",
                "sentence_range": [run[0] + 1, run[2] + 2],
                "pair_count": len(run),
                "action": "review_flag",
                "note": "Keep spatial and relational actions; inspect repeated rhetorical accompaniment.",
            })
            break

    if paragraphs:
        tail_count = min(3, len(paragraphs))
        body = "\n".join(paragraphs[:-tail_count])
        tail = "\n".join(paragraphs[-tail_count:])
        repeated = [term for term in ENDING_CLOSURE_MARKERS if term in body and term in tail]
        if len(repeated) >= 3:
            findings.append({
                "type": "ending_dense_closure_candidate",
                "paragraph_range": [len(paragraphs) - tail_count + 1, len(paragraphs)],
                "repeated_markers": repeated[:8],
                "action": "review_flag",
                "note": "Preserve required conclusions and interfaces before trimming closure.",
            })

    return findings


def analyze(path: Path, mode: str, structure: bool) -> dict:
    text = path.read_text(encoding="utf-8")
    sentences = split_sentences(text)
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    findings = lexical_findings(text)
    findings += rhythm_findings(sentences)
    findings += template_findings(text)
    if structure:
        findings += structure_findings(text, sentences, paragraphs)
    return {
        "schema": "natural_prose_audit_v1",
        "source": str(path.resolve()),
        "mode": mode,
        "statistics": {
            "characters": len(text),
            "sentences": len(sentences),
            "paragraphs": len(paragraphs),
            "structure_enabled": structure,
        },
        "finding_count": len(findings),
        "findings": findings,
        "verdict": "warnings_only_no_authorship_or_detector_claim",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Non-blocking naturalness audit for Chinese prose")
    parser.add_argument("text_path", type=Path)
    parser.add_argument("--mode", choices=("fiction", "nonfiction", "general"), default="general")
    parser.add_argument("--structure", action="store_true", help="add conservative deep-structure proxies")
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()

    if not args.text_path.is_file():
        parser.error(f"file not found: {args.text_path}")
    result = analyze(args.text_path, args.mode, args.structure)
    print(json.dumps(result, ensure_ascii=False, indent=None if args.compact else 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
