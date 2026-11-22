Two problems in the batch BATCH-2027W07 reconciliation:

1. PAY-8801 (Brightwell Goods, $1,128.40) is in the settlement export twice. The payment processor's webhook was retried after a timeout (ticket PAY-INC-552) and the export recorded the one transfer as two rows. Only one disbursement happened, so the duplicate row should be removed.

2. PAY-8841 (Copperline Trading, $2,366.00) was disbursed on 2027-02-15, one day after the window ends. A payout belongs to the batch in which it is disbursed, so it moves to next week's batch. The settled amount matches the ledger, so nothing else changes for it.

I did not finish checking the remaining payouts or the fee tiers.
