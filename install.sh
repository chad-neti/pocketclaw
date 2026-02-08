#!/bin/bash
# PocketClaw installer for Termux
# Usage: curl -sL https://raw.githubusercontent.com/pocketclaw/pocketclaw/main/install.sh | bash

set -e

REPO="pocketclaw/pocketclaw"
INSTALL_DIR="$HOME/.pocketclaw"
APP_DIR="$INSTALL_DIR/app"

# ── Colours ───────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'
ok() { echo -e "  ${GREEN}[+]${NC} $1"; }
err() { echo -e "  ${RED}[!]${NC} $1"; }
info() { echo -e "  ${CYAN}[*]${NC} $1"; }

echo -e "\n${CYAN}PocketClaw${NC} installer\n"

# ── Check we're in Termux ─────────────────────────────────
if [ -z "$TERMUX_VERSION" ] && [ ! -d "/data/data/com.termux" ]; then
    err "This installer is designed for Termux on Android."
    err "Get Termux from F-Droid: https://f-droid.org/packages/com.termux/"
    exit 1
fi

# ── Update packages ───────────────────────────────────────
info "Updating packages..."
pkg update -y -q 2>/dev/null && pkg upgrade -y -q 2>/dev/null
ok "Packages updated"

# ── Install Python & Git ──────────────────────────────────
for dep in python git; do
    if ! command -v $dep &>/dev/null; then
        info "Installing $dep..."
        pkg install -y -q $dep 2>/dev/null
    fi
done
ok "Python $(python3 --version 2>&1 | cut -d' ' -f2) + Git ready"

# ── Check Termux:API ─────────────────────────────────────
if ! command -v termux-battery-status &>/dev/null; then
    echo ""
    err "Termux:API not found."
    echo ""
    echo "  Install it from F-Droid:"
    echo "  https://f-droid.org/packages/com.termux.api/"
    echo ""
    echo "  Then install the bridge package:"
    echo "    pkg install termux-api"
    echo ""
    echo "  Re-run this installer after."
    exit 1
fi
ok "Termux:API detected"

# ── Clone / Update repo ──────────────────────────────────
if [ -d "$APP_DIR/.git" ]; then
    info "Updating existing install..."
    cd "$APP_DIR" && git pull -q
    ok "Updated to latest"
else
    info "Downloading PocketClaw..."
    mkdir -p "$INSTALL_DIR"
    git clone -q "https://github.com/$REPO.git" "$APP_DIR"
    ok "Downloaded"
fi

# ── Install Python deps ──────────────────────────────────
info "Installing dependencies..."
pip install -q -r "$APP_DIR/requirements.txt" 2>/dev/null
ok "Dependencies installed"

# ── Create directories ────────────────────────────────────
mkdir -p "$INSTALL_DIR"/{skills/custom,skills/community,memory/conversations,memory/summaries,logs}

# ── Default config ────────────────────────────────────────
if [ ! -f "$INSTALL_DIR/config.yaml" ]; then
    cp "$APP_DIR/config.default.yaml" "$INSTALL_DIR/config.yaml"
    ok "Config created at ~/.pocketclaw/config.yaml"
else
    ok "Config exists, skipping"
fi

# ── Identity file (the heart) ─────────────────────────────
if [ ! -f "$INSTALL_DIR/memory/identity.md" ]; then
    cp "$APP_DIR/identity.default.md" "$INSTALL_DIR/memory/identity.md"
    ok "Identity seeded at ~/.pocketclaw/memory/identity.md"
else
    ok "Identity exists, skipping"
fi

# ── Update skills paths to point at install ───────────────
# Patch config to use installed paths
python3 -c "
import yaml
from pathlib import Path
cfg_path = Path.home() / '.pocketclaw' / 'config.yaml'
cfg = yaml.safe_load(cfg_path.read_text())
cfg.setdefault('skills', {})['paths'] = [
    str(Path.home() / '.pocketclaw/app/skills/builtin'),
    str(Path.home() / '.pocketclaw/app/skills/official') if (Path.home() / '.pocketclaw/app/skills/official').exists() else '',
    str(Path.home() / '.pocketclaw/skills/community'),
    str(Path.home() / '.pocketclaw/skills/custom'),
]
cfg['skills']['paths'] = [p for p in cfg['skills']['paths'] if p]
cfg_path.write_text(yaml.dump(cfg, default_flow_style=False))
" 2>/dev/null

# ── Add to PATH ───────────────────────────────────────────
SHELL_RC="$HOME/.bashrc"
[ -f "$HOME/.zshrc" ] && SHELL_RC="$HOME/.zshrc"

if ! grep -q "pocketclaw" "$SHELL_RC" 2>/dev/null; then
    echo "" >> "$SHELL_RC"
    echo '# PocketClaw' >> "$SHELL_RC"
    echo "export PATH=\"$APP_DIR/bin:\$PATH\"" >> "$SHELL_RC"
    ok "Added to PATH"
fi

# ── Make executable ───────────────────────────────────────
chmod +x "$APP_DIR/bin/pocket"

# ── Storage access ────────────────────────────────────────
if [ ! -d "$HOME/storage" ]; then
    info "Setting up storage access..."
    termux-setup-storage 2>/dev/null || true
fi

# ── Done ──────────────────────────────────────────────────
echo ""
echo -e "${GREEN}PocketClaw installed!${NC}"
echo ""
echo "  Get started:"
echo "    1. Edit your config:  nano ~/.pocketclaw/config.yaml"
echo "       (add your API key under llm.api_key)"
echo ""
echo "    2. Start chatting:    source ~/.bashrc && pocket"
echo ""
echo "  Or one-shot:            pocket \"what's my battery at?\""
echo ""
echo "  Commands:"
echo "    pocket help            Full command list"
echo "    pocket doctor          Check everything works"
echo "    pocket skills          See available skills"
echo ""
