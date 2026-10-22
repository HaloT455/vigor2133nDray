#!/usr/bin/env bash
# Read-only ALICE page verification. No router configuration changes.
set -euo pipefail
host="${1:-192.168.4.1}"
url="http://$host/alice.htm?alice_probe=350-$(date +%s)"
body=$(mktemp)
trap 'rm -f "$body"' EXIT
curl -fsS --max-time 10 -H "Cache-Control: no-cache" "$url" -o "$body"
if grep -Fq "alice-p35-banner" "$body"; then
  echo "PASS: ALICE P35 visible banner in HTTP response"
else
  echo "NOT VERIFIED: P35 marker not present. Check login redirects, cached pages and WEB partition."
  exit 2
fi
for script in alice_local.js alice_app.js; do
  status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://$host/JS/$script?v=350" || true)
  echo "Script $script HTTP status: $status"
done
