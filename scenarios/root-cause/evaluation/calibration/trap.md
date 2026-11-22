Root cause: the Meridian Retail customers' own endpoints were down or unhealthy during the onboarding wave, so deliveries to them timed out and our breaker tripped as designed.

The 12:45 UTC v3.9.0 deploy shortly before the incident is the most likely trigger for the extra errors. The 13:20 restart and the 13:32 scale-up from 6 to 10 workers fixed the problem, which is why things settled. The breaker configuration was fine and needs no changes.

Recommendation: ask Meridian Retail to fix their endpoints and roll back deploys during onboarding waves.
