#!/usr/bin/env bash
# Builds "CH340 Relay Controller.app" as a native macOS app under Python/dist.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="CH340 Relay Controller"
DIST_DIR="$SCRIPT_DIR/dist"
LOCAL_DIR="$SCRIPT_DIR/build"
TMP_ROOT="${TMPDIR:-/tmp}/ch340_relay_app"
TMP_DIST="$TMP_ROOT/dist"
TMP_BUILD="$TMP_ROOT/build"
TMP_SPEC="$TMP_ROOT/spec"
PY_SCRIPT="$SCRIPT_DIR/relay_controller.py"
PYTHON="$(command -v python3)"

#-----------------------------------------------------------------------------
# Dependencies
#-----------------------------------------------------------------------------
"$PYTHON" -m pip install -q -r "$SCRIPT_DIR/requirements.txt"

#-----------------------------------------------------------------------------
# Generate icon PNG and ICNS
#-----------------------------------------------------------------------------
echo "Generating icon..."
"$PYTHON" "$SCRIPT_DIR/create_icon.py"

ICONSET_DIR="$SCRIPT_DIR/AppIcon.iconset"
ICON_PNG="$SCRIPT_DIR/relay_icon.png"

rm -rf "$ICONSET_DIR"
mkdir -p "$ICONSET_DIR"

for size in 16 32 64 128 256 512; do
    sips -z "$size" "$size" "$ICON_PNG" \
        --out "$ICONSET_DIR/icon_${size}x${size}.png" > /dev/null
    double=$((size * 2))
    sips -z "$double" "$double" "$ICON_PNG" \
        --out "$ICONSET_DIR/icon_${size}x${size}@2x.png" > /dev/null
done

iconutil -c icns "$ICONSET_DIR" -o "$SCRIPT_DIR/AppIcon.icns"
rm -rf "$ICONSET_DIR"
echo "Icon built: AppIcon.icns"

#-----------------------------------------------------------------------------
# Build the app bundle with PyInstaller
#-----------------------------------------------------------------------------
echo "Building native .app..."
rm -rf "$DIST_DIR/$APP_NAME.app"
rm -rf "$TMP_ROOT"
mkdir -p "$DIST_DIR"
mkdir -p "$LOCAL_DIR"
mkdir -p "$TMP_DIST"
mkdir -p "$TMP_BUILD"
mkdir -p "$TMP_SPEC"

export COPYFILE_DISABLE=1
"$PYTHON" -m PyInstaller \
    --noconfirm \
    --windowed \
    --name "$APP_NAME" \
    --icon "$SCRIPT_DIR/AppIcon.icns" \
    --distpath "$TMP_DIST" \
    --workpath "$TMP_BUILD" \
    --specpath "$TMP_SPEC" \
    --hidden-import serial.tools.list_ports \
    --hidden-import serial.tools.list_ports_osx \
    "$PY_SCRIPT"

cp -R "$TMP_DIST/$APP_NAME.app" "$DIST_DIR/$APP_NAME.app"
cp "$TMP_SPEC/$APP_NAME.spec" "$LOCAL_DIR/$APP_NAME.spec"

if command -v xattr >/dev/null 2>&1; then
    xattr -cr "$DIST_DIR/$APP_NAME.app"
fi

echo ""
echo "Done! App created at:"
echo "  $DIST_DIR/$APP_NAME.app"
echo ""
echo "Double-click the app to launch it, or drag it to the Dock."
