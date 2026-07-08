"""
pipeline/audio_mastering.py
Professional audio processing: mastering, EQ, compression, reverb, de-essing,
natural speech patterns, background music mixing, and spatial audio.
"""
import os, sys, logging, subprocess, tempfile
from pathlib import Path
import numpy as np
from typing import Optional, Tuple, List

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# AUDIO ANALYSIS & PROCESSING (using librosa and pydub)
# ═══════════════════════════════════════════════════════════════════════════

class AudioProcessor:
    """Core audio processing with librosa."""
    
    @staticmethod
    def load_audio(path: str, sr: int = 22050) -> Tuple[np.ndarray, int]:
        """Load audio file."""
        try:
            import librosa
            audio, sample_rate = librosa.load(path, sr=sr, mono=False)
            if audio.ndim == 1:
                audio = audio.reshape(1, -1)  # Convert to 2D
            return audio, sample_rate
        except Exception as e:
            logger.error(f"Failed to load audio: {e}")
            raise
    
    @staticmethod
    def save_audio(audio: np.ndarray, path: str, sr: int = 22050):
        """Save audio to file."""
        try:
            import soundfile as sf
            if audio.ndim == 1:
                audio = audio.reshape(-1, 1)
            sf.write(path, audio.T, sr)
        except Exception as e:
            logger.error(f"Failed to save audio: {e}")
            raise
    
    @staticmethod
    def normalize_audio(audio: np.ndarray, target_db: float = -20.0) -> np.ndarray:
        """
        Normalize audio to target dB level.
        
        Args:
            audio: Audio array
            target_db: Target dB level
        
        Returns:
            Normalized audio
        """
        # Calculate RMS
        rms = np.sqrt(np.mean(audio ** 2))
        
        if rms == 0:
            return audio
        
        # Current dB
        current_db = 20 * np.log10(rms)
        
        # Calculate gain
        gain_db = target_db - current_db
        gain = 10 ** (gain_db / 20)
        
        # Apply gain
        normalized = audio * gain
        
        # Prevent clipping
        peak = np.abs(normalized).max()
        if peak > 1.0:
            normalized = normalized / peak * 0.99
        
        return normalized


# ═══════════════════════════════════════════════════════════════════════════
# EQ & TONE CONTROL
# ═══════════════════════════════════════════════════════════════════════════

class AudioEqualizer:
    """Professional audio equalization."""
    
    @staticmethod
    def apply_voice_eq(audio: np.ndarray, sr: int = 22050, preset: str = "broadcast") -> np.ndarray:
        """
        Apply voice-optimized EQ.
        
        Presets:
        - broadcast: Professional broadcast voice
        - warm: Warm, rich voice
        - bright: Clear, bright voice
        - natural: Subtle enhancement
        - podcast: Podcast-optimized
        """
        try:
            import librosa
            from scipy import signal
            
            presets = {
                "broadcast": {
                    "low_cut": 80,      # High-pass filter
                    "low_shelf": (200, 0.8, -2),    # Reduce rumble
                    "low_mid": (400, 1.5, 2),       # Body
                    "mid": (1800, 1.0, 3),          # Presence
                    "high_mid": (4000, 1.2, 2),     # Clarity
                    "high_shelf": (8000, 0.8, 1),   # Air
                },
                "warm": {
                    "low_cut": 60,
                    "low_shelf": (150, 1.0, 1),
                    "low_mid": (300, 1.2, 3),
                    "mid": (2000, 0.8, -1),
                    "high_mid": (5000, 1.0, 1),
                    "high_shelf": (10000, 0.8, -1),
                },
                "bright": {
                    "low_cut": 100,
                    "low_shelf": (200, 0.8, -3),
                    "low_mid": (500, 1.0, 0),
                    "mid": (2500, 1.2, 4),
                    "high_mid": (6000, 1.5, 3),
                    "high_shelf": (10000, 1.0, 2),
                },
                "natural": {
                    "low_cut": 70,
                    "low_shelf": (150, 0.8, -1),
                    "low_mid": (350, 1.0, 1),
                    "mid": (1500, 0.8, 1),
                    "high_mid": (4500, 1.0, 1),
                    "high_shelf": (9000, 0.8, 0.5),
                },
                "podcast": {
                    "low_cut": 90,
                    "low_shelf": (180, 1.0, -2),
                    "low_mid": (400, 1.3, 2.5),
                    "mid": (2000, 1.0, 2),
                    "high_mid": (5000, 1.2, 1.5),
                    "high_shelf": (8000, 0.8, 0.5),
                }
            }
            
            eq_settings = presets.get(preset, presets["natural"])
            
            # Apply high-pass filter (remove low rumble)
            nyquist = sr / 2
            low_cut_norm = eq_settings["low_cut"] / nyquist
            b, a = signal.butter(4, low_cut_norm, btype='high')
            result = signal.filtfilt(b, a, audio)
            
            # For more sophisticated EQ, use FFT-based filtering
            # This is a simplified version
            
            logger.info(f"Applied {preset} voice EQ")
            return result
            
        except Exception as e:
            logger.warning(f"EQ failed: {e}")
            return audio
    
    @staticmethod
    def apply_parametric_eq(
        audio: np.ndarray,
        sr: int,
        freq: float,
        q: float,
        gain_db: float
    ) -> np.ndarray:
        """
        Apply parametric EQ at specific frequency.
        
        Args:
            audio: Audio array
            sr: Sample rate
            freq: Center frequency in Hz
            q: Q factor (bandwidth)
            gain_db: Gain in dB
        """
        try:
            from scipy import signal
            
            # Design peaking filter
            nyquist = sr / 2
            freq_norm = freq / nyquist
            
            # Convert gain to linear
            gain = 10 ** (gain_db / 20)
            
            # Simple peaking filter using biquad
            b, a = signal.iirpeak(freq_norm, q)
            
            if gain_db > 0:
                # Boost
                result = signal.filtfilt(b * gain, a, audio)
            else:
                # Cut
                result = signal.filtfilt(b / gain, a, audio)
            
            return result
        except Exception as e:
            logger.warning(f"Parametric EQ failed: {e}")
            return audio


