"""
HỆ THỐNG AI DỊCH ẢNH TỰ ĐỘNG - PHƯƠNG PHÁP 2 (INPAINTING & TYPOGRAPHY)
- Đọc từng ảnh trong 13 bộ sản phẩm được chỉ định
- Nhận diện văn bản tiếng Trung / tiếng Anh bằng RapidOCR
- Dịch thuật ngữ STEM / Robotics chuẩn xác sang tiếng Việt
- Phục hồi nền bằng thuật toán Inpainting (không dùng hộp màu đặc)
- Vẽ chữ tiếng Việt chất lượng cao (Segoe UI / Arial) với tỷ lệ tự động
- Lưu kết quả vào bo_anh_da_dich/ với tên file và thư mục giống hệt ảnh gốc
"""

import os
import sys
import re
import csv
import json
import time
import urllib.request
import urllib.parse
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from rapidocr_onnxruntime import RapidOCR

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(BASE_DIR, "bo_anh_san_pham")
OUT_DIR = os.path.join(BASE_DIR, "bo_anh_da_dich")

os.makedirs(OUT_DIR, exist_ok=True)

# 1. Từ điển chuyên ngành STEM / Robotics & Maker
STEM_GLOSSARY = {
    # Thuật ngữ chung & Giáo dục
    '创客': 'Maker',
    '创客机器人': 'Robot Maker',
    '契合创客机器人教育': 'Phù hợp giáo dục Robot Maker',
    '契合创客机器人、STEAM、人工智能教育': 'Phù hợp Robot Maker, STEAM & Giáo dục AI',
    '契合创客机器人': 'Phù hợp Robot Maker',
    '人工智能教育': 'Giáo dục Trí tuệ Nhân tạo',
    'STEAM教育': 'Giáo dục STEAM',
    'STEAM': 'STEAM',
    '微信小程序': 'Mini App WeChat',
    '微信公众号': 'Trang WeChat chính thức',
    '开始扮演': 'Bắt đầu mô phỏng',
    '舞蹈': 'Khiêu vũ',
    '展示': 'Trình diễn',
    '任务': 'Nhiệm vụ',
    '任务一': 'Nhiệm vụ 1',
    '任务二': 'Nhiệm vụ 2',
    '任务三': 'Nhiệm vụ 3',
    '课程内容': 'Nội dung bài học',
    '课程标题': 'Tên bài học',
    
    # Tiếng Anh chuyên ngành
    'introductory programming': 'lập trình nhập môn',
    'introductoryprogramming': 'lập trình nhập môn',
    'Designed for introductory programming': 'Thiết kế cho lập trình nhập môn',
    'Designedfor introductoryprogramming': 'Thiết kế cho lập trình nhập môn',
    'Easy to get started': 'Dễ dàng bắt đầu',
    'Easyto getstarted': 'Dễ dàng bắt đầu',
    'Easy to implement programming': 'Dễ dàng thực hành lập trình',
    'Easytoimplementprogramming': 'Dễ dàng thực hành lập trình',
    'Rich hardware configuration and multiple expansion ports': 'Cấu hình phần cứng phong phú & nhiều cổng mở rộng',
    'Richhardwareconfigurationand multipleexpansionports': 'Cấu hình phần cứng phong phú & nhiều cổng mở rộng',
    'Richhardwareconfiguration': 'Cấu hình phần cứng phong phú',
    'multipleexpansionports': 'nhiều cổng mở rộng',
    'Supports simultaneous access to 8 sensors': 'Hỗ trợ kết nối đồng thời 8 cảm biến',
    'Supportssimultaneousaccessto8sensors': 'Hỗ trợ kết nối đồng thời 8 cảm biến',
    'Support simultaneous access to 2 motors': 'Hỗ trợ kết nối đồng thời 2 động cơ',
    'Supportsimultaneousaccessto2motors': 'Hỗ trợ kết nối đồng thời 2 động cơ',
    'Attracting children with cool modes': 'Thu hút trẻ em với các chế độ thú vị',
    'Attracting children withcool modes': 'Thu hút trẻ em với các chế độ thú vị',
    'Automatic obstacle avoidance mode': 'Chế độ tự động tránh chướng ngại vật',
    'Automaticobstacleavoidancemode': 'Chế độ tự động tránh chướng ngại vật',
    'Scratch programming': 'Lập trình Scratch',
    'Scratchprogramming': 'Lập trình Scratch',
    'Get sensor data': 'Thu thập dữ liệu cảm biến',
    'Getsensordata': 'Thu thập dữ liệu cảm biến',
    'Exercise logic thinking': 'Rèn luyện tư duy logic',
    'Exerciselogicthinking': 'Rèn luyện tư duy logic',
    'Custom Course Map': 'Bản đồ sa bàn tùy chỉnh',
    'Custom CourseMap': 'Bản đồ sa bàn tùy chỉnh',
    'Matched courses': 'Giáo trình đồng bộ',
    'Track maps and courses': 'Bản đồ đường đua & bài học',
    'Trackmapsandcourses': 'Bản đồ đường đua & bài học',
    'List of courses launched': 'Danh sách bài học phát hành',
    'Listofcourseslaunched': 'Danh sách bài học phát hành',
    'Course content display': 'Hiển thị nội dung bài học',
    'Coursecontentdisplay': 'Hiển thị nội dung bài học',
    'Attachment:Model size after assembly': 'Kích thước mô hình sau khi lắp ráp',
    'Attachment:Model size afterassembly': 'Kích thước mô hình sau khi lắp ráp',
    'Lead children to the road of programming': 'Dẫn lối trẻ em bước vào con đường lập trình',
    'Leadchildren to theroad ofprogramming': 'Dẫn lối trẻ em bước vào con đường lập trình',
    'Exercise ability': 'Rèn luyện kỹ năng thực hành',
    'Comprehend the structural': 'Thấu hiểu cấu trúc cơ khí',
    'Comprehend thestructural': 'Thấu hiểu cấu trúc cơ khí',
    'DIY': 'Tự tay chế tạo (DIY)',
    'Assembling': 'Lắp ráp mô hình',
    'Course Title': 'Tên khóa học',
    'Course content': 'Nội dung bài học',
    
    # Cảm biến & Linh kiện
    'Infrared ranging/obstacle avoidance': 'Đo khoảng cách / Tránh vật cản hồng ngoại',
    'Ambient light detection': 'Cảm biến ánh sáng môi trường',
    'Sound detection': 'Cảm biến âm thanh',
    'Infrared remote control reception': 'Thu tín hiệu điều khiển hồng ngoại',
    'Tracking Sensor': 'Cảm biến dò đường',
    'Ultrasonic Sensor': 'Cảm biến siêu âm',
    'Color Sensor': 'Cảm biến màu sắc',
    'Touch Sensor': 'Cảm biến chạm',
    'Main Controller': 'Bộ điều khiển chính',
    'Geared Motor': 'Động cơ giảm tốc',
    'Digital Servo': 'Servo kỹ thuật số',
    'Omni Wheel': 'Bánh xe đa hướng',
}

