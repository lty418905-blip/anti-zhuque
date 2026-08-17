# Structured writing input

Use this workflow before generating new prose. Its purpose is to separate task compilation from drafting while keeping both steps available to the same agent.

## Compile

1. Read the user's current natural-language request and any materials the user supplied or authorized.
2. Copy `assets/structured-writing-input-template.json` to a task-local JSON file.
   The untouched template is intentionally invalid; replace every `REPLACE_*` placeholder before validation.
3. Preserve the user's operative request verbatim in `user_request.original_instruction`.
4. List every source under `source_contract.materials`. State its authority and permitted use. Use an empty array when no source exists; do not invent a source.
5. Fill `fact_contract.immutable_facts` and `fact_contract.prohibited_inferences`. If no external facts were supplied, explicitly record that the work must not claim externally verified facts.
6. Freeze point of view, participants, knowledge boundaries, scenes, output format, title policy, and completion conditions.
7. Put only positive writing directions in `positive_style_requirements`. Do not copy detector scores, high-risk spans, word blacklists, thresholds, audit findings, or detailed review checklists.

## Length

Length has no default.

- If the user explicitly states a length, set `length_contract.source` to `USER_NATURAL_LANGUAGE` and preserve that exact sentence or phrase in `instruction`.
- Parsed `min`, `max`, and `unit` are optional. Fill numeric values only when the same Arabic numerals occur in the preserved instruction.
- If the user gives no length, set `source` and `instruction` to `UNSPECIFIED`, and set `min`, `max`, and `unit` to `null`.
- Never infer a minimum from genre, examples, a template, a model context window, or an internal quality gate.

## Events

If events are needed, use `scene-event-weaver` first. Set `event_contract.source` to `SCENE_EVENT_WEAVER_SELECTED_ONLY` and copy only final event-card objects whose status is `SELECTED`. Keep all library inclusion flags false.

If no event card is used, set `source` to `NONE` and leave `selected_event_cards` empty.

## Validate and freeze

Run:

```text
python scripts/validate_structured_writing_input.py writing-input.json
```

Fix every error. A PASS proves only that required boundaries are present and obvious leakage is absent; it does not prove literary quality or factual truth.

After validation, treat the JSON as frozen. If the user's request or source set changes, create a new JSON version and validate again.

## Write with the same agent

The compiling agent may write the prose itself after validation. During drafting it should load only:

- the frozen structured JSON;
- source materials explicitly listed in `source_contract.materials`;
- any selected event cards already embedded in the JSON.

Do not simultaneously load detailed audit references, detector evidence, score reports, word lists, or revision findings. Draft from positive requirements and frozen boundaries. Run the audit workflow only after the prose exists.
