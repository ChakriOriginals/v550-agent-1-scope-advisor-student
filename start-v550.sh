#!/bin/sh
set -eu

package_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
endpoint_file="$package_dir/config/endpoint.txt"
client_path="${CODEX_HOME:-$HOME/.codex}/skills/v550-scope-advisor/scripts/local_telemetry_client.py"

if [ ! -f "$endpoint_file" ]; then
  echo "Missing instructor endpoint configuration." >&2
  exit 2
fi

V550_ACTION_ENDPOINT=$(sed -n '1p' "$endpoint_file")
export V550_ACTION_ENDPOINT

if [ ! -f "$client_path" ]; then
  echo "The V550 skill is not installed. Run: python3 install.py" >&2
  exit 2
fi

printf 'V550 student key (input hidden): ' >&2
stty -echo
IFS= read -r V550_STUDENT_KEY
stty echo
printf '\n' >&2
export V550_STUDENT_KEY
trap 'unset V550_STUDENT_KEY V550_ACTION_ENDPOINT; stty echo 2>/dev/null || true' EXIT HUP INT TERM

python3 "$client_path" --check-config

if ! command -v codex >/dev/null 2>&1; then
  echo "Codex CLI was not found. Ask the instructor or TA for local setup help." >&2
  exit 2
fi

exec codex
