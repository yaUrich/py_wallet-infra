#!/usr/bin/env python3
"""Reject image references that are outside the GitOps image policy."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


APPLICATION_IMAGES = {
    "ghcr.io/amysyutin/py_wallet-api",
    "ghcr.io/amysyutin/py_wallet-front",
    "ghcr.io/amysyutin/py_wallet-snapshot-service",
}
INFRASTRUCTURE_IMAGES = {
    "postgres:16",
    "amazon/aws-cli:2.32.8",
}
SHA_TAG = re.compile(r"[0-9a-f]{40}")
IMAGE_LINE = re.compile(r"^\s*image:\s*([^\s#]+)")


def validate_image(image: str) -> str | None:
    """Return a policy error for *image*, or ``None`` when it is allowed."""
    if image in INFRASTRUCTURE_IMAGES:
        return None

    repository, separator, tag = image.rpartition(":")
    if not separator or repository not in APPLICATION_IMAGES:
        return (
            "image is not an approved application image or pinned infrastructure "
            f"image: {image}"
        )
    if not SHA_TAG.fullmatch(tag):
        return f"application image must use a full 40-character lowercase Git SHA: {image}"
    return None


def validate_directory(rendered_directory: Path) -> list[str]:
    errors: list[str] = []
    for manifest in sorted(rendered_directory.rglob("*.yaml")):
        for line_number, line in enumerate(manifest.read_text().splitlines(), start=1):
            match = IMAGE_LINE.match(line)
            if match is None:
                continue
            error = validate_image(match.group(1))
            if error is not None:
                errors.append(f"{manifest}:{line_number}: {error}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate image references in rendered Kubernetes manifests."
    )
    parser.add_argument("rendered_directory", type=Path)
    arguments = parser.parse_args()

    if not arguments.rendered_directory.is_dir():
        print(
            f"rendered directory does not exist: {arguments.rendered_directory}",
            file=sys.stderr,
        )
        return 1

    errors = validate_directory(arguments.rendered_directory)
    if errors:
        print("GitOps image policy failed:", file=sys.stderr)
        print("\n".join(errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
