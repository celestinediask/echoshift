import os
import re
import subprocess
import asyncio
import sys
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
    """Parse SRT file robustly, handling AI timestamp hallucinations."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    
    subtitles = []
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
            
        if line.isdigit():
            if i + 1 < len(lines) and '-->' in lines[i+1]:
                ts_line = lines[i+1]
                
                text_lines = []
                j = i + 2
                while j < len(lines):
                    if lines[j].strip().isdigit():
                        if j + 1 < len(lines) and '-->' in lines[j+1]:
                            break
                    text_lines.append(lines[j].strip())
                    j += 1
                
                text = " ".join([t for t in text_lines if t])
                
                parts = ts_line.split('-->')
                if len(parts) == 2:
                    start_str = parts[0].strip()
                    end_str = parts[1].strip()
                    
                    def to_seconds(ts):
                        ts = re.sub(r':(\d{3})$', r',\1', ts)
                        pts = re.split(r'[:,]', ts)
                        if len(pts) == 4:
                            return int(pts[0])*3600 + int(pts[1])*60 + int(pts[2]) + int(pts[3])/1000
                        elif len(pts) == 3:
                            return int(pts[0])*60 + int(pts[1]) + int(pts[2])/1000
                        return 0
                            
                    start_sec = to_seconds(start_str)
                    end_sec = to_seconds(end_str)
                    
                    subtitles.append({
                        "start": start_sec,
                        "end": end_sec,
                        "text": text
                    })
                i = j
            else:
                i += 1
        else:
            i += 1
            
    return subtitles

async def generate_tts_audio(text, output_path, voice):
    """Use Edge TTS to generate high-quality audio."""
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"Error generating TTS for '{text[:20]}': {e}")
        return False

def get_audio_duration(file_path):
    try:
        res = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(file_path)], capture_output=True, text=True)
        return float(res.stdout.strip())
    except:
        return 0.0

async def assemble_audio(subtitles, output_file, temp_dir, voice):
    """Stitch audio segments together with silent gaps using FFmpeg, preventing overlaps."""
    print(f"Assembling final audio using voice: {voice}...")
    
    inputs = []
    filter_complex = ""
    valid_count = 0
    
    # Generate audio segments
    for i, sub in enumerate(subtitles):
        audio_file = temp_dir / f"seg_{i}.mp3"
        if await generate_tts_audio(sub['text'], audio_file, voice=voice):
            inputs.append(f"-i \"{audio_file}\"")
            
            # Calculate allowed duration before next subtitle
            if i + 1 < len(subtitles):
                allowed_dur = subtitles[i+1]['start'] - sub['start']
            else:
                allowed_dur = sub['end'] - sub['start']
                
            allowed_dur = max(allowed_dur - 0.1, 0.5) # small buffer
            
            actual_dur = get_audio_duration(audio_file)
            delay_ms = int(sub['start'] * 1000)
            
            if actual_dur > allowed_dur and allowed_dur > 0:
                ratio = min(actual_dur / allowed_dur, 1.45) # cap speedup at 1.45x
                filter_complex += f"[{valid_count}:a]atempo={ratio},adelay={delay_ms}|{delay_ms}[a{valid_count}];"
            else:
                filter_complex += f"[{valid_count}:a]adelay={delay_ms}|{delay_ms}[a{valid_count}];"
                
            valid_count += 1
        print(".", end="", flush=True)
    
    print("\nMixing tracks...")
    if valid_count == 0:
        print("No audio segments were generated.")
        return

    # Mix all streams without normalizing/lowering volume
    mix_str = "".join([f"[a{i}]" for i in range(valid_count)])
    filter_complex += f"{mix_str}amix=inputs={valid_count}:duration=longest:dropout_transition=0:normalize=0[out]"
    
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
    if len(sys.argv) < 2 or sys.argv[1] not in ["source", "target"]:
        print("Usage: python tts_srt.py [source|target]")
        print("  source: Use the original English SRT")
        print("  target: Use the translated Malayalam (.ml.srt) SRT")
        return

    mode = sys.argv[1]
    downloads_dir = Path("downloads")
    
    if mode == "target":
        srt_files = [f for f in downloads_dir.iterdir() if f.name.endswith(".ml.srt") and f.is_file()]
        voice = "ml-IN-SobhanaNeural" # Default fallback
        # Check for detected gender
        gender_file = downloads_dir / "gender.txt"
        if gender_file.exists():
            with open(gender_file, "r") as f:
                detected_gender = f.read().strip()
                if detected_gender == "MALE":
                    voice = "ml-IN-MidhunNeural"
        output_suffix = ".ml_audio.mp3"
    else:
        # source: find files ending in .srt but NOT .ml.srt
        srt_files = [
            f for f in downloads_dir.iterdir() 
            if f.suffix.lower() == ".srt" and not f.name.endswith(".ml.srt") and f.is_file()
        ]
        voice = "en-US-GuyNeural" # Default fallback
        # Check for detected gender
        gender_file = downloads_dir / "gender.txt"
        if gender_file.exists():
            with open(gender_file, "r") as f:
                detected_gender = f.read().strip()
                if detected_gender == "FEMALE":
                    voice = "en-US-JennyNeural"
        output_suffix = ".en_audio.mp3"

    if not srt_files:
        print(f"No {mode} SRT files found in 'downloads/'.")
        return
    
    if len(srt_files) > 1:
        print(f"Safety Alert: Found {len(srt_files)} {mode} SRT files. Please keep only ONE in 'downloads/'.")
        return

    srt_path = srt_files[0]
    # Name the output audio based on the original base name
    output_name = srt_path.name.replace(".ml.srt", "").replace(".srt", "") + output_suffix
    output_path = downloads_dir / output_name
    
    temp_dir = Path("temp_audio_segments")
    temp_dir.mkdir(exist_ok=True)
    
    try:
        subtitles = parse_srt(srt_path)
        print(f"Found {len(subtitles)} subtitle segments for {mode} audio.")
        await assemble_audio(subtitles, output_path, temp_dir, voice=voice)
    finally:
        # Cleanup
        for f in temp_dir.iterdir():
            f.unlink()
        if temp_dir.exists():
            temp_dir.rmdir()

if __name__ == "__main__":
    asyncio.run(main())
