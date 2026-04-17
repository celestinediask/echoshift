import yt_dlp
import sys
import os
from tqdm import tqdm

def download_video(url, output_path=None):
    """
    Downloads a YouTube video showing separate progress bars for video and audio.
    """
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    if output_path is None:
        folder_name = "downloads"
        output_path = os.path.join(project_root, folder_name)
    else:
        folder_name = os.path.basename(output_path)
    
    os.makedirs(output_path, exist_ok=True)

    # Use a list to allow the inner hook function to modify the variable
    pbar = [None] 
    downloaded_any = [False]

    def progress_hook(d):
        if d['status'] == 'downloading':
            downloaded_any[0] = True
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            
            if total:
                if pbar[0] is None:
                    # Determine if we are downloading video or audio
                    info = d.get('info_dict', {})
                    vcodec = info.get('vcodec', 'none')
                    acodec = info.get('acodec', 'none')
                    
                    if vcodec != 'none' and acodec == 'none':
                        desc = "Downloading Video"
                    elif vcodec == 'none' and acodec != 'none':
                        desc = "Downloading Audio"
                    else:
                        desc = "Downloading"

                    pbar[0] = tqdm(
                        total=total,
                        unit='B',
                        unit_scale=True,
                        unit_divisor=1024,
                        desc=desc,
                        leave=True
                    )
                
                pbar[0].n = downloaded
                pbar[0].refresh()
        
        elif d['status'] == 'finished':
            if pbar[0]:
                # Ensure the bar reaches 100% and close it
                pbar[0].n = pbar[0].total
                pbar[0].refresh()
                pbar[0].close()
                pbar[0] = None
                print()  # Add a space between bars or before final message

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'keepvideo': True,
        'progress_hooks': [progress_hook],
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first to check if file exists
            info = ydl.extract_info(url, download=False)
            filename = ydl.prepare_filename(info)
            
            # If the final merged file already exists, yt-dlp usually skips.
            # We check manually to decide whether to print the "Starting" messages.
            if os.path.exists(filename):
                print("Video is already downloaded.")
                return

            print(f"Starting download for: {url}")
            print(f"Saving to folder: {folder_name}/")
            print()  # Space before the first progress bar
            
            ydl.download([url])
            
        if downloaded_any[0]:
            print(f"Merging and processing completed successfully!")
            print(f"Files saved in: {folder_name}/")
        else:
            # This case might be reached if yt-dlp skips for other reasons
            print("Video is already downloaded.")
            
    except Exception as e:
        if pbar[0]:
            pbar[0].close()
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python download_youtube.py <YOUTUBE_URL>")
        sys.exit(1)
    
    video_url = sys.argv[1]
    download_video(video_url)
