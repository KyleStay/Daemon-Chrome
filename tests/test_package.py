import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
import zipfile

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("package", ROOT / "scripts/package.py")
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


class PackageContract(unittest.TestCase):
    def test_production_and_dev_retain_only_background_permission_and_assets(self):
        for mode in ["production", "dev"]:
            result = package.build(mode)
            data = Path(result["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), result["sha256"])
            self.assertEqual(result, package.build(mode), "Packaging should be reproducible")
            with zipfile.ZipFile(result["path"]) as archive:
                manifest = json.loads(archive.read("manifest.json"))
                self.assertEqual(manifest["permissions"], ["background"])
                self.assertNotIn("background", manifest, "This product has no runtime worker")
                self.assertNotIn("key", manifest)
                self.assertEqual(set(archive.namelist()), {"manifest.json", *manifest["icons"].values()})
                self.assertIsNone(archive.testzip())
                for asset, size in manifest["icons"].items():
                    data = archive.read(size)
                    self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                    self.assertEqual(int.from_bytes(data[16:20], "big"), int(asset))
                    self.assertEqual(int.from_bytes(data[20:24], "big"), int(asset))

    def test_replacement_requires_verified_existing_public_key_without_output(self):
        output = ROOT / "dist/replacement/manifest.json"
        previous = output.read_bytes() if output.exists() else None
        with self.assertRaisesRegex(ValueError, "requires"):
            package.build("replacement")
        self.assertEqual(output.read_bytes() if output.exists() else None, previous)

    def test_separate_build_cannot_accidentally_use_production_identity(self):
        with self.assertRaisesRegex(ValueError, "only valid"):
            package.build("dev", Path("unused"))

    def test_downloaded_production_public_identity(self):
        key = ROOT / "evidence/production-public-key.txt"
        if not key.exists():
            self.skipTest("Published public key evidence not present")
        result = package.build("replacement", key)
        with zipfile.ZipFile(result["path"]) as archive:
            manifest = json.loads(archive.read("manifest.json"))
            data = __import__("base64").b64decode(manifest["key"])
            identity = "".join(chr(97 + int(c, 16)) for c in hashlib.sha256(data).hexdigest()[:32])
            self.assertEqual(identity, package.STORE_ID)
            self.assertEqual(manifest["permissions"], ["background"])


if __name__ == "__main__":
    unittest.main()