# Các từ viết tắt, tên thương hiệu, đơn vị giữ nguyên bản quyền
PROTECTED_WORDS = {
    'ZMROBO', 'ZINROBO', 'ROBO', 'ROBOT', 'RoboMaker', 'RoboRun', 'WiseBot',
    'WiseChild', 'Alpha Set', 'Beta Set', 'Innovation Storm', 'Intelligence Storm',
    'Defender WiseKit', 'Creative Expansion', 'Robot Sensor', 'Alpha X',
    'Scratch', 'Python', 'Micro:bit', 'Bluetooth', 'USB', 'LED', 'RGB', 'DC',
    'LEGO', 'JoinMax', 'JoinMaxDigital', 'NOC', 'RIC', 'STEM', 'STEAM', 'AI'
}

# 2. Bộ dịch trực tuyến với bộ nhớ đệm
TRANSLATION_CACHE = {}

def translate_phrase(text):
    text = text.strip()
    if not text:
        return ""
        
    # Check protected words
    if text in PROTECTED_WORDS or text.upper() in PROTECTED_WORDS:
        return text
        
    # Check glossary
    if text in STEM_GLOSSARY:
        return STEM_GLOSSARY[text]
    for k, v in STEM_GLOSSARY.items():
        if k.lower() == text.lower():
            return v
            
    # Check cache
    if text in TRANSLATION_CACHE:
        return TRANSLATION_CACHE[text]
        
    # Gọi Google Translate API
    try:
        url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=vi&dt=t&q=' + urllib.parse.quote(text)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode('utf-8'))
            translated = ''.join([part[0] for part in res[0] if part[0]]).strip()
            
            # Hậu xử lý thuật ngữ
            for k, v in STEM_GLOSSARY.items():
                if k.lower() in translated.lower():
                    translated = re.sub(re.escape(k), v, translated, flags=re.IGNORECASE)
                    
            TRANSLATION_CACHE[text] = translated
            return translated
    except Exception as e:
        return text

