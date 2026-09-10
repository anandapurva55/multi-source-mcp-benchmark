# Context

Service: notify-relay (outbound webhook delivery)

Incident window: 2027-04-12, 12:45 UTC through 14:15 UTC

Timezone note: log and git commit timestamps in this evidence set are in UTC unless a file states otherwise. `handover_note.md` uses IST (India Standard Time, UTC+5:30).

Evidence: `app_logs.txt` holds per-minute delivery summaries and individual error samples. `relay-config` is a git repository tracking notify-relay's circuit breaker and worker configuration; look for it alongside the other evidence. `deploy_log.md` records application deploys. `sla_note.md` documents a customer delivery commitment relevant to the circuit breaker configuration. `support_queue_note.md` summarizes customer-reported issues during the window. `handover_note.md` is a shift handover note from earlier that day. `incident_ticket.md` is the on-call engineer's factual record of alert and mitigation timestamps.
