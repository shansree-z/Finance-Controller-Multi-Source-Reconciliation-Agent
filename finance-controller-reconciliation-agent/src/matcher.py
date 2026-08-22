import pandas as pd

def load_data(ledger_path, settlement_path):
    try:
        ledger = pd.read_csv(ledger_path)
        settlement = pd.read_csv(settlement_path)
    except FileNotFoundError as e:
        raise SystemExit(f"Required data file missing: {e}. Run data/generate_data.py first.")

    required_ledger_cols = {"order_id", "amount"}
    required_settlement_cols = {"order_id", "amount", "utr"}
    if not required_ledger_cols.issubset(ledger.columns):
        raise SystemExit(f"Ledger CSV missing required columns: {required_ledger_cols - set(ledger.columns)}")
    if not required_settlement_cols.issubset(settlement.columns):
        raise SystemExit(f"Settlement CSV missing required columns: {required_settlement_cols - set(settlement.columns)}")

    return ledger, settlement


def exact_match(ledger, settlement, tolerance=0.01):
    ledger = ledger.dropna(subset=["amount"]).copy()
    results = []
    settlement_by_order = settlement.groupby("order_id")

    for _, l_row in ledger.iterrows():
        oid = l_row["order_id"]
        expected_amount = l_row["amount"] - l_row.get("refund_amount", 0)

        if oid not in settlement_by_order.groups:
            results.append({"order_id": oid, "status": "UNMATCHED",
                             "reason": "no settlement record found"})
            continue

        s_rows = settlement_by_order.get_group(oid)

        if len(s_rows) > 1:
            results.append({"order_id": oid, "status": "AMBIGUOUS",
                             "reason": f"{len(s_rows)} settlement rows for one order — needs review"})
            continue

        s_amount = s_rows.iloc[0]["amount"]
        if abs(s_amount - expected_amount) <= tolerance:
            results.append({"order_id": oid, "status": "MATCHED",
                             "reason": "exact match within tolerance"})
        else:
            results.append({"order_id": oid, "status": "AMBIGUOUS",
                             "reason": f"amount diff of {round(s_amount - expected_amount, 2)} — needs review"})

    return pd.DataFrame(results)


def match_bank_confirmation(settlement, bank, tolerance=0.01):
    results = []
    bank_by_utr = bank.set_index("utr")

    for _, s_row in settlement.iterrows():
        utr = s_row["utr"]
        if utr not in bank_by_utr.index:
            results.append({"utr": utr, "order_id": s_row["order_id"],
                             "bank_status": "UNCONFIRMED",
                             "reason": "settlement exists but no bank credit found — possible payout failure"})
            continue

        b_match = bank_by_utr.loc[[utr]]

        if len(b_match) > 1:
            results.append({"utr": utr, "order_id": s_row["order_id"],
                             "bank_status": "DUPLICATE_BANK_ENTRY",
                             "reason": f"{len(b_match)} bank entries found for this UTR — needs review"})
            continue

        b_row = b_match.iloc[0]

        if abs(b_row["amount"] - s_row["amount"]) <= tolerance:
            results.append({"utr": utr, "order_id": s_row["order_id"],
                             "bank_status": "CONFIRMED", "reason": "bank credit matches settlement"})
        else:
            results.append({"utr": utr, "order_id": s_row["order_id"],
                             "bank_status": "AMOUNT_MISMATCH",
                             "reason": f"bank credited {b_row['amount']}, settlement says {s_row['amount']}"})

    return pd.DataFrame(results)