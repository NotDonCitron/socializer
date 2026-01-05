#!/usr/bin/env python3
"""
Video-Optimierungs-Script für Social Media Content
Automatisiert Text-Overlays, Highlights und CTAs nach Socializer Content-Strategie
"""

from pathlib import Path

from moviepy import (
    AudioClip,
    AudioFileClip,
    ColorClip,
    CompositeAudioClip,
    CompositeVideoClip,
    TextClip,
    VideoFileClip,
    concatenate_videoclips,
    vfx,
)
import numpy as np
from kokoro import KModel, KPipeline

# Konfiguration
INPUT_VIDEO = "/home/kek/socializer/export/videos_preview/tool_walkthrough_preview_motion_base.mp4"
OUTPUT_VIDEO = "/home/kek/socializer/export/videos_preview/tool_walkthrough_OPTIMIZED.mp4"
FONT_PATH = Path("/home/kek/socializer/export/fonts/Montserrat-wght.ttf")
VOICEOVER_AUDIO = "/home/kek/socializer/export/videos_preview/tool_walkthrough_OPTIMIZED_voice_kokoro.wav"
VOICEOVER_TEXT = (
    "Save ten hours weekly with AI code review. "
    "Connect data, process instantly, export and automate. "
    "Follow for daily AI insights."
)
VOICEOVER_VOICE = "am_onyx"
VOICEOVER_SPEED = 1.0
VOICEOVER_SILENCE_SEC = 0.12
VOICEOVER_SAMPLE_RATE = 24000
DARK_OVERLAY_OPACITY = 0.28
ZOOM_MAX = 1.08

# Text-Overlays nach Timeline
OVERLAYS = [
    {
        "text": "Save 10 Hours/Week\nWith This AI Tool",
        "start": 0.0,
        "duration": 3.0,
        "fontsize": 60,
        "color": "white",
        "stroke_color": "black",
        "stroke_width": 3,
        "position": ("center", 120),
        "font": "Montserrat-Bold"
    },
    {
        "text": "Manual workflows = wasted time",
        "start": 3.0,
        "duration": 2.0,
        "fontsize": 50,
        "color": "white",
        "stroke_color": "black",
        "stroke_width": 2,
        "position": ("center", 300),
        "font": "Montserrat-Bold"
    },
    {
        "text": "1. Connect your data",
        "start": 5.0,
        "duration": 2.0,
        "fontsize": 45,
        "color": "white",
        "stroke_color": "black",
        "stroke_width": 2,
        "position": ("center", 1600),
        "font": "Montserrat-Bold"
    },
    {
        "text": "2. AI processes instantly",
        "start": 7.0,
        "duration": 2.0,
        "fontsize": 45,
        "color": "#00FF41",  # Neon Green
        "stroke_color": "black",
        "stroke_width": 2,
        "position": ("center", 1600),
        "font": "Montserrat-Bold"
    },
    {
        "text": "3. Export & automate",
        "start": 9.0,
        "duration": 2.0,
        "fontsize": 45,
        "color": "white",
        "stroke_color": "black",
        "stroke_width": 2,
        "position": ("center", 1600),
        "font": "Montserrat-Bold"
    },
    {
        "text": "Follow for daily AI insights →\nLink in bio 🔗",
        "start": 11.0,
        "duration": 3.0,
        "fontsize": 55,
        "color": "#00A3FF",  # Blue CTA
        "stroke_color": "black",
        "stroke_width": 3,
        "position": ("center", 250),
        "font": "Montserrat-Bold"
    }
]


def create_text_overlay(text_config):
    """Erstellt einen Text-Overlay-Clip mit Styling"""
    try:
        font_value = text_config.get("font", "Arial-Bold")
        if font_value == "Montserrat-Bold" and FONT_PATH.exists():
            font_value = str(FONT_PATH)

        txt_clip = TextClip(
            text=text_config["text"],
            font_size=text_config["fontsize"],
            color=text_config["color"],
            font=font_value,
            stroke_color=text_config.get("stroke_color", "black"),
            stroke_width=text_config.get("stroke_width", 2),
            method="caption",
            size=(1000, None),
            text_align="center",
            horizontal_align="center",
            vertical_align="center",
        )

        txt_clip = txt_clip.with_position(text_config["position"])
        txt_clip = txt_clip.with_start(text_config["start"])
        txt_clip = txt_clip.with_duration(text_config["duration"])

        # Fade-in/out Effekte
        txt_clip = txt_clip.with_effects([vfx.CrossFadeIn(0.3), vfx.CrossFadeOut(0.3)])

        return txt_clip
    except Exception as e:
        print(f"⚠️  Font '{text_config.get('font')}' nicht gefunden, verwende Standard-Font")
        # Fallback auf Standard-Font
        txt_clip = TextClip(
            text=text_config["text"],
            font_size=text_config["fontsize"],
            color=text_config["color"],
            stroke_color=text_config.get("stroke_color", "black"),
            stroke_width=text_config.get("stroke_width", 2),
            method="caption",
            size=(1000, None),
            text_align="center",
            horizontal_align="center",
            vertical_align="center",
        )
        txt_clip = txt_clip.with_position(text_config["position"])
        txt_clip = txt_clip.with_start(text_config["start"])
        txt_clip = txt_clip.with_duration(text_config["duration"])
        txt_clip = txt_clip.with_effects([vfx.CrossFadeIn(0.3), vfx.CrossFadeOut(0.3)])
        return txt_clip


