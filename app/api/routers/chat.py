from fastapi import APIRouter
from app.models.schemas import QuestionRequest, AnswerResponse
from app.services import rag_service # Import service

router = APIRouter(
    prefix="/ask",  # Thêm tiền tố cho tất cả các endpoint trong router này
    tags=["Ask Agent"],  # Thẻ để hiển thị trên tài liệu API
)

@router.post("/", response_model=AnswerResponse)
def ask_question(request: QuestionRequest):
    # Router chỉ cần gọi một hàm duy nhất từ service
    return rag_service.handle_question(request)
