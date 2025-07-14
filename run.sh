#!/bin/bash

# Mantooth Blog Processor Runner
# This script runs either the GUI or terminal version

echo "🦷 Mantooth Blog Processor"
echo "=========================="
echo

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_DIR="$SCRIPT_DIR/blog-processor/src"
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python3"
GUI_SCRIPT="$PYTHON_DIR/gui/blog_processor_gui.py"
CLI_SCRIPT="$PYTHON_DIR/main.py"

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
echo

# Check for command line argument
if [ "$1" = "--cli" ] || [ "$1" = "--terminal" ]; then
    echo "🖥️  Starting terminal version..."
    echo
    "$VENV_PYTHON" "$CLI_SCRIPT"
elif [ "$1" = "--cleanup" ]; then
    echo "🧹 Starting cleanup tool..."
    echo
    "$VENV_PYTHON" "$PYTHON_DIR/blog_manager.py"
else
    # Try to run GUI first, fallback to CLI if no display
    echo "🎨 Attempting to start GUI version..."
    echo "💡 Use './run.sh --cli' to force terminal version"
    echo
    
    if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
        echo "⚠️  No display detected, falling back to terminal version..."
        echo
        "$VENV_PYTHON" "$CLI_SCRIPT"
    else
        # Try GUI, fallback to CLI on error
        if ! "$VENV_PYTHON" "$GUI_SCRIPT" 2>/dev/null; then
            echo "⚠️  GUI failed to start, falling back to terminal version..."
            echo
            "$VENV_PYTHON" "$CLI_SCRIPT"
        fi
    fi
fi

echo
echo "👋 Blog processor finished!"