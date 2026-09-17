# ADR 003 — Duplicate message identifiers

Status: accepted · 2026-09-17

The data dictionary describes `msg_id` as the message identifier, but the pack contains three duplicated values. Rejecting the pack or de-duplicating would violate the requirement to account for every human row.

The loader preserves `msg_id` and assigns later occurrences a deterministic internal `record_id` (for example `M12345#2`). Model reconciliation/checkpoint/resume use `record_id`; reports continue to cite the original `msg_id`. Reply lookup uses the first occurrence and does not infer ambiguous conversation links.
