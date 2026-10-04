"""
CLI interface for YouTube Stream Downloader
"""

import argparse
import os
import sys
from typing import List, Optional

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from core.downloader import StreamDownloader
from core.utils import check_ffmpeg, format_seconds_to_time
from core.config import load_config


def print_banner():
    banner = """
==========================================================
        YOUTUBE STREAM & VIDEO DOWNLOADER (CLI)
==========================================================
    """
    print(banner)


def run_cli(args_list: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download YouTube Livestreams & Videos with custom time ranges.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  # Download livestream stopping 45 minutes before live head:
  python main.py --cli --url "https://www.youtube.com/live/..." --cutoff 45

  # Download clip from 00:15:00 to 01:00:00:
  python main.py --cli --url "https://www.youtube.com/watch?v=..." --start 00:15:00 --end 01:00:00

  # Inspect stream/video metadata without downloading:
  python main.py --cli --url "https://www.youtube.com/watch?v=..." --info
        """
    )
    parser.add_argument("--cli", action="store_true", help="Run in command-line interface mode (CLI)")
    parser.add_argument("-u", "--url", type=str, help="YouTube stream or video URL")
    parser.add_argument("-s", "--start", type=str, default="", help="Start time (e.g. 00:10:00 or 600)")
    parser.add_argument("-e", "--end", type=str, default="", help="End time (e.g. 01:30:00 or 5400)")
    parser.add_argument("-c", "--cutoff", type=float, default=0, help="Cutoff N minutes before live head (for livestreams)")
    parser.add_argument("-o", "--out-dir", type=str, default="", help="Directory to save downloaded video")
    parser.add_argument("-f", "--format", choices=["mkv", "mp4"], default="mkv", help="Video container format (mkv / mp4)")
    parser.add_argument("-q", "--quality", choices=["best", "1080", "720", "480", "audio"], default="best", help="Video quality")
    parser.add_argument("-t", "--threads", type=int, default=16, help="Number of parallel fragment download threads (default: 16)")
    parser.add_argument("-i", "--info", action="store_true", help="Only check and display stream/video metadata")

    args = parser.parse_args(args_list)

    print_banner()

    ffmpeg_ok, ffmpeg_info = check_ffmpeg()
    if not ffmpeg_ok:
        print(f"[WARNING] {ffmpeg_info}")
        print("-> Recommendation: Install FFmpeg and add to system PATH for proper stream multiplexing.\n")

    cfg = load_config()

    if not args.url:
        # Prompt user interactively if URL was omitted
        try:
            url_input = input("Enter YouTube Stream / Video URL: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            return 1
        if not url_input:
            print("Error: No URL provided.")
            return 1
        args.url = url_input

    downloader = StreamDownloader()

    if args.info:
        print(f"Fetching metadata from: {args.url} ...")
        try:
            info = downloader.get_info(args.url)
            print("-" * 50)
            print(f"Title:         {info['title']}")
            print(f"Channel:       {info['uploader']}")
            print(f"Video ID:      {info['id']}")
            print(f"Is Live:       {'Yes (Livestream)' if info['is_live'] else 'No'}")
            if info.get('duration'):
                print(f"Duration:      {format_seconds_to_time(info['duration'])} ({info['duration']}s)")
            if info.get('current_head_sq'):
                print(f"Live Head SQ:  {info['current_head_sq']}")
            print("-" * 50)
            return 0
        except Exception as e:
            print(f"Error fetching metadata: {e}")
            return 1

    out_dir = args.out_dir or cfg.get("output_dir") or os.getcwd()
    os.makedirs(out_dir, exist_ok=True)

    # Determine mode
    mode = "full"
    if args.cutoff > 0:
        mode = "cutoff"
    elif args.start or args.end:
        mode = "range"

    options = {
        "output_dir": out_dir,
        "mode": mode,
        "start_time": args.start,
        "end_time": args.end,
        "cutoff_minutes": args.cutoff,
        "format": args.format,
        "quality": args.quality,
        "concurrent_fragments": args.threads
    }

    def on_progress(p):
        status = p.get('status')
        if status == 'downloading':
            pct = p.get('percent', 0.0)
            spd = p.get('speed', 'N/A')
            eta = p.get('eta', 'N/A')
            frag_idx = p.get('fragment_index')
            frag_cnt = p.get('fragment_count')
            frag_info = f" | Fragments: {frag_idx}/{frag_cnt}" if frag_cnt else ""
            sys.stdout.write(f"\r[Downloading] {pct:.1f}% | Speed: {spd} | ETA: {eta}{frag_info}    ")
            sys.stdout.flush()
        elif status == 'finished':
            print("\n[Fragments Downloaded] Processing and multiplexing file with FFmpeg...")

    def on_log(msg):
        # yt-dlp internal messages
        print(f"  {msg}")

    try:
        success = downloader.download(
            url=args.url,
            options=options,
            progress_callback=on_progress,
            log_callback=on_log
        )
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\nReceived stop signal (Ctrl+C). Cancelling...")
        downloader.cancel()
        return 130


if __name__ == "__main__":
    sys.exit(run_cli())
