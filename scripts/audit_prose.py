#!/usr/bin/env python3
"""Emit non-blocking shape warnings for Chinese prose. Never edits text."""

from __future__ import annotations

import argparse
from collections import Counter
from difflib import SequenceMatcher
import json
import re
import statistics
from pathlib import Path


TRANSITIONS = (
    "首先", "其次", "最后", "此外", "另外", "与此同时", "综上所述",
    "值得注意的是", "需要指出的是", "从某种意义上说",
)

AUTHOR_METAPHORS = ("算账", "这笔账", "把账算清")

NOVEL_CLICHES = (
    "瞳孔骤缩", "倒吸一口凉气", "空气仿佛凝固", "满场死寂",
    "眼中闪过一丝", "嘴角上扬", "攥紧了拳头",
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
    "所以", "说明", "证明", "意味着", "只能", "不等于", "不是", "但",
)

ENDING_CLOSURE_MARKERS = (
    "所以", "原来", "这意味着", "这才", "终于", "我明白", "问题", "答案",
    "这笔账", "算清",
)

INTERPRETATION_MARKERS = (
    "这意味着", "这说明", "等于", "也就是说", "显然", "我意识到", "我明白",
    "我知道", "她是在", "他是在", "像是在", "仿佛是在",
)

MICRO_LOOP_FUNCTION_MARKERS = {
    "scene_reset": (
        "安静了一瞬", "又开始", "重新开始", "声音冒出来", "声音又", "动起来",
        "松开了一样", "重新", "再次",
    ),
    "attempt_or_restaging": (
        "又试", "再试", "试了一次", "重新握", "重新拿", "又拿", "又放",
        "再问", "又问", "重新说", "再说",
    ),
    "epistemic_recheck": EPISTEMIC_LIMITERS + (
        "可能是", "也可能", "说不清", "没办法确认", "无法确认", "不能确定",
        "像是", "好像", "会不会",
    ),
    "local_closure": (
        "什么都没发生", "还是没", "仍然没", "没有再", "没再", "一动不动",
        "就这样", "到这里", "算了", "没结果",
    ),
    "explanation_or_summary": (
        "关键是", "实际做", "写下来", "不要编", "也就是说", "这说明",
        "这意味着", "所以", "不等于",
    ),
}

EXCLUSION_PATTERNS = (
    re.compile(r"没有[^。！？\n]{0,45}也没有"),
    re.compile(r"既没有[^。！？\n]{0,45}也没有"),
    re.compile(r"不曾[^。！？\n]{0,45}也不曾"),
    re.compile(r"并未[^。！？\n]{0,45}(?:也|更)(?:未|没有)"),
)

NARRATIVE_NEGATION_PATTERN = re.compile(
    r"(?:没(?:有)?|并未|不曾)[^。！？!?\n]{0,55}"
)

BACKGROUND_BEAT_MARKERS = (
    "下棋", "棋盘", "棋子", "拍桌", "壁炉", "柴火", "星象图", "楼梯",
    "画像洞口", "脚步", "笑声", "说话声", "响了一声", "声音",
)

FOREGROUND_PAUSE_MARKERS = (
    "没催", "没有催", "等着", "等了一下", "停住", "停了一下", "悬在",
    "沉默", "没说话", "没有说话", "十几秒", "片刻", "没马上答",
)

RETURN_TO_TEXT_CUES = re.compile(
    r"(?:目光|视线|眼睛)[^。！？!?\n]{0,18}(?:落回|回到|移回|转回)|"
    r"(?:又|重新|再)(?:读|看)[^。！？!?\n]{0,12}"
)

QUOTE_SPAN_PATTERN = re.compile(r'[\"“]([^\"”\n]{2,240})[\"”]')

VOICE_SIGNATURE_PATTERNS = {
    "self_equation": re.compile(r"(?P<term>[\u4e00-\u9fff]{1,6})是(?P=term)"),
    "binary_boundary": re.compile(r"不等于|另一回事|没有第三条路|一种[^。！？!?\n]{0,40}另一种"),
    "contrast_definition": re.compile(r"不是[^。！？!?\n]{0,28}(?:而是|是)"),
}


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[。！？!?…])", text) if s.strip()]


