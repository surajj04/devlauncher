#!/usr/bin/env bash
#
# DevLaunch local installer
# Installs the PyInstaller build to /opt/devlauncher with icon and menu entry.
#
set -euo pipefail

# ---------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------
APP_NAME="devlauncher"
APP_DISPLAY="DevLaunch"
INSTALL_DIR="/opt/devlauncher"
BIN_LINK="/usr/bin/devlauncher"
DESKTOP_FILE="/usr/share/applications/devlauncher.desktop"
ICON_BASE="/usr/share/icons/hicolor"

ICON_SIZES=(16 24 32 48 64 128 256 512)

# ---------------------------------------------------------------
# Colours for output
# ---------------------------------------------------------------
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${BLUE}→${NC} $*"; }
ok()    { echo -e "${GREEN}✓${NC} $*"; }
warn()  { echo -e "${YELLOW}⚠${NC} $*"; }
fail()  { echo -e "${RED}✗${NC} $*" >&2; exit 1; }

# ---------------------------------------------------------------
# 1. Verify build exists
# ---------------------------------------------------------------
info "Checking build output..."
if [ ! -d "dist/DevLaunch" ]; then
    fail "dist/DevLaunch/ not found. Run the PyInstaller build first:
     uv run pyinstaller DevLaunch.spec --clean --noconfirm"
fi
if [ ! -f "dist/DevLaunch/DevLaunch" ]; then
    fail "dist/DevLaunch/DevLaunch binary not found."
fi
ok "Build found."

# ---------------------------------------------------------------
# 2. Prepare icon (convert JPG → PNG if needed)
# ---------------------------------------------------------------
info "Preparing icon..."

# Prefer icon.png; fall back to logo.jpg
SRC_ICON=""
if [ -f "assets/icon.png" ]; then
    SRC_ICON="assets/icon.png"
    ok "Using assets/icon.png"
elif [ -f "assets/logo.jpg" ]; then
    SRC_ICON="assets/logo.jpg"
    warn "Only logo.jpg found — converting to PNG..."
    if ! command -v convert >/dev/null 2>&1; then
        fail "ImageMagick not installed. Run: sudo apt install -y imagemagick"
    fi
    convert assets/logo.jpg \
        -resize 256x256 \
        -background none \
        -gravity center \
        -extent 256x256 \
        assets/icon.png
    ok "Converted assets/logo.jpg → assets/icon.png"
    SRC_ICON="assets/icon.png"
else
    fail "No icon found. Expected assets/icon.png or assets/logo.jpg"
fi

# ---------------------------------------------------------------
# 3. Install app files
# ---------------------------------------------------------------
info "Installing to $INSTALL_DIR ..."
sudo rm -rf "$INSTALL_DIR"
sudo mkdir -p "$INSTALL_DIR"
sudo cp -a dist/DevLaunch/. "$INSTALL_DIR/"
sudo chmod +x "$INSTALL_DIR/DevLaunch"
ok "App files installed."

# ---------------------------------------------------------------
# 4. Make data folder writable (portable SQLite storage)
# ---------------------------------------------------------------
info "Setting up data folder..."
sudo mkdir -p "$INSTALL_DIR/data"
sudo chmod 777 "$INSTALL_DIR/data"
ok "Data folder ready and writable."

# ---------------------------------------------------------------
# 5. Create symlink in /usr/bin
# ---------------------------------------------------------------
info "Creating symlink $BIN_LINK ..."
sudo ln -sf "$INSTALL_DIR/DevLaunch" "$BIN_LINK"
ok "Symlink created."

# ---------------------------------------------------------------
# 6. Install icons at multiple sizes
# ---------------------------------------------------------------
info "Installing icons at ${#ICON_SIZES[@]} sizes..."
if ! command -v convert >/dev/null 2>&1; then
    warn "ImageMagick not found — installing only 256x256 icon."
    sudo mkdir -p "$ICON_BASE/256x256/apps"
    sudo cp "$SRC_ICON" "$ICON_BASE/256x256/apps/devlauncher.png"
    sudo chmod 644 "$ICON_BASE/256x256/apps/devlauncher.png"
else
    for size in "${ICON_SIZES[@]}"; do
        dir="$ICON_BASE/${size}x${size}/apps"
        sudo mkdir -p "$dir"
        convert "$SRC_ICON" \
            -resize "${size}x${size}" \
            -background none \
            -gravity center \
            -extent "${size}x${size}" \
            "/tmp/devlauncher-${size}.png"
        sudo cp "/tmp/devlauncher-${size}.png" "$dir/devlauncher.png"
        sudo chmod 644 "$dir/devlauncher.png"
        rm -f "/tmp/devlauncher-${size}.png"
    done
fi
ok "Icons installed."

# ---------------------------------------------------------------
# 7. Create .desktop entry
# ---------------------------------------------------------------
info "Creating desktop entry..."
sudo tee "$DESKTOP_FILE" > /dev/null << EOF
[Desktop Entry]
Name=$APP_DISPLAY
Comment=Start, stop, and monitor local dev services
Exec=$INSTALL_DIR/DevLaunch
Icon=devlauncher
Terminal=false
Type=Application
Categories=Development;Utility;
StartupNotify=true
StartupWMClass=DevLaunch
Keywords=dev;launcher;services;process;database;server;
EOF
sudo chmod 644 "$DESKTOP_FILE"
ok "Desktop entry created."

# ---------------------------------------------------------------
# 8. Refresh system caches
# ---------------------------------------------------------------
info "Refreshing system caches..."
sudo update-desktop-database /usr/share/applications 2>/dev/null || true
sudo gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true
ok "Caches refreshed."

# ---------------------------------------------------------------
# Done
# ---------------------------------------------------------------
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅  DevLaunch installed successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  Run from terminal:  ${BLUE}devlauncher${NC}"
echo -e "  Or from app menu:   Search ${BLUE}DevLaunch${NC}"
echo ""
echo -e "  Installed at:       ${BLUE}/opt/devlauncher${NC}"
echo -e "  Data folder:        ${BLUE}/opt/devlauncher/data${NC}"
echo -e "  Desktop entry:      ${BLUE}/usr/share/applications/devlauncher.desktop${NC}"
echo ""
echo -e "  To uninstall:       ${BLUE}./uninstall-local.sh${NC}"
echo ""