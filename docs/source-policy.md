# Source Policy

## Whitelist
- Sources must be configured via environment variables. Only whitelisted channels and roles can act as official sources.

## Precedence Rules
- Official announcements supersede regular TA messages.
- Specific updates supersede general guidelines.

## Conflict Resolution
- Must be deterministic.
- Never pick a newer source by timestamp alone. Require explicit linkage (e.g. "update to X").
- Unresolvable conflicts result in a human handoff.

## Revoke/Supersede Mechanism
- A source can explicitly revoke or supersede an older source using specific structured metadata.

## Fixture Policy
- Test or demo fixtures must contain `is_fixture: true`.
- Fake deadlines that look real are strictly prohibited in production.