# 3. Hàm kiểm tra văn bản có cần dịch hay không
def is_translatable(text):
    t = text.strip()
    if not t:
        return False
        
    # Bỏ qua nếu chỉ là số, kích thước, thời gian, ký tự lạ
    if re.match(r'^[\d\s\.\:\,\-\_\+\*\/\\cm%°C]+$', t, re.IGNORECASE):
        return False
    if re.match(r'^\d+(\.\d+)?(cm|mm|m|g|kg|pcs|v|a|w|mah)$', t, re.IGNORECASE):
        return False
    if re.match(r'^\d{1,2}:\d{2}$', t): # Giờ phút 2:51
        return False
    if re.match(r'^[0-9a-f]{6,}$', t, re.IGNORECASE): # Mã hex
        return False
    if t in PROTECTED_WORDS or t.upper() in PROTECTED_WORDS:
        return False
        
    # Có ký tự tiếng Trung
    if any('\u4e00' <= c <= '\u9fff' for c in t):
        return True
        
    # Có từ tiếng Anh dài >= 3 chữ cái
    words = re.findall(r'[a-zA-Z]{3,}', t)
    if words:
        # Nếu tất cả các từ đều là tên thương hiệu -> bỏ qua
        if all(w.upper() in PROTECTED_WORDS for w in words):
            return False
        return True
        
    return False

