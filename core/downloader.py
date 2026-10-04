"""
StreamDownloader: Robust YouTube Stream & Video Downloader Engine
Supports:
  - Live streams (ongoing or recently finished) with live-from-start
  - Range selection (Start time -> End time)
  - Relative cutoff (-N minutes from current live head)
  - Standard YouTube videos / VODs with section clipping
  - Multi-threaded fragment downloading (high speed)
  - Pause / Cancellation support
"""

import os
import re
import sys
import threading
from typing import Any, Callable, Dict, Optional

import yt_dlp
from yt_dlp.extractor.youtube import YoutubeIE
from yt_dlp.utils import DownloadCancelled

from .utils import parse_time_to_seconds, format_seconds_to_time, format_bytes, sanitize_filename


class DownloaderLogger:
    """Redirects yt-dlp log messages to custom callback."""
    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self.log_callback = log_callback

    def debug(self, msg: str):
        if self.log_callback and not msg.startswith('[debug] '):
            self.log_callback(msg)

    def info(self, msg: str):
        if self.log_callback:
            self.log_callback(msg)

    def warning(self, msg: str):
        if self.log_callback:
            self.log_callback(f"[WARNING] {msg}")

    def error(self, msg: str):
        if self.log_callback:
            self.log_callback(f"[ERROR] {msg}")


