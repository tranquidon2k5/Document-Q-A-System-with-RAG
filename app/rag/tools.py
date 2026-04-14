from app.services.scholarships_service import crawl_all_scholarships, Scholarship
from langchain_community.document_loaders import WebBaseLoader
import re
import os
from datetime import datetime, timedelta
from typing import List
import calendar
from typing import Dict, List
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from serpapi import SerpApiClient

from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()


from langchain_google_genai import ChatGoogleGenerativeAI
classifier_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# --- Khởi tạo Pinecone (chỉ cho tool tìm kiếm sổ tay) ---

pinecone_api_key = os.getenv("PICONE_API_KEY")
pc = Pinecone(api_key=pinecone_api_key)
index_name = "sotayhust"  
index = pc.Index(index_name)

#Thiết lập tool search web tavily
tavily_tool = TavilySearch(max_results=5)

def get_similar_doc(text, namespace, topk = 5):
    results = index.search(
        namespace=namespace, 
        query={
            "inputs": {"text": text}, 
            "top_k": topk
        },
        fields=["text"]
    )
    list_doc = []
    for doc in results["result"]['hits']:
        list_doc.append(doc['fields']['text'])
    return list_doc

# --- TOOL KIỂM DUYỆT NỘI DUNG ---
@tool
def query_classifier(query: str) -> str:
    """
    Phân loại câu hỏi của người dùng vào một trong các danh mục sau: 'safe', 'sensitive_political'.
    """

    system_prompt = f"""
    Bạn là một chuyên gia kiểm duyệt nội dung cho một chatbot của trường đại học.
    Nhiệm vụ của bạn là phân loại câu hỏi của sinh viên vào MỘT trong hai danh mục sau đây:
    1. safe: Các câu hỏi liên quan trực tiếp đến đời sống, học tập, quy chế, học bổng, chính sách tại Đại học Bách Khoa Hà Nội và các nội dung liên quan đến Pháp luật, hiến pháp Việt Nam.
    2. sensitive_political: Các câu hỏi chứa nội dung về chính trị, tôn giáo, các vấn đề xã hội nhạy cảm, bạo lực, thù ghét, hoặc không phù hợp với môi trường giáo dục.

    Hãy chỉ trả về TÊN của danh mục (ví dụ: "safe" hoặc "sensitive_political"), không giải thích gì thêm.

    Câu hỏi cần phân loại: "{query}"
    """
    
    print(f"---TOOL: Classifying query: '{query}'---")
    
    # Gọi LLM để phân loại
    response = classifier_llm.invoke(system_prompt)
    
    # Xử lý kết quả trả về từ LLM
    classification = response.content.strip().lower()
    
    if "sensitive_political" in classification:
        return "sensitive_political"
    
    return "safe"
# --- Định nghĩa Tool 1: Tìm kiếm Sổ tay Sinh viên ---
@tool
def search_student_handbook(query: str) -> List[str]:
    """
    Sử dụng để tra cứu thông tin về ĐỜI SỐNG SINH VIÊN và CÁC DỊCH VỤ HỖ TRỢ trong Sổ tay Sinh viên.
    Rất hữu ích cho các câu hỏi về: điểm rèn luyện, hoạt động ngoại khóa, câu lạc bộ,
    ký túc xá, nhà trọ, các tuyến xe bus, hỗ trợ tâm lý, hướng nghiệp, việc làm thêm,
    quy tắc ứng xử văn hóa, quy định về học bổng và thông tin liên hệ các phòng ban, khoa, viện.
    """
    print(f"---SỬ DỤNG TOOL: search_docs với query: {query}---")
    return get_similar_doc(query, namespace = "semantic_chunker")

@tool
def search_academic_regulations(query: str) -> List[str]:
    """
    Sử dụng để tra cứu các QUY ĐỊNH HỌC THUẬT CHÍNH THỨC trong Quy chế Đào tạo.
    Dùng cho các câu hỏi về: tín chỉ, điểm số (GPA/CPA), đăng ký học phần, cảnh báo học tập,
    điều kiện tốt nghiệp, đồ án tốt nghiệp, nghỉ học tạm thời, buộc thôi học, học phí,
    học cùng lúc hai chương trình, và các vấn đề học vụ khác.
    """
    print(f"---TOOL: search_academic_regulations (namespace: QCDT2025) | Query: {query}---")
    return get_similar_doc(query, namespace="QCDT2025")

