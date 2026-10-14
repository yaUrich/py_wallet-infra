#!/usr/bin/env python3
"""Ensure each Terraform environment has a dedicated remote-state backend."""

from __future__ import annotations

import re
from pathlib import Path


ENVIRONMENTS = ("dev", "stage")
BACKEND_FIELD = re.compile(r'^\s*(bucket|key|dynamodb_table|profile)\s*=\s*"([^"]+)"\s*$', re.MULTILINE)
VARIABLE_DEFAULT = re.compile(
    r'variable\s+"(?P<name>aws_profile|environment)"\s*\{.*?^\s*default\s*=\s*"(?P<value>[^"]+)"\s*$',
    re.MULTILINE | re.DOTALL,
)


def backend_values(environment: str) -> dict[str, str]:
    source = Path("terraform/envs") / environment / "backend.tf"
    values = dict(BACKEND_FIELD.findall(source.read_text(encoding="utf-8")))
    required = {"bucket", "key", "dynamodb_table", "profile"}
    missing = required - values.keys()
    if missing:
        raise AssertionError(f"{source}: missing backend fields: {', '.join(sorted(missing))}")
    return values


def variable_defaults(environment: str) -> dict[str, str]:
    source = Path("terraform/envs") / environment / "variables.tf"
    return {match.group("name"): match.group("value") for match in VARIABLE_DEFAULT.finditer(source.read_text(encoding="utf-8"))}


def main() -> None:
    seen: dict[str, str] = {}
    for environment in ENVIRONMENTS:
        values = backend_values(environment)
        defaults = variable_defaults(environment)

        expected = {
            "bucket": f"pywallet-{environment}-tfstate",
            "key": f"envs/{environment}/terraform.tfstate",
            "dynamodb_table": f"pywallet-{environment}-tf-lock",
            "profile": f"pywallet-{environment}",
        }
        assert values == expected, f"{environment}: expected {expected}, got {values}"
        assert defaults.get("environment") == environment, f"{environment}: environment default must match folder"
        assert defaults.get("aws_profile") == values["profile"], f"{environment}: provider and backend profiles must match"

        for field in ("bucket", "key", "dynamodb_table"):
            value = values[field]
            assert value not in seen, f"{environment}: {field} duplicates {seen[value]} ({value})"
            seen[value] = f"{environment}.{field}"

    print("validated dedicated Terraform remote-state backends for dev and stage")


if __name__ == "__main__":
    main()
