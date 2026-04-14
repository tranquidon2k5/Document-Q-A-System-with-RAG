from fastapi import HTTPException, Query, APIRouter
from enum import Enum
from typing import List, Optional
from app.services.jobs_service import CAREER_MAP, CAREER_MAP_LOWER, VIETNAM_CITIES, fetch_jobs
from app.models.schemas import JobType


router = APIRouter(
    prefix="/jobs",  # Thêm tiền tố cho tất cả các endpoint trong router này
    tags=["Jobs"],  # Thẻ để hiển thị trên tài liệu API
)

@router.get("/", response_model=List[dict])
async def get_jobs(
    job_type: JobType,
    career: Optional[str] = Query(None, description="Tên chuyên ngành cần lọc, ví dụ: 'công nghệ thông tin'"),
    city: Optional[str] = Query(None, description="Tên tỉnh/thành phố cần lọc, ví dụ: 'Hà Nội'")
):
    """
    Lấy danh sách việc làm, có thể lọc theo chuyên ngành (không phân biệt hoa/thường) và thành phố.
    """
    location_mapping = {"hot": 1, "new": 2, "internship": 3}
    location_code = location_mapping[job_type.value]

    career_id = None
    if career:
        career_id = CAREER_MAP_LOWER.get(career.lower())
        
        if career_id:
            print(f"Đã tìm thấy chuyên ngành '{career}' với ID: {career_id}")
        else:
            print(f"Không tìm thấy chuyên ngành '{career}' trong danh sách.")

    if city and city not in VIETNAM_CITIES:
        raise HTTPException(status_code=400, detail="Tên thành phố không hợp lệ.")
        
    try:
        jobs_data = fetch_jobs(
            location_code=location_code,
            career=career,
            city=city
        )
        if jobs_data is None:
             raise HTTPException(status_code=500, detail="Không thể crawl dữ liệu việc làm.")
        return jobs_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server nội bộ.")

@router.get("/careers", response_model=List[str])
async def get_careers():
    """Cung cấp danh sách các chuyên ngành để lọc."""
    return list(CAREER_MAP.keys())

@router.get("/cities", response_model=List[str])
async def get_cities():
    """Cung cấp danh sách các tỉnh/thành phố để lọc."""
    return VIETNAM_CITIES

if __name__ == "__main__":
    print(fetch_jobs(1))