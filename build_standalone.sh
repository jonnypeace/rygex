#!/bin/bash
set -e

# --- Dependency Checks ---
MISSING_DEPS=0

check_cmd() {
    if ! command -v "$1" &> /dev/null; then
        echo "Error: $1 is not installed."
        echo "  -> $2"
        MISSING_DEPS=1
    fi
}

echo "Checking dependencies..."

check_cmd "pyinstaller" "Install with: pip install pyinstaller"
check_cmd "staticx" "Install with: pip install staticx"
check_cmd "patchelf" "Install with: sudo apt install patchelf (Debian/Ubuntu) or sudo pacman -S patchelf (Arch) or sudo dnf install patchelf (Fedora)"
check_cmd "cargo" "Install Rust and Cargo from: https://rustup.rs"
check_cmd "maturin" "Install with: pip install maturin"

if [ $MISSING_DEPS -eq 1 ]; then
    echo ""
    echo "Please install the missing dependencies above and try again."
    exit 1
fi

echo "All dependencies found."
echo ""

# --- Build Process ---

echo "Building Rust extension..."
maturin build --release

# Find the built .so file
SO_FILE=$(find target/release -name "librygex_ext.so" | head -n 1)
if [ -z "$SO_FILE" ]; then
    SO_FILE=$(find target/release -name "rygex_ext.so" | head -n 1)
fi

if [ -z "$SO_FILE" ]; then
    echo "Could not find built Rust extension (.so file)"
    exit 1
fi

echo "Found Rust extension: $SO_FILE"
# Copying to current dir for PyInstaller to find it easily
cp "$SO_FILE" ./rygex_ext.so

echo "Running PyInstaller..."
# We use --add-binary for the .so file. 
# We don't use --collect-all rygex to avoid bundling .py files as data,
# which causes staticx to choke. PyInstaller will follow imports automatically.
export PYTHONPATH=$PYTHONPATH:.
pyinstaller --onefile \
    --name rygex \
    --add-binary "rygex_ext.so:." \
    rygex/cli.py

echo "Creating static binary with staticx..."
# staticx bundles all shared library dependencies including libc
staticx dist/rygex dist/rygex-static

# Cleanup temporary files
rm ./rygex_ext.so
rm ./rygex.spec

echo "Build complete!"
echo "Standalone binary: dist/rygex"
echo "Static binary: dist/rygex-static"
echo ""
echo "Note: dist/rygex-static is a fully standalone Linux binary with all dependencies bundled."
echo "For Windows, run PyInstaller on a Windows machine using a similar command:"
echo "pyinstaller --onefile --name rygex --add-binary \"rygex_ext.pyd;.\" rygex/cli.py"