# Packet C evidence and grounded notice review

This is the Packet C historical record; the later hosted five-view verification
is in HOSTING.md. The old `scripts.c_demo` below resets synthetic-user passwords
and is NOT the submission/browser demonstration path. Do not run it against the
current identities merely to reproduce a video. Use stored actual analysis and
private existing sign-in as described in DEMO.md; do not spend extra model calls.
The absent observation feed/model issue time and advisory limitations remain.

## Verified data and limitations

Fictional school coordinates: 28.4744, 77.5030 (Greater Noida vicinity, not a sensor).
Provider: [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api),
explicit `domains=cams_global`, PM2.5/PM10, five forecast days and UTC timestamps.
CAMS global regional output: 0.4 degrees, approximately 45 km; native three-hourly
output served hourly with interpolation. Local roads, classrooms and campus
exposure are unresolved. Concentrations are instantaneous near-surface model
outputs, not station measurements, daily averages or Indian AQI. No US/European
AQI is requested or relabelled; no AQI, legal GRAP stage or closure is calculated.

Actual successful live fetch: 2026-10-08 17:25:12.562767 UTC. Provider grid: 28.5,
77.5; valid times 2026-10-08 00:00 through 2026-10-12 23:00 UTC (120 hourly points
per pollutant). At valid time 2026-10-08 18:00 UTC: PM2.5 81.0 and PM10 131.3
ug/m3. These are forecasts, not measured conditions. Retrieval age was 2 minutes
42.5 seconds at completed verification, 17:27:55.058284 UTC. Model issue time is
NOT supplied and remains null. `generationtime_ms` is not a model issue timestamp.
Snapshot: 0481c307-c475-4b14-94a0-f15b3f48dc41; HTTP-body SHA-256:
`bdc957aecb513ac7cb2cc1e11e37c45624af090d19b582e6d79226c725d5dc68`.

The administrator API caches live retrieval for 15 minutes. Analysis/confirmation
reject retrieval older than one hour, future retrieval beyond five minutes, an
expired horizon or missing future values for either pollutant. These are explicitly
application evidence-review freshness rules, not health or legal concentration
thresholds. A fresh HTTP response cannot prove the underlying model cycle is fresh.
Failed refresh preserves original age; never replaces live data with replay.
Snapshots and parsed raw provider JSON persist in the existing compressed DynamoDB
table. Original HTTP bytes are not retained; their hash is provenance recorded at
retrieval, not a reproducible checksum of reserialized JSON. No new S3 bucket.

