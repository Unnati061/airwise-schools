"""Optional policy verification using operator/bundled pypdf, not backend dependencies."""
import hashlib
import json
import sys
import argparse
from pathlib import Path
from urllib.request import urlopen

from pypdf import PdfReader


def verify(local=False):
    sys.stdout.reconfigure(encoding="utf-8")
    folder = Path("work/policy-verification")
    folder.mkdir(parents=True, exist_ok=True)
    records = json.loads(Path("backend/app/data/policy_excerpts.json").read_text(encoding="utf-8"))
    for name in ("air2", "air4"):
        url = f"https://ncdc.mohfw.gov.in/uploads/pdf/{name}.pdf"
        path = folder / f"{name}.pdf"
        if local:
            content = path.read_bytes()
        else:
            with urlopen(url, timeout=30) as response:
                content = response.read(20_000_000)
        if not content.startswith(b"%PDF"):
            raise RuntimeError("Not official PDF bytes")
        if not local:
            path.write_bytes(content)
        record = next(r for r in records if r["source_url"] == url)
        if hashlib.sha256(content).hexdigest() != record["document_sha256"]:
            raise RuntimeError("Source bytes changed; manually review before updating curated evidence")
        reader = PdfReader(path)
        print(f"{url}: {len(content)} bytes; SHA256 {hashlib.sha256(content).hexdigest()}; {len(reader.pages)} PDF pages")
        print("Cover:", reader.pages[0].extract_text()[:500])
        page = 25 if name == "air2" else 14
        text = " ".join(reader.pages[page].extract_text().split())
        if record["excerpt"] not in text:
            raise RuntimeError("Curated passage not present on documented PDF page")
        print(f"PASS exact excerpt and hash; PDF page {page + 1}: {record['excerpt']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", action="store_true", help="Reverify already downloaded public PDF bytes without fetching again")
    verify(parser.parse_args().local)
