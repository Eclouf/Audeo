#!/bin/bash
# Build script for Audeo on Linux/macOS

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=============================================================="
echo "                   Audeo Build Script                         "
echo "=============================================================="

# Parse arguments
ONE_DIR=false
OPTIMIZE=false
DEBUG=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --onedir)
            ONE_DIR=true
            shift
            ;;
        --optimize)
            OPTIMIZE=true
            shift
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Check Python
echo -e "\n[1/3] Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON=$(command -v python3)
    echo "  ✓ $($PYTHON --version)"
elif command -v python &> /dev/null; then
    PYTHON=$(command -v python)
    echo "  ✓ $($PYTHON --version)"
else
    echo "  ✗ Python not found!"
    exit 1
fi

# Check PyInstaller
echo -e "\n[2/3] Checking PyInstaller..."
if $PYTHON -m pip show pyinstaller &> /dev/null; then
    echo "  ✓ PyInstaller installed"
else
    echo "  ℹ Installing PyInstaller..."
    $PYTHON -m pip install pyinstaller --quiet
    echo "  ✓ PyInstaller installed"
fi

# Build arguments
echo -e "\n[3/3] Building executable..."
BUILD_ARGS=("devscripts/build.py")

if $ONE_DIR; then
    BUILD_ARGS+=("--onedir")
    echo "  ℹ Mode: Multiple files (--onedir)"
else
    echo "  ℹ Mode: Single file (default)"
fi

if $OPTIMIZE; then
    BUILD_ARGS+=("--optimize")
    echo "  ℹ Optimizing bytecode..."
fi

if $DEBUG; then
    BUILD_ARGS+=("--debug")
    echo "  ℹ Debug mode enabled"
fi

# Run build
cd "$PROJECT_ROOT"
$PYTHON "${BUILD_ARGS[@]}"

if [ $? -eq 0 ]; then
    echo -e "\n=============================================================="
    echo "✓ Build successful!"
    echo "=============================================================="
else
    echo -e "\n=============================================================="
    echo "✗ Build failed!"
    echo "=============================================================="
    exit 1
fi
