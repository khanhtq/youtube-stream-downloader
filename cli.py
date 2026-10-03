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
        description="Tải YouTube Livestream & Video theo khoảng thời gian tùy chọn.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  # Tải livestream cắt lùi 45 phút so với hiện tại:
  python main.py --cli --url "https://www.youtube.com/live/..." --cutoff 45

  # Tải một đoạn từ 00:15:00 đến 01:00:00:
  python main.py --cli --url "https://www.youtube.com/watch?v=..." --start 00:15:00 --end 01:00:00

  # Xem thông tin video/stream mà không tải:
  python main.py --cli --url "https://www.youtube.com/watch?v=..." --info
        """
    )
    parser.add_argument("--cli", action="store_true", help="Chạy chế độ dòng lệnh (CLI)")
    parser.add_argument("-u", "--url", type=str, help="Đường link YouTube (Stream hoặc Video)")
    parser.add_argument("-s", "--start", type=str, default="", help="Thời điểm bắt đầu (ví dụ: 00:10:00 hoặc 600)")
    parser.add_argument("-e", "--end", type=str, default="", help="Thời điểm kết thúc (ví dụ: 01:30:00 hoặc 5400)")
    parser.add_argument("-c", "--cutoff", type=float, default=0, help="Mốc cắt lùi N phút so với live head (cho livestream)")
    parser.add_argument("-o", "--out-dir", type=str, default="", help="Thư mục lưu video tải về")
    parser.add_argument("-f", "--format", choices=["mkv", "mp4"], default="mkv", help="Định dạng video (mkv / mp4)")
    parser.add_argument("-q", "--quality", choices=["best", "1080", "720", "480", "audio"], default="best", help="Chất lượng video")
    parser.add_argument("-t", "--threads", type=int, default=16, help="Số luồng tải song song (mặc định: 16)")
    parser.add_argument("-i", "--info", action="store_true", help="Chỉ kiểm tra và in thông tin video/stream")

    args = parser.parse_args(args_list)

    print_banner()

    ffmpeg_ok, ffmpeg_info = check_ffmpeg()
    if not ffmpeg_ok:
        print(f"[CẢNH BÁO] {ffmpeg_info}")
        print("-> Khuyến nghị: Cần cài đặt FFmpeg và thêm vào PATH hệ thống để ghép video/audio chuẩn xác.\n")

    cfg = load_config()

    if not args.url:
        # Prompt user interactively if URL was omitted
        try:
            url_input = input("Nhập URL YouTube Stream / Video: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nĐã hủy.")
            return 1
        if not url_input:
            print("Lỗi: Bạn chưa nhập URL.")
            return 1
        args.url = url_input

    downloader = StreamDownloader()

    if args.info:
        print(f"Đang lấy thông tin từ: {args.url} ...")
        try:
            info = downloader.get_info(args.url)
            print("-" * 50)
            print(f"Tiêu đề:       {info['title']}")
            print(f"Kênh:          {info['uploader']}")
            print(f"ID Video:      {info['id']}")
            print(f"Đang Live:     {'Có (Livestream)' if info['is_live'] else 'Không'}")
            if info.get('duration'):
                print(f"Thời lượng:    {format_seconds_to_time(info['duration'])} ({info['duration']}s)")
            if info.get('current_head_sq'):
                print(f"Live Head SQ:  {info['current_head_sq']}")
            print("-" * 50)
            return 0
        except Exception as e:
            print(f"Lỗi khi lấy thông tin: {e}")
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
            frag_info = f" | Phân đoạn: {frag_idx}/{frag_cnt}" if frag_cnt else ""
            sys.stdout.write(f"\r[Đang tải] {pct:.1f}% | Tốc độ: {spd} | ETA: {eta}{frag_info}    ")
            sys.stdout.flush()
        elif status == 'finished':
            print("\n[Hoàn tất tải phân đoạn] Đang xử lý và ghép file...")

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
        print("\n\nĐã nhận tín hiệu dừng (Ctrl+C). Đang hủy...")
        downloader.cancel()
        return 130


if __name__ == "__main__":
    sys.exit(run_cli())
