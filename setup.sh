#!/bin/bash
# Avatar Studio — Full setup (self-contained, no external folders needed)
set -e
GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; NC='\033[0m'
STUDIO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${BLUE}  Avatar Studio — Setup${NC}\n"

# 1. Homebrew deps
for dep in ffmpeg cmake portaudio; do
  if ! brew list "$dep" &>/dev/null; then
    echo "Installing $dep..."
    brew install "$dep"
  fi
done
echo -e "${GREEN}  ✓${NC} System dependencies ready"

# 2. Python
PYTHON=""
for cmd in python3.11 python3.12 python3; do
  if command -v "$cmd" &>/dev/null; then
    VER=$("$cmd" -c "import sys; print(sys.version_info.minor)")
    if [ "$VER" -ge 10 ]; then PYTHON="$cmd"; break; fi
  fi
done
if [ -z "$PYTHON" ]; then brew install python@3.11; PYTHON=python3.11; fi
echo -e "${GREEN}  ✓${NC} Python: $PYTHON"

# 3. Venv
VENV="$STUDIO_DIR/venv"
if [ ! -d "$VENV" ]; then
  "$PYTHON" -m venv "$VENV"
fi
source "$VENV/bin/activate"
pip install --upgrade pip --quiet
echo -e "${GREEN}  ✓${NC} venv ready"

# 4. All packages
echo "Installing packages (this takes a few minutes)..."
pip install torch torchvision torchaudio --quiet
pip install f5-tts openai-whisper --quiet
pip install fastapi "uvicorn[standard]" python-multipart pyyaml rich \
    opencv-python librosa scipy Pillow imageio imageio-ffmpeg tqdm --quiet
echo -e "${GREEN}  ✓${NC} All packages installed"

# 5. Wav2Lip
WAV2LIP="$STUDIO_DIR/models/Wav2Lip"
if [ ! -d "$WAV2LIP" ]; then
  echo "Cloning Wav2Lip..."
  git clone https://github.com/Rudrabha/Wav2Lip.git "$WAV2LIP" --quiet
fi

# 6. Download models if missing
MODEL="$WAV2LIP/checkpoints/wav2lip_gan.pth"
mkdir -p "$(dirname "$MODEL")"
if [ ! -f "$MODEL" ] || [ $(wc -c < "$MODEL") -lt 1000000 ]; then
  echo "Downloading wav2lip_gan.pth (~416MB)..."
  python -c "
from huggingface_hub import hf_hub_download; import shutil
p = hf_hub_download('Nekochu/Wav2Lip','wav2lip_gan.pth',local_dir='/tmp/w2l')
shutil.copy2(p,'$MODEL')
print('Model saved.')
"
fi

FACE_MODEL="$WAV2LIP/face_detection/detection/sfd/s3fd.pth"
mkdir -p "$(dirname "$FACE_MODEL")"
if [ ! -f "$FACE_MODEL" ]; then
  echo "Downloading face detection model (~90MB)..."
  curl -sL "https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth" -o "$FACE_MODEL" --progress-bar
fi

echo -e "\n${GREEN}  Setup complete!${NC}"
echo "  Run: ./run.sh"
echo "  Open: http://localhost:8002"
