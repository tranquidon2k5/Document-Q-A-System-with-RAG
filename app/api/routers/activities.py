from fastapi import HTTPException, Query
from fastapi import APIRouter
from typing import List, Dict
from app.services.activities_service import fetch_activities, fetch_activity_details, get_raw_activities_from_page


# Tạo một APIRouter duy nhất cho file này
router = APIRouter(
    prefix="/activities",  # Thêm tiền tố cho tất cả các endpoint trong router này
    tags=["Activities"],  # Thẻ để hiển thị trên tài liệu API
)

@router.get("/", response_model=List[dict])
async def get_activities():
    """
    Endpoint để lấy danh sách các hoạt động, sự kiện.
    """
    try:
        activities_data = fetch_activities()
        
        if activities_data is None:
             raise HTTPException(status_code=500, detail="Không thể crawl dữ liệu hoạt động.")
        return activities_data
    except Exception as e:
        print(f"Lỗi tại endpoint /activities: {e}")
        raise HTTPException(status_code=500, detail="Lỗi server nội bộ.")
    
@router.get("/{activity_id}", response_model=Dict)
async def get_activity_details(activity_id: int):
    """
    Endpoint để lấy thông tin chi tiết của một hoạt động dựa trên ID.
    """
    try:
        details_data = fetch_activity_details(activity_id=activity_id)
        
        if not details_data:
             raise HTTPException(status_code=404, detail="Không tìm thấy hoạt động.")
        return details_data
        
    except Exception as e:
        print(f"Lỗi tại endpoint /activities/{activity_id}: {e}")
        raise HTTPException(status_code=500, detail="Lỗi server nội bộ.")
    
if __name__ == "__main__":
    res = fetch_activity_details(14505)
    print(res)
    print(type(res))