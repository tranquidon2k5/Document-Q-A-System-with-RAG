import uvicorn

if __name__ == "__main__":
    """
    Đây là điểm khởi đầu (entry point) để chạy ứng dụng.
    File này sẽ gọi Uvicorn, một máy chủ ASGI server, để khởi động và phục vụ
    ứng dụng FastAPI được định nghĩa trong file app/main.py.
    """
    uvicorn.run(
        # Đường dẫn đến đối tượng FastAPI app: "tên_thư_mục.tên_file:tên_biến_app"
        "app.main:app",
        
        # Cấu hình máy chủ
        host="127.0.0.1",  # Chạy trên local host
        port=8000,         # Sử dụng cổng 8000
        reload=True        # Tự động khởi động lại server mỗi khi có thay đổi trong code,
                           # rất hữu ích trong quá trình phát triển.
    )