# Access to confirmatory material (G6)

Holdout sessions of baseline-r4 were recorded on 24 Oct 2026 (01:08–06:17 UTC; Goose's repeated after an observer race, D27 point
4). Until the freeze commit is pushed, no holdout session's client logs, audit log or scores were opened or computed: the runner's
own checks (workload, quota, export, secret gate) are the only reads.

Reads of the confirmatory event runs (`events/`) before the freeze, none of them of client logs (adversarial review of the freeze):
- 22 Oct 18:19 and 18:32: command bounds and the quota observer's record of two failed attempts (qwen q5-start, gemini q3-silent),
  to decide whether they were quota stops.
- 23 Oct 07:50: the ground-truth logs of the 30 event runs (canary start log, lab server log), to check that the runs were
  complete; they show whether each event happened.
- 23 Oct 08:36: an assistant session extracted every event run's quota-observer record, which holds client screen captures, to
  check for quota messages.
The author's client-log rules were fixed on 22 Oct 21:09 and did not change afterwards (rounds 3 and 4 changed nothing). The host
rule (D36) and the second author's package came after these reads; neither depends on whether the events happened.

Every opening after the freeze is listed below.

| When | What | Why |
|---|---|---|
