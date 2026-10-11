# Source Release and Binary Redistribution

This is technical licence and artifact guidance,
not a legal opinion or blanket clearance. Original code remains MIT. Upstream
notice texts are unchanged, with hashes/URLs in third_party manifests.

## What Is Actually Included

| Surface | Inspected contents | Consequence |
| --- | --- | --- |
| Source repository | Requirements/npm lock reference dependencies, not bundled executables. Retained licence/AUTHORS/NOTICE texts are not dependency binaries. Check current files and reachable history separately with the supplied scan tools before publication. | Publishing source is not offering the Linux deployment ZIP or installed node_modules for download. Removing current files does not remove historical objects. |
| Local Vite build for hosting | index.html, one JavaScript bundle, one CSS file, THIRD_PARTY_NOTICES.txt. No .node/.so/.dll/.wasm files. React/React DOM/Scheduler/Lucide code is bundled JavaScript, which IS delivered to browser users. | Preserve applicable runtime copyright/licence text in the public notice asset. Build-tool code/notices are attributed, but installed Rolldown native binary is not in this build. |
| Private application Lambda ZIP | Actual198ELF entries, including OR-Tools libraries, NumPy/OpenBLAS/GCC runtimes, cryptography Rust/OpenSSL, AWS CRT and other extensions. Python3.12/x86_64. | Native binary obligations apply to any transfer/distribution of those binaries; private cloud execution does not magically relicense them. The browser receives API JSON, not these ELF files. No public binary release is authorized or cleared. |
| Separate smoke/deployment archives in ignored work | ZIPs stay local/private S3, not Git. | Never attach these to GitHub Releases merely because original source is MIT. |

scripts/repository_artifacts.py checks EVERY reachable commit tree, not just one
path per Git object, plus all reachable blobs for common archive/native signatures.
It reports locations only. Ignore probes confirm workZIPs, node_modules, venv,
Python/test caches, frontend private environment and dist are excluded. This
does not inspect credential caches or prove absence of arbitrary secrets/binary
formats; unreachable/reflog/remote objects are outside this reachable-ref scan.

## Three Build-tool Notice Gaps

- change-case5.4.4: MIT text recovered from the release's registry gitHead.
- @rolldown/binding-win32-x64-msvc1.2.13: MIT text recovered from its registry
  gitHead in the upstream monorepo. Existing Rolldown THIRD-PARTY-LICENSE also kept.
- uri-js-replace1.0.1: release commit38927505b51a74b53444dc723be10e0d2e53823c
  has no LICENSE (root tree/README checked). Upstream later added MIT-0 at commit
  a34c9a5b7a317b6039b2b3cf9d024ee8e418d281. All EIGHT installed dist files were
  verified against that revision's Git blob IDs byte-for-byte. That exact unchanged
  code now has supplied terms; retained notice is labelled subsequently supplied,
  not falsely attributed to the1.0.1tarball. Older metadata's MIT declaration is
  not silently rewritten. No vendor code is committed or dependency upgraded.

All three supplied texts are in the public notice asset. Main manifest now has
137notice files and zero missing-installed-notice entries. Retrieval's initial
uri LICENSE404 remains in resolved_failures for provenance, not hidden.

## Identified Native Conditions

These are redistribution conditions, not claims that every condition has been
fulfilled for a hypothetical public binary release. Actual source/build provenance
limits below matter. Preserve full texts rather than relying on this summary.

