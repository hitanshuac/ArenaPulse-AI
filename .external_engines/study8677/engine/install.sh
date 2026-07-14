#!/usr/bin/env bash
set -euo pipefail

# Antigravity repository knowledge engine installer for Linux/macOS.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

echo "Antigravity Repository Knowledge Engine - Installer"
echo "==================================================="
echo ""

if ! command -v python3 > /dev/null 2>&1; then
    echo "Error: Python 3 is not installed."
    echo "Please install Python 3.10 or higher from https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"

if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "Error: Python $PYTHON_VERSION detected. Python 3.10 or higher is required."
    exit 1
fi

echo "Python $PYTHON_VERSION detected"

if ! command -v git > /dev/null 2>&1; then
    echo "Error: Git is not installed."
    echo "Please install Git from https://git-scm.com/downloads"
    exit 1
fi

echo "Git $(git --version | cut -d' ' -f3) detected"
echo ""

echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Skipping creation."
else
    python3 -m venv venv
    echo "Virtual environment created"
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Upgrading pip..."
python -m pip install --upgrade pip --quiet

echo "Installing Antigravity CLI and engine..."
python -m pip install -e ./cli -e './engine[dev]' --quiet
echo "Dependencies installed"

echo "Setting up local configuration..."
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Antigravity local configuration
# This file is for trusted local development. Keep real credentials out of git.

# OpenAI-compatible endpoint
OPENAI_BASE_URL=https://your-endpoint/v1
OPENAI_API_KEY=your-key
OPENAI_MODEL=your-model

# Retrieval graph mode: off, compact, or full.
AG_RETRIEVAL_MODE=compact
EOF
    echo "Created .env file"
else
    echo ".env file already exists. Skipping creation."
fi

if [ -f ".gitignore" ] && ! grep -qxF ".env" .gitignore; then
    printf '\n.env\n' >> .gitignore
fi

mkdir -p artifacts .antigravity

echo ""
echo "==================================================="
echo "Installation complete."
echo ""
echo "Next steps:"
echo "1. Run /ag-setup in your agent host, or configure OPENAI_* in .env."
echo "2. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo "3. Build repository knowledge:"
echo "   ag-refresh --workspace ."
echo "4. Ask a repository question:"
echo "   ag-ask \"How does this project work?\" --workspace ."
echo ""
echo "Documentation: docs/en/QUICK_START.md"
echo "==================================================="
