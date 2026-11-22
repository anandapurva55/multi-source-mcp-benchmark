# Payloop integration note, ticket PAY-INC-552

2027-02-08: Payloop's disbursement webhook timed out and was retried for one payout in this week's batch. Our settlement export ingests each webhook event as its own row. Payloop's engineering team confirmed that a single transfer was issued for that payout on their side.
