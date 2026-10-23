#!/usr/bin/env bash
#
# DevLaunch local uninstaller
#
set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}→${NC} $*"; }
ok()   { echo -e "${GREEN}✓${NC} $*"; }

info "Removing DevLaunch..."

# Remove app files
sudo rm -rf /opt/devlauncher
ok "Removed /opt/devlauncher"

# Remove symlink
sudo rm -f /usr/bin/devlauncher
ok "Removed /usr/bin/devlauncher"

# Remove desktop entry
sudo rm -f /usr/share/applications/devlauncher.desktop
ok "Removed desktop entry"

# Remove icons at all sizes
for size in 16 24 32 48 64 128 256 512; do
    sudo rm -f "/usr/share/icons/hicolor/${size}x${size}/apps/devlauncher.png"
done
ok "Removed icons"

# Refresh caches
sudo update-desktop-database /usr/share/applications 2>/dev/null || true
sudo gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true
ok "Caches refreshed"

echo ""
echo -e "${GREEN}✅ DevLaunch uninstalled.${NC}"
echo ""