# ═══════════════════════════════════════════════════════════════════════════
# DYNAMIC RANGE COMPRESSION
# ═══════════════════════════════════════════════════════════════════════════

class AudioCompressor:
    """Dynamic range compression for consistent volume."""
    
    @staticmethod
    def compress(
        audio: np.ndarray,
        threshold_db: float = -20.0,
        ratio: float = 4.0,
        attack_ms: float = 5.0,
        release_ms: float = 50.0,
        sr: int = 22050
    ) -> np.ndarray:
        """
        Apply dynamic range compression.
        
        Args:
            audio: Audio array
            threshold_db: Compression threshold in dB
            ratio: Compression ratio (2:1 = 2.0)
            attack_ms: Attack time in milliseconds
            release_ms: Release time in milliseconds
            sr: Sample rate
        
        Returns:
            Compressed audio
        """
        # Convert times to samples
        attack_samples = int(attack_ms * sr / 1000)
        release_samples = int(release_ms * sr / 1000)
        
        # Convert threshold to linear
        threshold = 10 ** (threshold_db / 20)
        
        # Calculate envelope
        envelope = np.abs(audio)
        
        # Smooth envelope (attack/release)
        smoothed = np.zeros_like(envelope)
        for i in range(len(envelope)):
            if i == 0:
                smoothed[i] = envelope[i]
            else:
                if envelope[i] > smoothed[i - 1]:
                    # Attack
                    alpha = 1.0 - np.exp(-1.0 / attack_samples)
                else:
                    # Release
                    alpha = 1.0 - np.exp(-1.0 / release_samples)
                
                smoothed[i] = alpha * envelope[i] + (1 - alpha) * smoothed[i - 1]
        
        # Calculate gain reduction
        gain = np.ones_like(audio)
        over_threshold = smoothed > threshold
        
        # Apply compression to samples over threshold
        gain[over_threshold] = (
            (smoothed[over_threshold] / threshold) ** (1 - 1/ratio)
        ) ** -1
        
        # Apply makeup gain
        makeup_gain = ratio ** 0.5
        
        compressed = audio * gain * makeup_gain
        
        # Prevent clipping
        peak = np.abs(compressed).max()
        if peak > 1.0:
            compressed = compressed / peak * 0.99
        
        logger.info(f"Applied compression: {ratio:.1f}:1 @ {threshold_db}dB")
        return compressed
    
    @staticmethod
    def multiband_compress(audio: np.ndarray, sr: int = 22050) -> np.ndarray:
        """
        Apply multiband compression for professional sound.
        
        Splits audio into frequency bands and compresses each separately.
        """
        try:
            from scipy import signal
            
            # Split into 3 bands: low, mid, high
            nyquist = sr / 2
            
            # Low: 20-200 Hz
            b_low, a_low = signal.butter(4, [20/nyquist, 200/nyquist], btype='band')
            low = signal.filtfilt(b_low, a_low, audio)
            
            # Mid: 200-2000 Hz
            b_mid, a_mid = signal.butter(4, [200/nyquist, 2000/nyquist], btype='band')
            mid = signal.filtfilt(b_mid, a_mid, audio)
            
            # High: 2000+ Hz
            b_high, a_high = signal.butter(4, 2000/nyquist, btype='high')
            high = signal.filtfilt(b_high, a_high, audio)
            
            # Compress each band
            low_comp = AudioCompressor.compress(low, threshold_db=-25, ratio=3.0, sr=sr)
            mid_comp = AudioCompressor.compress(mid, threshold_db=-20, ratio=4.0, sr=sr)
            high_comp = AudioCompressor.compress(high, threshold_db=-18, ratio=2.5, sr=sr)
            
            # Mix bands
            result = low_comp + mid_comp + high_comp
            
            # Normalize
            peak = np.abs(result).max()
            if peak > 1.0:
                result = result / peak * 0.99
            
            logger.info("Applied multiband compression")
            return result
            
        except Exception as e:
            logger.warning(f"Multiband compression failed: {e}")
            return audio


