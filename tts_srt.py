import os
import re
import subprocess
import asyncio
import edge_tts
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def srt_time_to_seconds(srt_time):
    """Convert SRT timestamp (HH:MM:SS,mmm) to seconds."""
    h, m, s_ms = srt_time.split(":")
    s, ms = s_ms.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

def parse_srt(file_path):
    """Parse SRT file and return a list of dictionaries with start, end, and text."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    
    # Simple regex to split SRT blocks
    blocks = re.split(r'\n\s*\n', content)
    subtitles = []
    
    for block in blocks:
        lines = block.split("\n")
        if len(lines) >= 3:
            # Lines[0] is index, Lines[1] is timestamps, Lines[2:] is text
            time_match = re.match(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})", lines[1])
            if time_match:
                start_time = srt_time_to_seconds(time_match.group(1))
                end_time = srt_time_to_seconds(time_match.group(2))
                text = " ".join(lines[2:]).strip()
                subtitles.append({
                    "start": start_time,
                    "end": end_time,
                    "text": text
                })
    return subtitles

async def generate_tts_audio(text, output_path, voice="ml-IN-SobhanaNeural"):
    """Use Edge TTS to generate high-quality Malayalam audio."""
    print(f"Generating audio for: '{text[:30]}...'")
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"Error generating TTS for '{text[:20]}': {e}")
        return False

async def assemble_audio(subtitles, output_file, temp_dir):
    """Stitch audio segments together with silent gaps using FFmpeg."""
    print("Assembling final audio...")
    
    inputs = []
    filter_complex = ""
    valid_count = 0
    
    # Generate audio segments
    for i, sub in enumerate(subtitles):
        audio_file = temp_dir / f"seg_{i}.mp3"
        if await generate_tts_audio(sub['text'], audio_file):
            inputs.append(f"-i \"{audio_file}\"")
            delay_ms = int(sub['start'] * 1000)
            filter_complex += f"[{valid_count}:a]adelay={delay_ms}|{delay_ms}[a{valid_count}];"
            valid_count += 1
    
    if valid_count == 0:
        print("No audio segments were generated.")
        return

    # Mix all streams
    mix_str = "".join([f"[a{i}]" for i in range(valid_count)])
    filter_complex += f"{mix_str}amix=inputs={valid_count}:duration=longest[out]"
    
    # Full FFmpeg command
    input_str = " ".join(inputs)
    cmd = f"ffmpeg {input_str} -filter_complex \"{filter_complex}\" -map \"[out]\" -y \"{output_file}\""
    
    try:
        # Run subprocess to assemble
        subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Success! Final audio saved to: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error assembling audio: {e}")

async def main():
    downloads_dir = Path("downloads")
    srt_files = [f for f in downloads_dir.iterdir() if f.name.endswith(".ml.srt") and f.is_file()]
    
    if not srt_files:
        print("No Malayalam (.ml.srt) files found in 'downloads/'.")
        return
    
    srt_path = srt_files[0]
    output_audio = srt_path.with_suffix(".mp3").name.replace(".ml.mp3", ".ml_audio.mp3")
    output_path = downloads_dir / output_audio
    
    temp_dir = Path("temp_audio_segments")
    temp_dir.mkdir(exist_ok=True)
    
    try:
        subtitles = parse_srt(srt_path)
        print(f"Found {len(subtitles)} subtitle segments.")
        await assemble_audio(subtitles, output_path, temp_dir)
    finally:
        # Cleanup
        for f in temp_dir.iterdir():
            f.unlink()
        temp_dir.rmdir()

if __name__ == "__main__":
    asyncio.run(main())
