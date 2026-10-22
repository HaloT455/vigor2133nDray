#!/usr/bin/env bash
# Read-only ALICE LAN diagnosis; never changes router configuration.
set -uo pipefail
ROUTER="${1:-192.168.4.1}"
ALICE="${2:-192.168.4.145}"
echo "ALICE status: router=$ROUTER candidate_alias=$ALICE"
ip -4 route get "$ALICE" 2>/dev/null | sed -E 's/ uid [0-9]+//g' || true
for target in "$ROUTER" "$ALICE"; do
  if ping -n -c 1 -W 2 "$target" >/dev/null 2>&1; then echo "$target ping OK"; else echo "$target ping no reply"; fi
  for path in /weblogin.htm /doc/alice_ai.htm; do
    status=$(curl -4 -s -o /dev/null --max-time 4 --connect-timeout 2 -w '%{http_code}' "http://$target$path" || true)
    echo "$target$path HTTP ${status:-000}"
  done
done
echo 'Alias requires LAN IP ownership and listener; HTTP 404/000 is not fixed by a web asset patch.'
