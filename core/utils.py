"""
Utility functions for YouTube Stream Downloader
"""

import os
import re
import shutil
from typing import Optional, Tuple


def parse_time_to_seconds(time_str: Optional[str]) -> Optional[int]:
    """
    Parses various time format strings into total seconds.
    Supported formats:
      - "HH:MM:SS" (e.g. "01:23:45")
      - "MM:SS"    (e.g. "23:45")
      - "SS"       (e.g. "45")
      - "1h30m"    (e.g. "1h30m", "45m", "120s")
    Returns:
      Total seconds as integer, or None if input is empty or invalid.
    """
    if not time_str:
        return None

    s = time_str.strip()
    if not s:
        return None

    # Format: 1h30m / 45m / 90s
    pattern_dhms = re.match(r'^(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?\s*(?:(\d+)\s*s)?$', s, re.IGNORECASE)
    if pattern_dhms and any(pattern_dhms.groups()):
        h = int(pattern_dhms.group(1) or 0)
        m = int(pattern_dhms.group(2) or 0)
        sec = int(pattern_dhms.group(3) or 0)
        return h * 3600 + m * 60 + sec

    # Format: HH:MM:SS or MM:SS or SS
    parts = s.split(':')
    try:
        if len(parts) == 3:
            h = int(parts[0])
            m = int(parts[1])
            sec = int(float(parts[2]))
            return h * 3600 + m * 60 + sec
        elif len(parts) == 2:
            m = int(parts[0])
            sec = int(float(parts[1]))
            return m * 60 + sec
        elif len(parts) == 1:
            return int(float(parts[0]))
    except ValueError:
        return None

    return None


def format_seconds_to_time(seconds: Optional[float]) -> str:
    """
    Formats total seconds into HH:MM:SS string.
    """
    if seconds is None or seconds < 0:
        return "00:00:00"
    
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_bytes(bytes_count: Optional[float]) -> str:
    """
    Formats byte count into human readable units (B, KB, MB, GB).
    """
    if not bytes_count or bytes_count <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_idx = 0
    val = float(bytes_count)
    while val >= 1024 and unit_idx < len(units) - 1:
        val /= 1024
        unit_idx += 1
    return f"{val:.2f} {units[unit_idx]}"


def sanitize_filename(filename: str) -> str:
    """
    Removes invalid characters for filesystem paths across Windows/Linux.
    """
    # Replace invalid Windows filename characters: < > : " / \ | ? *
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Strip trailing spaces or dots
    cleaned = cleaned.strip('. ')
    return cleaned or "downloaded_stream"


def check_ffmpeg() -> Tuple[bool, str]:
    """
    Checks if ffmpeg is available in system PATH or local directory.
    Returns: (is_available, path_or_message)
    """
    path = shutil.which("ffmpeg")
    if path:
        return True, path
    return False, "FFmpeg không tìm thấy trong PATH hệ thống."