@tool
def search_law_vietnam(query: str) -> List[str]:
    """
    Sử dụng để tra cứu các VĂN BẢN LUẬT VIỆT NAM đã được nạp vào namespace 'LawVN'.
    Dùng cho các câu hỏi liên quan đến: Bộ luật, Hiến pháp, luật hình sự, luật dân sự,
    luật tố tụng, luật giáo dục, và các văn bản pháp luật khác.
    """
    print(f"---TOOL: search_law_vietnam (namespace: LawVN) | Query: {query}---")
    return get_similar_doc(query, namespace="LawVN")

# @tool
def search_website(query: str, num_results: int = 2): # Tăng num_results mặc định lên 3
    """
    Thực hiện tìm kiếm Google, lọc bỏ domain không mong muốn, 
    sau đó scrape nội dung từ các kết quả hợp lệ.
    """
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        raise ValueError("Vui lòng đặt SERPAPI_KEY trong biến môi trường của bạn.")

    # === BƯỚC 1: TÌM URL BẰNG SERPAPI ===
    print(f"Đang tìm kiếm các trang web liên quan cho: '{query}'...")
    params = {
        "api_key": api_key,
        "engine": "google",
        "q": query,
        "gl": "vn",
        "hl": "vi",
    }
    try:
        client = SerpApiClient(params)
        results = client.get_dict()
        
        if "organic_results" not in results:
            print("Không tìm thấy kết quả tự nhiên.")
            return

        # === LOGIC LỌC ĐÃ ĐƯỢC THÊM VÀO ĐÂY ===
        print("Đang lọc kết quả, loại bỏ các trang từ 'hust.edu.vn'...")
        
        # 1. Lấy toàn bộ danh sách kết quả
        all_organic_results = results["organic_results"]
        
        # 2. Tạo một danh sách link mới, chỉ chứa các link KHÔNG thuộc hust.edu.vn
        filtered_links = [
            result["link"] 
            for result in all_organic_results 
            if "hust.edu.vn" not in result["link"]
        ]
        
        # 3. Lấy số lượng link mong muốn từ danh sách đã lọc
        urls_to_scrape = filtered_links[:num_results]
        
        if not urls_to_scrape:
            print("Không tìm thấy link nào phù hợp sau khi đã lọc.")
            return
            
        print(f"Đã tìm thấy {len(urls_to_scrape)} link phù hợp để lấy dữ liệu.")
        
    except Exception as e:
        print(f"Lỗi khi gọi SerpApi: {e}")
        return

    # === BƯỚC 2: SCRAPE NỘI DUNG TỪ CÁC URL ĐÃ LỌC ===
    print("\nBắt đầu quá trình lấy nội dung chi tiết từ các trang web...")
    full_context = ""
    for i, url in enumerate(urls_to_scrape):
        print(f"Đang xử lý link {i+1}/{len(urls_to_scrape)}")
        content = scrape_content_from_url(url)
        if content:
            full_context += f"--- Nguồn {i+1} (từ {url}) ---\n"
            full_context += content + "\n\n"
    
    print("--- Hoàn thành việc lấy dữ liệu thô! ---")
    return full_context
