import pandas as pd
from src.fuzzy_resolver import resolve_ambiguous

fake_row = {"order_id": "ORD1005", "reason": "amount diff of 12.50 — needs review"}
fake_ledger_row = {"amount": 1500.00, "refund_amount": 0}
fake_settlement_rows = pd.DataFrame([{"amount": 1487.50}])

result = resolve_ambiguous(fake_row, fake_ledger_row, fake_settlement_rows)
print(result)