#!/bin/sh
set -eu

package_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

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

if ! desktop_executable=$(resolve_desktop_executable); then
  echo "ChatGPT Desktop was not found. Install or update the macOS app first." >&2
  exit 2
fi

echo "Opening ChatGPT Desktop for local V550 practice."
echo "In the app, open this folder: $package_dir"
echo 'Select Codex, start a local chat, and invoke $v550-scope-advisor.'
cd "$package_dir"
exec "$desktop_executable"
