#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Inspect and remove high-confidence invisible Unicode controls from UTF-8 text.

This is a conservative text-only hygiene utility. It never rewrites visible
language, never edits the source in place, and never claims to remove sampling
watermarks or prove human authorship.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import unicodedata
from collections import Counter
from pathlib import Path


HIGH_CONFIDENCE = {
    0x00AD: "SOFT HYPHEN",
    0x061C: "ARABIC LETTER MARK",
    0x200B: "ZERO WIDTH SPACE",
    0x200E: "LEFT-TO-RIGHT MARK",
    0x200F: "RIGHT-TO-LEFT MARK",
    0x202A: "LEFT-TO-RIGHT EMBEDDING",
    0x202B: "RIGHT-TO-LEFT EMBEDDING",
    0x202C: "POP DIRECTIONAL FORMATTING",
    0x202D: "LEFT-TO-RIGHT OVERRIDE",
    0x202E: "RIGHT-TO-LEFT OVERRIDE",
    0x2060: "WORD JOINER",
    0x2066: "LEFT-TO-RIGHT ISOLATE",
    0x2067: "RIGHT-TO-LEFT ISOLATE",
    0x2068: "FIRST STRONG ISOLATE",
    0x2069: "POP DIRECTIONAL ISOLATE",
    0x206A: "INHIBIT SYMMETRIC SWAPPING",
    0x206B: "ACTIVATE SYMMETRIC SWAPPING",
    0x206C: "INHIBIT ARABIC FORM SHAPING",
    0x206D: "ACTIVATE ARABIC FORM SHAPING",
    0x206E: "NATIONAL DIGIT SHAPES",
    0x206F: "NOMINAL DIGIT SHAPES",
    0xFEFF: "ZERO WIDTH NO-BREAK SPACE OR BOM",
}

REPORT_ONLY = {
    0x034F: "COMBINING GRAPHEME JOINER",
    0x180E: "MONGOLIAN VOWEL SEPARATOR",
    0x200C: "ZERO WIDTH NON-JOINER",
    0x200D: "ZERO WIDTH JOINER",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def label(codepoint: int, fallback: str | None = None) -> str:
    char = chr(codepoint)
    name = fallback or unicodedata.name(char, "UNNAMED")
    return f"U+{codepoint:04X} {name}"


def report_only_name(codepoint: int) -> str | None:
    if codepoint in REPORT_ONLY:
        return REPORT_ONLY[codepoint]
    if 0xFE00 <= codepoint <= 0xFE0F or 0xE0100 <= codepoint <= 0xE01EF:
        return "VARIATION SELECTOR"
    if 0xE0020 <= codepoint <= 0xE007F:
        return "EMOJI TAG CHARACTER"
    return None


def scan(text: str) -> dict:
    removable: Counter[str] = Counter()
    preserved: Counter[str] = Counter()
    initial_bom_count = 0

    for index, char in enumerate(text):
        codepoint = ord(char)
        if codepoint == 0xFEFF and index == 0:
            initial_bom_count += 1
            continue
        if codepoint in HIGH_CONFIDENCE:
            removable[label(codepoint, HIGH_CONFIDENCE[codepoint])] += 1
            continue
        semantic_name = report_only_name(codepoint)
        if semantic_name is not None:
            preserved[label(codepoint, semantic_name)] += 1

    return {
        "high_confidence_total": sum(removable.values()),
        "high_confidence_by_codepoint": dict(sorted(removable.items())),
        "preserved_semantic_total": sum(preserved.values()),
        "preserved_semantic_by_codepoint": dict(sorted(preserved.items())),
        "initial_bom_preserved": initial_bom_count,
    }


def read_utf8(path: Path) -> tuple[bytes, str]:
    data = path.read_bytes()
    return data, data.decode("utf-8", errors="strict")


def cleaned_text(text: str) -> str:
    kept: list[str] = []
    for index, char in enumerate(text):
        codepoint = ord(char)
        if codepoint == 0xFEFF and index == 0:
            kept.append(char)
        elif codepoint not in HIGH_CONFIDENCE:
            kept.append(char)
    return "".join(kept)


def default_output_path(source: Path) -> Path:
    if source.suffix:
        return source.with_name(f"{source.stem}.layer-a-clean{source.suffix}")
    return source.with_name(source.name + ".layer-a-clean")


def write_new_file(path: Path, data: bytes, overwrite_output: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite_output:
        raise FileExistsError(f"output already exists: {path}")
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
            temp_name = handle.name
        if path.exists() and not overwrite_output:
            raise FileExistsError(f"output already exists: {path}")
        os.replace(temp_name, path)
        temp_name = None
    finally:
        if temp_name is not None:
            Path(temp_name).unlink(missing_ok=True)


def inspect_result(source: Path) -> dict:
    source_bytes, text = read_utf8(source)
    return {
        "schema": "unicode_layer_a_v1",
        "mode": "inspect",
        "source": str(source.resolve()),
        "source_sha256": sha256_bytes(source_bytes),
        "source_bytes": len(source_bytes),
        "scan": scan(text),
        "boundary": "text_only_no_sampling_watermark_or_authorship_claim",
    }


def clean_result(source: Path, output: Path, overwrite_output: bool) -> dict:
    if source.resolve() == output.resolve():
        raise ValueError("refusing in-place clean; choose a different output path")

    source_bytes, text = read_utf8(source)
    pre_scan = scan(text)
    cleaned = cleaned_text(text)
    output_bytes = cleaned.encode("utf-8")
    write_new_file(output, output_bytes, overwrite_output)
    post_scan = scan(cleaned)
    if post_scan["high_confidence_total"] != 0:
        raise RuntimeError("post-clean verification found high-confidence controls")

    return {
        "schema": "unicode_layer_a_v1",
        "mode": "clean",
        "source": str(source.resolve()),
        "source_sha256": sha256_bytes(source_bytes),
        "source_bytes": len(source_bytes),
        "output": str(output.resolve()),
        "output_sha256": sha256_bytes(output_bytes),
        "output_bytes": len(output_bytes),
        "pre_clean_scan": pre_scan,
        "removed_total": pre_scan["high_confidence_total"],
        "post_clean_scan": post_scan,
        "source_modified": False,
        "boundary": "text_only_no_sampling_watermark_or_authorship_claim",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Conservative UTF-8 text Layer A inspector and cleaner"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("source", type=Path)
    inspect_parser.add_argument("--compact", action="store_true")

    clean_parser = subparsers.add_parser("clean")
    clean_parser.add_argument("source", type=Path)
    clean_parser.add_argument("--output", type=Path)
    clean_parser.add_argument("--overwrite-output", action="store_true")
    clean_parser.add_argument("--compact", action="store_true")

    args = parser.parse_args()
    if not args.source.is_file():
        parser.error(f"source file not found: {args.source}")

    try:
        if args.command == "inspect":
            result = inspect_result(args.source)
        else:
            output = args.output or default_output_path(args.source)
            result = clean_result(args.source, output, args.overwrite_output)
    except (UnicodeDecodeError, FileExistsError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))

    print(json.dumps(result, ensure_ascii=False, indent=None if args.compact else 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
