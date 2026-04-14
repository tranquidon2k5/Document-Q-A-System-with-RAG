from fastapi import HTTPException, Query, APIRouter
from typing import List
from app.services.scholarships_service import crawl_all_scholarships
    
router = APIRouter(
    prefix="/scholarships",  # Thêm tiền tố cho tất cả các endpoint trong router này
    tags=["Scholarships"],  # Thẻ để hiển thị trên tài liệu API
)

@router.get("/", response_model=List[dict])
async def get_scholarships():
    """
    Endpoint để lấy danh sách tất cả học bổng.
    """
    try:
        scholarships_data = crawl_all_scholarships()
        if scholarships_data is None:
            raise HTTPException(status_code=500, detail="Không thể crawl dữ liệu học bổng.")
        
        return scholarships_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server nội bộ: {str(e)}")

if __name__ == "__main__":
    print(crawl_all_scholarships())