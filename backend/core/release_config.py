"""Read release HATS configurations from the datasets directory."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

import yaml
from django.conf import settings


RELEASE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class ReleaseHatsConfigError(Exception):
    """Base error raised while resolving a release HATS configuration."""

    status_code = 500


class InvalidReleaseName(ReleaseHatsConfigError):
    """The requested release name cannot safely identify a dataset directory."""

    status_code = 400


class ReleaseHatsConfigNotFound(ReleaseHatsConfigError):
    """No HATS configuration exists for the requested release."""

    status_code = 404


class ReleaseHatsConfigTooLarge(ReleaseHatsConfigError):
    """The HATS configuration exceeds the configured size limit."""

    status_code = 413


class InvalidReleaseHatsConfig(ReleaseHatsConfigError):
    """The HATS configuration exists but is malformed or unsafe."""

    status_code = 422


class ReleaseHatsConfigRegistry:
    """Resolve and validate HATS configurations stored alongside datasets."""

    def __init__(self, datasets_dir=None, filename=None, max_size=None):
        if datasets_dir is None:
            datasets_dir = settings.DATASETS_DIR
        if filename is None:
            filename = settings.HATS_CONFIG_FILENAME
        if max_size is None:
            max_size = settings.HATS_CONFIG_MAX_SIZE

        if (
            not isinstance(filename, str)
            or not filename
            or filename in {".", ".."}
            or Path(filename).name != filename
        ):
            raise ValueError("HATS_CONFIG_FILENAME must be a file name, not a path")
        if (
            isinstance(max_size, bool)
            or not isinstance(max_size, int)
            or max_size <= 0
        ):
            raise ValueError("HATS_CONFIG_MAX_SIZE must be greater than zero")

        self.datasets_dir = Path(datasets_dir).expanduser().resolve()
        self.filename = filename
        self.max_size = max_size

    def get(self, release):
        """Return the validated HATS configuration for one release."""
        self._validate_release_name(release)
        config_path = self._config_path(release)

        if not config_path.is_file():
            raise ReleaseHatsConfigNotFound(
                f"HATS configuration not found for release '{release}'."
            )

        try:
            stat = config_path.stat()
        except OSError as exc:
            raise InvalidReleaseHatsConfig(
                f"Could not inspect HATS configuration for release '{release}'."
            ) from exc

        if stat.st_size > self.max_size:
            raise ReleaseHatsConfigTooLarge(
                f"HATS configuration for release '{release}' exceeds the "
                f"{self.max_size}-byte limit."
            )

        try:
            with config_path.open("rb") as config_file:
                raw_config = config_file.read(self.max_size + 1)
        except OSError as exc:
            raise InvalidReleaseHatsConfig(
                f"Could not read HATS configuration for release '{release}'."
            ) from exc

        if len(raw_config) > self.max_size:
            raise ReleaseHatsConfigTooLarge(
                f"HATS configuration for release '{release}' exceeds the "
                f"{self.max_size}-byte limit."
            )

        try:
            document = yaml.safe_load(raw_config)
        except (UnicodeError, yaml.YAMLError) as exc:
            raise InvalidReleaseHatsConfig(
                f"Could not parse HATS configuration for release '{release}'."
            ) from exc

        document = self._validate_document(release, document)

        return {
            "release": release,
            "last_modified": datetime.fromtimestamp(
                stat.st_mtime,
                tz=timezone.utc,
            ),
            "config": document,
        }

    def list(self):
        """Return metadata for every direct child with a HATS manifest."""
        if not self.datasets_dir.is_dir():
            return []

        try:
            release_dirs = sorted(
                path
                for path in self.datasets_dir.iterdir()
                if path.is_dir() and (path / self.filename).is_file()
            )
        except OSError as exc:
            raise InvalidReleaseHatsConfig(
                "Could not list release HATS configurations."
            ) from exc

        results = []
        for release_dir in release_dirs:
            result = self.get(release_dir.name)
            results.append(
                {
                    "release": result["release"],
                    "last_modified": result["last_modified"],
                }
            )
        return results

    def _config_path(self, release):
        config_path = (self.datasets_dir / release / self.filename).resolve()
        try:
            config_path.relative_to(self.datasets_dir)
        except ValueError as exc:
            raise InvalidReleaseHatsConfig(
                f"Unsafe HATS configuration path for release '{release}'."
            ) from exc
        return config_path

    @staticmethod
    def _validate_release_name(release):
        if (
            not isinstance(release, str)
            or release in {".", ".."}
            or not RELEASE_NAME_PATTERN.fullmatch(release)
        ):
            raise InvalidReleaseName("Invalid release identifier.")

    @staticmethod
    def _validate_document(release, document):
        if not isinstance(document, Mapping):
            raise InvalidReleaseHatsConfig(
                f"HATS configuration for release '{release}' must be an object."
            )

        if not document:
            raise InvalidReleaseHatsConfig(
                f"HATS configuration for release '{release}' must not be empty."
            )

        try:
            json.dumps(document, allow_nan=False)
        except (TypeError, ValueError, RecursionError) as exc:
            raise InvalidReleaseHatsConfig(
                f"HATS configuration for release '{release}' must contain only "
                "JSON-compatible values."
            ) from exc

        return document
