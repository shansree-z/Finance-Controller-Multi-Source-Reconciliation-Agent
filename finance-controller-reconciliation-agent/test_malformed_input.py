import pandas as pd
from src.matcher import exact_match

print("Testing matcher against malformed input (missing amount)...")
bad_ledger = pd.DataFrame([{"order_id": "ORDX", "amount": None, "refund_amount": 0}])
bad_settlement = pd.DataFrame([{"order_id": "ORDX", "amount": 100.0}])

try:
    result = exact_match(bad_ledger, bad_settlement)
    print("Handled without crashing:")
    print(result)
except Exception as e:
    print(f"Raised an exception instead of silently corrupting output: {e}")