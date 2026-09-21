#!/bin/sh
set -eu

package_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
endpoint_file="$package_dir/config/endpoint.txt"
client_path="${CODEX_HOME:-$HOME/.codex}/skills/v550-scope-advisor/scripts/local_telemetry_client.py"

resolve_codex_cli() {
  if [ -n "${V550_CODEX_CLI:-}" ]; then
    if [ -x "$V550_CODEX_CLI" ]; then
      printf '%s\n' "$V550_CODEX_CLI"
      return 0
    fi
    echo "V550_CODEX_CLI does not point to an executable Codex CLI." >&2
    return 1
  fi

  if command -v codex >/dev/null 2>&1; then
    command -v codex
    return 0
  fi

  for candidate in \
    "/Applications/ChatGPT.app/Contents/Resources/codex" \
    "$HOME/Applications/ChatGPT.app/Contents/Resources/codex" \
    "/Applications/Codex.app/Contents/Resources/codex" \
    "$HOME/Applications/Codex.app/Contents/Resources/codex" \
    "$HOME/.local/bin/codex" \
    "/opt/homebrew/bin/codex" \
    "/usr/local/bin/codex"
  do
    if [ -x "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  return 1
}

if [ "${1:-}" = "--check-cli" ]; then
  if resolve_codex_cli >/dev/null; then
    echo "Codex CLI detected."
    exit 0
  fi
  echo "Codex CLI was not found in PATH or the installed ChatGPT/Codex app." >&2
  exit 2
fi

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

if ! codex_cli=$(resolve_codex_cli); then
  echo "Codex CLI was not found in PATH or the installed ChatGPT/Codex app." >&2
  echo "Install the Codex CLI, or ask the instructor or TA for setup help." >&2
  exit 2
fi

trap 'unset V550_STUDENT_KEY V550_ACTION_ENDPOINT; stty echo 2>/dev/null || true' 0 HUP INT TERM

if [ -z "${V550_STUDENT_KEY:-}" ]; then
  if [ ! -t 0 ]; then
    echo "A private terminal is required to enter the V550 student key." >&2
    exit 2
  fi
  printf 'V550 student key (input hidden): ' >&2
  stty -echo
  IFS= read -r V550_STUDENT_KEY
  stty echo
  printf '\n' >&2
fi
export V550_STUDENT_KEY

python3 "$client_path" --check-config

exec "$codex_cli"
