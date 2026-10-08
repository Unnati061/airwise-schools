"""Fresh, Docker-free Python 3.12/Linux x86_64 application ZIP."""
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def package():
    stage = ROOT / "work" / "d2-package"
    target = ROOT / "work" / "airwise-app-d2.zip"
    if stage.exists() or target.exists():
        raise RuntimeError("D2 staging/artifact exists; inspect before another build")
    stage.mkdir(parents=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "--platform", "manylinux2014_x86_64",
                    "--platform", "manylinux_2_28_x86_64", "--implementation", "cp", "--python-version", "3.12",
                    "--only-binary=:all:", "--no-compile", "--target", str(stage), "-r", str(ROOT / "backend/requirements.txt")], check=True)
    shutil.copytree(ROOT / "backend", stage / "backend", ignore=shutil.ignore_patterns("__pycache__", "tests", "*.txt"))
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(stage.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                archive.write(path, path.relative_to(stage).as_posix())
    with zipfile.ZipFile(target) as archive:
        total = sum(v.file_size for v in archive.infolist())
        if total > 250 * 1024 * 1024 or archive.testzip():
            raise RuntimeError("ZIP corrupt or above 250 MiB extracted limit")
        for name in archive.namelist():
            if name.endswith((".dll", ".pyd")):
                raise RuntimeError("Windows binary in Linux ZIP")
            if ".so" in Path(name).name:
                header = archive.read(name)[:20]
                if header[:6] != b"\x7fELF\x02\x01" or struct.unpack("<H", header[18:20])[0] != 62:
                    raise RuntimeError("Native file is not ELF64 x86_64")
            if name.endswith(".dist-info/WHEEL"):
                tags = [line[5:] for line in archive.read(name).decode().splitlines() if line.startswith("Tag: ")]
                if not any(tag.endswith("-any") or ("x86_64" in tag and (tag.startswith("cp312-") or "-abi3-" in tag)) for tag in tags):
                    raise RuntimeError("Unexpected Linux/Python wheel tag")
    result = {"archive": str(target), "compressed_bytes": target.stat().st_size, "uncompressed_bytes": total,
              "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "runtime": "python3.12", "architecture": "x86_64"}
    (ROOT / "work/d2-package.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    package()