def visible_length(sentence: str) -> int:
    return len(re.sub(r"\s|[，。！？!?；;：:\"'“”‘’（）()《》〈〉…]", "", sentence))


def line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def locate_units(text: str, units: list[str]) -> list[tuple[int, int]]:
    """Map already-split units back to inclusive source line ranges."""
    located: list[tuple[int, int]] = []
    cursor = 0
    for unit in units:
        start = text.find(unit, cursor)
        if start < 0:
            start = text.find(unit)
        if start < 0:
            located.append((1, 1))
            continue
        end = start + len(unit)
        located.append((line_for_offset(text, start), line_for_offset(text, max(start, end - 1))))
        cursor = end
    return located


def normalize_overlap_text(text: str) -> str:
    return re.sub(r"[^\u3400-\u4dbf\u4e00-\u9fffA-Za-z0-9]", "", text)


def annotate_line_ranges(
    findings: list[dict],
    sentence_lines: list[tuple[int, int]],
    paragraph_lines: list[tuple[int, int]],
) -> list[dict]:
    for finding in findings:
        line_range: tuple[int, int] | None = None
        if "line_range" in finding:
            raw = finding["line_range"]
            line_range = (int(raw[0]), int(raw[1]))
        elif "line" in finding:
            line = int(finding["line"])
            line_range = (line, line)
        elif finding.get("lines"):
            lines = [int(x) for x in finding["lines"]]
            line_range = (min(lines), max(lines))
        elif "sentence_range" in finding and sentence_lines:
            start, end = finding["sentence_range"]
            start_i = max(0, int(start) - 1)
            end_i = min(len(sentence_lines) - 1, int(end) - 1)
            line_range = (sentence_lines[start_i][0], sentence_lines[end_i][1])
        elif "paragraph" in finding and paragraph_lines:
            index = max(0, int(finding["paragraph"]) - 1)
            if index < len(paragraph_lines):
                line_range = paragraph_lines[index]
        elif "paragraph_range" in finding and paragraph_lines:
            start, end = finding["paragraph_range"]
            start_i = max(0, int(start) - 1)
            end_i = min(len(paragraph_lines) - 1, int(end) - 1)
            line_range = (paragraph_lines[start_i][0], paragraph_lines[end_i][1])
        elif finding.get("paragraphs") and paragraph_lines:
            indexes = [max(0, int(x) - 1) for x in finding["paragraphs"]]
            indexes = [x for x in indexes if x < len(paragraph_lines)]
            if indexes:
                line_range = (
                    min(paragraph_lines[x][0] for x in indexes),
                    max(paragraph_lines[x][1] for x in indexes),
                )
        if line_range is not None:
            finding["line_range"] = [line_range[0], line_range[1]]
    return findings


def load_exemptions(path: Path | None, source: Path) -> list[dict]:
    if path is None:
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "natural_prose_audit_exemptions_v1":
        raise ValueError("unsupported exemptions schema")
    declared_source = Path(payload.get("source", "")).resolve()
    if declared_source != source.resolve():
        raise ValueError("exemptions source path does not match audited source")
    exemptions: list[dict] = []
    for item in payload.get("exemptions", []):
        start = int(item.get("line_start", 0))
        end = int(item.get("line_end", 0))
        kinds = item.get("finding_types")
        reason = str(item.get("reason", "")).strip()
        if start < 1 or end < start or not isinstance(kinds, list) or not kinds or not reason:
            raise ValueError("invalid exemption entry")
        exemptions.append({
            "line_start": start,
            "line_end": end,
            "finding_types": [str(x) for x in kinds],
            "reason": reason,
        })
    return exemptions


