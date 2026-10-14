#!/usr/bin/env python3
"""Verify that Terraform RDS profiles keep stage more durable than dev."""

from __future__ import annotations

import re
from pathlib import Path


ASSIGNMENT = re.compile(r"^\s*(backup_retention_period|deletion_protection|skip_final_snapshot|final_snapshot_identifier)\s*=\s*(.+?)\s*$", re.MULTILINE)


def environment_values(environment: str) -> dict[str, str]:
    source = Path("terraform/envs") / environment / "main.tf"
    values = dict(ASSIGNMENT.findall(source.read_text(encoding="utf-8")))
    expected_fields = {
        "backup_retention_period",
        "deletion_protection",
        "skip_final_snapshot",
    }
    missing = expected_fields - values.keys()
    if missing:
        raise AssertionError(f"{source}: missing RDS profile values: {', '.join(sorted(missing))}")
    return values


def main() -> None:
    dev = environment_values("dev")
    stage = environment_values("stage")

    assert dev == {
        "backup_retention_period": "0",
        "deletion_protection": "false",
        "skip_final_snapshot": "true",
    }, f"unexpected dev RDS profile: {dev}"
    assert stage["backup_retention_period"] == "7", f"unexpected stage retention: {stage}"
    assert stage["deletion_protection"] == "true", f"unexpected stage protection: {stage}"
    assert stage["skip_final_snapshot"] == "false", f"unexpected stage final snapshot policy: {stage}"
    assert stage["final_snapshot_identifier"] == '"${var.project}-${var.environment}-postgres-final"', (
        f"unexpected stage snapshot identifier: {stage}"
    )

    module = Path("terraform/modules/rds/main.tf").read_text(encoding="utf-8")
    for line in (
        "backup_retention_period   = var.backup_retention_period",
        "deletion_protection       = var.deletion_protection",
        "skip_final_snapshot       = var.skip_final_snapshot",
        "final_snapshot_identifier = var.skip_final_snapshot ? null : var.final_snapshot_identifier",
    ):
        assert line in module, f"RDS module is missing configurable setting: {line}"

    print("validated durable stage and ephemeral dev RDS profiles")


if __name__ == "__main__":
    main()
