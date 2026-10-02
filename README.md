# py_wallet-infra

GitOps repository for the **py_wallet** project: Kubernetes manifests and Argo CD Applications (app-of-apps), with pull-based deployments.

## Production Readiness Status

| Area | Status | Current state | Next step |
|---|---|---|---|
| GitOps | Done | Argo CD app-of-apps, pull-based deploy | AppProject hardening |
| CI/CD | Done | GHCR image by SHA, validated infra bump PR | Image signing / SBOM |
| Kubernetes runtime | Done | Probes, resources, API/frontend PDB, singleton snapshot policy | HPA after a load baseline |
| Database migrations | Done | Argo CD PreSync Alembic Job | Expand/contract migration policy |
| TLS | Done | cert-manager + Let's Encrypt | Certificate expiry alert |
| Secrets | Done | SealedSecrets in git (`postgres-secret`, `py-wallet-secrets`) | Backup controller master key offline |
| Monitoring | Done | ServiceMonitor, dashboard and runtime alerts | Configure notification delivery and validate SLO targets |
| Security hardening | Partial | NetworkPolicy and non-root workload hardening for API and snapshot jobs | Harden frontend and Postgres images |
| Backup/restore | Ready for configuration | Suspended encrypted object-storage backup CronJob + restore runbook | Configure destination secret and complete a restore rehearsal |
| AWS / Terraform | Done | VPC + EC2 + RDS modules, remote state, CI | See [`terraform/README.md`](terraform/README.md) |

See [`docs/releases/v0.1.md`](docs/releases/v0.1.md) for the platform release summary.
See [`docs/versioning.md`](docs/versioning.md) for component SemVer and the
product release procedure. The current product release candidate is described
by [`releases/v0.2.0.yaml`](releases/v0.2.0.yaml).
See [`docs/telegram-mini-app.md`](docs/telegram-mini-app.md) for Telegram Mini
App, bot token, and daily balance scheduler operations.
See [`docs/workload-security.md`](docs/workload-security.md) for workload
isolation controls, allowed traffic and the cluster verification procedure.
See [`docs/workload-availability.md`](docs/workload-availability.md) for the
disruption budgets, replica policy and the conditions for introducing HPA.
See [`docs/alerting.md`](docs/alerting.md) for the runtime alert thresholds,
triage steps and SLO validation boundary.
See [`docs/postgres-backup-restore.md`](docs/postgres-backup-restore.md) for
backup activation, restore rehearsal and recovery limits.

## Pull request validation

Same-repository pull requests are validated before auto-merge is enabled. The
workflow renders every Kustomize root with pinned Kustomize, validates built-in
Kubernetes resources and repository CRDs with pinned Kubeconform/catalog
versions, rejects plaintext Kubernetes `Secret` resources, and enforces the
GitOps image policy. Application images may only come from the three approved
`ghcr.io/amysyutin/py_wallet-*` repositories and must use a full 40-character
lowercase Git SHA. The only non-application images are the explicitly pinned
`postgres:16` and `amazon/aws-cli:2.32.8` images. Adding an image requires an
intentional policy and test update in the same pull request.

For the local render and policy checks, install Kustomize and run:

```bash
rendered_dir="$(mktemp -d)"
scripts/render-manifests.sh "${rendered_dir}"
scripts/check-manifest-policy.sh "${rendered_dir}"
python3 -m unittest tests/test_image_policy.py
```

Kubeconform runs in CI because schema validation downloads the pinned schema
set. A failing validation job prevents the auto-merge job from running.

## Goals

Move away from push deploys from CI (`kubectl` + kubeconfig) to GitOps:

| Layer | Responsibility |
|-------|----------------|
| **app-repo** | Tests → Docker build → push image to GHCR |
| **deploybot / CI bot** | Bump image tag in this repo only (no cluster access) |
| **Argo CD** | Sync desired state from git into the cluster |
| **PreSync hook** | Run `alembic upgrade head` before rolling out the Deployment |

## Deploy flow

```mermaid
flowchart TB
  subgraph appRepo["1. Application CI"]
    direction TB
    pushMain["Push to main (app-repo)"] --> ciTest["CI: lint + tests"]
    ciTest --> ciBuild["CI: docker build"]
    ciBuild --> ciPush["CI: push image to GHCR :SHA"]
  end

  subgraph infraRepo["2. Infra repo update"]
    direction TB
    updateInfra["deploybot: bump newTag on deploy branch"] --> validateInfra["PR: render + schema + policy validation"]
    validateInfra --> infraCommit["Auto-merge to py_wallet-infra main"]
  end

  subgraph argoCd["3. Argo CD sync"]
    direction TB
    argoDetect["Git drift detected"] --> argoSync["Sync desired state"]
  end

  subgraph cluster["4. Cluster rollout"]
    direction TB
    preSync["PreSync: migrate Job (same SHA)"] --> deploy["Sync: Deployment (same SHA)"]
    deploy --> rollout["RollingUpdate + readinessProbe"]
    rollout --> healthy["Synced / Healthy"]
  end

  ciPush --> updateInfra
  infraCommit --> argoDetect
  argoSync --> preSync
```

## Repository layout

