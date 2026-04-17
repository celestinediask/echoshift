import os
import time
import subprocess
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=api_key)

def convert_to_wav(file_path):
    """Converts the input file to a standard WAV format for better compatibility."""
    output_path = file_path.with_suffix(".temp.wav")
    print(f"Converting {file_path.name} to WAV for processing...")
    
    try:
        subprocess.run(
            ["ffmpeg", "-i", str(file_path), "-ar", "16000", "-ac", "1", str(output_path), "-y"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return output_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg conversion failed: {e}")

def transcribe_file(file_path):
    # Convert to WAV first to ensure compatibility
    wav_path = convert_to_wav(file_path)
    
    try:
        print(f"Uploading: {wav_path.name}...")
        file = genai.upload_file(path=str(wav_path))
        print(f"Uploaded file: {file.name}")

        # Polling for processing state
        while file.state.name == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(5)
            file = genai.get_file(file.name)

        if file.state.name == "FAILED":
            raise ValueError(f"File processing failed for {file.name}")

        print("\nFile processed. Generating transcription with Gemini 2.5 Flash...")

        # Use Gemini 2.5 Flash - standard for high-speed transcription in 2026
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        
        # Prompt for SRT subtitle format
        prompt = (
            "Please provide a high-accuracy, verbatim transcription of this audio in SubRip Subtitle (SRT) format. "
            "Ensure the output follows the standard SRT structure: "
            "1\n00:00:00,000 --> 00:00:00,000\nText here\n\n2\n00:00:00,000 --> 00:00:00,000\nNext text here..."
        )
        
        response = model.generate_content([file, prompt])
        
        # Save the transcription as .srt
        output_path = file_path.with_suffix(".srt")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        
        print(f"Success! SRT subtitle saved to: {output_path}")
        
        # Clean up Gemini file
        genai.delete_file(file.name)
        
    finally:
        # Keep the converted audio file as requested by the user
        # if wav_path.exists():
        #     wav_path.unlink()
        pass

def main():
    downloads_dir = Path("downloads")
    if not downloads_dir.exists():
        print("Error: 'downloads' directory not found.")
        return

    # Supported extensions
    extensions = {".webm", ".mp3", ".wav", ".m4a", ".flac"}
    
    files_to_process = [
        f for f in downloads_dir.iterdir() 
        if f.suffix.lower() in extensions and f.is_file() and not f.name.endswith(".temp.wav")
    ]

    if not files_to_process:
        print("No supported audio files found in 'downloads' folder.")
        return

    if len(files_to_process) > 1:
        print(f"Safety Alert: Found {len(files_to_process)} files in 'downloads'.")
        print("To avoid wasting API usage, please ensure only ONE file is in the folder at a time.")
        for f in files_to_process:
            print(f" - {f.name}")
        return

    # Process the single file
    file_path = files_to_process[0]
    try:
        transcribe_file(file_path)
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()
