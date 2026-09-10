# Scenario design notes

These are the rules I held myself to while building each scenario, mostly learned by getting them wrong first.

## The evidence has to let the agent find the problem, not be told about it

Nothing in `environment/evidence/` states a conclusion. Policy documents state facts, a fee tier that changed on a certain date, a hardware generation that isn't approved for production, a support queue with no outage reports, and the agent has to connect those facts to the raw data itself. If a fixture ever reads like "the ledger is wrong because of a duplicate transaction," that's the puzzle already solved for the agent, and it gets deleted.

## More than one thing has to be wrong, for genuinely different reasons

A scenario with a single discrepancy rewards finding it, not reasoning about it. Every scenario here has three or four independent issues, and they fail differently on purpose: a duplicate record, an unrelated stray record, a boundary condition, and a rule that changed and only got half-applied are four different kinds of mistake, not four instances of the same one. An agent that pattern-matches "find the anomaly" and stops after the first hit will only get partial credit.

## Every claim has to be independently checkable

`evaluation/claims.yaml` doesn't ask a judge to re-derive the right answer, it states it, with a tolerance where a number is involved. That's deliberate: a claim like "correctly explains the discrepancy" is unfalsifiable busywork for a judge model, while "states the net total as $24,460.80 within $1" is something a judge can check by reading, not calculating. It also means claims can be graded independently, so an answer that gets three of seven things right earns three-sevenths of the credit, not zero.

## A red herring only counts if the evidence can actually rule it out

Every scenario includes at least one plausible-sounding wrong explanation: a deploy that happens to land minutes before an incident, a memo that cites a run that looks comparable at a glance, a class of errors that could plausibly mean the other side is down. None of them are unresolvable ambiguity. Each one is ruled out by something concrete in the evidence, a diff that shows the deploy touched nothing relevant, a metadata table that shows two runs used different hardware, a support queue with zero matching complaints. If I couldn't point to the specific fact that rules out the wrong theory, I changed the scenario until I could.

## Authority has to be assignable, not asserted

Two disagreeing data sources are not interesting on their own; an agent still needs a principled way to decide which one to trust, and for what. In each scenario, authority is split by field, not by system: one source owns whether a record exists, another owns how it should be categorized or priced, and the evidence states those rules directly rather than declaring "system A is always right."
