"""Copy supplied distribution notices unchanged, with provenance; no cloud access."""
import hashlib
import json
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
ZIP_SHA = "4c8a9eb26fb8409f1608b72096d39de1509c5db3d31fa0937469e1294cf1d2c1"
OUTPUT = ROOT / "docs/third_party"


def notice(name):
    base = PurePosixPath(name).name.upper()
    if base.endswith(('.TS', '.JS', '.PY', '.MAP')):
        return False
    return base.startswith(("LICENSE", "LICENCE", "COPYING", "COPYRIGHT", "AUTHORS")) or base in (
        "NOTICE", "NOTICE.TXT", "THIRD-PARTY-LICENSE", "THIRDPARTYNOTICETEXT.TXT")


def collect():
    archive = ROOT / "work/airwise-app-features.zip"
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == ZIP_SHA
    entries = []
    missing = []
    def copy(destination, content, origin):
        path = OUTPUT / destination
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        entries.append({"file": destination, "origin": origin, "bytes": len(content),
                        "sha256": hashlib.sha256(content).hexdigest()})
    with ZipFile(archive) as source:
        for name in sorted(source.namelist()):
            if not name.startswith("backend/") and notice(name):
                copy("backend/" + name, source.read(name), "Linux ZIP: " + name)
    lock = json.loads((ROOT / "frontend/package-lock.json").read_text())
    for key, metadata in sorted(lock["packages"].items()):
        if not key or not key.startswith("node_modules/"):
            continue
        folder = ROOT / "frontend" / key
        if not folder.exists():
            continue  # Optional packages for other operating systems are not installed.
        paths = sorted(p for p in folder.rglob("*") if p.is_file() and notice(p.name)
                       and "node_modules" not in p.relative_to(folder).parts)
        if not paths:
            missing.append({"package": key, "version": metadata.get("version"), "reason": "No supplied notice file found"})
        for path in paths:
            relative = path.relative_to(folder).as_posix()
            destination = "frontend/" + key.removeprefix("node_modules/") + "/" + relative
            copy(destination, path.read_bytes(), f"npm {key}@{metadata.get('version')}: {relative}")
    supplement = OUTPUT / "upstream/manifest.json"
    if supplement.exists():
        upstream = json.loads(supplement.read_text())
        resolved = {e.get("package") for e in upstream["entries"] if e["scope"] == "frontend"}
        missing = [m for m in missing if m["package"].removeprefix("node_modules/") not in resolved]
        for entry in upstream["entries"]:
            content = (OUTPUT / entry["file"]).read_bytes()
            assert hashlib.sha256(content).hexdigest() == entry["sha256"]
            entries.append({**entry, "origin": "Upstream notice: " + entry["source_url"]})
    manifest = {"source_linux_zip_sha256": ZIP_SHA, "entries": entries, "missing_installed_notices": missing,
                "scope": "Supplied notices only; not a complete native/transitive provenance or legal clearance."}
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    public = ROOT / "frontend/public/THIRD_PARTY_NOTICES.txt"
    public.parent.mkdir(parents=True, exist_ok=True)
    with public.open("wb") as output:
        output.write(b"AirWise Schools original code: MIT. Third-party materials retain their own terms.\n")
        output.write((ROOT / "LICENSE").read_bytes())
        for entry in entries:
            if entry["file"].startswith(("frontend/", "upstream/frontend/")):
                output.write(("\n\n--- " + entry["origin"] + " ---\n\n").encode())
                output.write((OUTPUT / entry["file"]).read_bytes())
    print(json.dumps({"copied_notices": len(entries), "missing_installed_notices": missing}))


if __name__ == "__main__":
    collect()
