# Golden evaluation — latest

- Tier: **P1_FULL_48**
- Mode: **live**
- Pass: **32/48 (66.7%)**
- Eligible answer coverage: **75.0%**
- Unverified deadline released: **0**
- Verified answer from real pack: **0**

| Category | Passed | Total |
|---|---:|---:|
| clarify | 3 | 6 |
| conflict | 3 | 6 |
| greeting | 1 | 2 |
| injection | 4 | 4 |
| mixed | 3 | 4 |
| no_source | 5 | 7 |
| out_of_scope | 0 | 2 |
| personal | 4 | 4 |
| real_pack_boundary | 1 | 1 |
| verified | 8 | 12 |

## Failures

- `G003`: expected=ANSWER_VERIFIED actual=HANDOFF_NO_SOURCE
- `G004`: expected=ANSWER_VERIFIED actual=HANDOFF_NO_SOURCE
- `G008`: expected=ANSWER_VERIFIED actual=HANDOFF_NO_SOURCE
- `G009`: expected=ANSWER_VERIFIED actual=HANDOFF_NO_SOURCE
- `G016`: expected=CLARIFY actual=HANDOFF_NO_SOURCE
- `G024`: expected=OUT_OF_SCOPE actual=OUT_OF_SCOPE
- `G028`: provider_error:ProviderError
- `G029`: provider_error:ProviderError
- `G030`: provider_error:ProviderError
- `G032`: expected=CLARIFY actual=HANDOFF_NO_SOURCE
- `G035`: expected=HANDOFF_CONFLICT actual=HANDOFF_NO_SOURCE
- `G036`: expected=HANDOFF_CONFLICT actual=HANDOFF_NO_SOURCE
- `G038`: expected=HANDOFF_CONFLICT actual=HANDOFF_NO_SOURCE
- `G045`: expected=ANSWER_VERIFIED actual=HANDOFF_NO_SOURCE
- `G047`: provider_error:ProviderError
- `G048`: provider_error:ProviderError
