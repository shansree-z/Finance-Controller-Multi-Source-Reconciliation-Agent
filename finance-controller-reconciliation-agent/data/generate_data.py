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
        pass  # settlement exists, bank never confirmed it — real-world red flag
    elif outcome == "delayed_credit":
        bank_rows.append({
            "utr": s["utr"], "amount": s["amount"],
            "credited_on": s["settled_on"], "bank_ref": f"BANKREF{s['utr']}"
        })  # note: you can add a date offset here to simulate delay

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


print(f"Generated {len(ledger_rows)} ledger rows, {len(settlement_rows)} settlement rows")
