"""Read-only reachable tree/blob audit; locations only, no secret/cache contents."""
import json
import re
import subprocess


def git(*args):
    return subprocess.check_output(["git", *args])


def unsafe_path(path):
    return bool(re.search(r"(^|/)(work|node_modules|\.venv|__pycache__|\.pytest_cache|\.aws|\.vite)/|(^|/)\.env($|\.)|\.(zip|whl|tgz|tar|gz|so(?:\.\d+)*|dll|exe|node|pyc|pem|pfx|pyd|dylib|a|o|lib|wasm)$", path, re.I)) and not path.endswith(".env.example")


def audit():
    commits = git("rev-list", "--all").decode().splitlines()
    paths, blobs = set(), {}
    for commit in commits:
        for entry in git("ls-tree", "-r", "-z", commit).split(b"\0"):
            if not entry:
                continue
            metadata, path = entry.split(b"\t", 1)
            _, kind, oid = metadata.split()
            path = path.decode()
            paths.add(path)
            if kind == b"blob":
                blobs.setdefault(oid.decode(), set()).add(path)
    current = [p.decode() for p in git("ls-files", "-z").split(b"\0") if p]
    binary = []
    process = subprocess.Popen(["git", "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    for oid, names in blobs.items():
        process.stdin.write((oid + "\n").encode()); process.stdin.flush()
        header = process.stdout.readline().split()
        content = process.stdout.read(int(header[2])); process.stdout.read(1)
        pe = len(content) > 64 and content[:2] == b"MZ" and content[int.from_bytes(content[60:64], "little"):][:4] == b"PE\x00\x00"
        kind = "ELF" if content.startswith(b"\x7fELF") else "PE" if pe else "ZIP" if content.startswith(b"PK\x03\x04") else "GZIP" if content.startswith(b"\x1f\x8b") else None
        if kind:
            binary.append({"blob": oid, "paths": sorted(names), "kind": kind})
    process.stdin.close(); process.wait(timeout=10)
    candidates = ["work/airwise-app-features.zip", "frontend/node_modules/react/package.json",
                  ".venv/Lib/site-packages/_awscrt.pyd", "backend/app/__pycache__/example.pyc",
                  ".pytest_cache/example", "frontend/.env.d2", "frontend/dist/assets/example.js"]
    ignored = subprocess.run(["git", "check-ignore", *candidates], capture_output=True, text=True)
    result = dict(commits=len(commits), historical_unique_paths=len(paths), reachable_blobs=len(blobs),
                  tracked_paths=len(current), current_prohibited_paths=sorted(p for p in current if unsafe_path(p)),
                  historical_prohibited_paths=sorted(p for p in paths if unsafe_path(p)), archive_native_magic_findings=binary,
                  ignore_probe_paths=ignored.stdout.splitlines(),
                  limitations="Reachable refs only, not reflogs/unreachable/remote; magic/path scan is not an arbitrary binary or comprehensive secret detector.")
    print(json.dumps(result))
    return result


if __name__ == "__main__":
    audit()