| Library/terms | Actual or source-reference evidence | Conditions if binaries are distributed |
| --- | --- | --- |
| NumPy/OpenBLAS/LAPACK, BSD terms | NumPy Linux supplied combined licence; OpenBLAS/GCC shared objects in ZIP. | Retain copyright, conditions and disclaimers in source and binary accompanying materials; respect non-endorsement conditions. |
| libquadmath, LGPL2.1-or-later | Actual shared object; NumPy notice identifies LGPL; complete standard LGPL2.1 text now supplied. | Library object distribution requires corresponding source under section4 (including build/install scripts). Linked-work section6 additionally requires notice/licence, permission for modification/reverse-engineering for debugging modifications, and an allowed relinking route. Section6(b)'s suitable replaceable shared-library mechanism can address linked-work relinking, but is NOT a blanket exemption from library-source obligations. Exact runtime source/build and replaceability have not been established here. |
| libgfortran, GPL3+GCC-exception3.1 | Actual shared object; complete GPL3/exception already in NumPy notice. | Exception permits independent modules' combined Target Code under chosen terms only for eligible compilation processes. Preserve licence/exception notices; it does not remove copyleft from the runtime itself. A binary offer must resolve runtime corresponding-source requirements and build eligibility, not declare all NumPy code GPL or all runtimes MIT. |
| CoinUtils2.11.12/Osi0.108.11/Clp1.17.10/Cgl0.60.9/Cbc2.10.12, EPL2.0 | Actual Coin-family shared objects; exact source tags come from OR-Tools v9.15 CMake pins. Each pinned LICENSE retained. | EPL2section3.1: when distributing Program, make its source available under EPL and accompany it with a statement explaining reasonable source access; include EPL and retain notices (3.2/3.3). Section4 has commercial-distributor obligations. Merely copying EPL text is not a source offer. Separate interface-only linking does not automatically make original application source EPL. |
| OR-Tools/Abseil/SCIP10/SoPlex8/pybind11_abseil, Apache2 | Actual libraries or static/header build references; pinned licence text retained. | Include Apache2 text, retain required attribution/NOTICE where supplied and mark modifications to covered files. Patent/trademark conditions remain; no generic Apache source-offer obligation. |
| HiGHS1.12/pybind11, MIT; protobuf/RE2, BSD | Observed libraries/build pins; pinned text retained. | Retain copyright/licence/disclaimer text and applicable BSD non-endorsement terms. |
| zlib1.3.1, zlib; bzip2, BSD-like | Actual libz/libbz2; CMake pins zlib but bzip2 master is unpinned. bzip2-1.0.8 standard text retained, not binary provenance proof. | Preserve notices; do not misrepresent authorship, mark altered sources and comply with each source's specified notice/disclaimer conditions. |
| Eigen3.4 headers, MPL2; Boost1.87, BSL1.0 | OR-Tools build references EIGEN_MPL2_ONLY, Boost/static SoPlex usage. No separate Eigen/Boost shared library in ZIP. | MPL2 executable distribution of covered code requires its covered source available under MPL and notice of obtaining it (3.2); larger work may have another licence (3.3). BSL retains its notices except its specified machine-executable-only exception. Their inclusion/instantiation and exact patches still need build reconciliation. |
| Cryptography/Rust/OpenSSL | Actual cryptography binary contains version string OpenSSL4.0.3; tagged OpenSSL licence retained, alongside cryptography Apache/BSD. | OpenSSL4.0.3 text is Apache2. Preserve applicable notices/licences; version string is not a full Rust crate/static-link SBOM. No invented exact crate provenance. |
| AWS CRT/XXHash | Actual _awscrt ELF; supplied Apache2 and XXHash BSD2 NOTICE retained. | Preserve Apache/NOTICE and XXHash copyright/disclaimer. Other static AWS CRT dependency notice completeness needs exact build/source reconciliation. |

Primary terms and source evidence:
[LGPL2.1 sections4/6](https://raw.githubusercontent.com/gcc-mirror/gcc/releases/gcc-14.2.0/COPYING.LIB),
[EPL2](https://www.eclipse.org/legal/epl-2.0/),
[OR-Tools v9.15 build pins](https://raw.githubusercontent.com/google/or-tools/v9.15/cmake/dependencies/CMakeLists.txt).
Full GPL/exception, MPL, Apache, BSD and MIT texts are in the retained notice files.

## Precise Remaining Binary-release Issues

1. Exact source trees, applied patches and build/install scripts for NumPy's
   libquadmath/libgfortran are not collected; no tested replace/relink path or
   corresponding-source distribution/offer exists for this ZIP.
2. OR-Tools source pins are not a signed wheel build attestation. Unpinned bzip2
   master, patches, static Eigen/SoPlex/Boost/pybind components and actual Coin
   source correspondence have not been reproduced. No EPL source-offer package
   or comprehensive contributor-notice reconciliation is claimed.
3. Exact cryptography Rust crate and AWS CRT static native dependency SBOM/source
   notices are not fully reconciled. Observed OpenSSL version narrows one component,
   not the whole binary closure. No extra upstream files are invented.

These block claiming a fully cleared downloadable binary distribution. They do
not turn dependency references into binaries in the proposed original-source
repository. Ready-for-source-publication findings must remain scoped: preserve
MIT/notices/disclosures and do not attach ignored ZIPs or binaries. Government
excerpts/forecast credits retain separate terms; no blanket legal clearance.
