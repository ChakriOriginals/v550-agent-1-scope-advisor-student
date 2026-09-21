#!/bin/sh
set -eu

package_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
endpoint_file="$package_dir/config/endpoint.txt"

resolve_client_path() {
  for candidate in \
    "$HOME/.agents/skills/v550-scope-advisor/scripts/local_telemetry_client.py" \
    "${CODEX_HOME:-$HOME/.codex}/skills/v550-scope-advisor/scripts/local_telemetry_client.py"
  do
    if [ -f "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

resolve_desktop_executable() {
  if [ -n "${V550_CHATGPT_EXECUTABLE:-}" ]; then
    if [ -x "$V550_CHATGPT_EXECUTABLE" ]; then
      printf '%s\n' "$V550_CHATGPT_EXECUTABLE"
      return 0
    fi
    echo "V550_CHATGPT_EXECUTABLE does not point to an executable app." >&2
    return 1
  fi

  for candidate in \
    "/Applications/ChatGPT.app/Contents/MacOS/ChatGPT" \
    "$HOME/Applications/ChatGPT.app/Contents/MacOS/ChatGPT"
  do
    if [ -x "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

if [ "${1:-}" = "--check-desktop" ]; then
  if resolve_desktop_executable >/dev/null; then
    echo "ChatGPT Desktop detected."
    exit 0
  fi
  echo "ChatGPT Desktop was not found in a standard macOS application location." >&2
  exit 2
fi

if [ ! -f "$endpoint_file" ]; then
  echo "Missing instructor endpoint configuration." >&2
  exit 2
fi

if ! client_path=$(resolve_client_path); then
  echo "The V550 skill is not installed. Run: python3 install.py" >&2
  exit 2
fi

if ! desktop_executable=$(resolve_desktop_executable); then
  echo "ChatGPT Desktop was not found. Install or update the macOS app first." >&2
  exit 2
fi

if [ -z "${V550_CHATGPT_EXECUTABLE:-}" ] && pgrep -x ChatGPT >/dev/null 2>&1; then
  echo "ChatGPT Desktop is already running." >&2
  echo "Choose ChatGPT > Quit ChatGPT, then rerun this launcher so the app inherits your private V550 key." >&2
  exit 2
fi

V550_ACTION_ENDPOINT=$(sed -n '1p' "$endpoint_file")
export V550_ACTION_ENDPOINT

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

echo "Opening ChatGPT Desktop with temporary V550 credentials."
echo "In the app, open this folder: $package_dir"
echo 'Select Codex, start a local chat, and invoke $v550-scope-advisor.'
cd "$package_dir"
exec "$desktop_executable"
