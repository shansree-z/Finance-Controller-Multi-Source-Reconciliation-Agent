import csv
import random
from datetime import datetime, timedelta

random.seed(42)  # reproducibility — judges can rerun and get the same set

N = 60  # >50 as required by the brief

settlement_rows = []
ledger_rows = []
ground_truth_rows = []

for i in range(N):
    order_id = f"ORD{1000+i}"
    amount = round(random.uniform(200, 5000), 2)
    created_on = datetime(2026, 7, 1) + timedelta(days=random.randint(0, 20))

    outcome = random.choices(
        ["exact", "mismatch", "duplicate", "missing_settlement",
         "missing_ledger", "partial_refund"],
        weights=[55, 10, 8, 10, 8, 9]
    )[0]

    ground_truth_rows.append({"order_id": order_id, "true_outcome": outcome})

    ledger_rows.append({
        "order_id": order_id, "customer": f"cust_{i}",
        "amount": amount, "status": "paid",
        "created_on": created_on.date().isoformat(),
        "refund_amount": 0
    })

    settled_on = created_on + timedelta(days=random.randint(1, 3))

    if outcome == "exact":
        settlement_rows.append({
            "settlement_id": f"STL{2000+i}", "payment_id": f"pay_{i}",
            "order_id": order_id, "amount": amount,
            "utr": f"UTR{i}", "settled_on": settled_on.date().isoformat(),
            "fee": round(amount * 0.02, 2), "tax": round(amount * 0.0036, 2)
        })
    elif outcome == "mismatch":
        settlement_rows.append({
            "settlement_id": f"STL{2000+i}", "payment_id": f"pay_{i}",
            "order_id": order_id, "amount": round(amount - random.uniform(1, 15), 2),
            "utr": f"UTR{i}", "settled_on": settled_on.date().isoformat(),
            "fee": round(amount * 0.02, 2), "tax": round(amount * 0.0036, 2)
        })
    elif outcome == "duplicate":
        for dup in range(2):
            settlement_rows.append({
                "settlement_id": f"STL{2000+i}{dup}", "payment_id": f"pay_{i}",
                "order_id": order_id, "amount": amount,
                "utr": f"UTR{i}{dup}", "settled_on": settled_on.date().isoformat(),
                "fee": round(amount * 0.02, 2), "tax": round(amount * 0.0036, 2)
            })
    elif outcome == "missing_settlement":
        pass  # exists in ledger, no settlement row at all
    elif outcome == "missing_ledger":
        ledger_rows.pop()  # remove the ledger row we just added
        settlement_rows.append({
            "settlement_id": f"STL{2000+i}", "payment_id": f"pay_{i}",
            "order_id": order_id, "amount": amount,
            "utr": f"UTR{i}", "settled_on": settled_on.date().isoformat(),
            "fee": round(amount * 0.02, 2), "tax": round(amount * 0.0036, 2)
        })
    elif outcome == "partial_refund":
        refund = round(amount * random.uniform(0.2, 0.6), 2)
        ledger_rows[-1]["refund_amount"] = refund
        settlement_rows.append({
            "settlement_id": f"STL{2000+i}", "payment_id": f"pay_{i}",
            "order_id": order_id, "amount": round(amount - refund, 2),
            "utr": f"UTR{i}", "settled_on": settled_on.date().isoformat(),
            "fee": round(amount * 0.02, 2), "tax": round(amount * 0.0036, 2)
        })

# ============================================================
# HAND-CRAFTED EDGE CASES (Day 3) — deliberate, not randomized
# Placed BEFORE the bank_rows loop so these also get bank entries
# ============================================================

# --- Case 1: Currency/timezone drift ---
# Looks like a 1-day mismatch but isn't a real error — settled_on crosses
# midnight UTC vs IST
ledger_rows.append({
    "order_id": "ORD9001", "customer": "cust_tz1", "amount": 1200.00,
    "status": "paid", "created_on": "2026-07-10", "refund_amount": 0
})
settlement_rows.append({
    "settlement_id": "STL9001", "payment_id": "pay_tz1", "order_id": "ORD9001",
    "amount": 1200.00, "utr": "UTRTZ1", "settled_on": "2026-07-09",
    "fee": round(1200.00 * 0.02, 2), "tax": round(1200.00 * 0.0036, 2)
})
ground_truth_rows.append({"order_id": "ORD9001", "true_outcome": "tz_drift_not_an_error"})

