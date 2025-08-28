#!/bin/bash
#
# Install git hooks for Folder DateTime Fix project
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Folder DateTime Fix Git Hook Installer${NC}"
echo "======================================="
echo ""

# Find git directory
if [ -d ".git" ]; then
    GIT_DIR=".git"
elif [ -d "../.git" ]; then
    GIT_DIR="../.git"
else
    echo -e "${RED}Error:${NC} Git repository not found"
    echo "Please run from the project root directory"
    exit 1
fi

HOOKS_DIR="$GIT_DIR/hooks"
SCRIPT_DIR="$(dirname "$0")"

echo -e "${GREEN}Found git repository at:${NC} $GIT_DIR"
echo ""

# Check available hooks
echo -e "${BLUE}Available hooks:${NC}"
echo ""
echo "This will install a pre-commit hook that:"
echo "  • Automatically updates version.py with build information"
echo "  • Format: VERSION_BRANCH_BUILD-YYYYMMDD-COMMITHASH"
echo "  • Example: 0.5.1_main_42-20250828-a1b2c3d4"
echo ""

# Ask for confirmation
echo -e "${YELLOW}Install the version update hook?${NC}"
read -p "Install? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Installation cancelled${NC}"
    exit 0
fi

# Backup existing hook if it exists
if [ -f "$HOOKS_DIR/pre-commit" ]; then
    BACKUP_NAME="$HOOKS_DIR/pre-commit.backup-$(date +%Y%m%d-%H%M%S)"
    mv "$HOOKS_DIR/pre-commit" "$BACKUP_NAME"
    echo -e "${YELLOW}Note:${NC} Backed up existing pre-commit hook to $(basename $BACKUP_NAME)"
fi

# Install pre-commit hook
if [ -f "$SCRIPT_DIR/hooks/pre-commit-basic" ]; then
    cp "$SCRIPT_DIR/hooks/pre-commit-basic" "$HOOKS_DIR/pre-commit"
    chmod +x "$HOOKS_DIR/pre-commit"
    echo -e "${GREEN}✓${NC} Installed pre-commit hook"
else
    echo -e "${RED}Error:${NC} $SCRIPT_DIR/hooks/pre-commit-basic not found"
    exit 1
fi

# Make update-version.sh executable
if [ -f "$SCRIPT_DIR/update-version.sh" ]; then
    chmod +x "$SCRIPT_DIR/update-version.sh"
    echo -e "${GREEN}✓${NC} Made update-version.sh executable"
fi

echo ""
echo -e "${GREEN}Hook installation complete!${NC}"
echo ""
echo -e "${BLUE}Installed hooks:${NC}"
ls -la "$HOOKS_DIR" | grep -E "pre-commit" | grep -v backup || true

echo ""
echo -e "${BLUE}Manual version update:${NC}"
echo "  • Run: ./scripts/update-version.sh"
echo "  • Options: --build, --commit, --date YYYYMMDD"

echo ""
echo -e "${YELLOW}Tips:${NC}"
echo "  • Hook runs automatically on git commit"
echo "  • To bypass hook temporarily: git commit --no-verify"
echo "  • Version format: VERSION_BRANCH_BUILD-DATE-HASH"
echo "  • View version: python -c \"from version import __version__; print(__version__)\""

echo ""
echo -e "${GREEN}Ready to track versions!${NC}"