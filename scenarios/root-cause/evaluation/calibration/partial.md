The root cause was the 13:05 UTC config change CB-771. It lowered the circuit breaker's failure threshold from 50% to 15% and widened its grouping from per-endpoint to per-region. A handful of slow endpoints in ap-south then tripped the breaker for the whole region.

Two other theories do not hold. The 12:45 UTC v3.9.0 deploy changed the log format and added a metric, nothing in breaker or connection handling, and it rolled out healthy. The customers' endpoints were not down either: the support queue has no customer-reported outages in the window, and circuit_open errors outnumber customer_timeout errors by about 6 to 1.

I have not yet worked through the mitigation steps or the recommendation.
