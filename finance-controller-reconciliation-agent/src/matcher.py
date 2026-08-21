import pandas as pd

def load_data(ledger_path, settlement_path):
    ledger = pd.read_csv(ledger_path)
    settlement = pd.read_csv(settlement_path)
    return ledger, settlement

def exact_match(ledger, settlement, tolerance=0.01):
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