```
py_wallet-infra/
├── bootstrap/
│   └── root-app.yaml          # Root Argo CD Application (apply once)
├── apps/
│   ├── cluster.yaml           # Argo Application → manifests/cluster
│   ├── postgres.yaml          # Argo Application → manifests/postgres
│   └── py-wallet.yaml         # Argo Application → manifests/app
└── manifests/
    ├── cluster/               # Namespace, cert-manager ClusterIssuers, …
    ├── postgres/              # Postgres StatefulSet + SealedSecret
    └── app/                   # App Deployment, Ingress, migrate Job, SealedSecret, …
```

## Automated image bumps

Application build workflows create a unique `deploy/<service>/<sha>-<attempt>`
branch in this repository and open a pull request instead of pushing directly to
`main`. The pull request is rendered and validated by the same checks as every
other infrastructure change, then auto-merged. The auto-merge workflow applies
only to same-repository branches prefixed `deploy/`; infrastructure change PRs
always wait for an explicit maintainer merge after validation. A separate
workflow deletes deploy branches that no longer belong to an open pull request.
It runs when a pull request closes, can be started manually, and periodically
reconciles events suppressed by GitHub's `GITHUB_TOKEN` recursion protection.
Newer builds close older open deploy PRs for the same service, while a
main-branch workflow rebases unrelated open deploy PRs after each merge so
concurrent service releases do not block each other.

The deploybot token must be able to push branches and create pull requests in
this repository. It must not bypass branch protection or push directly to
`main`.

## Image versioning

The single source of truth for the app image tag is [`manifests/app/kustomization.yaml`](manifests/app/kustomization.yaml):

```yaml
images:
  - name: ghcr.io/amysyutin/py_wallet
    newName: ghcr.io/amysyutin/py_wallet-api
    newTag: <SHA>   # updated by deploybot after each successful build
```

Both the **Deployment** and the **PreSync migrate Job** use the same image reference so migrations and rollout always run the same build.

## Argo CD bootstrap

1. Install Argo CD in the cluster (outside this repo; see your k8sops/bootstrap tooling).
2. Apply the root Application once:

   ```bash
   kubectl apply -f bootstrap/root-app.yaml
   ```

3. Argo CD creates child Applications from `apps/` and syncs `manifests/*` automatically.

Child Applications target the in-cluster API server:

```yaml
destination:
  server: https://kubernetes.default.svc
```

## Secrets (SealedSecrets)

Sensitive values live in git as **encrypted** `SealedSecret` resources; the Bitnami controller in the cluster decrypts them into ordinary `Secret` objects at sync time.

| Secret | Namespace | Keys |
|--------|-----------|------|
| `postgres-secret` | `py-wallet-data` | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` |
| `py-wallet-secrets` | `py-wallet-dev` | `DATABASE_URL`, `JWT_SECRET` |
| `telegram-bot-secret` | `py-wallet-dev` | `TELEGRAM_BOT_TOKEN` |

Manifests: [`manifests/postgres/sealed-postgres-secret.yaml`](manifests/postgres/sealed-postgres-secret.yaml), [`manifests/app/sealed-py-wallet-secrets.yaml`](manifests/app/sealed-py-wallet-secrets.yaml).

The Telegram secret is intentionally not present until it is sealed for the
target cluster. Its references are optional, so the website remains deployable
without it. Follow the [Telegram Mini App runbook](docs/telegram-mini-app.md) to
create and commit only the encrypted SealedSecret.

**Rotate or add a secret:** generate a plaintext `Secret` locally, pipe through `kubeseal`, commit the resulting `SealedSecret` (never commit plaintext).

```bash
kubectl create secret generic py-wallet-secrets \
  -n py-wallet-dev \
  --from-literal=DATABASE_URL='...' \
  --from-literal=JWT_SECRET='...' \
  --dry-run=client -o yaml \
| kubeseal --format yaml \
  --controller-namespace kube-system \
  --controller-name sealed-secrets \
> manifests/app/sealed-py-wallet-secrets.yaml
```

**PreSync ordering:** the app `SealedSecret` is a PreSync hook with `sync-wave: "-1"` so `py-wallet-secrets` exists before the Alembic migrate Job (`sync-wave: "0"`). The migrate Job only mounts the DB secret (not the app ConfigMap).

**Outside git:** backup the Sealed Secrets controller master key (loss = re-seal all secrets on a new cluster):

```bash
kubectl get secret -n kube-system \
  -l sealedsecrets.bitnami.com/sealed-secrets-key \
  -o yaml > sealed-secrets-master.key.yaml   # store offline, not in git
```

## Security model

- **No plaintext secrets in git** — only `SealedSecret` ciphertext; decryption happens in-cluster.
- **No CI cluster access** — GitHub Actions does not use kubeconfig or deploy RBAC; only Argo CD applies manifests.
- **Legacy `ci-deployer` RBAC removed** — was used for the old push-deploy model.

## Related repositories

| Repo | Role |
|------|------|
| **py_wallet-infra** (this repo) | GitOps manifests and Argo CD apps |
| [py_wallet-api](https://github.com/amysyutin/py_wallet-api) | Backend application source, CI build & push to GHCR (`py_wallet-api`) |
| [py_wallet-front](https://github.com/amysyutin/py_wallet-front) | Frontend application source, CI build & push to GHCR (`py_wallet-front`) |
| [py_wallet-snapshot-service](https://github.com/amysyutin/py_wallet-snapshot-service) | Snapshot service source, CI build & push to GHCR (`py_wallet-snapshot-service`) |

## License

MIT
