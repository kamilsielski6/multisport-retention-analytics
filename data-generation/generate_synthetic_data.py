"""Generate deterministic synthetic retention analytics data.

The output is intentionally CSV so it can be uploaded to a Fabric Lakehouse
and converted to Delta/Parquet in a subsequent notebook.
"""

from __future__ import annotations

import argparse
import csv
import random
from calendar import monthrange
from datetime import date, datetime, timedelta
from pathlib import Path


DATE_FORMAT = "%Y-%m-%d"
DEFAULT_START_DATE = date(2025, 1, 1)


def parse_date(value: str) -> date:
    return datetime.strptime(value, DATE_FORMAT).date()


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def add_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 + months
    year, month = divmod(month_index, 12)
    month += 1
    return date(year, month, min(value.day, monthrange(year, month)[1]))


def random_date(rng: random.Random, start: date, end: date) -> date:
    return start + timedelta(days=rng.randint(0, (end - start).days))


def generate_customers(
    rng: random.Random, count: int, start_date: date, end_date: date
) -> list[dict]:
    cities = ["Warsaw", "Krakow", "Wroclaw", "Gdansk", "Poznan", "Lodz"]
    plans = ["standard", "premium", "family"]
    rows = []
    for customer_number in range(1, count + 1):
        customer_id = f"C{customer_number:06d}"
        signup_date = random_date(rng, start_date, end_date - timedelta(days=30))
        rows.append(
            {
                "customer_id": customer_id,
                "signup_date": signup_date.strftime(DATE_FORMAT),
                "city": rng.choice(cities),
                "plan_type": rng.choice(plans),
                "age_band": rng.choice(["18-24", "25-34", "35-44", "45-54", "55+"]),
                "acquisition_channel": rng.choice(
                    ["employer", "referral", "online", "partner"]
                ),
            }
        )
    return rows


def generate_memberships(
    rng: random.Random, customers: list[dict], end_date: date
) -> list[dict]:
    rows = []
    for customer in customers:
        signup_date = parse_date(customer["signup_date"])
        can_cancel = signup_date + timedelta(days=60) <= end_date
        status = "active" if not can_cancel or rng.random() >= 0.18 else "cancelled"
        cancellation_date = ""
        if status == "cancelled":
            cancellation_date = random_date(
                rng, signup_date + timedelta(days=60), end_date
            ).strftime(DATE_FORMAT)
        rows.append(
            {
                "membership_id": f"M{customer['customer_id'][1:]}",
                "customer_id": customer["customer_id"],
                "start_date": signup_date.strftime(DATE_FORMAT),
                "end_date": cancellation_date,
                "status": status,
                "monthly_fee": f"{rng.choice([59.0, 79.0, 99.0]):.2f}",
            }
        )
    return rows


def generate_visits(
    rng: random.Random,
    customers: list[dict],
    memberships: list[dict],
    start_date: date,
    end_date: date,
) -> list[dict]:
    membership_by_customer = {row["customer_id"]: row for row in memberships}
    activities = ["gym", "swimming", "yoga", "climbing", "fitness_class"]
    rows = []
    visit_number = 1
    for customer in customers:
        membership = membership_by_customer[customer["customer_id"]]
        active_until = parse_date(membership["end_date"]) if membership["end_date"] else end_date
        visit_start = max(start_date, parse_date(customer["signup_date"]))
        visit_end = min(end_date, active_until)
        if visit_start > visit_end:
            continue
        current = visit_start
        while current <= visit_end:
            monthly_visits = max(0, int(rng.gauss(7, 3)))
            for _ in range(monthly_visits):
                visit_date = random_date(
                    rng,
                    current,
                    min(add_months(current, 1) - timedelta(days=1), visit_end),
                )
                rows.append(
                    {
                        "visit_id": f"V{visit_number:08d}",
                        "customer_id": customer["customer_id"],
                        "visit_date": visit_date.strftime(DATE_FORMAT),
                        "activity_type": rng.choice(activities),
                        "duration_minutes": rng.choice([30, 45, 60, 75, 90]),
                    }
                )
                visit_number += 1
            current = add_months(current, 1)
    return rows


