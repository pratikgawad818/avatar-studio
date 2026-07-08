#!/usr/bin/env python3
"""
Example script: Generate a professional video with Avatar Studio Pro
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.master_pipeline import generate_with_preset

def main():
    print("=" * 60)
    print("🎬 Avatar Studio Pro - Example Video Generation")
    print("=" * 60)
    
    # Example script
    script = """
    Welcome to Avatar Studio Pro! This is an example of what you can create 
    with this professional AI video generation system. The results are 
    indistinguishable from real recordings and ready for YouTube, 
    TikTok, and Instagram.
    """
    
    print("\n📝 Script:")
    print(script.strip())
    
    print("\n🎯 Using preset: youtube_professional")
    print("⏱️  This will take 5-10 minutes...")
    print("")
    
    try:
        # Generate video
        video_path = generate_with_preset(
            script=script.strip(),
            avatar_image="avatars/efec546e.jpg",  # Use existing avatar
            preset_name="youtube_professional",
            output_path="outputs/example_video.mp4"
        )
        
        print("")
        print("=" * 60)
        print("✅ SUCCESS!")
        print("=" * 60)
        print(f"📹 Video created: {video_path}")
        print("\n🎉 Ready to upload to YouTube!")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure you have:")
        print("   1. An avatar photo in avatars/ directory")
        print("   2. All dependencies installed")
        print("   3. Wav2Lip checkpoint downloaded")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Check:")
        print("   - Run: python scripts/test_installation.py")
        print("   - Read: docs/QUICK_START.md")

if __name__ == "__main__":
    main()