def apply_exemptions(findings: list[dict], exemptions: list[dict]) -> tuple[list[dict], list[dict]]:
    kept: list[dict] = []
    suppressed: list[dict] = []
    for finding in findings:
        line_range = finding.get("line_range")
        matched = None
        if line_range:
            for exemption in exemptions:
                kinds = exemption["finding_types"]
                if finding["type"] not in kinds and "*" not in kinds:
                    continue
                if exemption["line_start"] <= line_range[0] and line_range[1] <= exemption["line_end"]:
                    matched = exemption
                    break
        if matched is None:
            kept.append(finding)
        else:
            suppressed.append({
                "type": finding["type"],
                "line_range": line_range,
                "reason": matched["reason"],
            })
    return kept, suppressed


def lexical_findings(text: str, mode: str) -> list[dict]:
    terms = [(x, "transition") for x in TRANSITIONS]
    terms += [(x, "author_metaphor") for x in AUTHOR_METAPHORS]
    if mode == "fiction":
        terms += [(x, "novel_cliche") for x in NOVEL_CLICHES]

    findings: list[dict] = []
    for term, kind in terms:
        starts = [m.start() for m in re.finditer(re.escape(term), text)]
        if not starts:
            continue
        findings.append({
            "type": kind,
            "term": term,
            "count": len(starts),
            "lines": [line_for_offset(text, p) for p in starts[:12]],
            "action": "review_in_context",
        })
    return findings


def rhythm_findings(sentences: list[str]) -> list[dict]:
    findings: list[dict] = []
    lengths = [visible_length(s) for s in sentences]

    for i in range(max(0, len(lengths) - 4)):
        window = lengths[i:i + 5]
        mean = statistics.fmean(window)
        if mean and statistics.pstdev(window) / mean < 0.12:
            findings.append({
                "type": "uniform_sentence_window",
                "sentence_range": [i + 1, i + 5],
                "lengths": window,
                "action": "read_aloud_then_keep_or_rephrase",
            })

    run_start = None
    for i, length in enumerate(lengths + [999]):
        if length <= 7 and run_start is None:
            run_start = i
        elif length > 7 and run_start is not None:
            if i - run_start >= 4:
                findings.append({
                    "type": "short_sentence_run",
                    "sentence_range": [run_start + 1, i],
                    "action": "keep_if_scene_pressure_supports_it",
                })
            run_start = None

    for i in range(max(0, len(sentences) - 2)):
        starts = [re.sub(r"^[\s\"'“”‘’（(]+", "", s)[:2] for s in sentences[i:i + 3]]
        if starts[0] and len(set(starts)) == 1:
            findings.append({
                "type": "repeated_sentence_start",
                "sentence_range": [i + 1, i + 3],
                "start": starts[0],
                "action": "review_in_context",
            })
    return findings


def pattern_findings(text: str) -> list[dict]:
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
                "excerpt": match.group(0)[:80],
                "action": "review_semantic_function",
            })
    return findings


def paragraph_function_tags(paragraph: str) -> set[str]:
    return {
        function
        for function, markers in MICRO_LOOP_FUNCTION_MARKERS.items()
        if any(marker in paragraph for marker in markers)
    }


def functional_micro_loop_findings(paragraphs: list[str]) -> list[dict]:
    """Flag nearby paragraphs that repeat the same narrative function.

    Surface wording and objects may differ. This is only a coarse reminder to
    compare full scene function; it never authorizes automatic deletion.
    """
    tagged = [paragraph_function_tags(paragraph) for paragraph in paragraphs]
    findings: list[dict] = []
    used_until = -1
    for start in range(len(paragraphs)):
        if start <= used_until or len(tagged[start]) < 2:
            continue
        end_limit = min(len(paragraphs), start + 12)
        for second in range(start + 1, end_limit):
            if len(tagged[second]) < 2:
                continue
            shared_pair = tagged[start] & tagged[second]
            if len(shared_pair) < 2:
                continue
            for third in range(second + 1, end_limit):
                shared = shared_pair & tagged[third]
                if len(shared) < 2:
                    continue
                if not (
                    "epistemic_recheck" in shared
                    or "explanation_or_summary" in shared
                    or "scene_reset" in shared
                ):
                    continue
                findings.append({
                    "type": "functional_micro_loop_candidate",
                    "paragraphs": [start + 1, second + 1, third + 1],
                    "paragraph_range": [start + 1, third + 1],
                    "shared_functions": sorted(shared),
                    "action": "review_flag",
                    "note": (
                        "Compare narrative function rather than repeated wording. "
                        "Keep distinct beats that change action, risk, relationship, or knowledge."
                    ),
                })
                used_until = third
                break
            if used_until >= start:
                break
    return findings


