# ADR 002 — Runtime compatibility and imported UI

Status: accepted · 2026-09-17

The preferred runtime remains Python 3.12+, but package metadata permits 3.10 because the available hackathon machine is 3.10. No 3.12-only syntax is used.

The React/Vite UI from `phoboi-cp2.zip` is retained as the clickable demo instead of rebuilding it. It is explicitly synthetic: realistic names were replaced by demo personas, official-looking badges were relabeled and a permanent warning banner was added. The operational truth remains the Python CLI/pipeline.

