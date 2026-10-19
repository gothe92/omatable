#!/usr/bin/env bash
# Install (or with --uninstall, remove) Omatable as a desktop app for the current user.
# --default-sqlite also makes it the default app for SQLite files.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="$HOME/.local/bin/omatable"
DESKTOP="$HOME/.local/share/applications/omatable.desktop"
ICON="$HOME/.local/share/icons/hicolor/scalable/apps/omatable.svg"
MIMEAPPS="${XDG_CONFIG_HOME:-$HOME/.config}/mimeapps.list"

if [[ "${1:-}" == "--uninstall" ]]; then
  rm -f "$BIN" "$DESKTOP" "$ICON"
  # Drop only Omatable's own default-app entries
  [[ -f "$MIMEAPPS" ]] && sed -i '/^application\/\(vnd\.\|x-\)sqlite3=omatable\.desktop;\?$/d' "$MIMEAPPS"
  update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
  gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
  echo "✔ Omatable removed (your databases and containers were not touched)"
  exit 0
fi

install -Dm 0755 "$SCRIPT_DIR/omatable" "$BIN"
install -Dm 0644 "$SCRIPT_DIR/omatable.svg" "$ICON"
install -Dm 0644 "$SCRIPT_DIR/omatable.desktop" "$DESKTOP"
gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true

echo "✔ App installed:           ~/.local/bin/omatable"
echo "✔ Desktop entry installed: ~/.local/share/applications/omatable.desktop"

# Omatable is offered under "Open with" for SQLite files; it only becomes the
# default app when asked to, so an existing choice is never overwritten
update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
if [[ " $* " == *" --default-sqlite "* ]]; then
  xdg-mime default omatable.desktop application/vnd.sqlite3 application/x-sqlite3
  echo "✔ SQLite files (.db, .sqlite, .sqlite3) now open with Omatable by default"
else
  echo "✔ Omatable is available under \"Open with\" for SQLite files"
  echo "  (run ./install.sh --default-sqlite to make it the default)"
fi
