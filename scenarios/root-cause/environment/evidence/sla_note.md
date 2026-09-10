# Customer delivery SLA note

Per the customer delivery SLA, notify-relay's circuit breaker must remain scoped per destination endpoint. Grouping the breaker above per-endpoint scope, for example by customer or by region, is an emergency change and requires five business days of advance customer notification; it is not permitted as a same-day change.

Lowering the breaker's failure threshold below 30% also requires a documented incident justification before it can be applied, since it makes the breaker trip on a smaller number of slow requests.