def adjacent_paragraph_overlap_findings(
    paragraphs: list[str], paragraph_lines: list[tuple[int, int]]
) -> list[dict]:
    findings: list[dict] = []
    for index in range(len(paragraphs) - 1):
        left = normalize_overlap_text(paragraphs[index])
        right = normalize_overlap_text(paragraphs[index + 1])
        if len(left) < 8 or len(right) < 8:
            continue
        match = SequenceMatcher(None, left, right, autojunk=False).find_longest_match(
            0, len(left), 0, len(right)
        )
        if match.size < 8:
            continue
        excerpt = left[match.a:match.a + match.size]
        if len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", excerpt)) < 6:
            continue
        findings.append({
            "type": "adjacent_paragraph_overlap_candidate",
            "paragraph_range": [index + 1, index + 2],
            "line_range": [paragraph_lines[index][0], paragraph_lines[index + 1][1]],
            "overlap": excerpt[:80],
            "overlap_characters": match.size,
            "action": "review_flag",
            "note": "Check fusion or split-assembly duplication before any naturalness edit.",
        })
    return findings


def assembly_blank_gap_findings(text: str) -> list[dict]:
    findings: list[dict] = []
    for match in re.finditer(r"\n(?:[ \t]*\n){2,}", text):
        start_line = line_for_offset(text, match.start())
        end_line = line_for_offset(text, match.end())
        if match.end() >= len(text.rstrip()) - 1:
            continue
        findings.append({
            "type": "assembly_blank_gap_candidate",
            "line_range": [start_line, end_line],
            "blank_line_run": max(2, end_line - start_line),
            "action": "review_flag",
            "note": "Extra blank space can be intentional; verify against the assembly lineage and source parts.",
        })
    return findings


def late_unestablished_quote_findings(text: str) -> list[dict]:
    findings: list[dict] = []
    seen: set[tuple[int, str]] = set()
    for cue in RETURN_TO_TEXT_CUES.finditer(text):
        tail = text[cue.end():cue.end() + 80]
        quote = QUOTE_SPAN_PATTERN.search(tail)
        if quote is None:
            continue
        after_quote = tail[quote.end():quote.end() + 12]
        if re.search(r"(?:我|他|她|[\u4e00-\u9fff]{2,5})(?:说|问|答|道)", after_quote):
            continue
        content = normalize_overlap_text(quote.group(1))
        if len(content) < 4:
            continue
        prefix = normalize_overlap_text(text[:cue.start()])
        if content in prefix:
            continue
        quote_start = cue.end() + quote.start()
        key = (line_for_offset(text, quote_start), content)
        if key in seen:
            continue
        seen.add(key)
        findings.append({
            "type": "late_unestablished_quote_candidate",
            "line_range": [line_for_offset(text, cue.start()), line_for_offset(text, quote_start)],
            "quote": quote.group(1)[:80],
            "action": "review_flag",
            "note": "A return-to-text cue introduces wording not previously established verbatim; verify the quoted source and referent.",
        })
    return findings


