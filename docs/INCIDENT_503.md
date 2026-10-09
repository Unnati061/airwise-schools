# Bounded Investigation: GET /current-plan 503

Investigated October 9, 2026, following commit `25be464`. Read-only historical
CloudWatch queries and a Lambda concurrency read; no new app traffic, load tests,
Bedrock calls, resource changes or deployment. SDK connect timeout 4 seconds,
read timeout 12 seconds, one total attempt per request. No raw log contents,
credentials, account IDs or private notice content exported.

## Observed Facts

- API Gateway logs contained one matching GET /current-plan 503 within
  11:30-13:30 UTC: **2026-10-09 11:42:54.550 UTC / 17:12:54.550 IST**.
- Gateway request ID: `E-Xx2iVcywMEMNg=`; integration latency **11 ms**.
- Targeted Lambda route/status search around the event found **zero** handler
  GET /current-plan 503 entries, with pagination complete for that search.
- A neighboring Lambda-log query showed cold starts around 4.25-4.35s and a
  GET /current-plan **200** with 595ms handler duration. That initial window's
  page was not exhaustive; this successful request is not a proven correlation
  with the failing Gateway request.
- Complete function metric results for the failure minute (17:12 IST):
  **Throttles Sum 1**, **ConcurrentExecutions Max 5**, **Errors Sum 0**,
  **Invocations Sum 10**. Current reserved concurrency read returned **5**.
- The corrected hosted-browser workflow passed. Its harness response-wait fix
  prevents an unattached promise failure; it does not fix or explain the 503.

## Interpretation and Limits

### Read-only Follow-up from d4120e2

Fresh reads used existing Sydney profile/resources, connect4s/read12s, one total
SDK attempt. Four-page bounds sufficed: pagination completed for both groups in
11:42:40-11:43:10 UTC, Gateway26 events and Lambda45 events (10 REPORT lines).
Gateway logged current-plan200 and the same503 request `E-Xx2iVcywMEMNg=`;
Lambda logged current-plan200, no503. The earlier incomplete window-page limit
is resolved for this window, not every log outside it. Metrics Complete, again
Throttles1/ConcurrentExecutionsMax5/Errors0/Invocations10 in the failure minute.
Configured Gateway fields are requestId, route, status and latency; no integration
error detail or upstream Lambda request ID. No causal join or code/configuration
cause found. No app traffic, model calls, load tests, resource changes or fix.

### Unchanged Conclusion

A Lambda concurrency throttle is confirmed in the same minute, at the configured
limit. This is **consistent with concurrency pressure being the likely cause**,
but does **not prove that this Gateway request was the throttled invocation or
explain its exact 503 mapping**. Metrics are minute-level; existing access logs
lack integration error details and an upstream Lambda request ID. Handler logs
cannot join that Gateway request ID. An underlying SDK error is not established
either. Zero Lambda Errors alone cannot rule out handled HTTP error responses.

AWS documents throttles as rejected invocations, separate from invocation/error
counts: [Lambda metrics](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics-types.html).
Granularity limits correlation: [concurrency monitoring](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-concurrency.html).

**No concrete request-level cause was established; no speculative code, retry,
concurrency or policy change was made.** No regression test claims to reproduce
or fix this incident. A future authorized diagnostic change could add safe request
correlation/integration error fields without bodies, headers or tokens. Do not
raise concurrency or add automatic mutation retries on this evidence alone.
This remains a documented reliability limitation.
