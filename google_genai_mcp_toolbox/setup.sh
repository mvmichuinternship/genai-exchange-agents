#!/bin/bash

# Google GenAI MCP Toolbox Setup Script
# This script installs and configures the Google GenAI Toolbox with database integration

set -e

echo "🚀 Setting up Google GenAI MCP Toolbox for ADK Agents"
echo "============================================================="

# Configuration
TOOLBOX_VERSION="latest"
INSTALL_DIR="/usr/local/bin"
WORK_DIR=$(pwd)

# Detect OS and architecture
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

# Normalize architecture names for the toolbox binary
case "$ARCH" in
    x86_64|amd64)
        ARCH="amd64"
        ;;
    arm64|aarch64)
        ARCH="arm64"
        ;;
    i386|i686)
        ARCH="386"
        ;;
    *)
        echo "❌ Unsupported architecture: $ARCH"
        echo "   Supported: amd64, arm64, 386"
        echo "   Please download manually from: https://github.com/googleapis/genai-toolbox/releases"
        exit 1
        ;;
esac

echo "� Detected OS: $OS, Architecture: $ARCH"# Function to install Toolbox binary
install_toolbox() {
    echo "📦 Installing Google GenAI Toolbox binary..."

    # Clean up any existing broken installation
    if [ -f "$INSTALL_DIR/toolbox" ]; then
        echo "   Removing existing toolbox binary..."
        if [ -w "$INSTALL_DIR" ]; then
            rm -f "$INSTALL_DIR/toolbox"
        else
            sudo rm -f "$INSTALL_DIR/toolbox"
        fi
    fi

    # Get the latest version (hardcoded for now, could be dynamic)
    VERSION="v0.18.0"

    # Normalize OS for Google Cloud Storage format
    case "$OS" in
        darwin)
            GCS_OS="darwin"
            ;;
        linux)
            GCS_OS="linux"
            ;;
        windows)
            GCS_OS="windows"
            ;;
        *)
            echo "❌ Unsupported OS: $OS"
            exit 1
            ;;
    esac

    # Download URL using Google Cloud Storage
    DOWNLOAD_URL="https://storage.googleapis.com/genai-toolbox/${VERSION}/${GCS_OS}/${ARCH}/toolbox"

    echo "   Downloading from: $DOWNLOAD_URL"

    # Download binary
    if command -v curl >/dev/null 2>&1; then
        curl -L -o toolbox "$DOWNLOAD_URL"
    elif command -v wget >/dev/null 2>&1; then
        wget -O toolbox "$DOWNLOAD_URL"
    else
        echo "❌ Neither curl nor wget found. Please install one of them."
        exit 1
    fi

    # Check if download was successful and is a valid binary
    if [ ! -f "toolbox" ] || [ ! -s "toolbox" ]; then
        echo "❌ Download failed or file is empty"
        echo "   Check if the URL is correct: $DOWNLOAD_URL"
        exit 1
    fi

    # Check if it's a valid binary (not an HTML error page)
    if file toolbox | grep -q "text"; then
        echo "❌ Downloaded file appears to be text, not a binary. Check the URL:"
        echo "   $DOWNLOAD_URL"
        echo "   This might be a 404 or incorrect version/platform."
        rm -f toolbox
        exit 1
    fi

    # Make executable
    chmod +x toolbox

    # Move to install directory (requires sudo)
    if [ -w "$INSTALL_DIR" ]; then
        mv toolbox "$INSTALL_DIR/toolbox"
    else
        echo "   Installing to $INSTALL_DIR (requires sudo)..."
        sudo mv toolbox "$INSTALL_DIR/toolbox"
    fi

    echo "✅ Toolbox binary installed successfully"

    # Verify installation
    if toolbox --version >/dev/null 2>&1; then
        echo "   Version: $(toolbox --version)"
    else
        echo "❌ Installation verification failed"
        echo "   Try downloading manually from: https://storage.googleapis.com/genai-toolbox/${VERSION}/"
        exit 1
    fi
}

# Function to install Python dependencies
install_python_deps() {
    echo "🐍 Installing Python dependencies..."

    # Detect Python executable
    if command -v python3.13 >/dev/null 2>&1; then
        PYTHON_EXEC="python3.13"
    elif command -v python3 >/dev/null 2>&1; then
        PYTHON_EXEC="python3"
    else
        echo "❌ Python 3 not found"
        exit 1
    fi

    echo "   Using Python: $PYTHON_EXEC ($($PYTHON_EXEC --version))"

    # Create virtual environment if it doesn't exist
    VENV_DIR="./venv"
    if [ ! -d "$VENV_DIR" ]; then
        echo "   Creating virtual environment..."
        $PYTHON_EXEC -m venv "$VENV_DIR"
    fi

    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    echo "   Activated virtual environment: $VENV_DIR"

    # Update the Python and pip executables to use the venv
    PYTHON_EXEC="$VENV_DIR/bin/python"
    PIP_EXEC="$VENV_DIR/bin/pip"

    # Upgrade pip first
    $PIP_EXEC install --upgrade pip

    # Install required packages
    $PIP_EXEC install toolbox-core asyncpg

    # Try to install google-adk (might not be available)
    if $PIP_EXEC install google-adk >/dev/null 2>&1; then
        echo "✅ Google ADK installed"
    else
        echo "⚠️  Google ADK not available (install manually if needed)"
    fi

    echo "✅ Python dependencies installed in virtual environment"
    echo "   To activate: source $VENV_DIR/bin/activate"
}

