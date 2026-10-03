import sys
import os
import re
import time

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import yt_dlp
from yt_dlp.extractor.youtube import YoutubeIE

def download_livestream_cutoff(url, cutoff_minutes=45, out_dir="g:/tmp/domixi", merge_format="mkv"):
    print("==================================================")
    print(" BẮT ĐẦU TẢI LIVESTREAM YOUTUBE (TỰ ĐỘNG CẮT)")
    print("==================================================")
    print(f"URL: {url}")
    print(f"Mốc cắt: -{cutoff_minutes} phút so với hiện tại\n")

    # 1. Trích xuất thông tin livestream
    print("Đang lấy thông tin luồng phát...")
    ydl_info_opts = {
        'live_from_start': True,
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_info_opts) as ydl:
        info = ydl.extract_info(url, download=False, process=True)

    title = info.get('title', 'livestream')
    video_id = info.get('id', 'video')
    print(f"Tiêu đề: {title}")
    print(f"Video ID: {video_id}")

    # Lấy sequence hiện tại ở live head
    fmts = info.get('requested_formats') or [info]
    sample_gen = fmts[0]['fragments']({})
    first_frag = next(sample_gen)
    current_head_sq = first_frag.get('fragment_count')

    if not current_head_sq:
        print("Lỗi: Không lấy được fragment_count từ luồng phát.")
        sys.exit(1)

    frag_duration = 2.0  # Mỗi fragment kéo dài 2 giây
    cutoff_frags = int((cutoff_minutes * 60) / frag_duration)
    target_max_sq = max(0, current_head_sq - cutoff_frags)

    total_duration_hours = (current_head_sq * frag_duration) / 3600
    target_duration_hours = (target_max_sq * frag_duration) / 3600

    print(f"-> Thời lượng livestream hiện tại: ~{total_duration_hours:.2f} giờ ({current_head_sq} fragments)")
    print(f"-> Mốc -{cutoff_minutes} phút: ~{target_duration_hours:.2f} giờ (Dừng tại fragment: {target_max_sq})")
    print(f"-> Tổng thời lượng video tải về: ~{(target_max_sq * frag_duration)/60:.1f} phút")
    print("-> Sẽ tiếp tục tải từ các phân đoạn đã có sẵn (resume)...")

    # 2. Hook generator phân đoạn để ngắt tại mốc target_max_sq
    orig_func = YoutubeIE._live_adaptive_fragments
    def custom_fragments(self, vid_id, itag, client_name, live_start_time, url_feed, base_url, f_duration, last_seq_cache, ctx):
        for frag in orig_func(self, vid_id, itag, client_name, live_start_time, url_feed, base_url, f_duration, last_seq_cache, ctx):
            sq_match = re.search(r'[?&/]sq[/=](\d+)', frag['url'])
            if sq_match:
                sq = int(sq_match.group(1))
                if sq > target_max_sq:
                    print(f"\n[Hoàn tất thu thập] Format {itag} đã đạt mốc fragment {sq} > {target_max_sq} (-{cutoff_minutes}m). Dừng nạp thêm.")
                    return
            yield frag

    YoutubeIE._live_adaptive_fragments = custom_fragments

    # 3. Cấu hình tải đa luồng
    out_template = os.path.join(out_dir, '%(title)s [%(id)s].%(ext)s')
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'live_from_start': True,
        'continuedl': True,
        'outtmpl': out_template,
        'merge_output_format': merge_format,
        'concurrent_fragment_downloads': 16,  # 16 luồng song song để tải tốc độ tối đa
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
    }

    print("\nĐang tải các phân đoạn với 16 luồng song song...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    print("\n==================================================")
    print(" ĐÃ TẢI XONG VÀ GHÉP FILE THÀNH CÔNG!")
    print("==================================================")

if __name__ == '__main__':
    target_url = "https://www.youtube.com/live/xIzdGai-m1c"
    download_livestream_cutoff(target_url, cutoff_minutes=45)