def narrative_negation_cluster_findings(
    paragraphs: list[str], paragraph_lines: list[tuple[int, int]]
) -> list[dict]:
    hit_paragraphs: list[tuple[int, int]] = []
    for index, paragraph in enumerate(paragraphs):
        narration = QUOTE_SPAN_PATTERN.sub("", paragraph)
        hits = NARRATIVE_NEGATION_PATTERN.findall(narration)
        if hits:
            hit_paragraphs.append((index, len(hits)))

    findings: list[dict] = []
    used_until = -1
    for start_pos, (start_index, _) in enumerate(hit_paragraphs):
        if start_index <= used_until:
            continue
        cluster = [
            item for item in hit_paragraphs[start_pos:]
            if item[0] - start_index <= 18
        ]
        total = sum(count for _, count in cluster)
        if len(cluster) < 4 or total < 4:
            continue
        end_index = cluster[-1][0]
        findings.append({
            "type": "narrative_negation_proof_cluster_candidate",
            "paragraph_range": [start_index + 1, end_index + 1],
            "line_range": [paragraph_lines[start_index][0], paragraph_lines[end_index][1]],
            "paragraph_hits": len(cluster),
            "clause_hits": total,
            "action": "review_flag",
            "note": (
                "Separate plot-bearing non-events from procedural proof of things that did not happen. "
                "Exempt scientific limits, object-layer classification, and relationship boundaries before editing."
            ),
        })
        used_until = end_index
    return findings


def background_pause_alignment_findings(
    paragraphs: list[str], paragraph_lines: list[tuple[int, int]]
) -> list[dict]:
    aligned: list[int] = []
    for index, paragraph in enumerate(paragraphs):
        if not any(marker in paragraph for marker in BACKGROUND_BEAT_MARKERS):
            continue
        if not any(marker in paragraph for marker in FOREGROUND_PAUSE_MARKERS):
            continue
        if not any(focal in paragraph for focal in ("我", "她", "他", "它", "他们", "她们")):
            continue
        aligned.append(index)
    findings: list[dict] = []
    for start in range(len(aligned)):
        nearby = [index for index in aligned[start:] if index - aligned[start] <= 25]
        if len(nearby) < 2:
            continue
        findings.append({
            "type": "background_foreground_beat_alignment_candidate",
            "paragraphs": [index + 1 for index in nearby],
            "line_range": [paragraph_lines[nearby[0]][0], paragraph_lines[nearby[-1]][1]],
            "aligned_beats": len(nearby),
            "action": "review_flag",
            "note": "Check whether background life repeatedly arrives exactly at foreground pauses without interaction or aftereffect.",
        })
        break
    return findings


def voice_signature_convergence_findings(
    paragraphs: list[str], paragraph_lines: list[tuple[int, int]]
) -> list[dict]:
    dialogue_hits: dict[str, list[int]] = {name: [] for name in VOICE_SIGNATURE_PATTERNS}
    narration_hits: dict[str, list[int]] = {name: [] for name in VOICE_SIGNATURE_PATTERNS}
    for index, paragraph in enumerate(paragraphs):
        quotes = "\n".join(QUOTE_SPAN_PATTERN.findall(paragraph))
        narration = QUOTE_SPAN_PATTERN.sub("", paragraph)
        for name, pattern in VOICE_SIGNATURE_PATTERNS.items():
            if pattern.search(quotes):
                dialogue_hits[name].append(index)
            if pattern.search(narration):
                narration_hits[name].append(index)
    findings: list[dict] = []
    for name in VOICE_SIGNATURE_PATTERNS:
        if not dialogue_hits[name] or not narration_hits[name]:
            continue
        indexes = sorted(set(dialogue_hits[name] + narration_hits[name]))
        findings.append({
            "type": "dialogue_narration_syntax_convergence_candidate",
            "signature_family": name,
            "dialogue_paragraphs": [x + 1 for x in dialogue_hits[name][:8]],
            "narration_paragraphs": [x + 1 for x in narration_hits[name][:8]],
            "line_range": [paragraph_lines[indexes[0]][0], paragraph_lines[indexes[-1]][1]],
            "action": "review_flag",
            "note": (
                "Shared syntax across dialogue and narration can be character-consistent or object-layer language. "
                "If distributed across three or more sites, mark NEXT_AUTHOR_HANDOFF rather than locally washing voice."
            ),
        })
    return findings


