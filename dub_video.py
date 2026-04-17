import os
import subprocess
import sys
from pathlib import Path

def merge_audio_video(video_path, audio_path, output_path):
    """Merge the specified audio and video files using FFmpeg."""
    print(f"Merging Visuals from: {video_path.name}")
    print(f"With Audio from: {audio_path.name}")
    
    # Check if the video path actually has a video stream
    # Some youtube-dl downloads split them.
    cmd = [
        "ffmpeg", "-i", str(video_path), "-i", str(audio_path),
        "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0",
        "-shortest", "-y", str(output_path)
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Success! Dubbed video saved to: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error merging video and audio: {e}")
        # If mapping fails, it might be because the first input has no video
        if "Stream map" in e.stderr:
             print("TIP: The input file chosen as 'video' does not seem to contain a video stream.")
             print("FFmpeg Details:")
             print(e.stderr)

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ["source", "target"]:
        print("Usage: python dub_video.py [source|target]")
        return

    mode = sys.argv[1]
    downloads_dir = Path("downloads")
    
    # 1. Locate the TTS audio file
    if mode == "target":
        audio_files = [f for f in downloads_dir.iterdir() if f.name.endswith(".ml_audio.mp3")]
        tag = "_ml_dubbed.mp4"
    else:
        audio_files = [f for f in downloads_dir.iterdir() if f.name.endswith(".en_audio.mp3")]
        tag = "_en_dubbed.mp4"

    if not audio_files:
        print(f"No {mode} audio file found.")
        return
    
    audio_path = audio_files[0]
    
    # 2. Locate the VIDEO file
    # We look for the largest file that matches the base name (usually the video stream)
    base_parts = audio_path.name.split('.')
    search_pattern = base_parts[0] # The main title
    
    potential_videos = [
        f for f in downloads_dir.iterdir() 
        if search_pattern in f.name and f.suffix in {".mp4", ".webm"}
        and "_dubbed" not in f.name and "_audio" not in f.name
    ]
    
    if not potential_videos:
        print("No matching video files found.")
        return

    # Sort by size to get the actual video file (video > audio only)
    video_path = sorted(potential_videos, key=lambda x: x.stat().st_size, reverse=True)[0]
    
    output_path = downloads_dir / (video_path.stem + tag)
    
    merge_audio_video(video_path, audio_path, output_path)

if __name__ == "__main__":
    main()
