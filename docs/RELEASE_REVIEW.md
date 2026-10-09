# Release Review - October 9, 2026 IST

Continued from7a803eb. Working tree initially clean. No repository creation,
publication, submission, model calls, AWS mutation or billing-setting changes.

Follow-up from9acf1fe: all three build-tool notices now reconciled and137 full
texts preserved. See NATIVE_REDISTRIBUTION.md for actual Git/frontend/ZIP contents,
applicable redistribution conditions and precise remaining binary-provenance
issues. The sections below are the previous checkpoint's chronological record,
not a current claim that those three notices remain missing. A prepared wording/
notice deployment first stopped at STS. After restored connectivity, read-only
preflight passed but the single S3 PUT failed with ConnectionClosedError. Object
state is unverified; no Lambda/Amplify update reached. Hosted verification remains
pending; exact handoff is in AWS_APP.md. No retry or binary publication.

Subsequent resume from06f8660: owner console-uploaded preserved bytes. Actual
S3 FULL_OBJECT CRC64/NVME/local SHA256 verified, existing Lambda CodeSha256
matched, Amplify job3 SUCCEED. Public browser notice hash and private admin revised
English/Hindi preview/logout verification passed. No model calls, automatic app
ZIP upload retry, new resources or publication. Historical pending claims below
are superseded; precise native binary-release obligations remain unchanged.

## Original Code and Third-party Materials

The owner selected MIT for original AirWise Schools code. Root LICENSE uses
2026 AirWise Schools contributors; it does not relicense dependencies, upstream
notices, official excerpts, forecast data or an owner-supplied blueprint.
Keep all upstream copyright/licence/NOTICE text and source attribution intact.

scripts/collect_notices.py copied115 supplied files, preserving exact bytes and
SHA256 provenance in docs/third_party/manifest.json. Sources: the SHA-verified
deployed Linux ZIP and installed locked frontend packages, not just Windows
Python metadata. No archive rebuild or binaries added to Git. Original notices
remain in the Lambda ZIP; docs/third_party contains copies, not replacement terms.
The frontend public/THIRD_PARTY_NOTICES.txt includes original MIT plus supplied
frontend notices, including runtime React/React DOM/Scheduler/Lucide and build
tools. The current minified local deployed-build artifact contains ISC identifiers
but not the searched MIT/copyright comments: do not rely on minifier comments
alone. Vite copies the notice asset into the next build. No hosting update in this
read-only release pass, so its hosted availability is NOT verified.

### Actual Bundled-notice Findings

- NumPy Linux wheel: BSD terms for NumPy/OpenBLAS/LAPACK, GPL-3.0-or-later WITH
  GCC-exception-3.1 for libgfortran, LGPL-2.1-or-later for dynamically linked
  libquadmath. Shared objects are actually in the ZIP. Preserve exceptions and
  notices, not a blanket BSD/MIT label. Exact source/build provenance and applicable
  source/relinking obligations must be resolved before distributing this binary
  bundle. No blanket copyleft conclusion about original code is made here.
- AWS CRT NOTICE includes XXHash BSD2 terms, retained with its Apache2 licence.
- python-dateutil preserves Apache/post2017 and BSD notices; its text says the
  BSD licence applies to all code. Do not reduce it to an invented MIT licence.
- Cryptography includes its Apache/BSD choice; exact bundled Rust/OpenSSL
  provenance/notice completeness has not been audited from source/build records.
- OR-Tools supplies Apache2 text, but its ZIP also contains Cbc/Cgl/Clp/CoinUtils/
  Osi, HiGHS, SCIP10, RE2, zlib, bzip2, protobuf and Abseil libraries. The wheel
  notice alone does not enumerate all version-specific dependency terms. Upstream
  native build/source notice reconciliation remains unresolved before binary
  redistribution. Merely using CP-SAT does not remove those packaged libraries.
- Supplied frontend tool notices include Vite's bundled notices, Rolldown
  THIRD-PARTY-LICENSE and TypeScript ThirdPartyNoticeText.txt. Three installed
  tools lack a standalone supplied notice: change-case5.4.4, uri-js-replace1.0.1,
  @rolldown/binding-win32-x64-msvc1.2.13. They declare MIT; declaration is not the
  missing copyright text. Recover exact-version upstream terms before distributing
  those packages/binaries; no inferred text or claim of complete clearance.
- Open-Meteo/CAMS attribution and CC BY4.0/noncommercial free-API conditions remain
  distinct from MIT. Government excerpts retain their exact source/page/hash;
  authority/attribution is not a blanket redistribution grant. See ATTRIBUTION.md.

This is a technical inventory, not legal advice or legal clearance. For the
planned original-source repository, do NOT add node_modules, venv, deployed ZIPs,
native binaries, work/private configuration or complete third-party PDFs. Keep
locked dependency references and these notices. Obtain specialist review before
offering binary releases or changing commercial use. No packages were relicensed.

## Bilingual Review

Reviewed all template branches: bound/missing date, LIVE/REPLAY/MANUAL, review-needed,
changed activities, explicitly permitted deferral, no changes and acknowledgement.
Stable activity/period/room/alternative IDs and plan versions match in both
languages. No dates, legal orders, closures, healthier indoor air or exposure
benefits are invented. Existing review checkbox gates copy/download, never sends.

