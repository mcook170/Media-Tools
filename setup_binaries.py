import os
import shutil
import urllib.request
import zipfile
import tempfile
from pathlib import Path


DOWNLOAD_SOURCES = [
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
    "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.zip",
]


def download_ffmpeg(target_dir: Path) -> bool:
    """
    Downloads ffmpeg.exe and ffprobe.exe into target_dir.
    Intended for development setup, not runtime use.
    """

    target_dir.mkdir(parents=True, exist_ok=True)

    ffmpeg_path = target_dir / "ffmpeg.exe"
    ffprobe_path = target_dir / "ffprobe.exe"

    if ffmpeg_path.exists() and ffprobe_path.exists():
        print("✓ FFmpeg already present")
        return True

    print("Downloading FFmpeg...")

    for idx, url in enumerate(DOWNLOAD_SOURCES, start=1):
        print(f"  Attempt {idx}/{len(DOWNLOAD_SOURCES)}")

        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_dir = Path(tmp_dir)
                zip_path = tmp_dir / "ffmpeg.zip"

                # Download
                urllib.request.urlretrieve(url, zip_path)

                # Extract
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(tmp_dir)

                # Locate binaries
                ffmpeg_file = next(tmp_dir.rglob("ffmpeg.exe"), None)
                ffprobe_file = next(tmp_dir.rglob("ffprobe.exe"), None)

                if not ffmpeg_file or not ffprobe_file:
                    raise FileNotFoundError("FFmpeg binaries not found in archive")

                # Copy to target directory
                shutil.copy2(ffmpeg_file, ffmpeg_path)
                shutil.copy2(ffprobe_file, ffprobe_path)

                print("✓ FFmpeg setup complete")
                return True

        except Exception as e:
            print(f"  ✗ Source failed: {e}")

    print("\n✗ Failed to download FFmpeg from all sources.")
    return False


if __name__ == "__main__":
    project_root = Path(__file__).parent
    third_party_dir = project_root / "third_party" / "ffmpeg"

    success = download_ffmpeg(third_party_dir)
    raise SystemExit(0 if success else 1)