# 4. Hàm xử lý Inpainting & Typography trên một ảnh
def process_image(src_path, out_path, engine, font_path):
    res, _ = engine(src_path)
    if not res:
        return None # Không có chữ
        
    # Lọc các cụm chữ cần dịch
    items = []
    for box, text, score in res:
        clean_t = text.strip()
        if score >= 0.60 and is_translatable(clean_t):
            vn_text = translate_phrase(clean_t)
            if vn_text and vn_text.lower() != clean_t.lower():
                items.append((box, clean_t, vn_text, score))
                
    if not items:
        return None # Không có chữ nào cần dịch
        
    img_bgr = cv2.imread(src_path, cv2.IMREAD_COLOR)
    if img_bgr is None:
        return None
        
    h, w = img_bgr.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    
    # Tạo mặt nạ vùng chữ
    for box, orig_t, vn_t, sc in items:
        pts = np.array(box, dtype=np.int32)
        cv2.fillPoly(mask, [pts], 255)
        
    # Giãn mặt nạ nhẹ để khử viền ký tự
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated_mask = cv2.dilate(mask, kernel, iterations=2)
    
    # Inpaint phục hồi nền tự nhiên
    inpainted_bgr = cv2.inpaint(img_bgr, dilated_mask, inpaintRadius=4, flags=cv2.INPAINT_TELEA)
    
    # Vẽ chữ tiếng Việt chất lượng cao bằng PIL
    img_pil = Image.fromarray(cv2.cvtColor(inpainted_bgr, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    for box, orig_t, vn_t, sc in items:
        pts = np.array(box, dtype=np.int32)
        min_x = max(0, int(np.min(pts[:, 0])))
        max_x = min(w, int(np.max(pts[:, 0])))
        min_y = max(0, int(np.min(pts[:, 1])))
        max_y = min(h, int(np.max(pts[:, 1])))
        
        box_w = max_x - min_x
        box_h = max_y - min_y
        if box_w <= 0 or box_h <= 0:
            continue
            
        # Xác định độ sáng nền để chọn màu chữ tương phản
        crop = inpainted_bgr[min_y:max_y, min_x:max_x]
        mean_c = crop.mean(axis=(0, 1))
        lum = 0.114 * mean_c[0] + 0.587 * mean_c[1] + 0.299 * mean_c[2]
        text_color = (20, 20, 20) if lum > 130 else (255, 255, 255)
        
        # Tự động tính cỡ chữ để không tràn khung
        font_size = int(box_h * 0.75)
        while font_size > 8:
            try:
                font = ImageFont.truetype(font_path, font_size)
            except Exception:
                font = ImageFont.load_default()
                break
            bbox = draw.textbbox((0, 0), vn_t, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            if tw <= box_w * 1.05 and th <= box_h * 1.1:
                break
            font_size -= 1
            
        try:
            font = ImageFont.truetype(font_path, max(font_size, 9))
        except Exception:
            font = ImageFont.load_default()
            
        bbox = draw.textbbox((0, 0), vn_t, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        
        tx = min_x + (box_w - tw) // 2
        ty = min_y + (box_h - th) // 2 - bbox[1]
        
        draw.text((tx, ty), vn_t, fill=text_color, font=font)
        
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if out_path.lower().endswith(('.jpg', '.jpeg')):
        img_pil.save(out_path, quality=98)
    else:
        img_pil.save(out_path)
        
    return items

# 5. Hàm chạy toàn bộ các bộ sản phẩm
def main():
    print("==========================================================================")
    print("      KHỞI ĐỘNG HỆ THỐNG AI DỊCH ẢNH TỰ ĐỘNG - ZMROBO (CÁCH 2)           ")
    print("==========================================================================")
    
    engine = RapidOCR()
    
    font_candidates = [
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\arial.ttf"
    ]
    font_path = next((f for f in font_candidates if os.path.exists(f)), "arial.ttf")
    print(f"Font chữ: {font_path}")
    print(f"Thư mục nguồn (ảnh gốc) : {SRC_DIR}")
    print(f"Thư mục đích (ảnh dịch) : {OUT_DIR}")
    print("--------------------------------------------------------------------------")
    
    kit_folders = sorted([f for f in os.listdir(SRC_DIR) if os.path.isdir(os.path.join(SRC_DIR, f))])
    # Bỏ qua JMC-SV-1707 theo yêu cầu người dùng
    kit_folders = [f for f in kit_folders if not f.startswith("JMC-SV-1707")]
    
    total_kits = len(kit_folders)
    print(f"Tổng số bộ sản phẩm cần xử lý: {total_kits} bộ")
    
    all_translated_records = []
    total_imgs_processed = 0
    total_imgs_translated = 0
    
    csv_log_path = os.path.join(OUT_DIR, "DANH_SACH_DOI_CHIEU.csv")
    csv_file = open(csv_log_path, 'w', newline='', encoding='utf-8')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["STT", "Bo_San_Pham", "Ten_File", "Chu_Goc", "Ban_Dich_Tieng_Viet", "Do_Chinh_Xac_OCR"])
    
    start_time = time.time()
    
    for k_idx, kit in enumerate(kit_folders, 1):
        src_kit_dir = os.path.join(SRC_DIR, kit)
        out_kit_dir = os.path.join(OUT_DIR, kit)
        
        images = sorted([f for f in os.listdir(src_kit_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))])
        print(f"\n[{k_idx}/{total_kits}] BỘ: {kit} ({len(images)} ảnh)")
        
        kit_trans_count = 0
        for i_idx, img_name in enumerate(images, 1):
            src_img_p = os.path.join(src_kit_dir, img_name)
            out_img_p = os.path.join(out_kit_dir, img_name)
            
            total_imgs_processed += 1
            t0 = time.time()
            
            try:
                items = process_image(src_img_p, out_img_p, engine, font_path)
            except Exception as e:
                items = None
                print(f"   [{i_idx}/{len(images)}] {img_name:<16} -> Lỗi: {e}")
                continue
                
            dt = time.time() - t0
            
            if items:
                kit_trans_count += 1
                total_imgs_translated += 1
                sample = ", ".join([f"{x[1]} -> {x[2]}" for x in items[:2]])
                print(f"   [{i_idx:02d}/{len(images):02d}] {img_name:<16} -> ✅ ĐÃ DỊCH ({len(items)} cụm, {dt:.1f}s): {sample[:65]}...")
                
                for item in items:
                    csv_writer.writerow([
                        len(all_translated_records) + 1,
                        kit,
                        img_name,
                        item[1],
                        item[2],
                        f"{item[3]:.2f}"
                    ])
                    all_translated_records.append((kit, img_name, item[1], item[2]))
                csv_file.flush()
            else:
                print(f"   [{i_idx:02d}/{len(images):02d}] {img_name:<16} -> ⚪ Không có chữ cần dịch ({dt:.1f}s)")
                
        print(f"   >>> Đã hoàn tất bộ {kit}: {kit_trans_count}/{len(images)} ảnh đã dịch sang tiếng Việt.")
        
    csv_file.close()
    
    # Tạo cẩm nang hướng dẫn sử dụng
    readme_path = os.path.join(OUT_DIR, "HUONG_DAN_SU_DUNG.md")
    with open(readme_path, 'w', encoding='utf-8') as f_rm:
        f_rm.write("# BỘ SƯU TẬP HÌNH ẢNH ĐÃ DỊCH TIẾNG VIỆT (PHƯƠNG PHÁP 2)\n\n")
        f_rm.write(f"- Thời gian hoàn thành: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f_rm.write(f"- Tổng số bộ sản phẩm: {total_kits} bộ\n")
        f_rm.write(f"- Tổng số ảnh đã dịch: {total_imgs_translated} ảnh\n\n")
        f_rm.write("## HƯỚNG DẪN THAY THẾ VÀO HỆ THỐNG:\n\n")
        f_rm.write("1. Toàn bộ hình ảnh trong thư mục này được phân loại theo từng bộ và **GIỮ NGUYÊN 100% TÊN FILE GỐC** (ví dụ `cover.png`, `1.png`, `1799_3.jpg`...).\n")
        f_rm.write("2. Bạn hãy mở xem từng thư mục, duyệt qua các ảnh đã dịch. Nếu thấy ảnh nào không cần thiết hoặc muốn giữ ảnh gốc, bạn chỉ cần **XÓA ẢNH ĐÓ ĐI** khỏi thư mục này.\n")
        f_rm.write("3. Sau khi lọc xong những ảnh ưng ý, bạn chỉ cần copy các ảnh còn lại dán đè vào thư mục ảnh của hệ thống hoặc báo để tôi tự động ghi đè chuẩn mã.\n\n")
        f_rm.write("Xem chi tiết toàn bộ các cụm chữ đã dịch tại file: `DANH_SACH_DOI_CHIEU.csv`.\n")
        
    elapsed = time.time() - start_time
    print("\n==========================================================================")
    print("                         HOÀN TẤT TOÀN BỘ QUY TRÌNH!                      ")
    print(f"  Thời gian thực thi : {elapsed/60:.1f} phút")
    print(f"  Tổng ảnh đã quét   : {total_imgs_processed} ảnh")
    print(f"  Tổng ảnh đã dịch   : {total_imgs_translated} ảnh")
    print(f"  Thư mục lưu trữ    : {OUT_DIR}")
    print(f"  Bảng tra cứu CSV   : {csv_log_path}")
    print("==========================================================================")

if __name__ == "__main__":
    main()

