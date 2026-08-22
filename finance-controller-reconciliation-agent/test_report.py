import pandas as pd
from src.report import generate_report

fake_matched_df = pd.DataFrame([
    {"order_id": "ORD1", "status": "MATCHED", "reason": "exact match within tolerance"},
    {"order_id": "ORD2", "status": "MATCHED", "reason": "exact match within tolerance"},
    {"order_id": "ORD3", "status": "AMBIGUOUS", "reason": "amount diff of 5.00"},
    {"order_id": "ORD4", "status": "UNMATCHED", "reason": "no settlement record found"},
])

fake_resolved = [
    {"order_id": "ORD3", "reason": "partial refund explains the gap", "final_status": "RESOLVED"},
    {"order_id": "ORD4", "reason": "no counterpart found even after review", "final_status": "EXCEPTION"},
]

generate_report(fake_matched_df, fake_resolved)