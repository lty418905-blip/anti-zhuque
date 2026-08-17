# Event-library schemas

## Scene profile

Required fields:

- `schema`: `SCENE_EVENT_PROFILE_V1`
- `work_id`, `scene_ids`, `source_paths`
- `genre`, `fiction_status`
- `scene_anchors`: at least four concrete values from the current work
- `participants`: each with `id`, `immediate_goal`, `pressure`, `knowledge_limit`, `visible_behavior_range`
- `available_objects`, `available_spaces`, `time_window`
- `missing_functions`
- `immutable_facts`, `forbidden_outcomes`, `recent_mechanisms`
- `max_selected_events`: integer, normally 5

## Candidate event

Every JSONL object requires:

- `schema`: `SCENE_EVENT_CANDIDATE_V1`
- `event_id`, `scene_id`, `title`
- `source_mode`: `SCENE_DERIVED`, `SEED_ADAPTED`, or `USER_PROVIDED`
- `origin_seed_id`: seed ID or `NONE`
- `domain`, `scale`
- `scene_anchors`: at least two values that exist in the scene profile
- `trigger`, `immediate_need`, `visible_behavior`
- `reaction_branches`: at least two
- `immediate_cost`, `residue`, `aftereffect_window`
- `pov_gate`, `function_tags`
- `variation_axes`: at least two
- `forbidden_results`: at least one
- `dedupe_signature`
- `fact_status`: `PROPOSAL_NOT_FACT`
- `status`: `CANDIDATE`, `SELECTED`, or `REJECTED`
- `selection_reason`, `rejection_reason`
- `chain`: either `NONE` or a chain object

## Chain object

Required fields:

- `mode`: `ROOT_SEEDED_CHAIN`
- `goal`
- `steps`: two to six objects with `step_id`, `visible_action`, `state_in`, `state_out`
- `state_handshakes`: one fewer than step count
- `abort_options`: at least one unused plausible exit
- `settlement_point`
- `carrying_residue`
- `independent_coincidences`: 0 or 1
- `forbidden_results`

## Call card

The call card lists selected IDs, the exact scene profile, event cards, total load, postcheck questions, and any outline escalation. It must not contain rejected candidates or the full seed library.
