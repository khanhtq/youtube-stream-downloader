# YouTube Stream Downloader

A minimalist, high-performance desktop tool and command-line utility for downloading YouTube livestreams and videos with custom time ranges, live-stream head cutoffs, and output directory selection.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/khanhtq/youtube-stream-downloader)

---

## Features

- **Flexible Time Range Selection**:
  - **Start - End Range**: Download specific sections using timestamps (e.g., `00:15:00` to `01:30:00`) or raw seconds.
  - **Live Head Cutoff**: Download live streams from the beginning and automatically stop `N` minutes before the current live head (e.g., `-45` minutes to avoid incomplete or buffering segments).
  - **Full Download**: Download entire streams or uploaded videos from start to finish.
- **Real-Time Livestream Support**:
  - Direct integration with YouTube adaptive fragment generators (`live-from-start`), stopping at the exact target sequence without unnecessary downloads.
  - Automatic fragment retries and download resumption.
- **High-Speed Multi-Threading**:
  - Concurrent fragment downloads (up to 16 parallel threads by default) to saturate network bandwidth.
- **Custom Destination Directory**:
  - Pick any target folder via file dialog or direct input.
  - Automatically persists the last used directory in `config.json`.
  - Quick "Open Folder" button in File Explorer.
- **Minimalist Desktop Interface**:
  - Dark-mode interface built with CustomTkinter.
  - Clear real-time progress indicators: percentage, download speed (MB/s), estimated time remaining (ETA), fragment count, and embedded console log.
- **Command-Line Interface (CLI)**:
  - Comprehensive flags for terminal workflows, automated scripts, or scheduled tasks.

---

## Requirements

1. **Python**: Version 3.10 or higher.
2. **FFmpeg**: Required in system `PATH` for video and audio stream multiplexing.
   - Verify on Windows: Run `ffmpeg -version` in PowerShell or Command Prompt.
   - If not installed, download from [gyan.dev FFmpeg](https://www.gyan.dev/ffmpeg/builds/) or install via `winget install Gyan.FFmpeg`.

---

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/khanhtq/youtube-stream-downloader.git
   cd youtube-stream-downloader
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### 1. Graphical User Interface (GUI)

- **Option A**: Double-click `run.bat` (Windows).
- **Option B**: Run from the terminal:
  ```bash
  python main.py
  ```

#### Steps:
1. Paste the YouTube livestream or video URL into the URL field. Click **Check** to fetch title, channel, and stream status.
2. Select your download mode:
   - **Start - End Range**: Enter start time (e.g., `00:10:00`) and end time (e.g., `01:00:00`). Leave empty to start from beginning or download until the end.
   - **Live Cutoff (-N min)**: Enter minutes to cutoff before the live head (e.g., `45`).
   - **Full**: Download the complete stream or video.
3. Choose the output directory and adjust format (MKV / MP4), quality, or download threads if needed.
4. Click **Start Download**. You can cancel the operation at any time using **Cancel**.

---

### 2. Command-Line Interface (CLI)

Pass CLI arguments directly to `main.py` or `cli.py`:

```bash
# View all available CLI options:
python main.py --help
```

#### Common Examples:

- **Download livestream cutting off 45 minutes before live head:**
  ```bash
  python main.py --cli --url "https://www.youtube.com/live/VIDEO_ID" --cutoff 45 --out-dir "D:/Videos"
  ```

- **Download a segment from 00:15:00 to 01:00:00:**
  ```bash
  python main.py --cli --url "https://www.youtube.com/watch?v=VIDEO_ID" --start 00:15:00 --end 01:00:00 --out-dir "D:/Videos"
  ```

- **Download with 16 parallel threads in MKV format at 1080p quality:**
  ```bash
  python main.py --cli --url "https://www.youtube.com/live/VIDEO_ID" --format mkv --quality 1080 --threads 16
  ```

- **Inspect stream or video metadata without downloading:**
  ```bash
  python main.py --cli --url "https://www.youtube.com/live/VIDEO_ID" --info
  ```

---

## Project Structure

```
youtube-stream-downloader/
├── core/                       # Core downloader engine and utilities
│   ├── __init__.py
│   ├── downloader.py           # StreamDownloader engine, adaptive fragment hook, cancel logic
│   ├── config.py               # User settings persistence (config.json)
│   └── utils.py                # Time parser, byte formatter, FFmpeg verification
├── ui/                         # Minimalist desktop UI
│   ├── __init__.py
│   └── app.py                  # CustomTkinter interface with async worker threads
├── tests/                      # Unit tests
│   └── test_core.py
├── cli.py                      # CLI argument parsing and terminal runner
├── main.py                     # Unified entry point routing to GUI or CLI
├── run.bat                     # Windows one-click launcher
├── requirements.txt            # Dependency list
├── .gitignore                  # Git ignore rules
└── README.md                   # Project documentation
```

---

## License & Disclaimer

This project is released under the MIT License. It is intended for educational purposes and personal archival. Please respect YouTube's Terms of Service and content creators' rights.
