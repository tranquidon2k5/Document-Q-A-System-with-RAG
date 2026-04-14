# QA System with RAG

Hệ thống trợ lý ảo thông minh hỗ trợ sinh viên tra cứu thông tin về học bổng, việc làm, hoạt động ngoại khóa thông qua công nghệ RAG (Retrieval Augmented Generation).

## 🚀 Tính năng chính
- **Chat thông minh**: Trả lời câu hỏi dựa trên tài liệu thực tế của HUST.
- **Tra cứu Học bổng**: Cập nhật thông tin học bổng mới nhất.
- **Tìm kiếm Việc làm**: Kết nối sinh viên với các cơ hội nghề nghiệp.
- **Hoạt động ngoại khóa**: Thông tin chi tiết về các sự kiện, câu lạc bộ.
- **Text-to-Speech (TTS)**: Phát âm câu trả lời bằng giọng nói chuẩn tiếng Việt.

## 🛠 Công nghệ sử dụng
- **Backend**: FastAPI (Python)
- **Frontend**: Vanilla HTML/JS/CSS
- **AI**: MCP (Model Context Protocol), RAG, OpenAI/LLMs
- **Containerization**: Docker

## 📦 Cài đặt và Chạy ứng dụng

### 1. Chạy bằng Docker (Khuyên dùng)
```bash
docker build -t hust-ai-assistant .
docker run -p 8000:8000 hust-ai-assistant
```

### 2. Chạy thủ công
**Yêu cầu**: Python 3.10+ và `uv` (hoặc `pip`)

```bash
# Cài đặt thư viện
pip install -r requirements.txt

# Chạy server
python run.py
```
Sau đó mở `index.html` trực tiếp trong trình duyệt để sử dụng giao diện.

## 📂 Cấu trúc thư mục
- `app/`: Mã nguồn Backend (FastAPI, RAG logic, Routers)
- `notebook/`: Các bản nháp nghiên cứu và thử nghiệm AI.
- `index.html`, `script.js`, `style.css`: Giao diện người dùng.
- `dockerfile`: Cấu hình Docker.

