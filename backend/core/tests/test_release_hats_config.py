import tempfile
from pathlib import Path

import yaml
from django.test import SimpleTestCase, override_settings
from django.urls import resolve
from rest_framework.test import APIRequestFactory

from core.release_config import (
    InvalidReleaseHatsConfig,
    InvalidReleaseName,
    ReleaseHatsConfigNotFound,
    ReleaseHatsConfigRegistry,
    ReleaseHatsConfigTooLarge,
)
from core.views import ReleaseHatsConfigView


class ReleaseHatsConfigTestMixin:
    def setUp(self):
        super().setUp()
        self.tempdir = tempfile.TemporaryDirectory()
        self.datasets_dir = Path(self.tempdir.name)
        self.settings_override = override_settings(
            DATASETS_DIR=str(self.datasets_dir),
            HATS_CONFIG_FILENAME="hats_config.yaml",
            HATS_CONFIG_MAX_SIZE=1024 * 1024,
        )
        self.settings_override.enable()

    def tearDown(self):
        self.settings_override.disable()
        self.tempdir.cleanup()
        super().tearDown()

    def write_config(self, release="dp1", document=None, raw=None):
        release_dir = self.datasets_dir / release
        release_dir.mkdir(parents=True, exist_ok=True)
        config_path = release_dir / "hats_config.yaml"
        if raw is None:
            if document is None:
                document = {
                    "input": {
                        "which_release": release,
                        "compute_magnitude": True,
                    },
                    "dust": {"use_dustmap": "sfd"},
                    "cluster": {"executor": "local"},
                }
            raw = yaml.safe_dump(document, sort_keys=False)
        config_path.write_text(raw, encoding="utf-8")
        return config_path


class ReleaseHatsConfigRegistryTestCase(
    ReleaseHatsConfigTestMixin,
    SimpleTestCase,
):
    def test_get_returns_validated_document_and_file_metadata(self):
        self.write_config()

        result = ReleaseHatsConfigRegistry().get("dp1")

        self.assertEqual("dp1", result["release"])
        self.assertEqual("dp1", result["config"]["input"]["which_release"])
        self.assertEqual("sfd", result["config"]["dust"]["use_dustmap"])
        self.assertIsNotNone(result["last_modified"].tzinfo)

    def test_list_returns_sorted_summaries_and_ignores_directories_without_config(self):
        self.write_config("dr2")
        self.write_config("dp1")
        (self.datasets_dir / "no-config").mkdir()

        results = ReleaseHatsConfigRegistry().list()

        self.assertEqual(["dp1", "dr2"], [item["release"] for item in results])
        self.assertNotIn("config", results[0])
        self.assertNotIn("checksum", results[0])
        self.assertNotIn("schema_version", results[0])

    def test_list_returns_empty_when_datasets_directory_does_not_exist(self):
        registry = ReleaseHatsConfigRegistry(
            datasets_dir=self.datasets_dir / "missing",
        )

        self.assertEqual([], registry.list())

    def test_get_rejects_invalid_release_name(self):
        with self.assertRaises(InvalidReleaseName):
            ReleaseHatsConfigRegistry().get("../dp1")

    def test_get_rejects_symlink_outside_datasets_directory(self):
        with tempfile.TemporaryDirectory() as outside_tempdir:
            outside_release = Path(outside_tempdir) / "external"
            outside_release.mkdir()
            (outside_release / "hats_config.yaml").write_text(
                yaml.safe_dump({"input": {"which_release": "linked"}}),
                encoding="utf-8",
            )
            (self.datasets_dir / "linked").symlink_to(
                outside_release,
                target_is_directory=True,
            )

            with self.assertRaises(InvalidReleaseHatsConfig):
                ReleaseHatsConfigRegistry().get("linked")

    def test_get_returns_not_found_for_missing_config(self):
        with self.assertRaises(ReleaseHatsConfigNotFound):
            ReleaseHatsConfigRegistry().get("dp1")

    def test_get_rejects_config_above_size_limit(self):
        self.write_config(raw="input:\n  value: long\n")

        with self.assertRaises(ReleaseHatsConfigTooLarge):
            ReleaseHatsConfigRegistry(max_size=10).get("dp1")

    def test_registry_rejects_non_positive_size_limit(self):
        for max_size in (0, -1, True, "1024"):
            with self.subTest(max_size=max_size):
                with self.assertRaisesRegex(ValueError, "greater than zero"):
                    ReleaseHatsConfigRegistry(max_size=max_size)

    def test_registry_rejects_unsafe_filename(self):
        for filename in ("", ".", "..", "nested/hats_config.yaml", 123):
            with self.subTest(filename=filename):
                with self.assertRaisesRegex(ValueError, "must be a file name"):
                    ReleaseHatsConfigRegistry(filename=filename)

    def test_get_rejects_malformed_yaml(self):
        self.write_config(raw="config: [unterminated")

        with self.assertRaises(InvalidReleaseHatsConfig):
            ReleaseHatsConfigRegistry().get("dp1")

    def test_get_rejects_non_object_yaml(self):
        self.write_config(raw="- one\n- two\n")

        with self.assertRaisesRegex(InvalidReleaseHatsConfig, "must be an object"):
            ReleaseHatsConfigRegistry().get("dp1")

    def test_get_rejects_values_that_cannot_be_returned_as_json(self):
        self.write_config(document={"selected": {"sfd", "planck"}})

        with self.assertRaisesRegex(InvalidReleaseHatsConfig, "JSON-compatible"):
            ReleaseHatsConfigRegistry().get("dp1")

    def test_get_rejects_empty_config(self):
        self.write_config(document={})

        with self.assertRaisesRegex(InvalidReleaseHatsConfig, "must not be empty"):
            ReleaseHatsConfigRegistry().get("dp1")