# ═══════════════════════════════════════════════════════════════════════════
# REVERB & SPATIAL EFFECTS
# ═══════════════════════════════════════════════════════════════════════════

class ReverbProcessor:
    """Add natural reverb and spatial effects."""
    
    @staticmethod
    def add_reverb(
        audio: np.ndarray,
        room_size: float = 0.3,
        damping: float = 0.5,
        wet_level: float = 0.15,
        sr: int = 22050
    ) -> np.ndarray:
        """
        Add subtle reverb for natural room tone.
        
        Args:
            audio: Audio array
            room_size: Room size (0-1, 0.3 = small room)
            damping: High-frequency damping (0-1)
            wet_level: Reverb mix level (0-1, 0.15 = subtle)
            sr: Sample rate
        
        Returns:
            Audio with reverb
        """
        # Simple reverb using comb filters and all-pass filters
        # This is a simplified Freeverb-style algorithm
        
        # Comb filter delays (in samples)
        comb_delays = [
            int(sr * 0.0297),
            int(sr * 0.0371),
            int(sr * 0.0411),
            int(sr * 0.0437)
        ]
        
        # Apply room size scaling
        comb_delays = [int(d * (0.5 + room_size * 0.5)) for d in comb_delays]
        
        # Initialize comb filters
        comb_outputs = []
        for delay in comb_delays:
            # Simple comb filter
            output = np.zeros_like(audio)
            buffer = np.zeros(delay)
            
            for i in range(len(audio)):
                output[i] = audio[i] + buffer[-1] * (1 - damping) * 0.7
                buffer = np.roll(buffer, 1)
                buffer[0] = output[i]
            
            comb_outputs.append(output)
        
        # Mix comb filters
        reverb = np.mean(comb_outputs, axis=0)
        
        # Mix dry and wet
        result = audio * (1 - wet_level) + reverb * wet_level
        
        # Normalize
        peak = np.abs(result).max()
        if peak > 1.0:
            result = result / peak * 0.99
        
        logger.info(f"Added reverb: room={room_size:.2f}, wet={wet_level:.2f}")
        return result


# ═══════════════════════════════════════════════════════════════════════════
# DE-ESSER (REDUCE SIBILANCE)
# ═══════════════════════════════════════════════════════════════════════════

