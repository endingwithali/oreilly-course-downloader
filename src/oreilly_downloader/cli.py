import argparse
import os
import json
import time
import concurrent.futures
from typing import Optional

from colorama import init, Fore
from tqdm import tqdm
import builtins
import sys

# Route all print statements through tqdm to prevent progress-bar visual corruption
_original_print = builtins.print


def _tqdm_print(*args, sep=" ", end="\n", file=None, flush=False):
    text = sep.join(str(a) for a in args)
    tqdm.write(text, file=file or sys.stdout, end=end)


builtins.print = _tqdm_print

init(autoreset=True)

from .core.browsers import BrowserFactory, IBrowser
from .core.auth import AuthService
from .core.extractor import ExtractorService
from .core.downloader import DownloaderService
from .core.models import Course, Module, Lesson, Video
from .core.utils import PathManager
from .core.vtt import VttProcessor


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


def _handle_authentication(
    driver,
    auth: AuthService,
    email: Optional[str],
    password: Optional[str],
    manual_login: bool,
) -> bool:
    """Handles the authentication flow either manually, via credentials, or via existing session."""
    if manual_login:
        print(Fore.YELLOW + "\n=======================================================")
        print(Fore.YELLOW + "⚠️ MANUAL LOGIN MODE ACTIVE")
        print(Fore.YELLOW + "=======================================================")

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
        return False

    if email and password:
        if not auth.login(email, password):
            print(
                Fore.RED
                + "\n❌ Authentication failed. (Possible CAPTCHA block or invalid credentials)"
            )
            print(
                Fore.YELLOW
                + "👉 Solution: Run 'uv run oreilly-dl --manual-login --browser stealth' to log in yourself safely."
            )
            return False
        return True

    driver.get("https://learning.oreilly.com/home/")
    time.sleep(3)
    if not auth.is_logged_in():
        print(Fore.RED + "\n❌ Error: You are NOT logged in.")
        print(
            Fore.YELLOW
            + "👉 Solution: pass '--email' and '--password', OR use '--manual-login'"
        )
        return False

    return True


def _process_single_video(
    executor: concurrent.futures.ThreadPoolExecutor,
    video: Video,
    vid_idx: int,
    lesson_title: str,
    less_idx: int,
    module_title: str,
    mod_idx: int,
    course_dir: str,
    driver,
    extractor: ExtractorService,
    downloader: DownloaderService,
    transcripts_only: bool,
) -> Optional[concurrent.futures.Future]:
    """Handles extraction and immediate download of a single video. Returns Future if successfully triggered download."""
    vid_file, txt_file = PathManager.get_video_paths(
        course_dir, mod_idx, module_title, less_idx, lesson_title, vid_idx, video.title
    )

    if transcripts_only and os.path.exists(txt_file):
        print(Fore.YELLOW + f"⏩ Skipping {video.title} (transcript extracted)")
        return None
    elif not transcripts_only and os.path.exists(vid_file):
        print(Fore.YELLOW + f"⏩ Skipping {video.title} (video downloaded)")
        return None

    print(f"\n{Fore.CYAN}🎥 Extracting data for: {video.title}")
    print(
        Fore.YELLOW
        + f"📁 Saving to folder: {os.path.basename(os.path.dirname(vid_file))}"
    )

    if transcripts_only:
        print(f"{Fore.MAGENTA}  🚀 Loading transcript page: {video.url}")
        driver.get(video.url)
        time.sleep(3)

        video.transcript = extractor.extract_transcript()
        if video.transcript:
            downloader.save_transcript(video.transcript, txt_file)
            print(Fore.GREEN + f"✅ Transcript extracted.")
        else:
            print(Fore.RED + f"❌ No transcript available.")
        return None
    else:
        # Extracting the m3u8 url
        m3u8 = extractor.extract_m3u8_url(video.url)
        if m3u8:
            video.m3u8_url = m3u8
            video.transcript = extractor.extract_transcript()

            if video.transcript:
                downloader.save_transcript(video.transcript, txt_file)

            print(
                Fore.GREEN
                + f"✅ M3U8 Fetched. Queuing {video.title} for background download..."
            )
            return executor.submit(downloader.download_video, m3u8, vid_file)
        else:
            print(Fore.RED + f"❌ No m3u8 found.")
            return None


