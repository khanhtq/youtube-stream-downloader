"""
YouTube Stream Downloader - Legacy Script Wrapper
Maintained for backwards-compatibility.
"""

import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from core.downloader import StreamDownloader


def download_livestream_cutoff(url, cutoff_minutes=45, out_dir="downloads", merge_format="mkv"):
    """
    Downloads a livestream up to cutoff_minutes before the live head.
    """
    downloader = StreamDownloader()
    options = {
        'mode': 'cutoff',
        'cutoff_minutes': cutoff_minutes,
        'output_dir': out_dir,
        'format': merge_format,
        'concurrent_fragments': 16,
        'quality': 'best'
    }
    return downloader.download(
        url=url,
        options=options,
        log_callback=print
    )


if __name__ == '__main__':
    target_url = "https://www.youtube.com/live/xIzdGai-m1c"
    download_livestream_cutoff(target_url, cutoff_minutes=45)
