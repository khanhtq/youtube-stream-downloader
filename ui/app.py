"""
Minimalist and Professional GUI for YouTube Stream Downloader
Built with CustomTkinter
"""

import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Any, Dict, Optional

import customtkinter as ctk

from core.config import load_config, save_config
from core.downloader import StreamDownloader
from core.utils import check_ffmpeg, format_seconds_to_time


class App(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Load persisted settings
        self.config = load_config()

        # Window configuration
        self.title("YouTube Stream Downloader")
        self.geometry("860x780")
        self.minsize(780, 680)

        # Apply dark mode theme
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Core downloader instance & thread
        self.downloader = StreamDownloader()
        self.download_thread: Optional[threading.Thread] = None

        # Build UI layout
        self._init_ui()

        # Handle window closing
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _init_ui(self):
        # Main scrollable canvas frame to support all screen resolutions
        self.main_container = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=15)

        # 1. Header Frame
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))

        title_label = ctk.CTkLabel(
            header_frame,
            text="YouTube Stream Downloader",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="A high-performance utility to download YouTube streams & videos with custom time ranges",
            font=ctk.CTkFont(size=12),
            text_color="gray70"
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))

        # FFmpeg status badge
        ffmpeg_ok, ffmpeg_info = check_ffmpeg()
        status_color = "#2ecc71" if ffmpeg_ok else "#e67e22"
        status_text = "● FFmpeg: Ready" if ffmpeg_ok else "▲ FFmpeg: Not found in PATH"
        
        self.ffmpeg_badge = ctk.CTkLabel(
            header_frame,
            text=status_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=status_color
        )
        self.ffmpeg_badge.pack(anchor="e", pady=(0, 0))

        # 2. Section: Video / Stream URL
        url_card = ctk.CTkFrame(self.main_container, corner_radius=8)
        url_card.pack(fill="x", pady=(0, 12), padx=2)

        url_title = ctk.CTkLabel(
            url_card,
            text="1. YouTube Stream or Video URL",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        url_title.pack(anchor="w", padx=15, pady=(12, 6))

        url_input_row = ctk.CTkFrame(url_card, fg_color="transparent")
        url_input_row.pack(fill="x", padx=15, pady=(0, 12))

        self.url_entry = ctk.CTkEntry(
            url_input_row,
            placeholder_text="https://www.youtube.com/live/... or https://www.youtube.com/watch?v=...",
            font=ctk.CTkFont(size=12),
            height=36
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_paste = ctk.CTkButton(
            url_input_row,
            text="Paste",
            width=65,
            height=36,
            command=self._paste_clipboard
        )
        self.btn_paste.pack(side="left", padx=(0, 8))

        self.btn_check = ctk.CTkButton(
            url_input_row,
            text="Check",
            width=85,
            height=36,
            fg_color="#34495e",
            hover_color="#2c3e50",
            command=self._check_url_info
        )
        self.btn_check.pack(side="left")

        # Metadata preview row
        self.info_preview = ctk.CTkLabel(
            url_card,
            text="No video information loaded.",
            font=ctk.CTkFont(size=11),
            text_color="gray60",
            anchor="w"
        )
        self.info_preview.pack(fill="x", padx=15, pady=(0, 10))

        # 3. Section: Time Range Selection
        range_card = ctk.CTkFrame(self.main_container, corner_radius=8)
        range_card.pack(fill="x", pady=(0, 12), padx=2)

        range_title = ctk.CTkLabel(
            range_card,
            text="2. Download Time Range",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        range_title.pack(anchor="w", padx=15, pady=(12, 8))

        self.mode_selector = ctk.CTkSegmentedButton(
            range_card,
            values=["Time Range (Start - End)", "Live Cutoff (-N min)", "Full Download"],
            command=self._on_mode_change
        )
        self.mode_selector.set("Time Range (Start - End)")
        self.mode_selector.pack(fill="x", padx=15, pady=(0, 12))

        # Mode Container: Range
        self.frame_range = ctk.CTkFrame(range_card, fg_color="transparent")
        self.frame_range.pack(fill="x", padx=15, pady=(0, 12))

        lbl_start = ctk.CTkLabel(self.frame_range, text="Start Time:", font=ctk.CTkFont(size=12))
        lbl_start.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=4)

        self.entry_start = ctk.CTkEntry(self.frame_range, placeholder_text="00:00:00 (Empty = Start)", width=180, height=32)
        self.entry_start.grid(row=0, column=1, sticky="w", padx=(0, 20), pady=4)
        self.entry_start.insert(0, "00:00:00")

        lbl_end = ctk.CTkLabel(self.frame_range, text="End Time:", font=ctk.CTkFont(size=12))
        lbl_end.grid(row=0, column=2, sticky="w", padx=(0, 10), pady=4)

        self.entry_end = ctk.CTkEntry(self.frame_range, placeholder_text="01:30:00 (Empty = End)", width=180, height=32)
        self.entry_end.grid(row=0, column=3, sticky="w", pady=4)

        lbl_range_hint = ctk.CTkLabel(
            self.frame_range,
            text="Format: HH:MM:SS (e.g. 01:20:00) or total seconds (e.g. 4800). Leave empty to start from beginning / end.",
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        )
        lbl_range_hint.grid(row=1, column=0, columnspan=4, sticky="w", pady=(4, 0))

        # Mode Container: Cutoff
        self.frame_cutoff = ctk.CTkFrame(range_card, fg_color="transparent")

        lbl_cutoff = ctk.CTkLabel(self.frame_cutoff, text="Cutoff Point:", font=ctk.CTkFont(size=12))
        lbl_cutoff.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=4)

        self.entry_cutoff = ctk.CTkEntry(self.frame_cutoff, placeholder_text="45", width=120, height=32)
        self.entry_cutoff.grid(row=0, column=1, sticky="w", padx=(0, 10), pady=4)
        self.entry_cutoff.insert(0, str(self.config.get("default_cutoff_minutes", 45)))

        lbl_unit = ctk.CTkLabel(self.frame_cutoff, text="minutes before current live head", font=ctk.CTkFont(size=12))
        lbl_unit.grid(row=0, column=2, sticky="w", pady=4)

        lbl_cutoff_hint = ctk.CTkLabel(
            self.frame_cutoff,
            text="Downloads from stream start and stops N minutes prior to the live head.",
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        )
        lbl_cutoff_hint.grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 0))

        # Mode Container: Full
        self.frame_full = ctk.CTkFrame(range_card, fg_color="transparent")
        lbl_full_hint = ctk.CTkLabel(
            self.frame_full,
            text="Downloads the entire stream from start to live head, or the complete video.",
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        )
        lbl_full_hint.pack(anchor="w", pady=(0, 4))

        # 4. Section: Output Directory & Formats
        opt_card = ctk.CTkFrame(self.main_container, corner_radius=8)
        opt_card.pack(fill="x", pady=(0, 12), padx=2)

        opt_title = ctk.CTkLabel(
            opt_card,
            text="3. Output Directory & Format Settings",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        opt_title.pack(anchor="w", padx=15, pady=(12, 8))

        # Output folder row
        folder_row = ctk.CTkFrame(opt_card, fg_color="transparent")
        folder_row.pack(fill="x", padx=15, pady=(0, 10))

        self.out_dir_entry = ctk.CTkEntry(
            folder_row,
            font=ctk.CTkFont(size=12),
            height=34
        )
        self.out_dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.out_dir_entry.insert(0, self.config.get("output_dir", ""))

        btn_browse = ctk.CTkButton(
            folder_row,
            text="Browse...",
            width=110,
            height=34,
            command=self._browse_directory
        )
        btn_browse.pack(side="left", padx=(0, 8))

        btn_open = ctk.CTkButton(
            folder_row,
            text="Open",
            width=60,
            height=34,
            fg_color="#34495e",
            hover_color="#2c3e50",
            command=self._open_output_dir
        )
        btn_open.pack(side="left")

        # Options row (Format, Quality, Threads)
        options_row = ctk.CTkFrame(opt_card, fg_color="transparent")
        options_row.pack(fill="x", padx=15, pady=(0, 12))

        # Format
        lbl_fmt = ctk.CTkLabel(options_row, text="Format:", font=ctk.CTkFont(size=12))
        lbl_fmt.grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        self.fmt_menu = ctk.CTkOptionMenu(
            options_row,
            values=["mkv", "mp4"],
            width=90,
            height=30
        )
        self.fmt_menu.set(self.config.get("format", "mkv"))
        self.fmt_menu.grid(row=0, column=1, sticky="w", padx=(0, 20), pady=4)

        # Quality
        lbl_quality = ctk.CTkLabel(options_row, text="Quality:", font=ctk.CTkFont(size=12))
        lbl_quality.grid(row=0, column=2, sticky="w", padx=(0, 8), pady=4)
        self.quality_menu = ctk.CTkOptionMenu(
            options_row,
            values=["Best (Original)", "1080p", "720p", "480p", "Audio Only (MP3)"],
            width=160,
            height=30
        )
        self.quality_menu.set("Best (Original)")
        self.quality_menu.grid(row=0, column=3, sticky="w", padx=(0, 20), pady=4)

        # Threads
        lbl_threads = ctk.CTkLabel(options_row, text="Threads:", font=ctk.CTkFont(size=12))
        lbl_threads.grid(row=0, column=4, sticky="w", padx=(0, 8), pady=4)
        self.threads_menu = ctk.CTkOptionMenu(
            options_row,
            values=["16 Threads (Max Speed)", "8 Threads", "4 Threads"],
            width=170,
            height=30
        )
        self.threads_menu.set("16 Threads (Max Speed)")
        self.threads_menu.grid(row=0, column=5, sticky="w", pady=4)

        # 5. Section: Action Controls & Progress
        action_card = ctk.CTkFrame(self.main_container, corner_radius=8)
        action_card.pack(fill="x", pady=(0, 12), padx=2)

        action_row = ctk.CTkFrame(action_card, fg_color="transparent")
        action_row.pack(fill="x", padx=15, pady=(12, 10))

        self.btn_download = ctk.CTkButton(
            action_row,
            text="▶ START DOWNLOAD",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self._start_download
        )
        self.btn_download.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_cancel = ctk.CTkButton(
            action_row,
            text="✕ CANCEL",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#c0392b",
            hover_color="#962d22",
            height=40,
            width=110,
            state="disabled",
            command=self._cancel_download
        )
        self.btn_cancel.pack(side="left")

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(action_card, height=12)
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 8))
        self.progress_bar.set(0.0)

        # Stats label
        self.lbl_stats = ctk.CTkLabel(
            action_card,
            text="Ready.",
            font=ctk.CTkFont(size=12),
            text_color="gray70",
            anchor="w"
        )
        self.lbl_stats.pack(fill="x", padx=15, pady=(0, 10))

        # 6. Section: Console Log
        log_card = ctk.CTkFrame(self.main_container, corner_radius=8)
        log_card.pack(fill="both", expand=True, pady=(0, 5), padx=2)

        log_header = ctk.CTkFrame(log_card, fg_color="transparent")
        log_header.pack(fill="x", padx=15, pady=(10, 4))

        lbl_log = ctk.CTkLabel(
            log_header,
            text="Activity Log (Console)",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        lbl_log.pack(side="left")

        btn_clear_log = ctk.CTkButton(
            log_header,
            text="Clear Log",
            width=70,
            height=26,
            fg_color="#34495e",
            hover_color="#2c3e50",
            command=self._clear_log
        )
        btn_clear_log.pack(side="right")

        self.log_textbox = ctk.CTkTextbox(
            log_card,
            font=ctk.CTkFont(family="Consolas", size=11),
            height=130
        )
        self.log_textbox.pack(fill="both", expand=True, padx=15, pady=(0, 12))

    # UI Events & Callbacks
    def _paste_clipboard(self):
        try:
            content = self.clipboard_get()
            if content:
                self.url_entry.delete(0, "end")
                self.url_entry.insert(0, content.strip())
        except Exception:
            pass

    def _browse_directory(self):
        initial = self.out_dir_entry.get().strip() or os.getcwd()
        selected = filedialog.askdirectory(initialdir=initial, title="Select Output Directory")
        if selected:
            self.out_dir_entry.delete(0, "end")
            self.out_dir_entry.insert(0, selected)
            save_config({"output_dir": selected})

    def _open_output_dir(self):
        target_dir = self.out_dir_entry.get().strip()
        if target_dir and os.path.exists(target_dir):
            try:
                os.startfile(target_dir)
            except Exception:
                subprocess.Popen(["explorer", target_dir])
        else:
            messagebox.showwarning("Notice", "Output directory does not exist or has not been selected.")

    def _on_mode_change(self, mode: str):
        self.frame_range.pack_forget()
        self.frame_cutoff.pack_forget()
        self.frame_full.pack_forget()

        if mode == "Time Range (Start - End)":
            self.frame_range.pack(fill="x", padx=15, pady=(0, 12))
        elif mode == "Live Cutoff (-N min)":
            self.frame_cutoff.pack(fill="x", padx=15, pady=(0, 12))
        elif mode == "Full Download":
            self.frame_full.pack(fill="x", padx=15, pady=(0, 12))

    def _append_log(self, text: str):
        def _insert():
            self.log_textbox.insert("end", text + "\n")
            self.log_textbox.see("end")
        self.after(0, _insert)

    def _clear_log(self):
        self.log_textbox.delete("1.0", "end")

    def _check_url_info(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Error", "Please enter a valid YouTube URL.")
            return

        self.info_preview.configure(text="Fetching metadata from YouTube...", text_color="#3498db")
        self.btn_check.configure(state="disabled")

        def _worker():
            try:
                info = self.downloader.get_info(url)
                status = "🔴 LIVE" if info['is_live'] else "🎬 Video/VOD"
                dur = format_seconds_to_time(info['duration']) if info['duration'] else "Live"
                display = f"[{status}] {info['title']} | Channel: {info['uploader']} | Duration: {dur}"
                self.after(0, lambda: self.info_preview.configure(text=display, text_color="#2ecc71"))
                self._append_log(f"-> Metadata fetched: {info['title']} ({status})")
            except Exception as e:
                err_text = f"Failed to fetch metadata: {e}"
                self.after(0, lambda: self.info_preview.configure(text=err_text, text_color="#e74c3c"))
                self._append_log(f"[ERROR] {err_text}")
            finally:
                self.after(0, lambda: self.btn_check.configure(state="normal"))

        threading.Thread(target=_worker, daemon=True).start()

    def _start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Error", "Please enter a valid YouTube URL.")
            return

        out_dir = self.out_dir_entry.get().strip()
        if not out_dir:
            messagebox.showwarning("Error", "Please select an output directory.")
            return

        mode_val = self.mode_selector.get()
        start_time = None
        end_time = None
        cutoff_minutes = 0.0

        if mode_val == "Time Range (Start - End)":
            mode = "range"
            start_time = self.entry_start.get().strip()
            end_time = self.entry_end.get().strip()
        elif mode_val == "Live Cutoff (-N min)":
            mode = "cutoff"
            try:
                cutoff_minutes = float(self.entry_cutoff.get().strip() or 0)
            except ValueError:
                messagebox.showerror("Error", "Cutoff must be a valid number of minutes (e.g. 45).")
                return
        else:
            mode = "full"

        # Quality mapping
        quality_map = {
            "Best (Original)": "best",
            "1080p": "1080",
            "720p": "720",
            "480p": "480",
            "Audio Only (MP3)": "audio"
        }
        quality = quality_map.get(self.quality_menu.get(), "best")

        # Threads mapping
        threads_map = {
            "16 Threads (Max Speed)": 16,
            "8 Threads": 8,
            "4 Threads": 4
        }
        threads = threads_map.get(self.threads_menu.get(), 16)

        format_val = self.fmt_menu.get().lower()

        options = {
            "output_dir": out_dir,
            "mode": mode,
            "start_time": start_time,
            "end_time": end_time,
            "cutoff_minutes": cutoff_minutes,
            "format": format_val,
            "quality": quality,
            "concurrent_fragments": threads
        }

        # Save config
        save_config({
            "output_dir": out_dir,
            "format": format_val,
            "default_cutoff_minutes": cutoff_minutes if cutoff_minutes > 0 else 45
        })

        # Set UI state to downloading
        self.btn_download.configure(state="disabled", text="⏳ DOWNLOADING...")
        self.btn_cancel.configure(state="normal")
        self.progress_bar.set(0.0)
        self.lbl_stats.configure(text="Connecting to stream server...")

        def _on_progress(data: Dict[str, Any]):
            status = data.get("status")
            if status == "downloading":
                pct = data.get("percent", 0.0)
                spd = data.get("speed", "N/A")
                eta = data.get("eta", "N/A")
                f_idx = data.get("fragment_index")
                f_cnt = data.get("fragment_count")
                f_str = f" | Fragments: {f_idx}/{f_cnt}" if f_cnt else ""
                
                self.after(0, lambda: self.progress_bar.set(pct / 100.0))
                self.after(0, lambda: self.lbl_stats.configure(
                    text=f"Progress: {pct:.1f}% | Speed: {spd} | ETA: {eta}{f_str}"
                ))
            elif status == "finished":
                self.after(0, lambda: self.progress_bar.set(1.0))
                self.after(0, lambda: self.lbl_stats.configure(text="Merging video fragments with FFmpeg..."))

        def _worker():
            try:
                success = self.downloader.download(
                    url=url,
                    options=options,
                    progress_callback=_on_progress,
                    log_callback=self._append_log
                )
                if success:
                    self.after(0, lambda: self.progress_bar.set(1.0))
                    self.after(0, lambda: self.lbl_stats.configure(
                        text="✔ DOWNLOAD COMPLETED SUCCESSFULLY!",
                        text_color="#2ecc71"
                    ))
                    self.after(0, lambda: messagebox.showinfo("Success", "Video downloaded and processed successfully!"))
                elif self.downloader.is_cancelled:
                    self.after(0, lambda: self.lbl_stats.configure(
                        text="✕ Download cancelled.",
                        text_color="#e67e22"
                    ))
                else:
                    self.after(0, lambda: self.lbl_stats.configure(
                        text="✕ Download failed. Please check the log.",
                        text_color="#e74c3c"
                    ))
            except Exception as e:
                self._append_log(f"[SYSTEM ERROR] {e}")
                self.after(0, lambda: self.lbl_stats.configure(
                    text=f"Error: {e}",
                    text_color="#e74c3c"
                ))
            finally:
                self.after(0, self._reset_ui_after_download)

        self.download_thread = threading.Thread(target=_worker, daemon=True)
        self.download_thread.start()

    def _cancel_download(self):
        if self.downloader.is_running:
            self.downloader.cancel()
            self._append_log("-> Cancellation signal sent...")
            self.btn_cancel.configure(state="disabled", text="Cancelling...")

    def _reset_ui_after_download(self):
        self.btn_download.configure(state="normal", text="▶ START DOWNLOAD")
        self.btn_cancel.configure(state="disabled", text="✕ CANCEL")

    def _on_close(self):
        if self.downloader.is_running:
            if messagebox.askyesno("Confirm Exit", "A download is currently in progress. Are you sure you want to cancel and exit?"):
                self.downloader.cancel()
                self.destroy()
        else:
            self.destroy()
