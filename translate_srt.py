import os
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

def translate_srt(file_path, target_lang="Malayalam"):
    print(f"Translating: {file_path.name} to {target_lang}...")
    
    # Read the original SRT content
    with open(file_path, "r", encoding="utf-8") as f:
        srt_content = f.read()

    # Use Gemini 2.5 Flash for accurate and fast translation
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    
    # Prompt for translation while preserving SRT structure
    prompt = (
        f"You are a professional dubbing adapter and translator. Translate the following SRT subtitle text into {target_lang}. "
        "CRITICAL INSTRUCTIONS: "
        "1. Keep all timestamps, indices, and SRT formatting exactly the same. Do not translate indices or timestamps. "
        "2. ADAPTATION: The translated text must take the exact same amount of time to speak out loud as the original English. "
        f"{target_lang} usually takes longer to say than English. You MUST summarize and adapt the phrasing so it is short, concise, and naturally matches the original lip-sync timing. Avoid overly formal or wordy translations. "
        "3. Maintain the exact line structure.\n\n"
        f"Here is the content:\n\n{srt_content}"
    )
    
    try:
        response = model.generate_content(prompt)
        
        # Save the translated SRT
        # Naming convention: original_name.ml.srt
        output_path = file_path.with_suffix(".ml.srt")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        
        print(f"Success! Translated SRT saved to: {output_path}")
    except Exception as e:
        print(f"Error during translation: {e}")

def main():
    downloads_dir = Path("downloads")
    if not downloads_dir.exists():
        print("Error: 'downloads' directory not found.")
        return

    # Look for standard SRT files, but ignore already translated ones (.ml.srt)
    srt_files = [
        f for f in downloads_dir.iterdir() 
        if f.suffix.lower() == ".srt" and not f.name.endswith(".ml.srt") and f.is_file()
    ]

    if not srt_files:
        print("No source SRT files found in 'downloads' folder.")
        return

    if len(srt_files) > 1:
        print(f"Safety Alert: Found {len(srt_files)} SRT files.")
        print("To avoid wasting API usage, please ensure only ONE source SRT file is in the folder at a time.")
        for f in srt_files:
            print(f" - {f.name}")
        return

    # Process the single file
    file_path = srt_files[0]
    translate_srt(file_path, target_lang="Malayalam")

if __name__ == "__main__":
    main()
