import argparse
import csv
import sqlite3
from pathlib import Path

_parser = argparse.ArgumentParser(description="Regenerate this scenario's evidence deterministically.")
_parser.add_argument(
    "--out",
    type=Path,
    default=Path(__file__).resolve().parent.parent / "environment" / "evidence",
    help="directory to write evidence into (default: the scenario's environment/evidence)",
)
out = _parser.parse_args().out
out.mkdir(parents=True, exist_ok=True)

# seller_id, seller_name, fee_tier_rate (as of order date, per fee_tier_schedule.md)
# Thistle Provisions crosses from tier 1 (12%) to tier 2 (9%) on 2027-02-10
sellers = {
    "SLR-201": "Brightwell Goods",
    "SLR-207": "Marrow & Finch",
    "SLR-214": "Oakhollow Supply",
    "SLR-219": "Thistle Provisions",
    "SLR-226": "Copperline Trading",
    "SLR-233": "Fenwick & Vale",
    "SLR-241": "Harrow Lane Co",
}

fee_rate = {
    "SLR-201": 0.09,
    "SLR-207": 0.12,
    "SLR-214": 0.07,
    "SLR-219": None,  # depends on order date, handled specially
    "SLR-226": 0.09,
    "SLR-233": 0.07,
    "SLR-241": 0.12,
}

def thistle_rate(order_date: str) -> float:
    return 0.09 if order_date >= "2027-02-10" else 0.12

# payout_id, seller_id, order_date_utc, gross_order_amount_usd, ledger_fee_rate_used
rows = [
    ("PAY-8801", "SLR-201", "2027-02-08", 1240.00, 0.09),
    ("PAY-8802", "SLR-207", "2027-02-08", 620.00, 0.12),
    ("PAY-8803", "SLR-214", "2027-02-08", 3100.00, 0.07),
    ("PAY-8804", "SLR-219", "2027-02-08", 480.00, 0.12),   # before tier change: 12% correct
    ("PAY-8805", "SLR-226", "2027-02-09", 990.00, 0.09),
    ("PAY-8806", "SLR-233", "2027-02-09", 2250.00, 0.07),
    ("PAY-8807", "SLR-241", "2027-02-09", 340.00, 0.12),
    ("PAY-8808", "SLR-201", "2027-02-09", 875.00, 0.09),
    ("PAY-8809", "SLR-219", "2027-02-09", 560.00, 0.12),   # before tier change: 12% correct
    ("PAY-8810", "SLR-207", "2027-02-10", 715.00, 0.12),
    ("PAY-8811", "SLR-219", "2027-02-10", 640.00, 0.12),   # ON/AFTER 2027-02-10: LEDGER BUG, should be 0.09
    ("PAY-8812", "SLR-226", "2027-02-10", 1180.00, 0.09),
    ("PAY-8813", "SLR-214", "2027-02-11", 2400.00, 0.07),
    ("PAY-8814", "SLR-233", "2027-02-11", 1750.00, 0.07),
    ("PAY-8815", "SLR-201", "2027-02-11", 990.00, 0.09),
    ("PAY-8816", "SLR-219", "2027-02-11", 410.00, 0.09),   # after tier change: correctly 0.09 this time
    ("PAY-8817", "SLR-241", "2027-02-12", 505.00, 0.12),
    ("PAY-8818", "SLR-207", "2027-02-12", 830.00, 0.12),
    ("PAY-8819", "SLR-226", "2027-02-12", 1420.00, 0.09),
    ("PAY-8820", "SLR-214", "2027-02-13", 3350.00, 0.07),
    ("PAY-8821", "SLR-233", "2027-02-13", 960.00, 0.07),
    ("PAY-8822", "SLR-201", "2027-02-13", 1105.00, 0.09),
    ("PAY-8841", "SLR-226", "2027-02-14", 2600.00, 0.09),  # settles late (next window), see below
]

# --- write payout_ledger.csv (the ledger's own numbers, bug included as-is) ---
ledger_path = out / "payout_ledger.csv"
with ledger_path.open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["payout_id", "seller_id", "seller_name", "order_date_utc",
                "gross_order_amount_usd", "fee_rate_applied", "fee_amount_usd", "net_payout_usd"])
    for payout_id, seller_id, order_date, gross, fee_rate_applied in rows:
        fee_amount = round(gross * fee_rate_applied, 2)
        net = round(gross - fee_amount, 2)
        w.writerow([payout_id, seller_id, sellers[seller_id], order_date,
                    f"{gross:.2f}", fee_rate_applied, f"{fee_amount:.2f}", f"{net:.2f}"])

