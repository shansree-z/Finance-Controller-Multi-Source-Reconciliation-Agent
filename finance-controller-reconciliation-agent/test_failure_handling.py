import pandas as pd
from unittest.mock import patch
from src.fuzzy_resolver import resolve_with_retry

fake_row = {"order_id": "ORD9999", "reason": "amount diff of 8.00 — needs review"}
fake_ledger_row = {"amount": 900.00, "refund_amount": 0}
fake_settlement_rows = pd.DataFrame([{"amount": 892.00}])

# Simulate Gemini being completely unavailable
with patch("src.fuzzy_resolver.resolve_ambiguous", side_effect=Exception("simulated API outage")):
    result = resolve_with_retry(fake_row, fake_ledger_row, fake_settlement_rows)
    print(result)