class DeEsser:
    """Reduce harsh 's' sounds (sibilance)."""
    
    @staticmethod
    def de_ess(
        audio: np.ndarray,
        sr: int = 22050,
        freq: float = 6000.0,
        threshold_db: float = -25.0,
        ratio: float = 3.0
    ) -> np.ndarray:
        """
        Apply de-essing to reduce sibilance.
        
        Args:
            audio: Audio array
            sr: Sample rate
            freq: Sibilance frequency (typically 5-8 kHz)
            threshold_db: Detection threshold
            ratio: Compression ratio for sibilance
        
        Returns:
            De-essed audio
        """
        try:
            from scipy import signal
            
            # Extract high frequencies (sibilance range)
            nyquist = sr / 2
            b, a = signal.butter(4, freq / nyquist, btype='high')
            sibilance = signal.filtfilt(b, a, audio)
            
            # Detect sibilance envelope
            envelope = np.abs(sibilance)
            threshold = 10 ** (threshold_db / 20)
            
            # Compress only sibilance
            gain = np.ones_like(audio)
            over_threshold = envelope > threshold
            gain[over_threshold] = (envelope[over_threshold] / threshold) ** (1 - 1/ratio) ** -1
            
            # Apply to high frequencies only
            sibilance_reduced = sibilance * gain
            
            # Get low frequencies
            b_low, a_low = signal.butter(4, freq / nyquist, btype='low')
            low_freq = signal.filtfilt(b_low, a_low, audio)
            
            # Recombine
            result = low_freq + sibilance_reduced
            
            # Normalize
            peak = np.abs(result).max()
            if peak > 1.0:
                result = result / peak * 0.99
            
            logger.info("Applied de-essing")
            return result
            
        except Exception as e:
            logger.warning(f"De-essing failed: {e}")
            return audio


# ═══════════════════════════════════════════════════════════════════════════
# BACKGROUND MUSIC MIXING
# ═══════════════════════════════════════════════════════════════════════════

class MusicMixer:
    """Mix background music with voice."""
    
    @staticmethod
    def mix_background_music(
        voice_audio: np.ndarray,
        music_path: str,
        music_level_db: float = -25.0,
        ducking: bool = True,
        ducking_amount_db: float = -8.0,
        sr: int = 22050
    ) -> np.ndarray:
        """
        Mix background music with voice, with optional ducking.
        
        Args:
            voice_audio: Voice audio array
            music_path: Path to background music file
            music_level_db: Music volume level in dB
            ducking: Enable ducking (reduce music when voice is present)
            ducking_amount_db: Amount to reduce music during voice (dB)
            sr: Sample rate
        
        Returns:
            Mixed audio
        """
        try:
            import librosa
            
            # Load music
            music, _ = librosa.load(music_path, sr=sr, mono=True)
            
            # Loop or trim music to match voice length
            if len(music) < len(voice_audio):
                # Loop music
                repeats = int(np.ceil(len(voice_audio) / len(music)))
                music = np.tile(music, repeats)[:len(voice_audio)]
            else:
                # Trim music
                music = music[:len(voice_audio)]
            
            # Set music level
            music_gain = 10 ** (music_level_db / 20)
            music = music * music_gain
            
            # Apply ducking if enabled
            if ducking:
                # Detect voice activity
                voice_envelope = np.abs(voice_audio)
                
                # Smooth envelope
                from scipy import signal
                window_size = int(sr * 0.05)  # 50ms
                voice_envelope = signal.convolve(voice_envelope, np.ones(window_size)/window_size, mode='same')
                
                # Threshold for voice detection
                voice_threshold = np.percentile(voice_envelope, 30)
                voice_active = voice_envelope > voice_threshold
                
                # Calculate ducking gain
                ducking_gain = 10 ** (ducking_amount_db / 20)
                music_gain_curve = np.where(voice_active, ducking_gain, 1.0)
                
                # Smooth gain changes
                music_gain_curve = signal.convolve(music_gain_curve, np.ones(window_size)/window_size, mode='same')
                
                # Apply ducking
                music = music * music_gain_curve
            
            # Mix
            mixed = voice_audio + music
            
            # Normalize
            peak = np.abs(mixed).max()
            if peak > 1.0:
                mixed = mixed / peak * 0.99
            
            logger.info(f"Mixed background music: level={music_level_db}dB, ducking={ducking}")
            return mixed
            
        except Exception as e:
            logger.warning(f"Music mixing failed: {e}")
            return voice_audio


# ═══════════════════════════════════════════════════════════════════════════
# FULL AUDIO MASTERING PIPELINE
# ═══════════════════════════════════════════════════════════════════════════

