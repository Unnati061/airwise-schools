# Recovery, Bilingual Previews and Operational Metrics

October9,2026; continued from `1b8c067`. Same architecture/resources, no model calls
or message delivery. Native solver, independent validator, authentication and
version/approval checks are preserved. Generated OpenAPI contracts updated.

## Request Recovery

Finite frontend timeouts clear loading/action locks and display errors. Reads
have an explicit Retry loading button; it is disabled while loading. Approval,
acknowledgement and execution-report indeterminate/5xx failures offer an explicit
Retry the same request button. No automatic mutation retry or paid analysis retry.
The retry closes over the original version/payload, not current edited fields.

Approvals already have durable draft-ID receipts and never rewind the current
pointer on replay. New UI reports use a UUID request_id; the transaction stores
the latest report, immutable request receipt, state condition and audit together.
Replaying a receipt returns the saved result without overwriting a later report
or creating another event/count. Reusing its ID with different content returns409;
foreign teachers403. Legacy clients without UUID retain identical-payload
deduplication, but do not get the new durable late-retry guarantee.

Backend restart/concurrent request tests exercise the receipts. A refreshed browser
does not retain an unfinished report form/request UUID: read saved reports before
entering another action. The explicit in-tab retry preserves its UUID/payload.
No claim of exactly-once networking, global logout revocation or durable jobs.

An identical model-cache PENDING claim younger than five minutes returns409,
explicitly without a second model request. After five minutes it is conditionally
fenced into MODEL_FAILURE with OUTCOME_UNKNOWN_NO_RETRY. The allowance remains
consumed; a late writer with the old etag cannot commit. Identical retries return
the failure instead of reissuing a possibly paid call. Original provider completion
and token usage may be unknown after a crash; failure does not mean zero cost.
Five minutes exceeds the28second Lambda deadline and bounded model transport;
this is an application recovery rule, not a worker lease/queue.

## English/Hindi Previews

Existing administrator-only GET /approved-plans/{version} now returns a
MessagePreview from immutable approved facts. Review renders both languages,
PREVIEW ONLY / NOT SENT labels, version, evidence mode, date when actually bound,
changed activity/period/room/alternative IDs and review-needed warning. REPLAY
is explicitly synthetic; manual input with no bound date says date unspecified.
No invented clock time, legal order, closure or health-effect statement.

Templates are authored deterministically, not paid model translation. Stable IDs
remain identical in both languages; they are not translated into new identifiers.
Administrator checks both language versions/dates/assignments before copy or UTF-8
text download. The checkbox is local review gating, not a persisted approval/audit
of message wording or professional translation certification. No sending endpoint,
parent address list, messaging service or publication was added.

## Outdoor Student-hours

Activity.duration_minutes is nullable for backwards compatibility, integer1-180.
The labelled synthetic fixture explicitly declares40minutes per activity; this is
demo input, not measured lesson duration. Stored old activities retain null: no
retroactive40minute default or rewrite of immutable approved snapshots.

Restricted periods cover a whole discrete single-period activity in this MVP.
Intersection minutes are its declared duration when its section/period matches
any confirmed restriction, otherwise0. Multiple matching restrictions count once.
For each activity: student-hours = synthetic section size × those minutes /60.
Sum integer student-minutes first; backend hours rounded to6decimals, UI to2.
No partial-period/clock-interval or multi-period support is claimed.

Existing administrator execution review returns:
- Original restricted outdoor student-hours.
- Approved restricted outdoor student-hours.
- Planned indoor substitution student-hours, only an explicit alternative moving
  an originally restricted outdoor activity indoors (not a deferral).
- Teacher-reported completed indoor student-hours, only COMPLETED for that
  activity's assigned teacher and exact plan version.
- Unknown indoor execution student-hours, no report or NEEDS_CLARIFICATION.

Latest reports are keyed by activity/version; retries do not sum extra hours.
Acknowledgement is not completion. COULD_NOT_IMPLEMENT contributes no completed
hours; deferrals are never represented as completed indoor activity. Missing any
relevant duration returns unavailable/null totals and lists the activity IDs,
not a misleading zero. These are synthetic scheduling/teacher-self-report metrics,
**not measured exposure reduction, cleaner indoor air or health benefits**.

