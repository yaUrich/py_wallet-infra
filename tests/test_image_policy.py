from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "check_image_policy.py"
FIXTURES = Path(__file__).parent / "fixtures" / "image-policy"
SPEC = importlib.util.spec_from_file_location("check_image_policy", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
POLICY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(POLICY)


class ImagePolicyTests(unittest.TestCase):
    def test_allows_pinned_application_and_infrastructure_images(self) -> None:
        images = (
            "ghcr.io/amysyutin/py_wallet-api:ef68d3a1ed2f49162e57a477731692636a1dd0bd",
            "ghcr.io/amysyutin/py_wallet-front:c17d5d2507284e87fed6adc85cc387ce5d642879",
            "ghcr.io/amysyutin/py_wallet-snapshot-service:1205ed4e18f35ff81062ead944dccc643e4fc214",
            "postgres:16",
            "amazon/aws-cli:2.32.8",
        )

        for image in images:
            with self.subTest(image=image):
                self.assertIsNone(POLICY.validate_image(image))

        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture = FIXTURES / "valid.yaml"
            manifest = Path(temporary_directory) / fixture.name
            manifest.write_text(fixture.read_text())
            self.assertEqual(POLICY.validate_directory(Path(temporary_directory)), [])

    def test_rejects_mutable_or_unapproved_images(self) -> None:
        images = (
            "ghcr.io/amysyutin/py_wallet-api:latest",
            "ghcr.io/amysyutin/py_wallet-api:ef68d3a",
            "ghcr.io/example/py_wallet-api:ef68d3a1ed2f49162e57a477731692636a1dd0bd",
            "postgres:17",
        )

        for image in images:
            with self.subTest(image=image):
                self.assertIsNotNone(POLICY.validate_image(image))

    def test_reports_manifest_location_for_an_invalid_image(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture = FIXTURES / "invalid.yaml"
            manifest = Path(temporary_directory) / fixture.name
            manifest.write_text(fixture.read_text())

            errors = POLICY.validate_directory(Path(temporary_directory))

        self.assertEqual(len(errors), 1)
        self.assertIn("invalid.yaml:8", errors[0])
        self.assertIn("ghcr.io/amysyutin/py_wallet-api:latest", errors[0])


if __name__ == "__main__":
    unittest.main()
