#!/usr/bin/env python3
"""
Faster-Whisper SRT Converter
=============================
將音訊/影片檔案轉換為 SRT 字幕檔，使用 faster-whisper 語音辨識引擎。
支援模型選擇、進度條顯示、影片自動擷取音訊。

Usage:
    python faster_whisper_srt.py <input_file> [--model MODEL] [--max-chars MAX_CHARS]

Examples:
    python faster_whisper_srt.py demo.mp3
    python faster_whisper_srt.py demo.mp4 --model large-v3-turbo
    python faster_whisper_srt.py demo.wav --max-chars 30

Available Models:
    tiny, tiny.en, base, base.en, small, small.en,
    medium, medium.en, large-v1, large-v2, large-v3, large-v3-turbo
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import warnings
from datetime import timedelta
from pathlib import Path

# Suppress noisy huggingface_hub warnings (symlinks + unauthenticated requests)
# These are harmless for local use and clutter the terminal output.
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore", message=".*symlinks.*")
warnings.filterwarnings("ignore", message=".*unauthenticated.*")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".wma"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv"}
SUPPORTED_EXTENSIONS = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS

VALID_MODELS = [
    "tiny", "tiny.en",
    "base", "base.en",
    "small", "small.en",
    "medium", "medium.en",
    "large-v1", "large-v2", "large-v3",
    "large-v3-turbo",
]

# Estimated model sizes in MB (for download progress estimation)
MODEL_SIZES_MB = {
    "tiny": 75, "tiny.en": 75,
    "base": 145, "base.en": 145,
    "small": 490, "small.en": 490,
    "medium": 1500, "medium.en": 1500,
    "large-v1": 3100, "large-v2": 3100, "large-v3": 3100,
    "large-v3-turbo": 1600,
}

# ---------------------------------------------------------------------------
# Environment Checks
# ---------------------------------------------------------------------------


def check_ffmpeg():
    """Check if FFmpeg is available on the system."""
    if shutil.which("ffmpeg") is None:
        print("[!] FFmpeg is not installed.")
        print("    Windows:  winget install --id Gyan.FFmpeg --source winget")
        print("    macOS:    brew install ffmpeg")
        sys.exit(1)


def check_faster_whisper():
    """Check if faster-whisper is installed."""
    try:
        from faster_whisper import WhisperModel  # noqa: F401
    except ImportError:
        print("[!] faster-whisper is not installed.")
        print("    Install with: pip install faster-whisper")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Audio Helpers
# ---------------------------------------------------------------------------


def get_audio_duration(file_path: str) -> float:
    """Get the duration of an audio file in seconds using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(file_path),
            ],
            capture_output=True,
            text=True,
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def extract_audio_from_video(video_path: str) -> str:
    """Extract audio from a video file and save it as WAV in the same directory. Skip if exists."""
    video_p = Path(video_path)
    output_audio = video_p.with_suffix(".wav")

    if output_audio.exists():
        print(f"[*] Found existing audio file, skipping extraction: {output_audio.name}")
        return str(output_audio)

    print(f"[*] Extracting audio from video: {video_p.name}")
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-i", str(video_path),
                "-vn",                  # no video
                "-acodec", "pcm_s16le", # WAV format
                "-ar", "16000",         # 16kHz (Whisper optimal)
                "-ac", "1",             # mono
                "-y",                   # overwrite
                str(output_audio),
            ],
            capture_output=True,
            check=True,
        )
        print("[+] Audio extraction complete.")
        return str(output_audio)
    except subprocess.CalledProcessError as e:
        print(f"[!] Failed to extract audio: {e.stderr.decode() if e.stderr else e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# SRT Formatting
# ---------------------------------------------------------------------------


def format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)."""
    td = timedelta(seconds=seconds)
    hours = int(td.total_seconds() // 3600)
    minutes = int((td.total_seconds() % 3600) // 60)
    secs = int(td.total_seconds() % 60)
    millis = int((td.total_seconds() % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def split_text_by_chars(text: str, max_chars: int, min_chars: int = 4) -> list:
    """Split text into chunks based on character limit."""
    if len(text) <= max_chars:
        return [text]

    lines = []
    current = ""

    for char in text:
        current += char
        if len(current) >= max_chars:
            lines.append(current)
            current = ""

    if current:
        # Merge short trailing chunk with previous line
        if len(current) < min_chars and lines:
            lines[-1] += current
        else:
            lines.append(current)

    return lines


# ---------------------------------------------------------------------------
# Model Loading with Progress Indicator
# ---------------------------------------------------------------------------


def load_model_with_progress(model_name: str, on_progress_callback=None):
    """
    Load a faster-whisper model with a visual progress indicator.
    
    on_progress_callback: function(str) -> None. If provided, status messages
                          are sent here instead of stdout.
    """
    from faster_whisper import WhisperModel

    msg_init = f"[*] Analyzing model: {model_name}"
    if on_progress_callback:
        on_progress_callback(msg_init)
    else:
        print(msg_init)

    stop_flag = False
    LINE_WIDTH = 80

    def loading_indicator():
        spinner = "|/-\\"
        i = 0
        cache_dir = Path(os.environ.get("USERPROFILE", os.environ.get("HOME", ""))) / ".cache" / "huggingface" / "hub"
        # HF replaces slash and dot in repo names for the cache folder name
        repo_name = f"Systran/faster-whisper-{model_name}".replace("/", "--")
        model_cache_dir = cache_dir / f"models--{repo_name}"
        
        expected_mb = MODEL_SIZES_MB.get(model_name, 0)
        start_size = 0
        
        # Initial size check of the entire hub or specific model dir
        try:
            if model_cache_dir.exists():
                start_size = sum(f.stat().st_size for f in model_cache_dir.glob("**/*") if f.is_file())
        except Exception:
            pass

        while not stop_flag:
            current_size = 0
            try:
                if model_cache_dir.exists():
                    current_size = sum(f.stat().st_size for f in model_cache_dir.glob("**/*") if f.is_file())
            except Exception:
                pass

            delta_mb = (current_size - start_size) / (1024 * 1024)
            msg = ""

            # Check if size is increasing
            if current_size > start_size and delta_mb > 0.1:
                # We are downloading
                if expected_mb > 0:
                    pct = min((current_size / (1024 * 1024)) / expected_mb * 100, 99)
                    msg = f"[*] Downloading... {spinner[i % 4]} {(current_size / (1024*1024)):.0f} / ~{expected_mb} MB ({pct:.0f}%)"
                else:
                    msg = f"[*] Downloading... {spinner[i % 4]} {(current_size / (1024*1024)):.0f} MB"
            else:
                # Not downloading or size hasn't changed (could be extracting/loading)
                msg = f"[*] Loading model... {spinner[i % 4]}"

            if on_progress_callback:
                on_progress_callback(msg)
            else:
                sys.stdout.write(f"\r{msg:<{LINE_WIDTH}}")
                sys.stdout.flush()
            
            time.sleep(0.5)
            i += 1

        if not on_progress_callback:
            sys.stdout.write(f"\r{'':<{LINE_WIDTH}}\r")
            sys.stdout.flush()

    t = threading.Thread(target=loading_indicator, daemon=True)
    t.start()

    try:
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
    except Exception as e:
        stop_flag = True
        raise e
    finally:
        stop_flag = True
        t.join(timeout=1.0)

    success_msg = "[+] Model loaded successfully."
    if on_progress_callback:
         on_progress_callback(success_msg)
    else:
        print(success_msg)
        
    return model


def get_model_path_info(model_name: str):
    """
    Check if model exists in cache and return path info.
    Returns: (is_cached: bool, path_or_msg: str)
    """
    try:
        from huggingface_hub import try_to_load_from_cache
        
        # faster-whisper uses specific repo names
        repo_id = f"Systran/faster-whisper-{model_name}"
        filename = "model.bin" # Check for main model file
        
        # This returns filepath if cached, else None
        cached_path = try_to_load_from_cache(repo_id=repo_id, filename=filename)
        
        if cached_path:
            # Return the folder containing the model
            return True, str(Path(cached_path).parent)
        else:
             # Default cache location prediction
            cache_dir = Path(os.environ.get("USERPROFILE", os.environ.get("HOME", ""))) / ".cache" / "huggingface" / "hub"
            return False, f"{cache_dir} (Will download)"
            
    except ImportError:
        return False, "huggingface_hub not available"
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Core Transcription
# ---------------------------------------------------------------------------


def transcribe_and_build_srt(
    audio_path: str,
    model,
    model_name: str,
    max_chars: int = 40,
    progress_callback=None,
    translator=None,
    target_lang: str = "zho_Hant",
    bilingual: bool = False,
    audio_language: str = "auto",
    use_opencc: bool = True
) -> str:
    """Transcribe audio using a pre-loaded faster-whisper model and return SRT content.
    Optionally translates text if translator is provided.

    progress_callback: function(current_seconds, total_seconds)
    """
    from tqdm import tqdm

    # --- Get duration for progress bar ---
    total_duration = get_audio_duration(audio_path)
    if total_duration <= 0:
        print("[!] Could not determine audio duration. Progress bar will be approximate.")
        total_duration = 1.0

    if progress_callback:
        progress_callback(0, total_duration)

    # --- Determine language and prompt ---
    lang_code = None
    initial_prompt = None
    cc = None

    if audio_language == "zh":
        lang_code = "zh"
    elif audio_language != "auto":
        lang_code = audio_language
        
    if use_opencc or lang_code == "zh":
        initial_prompt = "以下是普通話的字詞。這是一段繁體中文的字幕。"
        
    if use_opencc:
        try:
            import opencc
            # s2twp: Simplified to Traditional (Taiwan Standard) with phrase conversion
            cc = opencc.OpenCC('s2twp')
        except ImportError:
            print("[!] opencc-python-reimplemented not installed. Traditional Chinese forcing may be unreliable.")

    # --- Transcribe with progress ---
    print(f"[*] Transcribing: {Path(audio_path).name}")
    segments_iter, info = model.transcribe(
        audio_path,
        language=lang_code,
        initial_prompt=initial_prompt,
        word_timestamps=False,
        vad_filter=True,
    )

    srt_lines = []
    subtitle_index = 1

    progress_bar = None
    if not progress_callback:
        progress_bar = tqdm(
            total=int(total_duration),
            unit="s",
            desc="Transcribing",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}s [{elapsed}<{remaining}, {rate_fmt}]",
            ncols=80,
        )

    last_pos = 0.0

    for segment in segments_iter:
        text = segment.text.strip()
        if not text:
            continue
            
        # Post-process with OpenCC if forcing Traditional Chinese
        if cc:
            text = cc.convert(text)
            # Standardize Chinese punctuation: use full-width commas
            text = text.replace(",", "，")

        progress = int(segment.end) - int(last_pos)
        if progress > 0:
            if progress_bar:
                progress_bar.update(progress)
            if progress_callback:
                progress_callback(segment.end, total_duration)
            last_pos = segment.end

        # Handle Translation
        translated_text = ""
        if translator:
            # Info.language contains the detected language by whisper
            detected_lang = info.language if info.language else "zh"
            translated_text = translator.translate(text, source_lang=detected_lang, target_lang=target_lang)
            # If translating TO Chinese, also ensure full-width commas
            if target_lang.startswith("zho"):
                translated_text = translated_text.replace(",", "，")

        # Decide what to print based on bilingual setting
        lines = []
        if translator:
            if bilingual:
                # Top line native, bottom line translated, or vice versa. Let's do Orig then Trans
                orig_lines = split_text_by_chars(text, max_chars)
                trans_lines = split_text_by_chars(translated_text, max_chars)
                # Simple zip-like join or just original then translation block
                lines = orig_lines + trans_lines
            else:
                lines = split_text_by_chars(translated_text, max_chars)
        else:
            lines = split_text_by_chars(text, max_chars)

        duration = segment.end - segment.start
        # If bilingual, we don't split the time, we show the whole block for the segment duration
        if bilingual or len(lines) == 1:
            srt_lines.append(f"{subtitle_index}")
            srt_lines.append(
                f"{format_timestamp(segment.start)} --> {format_timestamp(segment.end)}"
            )
            for line in lines:
                 srt_lines.append(line)
            srt_lines.append("")
            subtitle_index += 1
        else:
            time_per_line = duration / len(lines) if lines else duration
            for i, line in enumerate(lines):
                start_time = segment.start + (i * time_per_line)
                end_time = segment.start + ((i + 1) * time_per_line)

                srt_lines.append(f"{subtitle_index}")
                srt_lines.append(
                    f"{format_timestamp(start_time)} --> {format_timestamp(end_time)}"
                )
                srt_lines.append(line)
                srt_lines.append("")

                subtitle_index += 1

    remaining = int(total_duration) - int(last_pos)
    if remaining > 0:
        if progress_bar:
            progress_bar.update(remaining)
        if progress_callback:
            progress_callback(total_duration, total_duration)

    if progress_bar:
        progress_bar.close()

    return "\n".join(srt_lines)


def process_file(
    input_path: Path, 
    model, 
    model_name: str, 
    max_chars: int, 
    progress_callback=None,
    translator=None,
    target_lang: str = "zho_Hant",
    bilingual: bool = False,
    audio_language: str = "auto",
    use_opencc: bool = True
) -> bool:
    """Process a single audio/video file. Returns True on success."""
    ext = input_path.suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        print(f"[!] Skipping {input_path.name}: unsupported format ({ext})")
        return False

    audio_file = str(input_path)

    if ext in VIDEO_EXTENSIONS:
        check_ffmpeg()
        audio_file = extract_audio_from_video(str(input_path))

    srt_content = transcribe_and_build_srt(
        audio_path=audio_file,
        model=model,
        model_name=model_name,
        max_chars=max_chars,
        progress_callback=progress_callback,
        translator=translator,
        target_lang=target_lang,
        bilingual=bilingual,
        audio_language=audio_language
    )

    output_filename = f"{input_path.stem}_{model_name}.srt"
    output_path = input_path.parent / output_filename
    output_path.write_text(srt_content, encoding="utf-8")
    print(f"[+] SRT file created: {output_path}")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Convert audio/video files to SRT subtitles using faster-whisper.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python faster_whisper_srt.py demo.mp3
  python faster_whisper_srt.py a.mp3 b.mp3 c.mp4
  python faster_whisper_srt.py *.mp3 --model large-v3-turbo
  python faster_whisper_srt.py demo.wav --model medium --max-chars 30
        """,
    )
    parser.add_argument(
        "input_files",
        nargs="+",
        help="One or more audio/video files to convert.",
    )
    parser.add_argument(
        "--model",
        default="medium",
        choices=VALID_MODELS,
        help="Whisper model to use (default: medium).",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=40,
        help="Maximum characters per subtitle line (default: 40, minimum: 4).",
    )
    
    # Translation Args
    parser.add_argument(
        "--translate",
        action="store_true",
        help="Enable translation using NLLB-200.",
    )
    parser.add_argument(
        "--target-lang",
        default="zho_Hant",
        help="Target language for translation (BCP-47 tag, default: zho_Hant).",
    )
    parser.add_argument(
        "--bilingual",
        action="store_true",
        help="Output bilingual subtitles (Original + Translated). Requires --translate.",
    )

    # Language Args
    parser.add_argument(
        "--language",
        default="auto",
        help="Input audio language. 'auto' for auto-detect, 'zh' for Chinese, 'en' for English, 'ja' for Japanese.",
    )
    parser.add_argument(
        "--no-opencc",
        action="store_true",
        help="Disable automatic Simplified to Traditional Chinese text conversion.",
    )

    args = parser.parse_args()

    # --- Validate ---
    if args.max_chars < 4:
        print("[!] --max-chars must be at least 4.")
        sys.exit(1)

    check_faster_whisper()

    # --- Collect and validate input files ---
    input_paths = []
    for raw in args.input_files:
        p = Path(raw).resolve()
        if not p.exists():
            print(f"[!] File not found, skipping: {p}")
            continue
        input_paths.append(p)

    if not input_paths:
        print("[!] No valid input files found.")
        sys.exit(1)

    total_files = len(input_paths)

    # --- Load main model once for all files ---
    model = load_model_with_progress(args.model)
    
    # --- Load translation model if enabled ---
    translator = None
    if args.translate:
        try:
            from translation import NLLBTranslator
            translator = NLLBTranslator()
            if not translator.load():
                print("[!] Failed to load translation model. Proceeding without translation.")
                translator = None
        except ImportError:
            print("[!] Translation module not found or missing dependencies (transformers).")
            translator = None

    # --- Process each file ---
    success_count = 0
    for idx, input_path in enumerate(input_paths, 1):
        if total_files > 1:
            print(f"\n[{idx}/{total_files}] Processing: {input_path.name}")
        success = process_file(
            input_path, 
            model, 
            args.model, 
            args.max_chars, 
            translator=translator, 
            target_lang=args.target_lang, 
            bilingual=args.bilingual,
            audio_language=args.language,
            use_opencc=not args.no_opencc
        )
        if success:
            success_count += 1

    # --- Summary (only shown for batch jobs) ---
    if total_files > 1:
        print(f"\n[+] Done! {success_count}/{total_files} files converted successfully.")


if __name__ == "__main__":
    main()

