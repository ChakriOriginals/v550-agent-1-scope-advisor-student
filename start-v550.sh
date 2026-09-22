#!/bin/sh
set -eu

package_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

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

if ! codex_cli=$(resolve_codex_cli); then
  echo "Codex CLI was not found in PATH or the installed ChatGPT/Codex app." >&2
  echo "Install the Codex CLI, or ask the instructor or TA for setup help." >&2
  exit 2
fi

cd "$package_dir"
exec "$codex_cli"
