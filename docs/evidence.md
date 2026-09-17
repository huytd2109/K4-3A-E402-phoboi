# Evidence from the anonymized Discord pack

## Reproducible inventory

Counts are from `Import-Csv data/discord-pack/k4_messages.csv`, filtering human rows with `is_bot == False`. Keyword counts are simple case-insensitive regex matches and may overlap; they measure prevalence, not classifier precision.

| Measure | Count |
|---|---:|
| Total rows | 1,092 |
| Human rows | 779 |
| Bot rows | 313 |
| Encoded authors including BOT | 202 |
| Human rows mentioning bot | 307 |
| K4-L2-3 rows | 264 |
| K4-L3-4 rows | 828 |
| Duplicate `msg_id` values | 3 |

## Pain-point keyword scan (human rows)

| Pattern family | Count | Example references |
|---|---:|---|
| deadline / hạn nộp / hạn chót | 10 | `M19124`, `M72484`, `M07416` |
| điểm danh | 37 | `M69081`, `M17046`, `M21623` |
| XP | 32 | `M22827`, `M77476`, `M49945` |
| standup | 57 | `M60122`, `M22827`, `M35505` |
| nộp lab/bài, cách nộp | 17 | `M84993`, `M72484`, `M07416` |
| ticket | 22 | `M49744`, `M78683`, `M08310` |

The references provide more than five auditable examples without copying raw peer messages. No attempt was made to identify authors.

## Product evidence and limits

- Logistics and personal-record themes recur enough to justify separate routing and privacy policy.
- Four existing daily reports in the pack demonstrate truncation, broken insertion text and “not yet confirmed” replies; digest improvement is nevertheless outside this MVP.
- Pack lacks true channel names, staff labels and original announcement URLs. It cannot establish deadline ground truth or official authority.
- Three IDs (`M80709`, `M59723`, `M88243`) occur twice. Batch processing preserves original `msg_id` and adds a unique internal `record_id` suffix for later occurrences.
- Data is tracked in Git despite the pack's publication restrictions. Keep the repository private and follow BTC deletion requests; the implementation does not copy raw rows into committed reports.

