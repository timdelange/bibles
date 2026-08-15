#!/usr/bin/env bash
set -euo pipefail

REPO_NAME="${1:-bibles}"
ROOT_DIR="$(cd "$(dirname "${0}")" && pwd)"

if [ -z "${GH_TOKEN:-}" ]; then
  echo "Error: GH_TOKEN is not set." >&2
  echo "Add it as a Runtime Secret in Cursor, then start a new cloud agent run." >&2
  exit 1
fi

cd "${ROOT_DIR}"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: ${ROOT_DIR} is not a git repository." >&2
  exit 1
fi

echo "${GH_TOKEN}" | gh auth login --with-token
gh auth status

if git remote get-url origin >/dev/null 2>&1; then
  echo "Remote origin already exists; pushing to existing remote."
  git push -u origin main
else
  gh repo create "${REPO_NAME}" --private --source=. --remote=origin --push
fi

echo "Done. Repository: $(gh repo view --json url -q .url)"
