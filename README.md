# YouTube Stream Downloader ⚡

> **Công cụ tối giản, chuyên nghiệp giúp tải Livestream và Video YouTube với khả năng tùy chọn khoảng thời gian cần tải và thư mục lưu trữ.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GUI](https://img.shields.io/badge/UI-CustomTkinter-darkblue.svg)](https://github.com/TomSchimansky/CustomTkinter)

---

## 🌟 Tính Năng Nổi Bật

- 🎯 **Tùy chọn khoảng thời gian tải linh hoạt**:
  - **Start - End**: Tải một đoạn cụ thể (Ví dụ: từ `00:15:00` đến `01:30:00` hoặc nhập theo số giây).
  - **Cắt lùi Live Head (-N phút)**: Tải livestream từ đầu và dừng trước thời điểm hiện tại `N` phút (ví dụ: `-45` phút như cấu hình ban đầu để tránh phân đoạn đang phát dở).
  - **Tải toàn bộ (Full)**: Tải toàn bộ luồng phát từ đầu đến hiện tại hoặc toàn bộ video đã đăng tải.
- 🔴 **Hỗ trợ Livestream Trực Tiếp (Live-from-start)**:
  - Can thiệp trực tiếp vào generator phân đoạn adaptive fragments của YouTube để ngắt tải chính xác tại sequence mục tiêu.
  - Tự động tiếp tục (resume) và tải lại các phân đoạn bị lỗi.
- ⚡ **Tốc độ cao đa luồng**:
  - Hỗ trợ tải song song lên tới **16 luồng phân đoạn** cùng lúc (`concurrent_fragment_downloads`), tận dụng tối đa băng thông mạng.
- 📂 **Lựa chọn thư mục lưu trữ tùy ý**:
  - Dễ dàng chọn thư mục đích bằng hộp thoại chọn thư mục hoặc gõ đường dẫn trực tiếp.
  - Tự động ghi nhớ thư mục lưu video cho các lần mở sau (`config.json`).
  - Nút **Mở thư mục** nhanh chỉ với 1 click.
- 🖥️ **Giao diện Desktop tối giản & chuyên nghiệp**:
  - Phong cách Dark Mode thanh lịch, trực quan, không màu mè lòe loẹt.
  - Hiển thị đầy đủ thông tin video, thanh tiến trình (%), tốc độ tải thực tế (`MB/s`), thời gian ước tính còn lại (`ETA`), số phân đoạn.
  - Khung nhật ký console tích hợp ngay trên màn hình.
- 💻 **Chế độ dòng lệnh (CLI)**:
  - Đầy đủ tham số cho các bạn thích sử dụng terminal hoặc lập lịch tự động.

---

## 🛠️ Yêu Cầu Hệ Thống

1. **Python**: Phiên bản 3.10 trở lên.
2. **FFmpeg**: Cần có trong biến môi trường `PATH` để ghép luồng hình ảnh & âm thanh thành file hoàn chỉnh.
   - *Kiểm tra trên Windows*: Mở Command Prompt / PowerShell và gõ `ffmpeg -version`.
   - *Nếu chưa có*: Tải từ [gyan.dev FFmpeg](https://www.gyan.dev/ffmpeg/builds/) hoặc cài bằng `winget install Gyan.FFmpeg`.

---

## 🚀 Cài Đặt

1. **Clone repository về máy**:
   ```bash
   git clone https://github.com/khanhtq/youtube-stream-downloader.git
   cd youtube-stream-downloader
   ```

2. **Cài đặt các thư viện cần thiết**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 📖 Hướng Dẫn Sử Dụng

### 1. Khởi chạy Giao diện Đồ họa (GUI)

- **Cách 1**: Nhấp đúp vào file `run.bat` (trên Windows).
- **Cách 2**: Chạy qua dòng lệnh:
  ```bash
  python main.py
  ```

#### Các bước thao tác trên giao diện:
1. **Dán URL** livestream/video YouTube vào ô nhập (có nút *Dán* và *Kiểm tra* để xem trước tiêu đề và trạng thái live).
2. **Chọn chế độ tải**:
   - `Khoảng thời gian (Start - End)`: Nhập thời điểm bắt đầu (ví dụ: `00:10:00`) và thời điểm dừng (ví dụ: `01:00:00`). Để trống để tải từ đầu hoặc đến hết.
   - `Cắt lùi Live (-N phút)`: Nhập số phút muốn lùi so với live head (ví dụ: `45`).
   - `Tải toàn bộ (Full)`: Tải hết toàn bộ luồng.
3. **Chọn thư mục lưu video**: Nhấn `Chọn thư mục...` để duyệt thư mục muốn lưu video.
4. **Tùy chọn định dạng & chất lượng**: MKV/MP4, chất lượng 1080p, 720p hoặc Tốt nhất.
5. Nhấn **▶ BẮT ĐẦU TẢI**. Bạn có thể nhấn **✕ HỦY TẢI** bất cứ lúc nào.

---

### 2. Sử dụng Chế độ Dòng lệnh (CLI)

Bạn có thể truyền trực tiếp các tham số vào `main.py` (hoặc `cli.py`):

```bash
# Xem hướng dẫn chi tiết các tùy chọn:
python main.py --help
```

#### Một số ví dụ thông dụng:

- **Tải livestream lùi 45 phút so với live head (tương tự mã nguồn gốc):**
  ```bash
  python main.py --cli --url "https://www.youtube.com/live/xIzdGai-m1c" --cutoff 45 --out-dir "D:/Videos"
  ```

- **Tải một đoạn cụ thể từ 00:15:00 đến 01:00:00:**
  ```bash
  python main.py --cli --url "https://www.youtube.com/watch?v=VIDEO_ID" --start 00:15:00 --end 01:00:00 --out-dir "D:/Videos"
  ```

- **Tải với 16 luồng song song, định dạng MKV, chất lượng 1080p:**
  ```bash
  python main.py --cli --url "https://www.youtube.com/live/VIDEO_ID" --format mkv --quality 1080 --threads 16
  ```

- **Chỉ kiểm tra thông tin video/stream mà không tải:**
  ```bash
  python main.py --cli --url "https://www.youtube.com/live/VIDEO_ID" --info
  ```

---

## 📂 Cấu Trúc Dự Án

```
youtube-stream-downloader/
├── core/                       # Lõi xử lý logic tải & cấu hình
│   ├── __init__.py
│   ├── downloader.py           # Engine tải luồng, can thiệp adaptive fragments, hủy tải
│   ├── config.py               # Quản lý cấu hình & lưu tùy chọn người dùng
│   └── utils.py                # Hàm tiện ích (parse thời gian, format bytes, kiểm tra ffmpeg)
├── ui/                         # Giao diện người dùng Desktop tối giản
│   ├── __init__.py
│   └── app.py                  # Giao diện CustomTkinter hiện đại, đa luồng không giật lag
├── tests/                      # Bộ kiểm thử đơn vị
│   └── test_core.py
├── cli.py                      # Bộ điều khiển dòng lệnh
├── main.py                     # Entry point chính tự động phân phối CLI/GUI
├── run.bat                     # File thực thi nhanh 1-click cho Windows
├── requirements.txt            # Danh sách thư viện phụ thuộc
├── .gitignore                  # Cấu hình bỏ qua file rác / file tải tạm
└── README.md                   # Tài liệu hướng dẫn sử dụng
```

---

## 📜 Giấy Phép & Tuyên Bố Miễn Trừ Trách Nhiệm

Dự án này được phát triển cho mục đích học tập và lưu trữ nội dung cá nhân hợp pháp. Vui lòng tuân thủ điều khoản dịch vụ của YouTube và bản quyền nội dung của các nhà sáng tạo.
