# Attribution

## Development Assistance

Codex assisted implementation, testing, packaging, debugging and documentation.
The owner directed requirements and reviewed the work. Runtime interpretation
uses Bedrock Nova Lite, not Codex; neither model confirms restrictions or approves plans.
The architecture illustration was supplied by the project owner as a Gemini-generated image.

Original project code and authored bilingual templates are MIT; see ../LICENSE.
Dependencies, data and official passages retain their own terms. This is a technical
contents review, not blanket legal clearance.

## Software

| Component | Version | Installed declaration |
| --- | --- | --- |
| FastAPI | 0.143.0 | MIT |
| Pydantic | 2.13.5 | MIT |
| Mangum | 0.22.0 | MIT |
| OR-Tools | 9.15.6755 | Apache-2.0 |
| boto3 / botocore | 1.43.109 | Apache-2.0 |
| PyJWT | 2.15.1 | MIT |
| cryptography | 50.0.2 | Apache-2.0 OR BSD-3-Clause |
| React / React DOM | 19.3.0 | MIT |
| Lucide React | 1.53.0 | ISC |
| Vite | 8.3.4 | MIT |
| TypeScript | 5.9.3 | Apache-2.0 |
| openapi-typescript | 7.13.0 | MIT |

Locked trees are in backend/requirements*.txt and frontend/package-lock.json.
137 supplied licence/NOTICE/AUTHORS files and provenance hashes are retained under
[third_party](third_party/manifest.json). Initial upstream notice bytes are unchanged.
The public browser asset THIRD_PARTY_NOTICES.txt accompanies the delivered
React/React DOM/Scheduler/Lucide JavaScript; no native .node/.so/.dll/.wasm is delivered
by the frontend. Browser tests use separately installed Playwright.

Missing build-tool notice recovery is documented in
[native redistribution](NATIVE_REDISTRIBUTION.md), including change-case, Rolldown's
Windows binding and uri-js-replace's subsequently supplied MIT-0 terms. The latter
was checked against all eight unchanged installed dist files, not misrepresented
as a licence originally shipped in the 1.0.1 tarball.

The openapi-core MIT notice is retained from its npm-recorded release commit.
A misclassified upstream license-rule test was replaced with that actual notice;
the manifests preserve its source URL and byte hash. No dependency was upgraded.

Private Lambda ZIPs contain 198 ELF entries; LGPL/GPL-with-GCC-exception/EPL/MPL
source/relink/build-provenance and static-dependency notice issues are not fully
resolved for public binary redistribution. Full supplied texts remain in the ZIPs.
Do not publish deployment archives or dependency binaries. Source dependency
references are not distributions of those binaries. See the precise obligations
and outstanding source/build/SBOM requirements in NATIVE_REDISTRIBUTION.md.

## Evidence

[Open-Meteo](https://open-meteo.com/en/docs/air-quality-api) supplies underlying
CAMS global regional model output. Its [terms](https://open-meteo.com/en/terms)
specify CC BY 4.0 data and non-commercial free-API conditions. Preserve source credit
and limitations; review terms before commercial reuse.

Ministry of Health/NCDC advisories dated November 1, 2025 and September 2022 are
credited with exact excerpts, page references, source URLs and document/excerpt
hashes in backend/app/data/policy_excerpts.json. See [evidence](EVIDENCE.md).
Attribution does not establish an active order, endorsement or blanket permission
to redistribute entire government PDFs.

Timetable, section sizes, teachers, internal school policy and replay concentrations
are sample data. No child identities or medical records are included. OpenAQ
documentation was investigated but no station observations were ingested.
