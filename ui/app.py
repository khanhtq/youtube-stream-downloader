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
            text="Công cụ tải livestream & video theo khoảng thời gian tùy chọn (Hỗ trợ cắt lùi live stream)",
            font=ctk.CTkFont(size=12),
            text_color="gray70"
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))

        # FFmpeg status badge
        ffmpeg_ok, ffmpeg_info = check_ffmpeg()
        status_color = "#2ecc71" if ffmpeg_ok else "#e67e22"
        status_text = "● FFmpeg: Sẵn sàng" if ffmpeg_ok else "▲ FFmpeg: Chưa có trong PATH"
        
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
            text="1. Đường dẫn Stream hoặc Video YouTube",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        url_title.pack(anchor="w", padx=15, pady=(12, 6))

        url_input_row = ctk.CTkFrame(url_card, fg_color="transparent")
        url_input_row.pack(fill="x", padx=15, pady=(0, 12))

        self.url_entry = ctk.CTkEntry(
            url_input_row,
            placeholder_text="https://www.youtube.com/live/... hoặc https://www.youtube.com/watch?v=...",
            font=ctk.CTkFont(size=12),
            height=36
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_paste = ctk.CTkButton(
            url_input_row,
            text="Dán",
            width=65,
            height=36,
            command=self._paste_clipboard
        )
        self.btn_paste.pack(side="left", padx=(0, 8))

        self.btn_check = ctk.CTkButton(
            url_input_row,
            text="Kiểm tra",
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
            text="Chưa có thông tin video.",
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
            text="2. Khoảng thời gian muốn tải",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        range_title.pack(anchor="w", padx=15, pady=(12, 8))

        self.mode_selector = ctk.CTkSegmentedButton(
            range_card,
            values=["Khoảng thời gian (Start - End)", "Cắt lùi Live (-N phút)", "Tải toàn bộ (Full)"],
            command=self._on_mode_change
        )
        self.mode_selector.set("Khoảng thời gian (Start - End)")
        self.mode_selector.pack(fill="x", padx=15, pady=(0, 12))

        # Mode Container: Range
        self.frame_range = ctk.CTkFrame(range_card, fg_color="transparent")
        self.frame_range.pack(fill="x", padx=15, pady=(0, 12))

        lbl_start = ctk.CTkLabel(self.frame_range, text="Bắt đầu từ:", font=ctk.CTkFont(size=12))
        lbl_start.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=4)

        self.entry_start = ctk.CTkEntry(self.frame_range, placeholder_text="00:00:00 (Trống = Từ đầu)", width=180, height=32)
        self.entry_start.grid(row=0, column=1, sticky="w", padx=(0, 20), pady=4)
        self.entry_start.insert(0, "00:00:00")

        lbl_end = ctk.CTkLabel(self.frame_range, text="Dừng lại tại:", font=ctk.CTkFont(size=12))
        lbl_end.grid(row=0, column=2, sticky="w", padx=(0, 10), pady=4)

        self.entry_end = ctk.CTkEntry(self.frame_range, placeholder_text="01:30:00 (Trống = Đến hết)", width=180, height=32)
        self.entry_end.grid(row=0, column=3, sticky="w", pady=4)

        lbl_range_hint = ctk.CTkLabel(
            self.frame_range,
            text="💡 Hỗ trợ định dạng: HH:MM:SS (ví dụ 01:20:00) hoặc số giây (ví dụ 4800). Để trống = từ đầu / đến hết.",
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        )
        lbl_range_hint.grid(row=1, column=0, columnspan=4, sticky="w", pady=(4, 0))

        # Mode Container: Cutoff
        self.frame_cutoff = ctk.CTkFrame(range_card, fg_color="transparent")

        lbl_cutoff = ctk.CTkLabel(self.frame_cutoff, text="Mốc cắt lùi:", font=ctk.CTkFont(size=12))
        lbl_cutoff.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=4)

        self.entry_cutoff = ctk.CTkEntry(self.frame_cutoff, placeholder_text="45", width=120, height=32)
        self.entry_cutoff.grid(row=0, column=1, sticky="w", padx=(0, 10), pady=4)
        self.entry_cutoff.insert(0, str(self.config.get("default_cutoff_minutes", 45)))

        lbl_unit = ctk.CTkLabel(self.frame_cutoff, text="phút so với thời điểm Live hiện tại", font=ctk.CTkFont(size=12))
        lbl_unit.grid(row=0, column=2, sticky="w", pady=4)

        lbl_cutoff_hint = ctk.CTkLabel(
            self.frame_cutoff,
            text="💡 Tải từ đầu luồng và dừng tại mốc trước thời điểm hiện tại N phút (như cấu hình gốc của dự án).",
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        )
        lbl_cutoff_hint.grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 0))

        # Mode Container: Full
        self.frame_full = ctk.CTkFrame(range_card, fg_color="transparent")
        lbl_full_hint = ctk.CTkLabel(
            self.frame_full,
            text="💡 Tải toàn bộ nội dung stream từ đầu đến thời điểm hiện tại hoặc toàn bộ video hoàn chỉnh.",
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        )
        lbl_full_hint.pack(anchor="w", pady=(0, 4))

        # 4. Section: Output Directory & Formats
        opt_card = ctk.CTkFrame(self.main_container, corner_radius=8)
        opt_card.pack(fill="x", pady=(0, 12), padx=2)

        opt_title = ctk.CTkLabel(
            opt_card,
            text="3. Thư mục lưu & Định dạng đầu ra",
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
            text="Chọn thư mục...",
            width=110,
            height=34,
            command=self._browse_directory
        )
        btn_browse.pack(side="left", padx=(0, 8))

        btn_open = ctk.CTkButton(
            folder_row,
            text="Mở",
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
        lbl_fmt = ctk.CTkLabel(options_row, text="Định dạng:", font=ctk.CTkFont(size=12))
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
        lbl_quality = ctk.CTkLabel(options_row, text="Chất lượng:", font=ctk.CTkFont(size=12))
        lbl_quality.grid(row=0, column=2, sticky="w", padx=(0, 8), pady=4)
        self.quality_menu = ctk.CTkOptionMenu(
            options_row,
            values=["Tốt nhất (Gốc)", "1080p", "720p", "480p", "Chỉ âm thanh (MP3)"],
            width=150,
            height=30
        )
        self.quality_menu.set("Tốt nhất (Gốc)")
        self.quality_menu.grid(row=0, column=3, sticky="w", padx=(0, 20), pady=4)

        # Threads
        lbl_threads = ctk.CTkLabel(options_row, text="Luồng tải:", font=ctk.CTkFont(size=12))
        lbl_threads.grid(row=0, column=4, sticky="w", padx=(0, 8), pady=4)
        self.threads_menu = ctk.CTkOptionMenu(
            options_row,
            values=["16 luồng (Tối đa)", "8 luồng", "4 luồng"],
            width=135,
            height=30
        )
        self.threads_menu.set("16 luồng (Tối đa)")
        self.threads_menu.grid(row=0, column=5, sticky="w", pady=4)

        # 5. Section: Action Controls & Progress
        action_card = ctk.CTkFrame(self.main_container, corner_radius=8)
        action_card.pack(fill="x", pady=(0, 12), padx=2)

        action_row = ctk.CTkFrame(action_card, fg_color="transparent")
        action_row.pack(fill="x", padx=15, pady=(12, 10))

        self.btn_download = ctk.CTkButton(
            action_row,
            text="▶ BẮT ĐẦU TẢI",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self._start_download
        )
        self.btn_download.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_cancel = ctk.CTkButton(
            action_row,
            text="✕ HỦY TẢI",
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
            text="Sẵn sàng thực hiện tác vụ.",
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
            text="Nhật ký hoạt động (Console Log)",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        lbl_log.pack(side="left")

        btn_clear_log = ctk.CTkButton(
            log_header,
            text="Xóa log",
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
        selected = filedialog.askdirectory(initialdir=initial, title="Chọn thư mục lưu video")
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
            messagebox.showwarning("Thông báo", "Thư mục lưu video không tồn tại hoặc chưa được chọn.")

    def _on_mode_change(self, mode: str):
        self.frame_range.pack_forget()
        self.frame_cutoff.pack_forget()
        self.frame_full.pack_forget()

        if mode == "Khoảng thời gian (Start - End)":
            self.frame_range.pack(fill="x", padx=15, pady=(0, 12))
        elif mode == "Cắt lùi Live (-N phút)":
            self.frame_cutoff.pack(fill="x", padx=15, pady=(0, 12))
        elif mode == "Tải toàn bộ (Full)":
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
            messagebox.showwarning("Lỗi", "Vui lòng nhập đường link YouTube.")
            return

        self.info_preview.configure(text="Đang phân tích thông tin từ YouTube...", text_color="#3498db")
        self.btn_check.configure(state="disabled")

        def _worker():
            try:
                info = self.downloader.get_info(url)
                status = "🔴 ĐANG LIVE" if info['is_live'] else "🎬 Video/VOD"
                dur = format_seconds_to_time(info['duration']) if info['duration'] else "Trực tiếp"
                display = f"[{status}] {info['title']} | Kênh: {info['uploader']} | Thời lượng: {dur}"
                self.after(0, lambda: self.info_preview.configure(text=display, text_color="#2ecc71"))
                self._append_log(f"-> Phân tích thành công: {info['title']} ({status})")
            except Exception as e:
                err_text = f"Không thể lấy thông tin: {e}"
                self.after(0, lambda: self.info_preview.configure(text=err_text, text_color="#e74c3c"))
                self._append_log(f"[LỖI] {err_text}")
            finally:
                self.after(0, lambda: self.btn_check.configure(state="normal"))

        threading.Thread(target=_worker, daemon=True).start()

    def _start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Lỗi", "Vui lòng nhập đường link YouTube cần tải.")
            return

        out_dir = self.out_dir_entry.get().strip()
        if not out_dir:
            messagebox.showwarning("Lỗi", "Vui lòng chọn thư mục lưu video.")
            return

        mode_val = self.mode_selector.get()
        start_time = None
        end_time = None
        cutoff_minutes = 0.0

        if mode_val == "Khoảng thời gian (Start - End)":
            mode = "range"
            start_time = self.entry_start.get().strip()
            end_time = self.entry_end.get().strip()
        elif mode_val == "Cắt lùi Live (-N phút)":
            mode = "cutoff"
            try:
                cutoff_minutes = float(self.entry_cutoff.get().strip() or 0)
            except ValueError:
                messagebox.showerror("Lỗi", "Mốc cắt lùi phải là số phút hợp lệ (ví dụ: 45).")
                return
        else:
            mode = "full"

        # Quality mapping
        quality_map = {
            "Tốt nhất (Gốc)": "best",
            "1080p": "1080",
            "720p": "720",
            "480p": "480",
            "Chỉ âm thanh (MP3)": "audio"
        }
        quality = quality_map.get(self.quality_menu.get(), "best")

        # Threads mapping
        threads_map = {
            "16 luồng (Tối đa)": 16,
            "8 luồng": 8,
            "4 luồng": 4
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
        self.btn_download.configure(state="disabled", text="⏳ ĐANG TẢI...")
        self.btn_cancel.configure(state="normal")
        self.progress_bar.set(0.0)
        self.lbl_stats.configure(text="Đang kết nối tới máy chủ luồng phát...")

        def _on_progress(data: Dict[str, Any]):
            status = data.get("status")
            if status == "downloading":
                pct = data.get("percent", 0.0)
                spd = data.get("speed", "N/A")
                eta = data.get("eta", "N/A")
                f_idx = data.get("fragment_index")
                f_cnt = data.get("fragment_count")
                f_str = f" | Phân đoạn: {f_idx}/{f_cnt}" if f_cnt else ""
                
                self.after(0, lambda: self.progress_bar.set(pct / 100.0))
                self.after(0, lambda: self.lbl_stats.configure(
                    text=f"Tiến độ: {pct:.1f}% | Tốc độ: {spd} | ETA: {eta}{f_str}"
                ))
            elif status == "finished":
                self.after(0, lambda: self.progress_bar.set(1.0))
                self.after(0, lambda: self.lbl_stats.configure(text="Đang xử lý ghép các phân đoạn video bằng FFmpeg..."))

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
                        text="✔ TẢI VÀ XỬ LÝ HOÀN TẤT!",
                        text_color="#2ecc71"
                    ))
                    self.after(0, lambda: messagebox.showinfo("Thành công", "Đã tải xong và lưu video thành công!"))
                elif self.downloader.is_cancelled:
                    self.after(0, lambda: self.lbl_stats.configure(
                        text="✕ Tác vụ tải đã bị hủy.",
                        text_color="#e67e22"
                    ))
                else:
                    self.after(0, lambda: self.lbl_stats.configure(
                        text="✕ Quá trình tải gặp lỗi. Vui lòng kiểm tra log.",
                        text_color="#e74c3c"
                    ))
            except Exception as e:
                self._append_log(f"[LỖI HỆ THỐNG] {e}")
                self.after(0, lambda: self.lbl_stats.configure(
                    text=f"Lỗi: {e}",
                    text_color="#e74c3c"
                ))
            finally:
                self.after(0, self._reset_ui_after_download)

        self.download_thread = threading.Thread(target=_worker, daemon=True)
        self.download_thread.start()

    def _cancel_download(self):
        if self.downloader.is_running:
            self.downloader.cancel()
            self._append_log("-> Đã gửi tín hiệu hủy tải...")
            self.btn_cancel.configure(state="disabled", text="Đang dừng...")

    def _reset_ui_after_download(self):
        self.btn_download.configure(state="normal", text="▶ BẮT ĐẦU TẢI")
        self.btn_cancel.configure(state="disabled", text="✕ HỦY TẢI")

    def _on_close(self):
        if self.downloader.is_running:
            if messagebox.askyesno("Xác nhận thoát", "Đang có tiến trình tải hoạt động. Bạn có chắc muốn dừng và thoát?"):
                self.downloader.cancel()
                self.destroy()
        else:
            self.destroy()
