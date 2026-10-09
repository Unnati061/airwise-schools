"""Bounded primary-source notice retrieval; no dependency installation or AWS calls."""
import hashlib
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/third_party/upstream"


def download(url):
    with urlopen(url, timeout=12) as response:
        content = response.read(2_000_001)
    if len(content) > 2_000_000 or not content:
        raise ValueError("Notice response exceeds bound or is empty")
    return content


def retrieve():
    manifest = OUTPUT / "manifest.json"
    if manifest.exists():
        raise RuntimeError("Retrieval already recorded; inspect rather than repeat")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    entries, failures = [], []
    def save(name, url, scope, **metadata):
        try:
            content = download(url)
            path = OUTPUT / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            entries.append(dict(file="upstream/" + name, source_url=url, scope=scope,
                                bytes=len(content), sha256=hashlib.sha256(content).hexdigest(), **metadata))
            print("Retrieved " + name, flush=True)
        except Exception as error:
            failures.append(dict(file=name, source_url=url, error_class=type(error).__name__))
            print("Unavailable " + name + ": " + type(error).__name__, flush=True)
    packages = [
        ("change-case", "5.4.4", "blakeembrey/change-case"),
        ("uri-js-replace", "1.0.1", "andreinwald/uri-js-replace"),
        ("@rolldown/binding-win32-x64-msvc", "1.2.13", "rolldown/rolldown"),
    ]
    for package, version, repo in packages:
        registry = "https://registry.npmjs.org/" + quote(package, safe="") + "/" + version
        try:
            release = json.loads(download(registry))
            assert release["name"] == package and release["version"] == version
            ref = release.get("gitHead") or "v" + version
            save("frontend/" + package + "/LICENSE", f"https://raw.githubusercontent.com/{repo}/{ref}/LICENSE",
                 "frontend", package=package, version=version, registry_url=registry,
                 git_ref=ref, ref_basis="registry gitHead" if release.get("gitHead") else "release version tag")
        except Exception as error:
            failures.append(dict(package=package, error_class=type(error).__name__))
    native = [
        ("CoinUtils", "Mizux/CoinUtils", "cmake/2.11.12", "LICENSE"),
        ("Osi", "Mizux/Osi", "cmake/0.108.11", "LICENSE"),
        ("Clp", "Mizux/Clp", "cmake/1.17.10", "LICENSE"),
        ("Cgl", "Mizux/Cgl", "cmake/0.60.9", "LICENSE"),
        ("Cbc", "Mizux/Cbc", "cmake/2.10.12", "LICENSE"),
        ("HiGHS", "ERGO-Code/HiGHS", "v1.12.0", "LICENSE.txt"),
        ("SCIP", "scipopt/scip", "v10.0.0", "LICENSE"),
        ("SoPlex", "scipopt/soplex", "v8.0.0", "LICENSE"),
        ("Abseil", "abseil/abseil-cpp", "20250814.1", "LICENSE"),
        ("protobuf", "protocolbuffers/protobuf", "v33.1", "LICENSE"),
        ("RE2", "google/re2", "2025-08-12", "LICENSE"),
        ("zlib", "madler/zlib", "v1.3.1", "LICENSE"),
        ("pybind11", "pybind/pybind11", "v2.13.6", "LICENSE"),
        ("pybind11_abseil", "pybind/pybind11_abseil", "v202402.0", "LICENSE"),
    ]
    for name, repo, ref, file in native:
        save("backend/" + name + "/" + file, f"https://raw.githubusercontent.com/{repo}/{ref}/{file}",
             "backend", ref=ref, ref_basis="OR-Tools v9.15 build configuration; not wheel attestation")
    save("backend/LGPL-2.1.txt", "https://raw.githubusercontent.com/gcc-mirror/gcc/releases/gcc-14.2.0/COPYING.LIB",
         "backend", ref_basis="Complete standard LGPL2.1 text, not NumPy runtime build provenance")
    manifest.write_text(json.dumps(dict(entries=entries, failures=failures), indent=2) + "\n")
    print(json.dumps(dict(retrieved=len(entries), failures=failures)))


if __name__ == "__main__":
    retrieve()
