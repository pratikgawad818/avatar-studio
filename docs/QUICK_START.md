# 🚀 Avatar Studio Pro - Quick Start Guide

## Get Professional AI Videos in 5 Minutes

This guide will get you up and running with professional, undetectable AI videos immediately.

---

## ⚡ Quick Installation

### 1. Install System Dependencies

```bash
# macOS
brew install ffmpeg cmake python@3.11

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install ffmpeg cmake python3.11 python3.11-venv

# Verify installation
ffmpeg -version  # Should be 5.0+
python3 --version  # Should be 3.10 or 3.11
```

### 2. Setup Python Environment

```bash
cd avatar-studio

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements_pro.txt

# This will take 5-10 minutes
```

### 3. Download AI Models

```bash
# Create directories
mkdir -p models/Wav2Lip/checkpoints

# Download Wav2Lip checkpoint (required)
# Visit: https://github.com/Rudrabha/Wav2Lip#getting-the-weights
# Download wav2lip_gan.pth
# Place in: models/Wav2Lip/checkpoints/wav2lip_gan.pth
```

---

## 🎬 Your First Video (3 Steps)

### Step 1: Prepare Your Assets

```bash
# 1. Avatar photo (your face photo)
#    - Place in: avatars/
#    - Requirements: Clear, frontal face, good lighting
#    - Format: JPG or PNG

# 2. Script (what you want to say)
#    - Keep under 150 words for faster processing
#    - Write naturally as you would speak

# Example:
echo "Welcome to my channel! Today I'm sharing the top 5 tips for productivity. Let's dive in!" > script.txt
```

### Step 2: Run Generation

```python
# Create: generate_video.py
from pipeline.master_pipeline import generate_with_preset

# Generate your video
video = generate_with_preset(
    script=open("script.txt").read(),
    avatar_image="avatars/my_photo.jpg",
    preset_name="youtube_professional",  # or "tiktok_viral", "instagram_reels"
    output_path="outputs/my_first_video.mp4"
)

print(f"✓ Video created: {video}")
```

```bash
# Run it
python generate_video.py

# Wait 5-15 minutes (depending on length and hardware)
# Your video will be in outputs/
```

### Step 3: View and Share

```bash
# Open your video
open outputs/my_first_video.mp4

# It's ready to upload to YouTube, TikTok, Instagram!
```

---

## 🎯 Quick Preset Guide

### Choose Your Platform

```python
# YouTube (16:9, 1080p)
preset_name="youtube_professional"

# TikTok (9:16, vertical)
preset_name="tiktok_viral"

# Instagram Reels (9:16, vertical)
preset_name="instagram_reels"

# LinkedIn (16:9, professional)
preset_name="linkedin_professional"
```

### Choose Your Quality

```python
# Fast preview (2-3 min for 30s video)
preset_name="fast_preview"

# Balanced - RECOMMENDED (5-7 min for 30s video)
preset_name="balanced"

# Maximum quality (12-15 min for 30s video)
preset_name="maximum_quality"
```

### Choose Your Style

```python
# Cinematic look
preset_name="cinematic"

# Natural documentary
preset_name="documentary"

# Podcast clip
preset_name="podcast_clip"

# Explainer/tutorial
preset_name="explainer_video"
```

---

## 📝 Common Use Cases

### 1. YouTube Tutorial

```python
from pipeline.master_pipeline import generate_with_preset

generate_with_preset(
    script="In this tutorial, I'll show you how to use AI for video creation...",
    avatar_image="avatars/my_face.jpg",
    preset_name="youtube_professional",
    output_path="tutorial.mp4"
)
```

### 2. TikTok/Reels Short

```python
generate_with_preset(
    script="Here's a life hack that will blow your mind!",
    avatar_image="avatars/my_face.jpg",
    preset_name="tiktok_viral",
    output_path="tiktok_short.mp4"
)
```

### 3. Product Demo

```python
generate_with_preset(
    script="Introducing our revolutionary new product...",
    avatar_image="avatars/professional.jpg",
    preset_name="product_demo",
    output_path="demo.mp4"
)
```

### 4. LinkedIn Post

```python
generate_with_preset(
    script="Here are my thoughts on the future of AI in business...",
    avatar_image="avatars/headshot.jpg",
    preset_name="linkedin_professional",
    output_path="linkedin_post.mp4"
)
```

---

## 🎨 Customization Examples