class ReleaseHatsConfigViewTestCase(
    ReleaseHatsConfigTestMixin,
    SimpleTestCase,
):
    def setUp(self):
        super().setUp()
        self.factory = APIRequestFactory()
        self.view = ReleaseHatsConfigView.as_view(permission_classes=[])

    def test_url_resolves_to_release_hats_config_view(self):
        match = resolve("/api/releases/hats_config/")

        self.assertEqual("release-hats-config", match.view_name)

    def test_get_returns_one_release_config(self):
        self.write_config("dp1")
        request = self.factory.get(
            "/api/releases/hats_config/",
            {"release": "dp1"},
        )

        response = self.view(request)

        self.assertEqual(200, response.status_code)
        self.assertEqual("dp1", response.data["release"])
        self.assertIn("config", response.data)
        self.assertNotIn("checksum", response.data)
        self.assertNotIn("schema_version", response.data)
        self.assertNotIn("capabilities", response.data)

    def test_get_without_release_returns_summaries(self):
        self.write_config("dp1")
        request = self.factory.get("/api/releases/hats_config/")

        response = self.view(request)

        self.assertEqual(200, response.status_code)
        self.assertEqual("dp1", response.data["results"][0]["release"])
        self.assertNotIn("config", response.data["results"][0])

    def test_get_returns_domain_error_status(self):
        request = self.factory.get(
            "/api/releases/hats_config/",
            {"release": "missing"},
        )

        response = self.view(request)

        self.assertEqual(404, response.status_code)
        self.assertIn("error", response.data)

    def test_get_rejects_blank_release_query(self):
        request = self.factory.get(
            "/api/releases/hats_config/",
            {"release": ""},
        )

        response = self.view(request)

        self.assertEqual(400, response.status_code)

    def test_endpoint_requires_authentication(self):
        request = self.factory.get("/api/releases/hats_config/")

        response = ReleaseHatsConfigView.as_view()(request)

        self.assertIn(response.status_code, {401, 403})
