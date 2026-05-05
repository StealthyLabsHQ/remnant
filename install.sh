#!/bin/sh
set -eu

REPO_ARG="${1:-}"

if [ -z "${HOME:-}" ]; then
  echo "HOME is not set. Remnant needs a home directory to install into ~/.remnant." >&2
  exit 1
fi

if [ -n "$REPO_ARG" ]; then
  REPO="$(cd "$REPO_ARG" && pwd)"
else
  SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
  REPO="$SCRIPT_DIR"
fi

if [ ! -f "$REPO/packages/cli/pyproject.toml" ]; then
  if ! command -v git >/dev/null 2>&1; then
    echo "git is required for one-line install. Install Git first: https://git-scm.com/downloads" >&2
    exit 1
  fi

  REPO="$HOME/.remnant/remnant"
  if [ -d "$REPO/.git" ]; then
    git -C "$REPO" pull --ff-only >/dev/null
  else
    mkdir -p "$(dirname "$REPO")"
    git clone https://github.com/StealthyLabsHQ/remnant.git "$REPO" >/dev/null
  fi
fi

CLI="$REPO/packages/cli"
BIN="$HOME/.remnant/bin"
CMD="$BIN/remnant"

if [ ! -f "$CLI/pyproject.toml" ]; then
  echo "Cannot find packages/cli/pyproject.toml under $REPO. Pass the repo path as the first argument." >&2
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install it first: https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
fi

mkdir -p "$BIN"

cat > "$CMD" <<EOF
#!/bin/sh
exec uv run --no-project --with typer --with-editable "$CLI" remnant "\$@"
EOF

chmod +x "$CMD"

case "${SHELL:-}" in
  */zsh) PROFILE="$HOME/.zprofile" ;;
  */bash) PROFILE="$HOME/.bashrc" ;;
  *) PROFILE="$HOME/.profile" ;;
esac

PATH_LINE="export PATH=\"\$HOME/.remnant/bin:\$PATH\""
if [ -f "$PROFILE" ] && grep -F "$HOME/.remnant/bin" "$PROFILE" >/dev/null 2>&1; then
  echo "$BIN is already in your PATH profile."
else
  {
    echo ""
    echo "# Remnant CLI"
    echo "$PATH_LINE"
  } >> "$PROFILE"
  echo "Added $BIN to $PROFILE. Open a new terminal before running remnant."
fi

echo "Installed remnant command: $CMD"
echo "Try: remnant --help"
