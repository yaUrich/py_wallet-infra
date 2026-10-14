#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 RENDERED_DIRECTORY" >&2
  exit 2
fi

rendered_directory=$1
if [[ ! -d "${rendered_directory}" ]]; then
  echo "rendered directory does not exist: ${rendered_directory}" >&2
  exit 1
fi

failed=0

if grep -R -n -E '^[[:space:]]*image:[[:space:]].*:latest([[:space:]]|$)' "${rendered_directory}"; then
  echo "mutable :latest image tags are forbidden" >&2
  failed=1
fi

if ! python3 "$(dirname "$0")/check_image_policy.py" "${rendered_directory}"; then
  failed=1
fi

if grep -R -n -E '^kind:[[:space:]]+Secret[[:space:]]*$' "${rendered_directory}"; then
  echo "plaintext Kubernetes Secret resources are forbidden; use SealedSecret" >&2
  failed=1
fi

exit "${failed}"