### Add Background Music

```python
from pipeline.master_pipeline import MasterPipeline
from pipeline.presets import PresetLibrary

preset = PresetLibrary.get_preset("youtube_professional")
preset.background_music = True

pipeline = MasterPipeline()
pipeline.generate_video(
    script="Your script here...",
    avatar_image="avatars/photo.jpg",
    preset=preset,
    background_music="music/background.mp3",  # Add this
    output_path="video_with_music.mp4"
)
```

### Adjust Voice Speed

```python
preset = PresetLibrary.get_preset("balanced")
preset.voice_speed = 1.1  # 10% faster

# Then generate as usual
```

### Change Subtitle Style

```python
preset = PresetLibrary.get_preset("youtube_professional")
preset.subtitle_style = "tiktok"  # Bold yellow text
preset.subtitle_animation = True  # Add animations
```

### Adjust Avatar Size/Position

```python
preset = PresetLibrary.get_preset("balanced")
preset.avatar_scale = 0.65  # Bigger (default 0.55)
preset.avatar_position = "lower_right"  # Move to corner
```

---

## 🔧 Troubleshooting

### Problem: "FFmpeg not found"

```bash
# macOS
brew install ffmpeg

# Ubuntu
sudo apt-get install ffmpeg

# Verify
ffmpeg -version
```

### Problem: "ModuleNotFoundError: No module named 'torch'"

```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall PyTorch
pip install torch torchvision

# For Apple Silicon (M1/M2/M3)
pip install torch torchvision
```

### Problem: "Out of memory"

```python
# Use faster preset with lower requirements
preset_name="fast_preview"

# Or reduce resolution
preset.resolution = "1280x720"  # Instead of 1920x1080
```

### Problem: Video processing is slow

**Solutions:**
1. Use `"fast_preview"` preset for testing
2. Reduce script length (< 100 words)
3. Disable face enhancement: `preset.face_enhancement = False`
4. Disable upscaling: `preset.upscale_video = False`
5. Use GPU/MPS if available

### Problem: Lip-sync is off

```python
# Use enhanced lip-sync (takes longer but more accurate)
preset.lipsync_quality = "enhanced"
preset.lipsync_preprocess = True
preset.lipsync_postprocess = True
```

### Problem: Audio sounds robotic

```python
# Use warmer voice EQ
preset.voice_eq_preset = "warm"

# Add reverb
preset.voice_reverb = True

# Slow down slightly
preset.voice_speed = 0.95
```

---

## 💡 Pro Tips

### 1. **Avatar Photo Quality**
- ✅ Use well-lit, high-resolution photos
- ✅ Face should be frontal and clearly visible
- ✅ Neutral expression works best
- ❌ Avoid sunglasses, heavy shadows, or extreme angles

### 2. **Script Writing**
- ✅ Write as you speak (conversational)
- ✅ Keep sentences short and clear
- ✅ Use punctuation for natural pauses
- ✅ Read aloud before generating
- ❌ Avoid long run-on sentences

### 3. **Platform Optimization**
```python
# For YouTube: 1080p, 16:9
preset_name="youtube_professional"

# For TikTok/Reels: 1080x1920, 9:16
preset_name="tiktok_viral" or "instagram_reels"

# For LinkedIn: 720p is sufficient
preset_name="linkedin_professional"
```

### 4. **Processing Time**
- **Short scripts (< 50 words)**: 3-5 min
- **Medium scripts (50-100 words)**: 5-10 min
- **Long scripts (100-150 words)**: 10-15 min

### 5. **Quality vs Speed**
```python
# Testing/Previewing → Use "fast_preview"
# Publishing → Use "balanced" or "maximum_quality"
```

---

## 📊 Feature Checklist

Use this checklist to ensure professional output:

### ✅ Essential Features (Always On)
- [x] Lip-sync
- [x] Anti-detection
- [x] Platform-specific encoding
- [x] Audio mastering

### ✅ Recommended Features
- [x] Face enhancement (GFPGAN)
- [x] Head movement
- [x] Eye blinks
- [x] Subtitles
- [x] Color grading
- [x] Shadows and lighting

### 🎛️ Optional Features (Slower but Better)
- [ ] Upscaling (2x or 4x)
- [ ] Background music
- [ ] Advanced color matching
- [ ] Film grain
- [ ] Maximum stealth level

---

## 🎬 Complete Example Script