def generate_payments(
    rng: random.Random, memberships: list[dict], end_date: date
) -> list[dict]:
    rows = []
    payment_number = 1
    for membership in memberships:
        current = parse_date(membership["start_date"]).replace(day=1)
        membership_end = (
            parse_date(membership["end_date"])
            if membership["end_date"]
            else end_date
        )
        while current <= membership_end:
            payment_date = min(
                current + timedelta(days=rng.randint(0, 4)), membership_end
            )
            rows.append(
                {
                    "payment_id": f"P{payment_number:08d}",
                    "membership_id": membership["membership_id"],
                    "payment_date": payment_date.strftime(DATE_FORMAT),
                    "amount": membership["monthly_fee"],
                    "payment_status": "paid"
                    if rng.random() >= 0.05
                    else "failed",
                }
            )
            payment_number += 1
            current = add_months(current, 1)
    return rows


def generate_churn_labels(
    customers: list[dict], memberships: list[dict], visits: list[dict], end_date: date
) -> list[dict]:
    membership_by_customer = {row["customer_id"]: row for row in memberships}
    last_visit_by_customer: dict[str, date] = {}
    for visit in visits:
        visit_date = parse_date(visit["visit_date"])
        customer_id = visit["customer_id"]
        if visit_date > last_visit_by_customer.get(customer_id, date.min):
            last_visit_by_customer[customer_id] = visit_date

    rows = []
    for customer in customers:
        customer_id = customer["customer_id"]
        membership = membership_by_customer[customer_id]
        last_visit = last_visit_by_customer.get(customer_id)
        inactivity_days = (end_date - last_visit).days if last_visit else None
        cancelled = membership["status"] == "cancelled"
        churned = cancelled or (inactivity_days is not None and inactivity_days >= 60)
        rows.append(
            {
                "customer_id": customer_id,
                "snapshot_date": end_date.strftime(DATE_FORMAT),
                "last_visit_date": last_visit.strftime(DATE_FORMAT) if last_visit else "",
                "inactivity_days": inactivity_days if inactivity_days is not None else "",
                "churned": int(churned),
                "churn_reason": (
                    "membership_cancelled"
                    if cancelled
                    else "inactive_60_days"
                    if churned
                    else "active"
                ),
            }
        )
    return rows


def generate_dataset(output_dir: Path, customer_count: int, start_date: date, end_date: date, seed: int) -> None:
    if end_date <= start_date:
        raise ValueError("end_date must be later than start_date")

    rng = random.Random(seed)
    customers = generate_customers(rng, customer_count, start_date, end_date)
    memberships = generate_memberships(rng, customers, end_date)
    visits = generate_visits(rng, customers, memberships, start_date, end_date)
    payments = generate_payments(rng, memberships, end_date)
    churn_labels = generate_churn_labels(customers, memberships, visits, end_date)

    write_csv(
        output_dir / "customers.csv",
        ["customer_id", "signup_date", "city", "plan_type", "age_band", "acquisition_channel"],
        customers,
    )
    write_csv(
        output_dir / "memberships.csv",
        ["membership_id", "customer_id", "start_date", "end_date", "status", "monthly_fee"],
        memberships,
    )
    write_csv(
        output_dir / "visits.csv",
        ["visit_id", "customer_id", "visit_date", "activity_type", "duration_minutes"],
        visits,
    )
    write_csv(
        output_dir / "payments.csv",
        ["payment_id", "membership_id", "payment_date", "amount", "payment_status"],
        payments,
    )
    write_csv(
        output_dir / "churn_labels.csv",
        ["customer_id", "snapshot_date", "last_visit_date", "inactivity_days", "churned", "churn_reason"],
        churn_labels,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("data-generation/output"))
    parser.add_argument("--customers", type=int, default=1000)
    parser.add_argument("--start-date", type=parse_date, default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", type=parse_date, default=date(2026, 12, 31))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.customers < 1:
        parser.error("--customers must be at least 1")
    generate_dataset(args.output_dir, args.customers, args.start_date, args.end_date, args.seed)
    print(f"Generated synthetic data in {args.output_dir}")


if __name__ == "__main__":
    main()
