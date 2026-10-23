"""Package Background without changing an installed browser or signing identity."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent.parent
STORE_ID = "mfcallgpgnojmoaffommnnbfojdghfck"


def verified_key(path):
    if path is None:
        raise ValueError("Replacement requires the existing store item's public key file")
    value = "".join(path.read_text().split())
    try:
        data = base64.b64decode(value, validate=True)
    except ValueError as error:
        raise ValueError("Expected base64 DER public key") from error
    if not data or len(data) > 8192:
        raise ValueError("Invalid public key size")
    result = subprocess.run(["openssl", "pkey", "-pubin", "-inform", "DER", "-noout"],
                            input=data, capture_output=True)
    if result.returncode:
        raise ValueError("Expected public key, never a private key or certificate")
    actual = "".join(chr(ord("a") + int(c, 16)) for c in hashlib.sha256(data).hexdigest()[:32])
    if actual != STORE_ID:
        raise ValueError("Public key does not match the verified existing store item")
    return value


def build(mode="production", public_key=None):
    if mode not in {"production", "dev", "replacement"}:
        raise ValueError("Unknown build mode")
    if public_key is not None and mode != "replacement":
        raise ValueError("Public key input is only valid for explicit replacement mode")
    key = verified_key(public_key) if mode == "replacement" else None
    manifest = json.loads((ROOT / "manifest.json").read_text())
    if mode == "dev":
        manifest["name"] += " Dev"
        manifest["version"] += ".1"
        manifest["version_name"] = manifest["version"] + " Development"
    if key:
        manifest["key"] = key
        manifest["version_name"] = manifest["version"] + " Replacement candidate"
    output = ROOT / "dist" / mode
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for asset in manifest["icons"].values():
        target = output / asset
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(ROOT / asset, target)
    archive = ROOT / "dist" / f"background-{mode}-{manifest['version']}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for file in sorted(output.rglob("*")):
            if file.is_file():
                info = zipfile.ZipInfo(file.relative_to(output).as_posix(), (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                bundle.writestr(info, file.read_bytes())
    return {"mode": mode, "version": manifest["version"], "path": str(archive),
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(), "unpacked": str(output)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["production", "dev", "replacement"], default="production")
    parser.add_argument("--public-key-file", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.mode, args.public_key_file), indent=2))
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + "\n")
