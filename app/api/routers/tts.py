from fastapi import HTTPException, Query, Response, APIRouter
from langchain_core.messages import BaseMessage
from app.models.schemas import TTSRequest
from app.services.tts_service import get_speech

router = APIRouter(
    prefix="/tts",  # Thêm tiền tố cho tất cả các endpoint trong router này
    tags=["Text to speech"],  # Thẻ để hiển thị trên tài liệu API
)

@router.post("/", summary="Tổng hợp văn bản thành giọng nói với logic ưu tiên")
async def text_to_speech(request: TTSRequest):
    """
    Ưu tiên 1: Gọi API TTS ngoài qua Ngrok.
    Ưu tiên 2: Nếu thất bại, dùng gTTS làm phương án dự phòng.
    """
    if not request.text:
        raise HTTPException(status_code=400, detail="Văn bản không được để trống.")
    
    return get_speech(request.text, request.speaker_id)