class StreamDownloader:
    """High-performance stream & video downloader."""

    def __init__(self):
        self._cancel_event = threading.Event()
        self._is_running = False

    @property
    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()

    @property
    def is_running(self) -> bool:
        return self._is_running

    def cancel(self):
        """Signals download cancellation."""
        self._cancel_event.set()

    def get_info(self, url: str) -> Dict[str, Any]:
        """
        Extracts stream metadata without starting full download.
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'live_from_start': True,
            'extract_flat': False,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        title = info.get('title', 'Unknown Title')
        video_id = info.get('id', '')
        uploader = info.get('uploader') or info.get('channel', 'Unknown Channel')
        duration = info.get('duration')
        is_live = info.get('is_live', False) or info.get('live_status') == 'is_live'
        thumbnail = info.get('thumbnail', '')
        
        # Try to find current fragment count if live
        current_head_sq = None
        frag_duration = 2.0
        try:
            fmts = info.get('requested_formats') or info.get('formats') or [info]
            for fmt in fmts:
                if 'fragments' in fmt and callable(fmt['fragments']):
                    sample_gen = fmt['fragments']({})
                    first_frag = next(sample_gen)
                    current_head_sq = first_frag.get('fragment_count')
                    if current_head_sq:
                        break
        except Exception:
            pass

        return {
            'id': video_id,
            'title': title,
            'uploader': uploader,
            'duration': duration,
            'is_live': is_live,
            'thumbnail': thumbnail,
            'current_head_sq': current_head_sq,
            'frag_duration': frag_duration,
            'raw_info': info
        }

    def download(
        self,
        url: str,
        options: Dict[str, Any],
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        Executes download based on specified options.
        Options:
            - output_dir: str
            - mode: 'range' | 'cutoff' | 'full'
            - start_time: int | str (seconds or HH:MM:SS)
            - end_time: int | str (seconds or HH:MM:SS)
            - cutoff_minutes: float (relative minutes before live head)
            - format: 'mkv' | 'mp4'
            - quality: 'best' | '1080' | '720' | '480' | 'audio'
            - concurrent_fragments: int (default 16)
        """
        self._cancel_event.clear()
        self._is_running = True

        def log(msg: str):
            if log_callback:
                log_callback(msg)

        def emit_progress(data: Dict[str, Any]):
            if progress_callback:
                progress_callback(data)

        orig_adaptive_fragments = YoutubeIE._live_adaptive_fragments
        try:
            log("==================================================")
            log(" STARTING STREAM / VIDEO DOWNLOAD")
            log("==================================================")
            log(f"Target URL: {url}")

            out_dir = options.get('output_dir') or os.getcwd()
            os.makedirs(out_dir, exist_ok=True)
            log(f"Output directory: {out_dir}")

            # 1. Fetch info
            log("Analyzing stream metadata...")
            info_data = self.get_info(url)
            title = info_data['title']
            video_id = info_data['id']
            is_live = info_data['is_live']
            duration = info_data['duration']
            current_head_sq = info_data['current_head_sq']
            frag_duration = info_data['frag_duration']

            log(f"Title: {title}")
            log(f"Channel: {info_data['uploader']}")
            log(f"Status: {'LIVE NOW (Livestream)' if is_live else 'Recorded Video / Ended Stream'}")

            # 2. Parse range/cutoff settings
            mode = options.get('mode', 'range')
            start_sec = parse_time_to_seconds(str(options.get('start_time', ''))) if options.get('start_time') else None
            end_sec = parse_time_to_seconds(str(options.get('end_time', ''))) if options.get('end_time') else None
            cutoff_minutes = float(options.get('cutoff_minutes', 0) or 0)

            # Determine fragment targets for live streams
            target_min_sq = None
            target_max_sq = None

            if is_live:
                if mode == 'cutoff' and cutoff_minutes > 0:
                    if not current_head_sq:
                        log("[NOTICE] Could not automatically obtain live head sequence, using defaults.")
                    else:
                        cutoff_frags = int((cutoff_minutes * 60) / frag_duration)
                        target_max_sq = max(0, current_head_sq - cutoff_frags)
                        target_dur_hours = (target_max_sq * frag_duration) / 3600
                        log(f"-> Cutoff point: -{cutoff_minutes} minutes before current live head.")
                        log(f"-> Stopping at fragment: {target_max_sq} (~{target_dur_hours:.2f} hrs).")
                elif mode == 'range':
                    if start_sec is not None and start_sec > 0:
                        target_min_sq = int(start_sec / frag_duration)
                        log(f"-> Downloading from: {format_seconds_to_time(start_sec)} (Fragment >= {target_min_sq})")
                    if end_sec is not None and end_sec > 0:
                        target_max_sq = int(end_sec / frag_duration)
                        log(f"-> Stopping at: {format_seconds_to_time(end_sec)} (Fragment <= {target_max_sq})")
                else:
                    log("-> Mode: Downloading full live stream.")

                # Hook live adaptive fragments generator
                def custom_fragments(self_ie, vid_id, itag, client_name, live_start_time, url_feed, base_url, f_duration, last_seq_cache, ctx):
                    for frag in orig_adaptive_fragments(self_ie, vid_id, itag, client_name, live_start_time, url_feed, base_url, f_duration, last_seq_cache, ctx):
                        if self._cancel_event.is_set():
                            raise DownloadCancelled("Download was cancelled by user.")

                        sq_match = re.search(r'[?&/]sq[/=](\d+)', frag['url'])
                        if sq_match:
                            sq = int(sq_match.group(1))
                            if target_min_sq is not None and sq < target_min_sq:
                                continue
                            if target_max_sq is not None and sq > target_max_sq:
                                log(f"[Collection Complete] Format {itag} reached fragment {sq} > {target_max_sq}. Stopping feed.")
                                return
                        yield frag

                YoutubeIE._live_adaptive_fragments = custom_fragments
            else:
                # Finished stream or standard video
                if mode == 'range' and (start_sec is not None or end_sec is not None):
                    s_text = format_seconds_to_time(start_sec) if start_sec is not None else "00:00:00"
                    e_text = format_seconds_to_time(end_sec) if end_sec is not None else "End of video"
                    log(f"-> Downloading section: From {s_text} to {e_text}")

            # 3. Quality & format configuration
            quality = options.get('quality', 'best')
            if quality == 'audio':
                fmt_str = 'bestaudio/best'
            elif quality == '1080':
                fmt_str = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
            elif quality == '720':
                fmt_str = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
            elif quality == '480':
                fmt_str = 'bestvideo[height<=480]+bestaudio/best[height<=480]'
            else:
                fmt_str = 'bestvideo+bestaudio/best'

            merge_fmt = options.get('format', 'mkv').lower()
            if merge_fmt not in ['mkv', 'mp4']:
                merge_fmt = 'mkv'

            concurrent_frags = int(options.get('concurrent_fragments', 16))

            out_template = os.path.join(out_dir, '%(title)s [%(id)s].%(ext)s')

            # 4. Progress hook
            def ytdl_progress_hook(d):
                if self._cancel_event.is_set():
                    raise DownloadCancelled("Download was cancelled by user.")

                status = d.get('status')
                if status == 'downloading':
                    frag_idx = d.get('fragment_index')
                    frag_cnt = d.get('fragment_count')
                    dl_bytes = d.get('downloaded_bytes') or 0
                    total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                    speed = d.get('speed')
                    eta = d.get('eta')

                    percent = 0.0
                    if frag_cnt and frag_cnt > 0 and frag_idx:
                        percent = min(100.0, (frag_idx / frag_cnt) * 100.0)
                    elif total_bytes and total_bytes > 0:
                        percent = min(100.0, (dl_bytes / total_bytes) * 100.0)

                    emit_progress({
                        'status': 'downloading',
                        'percent': percent,
                        'fragment_index': frag_idx,
                        'fragment_count': frag_cnt,
                        'speed': f"{format_bytes(speed)}/s" if speed else "N/A",
                        'eta': format_seconds_to_time(eta) if eta is not None else "N/A",
                        'downloaded': format_bytes(dl_bytes),
                        'total': format_bytes(total_bytes) if total_bytes else "N/A"
                    })
                elif status == 'finished':
                    emit_progress({
                        'status': 'finished',
                        'percent': 100.0,
                        'filename': d.get('filename')
                    })

            # 5. Build yt-dlp options
            ydl_opts = {
                'format': fmt_str,
                'outtmpl': out_template,
                'continuedl': True,
                'concurrent_fragment_downloads': concurrent_frags,
                'fragment_retries': 10,
                'skip_unavailable_fragments': True,
                'logger': DownloaderLogger(log_callback=log),
                'progress_hooks': [ytdl_progress_hook],
                'no_warnings': True,
            }

            if quality == 'audio':
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            else:
                ydl_opts['merge_output_format'] = merge_fmt

            if is_live:
                ydl_opts['live_from_start'] = True
            else:
                if mode == 'range' and (start_sec is not None or end_sec is not None):
                    s = start_sec if start_sec is not None else 0
                    e = end_sec if end_sec is not None else float('inf')
                    ydl_opts['download_ranges'] = yt_dlp.utils.download_range_func([], [[s, e]])
                    ydl_opts['force_keyframes_at_cuts'] = True

            log(f"Starting download with {concurrent_frags} parallel threads...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            if self._cancel_event.is_set():
                log("\n[NOTICE] Download was cancelled by user.")
                emit_progress({'status': 'cancelled'})
                return False

            log("\n==================================================")
            log(" DOWNLOAD AND MERGE COMPLETED SUCCESSFULLY!")
            log("==================================================")
            emit_progress({'status': 'completed', 'percent': 100.0})
            return True

        except DownloadCancelled:
            log("\n[CANCELLED] Download task was stopped as requested.")
            emit_progress({'status': 'cancelled'})
            return False
        except Exception as e:
            err_msg = str(e)
            log(f"\n[DOWNLOAD ERROR] {err_msg}")
            emit_progress({'status': 'error', 'error': err_msg})
            return False
        finally:
            YoutubeIE._live_adaptive_fragments = orig_adaptive_fragments
            self._is_running = False
