---
name: scene-event-weaver
description: Build a task-local, scene-specific event library from the actual article, chapter, outline, characters, setting, and constraints, then select bounded life events or causal event chains that improve naturalness, pacing, humor, emotion, or theme without inventing unauthorized facts. Use for fiction, narrative scenes, scripts, chapter planning, and narrative nonfiction when users ask for event cards,生活化事件、突发事件链、日常节奏、场景事件库、情绪显影事件、情节自然化, or want an agent to adapt a generic event library to a specific text. Never use the bundled seed library as direct prose input.
---

# Scene Event Weaver

Create a new event library for the current text. Treat bundled seeds as mechanism examples, never as a ready-made selection pool or fact source.

## Core contract

1. Read the actual text or approved outline before proposing events.
2. Freeze facts, character knowledge, relationships, chronology, setting rules, point of view, and ending interface.
3. Build a task-local `scene-profile.json` from the current work.
4. Create a new `scene-event-library.jsonl` whose entries cite scene-specific anchors.
5. Validate the library before selecting events.
6. Select zero to five events by default. Zero is valid; five is a ceiling, not a target.
7. Let events alter attention, action, timing, object state, social pressure, or later behavior. Do not insert decorative incidents that reset in the next paragraph.
8. Stop and request outline-level authorization if an event changes a major choice, causal outcome, relationship stage, knowledge boundary, research claim, timeline anchor, legal or institutional state, or ending interface.

For narrative nonfiction, create events only from user-provided or verified facts. Never invent a real incident to make the writing feel human.

## Required workflow

### 1. Build the scene profile

Copy `assets/scene-profile-template.json`. Fill every field from the current text and its constraints. Include scene IDs, source locations, participant goals and limits, available objects and spaces, time windows, pacing needs, immutable facts, forbidden outcomes, and recent mechanisms.

Read `references/workflow.md` for the evidence and nonfiction rules.

### 2. Generate a dedicated candidate library

Read `assets/generic-event-archetype-seeds.jsonl` only after the scene profile exists. Use it to vary mechanisms, not to choose finished events.

Create 6–12 candidates for one short scene and 12–30 candidates for a chapter or multi-scene article. Create fewer only when the user asks for one narrowly constrained event.

Every candidate must contain at least two anchors unique to the current text and vary at least two axes from any seed. Set `fact_status=PROPOSAL_NOT_FACT` and `status=CANDIDATE`.

Do not send the seed library or the entire candidate library to a prose model. Only send selected, scene-specific event cards.

### 3. Validate before selection

Run:

```text
python scripts/validate_scene_event_library.py scene-event-library.jsonl --scene-profile scene-profile.json
```

Fix schema, duplicate, anchor, cap, residue, and chain errors before literary selection. Mechanical validation does not prove that an event is good.

### 4. Select by function, not quota

Judge direct scene fit, character fit, causal compatibility, tonal value, visible cost, downstream residue, point-of-view observability, repetition, and plot-shortcut risk.

Reject candidates that need a coincidence only to connect, make a competent character suddenly foolish, cause serious harm for humor, resolve the main conflict by accident, or upgrade ordinary care into therapy or romance.

Mark selected entries `SELECTED`; mark the rest `REJECTED` with a short reason. Use `assets/event-call-card-template.json` for the final call card.

### 5. Compose an event chain only when one event is insufficient

Read `references/chain-composition.md`. A chain must have one root event, two to six visible steps, real state handshakes, at least one unused abort option, one settlement point, and residue that changes a downstream action.

The writer may elaborate direct consequences of the selected root within the frozen boundaries. The writer may not consult the full library, add a second independent event, or create a new plot result.

### 6. Postcheck the written scene

After prose exists, extract actual event steps and compare them to the frozen call card. Check causality, aftereffects, resets, fact expansion, relationship upgrades, research claims, and background details that become metronomes at every pause.

If the answer reveals scope expansion, revert the event or return to outline review. Do not rationalize the prose after the fact.

## Resource map

- `references/workflow.md`: profiling, candidate generation, selection, and nonfiction constraints.
- `references/schema.md`: exact JSON fields and validation rules.
- `references/chain-composition.md`: causal-chain rules and failure modes.
- `assets/generic-event-archetype-seeds.jsonl`: generic mechanism seeds; direct use is forbidden.
- `assets/scene-profile-template.json`: task-local scene profile.
- `assets/event-call-card-template.json`: selected event package.
- `scripts/validate_scene_event_library.py`: deterministic schema and boundary checks.
- `scripts/self_test.py`: validator regression test.

## Non-negotiable boundaries

- Do not claim a seed is a story fact.
- Do not reuse project names, proprietary world rules, or prior-story outcomes in an unrelated work.
- Do not force an event into every scene.
- Do not use random accidents to imitate human writing or evade an AI detector.
- Do not prescribe fixed sensory, joke, interruption, or sentence quotas.
- Do not turn ordinary care into diagnosis, therapy, romance, or moral proof.
- Do not create medical, legal, scientific, financial, or safety consequences without the appropriate factual gate.
- Do not keep a task-local library as a permanent author profile unless the user explicitly requests it.
