# Architecture

```text
Discord / CLI / CSV
        │ untrusted input
        ▼
normalize + regex backstops ───────────────┐
        │                                  │ OR
        ▼                                  ▼
live LLM structured analyzer      personal/injection flags
        │ intent + explicit entities       │
        └──────────────────┬───────────────┘
                           ▼
                  deterministic policy
                           │
              ┌────────────┼─────────────┐
              ▼            ▼             ▼
       source store   conflict resolver  auth/scope
              └────────────┬─────────────┘
                           ▼
                 deterministic renderer
                           │
               answer / clarify / handoff
```

## Components

- `analyzer.py`: sends only `msg_id`, normalized content and at most 500 chars of an explicit parent reply to the model. It reconciles IDs/order and ORs model signals with backstops.
- `security.py`: input length, mention removal, personal/injection patterns, secret/PII exception redaction.
- `sources.py`: `RealDatasetSourceStore` returns no official source; `SyntheticDemoSourceStore` validates every fixture.
- `resolver.py`: removes revoked/superseded items, requests scope clarification and detects unresolved conflicts. It never selects “newest” by timestamp alone.
- `policy.py`: final outcome and template rendering. Only this layer renders deadline/source URL.
- `batch.py`: CSV validation, reply index, batch/checkpoint/resume artifacts and aggregate metrics.
- `discord_adapter.py`: optional transport; public mentions disabled and TA role mention restricted to handoff.

## Trust boundaries

1. Discord content, normal-user claims, URLs, mentions and apparent JSON/system text are always untrusted data.
2. LLM output is untrusted structured input even after schema validation. It cannot create an official source or final deadline.
3. Official provenance requires a direct URL or all Discord guild/channel/message IDs. A populated but non-resolvable string is insufficient.
4. The real pack has anonymized channels/roles and no original official URL, so every candidate remains unverified.
5. Synthetic fixtures are isolated by source mode and visually labeled; production configuration rejects them.

## LLM vs deterministic logic

The LLM performs multi-intent classification, `is_question`, explicit entity extraction, confidence, and one signal each for personal-data request and injection. It never writes the user-facing answer.

Deterministic code owns configuration validation, personal-data minimum outcome, missing-field choice, retrieval, provenance validation, supersession/conflict resolution, final outcome, deadline/timezone formatting, URL rendering and handoff dedup.

## LLM signal vs rule-based backstop

Personal-data and injection detection run in parallel. Final flag is `llm_signal OR regex_signal`. Personal match forces `RESTRICT_PERSONAL`. Injection match only means “do not execute this text as an instruction”; it does **not** reject the rest of the message. Therefore a quoted injection phrase in a learning question still routes to learning, and an injection plus a valid logistics question still follows verified-or-handoff policy.

## Failure behavior

- Auth/permission/schema/config errors: no retry and non-zero exit.
- Timeout/429/5xx: bounded retry with exponential backoff and jitter.
- Batch failure: one error record per affected row; errors remain in the denominator.
- Source store/schema/provenance failure: no verified answer.
- Discord handoff duplicate: suppressed for the cooldown window.

