import os
import subprocess
import json
from colorama import init, Fore

init(autoreset=True)
from .utils import SanityUtils


class DownloaderService:
    def __init__(self, output_dir: str = "downloads"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def download_video(self, m3u8_url: str, output_path: str) -> bool:
        """Atomic, auto-reconnecting fetch of media files via ffmpeg."""
        temp_output_path = output_path + ".part"
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-user_agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "-reconnect", "1",
            "-reconnect_streamed", "1",
            "-reconnect_delay_max", "5",
            "-i",
            m3u8_url,
            "-c",
            "copy",
            "-bsf:a",
            "aac_adtstoasc",
            "-f",
            "mp4",
            temp_output_path,
        ]

        try:
            print(Fore.CYAN + f"⬇️ Queued & Downloading: {os.path.basename(output_path)} ...")
            process = subprocess.Popen(
                ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            _, stderr = process.communicate()

            if process.returncode != 0:
                print(Fore.RED + f"❌ Error details for {os.path.basename(output_path)}: {stderr}")
                if os.path.exists(temp_output_path):
                    os.remove(temp_output_path)
                return False

            if os.path.exists(temp_output_path):
                os.replace(temp_output_path, output_path)

            print(Fore.GREEN + f"✅ Finished Download: {os.path.basename(output_path)}")
            return True
        except Exception as e:
            print(Fore.RED + f"❌ Failed to run ffmpeg for {os.path.basename(output_path)}: {str(e)}")
            if os.path.exists(temp_output_path):
                os.remove(temp_output_path)
            return False

    def save_transcript(self, transcript: str, filepath: str):
        """Saves a string transcript locally."""
        if not transcript:
            return
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(transcript)
        except Exception as e:
            print(Fore.RED + f"❌ Failed to save transcript: {e}")
