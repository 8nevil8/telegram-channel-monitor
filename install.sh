#!/bin/bash
# Telegram Channel Monitor - Linux/macOS Installation Script
# Downloads latest code from GitHub and installs to ~/.tgmonitor
# Compatible with Python 3.8+

set -e  # Exit on error

echo "========================================"
echo "Telegram Channel Monitor - Installer"
echo "========================================"
echo ""

# GitHub repository information
REPO_URL="https://github.com/8nevil8/telegram-channel-monitor"
ZIP_URL="https://github.com/8nevil8/telegram-channel-monitor/archive/refs/heads/master.zip"
TEMP_DIR="/tmp/tgmonitor-install-$$"
INSTALL_DIR="$HOME/.tgmonitor"

echo "Repository: $REPO_URL"
echo "Installation directory: $INSTALL_DIR"
echo ""

# Step 1: Check Python version
echo "[1/11] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 is not installed or not in PATH."
    echo "Please install Python 3.8 or higher:"
    echo "  - Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
    echo "  - macOS: brew install python3"
    echo "  - Or download from https://www.python.org/downloads/"
    exit 1
fi

# Get Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $PYTHON_VERSION"

# Parse major and minor version
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

# Check if version is >= 3.8
if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo "ERROR: Python 3.8 or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "Python version OK"
echo ""

# Step 2: Check for required tools
echo "[2/11] Checking for required tools..."
DOWNLOAD_TOOL=""
if command -v curl &> /dev/null; then
    DOWNLOAD_TOOL="curl"
    echo "Found curl"
elif command -v wget &> /dev/null; then
    DOWNLOAD_TOOL="wget"
    echo "Found wget"
else
    echo "ERROR: Neither curl nor wget is installed"
    echo "Please install one of them:"
    echo "  - Ubuntu/Debian: sudo apt install curl"
    echo "  - macOS: curl is pre-installed"
    exit 1
fi

if ! command -v unzip &> /dev/null; then
    echo "ERROR: unzip is not installed"
    echo "Please install it:"
    echo "  - Ubuntu/Debian: sudo apt install unzip"
    echo "  - macOS: unzip is pre-installed"
    exit 1
fi
echo "Required tools OK"
echo ""

# Step 3: Prepare temporary directory
echo "[3/11] Preparing temporary directory..."
if [ -d "$TEMP_DIR" ]; then
    echo "Cleaning up previous download..."
    rm -rf "$TEMP_DIR"
fi
mkdir -p "$TEMP_DIR"
echo "Temporary directory ready"
echo ""

# Step 4: Download latest code from GitHub
echo "[4/11] Downloading latest code from GitHub..."
echo "This may take a moment..."

if [ "$DOWNLOAD_TOOL" = "curl" ]; then
    curl -L -o "$TEMP_DIR/repo.zip" "$ZIP_URL" 2>/dev/null
else
    wget -O "$TEMP_DIR/repo.zip" "$ZIP_URL" 2>/dev/null
fi

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to download code from GitHub"
    echo "Please check your internet connection and try again"
    echo "Or download manually from: $REPO_URL"
    rm -rf "$TEMP_DIR"
    exit 1
fi
echo "Download complete"
echo ""

# Step 5: Extract downloaded ZIP
echo "[5/11] Extracting files..."
unzip -q "$TEMP_DIR/repo.zip" -d "$TEMP_DIR"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to extract downloaded files"
    rm -rf "$TEMP_DIR"
    exit 1
fi
echo "Files extracted"
echo ""

# Find the extracted directory (will be telegram-channel-monitor-master or similar)
EXTRACTED_DIR=$(find "$TEMP_DIR" -maxdepth 1 -type d -name "telegram-channel-monitor-*" | head -n 1)
if [ -z "$EXTRACTED_DIR" ] || [ ! -d "$EXTRACTED_DIR" ]; then
    echo "ERROR: Could not find extracted directory"
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo "Working from: $EXTRACTED_DIR"
echo ""

# Step 6: Create installation directory structure
echo "[6/11] Creating directory structure..."
mkdir -p "$INSTALL_DIR/app/src"
echo "Directory structure created"
echo ""