def generate_kokoro_voiceover(text: str, output_path: Path) -> None:
    """Generate a Kokoro voiceover WAV file."""
    model = KModel().to("cpu").eval()
    pipeline = KPipeline(lang_code=VOICEOVER_VOICE[0], model=False)
    pack = pipeline.load_voice(VOICEOVER_VOICE)

    chunks = []
    silence = np.zeros(int(VOICEOVER_SAMPLE_RATE * VOICEOVER_SILENCE_SEC), dtype=np.float32)
    for _, ps, _ in pipeline(text, VOICEOVER_VOICE, VOICEOVER_SPEED):
        ref_s = pack[len(ps) - 1]
        audio = model(ps, ref_s, VOICEOVER_SPEED).cpu().numpy()
        chunks.append(audio)
        if VOICEOVER_SILENCE_SEC > 0:
            chunks.append(silence)

    if not chunks:
        raise RuntimeError("Kokoro produced no audio.")
    if VOICEOVER_SILENCE_SEC > 0:
        chunks.pop()

    full_audio = np.concatenate(chunks)

    import wave

    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(VOICEOVER_SAMPLE_RATE)
        pcm = np.clip(full_audio, -1.0, 1.0)
        pcm = (pcm * 32767.0).astype(np.int16)
        wf.writeframes(pcm.tobytes())


def fit_audio_to_video(audio: AudioFileClip, duration: float) -> AudioFileClip:
    """Pad or trim audio to match the video duration."""
    if audio.duration < duration:
        silence = AudioClip(lambda t: 0.0, duration=duration, fps=44100)
        return CompositeAudioClip([silence, audio])
    return audio.subclipped(0, duration)


def create_highlight_circle(center_x, center_y, radius, start_time, duration, color="#FFD700"):
    """
    Erstellt einen animierten Highlight-Circle
    (Vereinfachte Version - für komplexere Shapes nutze ImageClip)
    """
    # Placeholder - würde normalerweise PIL/OpenCV nutzen
    # Für Production: Nutze ImageClip mit vorgerenderten Highlight-Grafiken
    pass


def optimize_video():
    """Hauptfunktion zur Video-Optimierung"""

    print("🎬 Starte Video-Optimierung...")
    print(f"📂 Input: {INPUT_VIDEO}")

    # 1. Lade Original-Video
    video = VideoFileClip(INPUT_VIDEO)
    print(f"✅ Video geladen: {video.duration:.2f}s, {video.size}")

    # 2. Sanfter Zoom + dunkles Overlay für bessere Lesbarkeit
    zoomed = video.with_effects(
        [
            vfx.Resize(lambda t: 1.0 + (ZOOM_MAX - 1.0) * (t / video.duration)),
            vfx.Crop(
                x_center=video.w / 2,
                y_center=video.h / 2,
                width=video.w,
                height=video.h,
            ),
        ]
    )
    dark_overlay = ColorClip(size=video.size, color=(0, 0, 0)).with_opacity(
        DARK_OVERLAY_OPACITY
    )
    dark_overlay = dark_overlay.with_duration(video.duration)

    # 3. Erstelle Text-Overlays
    text_clips = []
    for overlay_config in OVERLAYS:
        try:
            text_clip = create_text_overlay(overlay_config)
            text_clips.append(text_clip)
            print(f"✅ Text-Overlay erstellt: '{overlay_config['text'][:30]}...'")
        except Exception as e:
            print(f"❌ Fehler bei Text-Overlay: {e}")

    # 4. Composite: Video + Overlay + alle Text-Overlays
    final_clips = [zoomed, dark_overlay] + text_clips
    final_video = CompositeVideoClip(final_clips)

    # 5. Voice-over (Kokoro)
    voice_path = Path(VOICEOVER_AUDIO)
    if not voice_path.exists():
        print("🎤 Generiere Kokoro Voice-Over...")
        generate_kokoro_voiceover(VOICEOVER_TEXT, voice_path)

    audio_clip = AudioFileClip(str(voice_path))
    audio_clip = fit_audio_to_video(audio_clip, video.duration)
    final_video = final_video.with_audio(audio_clip)

    # 6. Export
    print(f"💾 Exportiere optimiertes Video nach: {OUTPUT_VIDEO}")
    final_video.write_videofile(
        OUTPUT_VIDEO,
        codec='libx264',
        audio_codec='aac',
        fps=30,
        preset='medium',
        bitrate='5000k'
    )

    print("✅ Video-Optimierung abgeschlossen!")
    print(f"📊 Output: {OUTPUT_VIDEO}")

    # Cleanup
    video.close()
    final_video.close()


def quick_preview():
    """Erstellt eine schnelle Vorschau der ersten 5 Sekunden"""
    video = VideoFileClip(INPUT_VIDEO).subclip(0, 5)
    text_clip = create_text_overlay(OVERLAYS[0])

    preview = CompositeVideoClip([video, text_clip])
    preview_path = OUTPUT_VIDEO.replace(".mp4", "_PREVIEW.mp4")

    preview.write_videofile(preview_path, fps=30)
    print(f"👀 Vorschau erstellt: {preview_path}")

    video.close()
    preview.close()


if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("🎥 SOCIALIZER - Video Content Optimizer")
    print("=" * 60)

    if "--preview" in sys.argv:
        print("📸 Preview-Modus aktiviert")
        quick_preview()
    else:
        optimize_video()

    print("\n✨ Nächste Schritte:")
    print("1. Review das optimierte Video")
    print("2. Füge ggf. manuell Highlights/Circles in CapCut hinzu")
    print("3. Upload zu TikTok/Instagram/YouTube Shorts")
    print("4. Tracke Performance-Metriken")
