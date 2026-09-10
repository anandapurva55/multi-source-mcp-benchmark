# Payloop integration note, ticket PAY-INC-552

2027-02-08: Payloop's disbursement webhook retried after a timeout on one payout in this week's batch. Engineering confirmed the underlying transfer itself was not duplicated on Payloop's side, but our settlement export ingested both the original and retried webhook events as separate rows.

Any payout showing two disbursement rows with the same payout_id and the same amount in the same batch should be treated as a single disbursement.