# Function to setup database
setup_database() {
    echo "🗄️ Setting up PostgreSQL database..."

    # Check if PostgreSQL is available
    if ! command -v psql >/dev/null 2>&1; then
        echo "⚠️  PostgreSQL not found. Please install PostgreSQL first."
        echo "   On macOS: brew install postgresql"
        echo "   On Ubuntu: sudo apt-get install postgresql postgresql-contrib"
        echo "   On CentOS: sudo yum install postgresql postgresql-server"
        return 1
    fi

    # Create database
    DB_NAME="testgendb"
    DB_USER="${USER}"

    echo "   Creating database: $DB_NAME"

    # Create database (ignore error if exists)
    createdb "$DB_NAME" 2>/dev/null || echo "   Database $DB_NAME already exists"

    # Apply schema
    if [ -f "schema.sql" ]; then
        echo "   Applying database schema..."
        # Use IF NOT EXISTS pattern to avoid conflicts
        sed 's/CREATE TABLE /CREATE TABLE IF NOT EXISTS /g; s/CREATE INDEX /CREATE INDEX IF NOT EXISTS /g; s/CREATE TRIGGER /CREATE OR REPLACE TRIGGER /g' schema.sql > schema_safe.sql
        psql "$DB_NAME" < schema_safe.sql
        rm -f schema_safe.sql
        echo "✅ Database schema applied"
    else
        echo "⚠️  schema.sql not found. Please run this script from the project directory."
    fi
}

# Function to setup configuration
setup_config() {
    echo "⚙️ Setting up configuration..."

    # Copy example config if tools.yaml doesn't exist
    if [ ! -f "tools.yaml" ]; then
        if [ -f "tools.yaml.example" ]; then
            cp tools.yaml.example tools.yaml
            echo "✅ Configuration file created: tools.yaml"
            echo "   Please edit tools.yaml with your database credentials"
        else
            echo "⚠️  tools.yaml.example not found"
        fi
    else
        echo "   tools.yaml already exists"
    fi
}

# Function to test installation
test_installation() {
    echo "🧪 Testing installation..."

    # Test Toolbox binary
    if toolbox --version >/dev/null 2>&1; then
        echo "✅ Toolbox binary working"
    else
        echo "❌ Toolbox binary test failed"
        return 1
    fi

    # Check for virtual environment
    VENV_DIR="./venv"
    if [ -d "$VENV_DIR" ]; then
        PYTHON_EXEC="$VENV_DIR/bin/python"
        echo "   Testing with virtual environment: $VENV_DIR"
    else
        # Fallback to system Python
        if command -v python3.13 >/dev/null 2>&1; then
            PYTHON_EXEC="python3.13"
        elif command -v python3 >/dev/null 2>&1; then
            PYTHON_EXEC="python3"
        else
            echo "❌ Python 3 not found"
            return 1
        fi
        echo "   Testing with system Python: $PYTHON_EXEC"
    fi

    # Test Python imports
    if $PYTHON_EXEC -c "import asyncpg; print('asyncpg OK')" >/dev/null 2>&1; then
        echo "✅ Python asyncpg working"
    else
        echo "❌ Python asyncpg test failed"
        return 1
    fi

    # Test toolbox-core
    if $PYTHON_EXEC -c "from toolbox_core import ToolboxClient; print('toolbox-core OK')" >/dev/null 2>&1; then
        echo "✅ Python toolbox-core working"
    else
        echo "❌ Python toolbox-core test failed"
        return 1
    fi

    # Test database connection (if tools.yaml exists)
    if [ -f "tools.yaml" ]; then
        echo "   Testing database connection..."
        if toolbox --tools-file "tools.yaml" --validate >/dev/null 2>&1; then
            echo "✅ Configuration validation passed"
        else
            echo "⚠️  Configuration validation failed (check database credentials)"
        fi
    fi

    echo "✅ Installation test completed"
}

# Main installation flow
main() {
    echo "Starting installation..."
    echo

    # Install Toolbox binary - check if it exists AND works
    if ! command -v toolbox >/dev/null 2>&1 || ! toolbox --version >/dev/null 2>&1; then
        install_toolbox
    else
        echo "✅ Toolbox binary already installed: $(toolbox --version)"
    fi

    echo

    # Install Python dependencies
    install_python_deps

    echo

    # Setup database
    setup_database

    echo

    # Setup configuration
    setup_config

    echo

    # Test installation
    test_installation

    echo
    echo "🎉 Installation completed!"
    echo
    echo "📋 Next steps:"
    echo "1. Edit tools.yaml with your database credentials"
    echo "2. Start the Toolbox server: toolbox --tools-file tools.yaml"
    echo "3. Test with your ADK agents using the Python client"
    echo
    echo "📚 Documentation:"
    echo "- Toolbox docs: https://googleapis.github.io/genai-toolbox/"
    echo "- Project README: ./README.md"
    echo
}

# Parse command line arguments
case "${1:-all}" in
    binary)
        install_toolbox
        ;;
    python)
        install_python_deps
        ;;
    database)
        setup_database
        ;;
    config)
        setup_config
        ;;
    test)
        test_installation
        ;;
    all)
        main
        ;;
    *)
        echo "Usage: $0 [binary|python|database|config|test|all]"
        echo "  binary   - Install Toolbox binary only"
        echo "  python   - Install Python dependencies only"
        echo "  database - Setup database only"
        echo "  config   - Setup configuration only"
        echo "  test     - Test installation only"
        echo "  all      - Complete installation (default)"
        exit 1
        ;;
esac