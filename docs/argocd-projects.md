# Argo CD AppProject boundaries

Argo CD uses the AppProjects in [`apps/projects.yaml`](../apps/projects.yaml)
to prevent a child Application from deploying from an unapproved repository,
to an unapproved namespace, or with an unapproved resource type. The root
Application remains in Argo CD's built-in `default` project because it only
reads this repository's `apps/` directory and creates the child
Applications. The AppProjects use sync wave `-1`, so Argo CD creates their
boundaries before it reconciles child Application project assignments.

## Project assignment

| Project | Child Applications | Sources | Destinations | Resource boundary |
| --- | --- | --- | --- | --- |
| `py-wallet-runtime` | `py-wallet`, `py-wallet-front`, `postgres`, `py-wallet-snapshot-service` | This repository only | `py-wallet-dev`, `py-wallet-data` | Explicit namespaced workload, networking, certificate, monitoring and SealedSecret kinds; every cluster-scoped kind is denied. |
| `py-wallet-cluster` | `cluster` | This repository only | In-cluster API server | Only cluster-scoped `Namespace` and `cert-manager.io/ClusterIssuer`; every namespaced kind is denied. |
| `py-wallet-observability` | `monitoring`, `monitoring-extras`, `loki`, `alloy` | This repository plus the Prometheus Community, Grafana and Grafana Community Helm repositories | `monitoring` | Any resource kind, including cluster-scoped kinds required by the approved Helm charts. |

The `py-wallet-observability` wildcard is intentional and limited by both the
three approved chart sources and the `monitoring` destination. It permits the
upstream charts to install their CRDs, RBAC, admission components and
monitoring resources. It does not permit a source outside the listed
repositories or deployment to a different namespace.

## Operational procedure

1. Add an Application only after selecting the project whose source,
   destination and resource boundary already cover it.
2. If no project covers it, document the concrete resource kinds, source URL
   and target namespaces first. Review the required privilege change before
   editing `apps/projects.yaml`.
3. Keep workload Applications in `py-wallet-runtime`; do not grant them
   cluster-scoped access to accommodate a single resource.
4. Keep cluster bootstrap resources in `py-wallet-cluster`. A new
   cluster-scoped resource needs an explicit entry in its whitelist.
5. Treat changes to `py-wallet-observability` sources or its wildcard policy
   as a security review: chart updates can introduce cluster-level resources.

## Verification

The pull-request workflow validates every Application and AppProject through
Kubeconform. Before submitting a change, run:

```bash
rendered_dir="$(mktemp -d)"
scripts/render-manifests.sh "${rendered_dir}"
scripts/check-manifest-policy.sh "${rendered_dir}"
python3 scripts/check-grafana-dashboard.py
kubeconform -strict -summary apps bootstrap
```

The final command needs the same Argo CD CRD schema resolution available in
CI. It verifies that AppProject and Application objects remain valid in
addition to the rendered workload manifests.