def structure_findings(
    text: str,
    sentences: list[str],
    paragraphs: list[str],
    paragraph_lines: list[tuple[int, int]],
) -> list[dict]:
    """Return coarse review flags for narrative-closure regularity.

    These proxies cannot establish authorship or a defect. They intentionally
    emit no score and never recommend automatic edits.
    """
    findings: list[dict] = []
    findings += functional_micro_loop_findings(paragraphs)
    findings += adjacent_paragraph_overlap_findings(paragraphs, paragraph_lines)
    findings += assembly_blank_gap_findings(text)
    findings += late_unestablished_quote_findings(text)
    findings += narrative_negation_cluster_findings(paragraphs, paragraph_lines)
    findings += background_pause_alignment_findings(paragraphs, paragraph_lines)
    findings += voice_signature_convergence_findings(paragraphs, paragraph_lines)

    last_end = -1
    for i in range(max(0, len(sentences) - 5)):
        window = sentences[i:i + 6]
        joined = "".join(window)
        hits = [term for term in EPISTEMIC_LIMITERS if term in joined]
        total = sum(joined.count(term) for term in EPISTEMIC_LIMITERS)
        if total >= 3 and len(hits) >= 2 and i > last_end:
            findings.append({
                "type": "epistemic_limiter_cluster",
                "sentence_range": [i + 1, i + 6],
                "terms": hits[:8],
                "action": "review_flag",
                "note": "Keep any limiter required for evidence strength or technical accuracy.",
            })
            last_end = i + 5

    enum_pattern = "|".join(re.escape(x) for x in ENUMERATION_MARKERS)
    return_pattern = "|".join(re.escape(x) for x in EPISTEMIC_LIMITERS + RETURN_TO_EVIDENCE)
    cycle_pattern = re.compile(
        rf"(?:{enum_pattern})[^\n]{{0,260}}?(?:{return_pattern})"
    )
    for match in list(cycle_pattern.finditer(text))[:12]:
        findings.append({
            "type": "cognitive_audit_cycle_candidate",
            "line": line_for_offset(text, match.start()),
            "excerpt": match.group(0)[:120],
            "action": "review_flag",
            "note": "Keep full reasoning when it changes risk, relationship, resources, or action.",
        })

    closure_pairs: list[int] = []
    for i, sentence in enumerate(sentences):
        if "？" not in sentence and "?" not in sentence:
            continue
        answer = "".join(sentences[i + 1:i + 3])
        if any(marker in answer for marker in ANSWER_CLOSURE_MARKERS):
            closure_pairs.append(i)
    for start in range(len(closure_pairs)):
        run = [x for x in closure_pairs[start:] if x - closure_pairs[start] <= 12]
        if len(run) >= 3:
            findings.append({
                "type": "dialogue_unit_test_run",
                "sentence_range": [run[0] + 1, run[2] + 3],
                "closure_pairs": len(run),
                "action": "review_flag",
                "note": "Check social purpose, delayed answers, and interruptions without weakening accuracy.",
            })
            break

    paired: list[int] = []
    for i, sentence in enumerate(sentences):
        nearby = "".join(sentences[i:i + 2])
        if any(action in sentence for action in ACTION_MARKERS) and any(marker in nearby for marker in ARGUMENT_MARKERS):
            paired.append(i)
    for start in range(len(paired)):
        run = [x for x in paired[start:] if x - paired[start] <= 10]
        if len(run) >= 3:
            findings.append({
                "type": "action_argument_pair_run",
                "sentence_range": [run[0] + 1, run[2] + 2],
                "pair_count": len(run),
                "action": "review_flag",
                "note": "Do not delete valid spatial or relational actions; inspect one-to-one accompaniment.",
            })
            break

    interpreted_actions: list[int] = []
    for i, sentence in enumerate(sentences):
        if not any(action in sentence for action in ACTION_MARKERS):
            continue
        follow = "".join(sentences[i + 1:i + 3])
        if any(marker in follow for marker in INTERPRETATION_MARKERS):
            interpreted_actions.append(i)
    for start in range(len(interpreted_actions)):
        run = [x for x in interpreted_actions[start:] if x - interpreted_actions[start] <= 14]
        if len(run) >= 3:
            findings.append({
                "type": "action_immediate_interpretation_run",
                "sentence_range": [run[0] + 1, run[2] + 3],
                "pair_count": len(run),
                "action": "review_flag",
                "note": "Check whether each action needs an immediate unique meaning or can remain observable first.",
            })
            break

    for index, paragraph in enumerate(paragraphs):
        pattern_hits = sum(len(pattern.findall(paragraph)) for pattern in EXCLUSION_PATTERNS)
        limiter_hits = sum(paragraph.count(term) for term in EPISTEMIC_LIMITERS)
        if pattern_hits >= 2 or (pattern_hits >= 1 and limiter_hits >= 2):
            findings.append({
                "type": "exclusion_space_closure_candidate",
                "paragraph": index + 1,
                "pattern_hits": pattern_hits,
                "limiter_hits": limiter_hits,
                "action": "review_flag",
                "note": "Keep exclusions motivated by evidence, science, or safety; review only clustered closure of interpretation space.",
            })

    paragraph_tail_flags: list[bool] = []
    for paragraph in paragraphs:
        tail_sentences = split_sentences(paragraph)
        tail = tail_sentences[-1] if tail_sentences else paragraph[-80:]
        paragraph_tail_flags.append(any(marker in tail for marker in ENDING_CLOSURE_MARKERS + INTERPRETATION_MARKERS))
    for i in range(max(0, len(paragraph_tail_flags) - 2)):
        if all(paragraph_tail_flags[i:i + 3]):
            findings.append({
                "type": "paragraph_tail_closure_run",
                "paragraph_range": [i + 1, i + 3],
                "action": "review_flag",
                "note": "Read the three paragraph endings together; do not trim a necessary conclusion or chapter interface mechanically.",
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
                "note": "Compare against the mandatory chapter-exit interface before trimming any return.",
            })

    return findings


