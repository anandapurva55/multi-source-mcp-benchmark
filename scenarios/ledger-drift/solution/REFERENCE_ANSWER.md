Batch BATCH-2027W07 (2027-02-08 through 2027-02-14), Anchorstone Marketplace

Verified net payout total: $24,460.80 across 22 in-window payouts.

Corrections needed before releasing the report:

1. Duplicate disbursement. PAY-8801 (Brightwell Goods, $1,128.40) appears twice in the settlement export, a webhook retry recorded the same transfer as two rows (see PAY-INC-552). Only one disbursement actually happened. Remove the duplicate row; it inflates the raw settlement total by $1,128.40.

2. Unmatched settlement row. PAY-9999 (seller SLR-999, $275.00) appears in the settlement export with no corresponding entry in the payout ledger at all. This is not a real seller payout and should be investigated and excluded from the batch total.

3. Late settlement. PAY-8841 (Copperline Trading) is dated 2027-02-14 but did not actually disburse until 2027-02-15, which is outside this batch's window. Per settlement terms, a payout belongs to the batch in which it is disbursed, not the batch in which the order was placed, so it should move to next week's batch. Its ledger estimate was $2,366.00; the actual settled amount is $2,354.58, a small, expected difference from settling a day later, not an error.

4. Fee tier underpayment. PAY-8811 (Thistle Provisions, ordered 2027-02-10, $640.00 gross) was paid out using the old 12% fee tier ($563.20 net), but Thistle Provisions moved to the 9% tier effective that same date per the fee schedule. The correct net payout is $582.40, a $19.20 underpayment. This is not visible by comparing the ledger to the settlement export, since Payloop disbursed exactly what the ledger instructed; it only surfaces by checking the ledger's fee calculation against the fee tier schedule directly.

All other payouts in the window match between the ledger and the settlement export and use the correct fee tier; no correction is needed for them.

Action items:
1. Reverse the duplicate PAY-8801 disbursement in the settlement system.
2. Investigate PAY-9999 / SLR-999 with the Payloop integration team; it does not correspond to any onboarded seller in our ledger.
3. Move PAY-8841 into BATCH-2027W08 and reconcile it against the actual $2,354.58 settled amount.
4. Issue a correcting payout of $19.20 to Thistle Provisions for PAY-8811, and check whether any other Thistle Provisions payouts on or after 2027-02-10 also used the stale fee tier.
