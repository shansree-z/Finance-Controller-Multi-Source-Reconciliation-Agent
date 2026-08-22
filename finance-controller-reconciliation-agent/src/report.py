def generate_report(matched_df, resolved_exceptions, unconfirmed_bank=None):
    """
    matched_df: DataFrame from matcher.py with columns [order_id, status, reason]
    resolved_exceptions: list of dicts from the fuzzy resolver step
    unconfirmed_bank: optional DataFrame of settlement rows with bank_status != CONFIRMED
    """
    total = len(matched_df)
    deterministic_matched = (matched_df["status"] == "MATCHED").sum()

    resolved_by_agent = sum(
        1 for r in resolved_exceptions if r["final_status"] == "RESOLVED"
    )
    true_exceptions = sum(
        1 for r in resolved_exceptions if r["final_status"] == "EXCEPTION"
    )

    print("=" * 50)
    print("RECONCILIATION REPORT")
    print("=" * 50)
    print(f"Total records processed:        {total}")
    print(f"Exact matched (deterministic):  {deterministic_matched} ({deterministic_matched/total:.1%})")
    print(f"Resolved by agent (Gemini):     {resolved_by_agent} ({resolved_by_agent/total:.1%})")
    print(f"Unresolved exceptions:          {true_exceptions} ({true_exceptions/total:.1%})")

    # --- New bank confirmation summary ---
    if unconfirmed_bank is not None:
        print(f"Bank confirmation mismatches:   {len(unconfirmed_bank)}")
        if not unconfirmed_bank.empty:
            print("\n--- BANK ISSUES ---")
            for _, row in unconfirmed_bank.iterrows():
                print(f"- UTR {row['utr']}: {row['bank_status']}")

    print("-" * 50)
    overall_matched = deterministic_matched + resolved_by_agent
    print(f"OVERALL MATCH RATE: {overall_matched}/{total} ({overall_matched/total:.1%})")
    print("=" * 50)

    if true_exceptions > 0:
        print("\n--- EXCEPTION LIST (needs human review) ---")
        for r in resolved_exceptions:
            if r["final_status"] == "EXCEPTION":
                print(f"- Order {r['order_id']}: {r['reason']}")
    else:
        print("\nNo unresolved exceptions.")

    return {
        "total": total,
        "deterministic_matched": deterministic_matched,
        "resolved_by_agent": resolved_by_agent,
        "true_exceptions": true_exceptions,
        "overall_match_rate": overall_matched / total,
        "bank_mismatches": len(unconfirmed_bank) if unconfirmed_bank is not None else 0,
    }

import pandas as pd

def compare_to_ground_truth(matched_df, resolved_exceptions, ground_truth_path="data/ground_truth.csv"):
    truth = pd.read_csv(ground_truth_path).set_index("order_id")["true_outcome"].to_dict()

    final_decisions = {}
    for _, row in matched_df.iterrows():
        if row["status"] == "MATCHED":
            final_decisions[row["order_id"]] = "matched"

    for r in resolved_exceptions:
        final_decisions[r["order_id"]] = (
            "matched" if r["final_status"] == "RESOLVED" else "exception"
        )

    correct = 0
    false_positives = []
    false_negatives = []

    for order_id, true_label in truth.items():
        predicted = final_decisions.get(order_id, "exception")
        true_should_match = (true_label == "exact")
        predicted_matched = (predicted == "matched")

        if true_should_match == predicted_matched:
            correct += 1
        elif predicted_matched and not true_should_match:
            false_positives.append(order_id)
        elif not predicted_matched and true_should_match:
            false_negatives.append(order_id)

    total = len(truth)
    print("\n--- GROUND TRUTH COMPARISON ---")
    print(f"Correct classifications: {correct}/{total} ({correct/total:.1%})")
    print(f"False positives (wrongly matched): {len(false_positives)} -> {false_positives}")
    print(f"False negatives (wrongly flagged):  {len(false_negatives)} -> {false_negatives}")

    return {
        "accuracy": correct / total,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
    }