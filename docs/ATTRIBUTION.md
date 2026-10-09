# Sources, Tools and Licence Review

Recorded October9,2026 from installed metadata/source records. Principal-component
attribution, **not** an exhaustive transitive licence audit or project licence
grant. Preserve distribution notices; review locked dependencies before publishing.
The owner must intentionally select any licence for original project code.

## Follow-up Release Review

Reviewed metadata for all31 pinned Python runtime distributions and55 installed
npm packages; all had licence declarations. No dependencies were added. NumPy
declares BSD-3-Clause/0BSD/MIT/Zlib/CC0-1.0 components; python-dateutil declares
dual BSD/Apache licensing. Cryptography is Apache-2.0 OR BSD-3-Clause; cffi MIT-0,
typing_extensions PSF-2.0. These declarations are not a full bundled-native
notice/legal compatibility audit: review OR-Tools/NumPy/awscrt/cryptography
distribution notices and preserve required attribution before public release.
English/Hindi templates are authored project code, not third-party translation.

Read-only scripts/release_scan.py scans currently tracked file contents and every
reachable unique Git blob using bounded patterns for AWS access IDs, JWT literals,
private keys, GitHub tokens, credential URLs and quoted secret assignments.
It reports only locations/kinds, never matched values. After staging all intended
files:101 tracked working files and184 reachable unique history blobs, zero
pattern matches and zero private-path findings. A post-commit scan covers the new
commit as well; its blob count increases with this checkpoint.
Ignored work/env/cache files, credential caches, remote secrets and unreachable
objects/reflogs are excluded. No entropy scan or credential validation: absence
of these patterns is not proof of absence of every secret/private document.
Owner still reviews content/history and chooses an original-code licence; no
public repository, visibility change, push or submission was performed.

## AI Assistance

Codex assisted code, tests, packaging, AWS tooling, browser-check harnesses,
debugging and docs. The owner supplied the blueprint/requirements/constraints,
entered credentials privately and retains review/submission responsibility.
Bedrock `amazon.nova-lite-v1:0` is the separate runtime interpreter. Neither
model approves plans or computes official metrics.

## Principal Components

Installed declarations inspected locally, not inferred from remembered licences.
Upstream distributions and their bundled/transitive notices remain authoritative.

| Component | Version | Declared Licence |
| --- | --- | --- |
| FastAPI | 0.143.0 | MIT |
| Pydantic | 2.13.5 | MIT |
| Mangum | 0.22.0 | MIT |
| OR-Tools | 9.15.6755 | Apache 2.0 |
| boto3 / botocore | 1.43.109 | Apache-2.0 |
| PyJWT | 2.15.1 | MIT |
| cryptography | 50.0.2 | Apache-2.0 OR BSD-3-Clause |
| uvicorn (local) | 0.54.0 | BSD-3-Clause |
| pytest | 9.1.1 | MIT |
| React / React DOM | 19.3.0 | MIT |
| Lucide React icons | 1.53.0 | ISC (installed package declaration) |
| Vite | 8.3.4 | MIT |
| TypeScript | 5.9.3 | Apache-2.0 |
| @vitejs/plugin-react | 6.1.2 | MIT |
| openapi-typescript | 7.13.0 | MIT |

Full pinned/resolved trees: backend/requirements.txt, requirements-dev.txt,
frontend/package.json and package-lock.json. Browser harnesses use external
installed Playwright, not a bundled frontend dependency. No third-party photos
or custom AI mascot are application assets; interface icons come from Lucide.

## Data and Documents

- Forecast: [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api),
  underlying CAMS global. Regional model output, not station data.
  [Open-Meteo terms](https://open-meteo.com/en/terms) specify CC BY4.0 data and
  non-commercial free-API conditions. Preserve Open-Meteo/CAMS source credit,
  metadata/limitations; review terms before commercial reuse.
- Official excerpts: Ministry of Health/NCDC advisories November1,2025 and
  September2022; exact passage/page references and hashes in
  [EVIDENCE.md](EVIDENCE.md) and backend/app/data/policy_excerpts.json. Attribution
  is not legal activation, endorsement or a blanket grant to republish complete
  government PDFs. Owner reviews source terms before redistribution.
- OpenAQ: candidate documentation consulted, **no observations ingested**.
- Timetable/teacher identities/internal policy/pasted notices/REPLAY concentrations
  are synthetic. No child identities/medical records.
- Owner-supplied blueprint is planning input, not copied wholesale into this
  candidate public repository. Preserve its true date and implementation history.

References/hashes show what was reviewed, not accuracy, legal effect, campus
exposure or health benefit. A licence for this project's original code has not
been chosen by automation.