@tool
def get_scholarships(
    time_period: str = "upcoming", status: str = "all"
) -> List[Dict]:
    """
    Sử dụng để lấy danh sách học bổng, có thể lọc theo thời gian và trạng thái (còn hạn/hết hạn).
    
    Tham số `status` chấp nhận: "open", "expired", "all".
    
    Tham số `time_period` chấp nhận:
    - Các từ khóa: "upcoming", "this_week", "this_month", "last_7_days", "last_month".
    - Tháng cụ thể: chuỗi "YYYY-MM" (ví dụ: "2025-08" cho tháng 8 năm 2025).
    - Ngày cụ thể: chuỗi "YYYY-MM-DD" (ví dụ: "2025-09-01").
    """
    print(f"---TOOL: get_scholarships (time_period: {time_period}, status: {status})---")

    all_scholarships = crawl_all_scholarships()
    if not all_scholarships:
        return [{"error": "Không thể crawl dữ liệu học bổng."}]

    today = datetime.now()
    start_dt, end_dt = None, None

    time_period_mapping = {
        "upcoming": (today, today + timedelta(days=30)),
        "this_week": (today - timedelta(days=today.weekday()), (today - timedelta(days=today.weekday())) + timedelta(days=6)),
        "this_month": (today.replace(day=1), today.replace(day=calendar.monthrange(today.year, today.month)[1])),
        "last_7_days": (today - timedelta(days=7), today),
        "last_month": ((today.replace(day=1) - timedelta(days=1)).replace(day=1), today.replace(day=1) - timedelta(days=1)),
    }

    if time_period in time_period_mapping:
        start_dt, end_dt = time_period_mapping[time_period]
    else:
        try:
            # Thử định dạng YYYY-MM (cho cả tháng)
            parsed_date = datetime.strptime(time_period, "%Y-%m")
            start_dt = parsed_date.replace(day=1)
            last_day = calendar.monthrange(parsed_date.year, parsed_date.month)[1]
            end_dt = parsed_date.replace(day=last_day)
        except ValueError:
            try:
                # Thử định dạng YYYY-MM-DD (cho ngày cụ thể)
                parsed_date = datetime.strptime(time_period, "%Y-%m-%d")
                start_dt = end_dt = parsed_date
            except ValueError:
                return [{"error": f"Giá trị time_period '{time_period}' không hợp lệ. Phải là từ khóa hoặc theo định dạng YYYY-MM, YYYY-MM-DD."}]

    # Đảm bảo bao trọn cả ngày
    start_dt = start_dt.replace(hour=0, minute=0, second=0)
    end_dt = end_dt.replace(hour=23, minute=59, second=59)

    filtered_list = []
    for hb in all_scholarships:
        try:
            if 'Deadline' not in hb or not hb['Deadline']:
                continue
            
            deadline_dt = datetime.strptime(hb['Deadline'], '%Y-%m-%d %H:%M:%S')
            if not (start_dt <= deadline_dt <= end_dt):
                continue
            
            is_expired = deadline_dt < today
            current_status = "Expired" if is_expired else "Open"

            if status == "all" or (status == "open" and not is_expired) or (status == "expired" and is_expired):
                hb = Scholarship(hb)
                filtered_list.append(hb.get_full_info_string())
        except (ValueError, KeyError, TypeError) as e:
            print(f"Bỏ qua học bổng bị lỗi: {hb.get('Title')}, Lỗi: {e}")
            continue

    if not filtered_list:
        return [{"message": f"Không tìm thấy học bổng nào với trạng thái '{status}' trong khoảng thời gian '{time_period}'."}]

    return filtered_list


