#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p backups
umask 077
target="backups/lab-$(date -u +%Y%m%dT%H%M%SZ).dump"
temporary="$target.partial"
trap 'rm -f "$temporary"' EXIT
kubectl --context=devops-lab -n lab-helm exec postgres-0 -- \
  pg_dump -U lab -d lab -Fc > "$temporary"
test -s "$temporary"
mv "$temporary" "$target"
printf 'Backup saved: %s\n' "$target"
