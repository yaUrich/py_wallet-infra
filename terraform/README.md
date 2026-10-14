# Terraform — py_wallet AWS

AWS infrastructure for py_wallet: VPC, EC2, RDS PostgreSQL, and remote state.

## Architecture

```
Internet
   │
   ▼
┌─────────────────────────────────────────┐
│  VPC (dev: 10.20.0.0/16)                │
│                                         │
│  Public subnets (2 AZ)                  │
│    └─ EC2 (SSH from my_ip/32)           │
│                                         │
│  Private subnets (2 AZ)                 │
│    └─ RDS PostgreSQL (SG → EC2 SG only) │
└─────────────────────────────────────────┘

State: a dedicated S3 bucket and DynamoDB lock table per environment.
```

## Layout

| Path | Role |
|------|------|
| `bootstrap/` | S3 + DynamoDB for one environment's remote state (apply once per environment) |
| `modules/network` | VPC, IGW, public/private subnets, route tables |
| `modules/ec2` | EC2 instance |
| `modules/rds` | PostgreSQL + SG-to-SG + random password |
| `envs/dev` | Root module, remote state `envs/dev/...` |
| `envs/stage` | Root module, remote state `envs/stage/...` |

## Prerequisites

- Terraform `>= 1.6` locally; CI uses the pinned Terraform 1.16.3 release
- AWS CLI profiles `pywallet-dev` and `pywallet-stage` (or equivalent named profiles configured locally)
- EC2 key pair in AWS
- `my_ip_cidr` in `terraform.tfvars` (never commit real tfvars)

## Bootstrap remote state

```bash
cd terraform/bootstrap
terraform init
terraform apply
```

The default bootstrap values create the dev backend. To create the isolated
stage backend, use the non-secret example file:

```bash
terraform apply -var-file=stage.tfvars.example
```

Do not create the stage backend by reusing the dev bucket or lock table.

## Dev lifecycle

```bash
cd terraform/envs/dev
cp terraform.tfvars.example terraform.tfvars   # set your my_ip_cidr
terraform init
terraform plan
terraform apply
terraform destroy
```

## Stage

```bash
cd terraform/envs/stage
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
```

Use a different VPC CIDR than `dev` if both environments run at the same time.
Stage uses `pywallet-stage-tfstate`, `pywallet-stage-tf-lock`, and the
`pywallet-stage` AWS profile. Follow the
[state-backend migration runbook](docs/stage-backend-migration.md) before
switching an existing stage state to the new backend.

## CI

GitHub Actions (`.github/workflows/terraform-ci.yml`):

- `terraform fmt -check`
- `terraform init -backend=false` + `validate` (matrix: `dev`, `stage`)
- `scripts/check-terraform-backends.py` rejects shared buckets, keys, lock
  tables, profiles, and environment defaults
- `tflint`
- `checkov` (`soft_fail: true`)

## Local tooling

```bash
pre-commit install
pre-commit run --all-files
```

Requires `tflint` on `PATH` for the local tflint hook.

## Security notes

- SSH only from `my_ip_cidr` `/32`
- RDS: `publicly_accessible = false`, access via SG → SG
- State encrypted in S3; secrets in state are not masked by `sensitive` alone
- Dev RDS remains ephemeral (`backup_retention_period = 0`, `skip_final_snapshot = true`, `deletion_protection = false`). Stage retains automated backups for seven days, blocks deletion, and requires a final snapshot if protection is deliberately disabled.