def clean_website_text(text: str) -> str:
    """
    Làm sạch văn bản từ trang Wikipedia để chuẩn bị cho RAG.
    
    Args:
        text (str): Văn bản thô từ Wikipedia.
        
    Returns:
        str: Văn bản đã được làm sạch.
    """
    # 1. Loại bỏ các phần không cần thiết
    # Loại bỏ nội dung trong ngoặc vuông (như chú thích [1], [a])
    text = re.sub(r'\[.*?\]', '', text)
    # Loại bỏ các đoạn văn bản trong ngoặc đơn sau khi đã xóa chú thích,
    # ví dụ: (tiếng Anh: Hanoi University of Science and Technology, HUST)
    text = re.sub(r'\s*\([^)]*\)', '', text)
    # Loại bỏ các ký tự điều khiển định dạng, ví dụ: \n, \t, \xa0
    text = text.replace('\n', ' ').replace('\t', ' ').replace('\xa0', ' ')
    
    # 2. Loại bỏ các menu, thanh điều hướng, và các phần giao diện trang web
    # Các từ khóa thường xuất hiện ở thanh điều hướng
    keywords_to_remove = [
        'Bước tới nội dung', 'Trình đơn chính', 'chuyển sang thanh bên', 'ẩn',
        'Điều hướng', 'Trang Chính', 'Nội dung chọn lọc', 'Bài viết ngẫu nhiên',
        'Thay đổi gần đây', 'Báo lỗi nội dung', 'Tương tác', 'Hướng dẫn',
        'Giới thiệu Wikipedia', 'Cộng đồng', 'Thảo luận chung', 'Giúp sử dụng',
        'Liên lạc', 'Tải lên tập tin', 'Tìm kiếm', 'Giao diện', 'Quyên góp',
        'Tạo tài khoản', 'Đăng nhập', 'Công cụ cá nhân', 'Nội dung', 'Đầu',
        'Hiện/ẩn mục', 'sửa', 'sửa mã nguồn', 'Bách khoa toàn thư mở Wikipedia',
        'Đóng mở mục lục', 'Tất cả bài viết cần được wiki hóa',
        'Lỗi CS1: tên chung', 'Bài có liên kết hỏng', 'Trang thiếu chú thích trong bài',
        'Xem thêm', 'Chú thích', 'Ghi chú', 'Tham khảo', 'Liên kết ngoài',
        'Tiêu đề chuẩn', 'Lấy từ', 'Trang này được sửa đổi lần cuối',
        'Văn bản được phát hành theo Giấy phép', 'Chính sách quyền riêng tư',
        'Giới thiệu Wikipedia', 'Lời phủ nhận', 'Lập trình viên',
        'Thống kê', 'Tuyên bố về cookie', 'Phiên bản di động',
        'Bài viết', 'Thảo luận', 'Tiếng Việt', 'Đọc', 'Sửa đổi', 'Xem lịch sử',
        'Công cụ', 'Tác vụ', 'Chung', 'Các liên kết đến đây',
        'Thay đổi liên quan', 'Liên kết thường trực', 'Thông tin trang',
        'Trích dẫn trang này', 'Tạo URL rút gọn', 'Tải mã QR',
        'In và xuất', 'Tạo một quyển sách', 'Tải dưới dạng PDF', 'Bản để in ra',
        'Tại dự án khác', 'Wikimedia Commons', 'Khoản mục Wikidata',
        'Thứ tự', 'Hệ đại học', 'Hệ sau đại học'
    ]
    
    for keyword in keywords_to_remove:
        text = text.replace(keyword, ' ')
        
    # 3. Xử lý các đoạn văn bản dài và thừa
    text = re.sub(r'Đại học Bách khoa Hà Nội.*?(?=Lịch sử)', ' ', text)
    # Loại bỏ các danh sách dạng bảng
    text = re.sub(r'Thứ tự.*?Giám đốc', ' ', text, flags=re.DOTALL)
    text = re.sub(r'Hiệu trưởng.*?Tạ Quang Bửu', ' ', text, flags=re.DOTALL)
    text = re.sub(r'Đối tượng khen thưởng.*?Lao động', ' ', text, flags=re.DOTALL)
    text = re.sub(r'Thứ tự.*?(?=Nhà trường)', ' ', text, flags=re.DOTALL)
    text = re.sub(r'Trường, khoa, viện đào tạo.*?Khoa đại cương', ' ', text, flags=re.DOTALL)
    text = re.sub(r'Các phòng thí nghiệm đầu tư tập trung.*?Viện Công nghệ', ' ', text, flags=re.DOTALL)
    
    # 4. Loại bỏ các từ khóa thừa khác
    text = text.replace('Năm', ' ').replace('Ngày', ' ')
    
    # 5. Loại bỏ nhiều khoảng trắng thừa
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def scrape_content_from_url(url: str) -> str:
    """
    Sử dụng WebBaseLoader của LangChain để lấy nội dung chính của một trang web.
    Trả về nội dung dưới dạng văn bản thuần túy.
    """
    try:
        print(f"   -> Đang scrape url: {url}")
        # WebBaseLoader được thiết kế để tải và phân tích cú pháp HTML
        loader = WebBaseLoader(url)
        # Tải tài liệu
        docs = loader.load()
        # Nối nội dung của tất cả các tài liệu (thường chỉ có 1)
        content = " ".join([doc.page_content for doc in docs])
        # Thay thế nhiều khoảng trắng và dòng mới bằng một khoảng trắng duy nhất
        cleaned_content = ' '.join(content.split())
        return cleaned_content
    except Exception as e:
        print(f"   -> Lỗi khi scrape url {url}: {e}")
        return ""

if __name__ == "__main__":
    print(search_website("các trường, khoa, viện của Đại học Bách Khoa Hà Nội", num_results=2))