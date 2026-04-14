import uuid
from typing import List, Dict
from langchain_core.messages import BaseMessage
from models.schemas import QuestionRequest, AnswerResponse
from rag.agent import get_response

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
    # --- LOGIC QUẢN LÝ PHIÊN ---
    session_id = request.session_id
        
    # 1. Nếu client không gửi session_id hoặc id không tồn tại, tạo phiên mới.
    if not session_id or session_id not in conversation_histories:
        session_id = str(uuid.uuid4())
        conversation_histories[session_id] = []
        print(f"--- Bắt đầu phiên hội thoại mới: {session_id} ---")

    # 2. Lấy lịch sử hội thoại của phiên hiện tại.
    current_history = conversation_histories[session_id]
        
    # 3. Gọi hàm get_response đã được sửa đổi với câu hỏi và lịch sử.
    final_answer, updated_history = get_response(request.question, current_history)
        
    # 4. Cập nhật lại lịch sử cho phiên này trong bộ nhớ.
    conversation_histories[session_id] = updated_history
        
    # 5. Trả về câu trả lời và session_id cho client.
    return AnswerResponse(answer=final_answer, session_id=session_id)

def run_test():
    """
    Hàm test mô phỏng một cuộc hội thoại ngắn để kiểm tra rag_service.
    """
    print("--- BẮT ĐẦU TEST RAG SERVICE ---")

    # --- LƯỢT 1: Câu hỏi đầu tiên, không có session_id ---
    print("\n[LƯỢT 1] Gửi câu hỏi đầu tiên (không có session_id)...")
    first_request = QuestionRequest(question="Giới thiệu về trường cơ khí đại học bách khoa hà nội")
    
    # Gọi hàm xử lý
    first_response = handle_question(first_request)
    
    # Lấy session_id được tạo ra
    session_id = first_response.session_id
    
    print(f"-> Session ID mới được tạo: {session_id}")
    print(f"-> Câu trả lời của Bot: {first_response.answer[:100]}...") # In 100 ký tự đầu

    # **Kiểm tra kết quả Lượt 1**
    assert session_id is not None, "Test Lượt 1 Thất Bại: session_id không được tạo."
    assert session_id in conversation_histories, "Test Lượt 1 Thất Bại: session_id không được lưu."
    assert len(conversation_histories[session_id]) == 2, "Test Lượt 1 Thất Bại: Lịch sử hội thoại không có 2 tin nhắn."
    print("[LƯỢT 1] KIỂM TRA THÀNH CÔNG!")

    # --- LƯỢT 2: Câu hỏi tiếp theo, sử dụng session_id đã có ---
    print(f"\n[LƯỢT 2] Gửi câu hỏi tiếp theo (sử dụng session_id: {session_id})...")
    second_request = QuestionRequest(question="hiệu trưởng của trường đó là ai?", session_id=session_id)

    # Gọi hàm xử lý
    second_response = handle_question(second_request)
    
    print(f"-> Session ID đã sử dụng: {second_response.session_id}")
    print(f"-> Câu trả lời của Bot: {second_response.answer[:100]}...")

    # **Kiểm tra kết quả Lượt 2**
    assert second_response.session_id == session_id, "Test Lượt 2 Thất Bại: session_id bị thay đổi."
    assert len(conversation_histories[session_id]) == 4, "Test Lượt 2 Thất Bại: Lịch sử hội thoại không được cập nhật lên 4 tin nhắn."
    print("[LƯỢT 2] KIỂM TRA THÀNH CÔNG!")

    print("\n--- TEST HOÀN TẤT ---")
    print("Tất cả các kiểm tra cơ bản cho rag_service đã thành công.")

if __name__ == "__main__":
    run_test()