def analyze(
    path: Path,
    mode: str,
    structure: bool = False,
    exemptions: list[dict] | None = None,
) -> dict:
    text = path.read_text(encoding="utf-8")
    sentences = split_sentences(text)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    sentence_lines = locate_units(text, sentences)
    paragraph_lines = locate_units(text, paragraphs)
    findings = lexical_findings(text, mode)
    findings += rhythm_findings(sentences)
    findings += pattern_findings(text)
    if structure and mode == "fiction":
        findings += structure_findings(text, sentences, paragraphs, paragraph_lines)
    findings = annotate_line_ranges(findings, sentence_lines, paragraph_lines)
    findings, suppressed = apply_exemptions(findings, exemptions or [])
    return {
        "schema": "natural_prose_audit_v3",
        "source": str(path.resolve()),
        "mode": mode,
        "statistics": {
            "characters": len(text),
            "sentences": len(sentences),
            "paragraphs": len(paragraphs),
            "structure_enabled": structure and mode == "fiction",
        },
        "finding_count": len(findings),
        "findings": findings,
        "applied_exemption_count": len(exemptions or []),
        "suppressed_finding_count": len(suppressed),
        "suppressed_findings": suppressed,
        "manual_scene_review_dimensions": [
            "cognitive_cycle_periodicity",
            "narrative_function_micro_loop",
            "action_to_immediate_interpretation",
            "exclusion_space_closure",
            "dialogue_unit_test_closure_and_world_pause",
            "salient_object_function_overload",
            "paragraph_scene_chapter_overclosure",
            "life_event_follow_through",
            "within_chapter_contrast",
            "adjacent_paragraph_overlap_and_assembly_gap",
            "quote_referent_continuity",
            "narrative_negation_bearing",
            "background_foreground_beat_alignment",
            "dialogue_narration_voice_signature_convergence",
        ] if structure and mode == "fiction" else [],
        "verdict": "warnings_only_no_detector_claim",
    }


