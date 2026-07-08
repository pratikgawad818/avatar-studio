"""
pipeline/subtitles_pro.py
Professional subtitle system with animations, word-by-word highlighting,
karaoke-style sync, multiple premium styles, and platform-specific optimizations.
"""
import os, logging, subprocess, json
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import re

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# SUBTITLE DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

class SubtitleSegment:
    """A single subtitle segment with timing and styling."""
    
    def __init__(
        self,
        start: float,
        end: float,
        text: str,
        words: Optional[List[Dict]] = None
    ):
        self.start = start
        self.end = end
        self.text = text
        self.words = words or []  # [{text, start, end}, ...]
    
    def duration(self) -> float:
        return self.end - self.start
    
    def to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT timestamp format."""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    
    def to_srt_entry(self, index: int) -> str:
        """Convert to SRT format entry."""
        return (
            f"{index}\n"
            f"{self.to_srt_time(self.start)} --> {self.to_srt_time(self.end)}\n"
            f"{self.text}\n\n"
        )


# ═══════════════════════════════════════════════════════════════════════════
# WHISPER WORD-LEVEL TRANSCRIPTION
# ═══════════════════════════════════════════════════════════════════════════

class WhisperTranscriber:
    """Generate word-level timestamps using Whisper."""
    
    @staticmethod
    def transcribe_with_word_timestamps(
        audio_path: str,
        model: str = "base",
        language: str = "en"
    ) -> List[SubtitleSegment]:
        """
        Transcribe audio with word-level timestamps.
        
        Args:
            audio_path: Path to audio file
            model: Whisper model (tiny, base, small, medium, large)
            language: Language code
        
        Returns:
            List of SubtitleSegment objects with word-level timing
        """
        try:
            import whisper
            
            logger.info(f"Transcribing with Whisper ({model})...")
            model_obj = whisper.load_model(model)
            
            result = model_obj.transcribe(
                audio_path,
                language=language,
                word_timestamps=True,
                verbose=False
            )
            
            segments = []
            for seg in result.get("segments", []):
                words_data = []
                
                if "words" in seg:
                    for word in seg["words"]:
                        words_data.append({
                            "text": word.get("word", "").strip(),
                            "start": word.get("start", 0),
                            "end": word.get("end", 0)
                        })
                
                segment = SubtitleSegment(
                    start=seg.get("start", 0),
                    end=seg.get("end", 0),
                    text=seg.get("text", "").strip(),
                    words=words_data
                )
                segments.append(segment)
            
            logger.info(f"✓ Transcribed {len(segments)} segments")
            return segments
            
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            raise
    
    @staticmethod
    def group_words_into_lines(
        segments: List[SubtitleSegment],
        words_per_line: int = 6,
        max_duration: float = 4.0
    ) -> List[SubtitleSegment]:
        """
        Group words into subtitle lines.
        
        Args:
            segments: List of segments with word timing
            words_per_line: Maximum words per subtitle line
            max_duration: Maximum duration per subtitle
        
        Returns:
            New list of grouped segments
        """
        all_words = []
        for seg in segments:
            all_words.extend(seg.words)
        
        if not all_words:
            return segments
        
        # Group words
        grouped = []
        current_words = []
        current_start = None
        
        for word in all_words:
            if not current_start:
                current_start = word["start"]
            
            current_words.append(word)
            current_duration = word["end"] - current_start
            
            if len(current_words) >= words_per_line or current_duration >= max_duration:
                # Create segment
                text = " ".join([w["text"] for w in current_words])
                segment = SubtitleSegment(
                    start=current_start,
                    end=current_words[-1]["end"],
                    text=text,
                    words=current_words.copy()
                )
                grouped.append(segment)
                
                current_words = []
                current_start = None
        
        # Add remaining words
        if current_words:
            text = " ".join([w["text"] for w in current_words])
            segment = SubtitleSegment(
                start=current_start,
                end=current_words[-1]["end"],
                text=text,
                words=current_words
            )
            grouped.append(segment)
        
        logger.info(f"Grouped into {len(grouped)} subtitle lines")
        return grouped


# ═══════════════════════════════════════════════════════════════════════════
# SUBTITLE STYLES (ANIMATED)
# ═══════════════════════════════════════════════════════════════════════════

class SubtitleStyle:
    """Subtitle styling configurations."""
    
    STYLES = {
        "netflix": {
            "font": "Arial",
            "fontsize": 28,
            "fontcolor": "white",
            "borderw": 2,
            "bordercolor": "black",
            "shadowx": 1,
            "shadowy": 1,
            "box": 1,
            "boxcolor": "black@0.7",
            "boxborderw": 10,
            "alignment": "center",
            "animation": None
        },
        "youtube": {
            "font": "Montserrat-Bold",
            "fontsize": 32,
            "fontcolor": "white",
            "borderw": 3,
            "bordercolor": "black",
            "shadowx": 2,
            "shadowy": 2,
            "box": 0,
            "alignment": "center",
            "animation": "pop_in"
        },
        "tiktok": {
            "font": "Montserrat-ExtraBold",
            "fontsize": 36,
            "fontcolor": "yellow",
            "borderw": 4,
            "bordercolor": "black",
            "shadowx": 0,
            "shadowy": 0,
            "box": 0,
            "alignment": "center",
            "animation": "bounce"
        },
        "instagram": {
            "font": "Helvetica-Bold",
            "fontsize": 30,
            "fontcolor": "white",
            "borderw": 3,
            "bordercolor": "black",
            "shadowx": 1,
            "shadowy": 1,
            "box": 1,
            "boxcolor": "black@0.6",
            "boxborderw": 8,
            "alignment": "center",
            "animation": "slide_up"
        },
        "professional": {
            "font": "Helvetica",
            "fontsize": 26,
            "fontcolor": "white",
            "borderw": 2,
            "bordercolor": "black",
            "shadowx": 1,
            "shadowy": 1,
            "box": 1,
            "boxcolor": "black@0.5",
            "boxborderw": 6,
            "alignment": "center",
            "animation": "fade_in"
        },
        "karaoke": {
            "font": "Montserrat-Bold",
            "fontsize": 34,
            "fontcolor": "white",
            "borderw": 3,
            "bordercolor": "black",
            "shadowx": 2,
            "shadowy": 2,
            "box": 0,
            "alignment": "center",
            "animation": "word_highlight",
            "highlight_color": "yellow"
        },
        "minimal": {
            "font": "Helvetica-Light",
            "fontsize": 24,
            "fontcolor": "white",
            "borderw": 0,
            "shadowx": 0,
            "shadowy": 0,
            "box": 0,
            "alignment": "center",
            "animation": "fade_in"
        },
        "podcast": {
            "font": "Georgia",
            "fontsize": 26,
            "fontcolor": "white",
            "borderw": 2,
            "bordercolor": "black",
            "shadowx": 1,
            "shadowy": 1,
            "box": 1,
            "boxcolor": "black@0.6",
            "boxborderw": 8,
            "alignment": "center",
            "animation": None
        }
    }
    
    @classmethod
    def get_style(cls, name: str) -> dict:
        """Get style configuration by name."""
        return cls.STYLES.get(name, cls.STYLES["professional"])


# ═══════════════════════════════════════════════════════════════════════════
# ASS SUBTITLE GENERATOR (ADVANCED STYLING & ANIMATION)
# ═══════════════════════════════════════════════════════════════════════════

class ASSSubtitleGenerator:
    """Generate ASS subtitles with advanced styling and animations."""
    
    @staticmethod
    def generate_ass_file(
        segments: List[SubtitleSegment],
        output_path: str,
        style_name: str = "professional",
        video_width: int = 1280,
        video_height: int = 720
    ) -> str:
        """
        Generate ASS subtitle file with styling and animations.
        
        Args:
            segments: List of subtitle segments
            output_path: Output ASS file path
            style_name: Style preset name
            video_width: Video width
            video_height: Video height
        
        Returns:
            Path to ASS file
        """
        style = SubtitleStyle.get_style(style_name)
        
        # ASS header
        ass_content = [
            "[Script Info]",
            "Title: Professional Subtitles",
            "ScriptType: v4.00+",
            f"PlayResX: {video_width}",
            f"PlayResY: {video_height}",
            "WrapStyle: 0",
            "ScaledBorderAndShadow: yes",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        ]
        
        # Convert colors (white, black, etc.)
        color_map = {
            "white": "&H00FFFFFF",
            "black": "&H00000000",
            "yellow": "&H0000FFFF",
            "red": "&H000000FF",
        }
        
        primary_color = color_map.get(style["fontcolor"], "&H00FFFFFF")
        outline_color = color_map.get(style.get("bordercolor", "black"), "&H00000000")
        
        # Alignment: 2 = bottom center
        alignment = 2
        
        # Style definition
        ass_content.append(
            f"Style: Default,{style['font']},{style['fontsize']},{primary_color},&H000000FF,"
            f"{outline_color},&H00000000,-1,0,0,0,100,100,0,0,1,{style['borderw']},"
            f"{style.get('shadowx', 0)},{alignment},10,10,50,1"
        )
        
        ass_content.extend([
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
        ])
        
        # Generate subtitle events
        for seg in segments:
            start_time = ASSSubtitleGenerator._format_ass_time(seg.start)
            end_time = ASSSubtitleGenerator._format_ass_time(seg.end)
            
            text = seg.text
            
            # Apply animation tags
            animation = style.get("animation")
            if animation == "fade_in":
                text = f"{{\\fad(200,0)}}{text}"
            elif animation == "pop_in":
                text = f"{{\\t(0,200,\\fscx120\\fscy120)\\t(200,400,\\fscx100\\fscy100)}}{text}"
            elif animation == "slide_up":
                text = f"{{\\move(640,{video_height + 50},640,{video_height - 50},0,300)}}{text}"
            elif animation == "bounce":
                text = f"{{\\t(0,100,\\fscy120)\\t(100,200,\\fscy100)\\t(200,300,\\fscy110)\\t(300,400,\\fscy100)}}{text}"
            elif animation == "word_highlight" and seg.words:
                # Karaoke-style word highlighting
                text = ASSSubtitleGenerator._create_karaoke_effect(seg, style)
            
            # Box background (if enabled)
            if style.get("box"):
                text = f"{{\\bord{style['boxborderw']}\\3c{color_map.get('black', '&H00000000')}}}{text}"
            
            ass_content.append(
                f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}"
            )
        
        # Write file
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(ass_content))
        
        logger.info(f"✓ Generated ASS file: {output_path} ({len(segments)} segments)")
        return output_path
    
    @staticmethod
    def _format_ass_time(seconds: float) -> str:
        """Format time for ASS format (H:MM:SS.CS)."""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int((seconds - int(seconds)) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
    
    @staticmethod
    def _create_karaoke_effect(segment: SubtitleSegment, style: dict) -> str:
        """Create karaoke-style word-by-word highlighting."""
        if not segment.words:
            return segment.text
        
        # Karaoke tags in ASS
        # \k<duration> - karaoke effect duration in centiseconds
        highlight_color = style.get("highlight_color", "yellow")
        color_map = {"yellow": "&H0000FFFF", "red": "&H000000FF"}
        h_color = color_map.get(highlight_color, "&H0000FFFF")
        
        karaoke_text = ""
        for word in segment.words:
            duration_cs = int((word["end"] - word["start"]) * 100)
            karaoke_text += f"{{\\k{duration_cs}}}{word['text']} "
        
        return karaoke_text.strip()


# ═══════════════════════════════════════════════════════════════════════════
# SUBTITLE BURNING (RENDER TO VIDEO)
# ═══════════════════════════════════════════════════════════════════════════

def burn_subtitles_advanced(
    video_path: str,
    subtitles_path: str,
    output_path: str,
    force_style: Optional[str] = None
) -> str:
    """
    Burn subtitles to video using ASS format (supports animations).
    
    Args:
        video_path: Input video path
        subtitles_path: ASS subtitle file path
        output_path: Output video path
        force_style: Force subtitle style (override ASS styles)
    
    Returns:
        Path to output video
    """
    logger.info(f"Burning subtitles: {subtitles_path}")
    
    # Build ffmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"ass={subtitles_path}",
        "-c:v", "libx264",
        "-preset", "slow",  # Better quality
        "-crf", "18",
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0:
            logger.error(f"Subtitle burning failed: {result.stderr[-500:]}")
            raise RuntimeError("Subtitle burning failed")
        
        logger.info(f"✓ Subtitles burned: {output_path}")
        return output_path
        
    except subprocess.TimeoutExpired:
        logger.error("Subtitle burning timed out")
        raise


# ═══════════════════════════════════════════════════════════════════════════
# FULL PIPELINE
# ═══════════════════════════════════════════════════════════════════════════

def create_professional_subtitles(
    video_path: str,
    audio_path: str,
    output_video_path: str,
    style: str = "professional",
    use_whisper: bool = True,
    whisper_model: str = "base",
    words_per_line: int = 6,
    temp_dir: str = "temp"
) -> str:
    """
    Create and burn professional subtitles with animations.
    
    Args:
        video_path: Input video path
        audio_path: Audio file path (for transcription)
        output_video_path: Final output video path
        style: Subtitle style preset
        use_whisper: Use Whisper for transcription
        whisper_model: Whisper model size
        words_per_line: Words per subtitle line
        temp_dir: Temporary directory
    
    Returns:
        Path to output video
    """
    logger.info("Creating professional subtitles...")
    
    os.makedirs(temp_dir, exist_ok=True)
    
    # Get video dimensions
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0",
        video_path
    ]
    result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
    dims = result.stdout.strip().split(",")
    video_width = int(dims[0]) if len(dims) >= 1 else 1280
    video_height = int(dims[1]) if len(dims) >= 2 else 720
    
    # Transcribe with word-level timestamps
    if use_whisper:
        transcriber = WhisperTranscriber()
        segments = transcriber.transcribe_with_word_timestamps(
            audio_path,
            model=whisper_model
        )
        
        # Group into readable lines
        segments = transcriber.group_words_into_lines(
            segments,
            words_per_line=words_per_line
        )
    else:
        # Fallback to simple segmentation
        logger.warning("Whisper disabled - using simple segmentation")
        segments = []
    
    # Generate ASS file
    ass_path = os.path.join(temp_dir, "subtitles.ass")
    ASSSubtitleGenerator.generate_ass_file(
        segments,
        ass_path,
        style_name=style,
        video_width=video_width,
        video_height=video_height
    )
    
    # Burn subtitles
    burn_subtitles_advanced(video_path, ass_path, output_video_path)
    
    logger.info(f"✓ Professional subtitles complete: {output_video_path}")
    return output_video_path


if __name__ == "__main__":
    # Test subtitle system
    logger.setLevel(logging.INFO)
    print("Professional subtitle system loaded")
    print("Styles:", list(SubtitleStyle.STYLES.keys()))
