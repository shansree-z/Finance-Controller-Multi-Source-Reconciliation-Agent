from src.matcher import load_data, exact_match, match_bank_confirmation
from src.fuzzy_resolver import resolve_with_retry
from src.report import generate_report, compare_to_ground_truth
import pandas as pd

print("Loading data...")
ledger, settlement = load_data(
    "data/internal_ledger.csv", "data/settlement_report.csv"
)
bank = pd.read_csv("data/bank_report.csv")

print("Running deterministic matcher...")
matched_df = exact_match(ledger, settlement)

# --- Bank confirmation check ---
bank_check = match_bank_confirmation(settlement, bank)
unconfirmed = bank_check[bank_check["bank_status"] != "CONFIRMED"]
print("\n--- BANK CONFIRMATION CHECK ---")
print(f"Total settlement rows: {len(settlement)}")
print(f"Confirmed by bank: {len(bank_check) - len(unconfirmed)}")
print(f"Unconfirmed or mismatched: {len(unconfirmed)}")

# Anything not cleanly MATCHED needs the agent's help
exceptions = matched_df[matched_df["status"] != "MATCHED"]
print(f"\n{len(exceptions)} ambiguous/unmatched rows sent to Gemini for review...")

resolved = []
for _, row in exceptions.iterrows():
    ledger_row = ledger[ledger["order_id"] == row["order_id"]].iloc[0]
    settlement_rows = settlement[settlement["order_id"] == row["order_id"]]

    decision = resolve_with_retry(row, ledger_row, settlement_rows)

    final_status = (
        "RESOLVED"
        if decision["decision"] == "MATCH" and decision["confidence"] >= 0.7
        else "EXCEPTION"
    )
    resolved.append({
        "order_id": row["order_id"],
        "reason": decision["reason"],
        "final_status": final_status,
    })

print("\nGenerating report...\n")
generate_report(matched_df, resolved)

# Optional: only works if you created data/ground_truth.csv in Phase 5
try:
    compare_to_ground_truth(matched_df, resolved)
except FileNotFoundError:
    print("\n(Skipping ground-truth comparison — no ground_truth.csv found)")