## Local Checks and Deployment

85backend tests passed (two existing warnings), including nine new tests for
receipt replay/restart/concurrency/content mismatch/permissions, expired pending,
bilingual facts/manual dates/replay, duration accounting/old unknown duration,
exceptions/version isolation, duplicate restriction and deferral semantics.
Type generation and d2 production build passed. An initial build began before
generation finished and failed on old types; the sequential completed build passed.

Controlled offline Chrome checks passed lost approval/report503 recovery with
the same report UUID/payload, review-gated Hindi/English download, metrics and
1440×960 /390×844 layouts (no page overflow). Screenshots inspected; these are
labelled test doubles, not cloud permission evidence. No model/network-AWS calls.

New application ZIP reuses unchanged dependency entries from the SHA-verified
proven Linux archive, replacing only packaged backend code/data. No Windows
site-packages, profile/environment/cache files, tests or new dependencies.
- File: work/airwise-app-features.zip.
- Compressed87,395,863bytes; extracted240,725,058bytes including dependencies,
  below250MiB. Python3.12/x86_64,1024MB,28s, concurrency5 unchanged.
- SHA256 `4c8a9eb26fb8409f1608b72096d39de1509c5db3d31fa0937469e1294cf1d2c1`.
- Private existing bucket airwise-smoke-artifacts-a1f7411817; object
  `application/features/4c8a9eb26fb8409f1608b72096d39de1509c5db3d31fa0937469e1294cf1d2c1/airwise-app-features.zip`.
- One upload; S3 actual SHA256 checksum and size verified, not metadata/ETag.
- Existing owned Lambda updated with RevisionId guard; code SHA matched digest
  bytes encoded as Base64. No IAM, environment, route, Cognito, CORS or smoke change.
- Existing Amplify/main manual deployment job2 SUCCEED; staticZIP89,012bytes.
  No app/branch/resource recreation, secret URL logging or public bypass.

Commands:
```powershell
.venv\Scripts\python -m pytest backend/tests -q
.venv\Scripts\python -c "import json; from backend.app.main import app; print(json.dumps(app.openapi()))" | Set-Content -Encoding utf8 work/features-openapi.json
# From frontend: node node_modules/openapi-typescript/bin/cli.js ../work/features-openapi.json -o src/api.d.ts
npm --prefix frontend run build -- --mode d2
.venv\Scripts\python -m scripts.ui_fixtures
node scripts/check_features.cjs
.venv\Scripts\python -m scripts.update_features package
.venv\Scripts\python -m scripts.update_features update
node scripts/check_features_live.cjs
.venv\Scripts\python -m scripts.release_scan
```
Browser commands require the existing external PLAYWRIGHT_MODULE. Do not rerun
the one-shot deployment helper; its manifest blocks partial/repeated updates.
Existing app: https://main.d29v8cmldu93l3.amplifyapp.com . Actual hosted results
are recorded separately in STATUS after private sign-in; deployment alone is not
claimed as workflow success. No Bedrock call was needed.

Actual hosted private admin -> teacher A -> admin verification completed:
generation/validation/approval/repeat approval, review-gated previews,
acknowledgement then COMPLETED, same UUID receipt/timestamp, and administrator
Review passed. Teacher approval, administrator preview and foreign assignments
denied403. Version110a2908-9343-4747-9fd5-47398492b0ac showed original outdoor20,
approved outdoor0, planned indoor20, teacher-reported completed20, unknown0hours;
reported1/completed1/unresolved0. Synthetic self-report, not real student activity.
The explicit40minute metadata revision preserved original IDs/restrictions but
has MANUAL provenance/no bound date; preview disclosed date unspecified. Historical
bound versions were not rewritten. Actual desktop/mobile layout checks passed;
browser signed out at completion. No new paid interpretation was needed.

Cleanup: retain the working deployment for judging. When deliberately ending it,
use existing AWS_APP/HOSTING resource-specific cleanup. This task added only the
exact feature ZIP object above; delete only that key after confirming it is no
longer required, never the reused bucket/table/pool/smoke artifacts. No cleanup run.
