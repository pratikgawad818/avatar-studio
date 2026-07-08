#!/bin/bash

# Avatar Studio Pro - Dependency Installer
# Installs all required packages for professional AI video generation

set -e  # Exit on error

echo "================================================"
echo "🚀 Avatar Studio Pro - Dependency Installer"
echo "================================================"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "📍 Detected Python: $PYTHON_VERSION"

# Check if we're in virtual environment
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo "⚠️  Warning: Not in a virtual environment"
    echo "   Recommended: source venv/bin/activate"
    echo ""
fi

# Update pip
echo "📦 Updating pip..."
python3 -m pip install --upgrade pip

# Install dependencies in stages
echo ""
echo "Stage 1/5: Core Dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
pip install numpy opencv-python Pillow

echo ""
echo "Stage 2/5: Web Framework"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
pip install fastapi uvicorn[standard] python-multipart

echo ""
echo "Stage 3/5: Audio Processing"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
pip install librosa soundfile scipy audioread edge-tts

echo ""
echo "Stage 4/5: AI & Machine Learning"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
pip install torch torchvision openai-whisper

echo ""
echo "Stage 5/5: Video Enhancement (Optional but Recommended)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚠️  These packages are large and may take time..."

# GFPGAN and dependencies
pip install gfpgan basicsr realesrgan || echo "⚠️  Face enhancement packages failed (optional)"

# Background removal
pip install rembg || echo "⚠️  Background removal failed (optional)"

# Face detection
pip install dlib mediapipe || echo "⚠️  Face detection packages failed (optional)"

# Subtitle handling
pip install pysrt srt || echo "⚠️  Subtitle packages failed (optional)"

echo ""
echo "================================================"
echo "✅ Installation Complete!"
echo "================================================"
echo ""
echo "📊 Verifying installation..."
python3 scripts/test_installation.py

echo ""
echo "🎉 All set! Read docs/QUICK_START.md to begin."
echo "================================================"
