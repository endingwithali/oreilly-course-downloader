import re
import os

class SanityUtils:
    @staticmethod
    def sanitize_filename(name: str) -> str:
        name = re.sub(r'[<>:"/\\|?*]', '-', name)
        name = name.replace('\n', ' ').replace('\r', '')
        return " ".join(name.split()).strip()

class PathManager:
    @staticmethod
    def get_course_dir(base_dir: str, course_title: str) -> str:
        return os.path.join(base_dir, SanityUtils.sanitize_filename(course_title))

    @staticmethod
    def get_video_paths(course_dir: str, mod_idx: int, mod_title: str, less_idx: int, less_title: str, vid_idx: int, vid_title: str):
        vid_base_dir = os.path.join(
            course_dir,
            f"{mod_idx:02d} - {SanityUtils.sanitize_filename(mod_title)}",
            f"{less_idx:02d} - {SanityUtils.sanitize_filename(less_title)}",
            f"{vid_idx:02d} - {SanityUtils.sanitize_filename(vid_title)}",
        )
        return f"{vid_base_dir}.mp4", f"{vid_base_dir}_transcript.txt"
