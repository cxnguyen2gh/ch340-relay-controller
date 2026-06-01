** GOAL **
  Create a reliable GUI app to control a 4-channel CH340 USB relay board.

** CURRENT STATUS **

- macOS app is implemented first.
- The app is packaged as a native arm64 macOS app with PyInstaller.
- Current macOS app path:
  Python/dist/CH340 Relay Controller.app
- Source code and build scripts are under ./Python.
- Windows 11 packaging scripts are prepared but the EXE must be built on Windows.

** IMPLEMENTED MACOS APP **

- Opens a small GUI window with 4 relay sections.
- Each relay section contains:
  - Channel title.
  - LED status indicator.
  - ON/OFF toggle button.
  - Gray rounded label box with black text.
- Relay labels are:
  - Edge HD Power
  - GT81 Power
  - Fan Power
  - SPARE
- The ON/OFF button is vertically enlarged for easier clicking.
- Overall GUI font sizes have been increased.
- The Refresh Serial button uses the same button font style and a matching larger button size.
- Bottom serial status text uses black text on a gray background for readability.

** RELAY INTERACTION **

- User can toggle each relay by clicking:
  - The ON/OFF button.
  - The LED.
  - The gray label box below the relay.
- The app sends standard 4-byte CH340 relay commands over serial.
- The app auto-detects CH340-compatible serial ports.
- Refresh Serial rescans and reconnects to the relay board.

** RELAY DEFAULTS **

- Desired startup relay state:
  - Channel 1 ON.
  - Channels 2, 3, and 4 OFF.
- If the board is not connected, the app does not show Channel 1 as ON.
- Default relay states are pushed only after serial communication is available.

** LED STATUS DISPLAY **

- No serial communication:
  - LED is gray.
  - No radial lines are shown.
- Relay ON with serial communication:
  - LED is yellow.
  - 10 radial lines are shown around the LED.
- Relay OFF with serial communication:
  - LED is light blue.
  - No radial lines are shown.

** STARTUP **

- macOS startup installer exists:
  Python/install_startup_macos.sh
- The startup installer builds the app if needed and installs a LaunchAgent.
- The LaunchAgent launches the packaged native app at login.
- Windows startup installer exists:
  Python/install_startup_windows.bat
- The Windows startup installer builds the EXE if needed and creates a Startup folder shortcut.

** APP ICON **

- Icon generator exists:
  Python/create_icon.py
- The icon is a red LED with a white switch in the middle.
- Generated assets:
  - Python/relay_icon.png
  - Python/relay_icon.ico
  - Python/AppIcon.icns

** BUILD **

- macOS build script:
  Python/create_app.sh
- Build output:
  Python/dist/CH340 Relay Controller.app
- PyInstaller build temp files are created under the system temp directory to avoid macOS codesign metadata errors on the external volume.
- Windows build script:
  Python/create_app_windows.bat
- Windows build output:
  Python/dist/CH340 Relay Controller.exe
- Windows EXE should be built on a Windows 11 machine because PyInstaller does not cross-compile Windows executables from macOS.
- A full Windows installer is optional. For personal use, the EXE plus the Startup shortcut script is enough. Use an installer later only if Start Menu entries, uninstall support, code signing, or broader distribution are needed.

** CODING STYLE **

- Follow:
  ../Shared Prompts/coding_style_python.md
- Each Python file must include the required proprietary/export-controlled header.
- Each function must include a short comment block description.

** OUTPUT RULES **

- Put generated project code under ./Python.
- Keep the app clickable as a normal macOS .app bundle.
- Rebuild the app after source changes so Python/dist/CH340 Relay Controller.app matches the current source.
