import os
import shutil
import urllib.request
import zipfile
import sys

def download_ffmpeg():
    """Download ffmpeg and ffprobe for Windows.
    
    Tries multiple reliable sources with fallback options.
    """
    base_dir = os.path.abspath(os.path.dirname(__file__))
    
    ffmpeg_path = os.path.join(base_dir, "ffmpeg.exe")
    ffprobe_path = os.path.join(base_dir, "ffprobe.exe")
    
    # Skip if already present
    if os.path.exists(ffmpeg_path) and os.path.exists(ffprobe_path):
        print("✓ FFmpeg binaries already present")
        return True
    
    # Multiple download sources in order of preference
    download_sources = [
        # BtbN/FFmpeg-Builds - Reliable, modern builds
        "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
        # Fallback: older but stable static build
        "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.zip",
    ]
    
    print("Downloading ffmpeg and ffprobe...")
    
    for idx, url in enumerate(download_sources, 1):
        try:
            print(f"  Attempting source {idx}/{len(download_sources)}...")
            zip_path = os.path.join(base_dir, "ffmpeg.zip")
            
            # Record existing directories before extraction
            existing_dirs = set(os.listdir(base_dir))
            
            # Download with timeout
            urllib.request.urlretrieve(url, zip_path)
            
            print(f"  Extracting...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(base_dir)
            
            # Find and move the binaries
            found = False
            extracted_folders = []
            for root, dirs, files in os.walk(base_dir):
                if "ffmpeg.exe" in files and "ffprobe.exe" in files:
                    extracted_ffmpeg = os.path.join(root, "ffmpeg.exe")
                    extracted_ffprobe = os.path.join(root, "ffprobe.exe")
                    
                    shutil.move(extracted_ffmpeg, ffmpeg_path)
                    shutil.move(extracted_ffprobe, ffprobe_path)
                    
                    # Track the top-level extracted folder for cleanup
                    # Get the first new directory created at base_dir level
                    rel_path = os.path.relpath(root, base_dir)
                    top_folder = rel_path.split(os.sep)[0]
                    if top_folder != ".":
                        extracted_folders.append(os.path.join(base_dir, top_folder))
                    
                    found = True
                    break
            
            if found:
                # Cleanup: remove only the extracted FFmpeg folders, not all directories
                for folder in set(extracted_folders):
                    if os.path.isdir(folder):
                        shutil.rmtree(folder, ignore_errors=True)
                
                os.remove(zip_path)
                print("✓ FFmpeg setup complete")
                return True
            else:
                raise FileNotFoundError("Could not find ffmpeg.exe or ffprobe.exe in download")
            
        except Exception as e:
            print(f"  ✗ Source {idx} failed: {e}")
            # Clean up failed attempt
            try:
                if os.path.exists(zip_path):
                    os.remove(zip_path)
            except:
                pass
            continue
    
    # All sources failed
    print("\n✗ Failed to download FFmpeg from all sources")
    print("\nAlternative options:")
    print("  1. Install manually from https://ffmpeg.org/download.html")
    print("  2. Use your package manager:")
    print("     - Chocolatey: choco install ffmpeg")
    print("     - Winget: winget install FFmpeg")
    print("  3. Add to PATH and restart the application")
    return False

if __name__ == "__main__":
    success = download_ffmpeg()
    sys.exit(0 if success else 1)