Observation-feed discovery stopped early, within the 60-minute cap: no private
OpenAQ key was configured, so no authenticated station/feed lookup was attempted
and no suitable fresh station was verified. See [OpenAQ API location discovery](https://docs.openaq.org/api/operations/locations_get_v3_locations_get)
and [latest observations](https://docs.openaq.org/resources/latest). Observations
are explicitly unavailable; no station data is invented or silently substituted.
OpenAQ ingestion remains unimplemented until a privately supplied key and suitable
fresh station can be verified. The absence of observations is not evidence of
clean air or proof of forecast accuracy.

REPLAY is an immutable, labelled synthetic October 12 fixture, PM2.5 180 / PM10
260 ug/m3, with no physical resolution. It has its own cache pointer and source;
analysis and confirmation carry its mode. It is not live pollution evidence.
Every API result exposes mode/limitations; the minimal interface is authenticated
JSON, not a polished evidence dashboard. A replay-confirmed version stays explicitly
bound to replay evidence and must never be represented as a real operational order.

## Verified official policy evidence

Catalog: backend/app/data/policy_excerpts.json. Exact excerpt hashes are computed
and retained alongside source-byte hashes in typed POLICY records. Downloaded PDFs
were hashed, their passages extracted and relevant pages visually checked.
Verified 2026-10-08; policy verification metadata is separate from pollution freshness.

- [NCDC Health Advisory, Ministry letter dated 1 November 2025](https://ncdc.mohfw.gov.in/uploads/pdf/air2.pdf):
  India-wide advisory, Annexure IV school children, paragraph 5(ii), PDF page 26 /
  printed page 22. Citation `ncdc-2025-school-5ii`. School outdoor-activity guidance,
  not an active closure order. SHA-256
  `1f536f1c2bda53d3a82bb5ce6d77ffdcae2dd39b0d61f1555bbb2c6880a7e701`.
- [NCDC Health Advisory, September 2022](https://ncdc.mohfw.gov.in/uploads/pdf/air4.pdf):
  India-wide public-health advisory, Annexure I / General Population item 9, PDF
  page 15 / printed page 14. Citation `ncdc-2022-annex1-9`. General/vulnerable-population
  context; its AQI wording does not authorize conversion of model concentrations.
  SHA-256 `b91fc3b6b50fc3a3638948e7ab74eb0df1a7c9286522e2066061095cd899fc34`.
- `internal-review-only-v1` is fictional-school application policy, explicitly
  INTERNAL_POLICY, not government authority. No numerical pollution trigger exists.

The current NCDC index links were verified; older WordPress document links returned
404. An attempted historical CAQM PDF returned a challenge rather than verifiable
PDF bytes and was excluded. No active GRAP stage, current school order or local
closure has been established. A pasted notice is always UNVERIFIED until a human
reviews its authenticity, dates, support and scope. Citation membership validation
does not prove semantic entailment or a notice issuer's authenticity.

## Model, safeguards and actual AWS changes

Exact working model: `amazon.nova-lite-v1:0`, direct in-region Converse in
`ap-southeast-2`, profile `airwise`, through boto3. The availability preflight
reported AUTHORIZED / AVAILABLE agreement, entitlement and region. One initial
probe returned AccessDeniedException; a later response exposed fenced JSON parsing
before the bounded probe passed with 10 input + 13 output tokens. No SCP or account
settings were changed. The adapter now accepts only JSON or a sole JSON fence,
then validates schema and supplied citation/activity IDs. See the
[official Nova Lite model card](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-lite.html).
No Strands, public bypass, cross-region inference profile or automatic retry.

Only cloud change: inline policy `airwise-c-nova-lite` on the existing owned role
`airwise-b2-runtime-a1f7411817`, allowing `bedrock:InvokeModel` solely on
`arn:aws:bedrock:ap-southeast-2::foundation-model/amazon.nova-lite-v1:0`.
Existing table `airwise-b2-data-a1f7411817` and Cognito pool are reused. No new AWS
resources, no changes to the successful smoke-test Lambda, SCPs or account settings.
The role's previous DynamoDB policy remains unchanged. Script refuses policy
collisions or unexpected role ownership; it does not broaden unrelated permissions.

Requests: pasted notice <=3,000 characters, <=3 curated excerpts, model payload
<=14,000 encoded bytes plus a fixed system prompt, output <=700 tokens / 12,000
characters. Explanation output <=100 tokens. Model transport: five-second connect,
20-second read, one attempt. Upstream STS and database operations have their existing
bounded retries; this is not an end-to-end latency SLA.
Daily server allowance: ten attempts per authenticated administrator per Asia/Kolkata
calendar day, shared by interpretation and explanation; failures consume allowance.
Identical requests are cached durably. Conditional quota/pending transactions
coalesce concurrent duplicates. A process crash may leave PENDING and consume a
slot; no automatic expiration/resubmission exists. Usage events log actor, time,
model, counts, request hash, transport status/error class; never passwords, tokens
or notice input. Model outputs and interpreted notice material are private records.
Schema/citation rejection is retained in ANALYSIS, separate from transport usage.

All analyses require administrator review, including ambiguous dates and unsupported
instructions. Confirmation rejects invalid/model-failure results, stale versions,
stale/mismatched evidence, unsupported/uncited proposals and dates/periods outside
the existing affected weekday/evidence horizon. Human review supplies an explicit
calendar date and periods, with notice/ambiguity review acknowledgements. Inputs
retain an EvidenceBinding; draft and approval bind to that input/restriction revision.
Confirmation marks an old approved version for review; it does not replace it.
Existing independent validation, teacher authorization and approval are unchanged.
Explanations use model-selected fact IDs only; final text, counts and metrics are
computed outside the model. Invalid/failing explanation output uses deterministic
validated facts, explicitly labelled with model_status.

## Local demonstration and actual result

From the repository root, with authenticated airwise and existing work/aws-b2.json:

```powershell
.venv\Scripts\python -m scripts.c_demo
```

This resets passwords ONLY for the dedicated synthetic demo users, to random
memory-only values, signs in through real Cognito, resets the synthetic fixture to
an administrator-confirmed unrestricted baseline, fetches live evidence and uses
a clearly labelled synthetic pasted notice. It spends at most two uncached model
calls. It confirms restriction scope as the administrator, repairs, independently
validates and separately approves. No credentials/private notice content printed.

Actual analysis: SUCCESS, Nova Lite, 771 input / 195 output / 966 total tokens.
Cached identical analysis returned the same record without another model call;
input revision did not change until administrator confirmation. Teacher confirmation
and approval both returned 403. New input revision:
`19b1cabe-812b-453f-8843-1efef7e23e64`, LIVE binding for 2026-10-12.
Draft and approved version: `12826b9f-8209-49c3-ac24-e8d95bfe821a`, OPTIMAL,
independent validation passed. Activity `6-a:Mon-2` retains Mon-2, moves field ->
room-6-a and uses approved `indoor-movement`. Counts: zero changed periods, one
substitution, zero deferrals, one room move; all 240 activities accounted for.
Grounded explanation returned SUCCESS, using the independently computed counts.
This is a synthetic-school workflow demonstration, not an authenticated government
notice, an actual campus condition, or a real closure decision.

Protected API additions: GET /evidence/forecast?mode=LIVE|REPLAY, GET /evidence/{id},
GET /policy-excerpts, POST /notice-analyses, GET /notice-analyses/{id},
POST /notice-analyses/{id}/confirm, GET /draft-plans/{id}/explanation.
Use existing WORKFLOW.md private authentication steps; no role selector or bypass.
Loopback backend: http://127.0.0.1:8002. Generated frontend API types updated.

## Checks and remaining work

Targeted tests cover fabricated citations, relative/missing dates, failed model/cache
restart, replay/live mismatch, missing/stale evidence, failed live retrieval, daily
allowance, pending duplicate claims, unsupported/out-of-scope instructions, explicit
calendar/period scope, teacher/unauthenticated denial and deterministic explanation
fallback. B1/B2 regression suite is retained. See STATUS.md for final counts.
pip check, generated OpenAPI types and TypeScript/Vite build passed. An unscoped
pytest invocation mistakenly collected the historical ignored Linux ZIP staging
dependencies and failed collection; nothing was deleted, changed or rebuilt there.
The documented targeted backend/tests command passed.

Optional source re-verification helper: `scripts/verify_policy_sources.py --local`
reads the already downloaded public PDFs and asserts curated hashes/passages.
It uses the host's bundled pypdf runtime, not the application virtual environment;
pypdf is not a backend dependency. Without --local it downloads bounded official
PDF responses again and refuses changed bytes until a human reviews the catalog.

No new Python/Node dependencies. Offline fixtures do not verify source correctness;
the separate real demonstration establishes connectivity/authentication only.
Remaining work: verified fresh observations/private key, active-order verification,
production session/MFA and record-retention operations, expired-pending recovery,
human evidence-review interface. Single-period / one-day synthetic-school scope
continues. No forecast-accuracy or medical/legal safety guarantee.

Cleanup for C ONLY, when intentionally ending model access:
`aws iam delete-role-policy --role-name airwise-b2-runtime-a1f7411817 --policy-name airwise-c-nova-lite --profile airwise --region ap-southeast-2`.
Do not delete the shared table, pool, runtime role or Packet A resources merely to
clean up C. Their separate cleanup is documented in WORKFLOW.md / AWS_SMOKE.md.
Usage/evidence records currently have no TTL; any future deletion/retention policy
requires deliberate review, never blind file or database cleanup.
