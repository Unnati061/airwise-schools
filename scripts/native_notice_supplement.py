"""Additional native terms; metadata references are not reproducible-build proof."""
import hashlib
import json
from .upstream_notices import OUTPUT, download


def supplement():
    path = OUTPUT / "manifest.json"
    record = json.loads(path.read_text())
    if record.get("native_supplement_attempted"):
        raise RuntimeError("Already attempted; inspect failures instead of retrying")
    sources = [
        ("OpenSSL/LICENSE.txt", "https://raw.githubusercontent.com/openssl/openssl/openssl-4.0.3/LICENSE.txt", "Observed version string OpenSSL4.0.3 in cryptography Linux Rust binary; no build attestation"),
        ("Boost/LICENSE_1_0.txt", "https://raw.githubusercontent.com/boostorg/boost/boost-1.87.0/LICENSE_1_0.txt", "OR-Tools v9.15 static/header build dependency, not wheel attestation"),
        ("Eigen/COPYING.MPL2", "https://gitlab.com/libeigen/eigen/-/raw/3.4.0/COPYING.MPL2", "OR-Tools v9.15 header dependency with EIGEN_MPL2_ONLY; not wheel attestation"),
        ("bzip2/LICENSE", "https://gitlab.com/bzip2/bzip2/-/raw/bzip2-1.0.8/LICENSE", "Standard1.0.8 notice; actual OR-Tools source uses unpinned master, binary provenance unresolved"),
    ]
    for file, url, basis in sources:
        try:
            content = download(url)
            target = OUTPUT / "backend" / file
            target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(content)
            record["entries"].append(dict(file="upstream/backend/" + file, source_url=url, scope="backend",
                ref_basis=basis, bytes=len(content), sha256=hashlib.sha256(content).hexdigest()))
            print("Retrieved " + file, flush=True)
        except Exception as error:
            record["failures"].append(dict(file=file, source_url=url, error_class=type(error).__name__))
            print("Unavailable " + file + ": " + type(error).__name__, flush=True)
    record["native_supplement_attempted"] = True
    path.write_text(json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    supplement()
