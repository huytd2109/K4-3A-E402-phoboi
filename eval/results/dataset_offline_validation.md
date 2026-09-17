# Dataset pipeline validation

- Run date: 2026-09-17
- Mode: **offline_test — not live AI evidence**
- Provider/model: `offline-test-rules` / `deterministic-v1`
- Rows: 1,092 total · 779 human · 313 bot
- Coverage: 779/779 human (100%)
- Valid classifications: 779 · errors: 0
- Verified answers from real pack: **0**
- Groundedness/deadline correctness: **unverifiable**

Outcome counts: 1 greeting, 71 clarify, 17 no-source handoff, 599 out-of-scope, 21 personal restriction, 70 learning route. These are rule-baseline outputs, not reported as live-model accuracy.

| Intent | N | Verified | Clarify | Handoff |
|---|---:|---:|---:|---:|
| `GREETING` | 6 | 0.0% | 50.0% | 0.0% |
| `LEARNING` | 82 | 0.0% | 11.0% | 0.0% |
| `LOGISTICS_DEADLINE` | 20 | 0.0% | 75.0% | 25.0% |
| `LOGISTICS_LINK` | 62 | 0.0% | 80.6% | 8.1% |
| `LOGISTICS_SUBMISSION` | 17 | 0.0% | 47.1% | 52.9% |
| `PERSONAL_RESTRICTED` | 21 | 0.0% | 0.0% | 0.0% |
| `UNKNOWN` | 599 | 0.0% | 0.0% | 0.0% |

The final cache-validation rerun reused 779/779 classifications (`cache_hits=779`) while still regenerating every deterministic policy decision and report.
