"""Reconcile a subsequently supplied notice against unchanged installed code bytes."""
import hashlib
import json
from urllib.request import urlopen

from .upstream_notices import ROOT, OUTPUT, download

REF = "a34c9a5b7a317b6039b2b3cf9d024ee8e418d281"


def complete():
    manifest = OUTPUT / "manifest.json"
    record = json.loads(manifest.read_text())
    if any(e.get("package") == "uri-js-replace" for e in record["entries"]):
        raise RuntimeError("Already reconciled; do not repeat")
    tree_url = f"https://api.github.com/repos/andreinwald/uri-js-replace/git/trees/{REF}?recursive=1"
    tree = json.loads(download(tree_url))
    assert not tree.get("truncated")
    hashes = {e["path"]: e["sha"] for e in tree["tree"] if e["type"] == "blob"}
    matches = []
    folder = ROOT / "frontend/node_modules/uri-js-replace"
    for file in sorted((folder / "dist").rglob("*")):
        if not file.is_file():
            continue
        content = file.read_bytes()
        oid = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
        path = file.relative_to(folder).as_posix()
        assert hashes.get(path) == oid, "Installed URI code differs from notice-bearing upstream revision"
        matches.append(path)
    assert matches
    url = f"https://raw.githubusercontent.com/andreinwald/uri-js-replace/{REF}/LICENSE"
    content = download(url)
    assert b"MIT No Attribution" in content
    path = OUTPUT / "frontend/uri-js-replace/LICENSE"
    path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(content)
    record["entries"].append(dict(file="upstream/frontend/uri-js-replace/LICENSE", source_url=url,
        scope="frontend", package="uri-js-replace", version="1.0.1", git_ref=REF,
        ref_basis="Subsequently supplied MIT-0 notice; all installed dist files byte-identical to notice-bearing revision",
        verified_dist_files=matches, tree_url=tree_url, bytes=len(content), sha256=hashlib.sha256(content).hexdigest()))
    record["resolved_failures"] = record.pop("failures")
    record["failures"] = []
    manifest.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(dict(package="uri-js-replace", supplied_notice="MIT-0", matching_dist_files=len(matches), git_ref=REF)))


if __name__ == "__main__":
    complete()
