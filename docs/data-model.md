# Data model

The project uses a small star-like model for retention analysis. All source
data is synthetic and can be loaded into a Fabric Lakehouse as Delta tables.

## Tables

| Table | Grain | Primary key | Purpose |
|---|---|---|---|
| `customers` | One row per customer | `customer_id` | Customer profile and acquisition attributes |
| `memberships` | One row per membership period | `membership_id` | Plan, fee, start and cancellation dates |
| `visits` | One row per customer visit | `visit_id` | Activity frequency and duration |
| `payments` | One row per membership payment | `payment_id` | Revenue and payment status |
| `churn_labels` | One row per customer snapshot | `customer_id`, `snapshot_date` | Churn target and explanatory label |

## Relationships

```text
customers 1 ─── * memberships
customers 1 ─── * visits
memberships 1 ─── * payments
customers 1 ─── 1 churn_labels (per snapshot date)
```

`churn_labels.churned` is the analytical target. A customer is labelled as
churned when their membership is cancelled or their last visit is at least
60 days before the snapshot date.

## Initial data contract

- Dates use ISO `YYYY-MM-DD` format.
- Monetary values use decimal values with two fractional digits.
- Boolean targets are encoded as `0` or `1` in CSV.
- The generator is deterministic for a fixed `--seed`.
- Generated CSV files are temporary source data; production pipelines should
  validate schema and nullability before writing Delta tables.
