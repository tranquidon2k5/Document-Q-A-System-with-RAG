import re
import gtts
from vietnam_number import n2w
from datetime import datetime
import requests
import io
from fastapi import Response, HTTPException

# Từ điển dịch tên tháng sang tiếng Việt
MONTHS_VI = {
    'January': 'tháng Một',
    'February': 'tháng Hai',
    'March': 'tháng Ba',
    'April': 'tháng Tư',
    'May': 'tháng Năm',
    'June': 'tháng Sáu',
    'July': 'tháng Bảy',
    'August': 'tháng Tám',
    'September': 'tháng Chín',
    'October': 'tháng Mười',
    'November': 'tháng Mười Một',
    'December': 'tháng Mười Hai'
}

def preprocess_text(text: str) -> str:
    """
    Tiền xử lý văn bản: chuyển số, ngày tháng, ký tự đặc biệt, viết tắt sang dạng đầy đủ.
    """
    # 1. Mở rộng từ viết tắt (Ưu tiên số 1)
    abbreviations = {
        "sv": "sinh viên",
        "hcm": "hồ chí minh",
        "CNTT&TT" : "công nghệ thông tin và truyền thông"
    }
    for abbr, full_text in abbreviations.items():
        text = re.sub(r'\b' + re.escape(abbr) + r'\b', full_text, text, flags=re.IGNORECASE)

    # 2. Chuyển đổi ngày tháng (Dùng datetime - Ưu tiên số 2)
    matches = list(re.finditer(r'\b(\d{1,2}/\d{1,2}/\d{4})\b', text))
    if matches:
        processed_text_parts = []
        last_index = 0
        for match in matches:
            date_str = match.group(0)
            try:
                date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                
                day_str = n2w(date_obj.strftime("%d"))
                month_str = MONTHS_VI[date_obj.strftime("%B")]
                year_str = n2w(date_obj.strftime("%Y"))
                
                formatted_date = f"ngày {day_str} {month_str} năm {year_str}"
                
                processed_text_parts.append(text[last_index:match.start()])
                processed_text_parts.append(formatted_date)
            except (ValueError, IndexError):
                processed_text_parts.append(text[last_index:match.end()])
            
            last_index = match.end()
        
        processed_text_parts.append(text[last_index:])
        text = ''.join(processed_text_parts)

    # 3. Chuyển đổi các con số còn lại thành chữ (Ưu tiên số 3)
    matches = list(re.finditer(r'(\d[\d\.,]*)', text))
    if matches:
        processed_text_parts = []
        last_index = 0
        for match in matches:
            processed_text_parts.append(text[last_index:match.start()])
            number_str = match.group(0).replace('.', '').replace(',', '')
            try:
                processed_text_parts.append(n2w(number_str))
            except (ValueError, IndexError):
                processed_text_parts.append(match.group(0))
            last_index = match.end()
        processed_text_parts.append(text[last_index:])
        text = ''.join(processed_text_parts)
    
    # 4. Thay thế ký tự đặc biệt (Ưu tiên số 4 - Cuối cùng)
    # Bây giờ, chuỗi ngày tháng đã được xử lý xong, không còn ký tự '/'
    text = text.replace("&", " và ")
    text = text.replace("/", " trên ")
    text = text.replace("lẽ", "")
    
    # 5. Loại bỏ các ký tự không mong muốn và khoảng trắng thừa
    # Tinh chỉnh regex để xử lý tốt hơn
    print(text)
    return re.sub(r'\s+', ' ', text).strip()

EXTERNAL_TTS_URL = "https://bff88f795a6b.ngrok-free.app"
def get_speech(text : str, speaker_id : int):
    """
    Ưu tiên 1: Gọi API TTS ngoài qua Ngrok.
    Ưu tiên 2: Nếu thất bại, dùng gTTS làm phương án dự phòng.
    """
    
    # --- ƯU TIÊN 1: THỬ GỌI API BÊN NGOÀI ---
    if EXTERNAL_TTS_URL:
        print(f"--> [Ưu tiên 1] Thử gọi API ngoài: {EXTERNAL_TTS_URL}")
        print("Văn bản cần xử lý: ", text)
        print("Option giọng đọc: ", speaker_id)
        
        try:
            external_payload = {"text": preprocess_text(text), "speaker_id": speaker_id}
            # Đặt timeout hợp lý để không phải chờ quá lâu
            response = requests.post(f"{EXTERNAL_TTS_URL}/tts", json=external_payload, timeout=60)

            # Nếu request thành công (status code 2xx)
            if response.ok:
                print("--> [Ưu tiên 1] Thành công! Trả về audio từ API ngoài.")
                return Response(content=response.content, media_type='audio/wav')
            else:
                # Nếu service trả về lỗi (4xx, 5xx), ghi nhận và chuyển sang gTTS
                print(f"--> [Ưu tiên 1] Thất bại. Status: {response.status_code}. Chuyển sang gTTS.")

        except requests.exceptions.RequestException as e:
            print(f"--> [Ưu tiên 1] Thất bại. Lỗi mạng hoặc timeout: {e}. Chuyển sang gTTS.")

    # --- ƯU TIÊN 2 (DỰ PHÒNG): SỬ DỤNG GTTS ---
    print("--> [Ưu tiên 2] Sử dụng gTTS làm phương án dự phòng.")
    try:
        mp3_fp = io.BytesIO()
        tts = gtts.gTTS(text=text, lang='vi')
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)

        # gTTS trả về audio/mpeg (MP3)
        return Response(content=mp3_fp.read(), media_type="audio/mpeg")

    except Exception as e:
        print(f"--> [Ưu tiên 2] Lỗi khi tạo audio bằng gTTS: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi server nội bộ: {str(e)}")