```python
#!/usr/bin/env python3
"""
Complete example: Generate a professional YouTube video
"""

from pipeline.master_pipeline import MasterPipeline
from pipeline.presets import PresetLibrary

def main():
    # Load preset
    preset = PresetLibrary.get_preset("youtube_professional")
    
    # Customize if needed
    preset.voice_speed = 1.0
    preset.subtitle_style = "youtube"
    preset.color_grade = "professional"
    
    # Initialize pipeline
    pipeline = MasterPipeline(temp_dir="temp")
    
    # Your content
    script = """
    Welcome to my channel! Today I'm discussing the top 5 AI tools
    that are revolutionizing content creation. These tools will save
    you hours of work and help you create professional content.
    Let's dive into the first tool...
    """
    
    # Generate video
    print("🎬 Starting video generation...")
    
    video_path = pipeline.generate_video(
        script=script.strip(),
        avatar_image="avatars/my_photo.jpg",
        preset=preset,
        background_music="music/background.mp3",  # Optional
        output_path="outputs/youtube_video.mp4",
        progress_callback=lambda pct, msg: print(f"[{pct}%] {msg}")
    )
    
    print(f"\n✅ Video ready: {video_path}")
    print("📤 Ready to upload to YouTube!")
    
    # Optional: Cleanup temp files
    # pipeline.cleanup()

if __name__ == "__main__":
    main()
```

Save as `generate.py` and run:
```bash
python generate.py
```

---

## 🎯 Next Steps

### 1. Experiment with Presets
Try different presets to find your style:
```bash
python -c "from pipeline.presets import PresetLibrary; print('\n'.join(p.name for p in PresetLibrary.list_presets()))"
```

### 2. Create Custom Presets
```python
from pipeline.presets import create_custom_preset, PresetManager

# Create custom based on existing
my_preset = create_custom_preset(
    base_preset_name="youtube_professional",
    custom_name="My Brand Style",
    voice_speed=1.05,
    color_grade="warm",
    subtitle_style="minimal"
)

# Save for reuse
manager = PresetManager()
manager.save_preset(my_preset)
```

### 3. Batch Process Videos
```python
scripts = [
    "Script for video 1...",
    "Script for video 2...",
    "Script for video 3..."
]

for i, script in enumerate(scripts):
    generate_with_preset(
        script=script,
        avatar_image="avatars/photo.jpg",
        preset_name="balanced",
        output_path=f"outputs/video_{i+1}.mp4"
    )
```

### 4. Explore Advanced Features
- Read `PROFESSIONAL_UPGRADE.md` for complete feature list
- Check `pipeline/` directory for module documentation
- Experiment with different quality settings

---

## 📚 Additional Resources

### Documentation
- **Complete Guide**: `PROFESSIONAL_UPGRADE.md`
- **API Reference**: Code docstrings in `pipeline/`
- **Examples**: See `pipeline/master_pipeline.py`

### Presets Reference
```python
# List all presets
from pipeline.presets import PresetLibrary
for preset in PresetLibrary.list_presets():
    print(f"{preset.name}: {preset.description}")

# Get preset details
preset = PresetLibrary.get_preset("youtube_professional")
print(preset)
```

### Getting Help
1. Check troubleshooting section above
2. Review `PROFESSIONAL_UPGRADE.md`
3. Verify all dependencies are installed
4. Test with `fast_preview` preset first

---

## ✨ Success Checklist

Before your first video:
- [ ] FFmpeg installed and working (`ffmpeg -version`)
- [ ] Python 3.10+ installed
- [ ] Virtual environment activated
- [ ] All dependencies installed (`pip list`)
- [ ] Wav2Lip checkpoint downloaded
- [ ] Avatar photo ready (clear, frontal face)
- [ ] Script written (under 150 words)

Ready to generate:
- [ ] Choose appropriate preset for your platform
- [ ] Run generation script
- [ ] Wait 5-15 minutes
- [ ] Check output in `outputs/` directory
- [ ] Upload to your platform!

---

## 🎉 You're Ready!

You now have everything you need to create professional, undetectable AI videos.

**Start with this command:**
```python
from pipeline.master_pipeline import generate_with_preset

generate_with_preset(
    script="Your amazing script here!",
    avatar_image="avatars/your_photo.jpg",
    preset_name="youtube_professional",
    output_path="my_video.mp4"
)
```

**That's it! Welcome to professional AI video creation! 🚀**