def master_audio(
    input_path: str,
    output_path: str,
    preset: str = "professional",
    eq_preset: str = "broadcast",
    add_compression: bool = True,
    add_reverb: bool = True,
    add_deessing: bool = True,
    background_music: Optional[str] = None,
    music_level_db: float = -25.0,
    target_loudness_db: float = -16.0
) -> str:
    """
    Master audio with professional processing chain.
    
    Processing order:
    1. De-essing (reduce sibilance)
    2. EQ (tone shaping)
    3. Compression (dynamic control)
    4. Reverb (space/ambience)
    5. Background music (if provided)
    6. Final normalization
    
    Args:
        input_path: Input audio file
        output_path: Output audio file
        preset: Master preset (professional, podcast, broadcast, natural)
        eq_preset: EQ preset
        add_compression: Enable compression
        add_reverb: Enable reverb
        add_deessing: Enable de-essing
        background_music: Path to background music (optional)
        music_level_db: Background music level
        target_loudness_db: Target loudness (LUFS approximation)
    
    Returns:
        Path to mastered audio
    """
    logger.info(f"Mastering audio: {input_path}")
    
    # Preset configurations
    presets = {
        "professional": {
            "compression_ratio": 4.0,
            "compression_threshold": -20.0,
            "reverb_size": 0.25,
            "reverb_wet": 0.12,
        },
        "podcast": {
            "compression_ratio": 3.5,
            "compression_threshold": -22.0,
            "reverb_size": 0.15,
            "reverb_wet": 0.08,
        },
        "broadcast": {
            "compression_ratio": 5.0,
            "compression_threshold": -18.0,
            "reverb_size": 0.2,
            "reverb_wet": 0.1,
        },
        "natural": {
            "compression_ratio": 2.5,
            "compression_threshold": -24.0,
            "reverb_size": 0.3,
            "reverb_wet": 0.15,
        }
    }
    
    settings = presets.get(preset, presets["professional"])
    
    # Load audio
    processor = AudioProcessor()
    audio, sr = processor.load_audio(input_path)
    
    # Process first channel (or mono)
    if audio.ndim > 1:
        audio = audio[0]
    
    # 1. De-essing
    if add_deessing:
        deesser = DeEsser()
        audio = deesser.de_ess(audio, sr)
    
    # 2. EQ
    equalizer = AudioEqualizer()
    audio = equalizer.apply_voice_eq(audio, sr, eq_preset)
    
    # 3. Compression
    if add_compression:
        compressor = AudioCompressor()
        audio = compressor.multiband_compress(audio, sr)
        # audio = compressor.compress(
        #     audio, sr=sr,
        #     threshold_db=settings["compression_threshold"],
        #     ratio=settings["compression_ratio"]
        # )
    
    # 4. Reverb
    if add_reverb:
        reverb = ReverbProcessor()
        audio = reverb.add_reverb(
            audio, sr=sr,
            room_size=settings["reverb_size"],
            wet_level=settings["reverb_wet"]
        )
    
    # 5. Background music
    if background_music and os.path.exists(background_music):
        mixer = MusicMixer()
        audio = mixer.mix_background_music(
            audio, background_music,
            music_level_db=music_level_db,
            ducking=True,
            sr=sr
        )
    
    # 6. Final normalization to target loudness
    audio = processor.normalize_audio(audio, target_db=target_loudness_db)
    
    # Save
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    processor.save_audio(audio, output_path, sr)
    
    logger.info(f"✓ Mastered audio saved: {output_path}")
    return output_path


def enhance_speech_naturalness(
    input_path: str,
    output_path: str,
    add_breath_sounds: bool = True,
    add_micro_pauses: bool = True
) -> str:
    """
    Enhance speech to sound more natural.
    
    Args:
        input_path: Input audio
        output_path: Output audio
        add_breath_sounds: Add subtle breath sounds
        add_micro_pauses: Add natural micro-pauses
    
    Returns:
        Path to enhanced audio
    """
    # Placeholder for advanced speech enhancement
    # Would include:
    # - Subtle breath sounds between sentences
    # - Natural micro-pauses
    # - Pitch variation
    # - Energy variation
    
    logger.info("Speech naturalness enhancement (placeholder)")
    import shutil
    shutil.copy2(input_path, output_path)
    return output_path


if __name__ == "__main__":
    # Test audio mastering
    logger.setLevel(logging.INFO)
    print("Audio mastering module loaded")
    print("Features: EQ, compression, reverb, de-essing, music mixing")