# --- compute TRUE correct net payout per fee_tier_schedule.md (fixing the ledger's own bug) ---
def correct_rate(seller_id, order_date):
    if seller_id == "SLR-219":
        return thistle_rate(order_date)
    return fee_rate[seller_id]

true_rows = []
for payout_id, seller_id, order_date, gross, fee_rate_applied in rows:
    correct = correct_rate(seller_id, order_date)
    fee_amount = round(gross * correct, 2)
    net = round(gross - fee_amount, 2)
    true_rows.append((payout_id, seller_id, order_date, gross, correct, fee_amount, net))

print("=== Rows where ledger's applied rate differs from the correct rate (fee-tier bug) ===")
for payout_id, seller_id, order_date, gross, correct, fee_amount, net in true_rows:
    applied = next(r[4] for r in rows if r[0] == payout_id)
    if applied != correct:
        print(payout_id, seller_id, order_date, "ledger used", applied, "correct is", correct,
              "-> correct net", net, "vs ledger net", next(r for r in true_rows if r[0] == payout_id))

# --- settlement window: 2027-02-08T00:00:00Z through 2027-02-15T00:00:00Z ---
# PAY-8841 disburses 2027-02-15 (late, next window) for exactly the amount the ledger instructed
disbursements = []
batch_main = "BATCH-2027W07"
batch_next = "BATCH-2027W08"

for payout_id, seller_id, order_date, gross, correct, fee_amount, net in true_rows:
    if payout_id == "PAY-8841":
        continue  # handled specially below
    disbursed_at = f"{order_date}T18:00:00Z"
    # settlement pays out whatever the LEDGER told it to (ledger's own net_payout_usd, bug and all)
    ledger_net = next(r for r in rows if r[0] == payout_id)
    ledger_gross, ledger_rate = ledger_net[3], ledger_net[4]
    ledger_fee = round(ledger_gross * ledger_rate, 2)
    ledger_net_amount = round(ledger_gross - ledger_fee, 2)
    disbursements.append((payout_id, seller_id, ledger_net_amount, disbursed_at, batch_main))

# PAY-8841: settles one day late, same amount as the ledger instructed
pay_8841_net = next(round(r[3] - round(r[3] * r[4], 2), 2) for r in rows if r[0] == "PAY-8841")
disbursements.append(("PAY-8841", "SLR-226", pay_8841_net, "2027-02-15T09:20:00Z", batch_next))

# Duplicate: PAY-8801 (Brightwell) double-disbursed due to a webhook retry
dup = next(d for d in disbursements if d[0] == "PAY-8801")
disbursements.append((dup[0], dup[1], dup[2], "2027-02-08T18:04:00Z", batch_main))

# Settlement row with no corresponding payout_id in the ledger at all
disbursements.append(("PAY-9999", "SLR-999", 275.00, "2027-02-11T12:00:00Z", batch_main))

db_path = out / "settlement_export.sqlite"
if db_path.exists():
    db_path.unlink()
conn = sqlite3.connect(db_path)
conn.execute("""
CREATE TABLE disbursements (
    disbursement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    payout_id TEXT NOT NULL,
    seller_id TEXT NOT NULL,
    amount_usd REAL NOT NULL,
    disbursed_at_utc TEXT NOT NULL,
    batch_id TEXT NOT NULL
)
""")
conn.executemany(
    "INSERT INTO disbursements (payout_id, seller_id, amount_usd, disbursed_at_utc, batch_id) VALUES (?,?,?,?,?)",
    disbursements,
)
conn.commit()

# --- TRUE verified totals for the 2027-02-08 through 2027-02-14 (inclusive) window ---
in_window_true = [r for r in true_rows if r[0] != "PAY-8841"]
true_total = round(sum(r[6] for r in in_window_true), 2)
print(f"\nTrue in-window net payout total (excludes PAY-8841, correct fee tiers applied): {true_total:.2f}")
print(f"In-window payout count: {len(in_window_true)}")

naive_ledger_total = round(sum(round(r[3] - round(r[3] * r[4], 2), 2) for r in rows if r[0] != "PAY-8841"), 2)
print(f"Naive ledger total (bug included, still excluding PAY-8841): {naive_ledger_total:.2f}")

cur = conn.execute("SELECT SUM(amount_usd), COUNT(*) FROM disbursements WHERE batch_id = ?", (batch_main,))
settlement_total, settlement_count = cur.fetchone()
print(f"Raw settlement export total for {batch_main} (includes duplicate + stray row): {settlement_total:.2f} ({settlement_count} rows)")

conn.close()
print("\nWrote:", ledger_path, "and", db_path)