def _download_videos_concurrently(
    course: Course,
    driver,
    extractor: ExtractorService,
    downloader: DownloaderService,
    transcripts_only: bool,
    course_dir: str,
):
    """Iterates through the course structure and dispatches video processing with a bounded queue to avoid M3U8 expiration."""

    max_workers = 3
    active_futures = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for mod_idx, module in enumerate(course.modules, 1):
            for less_idx, lesson in enumerate(module.lessons, 1):
                for vid_idx, video in enumerate(lesson.videos, 1):

                    # Bounding the queue: Wait if we already have max_workers active downloads
                    # This prevents scraping 50 M3U8s in advance which lets their CDN tokens expire
                    while len(active_futures) >= max_workers:
                        done, active_futures = concurrent.futures.wait(
                            active_futures,
                            return_when=concurrent.futures.FIRST_COMPLETED,
                        )

                    future = _process_single_video(
                        executor=executor,
                        video=video,
                        vid_idx=vid_idx,
                        lesson_title=lesson.title,
                        less_idx=less_idx,
                        module_title=module.title,
                        mod_idx=mod_idx,
                        course_dir=course_dir,
                        driver=driver,
                        extractor=extractor,
                        downloader=downloader,
                        transcripts_only=transcripts_only,
                    )

                    if future:
                        active_futures.add(future)

        if active_futures and not transcripts_only:
            print(
                f"\n{Fore.CYAN}⏳ Waiting for remaining {len(active_futures)} downloads..."
            )
            concurrent.futures.wait(active_futures)

    print(f"\n{Fore.GREEN}✅ All course videos processed successfully!")


def process_course(
    course_url: str,
    headless: bool = True,
    browser_type: str = "firefox",
    email: Optional[str] = None,
    password: Optional[str] = None,
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

        if not _handle_authentication(driver, auth, email, password, manual_login):
            return

        extractor = ExtractorService(bm)
        downloader = DownloaderService()

        print(Fore.CYAN + "📚 Extracting course structure...")
        structure = extractor.extract_course_structure(course_url)
        if not structure:
            print(Fore.RED + "❌ Failed to extract course structure.")
            return

        course = build_course(structure)
        print(Fore.GREEN + f"✅ Found {len(course.modules)} modules")

        course_dir = PathManager.get_course_dir(downloader.output_dir, course.title)
        os.makedirs(course_dir, exist_ok=True)

        with open(
            os.path.join(course_dir, "course_structure.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(course.structure, f, indent=2)

        _download_videos_concurrently(
            course, driver, extractor, downloader, transcripts_only, course_dir
        )

    finally:
        bm.stop()
        print(f"\n{Fore.MAGENTA}✨ Done! Cleaned up browser.")


def main():
    parser = argparse.ArgumentParser(description="O'Reilly Course Downloader")
    parser.add_argument("url", nargs="?", help="URL of the course")
    parser.add_argument(
        "--on24-vtt",
        help="Direct URL to an ON24 VTT subtitle file to extract a live-event transcript.",
    )
    parser.add_argument(
        "--event-name",
        default="ON24_Live_Event",
        help="Name of the event to save the transcript under.",
    )
    parser.add_argument("--email", help="Login email")
    parser.add_argument("--password", help="Login password")
    parser.add_argument("--transcripts-only", action="store_true")
    parser.add_argument("--manual-login", action="store_true")
    parser.add_argument("--no-headless", action="store_true")
    parser.add_argument(
        "--browser", choices=["firefox", "chrome", "stealth"], default="firefox"
    )

    args = parser.parse_args()

    if args.on24_vtt:
        print(
            Fore.CYAN + f"\n[ON24 Transcript Mode] Processing Event: {args.event_name}"
        )
        vtt_content = VttProcessor.download_vtt(args.on24_vtt)
        if vtt_content:
            captions = VttProcessor.parse_vtt(vtt_content)
            if captions:
                transcript = VttProcessor.format_transcript(captions, args.event_name)
                dl_svc = DownloaderService()
                out_path = os.path.join(
                    dl_svc.output_dir, args.event_name, "full_transcript.txt"
                )
                dl_svc.save_transcript(transcript, out_path)
                print(
                    Fore.GREEN
                    + f"\n✨ Success! Saved standalone transcript to: {out_path}"
                )
        return

    active_headless = False if args.manual_login else not args.no_headless

    if not args.manual_login and not args.url:
        parser.error(
            "The course URL is required unless using --manual-login or --on24-vtt"
        )
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