# Step 7: Copy source files
echo "[7/11] Copying source files..."
cp "$EXTRACTED_DIR/src/__init__.py" "$INSTALL_DIR/app/src/"
cp "$EXTRACTED_DIR/src/main.py" "$INSTALL_DIR/app/src/"
cp "$EXTRACTED_DIR/src/monitor.py" "$INSTALL_DIR/app/src/"
cp "$EXTRACTED_DIR/src/matcher.py" "$INSTALL_DIR/app/src/"
cp "$EXTRACTED_DIR/src/notifier.py" "$INSTALL_DIR/app/src/"
echo "Source files copied"
echo ""

# Step 8: Copy requirements.txt
echo "[8/11] Copying requirements.txt..."
cp "$EXTRACTED_DIR/requirements.txt" "$INSTALL_DIR/app/"
echo "Requirements.txt copied"
echo ""

# Step 9: Copy config.example.yaml (only if not exists)
echo "[9/11] Setting up configuration..."
if [ ! -f "$INSTALL_DIR/config.yaml" ]; then
    cp "$EXTRACTED_DIR/config.example.yaml" "$INSTALL_DIR/config.yaml"
    echo "Created config.yaml from template"
else
    echo "Existing config.yaml preserved"
fi
echo ""

# Step 10: Copy .env.example (only if not exists)
echo "[10/11] Setting up environment file..."
if [ ! -f "$INSTALL_DIR/.env" ]; then
    cp "$EXTRACTED_DIR/.env.example" "$INSTALL_DIR/.env"
    echo "Created .env from template"
else
    echo "Existing .env preserved"
fi
echo ""

# Step 11: Create virtual environment
echo "[11/11] Creating virtual environment..."
if [ -d "$INSTALL_DIR/venv" ]; then
    echo "Removing old virtual environment..."
    rm -rf "$INSTALL_DIR/venv"
fi

python3 -m venv "$INSTALL_DIR/venv"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment"
    echo "You may need to install python3-venv:"
    echo "  - Ubuntu/Debian: sudo apt install python3-venv"
    rm -rf "$TEMP_DIR"
    exit 1
fi
echo "Virtual environment created"
echo ""

# Install dependencies
echo "Installing dependencies..."
echo "This may take a few minutes..."
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip --quiet
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/app/requirements.txt" --quiet
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    echo "Please check your internet connection and try again"
    rm -rf "$TEMP_DIR"
    exit 1
fi
echo "Dependencies installed successfully"
echo ""

# Generate tgmonitor.sh run script
echo "Creating run script..."
cat > "$INSTALL_DIR/tgmonitor.sh" << 'EOF'
#!/bin/bash
# Telegram Channel Monitor - Run Script
# Generated by install.sh

# Get script directory (resolves symlinks)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to installation directory
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    echo "Please run install.sh again to reinstall"
    exit 1
fi

# Run the monitor
python -m app.src.main "$@"

# Capture exit code
EXIT_CODE=$?

# Deactivate virtual environment
deactivate

# Exit with the same code as the monitor
exit $EXIT_CODE
EOF

# Make the run script executable
chmod +x "$INSTALL_DIR/tgmonitor.sh"
echo "Run script created and marked executable"
echo ""

# Clean up temporary files
echo "Cleaning up temporary files..."
rm -rf "$TEMP_DIR"
echo ""

# Installation complete
echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo ""
echo "Installation directory: $INSTALL_DIR"
echo "Repository: $REPO_URL"
echo ""
echo "NEXT STEPS:"
echo ""
echo "1. Edit configuration file:"
echo "   nano $INSTALL_DIR/config.yaml"
echo "   - Configure channels to monitor"
echo "   - Set up products and keywords"
echo ""
echo "2. Edit environment file:"
echo "   nano $INSTALL_DIR/.env"
echo "   - Add your Telegram API credentials from https://my.telegram.org/apps"
echo "   - Set API_ID, API_HASH, and PHONE_NUMBER"
echo ""
echo "3. Run the monitor:"
echo "   $INSTALL_DIR/tgmonitor.sh"
echo ""
echo "   Or add to PATH in your ~/.bashrc or ~/.zshrc:"
echo "   export PATH=\"\$HOME/.tgmonitor:\$PATH\""
echo "   Then run: tgmonitor.sh"
echo ""
echo "4. On first run:"
echo "   - Enter the authentication code sent to your Telegram app"
echo "   - Session will be saved for future runs"
echo ""
echo "To update:"
echo "   Just run this install.sh script again (preserves your config and session)"
echo ""
echo "To uninstall: rm -rf $INSTALL_DIR"
echo ""
