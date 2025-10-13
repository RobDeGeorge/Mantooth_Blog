#!/bin/bash

# Mantooth Blog Processor - Hyprland Optimized Runner
# Optimized for Hyprland/Wayland environments

echo "🦷 Mantooth Blog Processor (Hyprland Optimized)"
echo "=============================================="
echo

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python3"
GUI_SCRIPT="$SCRIPT_DIR/website/blog-processor/run_gui.py"

# Check if virtual environment exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Virtual environment not found at: $VENV_PYTHON"
    echo "💡 Please ensure the virtual environment is set up properly"
    exit 1
fi

# Change to project root directory
cd "$SCRIPT_DIR"

echo "📁 Working directory: $SCRIPT_DIR"
echo "🐍 Using Python: $VENV_PYTHON"
echo "🖥️  Display: $DISPLAY"
echo "🪟 Wayland: $WAYLAND_DISPLAY"
echo

# Enhanced environment setup for Hyprland
export QT_QPA_PLATFORM=wayland
export QT_WAYLAND_DISABLE_WINDOWDECORATION=1
export QT_AUTO_SCREEN_SCALE_FACTOR=1
export QT_ENABLE_HIGHDPI_SCALING=1
export QT_SCALE_FACTOR=1
export QT_USE_PHYSICAL_DPI=1

# Fallback to X11 if Wayland has issues
if [ -z "$WAYLAND_DISPLAY" ]; then
    echo "⚠️  Wayland not detected, falling back to X11"
    export QT_QPA_PLATFORM=xcb
fi

# Disable debug output for cleaner interface
export QT_LOGGING_RULES="*.debug=false;qt.qpa.*=false"

echo "🎨 Starting GUI with Hyprland optimizations..."
echo "💡 Window will auto-size to fit your screen"
echo

# Run the GUI
"$VENV_PYTHON" "$GUI_SCRIPT"

echo
echo "👋 Blog processor finished!"