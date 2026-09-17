# ADR 001 — Deterministic safety boundary

Status: accepted · 2026-09-17

## Decision

Use the LLM only for structured classification/extraction. Keep authorization, source trust, provenance, conflict resolution, final outcomes and response rendering in deterministic code.

## Why

A plausible but wrong deadline has direct cost. Schema validation alone cannot prove authority. This split makes `unverified_deadline_released=0` testable and prevents model prompt injection from granting itself source authority.

## Consequences

The bot abstains when official provenance is unavailable. Utility is protected separately with controlled synthetic coverage ≥95%.

