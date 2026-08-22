import os
import json
import time
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

SYSTEM_PROMPT = (
    "You are a finance reconciliation assistant. You are given ONE ambiguous "
    "order/settlement pair a deterministic matcher could not resolve. "
    "Decide MATCH (explainable discrepancy, e.g. partial refund, rounding) or "
    "EXCEPTION (needs human review). If uncertain, return EXCEPTION. "
    'Respond with ONLY strict JSON: {"decision": "MATCH or EXCEPTION", "reason": "...", "confidence": 0.0-1.0}'
)


def resolve_ambiguous(row, ledger_row, settlement_rows):
    user_prompt = (
        f"Order: {row['order_id']}\n"
        f"Ledger amount: {ledger_row['amount']}, refund: {ledger_row.get('refund_amount', 0)}\n"
        f"Settlement rows: {settlement_rows.to_dict('records')}\n"
        f"Flagged reason: {row['reason']}"
    )
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=SYSTEM_PROMPT + "\n\n" + user_prompt,
    )
    text = response.text.strip().strip("```json").strip("```").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"decision": "EXCEPTION", "reason": "model returned non-JSON response", "confidence": 0}


def resolve_with_retry(row, ledger_row, settlement_rows, max_retries=1):
    """
    Wraps resolve_ambiguous with rate-limit-safe delay, retry, and
    graceful degradation. If Gemini fails even after one retry, the
    row is marked as a clean, readable exception instead of crashing
    the whole batch or dumping raw error JSON into the report.
    """
    for attempt in range(max_retries + 1):
        try:
            result = resolve_ambiguous(row, ledger_row, settlement_rows)
            time.sleep(13)  # stay under free-tier ~5 requests/minute
            return result
        except Exception as e:
            if attempt == max_retries:
                error_str = str(e)
                if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
                    reason = "Agent temporarily unavailable (API rate limit reached) — flagged for manual review"
                elif "timeout" in error_str.lower():
                    reason = "Agent call timed out — flagged for manual review"
                else:
                    reason = f"Agent call failed unexpectedly — flagged for manual review ({error_str[:100]})"

                return {
                    "decision": "EXCEPTION",
                    "reason": reason,
                    "confidence": 0,
                }
            time.sleep(20)  # longer backoff before retrying