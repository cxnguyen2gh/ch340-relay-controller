#!/usr/bin/env bash
# Install CH340 Relay Controller as a macOS login item via LaunchAgent

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="CH340 Relay Controller"
APP_EXE="$SCRIPT_DIR/dist/$APP_NAME.app/Contents/MacOS/$APP_NAME"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST="$PLIST_DIR/com.ch340.relay-controller.plist"

if [[ ! -x "$APP_EXE" ]]; then
    "$SCRIPT_DIR/create_app.sh"
fi

mkdir -p "$PLIST_DIR"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.ch340.relay-controller</string>
  <key>ProgramArguments</key>
  <array>
    <string>$APP_EXE</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <false/>
  <key>StandardOutPath</key>
  <string>$HOME/Library/Logs/relay_controller.log</string>
  <key>StandardErrorPath</key>
  <string>$HOME/Library/Logs/relay_controller.log</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo "Installed. App will launch at login."
echo "To start now:  launchctl start com.ch340.relay-controller"
echo "To uninstall:  launchctl unload '$PLIST' && rm '$PLIST'"
