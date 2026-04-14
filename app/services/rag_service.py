import uuid
from typing import List, Dict
from langchain_core.messages import BaseMessage
from app.models.schemas import QuestionRequest, AnswerResponse
from app.rag.agent import get_response

# BỘ NHỚ LƯU TRỮ CÁC PHIÊN HỘI THOẠI
# Đây là nơi lưu trữ state của ứng dụng.
# Key: session_id (str), Value: list of BaseMessage
conversation_histories: Dict[str, List[BaseMessage]] = {}

def handle_question(request: QuestionRequest) -> AnswerResponse:
    """
    Hàm này xử lý toàn bộ logic nghiệp vụ cho một yêu cầu hỏi-đáp:
    1. Quản lý session ID.
    2. Lấy lịch sử hội thoại tương ứng.
    3. Gọi RAG agent để có câu trả lời.
    4. Cập nhật và lưu lại lịch sử hội thoại.
    5. Trả về response theo đúng định dạng.
    """
    session_id = request.session_id
    
    # 1. Nếu client không gửi session_id hoặc id không tồn tại, tạo phiên mới.
    if not session_id or session_id not in conversation_histories:
        session_id = str(uuid.uuid4())
        conversation_histories[session_id] = []
        print(f"--- Bắt đầu phiên hội thoại mới: {session_id} ---")
    else:
        print(f"--- Tiếp tục phiên hội thoại: {session_id} ---")

    # 2. Lấy lịch sử hội thoại của phiên hiện tại.
    current_history = conversation_histories[session_id]
    
    # 3. Gọi hàm get_response từ agent với câu hỏi và lịch sử.
    final_answer_text, updated_history = get_response(request.question, current_history)
    
    # 4. Cập nhật lại lịch sử cho phiên này trong bộ nhớ.
    conversation_histories[session_id] = updated_history
    
    # 5. Trả về đối tượng AnswerResponse (Pydantic model) cho router.
    return AnswerResponse(answer=final_answer_text, session_id=session_id)