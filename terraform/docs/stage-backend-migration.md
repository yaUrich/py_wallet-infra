# Migrate stage Terraform state to its dedicated backend

`stage` uses a backend separate from `dev`:

| Environment | S3 bucket | State key | DynamoDB lock table | AWS profile |
| --- | --- | --- | --- | --- |
| `dev` | `pywallet-dev-tfstate` | `envs/dev/terraform.tfstate` | `pywallet-dev-tf-lock` | `pywallet-dev` |
| `stage` | `pywallet-stage-tfstate` | `envs/stage/terraform.tfstate` | `pywallet-stage-tf-lock` | `pywallet-stage` |

This migration changes only Terraform's state storage. It must be performed by
an operator with access to both backends. Do not commit state files, AWS
credentials, or generated Terraform configuration.

## Before starting

1. Confirm no other `terraform plan` or `terraform apply` is running for
   `stage`.
2. Ensure the local AWS configuration contains the `pywallet-stage` profile.
3. Create the stage backend once from `terraform/bootstrap`:

   ```bash
   terraform init
   terraform apply -var-file=stage.tfvars.example
   ```

4. Record the current stage resource inventory and take an encrypted,
   access-controlled copy of `terraform state pull` outside the repository.

## Migrate

From `terraform/envs/stage`, run the following interactively. Terraform reads
the previously configured backend, detects the new backend in `backend.tf`,
and asks whether to copy the state.

```bash
terraform init -migrate-state
terraform plan
```

Accept the copy only after confirming the destination bucket, key and lock
table match the `stage` row above. A successful plan must show no unexpected
resource replacement or destruction. If it does, stop and investigate before
any apply.

## Verify and retire access

1. Run `terraform state list` using the new stage backend and compare it with
   the protected pre-migration inventory.
2. Run `terraform plan`; it must be empty or contain only intentional changes.
3. Keep the old state object until the migration and recovery procedure have
   been reviewed. Do not delete state objects as part of this runbook.
