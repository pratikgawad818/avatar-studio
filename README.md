# Avatar Studio

AI video generation with talking avatars

## Start Server

```bash
cd /Users/pratik/Desktop/avatar-studio
source venv/bin/activate
python app.py
```

Open: **http://localhost:8002**

## Make Video

1. Upload photo (clear face)
2. Write script
3. Select voice mode (Fast or Clone)
4. Click Generate
5. Wait 5-10 minutes
6. Video in `outputs/` folder

## Settings for Best Quality

- **Resolution:** 1920x1080 (default)
- **Avatar Scale:** 0.75 (default)
- **Lip Sync:** enhanced
- **Voice:** Fast mode for speed, Clone for your voice

## Features

✅ Full HD 1920x1080 output  
✅ Voice cloning (F5-TTS)  
✅ Text-to-speech (Edge-TTS)  
✅ Lip-sync (Wav2Lip)  
✅ Subtitles (Whisper AI)  
✅ Multiple aspect ratios

## Folders

- `avatars/` - Your photos
- `outputs/` - Generated videos
- `voices/` - Voice samples for cloning
- `backgrounds/` - Custom backgrounds

## Requirements

- Python 3.11 ✅
- FFmpeg
- 8GB+ RAM

## If Server Stops

```bash
cd /Users/pratik/Desktop/avatar-studio
source venv/bin/activate
python app.py
```

That's it!
