from pydantic import BaseModel
from enum import Enum
from typing import Optional 

class QuestionRequest(BaseModel):
    question: str
    # Client sẽ gửi kèm session_id để duy trì cuộc hội thoại
    session_id: Optional[str] = None

class AnswerResponse(BaseModel):
    answer: str
    # Server sẽ trả về session_id để client dùng cho lần gọi tiếp theo
    session_id: str

class JobType(str, Enum):
    hot = "hot"
    new = "new"
    internship = "internship"
    
class TTSRequest(BaseModel):
    text: str
    speaker_id : int = 1