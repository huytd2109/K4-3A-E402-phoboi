# Official source policy

## Environment matrix

| `APP_ENV` | Allowed source mode | Model |
|---|---|---|
| `test` | `dataset` or `synthetic_demo` | Offline fake/rules allowed |
| `demo` | `synthetic_demo` only | Live required |
| `production` | `dataset` only | Live required |

`official_discord` is reserved for a future whitelist-backed store and intentionally raises today.

## Provenance contract

An answer is verified only when an active source has either:

- a direct resolvable `source_url`; or
- `guild_id`, `channel_id`, and `message_id`, from which code builds the Discord permalink.

The source also declares role, publish/effective times, task/aliases, cohort/class scope, logistics type, timezone-aware deadline, optional submission URL, supersession, status and fixture flag. Pydantic rejects a synthetic fixture without the required labels/provenance.

## Deterministic conflict rules

1. Discard `revoked` and `superseded` records.
2. Apply an active record's explicit `supersedes` relation.
3. If cohort/class differs and the query lacks that field, ask one clarification question.
4. Different active deadlines/URLs at the same scope without supersession produce `HANDOFF_CONFLICT`.
5. Never choose a source because it merely has a later timestamp.
6. Render all deadlines as date, time, and `UTC+7`.

## Store behavior

`RealDatasetSourceStore` is candidate-only and its official `search()` always returns an empty list. The pack cannot yield `ANSWER_VERIFIED`.

`SyntheticDemoSourceStore` loads only `source_type=synthetic_demo`, `is_fixture=true` records. Every verified response carries `DỮ LIỆU DEMO`; UI uses a permanent synthetic banner.

