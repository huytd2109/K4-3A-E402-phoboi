# Blockers

## Live AI evidence

No `GEMINI_API_KEY` (or alternative provider key) is configured in the current environment. Therefore live preflight, full live batch, live golden eval and three-run stability evidence cannot be produced safely. The system cannot infer or manufacture a key, provider response, request ID or token usage; doing so would violate fail-closed and no-silent-mock requirements.

Required input: configure one real provider key locally (recommended: `GEMINI_API_KEY`) and keep the selected `LLM_MODEL` available to that account. Then run the live commands in `README.md`. No real deadline/channel/role/source data is requested.

