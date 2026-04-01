import os
import subprocess
import json
from .utils import SanityUtils

class DownloaderService:
    def __init__(self, output_dir: str = "downloads"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
    def _download_video(self, m3u8_url: str, output_path: str):
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", m3u8_url, "-c", "copy",
            "-bsf:a", "aac_adtstoasc", output_path
        ]
        
        try:
            print(f"Downloading {os.path.basename(output_path)} ...")
            process = subprocess.Popen(
                ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            _, stderr = process.communicate()
            if process.returncode != 0:
                print(f"❌ Error details: {stderr}")
                return False
            print("✅")
            return True
        except Exception as e:
            print(f"Failed to run ffmpeg: {str(e)}")
            return False

    def save_transcript(self, transcript: str, filepath: str):
        if not transcript: return
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(transcript)
        except Exception as e:
            print(f"Failed to save transcript: {e}")

    def download_course(self, course, transcripts_only: bool = False):
        print(f"\n🚀 Starting download for course: {course.title}")
        course_dir = os.path.join(self.output_dir, SanityUtils.sanitize_filename(course.title))
        os.makedirs(course_dir, exist_ok=True)
            
        with open(os.path.join(course_dir, 'course_structure.json'), 'w', encoding='utf-8') as f:
            json.dump(course.structure, f, indent=2)

        for mod_idx, module in enumerate(course.modules, 1):
            mod_title = SanityUtils.sanitize_filename(module.title)
            mod_dir = os.path.join(course_dir, f"{mod_idx:02d} - {mod_title}")
            os.makedirs(mod_dir, exist_ok=True)
                
            for less_idx, lesson in enumerate(module.lessons, 1):
                less_title = SanityUtils.sanitize_filename(lesson.title)
                less_dir = os.path.join(mod_dir, f"{less_idx:02d} - {less_title}")
                os.makedirs(less_dir, exist_ok=True)
                    
                for vid_idx, video in enumerate(lesson.videos, 1):
                    vid_title = SanityUtils.sanitize_filename(video.title)
                    vid_base_path = os.path.join(less_dir, f"{vid_idx:02d} - {vid_title}")
                    vid_file = f"{vid_base_path}.mp4"
                    txt_file = f"{vid_base_path}_transcript.txt"
                    
                    print(f"\nProcessing: {video.title}")
                    if video.transcript:
                        if not os.path.exists(txt_file):
                            self.save_transcript(video.transcript, txt_file)
                            print(f"Saved transcript: {txt_file}")
                            
                    if transcripts_only:
                        continue
                    if not video.m3u8_url:
                        print(f"⚠️ No m3u8 URL found for video, skipping download.")
                        continue
                        
                    if not os.path.exists(vid_file):
                        self._download_video(video.m3u8_url, vid_file)
                    else:
                        print(f"✅ Video already exists: {vid_file}, skipping.")
