Batch BATCH-2027W07 (2027-02-08 through 2027-02-14), Anchorstone Marketplace

Verified net payout total: $24,460.80 across 22 in-window payouts.

Corrections needed before releasing the report:

1. Duplicate disbursement. PAY-8801 (Brightwell Goods, $1,128.40) appears twice in the settlement export, a webhook retry recorded the same transfer as two rows (see PAY-INC-552). Only one disbursement actually happened. Remove the duplicate row; it inflates the raw settlement total by $1,128.40.

2. Unattributed settlement row. PAY-9999 (seller SLR-999, $275.00) appears in the settlement export with no corresponding entry in the payout ledger. Per the settlement terms the export is the record of money moved, so $275.00 did leave the account, but nothing ties it to a ledger payout. Exclude it from the seller net payout total, and treat it as an unexplained outflow to investigate with Payloop (confirm who SLR-999 is, and recover the funds if it is not a legitimate payee).

3. Late settlement. PAY-8841 (Copperline Trading) is dated 2027-02-14 but did not actually disburse until 2027-02-15, which is outside this batch's window. Per settlement terms, a payout belongs to the batch in which it is disbursed, not the batch in which the order was placed, so it should move to next week's batch. The settled amount ($2,366.00) matches the ledger exactly, so only the batch assignment changes.

4. Fee tier underpayment. PAY-8811 (Thistle Provisions, ordered 2027-02-10, $640.00 gross) was paid out using the old 12% fee tier ($563.20 net), but Thistle Provisions moved to the 9% tier effective that same date per the fee schedule. The correct net payout is $582.40, a $19.20 underpayment. This is not visible by comparing the ledger to the settlement export, since Payloop disbursed exactly what the ledger instructed; it only surfaces by checking the ledger's fee calculation against the fee tier schedule directly.

All other payouts in the window match between the ledger and the settlement export and use the correct fee tier; no correction is needed for them.

Action items:
1. Reverse the duplicate PAY-8801 disbursement in the settlement system.
2. Investigate the $275.00 outflow on PAY-9999 / SLR-999 with the Payloop integration team; it has no ledger entry. Keep it out of seller net payouts until it is explained, and recover it if it was sent in error.
3. Move PAY-8841 into BATCH-2027W08; its $2,366.00 settlement already matches the ledger, so no amount adjustment is needed.
4. Issue a correcting payout of $19.20 to Thistle Provisions for PAY-8811, and check whether any other Thistle Provisions payouts on or after 2027-02-10 also used the stale fee tier.