# --- Case 2: Split settlement (partial payouts across two rows) ---
split_total = 3000.00
ledger_rows.append({
    "order_id": "ORD9002", "customer": "cust_split1", "amount": split_total,
    "status": "paid", "created_on": "2026-07-11", "refund_amount": 0
})
settlement_rows.append({
    "settlement_id": "STL9002A", "payment_id": "pay_split1", "order_id": "ORD9002",
    "amount": 1800.00, "utr": "UTRSPLIT1A", "settled_on": "2026-07-12",
    "fee": round(1800.00 * 0.02, 2), "tax": round(1800.00 * 0.0036, 2)
})
settlement_rows.append({
    "settlement_id": "STL9002B", "payment_id": "pay_split1", "order_id": "ORD9002",
    "amount": 1200.00, "utr": "UTRSPLIT1B", "settled_on": "2026-07-13",
    "fee": round(1200.00 * 0.02, 2), "tax": round(1200.00 * 0.0036, 2)
})
ground_truth_rows.append({"order_id": "ORD9002", "true_outcome": "legitimate_split_settlement"})

# --- Case 3: Fee-only discrepancy (should be confidently auto-explained) ---
fee_case_amount = 2500.00
fee_case_fee = round(fee_case_amount * 0.02, 2)
fee_case_tax = round(fee_case_amount * 0.0036, 2)
ledger_rows.append({
    "order_id": "ORD9003", "customer": "cust_fee1", "amount": fee_case_amount,
    "status": "paid", "created_on": "2026-07-14", "refund_amount": 0
})
settlement_rows.append({
    "settlement_id": "STL9003", "payment_id": "pay_fee1", "order_id": "ORD9003",
    "amount": round(fee_case_amount - fee_case_fee - fee_case_tax, 2),
    "utr": "UTRFEE1", "settled_on": "2026-07-15",
    "fee": fee_case_fee, "tax": fee_case_tax
})
ground_truth_rows.append({"order_id": "ORD9003", "true_outcome": "fee_only_explainable"})

# --- Case 4: Reversed/negative settlement (chargeback) ---
ledger_rows.append({
    "order_id": "ORD9004", "customer": "cust_chargeback1", "amount": 1500.00,
    "status": "paid", "created_on": "2026-07-16", "refund_amount": 0
})
settlement_rows.append({
    "settlement_id": "STL9004", "payment_id": "pay_cb1", "order_id": "ORD9004",
    "amount": 1500.00, "utr": "UTRCB1", "settled_on": "2026-07-17",
    "fee": round(1500.00 * 0.02, 2), "tax": round(1500.00 * 0.0036, 2)
})
settlement_rows.append({
    "settlement_id": "STL9004R", "payment_id": "pay_cb1_reversal", "order_id": "ORD9004",
    "amount": -1500.00, "utr": "UTRCB1REV", "settled_on": "2026-07-20",
    "fee": 0, "tax": 0
})
ground_truth_rows.append({"order_id": "ORD9004", "true_outcome": "chargeback_reversal"})

print("Added 4 hand-crafted edge cases: TZ drift, split settlement, fee-only gap, chargeback reversal")

# ============================================================
# Bank statement generation — now runs AFTER edge cases are added,
# so ORD9001-9004's settlement rows also get bank confirmation rows
# ============================================================
bank_rows = []
for s in settlement_rows:
    outcome = random.choices(
        ["confirmed", "amount_drift", "missing_bank_entry", "delayed_credit"],
        weights=[80, 6, 8, 6]
    )[0]

    if outcome == "confirmed":
        bank_rows.append({
            "utr": s["utr"], "amount": s["amount"],
            "credited_on": s["settled_on"], "bank_ref": f"BANKREF{s['utr']}"
        })
    elif outcome == "amount_drift":
        bank_rows.append({
            "utr": s["utr"], "amount": round(s["amount"] - random.uniform(0.5, 3.0), 2),
            "credited_on": s["settled_on"], "bank_ref": f"BANKREF{s['utr']}"
        })
    elif outcome == "missing_bank_entry":
        pass
    elif outcome == "delayed_credit":
        bank_rows.append({
            "utr": s["utr"], "amount": s["amount"],
            "credited_on": s["settled_on"], "bank_ref": f"BANKREF{s['utr']}"
        })

with open("data/internal_ledger.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=ledger_rows[0].keys())
    writer.writeheader()
    writer.writerows(ledger_rows)

with open("data/settlement_report.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=settlement_rows[0].keys())
    writer.writeheader()
    writer.writerows(settlement_rows)

with open("data/ground_truth.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["order_id", "true_outcome"])
    writer.writeheader()
    writer.writerows(ground_truth_rows)

with open("data/bank_statement.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["utr", "amount", "credited_on", "bank_ref"])
    writer.writeheader()
    writer.writerows(bank_rows)

print(f"Generated {len(ledger_rows)} ledger rows, {len(settlement_rows)} settlement rows, and {len(bank_rows)} bank statement rows")