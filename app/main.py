from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import activities, jobs, scholarship, chat, tts

# Khởi tạo đối tượng FastAPI app
app = FastAPI(
    title="HUST AI Assistant API",
    description="API cho Trợ lý ảo HUST, cung cấp thông tin về học bổng, việc làm, hoạt động và giao diện chat.",
    version="1.0.0"
)

# Cấu hình CORS (Cross-Origin Resource Sharing)
# Cho phép frontend (chạy trên một domain/port khác) có thể giao tiếp với API này.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả. Trong môi trường production, bạn nên giới hạn lại chỉ domain của frontend.
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép tất cả các method (GET, POST, etc.)
    allow_headers=["*"],  # Cho phép tất cả các header.
)

# Gắn các router vào ứng dụng chính
# Mỗi router sẽ quản lý một nhóm các endpoint cụ thể
app.include_router(chat.router)
app.include_router(tts.router) # <-- THÊM ROUTER TTS MỚI
app.include_router(activities.router)
app.include_router(jobs.router)
app.include_router(scholarship.router)


# Endpoint gốc để kiểm tra "sức khỏe" của server
@app.get("/", tags=["Health Check"])
def read_root():
    """
    Endpoint gốc để kiểm tra xem server có đang chạy hay không.
    """
    return {"status": "HUST AI Assistant API is running!"}