def compare_audits(baseline: dict, candidate: dict, target_finding_type: str | None) -> dict:
    baseline_counts = Counter(item["type"] for item in baseline["findings"])
    candidate_counts = Counter(item["type"] for item in candidate["findings"])
    finding_types = sorted(set(baseline_counts) | set(candidate_counts))
    delta_by_type = {
        finding_type: candidate_counts[finding_type] - baseline_counts[finding_type]
        for finding_type in finding_types
    }
    character_delta = candidate["statistics"]["characters"] - baseline["statistics"]["characters"]
    paragraph_delta = candidate["statistics"]["paragraphs"] - baseline["statistics"]["paragraphs"]

    resolution = "NOT_REQUESTED"
    warnings: list[str] = []
    if target_finding_type:
        before = baseline_counts[target_finding_type]
        after = candidate_counts[target_finding_type]
        if before == 0:
            resolution = "BASELINE_TARGET_NOT_FOUND_REQUIRES_HUMAN_REVIEW"
        elif after >= before:
            resolution = "PRIMARY_FINDING_UNRESOLVED"
            warnings.append("target_finding_count_not_reduced")
            if character_delta < 0 or paragraph_delta < 0:
                warnings.append("compression_induced_expositional_monoculture_risk")
        else:
            resolution = "TARGET_PROXY_REDUCED_REQUIRES_HUMAN_REVIEW"

    return {
        "baseline_source": baseline["source"],
        "candidate_source": candidate["source"],
        "character_delta": character_delta,
        "paragraph_delta": paragraph_delta,
        "finding_count_delta_by_type": delta_by_type,
        "target_finding_type": target_finding_type,
        "target_finding_count_before": baseline_counts[target_finding_type] if target_finding_type else None,
        "target_finding_count_after": candidate_counts[target_finding_type] if target_finding_type else None,
        "primary_finding_resolution": resolution,
        "warnings": warnings,
        "note": (
            "Proxy reduction never proves literary improvement. Unchanged target shape after compression "
            "requires a fresh full-scene cold read before any review package or improvement claim."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Non-blocking naturalness audit for Chinese prose")
    parser.add_argument("text_path", type=Path)
    parser.add_argument("--mode", choices=("fiction", "general"), default="fiction")
    parser.add_argument("--structure", action="store_true", help="add non-blocking cognitive-structure proxies for fiction")
    parser.add_argument("--baseline", type=Path, help="compare candidate against a frozen baseline without editing either file")
    parser.add_argument("--target-finding-type", help="finding type the authorized revision was meant to reduce")
    parser.add_argument(
        "--exemptions",
        type=Path,
        help=(
            "optional natural_prose_audit_exemptions_v1 JSON with source-bound line ranges; "
            "the manifest must be separately hash-bound by the project evidence tool"
        ),
    )
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()

    if not args.text_path.is_file():
        parser.error(f"file not found: {args.text_path}")
    if args.target_finding_type and not args.baseline:
        parser.error("--target-finding-type requires --baseline")
    if args.baseline and not args.baseline.is_file():
        parser.error(f"baseline file not found: {args.baseline}")
    if args.exemptions and not args.exemptions.is_file():
        parser.error(f"exemptions file not found: {args.exemptions}")
    if args.exemptions and args.baseline:
        parser.error("--exemptions cannot be combined with --baseline; audit each source with its own binding")
    try:
        exemptions = load_exemptions(args.exemptions, args.text_path)
    except (ValueError, json.JSONDecodeError, OSError) as exc:
        parser.error(f"invalid exemptions manifest: {exc}")
    result = analyze(args.text_path, args.mode, args.structure, exemptions)
    if args.baseline:
        baseline = analyze(args.baseline, args.mode, args.structure)
        result["comparison"] = compare_audits(baseline, result, args.target_finding_type)
    print(json.dumps(result, ensure_ascii=False, indent=None if args.compact else 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
