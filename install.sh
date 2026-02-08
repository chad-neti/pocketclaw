#!/bin/bash
# PocketClaw installer for Termux
# Usage: curl -sL https://raw.githubusercontent.com/chad-neti/pocketclaw/main/install.sh | bash

set -e

# Fix encoding for Termux (defaults to ASCII on some devices)
export LANG=en_US.UTF-8
export PYTHONIOENCODING=utf-8

REPO="chad-neti/pocketclaw"
INSTALL_DIR="$HOME/.pocketclaw"
APP_DIR="$INSTALL_DIR/app"

# ── Colours ───────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
ok() { echo -e "  ${GREEN}[+]${NC} $1"; }
err() { echo -e "  ${RED}[!]${NC} $1"; }
info() { echo -e "  ${CYAN}[*]${NC} $1"; }

echo -e "\n${CYAN}${BOLD}PocketClaw${NC} installer\n"

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
    info "Termux:API not found. Installing..."
    pkg install -y termux-api 2>/dev/null || true
    if ! command -v termux-battery-status &>/dev/null; then
        echo ""
        err "Termux:API still not found."
        echo ""
        echo "  You need the Termux:API app from F-Droid:"
        echo "  https://f-droid.org/packages/com.termux.api/"
        echo ""
        echo "  Install the app, then re-run this installer."
        exit 1
    fi
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
ok "Dependencies installed (httpx, pyyaml)"

# ── Create directories ────────────────────────────────────
mkdir -p "$INSTALL_DIR"/{skills/custom,skills/community,memory/conversations,memory/summaries,logs}

# ── Default config ────────────────────────────────────────
if [ ! -f "$INSTALL_DIR/config.yaml" ]; then
    cp "$APP_DIR/config.default.yaml" "$INSTALL_DIR/config.yaml"
    ok "Config created"
else
    ok "Config exists, skipping"
fi

# ── Identity file ─────────────────────────────────────────
if [ ! -f "$INSTALL_DIR/memory/identity.md" ]; then
    cp "$APP_DIR/identity.default.md" "$INSTALL_DIR/memory/identity.md"
    ok "Identity seeded"
else
    ok "Identity exists, skipping"
fi

# ── Patch skills paths ───────────────────────────────────
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

# ── API key setup ─────────────────────────────────────────
echo ""
echo -e "${CYAN}${BOLD}API Setup${NC}"
echo ""

# Skip if key already configured
if [ -f "$INSTALL_DIR/.env" ] && grep -q "API_KEY=" "$INSTALL_DIR/.env" 2>/dev/null; then
    ok "API key already configured"
else
    echo "  Which AI provider?"
    echo ""
    echo "    1. Anthropic (Claude) — recommended"
    echo "    2. OpenAI (GPT-4o)"
    echo "    3. DeepSeek"
    echo "    4. Google (Gemini)"
    echo "    5. Groq (Llama)"
    echo "    6. Ollama (local — no key needed)"
    echo ""
    read -p "  > " PROVIDER_CHOICE
    echo ""

    case "$PROVIDER_CHOICE" in
        2) PROVIDER="openai";   ENV_NAME="OPENAI_API_KEY";   MODEL="gpt-4o" ;;
        3) PROVIDER="deepseek"; ENV_NAME="DEEPSEEK_API_KEY"; MODEL="deepseek-chat" ;;
        4) PROVIDER="google";   ENV_NAME="GOOGLE_API_KEY";   MODEL="gemini-2.0-flash" ;;
        5) PROVIDER="groq";     ENV_NAME="GROQ_API_KEY";     MODEL="llama-3.3-70b-versatile" ;;
        6) PROVIDER="ollama";   ENV_NAME="";                 MODEL="llama3.2" ;;
        *) PROVIDER="anthropic"; ENV_NAME="ANTHROPIC_API_KEY"; MODEL="claude-sonnet-4-20250514" ;;
    esac

    # Update config with chosen provider/model
    python3 -c "
import yaml
from pathlib import Path
cfg_path = Path.home() / '.pocketclaw' / 'config.yaml'
cfg = yaml.safe_load(cfg_path.read_text())
cfg.setdefault('llm', {})['provider'] = '$PROVIDER'
cfg['llm']['model'] = '$MODEL'
cfg_path.write_text(yaml.dump(cfg, default_flow_style=False))
" 2>/dev/null

    if [ "$PROVIDER" = "ollama" ]; then
        ok "Ollama selected — no API key needed"
        echo "  Make sure Ollama is running: ollama serve"
    elif [ -n "$ENV_NAME" ]; then
        read -p "  Paste your API key: " API_KEY
        echo ""
        if [ -n "$API_KEY" ]; then
            echo "${ENV_NAME}=${API_KEY}" > "$INSTALL_DIR/.env"
            ok "API key saved"

            # Quick connection test
            info "Testing connection..."
            if python3 -c "
import httpx, sys
key = '$API_KEY'
provider = '$PROVIDER'
model = '$MODEL'
try:
    if provider == 'anthropic':
        r = httpx.post('https://api.anthropic.com/v1/messages', headers={
            'x-api-key': key, 'anthropic-version': '2023-06-01', 'content-type': 'application/json',
        }, json={'model': model, 'max_tokens': 10, 'messages': [{'role': 'user', 'content': 'hi'}]}, timeout=10)
    else:
        urls = {'openai': 'https://api.openai.com/v1', 'deepseek': 'https://api.deepseek.com/v1',
                'groq': 'https://api.groq.com/openai/v1', 'google': 'https://generativelanguage.googleapis.com/v1beta'}
        r = httpx.post(urls.get(provider, 'https://api.openai.com/v1') + '/chat/completions', headers={
            'Authorization': f'Bearer {key}', 'Content-Type': 'application/json',
        }, json={'model': model, 'max_tokens': 10, 'messages': [{'role': 'user', 'content': 'hi'}]}, timeout=10)
    sys.exit(0 if r.status_code == 200 else 1)
except: sys.exit(1)
" 2>/dev/null; then
                ok "Connected to $MODEL"
            else
                echo -e "  ${RED}[!]${NC} Couldn't verify (may still work)"
            fi
        else
            err "No key entered — add it later: echo '${ENV_NAME}=your-key' > ~/.pocketclaw/.env"
        fi
    fi
fi

# ── Source PATH so pocket works immediately ───────────────
export PATH="$APP_DIR/bin:$PATH"

# ── Done ──────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}PocketClaw installed!${NC}"
echo ""
echo "  Start chatting:"
echo -e "    ${BOLD}source ~/.bashrc && pocket${NC}"
echo ""
echo "  Or one-shot:"
echo "    pocket \"what's my battery at?\""
echo ""
echo "  Commands:"
echo "    pocket help            Full command list"
echo "    pocket doctor          Check everything works"
echo "    pocket skills          See available skills"
echo ""
