#!/data/data/com.termux/files/usr/bin/sh
# Устанавливает tgu в PATH (Termux: $PREFIX/bin, иначе /usr/local/bin)
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
chmod +x "$DIR/tgu"
if [ -n "$PREFIX" ] && [ -d "$PREFIX/bin" ]; then
  BIN="$PREFIX/bin"
else
  BIN="/usr/local/bin"
  [ -w "$BIN" ] || BIN="$HOME/.local/bin"
  mkdir -p "$BIN"
fi
ln -sf "$DIR/tgu" "$BIN/tgu"
echo "✓ установлено: $(command -v tgu 2>/dev/null || echo "$BIN/tgu")"
echo "  дальше:      tgu login"
