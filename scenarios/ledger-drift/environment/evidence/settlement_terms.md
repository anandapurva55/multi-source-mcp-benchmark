# Settlement terms

Payout window: 2027-02-08T00:00:00Z through 2027-02-14T23:59:59Z (weekly batch BATCH-2027W07). A payout belongs to the batch in which it is actually disbursed, not the batch in which the underlying order was placed. All figures are in USD.

Source of record: `settlement_export.sqlite` (the Payloop processor's disbursement export) is the record of whether money actually moved and how much. `payout_ledger.csv` is the marketplace's own record of which seller and order each payout maps to; it is not itself a guarantee that Payloop disbursed the amount it lists.

`fee_tier_schedule.md` is the current, authoritative seller fee schedule. `processor_incident_note.md` documents one known integration issue during this window.
