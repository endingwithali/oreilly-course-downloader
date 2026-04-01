import argparse
import os
from typing import Optional

from colorama import init, Fore, Style

init(autoreset=True)

from .core.browsers import BrowserFactory, IBrowser
from .core.auth import AuthService
from .core.extractor import ExtractorService
from .core.downloader import DownloaderService
from .core.models import Course, Module, Lesson, Video
from .core.utils import SanityUtils


def build_course(structure: dict) -> Course:
    """Builds a Course object from the scraped structure dict."""
    course = Course(title="OReilly Extracted Course", modules=[], structure=structure)
    for mod_name, lessons_dict in structure.items():
        module = Module(title=mod_name, lessons=[])
        for lesson_name, videos_list in lessons_dict.items():
            lesson = Lesson(title=lesson_name, videos=[])
            for v_data in videos_list:
                video = Video(title=v_data["title"], url=v_data["url"])
                lesson.videos.append(video)
            module.lessons.append(lesson)
        course.modules.append(module)
    return course


def process_course(
    course_url: str,
    headless: bool = True,
    browser_type: str = "firefox",
    email: str = None,
    password: str = None,
    manual_login: bool = False,
    transcripts_only: bool = False,
):
    print(Fore.CYAN + "🚀 Initializing browser...")
    bm: IBrowser = BrowserFactory.create(browser_type=browser_type, headless=headless)
    driver = bm.start()
    if not driver:
        print(Fore.RED + "❌ Failed to start browser")
        return

    try:
        auth = AuthService(bm)

        if manual_login:
            print(
                Fore.YELLOW
                + "\n======================================================="
            )
            print(Fore.YELLOW + "⚠️ MANUAL LOGIN MODE ACTIVE")
            print(
                Fore.YELLOW + "======================================================="
            )

            driver.get("https://learning.oreilly.com/accounts/login/")
            print(Fore.CYAN + "\n⏳ Please log in via the newly opened browser window.")
            input(
                Fore.MAGENTA
                + "⏳ ONCE YOU ARE SUCCESSFULLY ON THE HOMEPAGE, press ENTER here to continue..."
            )

            if auth.is_logged_in():
                print(Fore.GREEN + "✅ Confirmed logged in manually. Profile saved!")
            else:
                print(Fore.RED + "⚠️ Warning: Could not detect logged-in state.")
            print(
                Fore.GREEN
                + "✨ Manual setup complete. Please close and run the script normally to download courses."
            )
            return

        # 1. Login if credentials are provided
        elif email and password:
            if not auth.login(email, password):
                print(
                    Fore.RED
                    + "\n❌ Authentication failed. (Possible CAPTCHA block or invalid credentials)"
                )
                print(
                    Fore.YELLOW
                    + "👉 Solution: Run 'uv run oreilly-dl --manual-login --browser stealth' to log in yourself safely."
                )
                return
        else:
            # 1. Start on main site to check if already logged in via profile
            driver.get("https://learning.oreilly.com/home/")
            import time

            time.sleep(3)  # Give it brief time to process session cookies
            if not auth.is_logged_in():
                print(Fore.RED + "\n❌ Error: You are NOT logged in.")
                print(
                    Fore.YELLOW + "👉 Solution: Either pass '--email' and '--password',"
                )
                print(
                    Fore.YELLOW
                    + "   OR run 'uv run oreilly-dl --manual-login --browser stealth' to authenticate once manually."
                )
                return

        extractor = ExtractorService(bm)
        downloader = DownloaderService()

        # 2. Extract structure
        print(Fore.CYAN + "📚 Extracting course structure...")
        structure = extractor.extract_course_structure(course_url)
        if not structure:
            print(Fore.RED + "❌ Failed to extract course structure.")
            return

        course = build_course(structure)
        print(Fore.GREEN + f"✅ Found {len(course.modules)} modules")

        course_dir_name = SanityUtils.sanitize_filename(course.title)
        course_dir_path = os.path.join(downloader.output_dir, course_dir_name)
        os.makedirs(course_dir_path, exist_ok=True)
        import json

        with open(
            os.path.join(course_dir_path, "course_structure.json"),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(course.structure, f, indent=2)

        # 3. Process each video in structure
        for mod_idx, module in enumerate(course.modules, 1):
            mod_title = SanityUtils.sanitize_filename(module.title)

            for less_idx, lesson in enumerate(module.lessons, 1):
                less_title = SanityUtils.sanitize_filename(lesson.title)

                for vid_idx, video in enumerate(lesson.videos, 1):
                    vid_title = SanityUtils.sanitize_filename(video.title)

                    # Constuction matching DownloaderService
                    vid_base_dir = os.path.join(
                        downloader.output_dir,
                        course_dir_name,
                        f"{mod_idx:02d} - {mod_title}",
                        f"{less_idx:02d} - {less_title}",
                        f"{vid_idx:02d} - {vid_title}",
                    )

                    vid_file = f"{vid_base_dir}.mp4"
                    txt_file = f"{vid_base_dir}_transcript.txt"

                    if transcripts_only:
                        if os.path.exists(txt_file):
                            print(
                                Fore.YELLOW
                                + f"⏩ Skipping extraction for {video.title} (transcript already downloaded)"
                            )
                            continue
                    else:
                        if os.path.exists(vid_file):
                            print(
                                Fore.YELLOW
                                + f"⏩ Skipping extraction for {video.title} (video already downloaded)"
                            )
                            continue

                    print(Fore.CYAN + f"\n🎥 Extracting data for: {video.title}")
                    print(
                        Fore.YELLOW
                        + f"   📁 Saving to folder: {os.path.basename(os.path.dirname(vid_base_dir))}"
                    )

                    if transcripts_only:
                        if video.url not in driver.current_url:
                            print(
                                Fore.MAGENTA + f"  🚀 Loading video page: {video.url}"
                            )
                            driver.get(video.url)
                            # Let the browser process the video page load completely
                            import time

                            time.sleep(3)

                        video.transcript = extractor.extract_transcript()
                        if video.transcript:
                            os.makedirs(os.path.dirname(txt_file), exist_ok=True)
                            downloader.save_transcript(video.transcript, txt_file)
                            print(
                                Fore.GREEN
                                + f"   ✅ Transcript extracted and saved in real-time."
                            )
                        else:
                            print(
                                Fore.RED
                                + f"   ❌ No transcript available for {video.title}"
                            )
                    else:
                        # The extractor knows to only load if it's not already on the page
                        m3u8 = extractor.extract_m3u8_url(video.url)
                        if m3u8:
                            video.m3u8_url = m3u8
                            video.transcript = extractor.extract_transcript()

                            os.makedirs(os.path.dirname(vid_file), exist_ok=True)

                            if video.transcript:
                                downloader.save_transcript(video.transcript, txt_file)

                            print(
                                Fore.GREEN
                                + f"   ✅ Playlist and transcript found. Starting video download in real-time..."
                            )
                            downloader._download_video(m3u8, vid_file)
                        else:
                            print(Fore.RED + f"   ❌ No m3u8 found for {video.title}")

    finally:
        bm.stop()
        print(Fore.MAGENTA + "\n✨ Done! Cleaned up browser.")


def main():
    parser = argparse.ArgumentParser(
        description="O'Reilly Course Downloader (Refactored)"
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="URL of the course to download (optional if using --manual-login)",
    )
    parser.add_argument("--email", help="O'Reilly login email")
    parser.add_argument("--password", help="O'Reilly login password")
    parser.add_argument(
        "--transcripts-only",
        action="store_true",
        help="Only download transcripts (skip video downloads)",
    )
    parser.add_argument(
        "--manual-login",
        action="store_true",
        help="Launch an interactive browser to log in and save profile, then exit.",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser in visible mode (default True for --manual-login)",
    )
    parser.add_argument(
        "--browser",
        choices=["firefox", "chrome", "stealth"],
        default="firefox",
        help="Browser to use (default: firefox)",
    )
    args = parser.parse_args()

    if args.manual_login:
        active_headless = False
    else:
        active_headless = not args.no_headless

    if not args.manual_login and not args.url:
        parser.error("The course URL is required unless you are using --manual-login")

    process_course(
        args.url,
        headless=active_headless,
        browser_type=args.browser,
        email=args.email,
        password=args.password,
        manual_login=args.manual_login,
        transcripts_only=args.transcripts_only,
    )


if __name__ == "__main__":
    main()