Concrete fixes: replace stiff Hindi acknowledgement wording with confirmation of
receiving the plan, distinguish it from implementation; align both languages on
explicit permission for deferral; clarify that revised information awaits approval
of a new plan; describe replay as neither current-pollution description nor
government-order evidence. Natural wording reviewed here, not professional
translation certification. Focused tests check matching facts/caveats/branches.
These source wording fixes are NOT redeployed; hosted7a803eb wording remains until
a separately authorized bounded update. No backend contract/solver/auth change.

## Read-only Billing Outcome

At19:16:21IST October9, profile airwise STS succeeded, account identifier redacted.
One Billing GetCredits and one Cost Explorer GetCostAndUsage attempt each ended
in ReadTimeoutError (connect4s/read12s/one total attempt); no AccessDenied/SCP
claim is supported by those timeouts. No repeat requests or billing enablement.
Global billing endpoints are used by the SDK; Sydney application configuration
and account did not change. scripts/release_billing.py emits only safe summaries.

Current spending, remaining credits, expiry and service coverage are UNVERIFIED;
previously owner-reported100USD is not a current balance. The requested cost
query was account-wide month-to-date through October9UTC exclusive, grouped by
charge type, not project-tagged or real-time. Even a successful query would be
delayed/estimated, not a final bill. Timeout does not prove the service did not
process/charge its nominal API query. No Bedrock calls were made.

Owner checks privately: AWS Billing and Cost Management -> Bills, current month:
inspect service charges before credits and net estimated due. Then Credits:
record remaining AND estimated remaining, expiry, enabled status and covered
services. If these are managed project credits, also inspect AWS Settings for
the assigned project balance/expiry; it is not necessarily identical to account
billing. Do not change preferences, activate services or paste account/credit IDs.
Share only amounts/currency/expiry/service coverage if a follow-up is needed.

AWS documentation: [GetCredits](https://docs.aws.amazon.com/boto3/latest/reference/services/billing/client/get_credits.html),
[credit tracking](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/tracking-free-tier-usage.html).

## Owner Release Steps

Relevant checks passed:8 preview/notice tests, two existing warnings,8.96s;
d2 production build1907modules/3.74s. Notice source/dist SHA256 both
583bb0e6ec80b2c8ed9e6560aeb112bd0f26eea91f806d467cb11d82ce1c04e1.
No contract changes, full-suite rerun, browser/model calls or AWS deployment.
Staged secret-pattern scan:222 tracked files/216 reachable history blobs,
zero pattern/private-path findings; not a comprehensive guarantee. Upstream notice
whitespace initially failed git diff --check. It is intentionally preserved, not
rewritten: whitespace checks exclude only copied third-party notices/public
notice aggregate via .gitattributes; original code/docs remain checked normally.
PyJWT's upstream AUTHORS.rst heading underline also triggers Git's conflict-marker
heuristic. Scoped diff checks exclude the preserved copies/public aggregate;
their integrity is checked against recorded hashes instead. No actual merge
conflict is present, and upstream text is not altered to silence the heuristic.
Commands: `python -m scripts.collect_notices` (use repository venv),
`.venv\Scripts\python -m pytest backend/tests/test_previews_metrics.py backend/tests/test_release_review.py -q`,
`npm --prefix frontend run build -- --mode d2` and
`Get-FileHash frontend/public/THIRD_PARTY_NOTICES.txt, frontend/dist/THIRD_PARTY_NOTICES.txt -Algorithm SHA256`.

1. Resolve the billing check and review notices/terms above. A future hosted update
   must include the browser notice asset and revised wording; this pass did not
   redeploy. Do not publish binary dependencies while obligations remain unresolved.
2. Privately review tracked files/history and rerun scripts.release_scan. It is
   pattern-limited, not a substitute for content review. Never publish credentials
   or demo-user passwords. Preserve honest commit dates/history.
3. GitHub -> New repository -> name airwise-schools -> Public. Leave README,
   .gitignore and licence initialization unchecked: this checkout has them already.
   Do this yourself only after review; no repository created here.
4. In the repository root, replace YOUR-USERNAME and run:

```powershell
git remote -v
git remote add origin https://github.com/YOUR-USERNAME/airwise-schools.git
git push -u origin codex/packet-a
```

If origin exists, inspect its URL first; do not overwrite it blindly. Use normal
GitHub credential-manager/browser authentication, never a token in the URL. No
branch rename, history rewrite, or node_modules/ZIP/private artifact upload.
5. Open the repository signed out; verify README, LICENSE, notices, source and
   docs are readable. Add the actual repo URL to README/writeup before submission.
6. Privately sign admin/teacher into separate browser profiles; prepare an
   unapproved valid synthetic draft and a cropped read-only Sydney AWS view.
   Follow DEMO.md's170second script; avoid recording sign-in/passwords/account IDs,
   storage/network panels or private console settings. Keep the current mode/date
   truthful (MANUAL/date unspecified is not LIVE or dated REPLAY). Show approval,
   new-version acknowledgement, exception reporting and administrator Review.
   Show previews and planned/reported hours briefly, no exposure/health claim.
7. Rehearse once with actual delays, then record under3minutes. Do not make extra
   model calls for footage: show the stored actual Nova interpretation/timing.
   Review the recording for secrets before any owner-controlled public/unlisted
   YouTube upload; test its link signed out. Recording/upload/submission not done.
8. Finalize writeup links; confirm actual organizer deadline/eligibility/check-in,
   judge-access expectations and required disclosure, then submit manually once.

GitHub instructions follow [official existing-code guidance](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github).
