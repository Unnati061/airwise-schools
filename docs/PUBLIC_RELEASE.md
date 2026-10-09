# Public Source Publication

## Publication Verified

Owner pushed https://github.com/Unnati061/airwise-schools . On October 9, 2026,
the signed-out GitHub page displayed Public/main/code/20 commits. Unauthenticated
GitHub API returned private=false/default_branch=main/latest SHA
`7b868e11154274b5fe98b63b960cb817e6480f31`, matching local HEAD and `git ls-remote`
origin/main. Current local branch remains codex/packet-a tracking origin/main.
Documentation changes are pushed to main with `git push origin HEAD:refs/heads/main`
and the resulting remote SHA is verified; no force push or history rewrite.
Initial unavailable-auth/manual instructions below are historical; do not rerun
repository creation/remote-add steps against this existing repository.
Binary obligations, ignored archives and no-public-password limits are unchanged.

Prepared October 9, 2026 IST, from `223beea`. Original code is MIT; third-party
licences, official excerpts and forecast attribution retain their own terms.
This is source publication, not a cleared native binary release or legal opinion.

## Confirmed Local State

- Git root: `C:\Users\Ashwani\Documents\Codex\2026-10-08\read-the-attached-airwise-schools-build\outputs\airwise-schools`.
- Current branch: `codex/packet-a`. Publish its final HEAD to remote `main`;
  no squash, history rewrite, force push or reset is needed.
- No Git remote currently exists. GitHub CLI is not installed, no GitHub
  connector is available, and enabled browser inventory provides no existing
  authenticated GitHub tab. No repository was created or public access verified.
- Source and reachable history scans find no prohibited deployment archives,
  dependency binaries/private paths or recognized secret patterns. These are
  limited detectors, not guarantees; reflogs/unreachable objects are not published
  by the normal branch push and are outside the scan.
- Keep `.gitignore`, root MIT LICENSE, docs/third_party texts/manifests and
  frontend/public/THIRD_PARTY_NOTICES.txt. Do not force-add ignored files.
- Hosted app: https://main.d29v8cmldu93l3.amplifyapp.com . Its public sign-in page
  and notice file are reachable; school operations remain authenticated.
  Never put demo passwords in README, issues, video or submission forms.

## Exact Manual Publication Steps

1. Sign in privately at https://github.com/new . Select your personal account
   as owner; name the repository `airwise-schools`; choose **Public**. Description:
   `School timetable repair, administrator approval and teacher execution reporting with grounded pollution evidence.`
   Do NOT initialize with README, licence or .gitignore: these already exist in
   the reviewed history. Create the empty repository. Do not create release assets.
2. In PowerShell, run the following. Replace `YOUR_GITHUB_USERNAME` with the
   selected account's actual login; do not put a token/password in the URL.

```powershell
Set-Location 'C:\Users\Ashwani\Documents\Codex\2026-10-08\read-the-attached-airwise-schools-build\outputs\airwise-schools'
git status --short --branch
git remote -v
.venv\Scripts\python -m scripts.release_scan
.venv\Scripts\python -m scripts.repository_artifacts
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/airwise-schools.git
git push --set-upstream origin HEAD:refs/heads/main
```

If `origin` already exists, stop and inspect it rather than replacing it. If the
push requires authentication, use Git Credential Manager's browser sign-in
privately. Never paste a token into a command/chat. If no browser sign-in helper
is installed, use an official Git for Windows/Git Credential Manager setup or
GitHub CLI browser authentication; do not invent a credential workaround.
If the remote was accidentally initialized, stop: do not force-push over it.

3. Open repository Settings -> default branch and confirm/set **main**. Confirm
   README, backend, frontend, LICENSE and docs are on `main`, and the latest commit
   matches local `git rev-parse HEAD`. Set the repository About website to the
   hosted app URL above. A local branch rename is optional and unnecessary.
4. Verify the repository page in an incognito/signed-out browser. It must load
   code, README and history without login. Also run this unauthenticated API check:

```powershell
$repo = Invoke-RestMethod -Uri 'https://api.github.com/repos/YOUR_GITHUB_USERNAME/airwise-schools' -Headers @{ 'User-Agent'='AirWise-public-check' } -TimeoutSec 15
$repo | Select-Object html_url,private,default_branch
git ls-remote origin refs/heads/main
git rev-parse HEAD
```

Expected: `private=False`, `default_branch=main`, public `html_url`; the remote
main SHA must match local HEAD. A timeout/403/404 does not prove public access.
Do not claim publication verified until both signed-out access and SHA checks pass.

5. Record the real repository URL/result in STATUS, README, BLUEPRINT_AUDIT and
   HACKATHON. Commit and push that documentation update to `main`, then recheck
   the latest SHA. No repository URL is invented in this prepared document.

## Native Obligations Still Open

Affected: ignored local/private S3 Linux application and smoke/deployment ZIPs,
installed Python/native dependencies, or any future distribution of those
binaries. The inspected application ZIP has 198 ELF entries. Git history contains
references/notices, not those dependencies. Hosted assets contain runtime
JavaScript with a publicly verified notice file, not the native libraries.

Before offering native ZIPs, obtain the exact component source/version/patch/build
inventory, not just upstream CMake pins. Specifically:

- NumPy's actual libquadmath: complete corresponding source/build/install scripts
  under LGPL2.1 section 4; retain licence/notice and satisfy linked-work section 6
  modification/reverse-engineering and replace/relink conditions. Shared-library
  use alone does not discharge the distributed library's source requirement.
- Actual libgfortran: resolve GPL3 runtime corresponding-source requirements and
  confirm GCC Runtime Library Exception 3.1 eligible-compilation conditions. The
  exception does not relicense the runtime itself as MIT.
- Actual CoinUtils/Osi/Clp/Cgl/Cbc: reconcile binary-to-source/patch correspondence,
  retain EPL2/contributor notices, make corresponding Program source available
  under EPL with a reasonable source-access statement. Copying licence text alone
  is not an EPL source offer. Review commercial-distributor conditions if applicable.
- OR-Tools static/header components (Eigen/SoPlex/Boost/pybind), unpinned bzip2 and
  other build dependencies: reconcile actual inclusion and exact modified sources;
  satisfy MPL covered-source access where applicable, and all Apache/MIT/BSD/
  zlib/Boost notice/modification conditions. Not every build reference proves a
  component is present in a particular binary.
- Cryptography Rust/OpenSSL and AWS CRT static dependencies: complete the exact
  SBOM and contributor/NOTICE reconciliation. OpenSSL4.0.3 was observed and its
  Apache2 notice retained, but it is not a complete Rust/CRT static dependency bill.

Full terms/evidence are in NATIVE_REDISTRIBUTION.md and retained upstream texts.
This review does not conclude that every private cloud transfer is exempt or
fully compliant; unresolved deployment-binary issues remain for proper review.
Do not attach these ZIPs or binaries to GitHub Releases while those issues remain.

## Remaining Owner Actions

1. Complete publication and verify public default-branch access as above.
2. Privately verify current AWS spend, credits and expiry; previous bounded billing
   requests timed out. Do not treat the earlier reported $100 as current balance.
3. Record the under-three-minute hosted admin -> teacher -> admin demo using
   docs/DEMO.md, showing real AWS usage, labelled replay/forecast limits and no
   passwords/tokens/account identifiers. Stored interpretation is not a new call.
4. Upload the video public/unlisted and test its signed-out link. Fill the real
   repository/video links into docs/HACKATHON.md. Confirm eligibility, deadline
   and event requirements before the owner submits; nothing is submitted here.
