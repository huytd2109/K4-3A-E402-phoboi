# Hard-test stability

- Date: 2026-09-17
- Mode/model: `offline_test` / `deterministic-v1`
- Command: `python -m pytest tests/test_hard_safety.py tests/test_demo_dod.py -q`
- Run 1: 12/12
- Run 2: 12/12
- Run 3: 12/12
- Variance: 0

Conflict, personal-data, injection and mixed-intent policy outcomes were stable 3/3. This is deterministic backstop/policy evidence, not Gemini stability evidence. Live three-run stability remains blocked by the missing provider key.

