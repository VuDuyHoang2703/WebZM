"""
HỆ THỐNG AI DỊCH ẢNH TỰ ĐỘNG NÂNG CẤP - PHƯƠNG PHÁP 2 (BLOCK MERGING & TYPOGRAPHY V3)
- Tự động gom khối văn bản cùng dòng và tiêu đề 2 dòng thành câu hoàn chỉnh
- Dịch chuẩn ngữ cảnh STEM / Robotics (Nhựa ABS, Mã sản phẩm, Trọng lượng bộ...)
- Chống đè chữ: Tự động đo khoảng cách tới cột bên cạnh (Collision Prevention)
- Đồng nhất 1 cỡ font duy nhất cho cả khối và tự động xuống dòng (Word Wrap)
- Phục hồi nền tự nhiên bằng Inpainting (không dùng hộp màu đặc)
- Bảo toàn 100% thương hiệu gốc (ZMROBO, RoboRun, WiseBot, Scratch, Python...)
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

# 1. Từ điển chuyên ngành STEM / Robotics & Phần cứng chuẩn xác
EXACT_REPLACEMENTS = {
    # Bảng thông số kỹ thuật (Spec Table)
    'Product Name': 'Tên sản phẩm',
    'ProductName': 'Tên sản phẩm',
    'Model': 'Mã sản phẩm',
    'Material': 'Chất liệu',
    'Abs,Etc.': 'Nhựa ABS, v.v.',
    'Abs, Etc.': 'Nhựa ABS, v.v.',
    'ABS,Etc.': 'Nhựa ABS, v.v.',
    'ABS': 'Nhựa ABS',
    'Packaging Type': 'Quy cách đóng gói',
    'Colorbox': 'Hộp màu',
    'Set Weight': 'Trọng lượng bộ',
    'About0.6KG': 'Khoảng 0.6 kg',
    'About 0.6KG': 'Khoảng 0.6 kg',
    'Package Dimensions': 'Kích thước hộp',
    'Model Weight': 'Trọng lượng mô hình',
    'About0.3KG': 'Khoảng 0.3 kg',
    'About 0.3KG': 'Khoảng 0.3 kg',
    'Suitable Age': 'Độ tuổi phù hợp',
    "User'sManual": 'Sách hướng dẫn',
    "User's Manual": 'Sách hướng dẫn',
    'Yes': 'Có',
    'Number Of Courses': 'Số bài học',
    'Number of Courses': 'Số bài học',
    'Numberof Courses': 'Số bài học',
    'Stock Code:002599': 'Mã CK: 002599',
    'Stock Code': 'Mã chứng khoán',
    'Controller': 'Bộ điều khiển',
    'Main Controller': 'Bộ điều khiển chính',
    
    # Bo mạch & Cổng kết nối & Cảm biến
    'Designed for introductory programming': 'Thiết kế cho lập trình nhập môn',
    'Designedfor introductoryprogramming': 'Thiết kế cho lập trình nhập môn',
    'Easy to get started': 'Dễ dàng bắt đầu',
    'Easyto getstarted': 'Dễ dàng bắt đầu',
    'Easy to implement programming': 'Dễ dàng thực hành lập trình',
    'Easytoimplementprogramming': 'Dễ dàng thực hành lập trình',
    'Extensible functions': 'Chức năng mở rộng phong phú',
    'Extensiblefunctions': 'Chức năng mở rộng phong phú',
    'ADC indicator': 'Đèn báo ADC',
    'ADCindicator': 'Đèn báo ADC',
    'Full color LED': 'Đèn LED đa màu (RGB)',
    'FullcolorLED': 'Đèn LED đa màu (RGB)',
    'FullcolorLED-': 'Đèn LED đa màu (RGB)',
    'Full color LED-': 'Đèn LED đa màu (RGB)',
    'ADC interface': 'Cổng cắm cảm biến (ADC)',
    'ADCinterface': 'Cổng cắm cảm biến (ADC)',
    '(back of board)': '(mặt sau bo mạch)',
    '(backofboard)': '(mặt sau bo mạch)',
    'Motor interface': 'Cổng cắm động cơ',
    'Motorinterface': 'Cổng cắm động cơ',
    'Servo motor interface': 'Cổng cắm Servo',
    'Servomotorinterface': 'Cổng cắm Servo',
    'Pc interface-': 'Cổng kết nối máy tính',
    'Pcinterface-': 'Cổng kết nối máy tính',
    'Buzzer': 'Còi chíp (Buzzer)',
    'Microphone': 'Micro thu âm',
    'Bluetooth': 'Mô-đun Bluetooth',
    'Infrared receiver': 'Mắt thu hồng ngoại',
    'Infraredreceiver': 'Mắt thu hồng ngoại',
    'Left button-': 'Nút bấm trái',
    'Leftbutton-': 'Nút bấm trái',
    'Right button': 'Nút bấm phải',
    'Rightbutton': 'Nút bấm phải',
    'Power': 'Nút nguồn',
    'DC Power interface': 'Cổng nguồn DC',
    'DCPowerinterface': 'Cổng nguồn DC',
    'Lithium battery interface': 'Cổng pin Lithium',
    'Lithiumbatteryinterface': 'Cổng pin Lithium',
    'Work indicating light': 'Đèn báo hoạt động',
    'Workindicatinglight': 'Đèn báo hoạt động',
    'TYPE-C interface': 'Cổng Type-C',
    'TYPE-Cinterface': 'Cổng Type-C',
    'Charging indicator': 'Đèn báo sạc',
    'Rich hardware configuration and multiple expansion ports': 'Cấu hình phần cứng phong phú & nhiều cổng mở rộng',
    'Rich hardware configuration': 'Cấu hình phần cứng phong phú',
    'multiple expansion ports': 'nhiều cổng mở rộng',
    'Supports simultaneous access to 8 sensors': 'Hỗ trợ kết nối đồng thời 8 cảm biến',
    'Support simultaneous access to 2 motors': 'Hỗ trợ kết nối đồng thời 2 động cơ',
    'Attracting children with cool modes': 'Thu hút trẻ em với các chế độ thú vị',
    'Automatic obstacle avoidance mode': 'Chế độ tự động tránh chướng ngại vật',
    'Scratch programming': 'Lập trình Scratch',
    'Get sensor data': 'Thu thập dữ liệu cảm biến',
    'Exercise logic thinking': 'Rèn luyện tư duy logic',
    'Custom Course Map': 'Bản đồ sa bàn tùy chỉnh',
    'Matched courses': 'Giáo trình đồng bộ',
    'Track maps and courses': 'Bản đồ đường đua & bài học',
    'List of courses launched': 'Danh sách bài học phát hành',
    'Course content display': 'Nội dung bài học',
    'Attachment:Model size after assembly': 'Kích thước mô hình sau khi lắp ráp',
    'Attachment:Model size afterassembly': 'Kích thước mô hình sau khi lắp ráp',
    'Lead children to the road of programming': 'Dẫn lối trẻ em bước vào con đường lập trình',
    'Exercise ability': 'Rèn luyện kỹ năng thực hành',
    'Comprehend the structural': 'Thấu hiểu cấu trúc cơ khí',
    'DIY': 'Tự tay chế tạo (DIY)',
    'Assembling': 'Lắp ráp mô hình',
    'Face Recognition': 'Nhận dạng khuôn mặt',
    
    # Giáo dục & Tiếng Trung
    '创客机器人教育': 'Giáo dục Robot Maker',
    '契合创客机器人教育': 'Phù hợp giáo dục Robot Maker',
    '契合创客机器人、STEAM、人工智能教育': 'Phù hợp Robot Maker, STEAM & Giáo dục AI',
    '契合创客机器人': 'Phù hợp Robot Maker',
    '人工智能教育': 'Giáo dục Trí tuệ Nhân tạo',
    'STEAM教育': 'Giáo dục STEAM',
    '开始扮演': 'Bắt đầu mô phỏng',
    '任务': 'Nhiệm vụ',
    '任务一': 'Nhiệm vụ 1',
    '任务二': 'Nhiệm vụ 2',
    '任务三': 'Nhiệm vụ 3',
    '创意扩展': 'Mở rộng sáng tạo',
}

# Thương hiệu & Mã phần cứng giữ nguyên bản quyền
PROTECTED_BRANDS = {
    'ZMROBO', 'ZINROBO', 'ROBO', 'ROBOT', 'ROBORUN', 'RoboRun', 'RoboMaker',
    'WiseBot', 'WiseChild', 'WiseChild 2', 'Alpha Set', 'Beta Set', 'Alpha X',
    'Innovation Storm', 'Intelligence Storm', 'Defender WiseKit', 'Creative Expansion',
    'Robot Sensor', 'CI-RCU', 'CSV', '1799', '2101', '2104', '2106', '2108', '2109',
    '2321', '2322', '2323', '2325', '2421', '2495', '2508', '6+', '26', '25.5x20x5cm',
    'Type-C', 'TYPE-C', 'BEEP', 'AICAM', 'Scratch', 'Python', 'Micro:bit'
}

def clean_ocr_raw(t):
    t = t.strip()
    if '器人教育' in t or '合客' in t:
        return '创客机器人教育'
    if '人工' in t and ('教育' in t or '司' in t or '#' in t):
        return '人工智能教育'
    return t

TRANSLATION_CACHE = {}

def translate_phrase_v3(text):
    text = clean_ocr_raw(text)
    if not text:
        return ""
        
    for k, v in EXACT_REPLACEMENTS.items():
        if k.lower() == text.lower() or text.lower().startswith(k.lower()):
            return v
            
    if text.upper() in PROTECTED_BRANDS or text in PROTECTED_BRANDS:
        return text
        
    if text in TRANSLATION_CACHE:
        return TRANSLATION_CACHE[text]
        
    try:
        url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=vi&dt=t&q=' + urllib.parse.quote(text)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode('utf-8'))
            trans = ''.join([part[0] for part in res[0] if part[0]]).strip()
            
            # Sửa các lỗi dịch ngữ cảnh máy móc
            trans = re.sub(r'\bCơ bụng\b', 'Nhựa ABS', trans, flags=re.IGNORECASE)
            trans = re.sub(r'\bNgười mẫu\b', 'Mã sản phẩm', trans, flags=re.IGNORECASE)
            trans = re.sub(r'\bĐặt trọng lượng\b', 'Trọng lượng bộ', trans, flags=re.IGNORECASE)
            trans = re.sub(r'\bChết cho Chúa\b', '', trans, flags=re.IGNORECASE)
            trans = re.sub(r'\bĐập 2\b', 'WiseChild 2', trans, flags=re.IGNORECASE)
            trans = re.sub(r'\bHekeshe\b', 'Maker', trans, flags=re.IGNORECASE)
            trans = re.sub(r'\bPhòng Lao động #Giáo dục\b', 'Giáo dục Trí tuệ Nhân tạo', trans, flags=re.IGNORECASE)
            
            TRANSLATION_CACHE[text] = trans
            return trans
    except Exception:
        return text

def wrap_text_to_width(draw, text, font, max_width):
    words = text.split()
    if not words:
        return []
    lines = []
    curr = words[0]
    for w in words[1:]:
        test_line = curr + " " + w
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            curr = test_line
        else:
            lines.append(curr)
            curr = w
    lines.append(curr)
    return lines

def process_image_v3(src_path, out_path, engine, font_path):
    res, _ = engine(src_path)
    if not res:
        return False
        
    img_bgr = cv2.imread(src_path, cv2.IMREAD_COLOR)
    if img_bgr is None:
        return False
    h, w = img_bgr.shape[:2]
    
    # 1. Parse all detected items
    all_detected = []
    for box, text, score in res:
        pts = np.array(box, dtype=np.float32)
        min_x = float(np.min(pts[:, 0]))
        max_x = float(np.max(pts[:, 0]))
        min_y = float(np.min(pts[:, 1]))
        max_y = float(np.max(pts[:, 1]))
        t = clean_ocr_raw(text.strip())
        
        # Bỏ qua các ký tự rác đơn lẻ (như 口, 凸, 三) hoặc logo
        if len(t) == 1 and not ('\u4e00' <= t <= '\u9fff' and t in EXACT_REPLACEMENTS):
            continue
            
        is_prot = (t.upper() in PROTECTED_BRANDS or bool(re.match(r'^[\d\s\.\:\,\-\_\+\*\/\\cm%°C]+$', t)))
        
        all_detected.append({
            'pts': pts,
            'box': (min_x, min_y, max_x, max_y),
            'text': t,
            'score': score,
            'w': max_x - min_x,
            'h': max_y - min_y,
            'cy': (min_y + max_y) / 2,
            'cx': (min_x + max_x) / 2,
            'is_protected': is_prot
        })
        
    items_to_process = [it for it in all_detected if not it['is_protected']]
    if not items_to_process:
        return False
        
    # 2. Cluster / Merge items on same line or connected titles
    merged_items = []
    used = set()
    items_to_process = sorted(items_to_process, key=lambda it: (it['cy'], it['box'][0]))
    
    for i, it1 in enumerate(items_to_process):
        if i in used:
            continue
        cluster = [it1]
        used.add(i)
        
        for j, it2 in enumerate(items_to_process[i+1:], i+1):
            if j in used:
                continue
            if abs(it1['cy'] - it2['cy']) < 0.4 * min(it1['h'], it2['h']):
                gap = it2['box'][0] - cluster[-1]['box'][2]
                if 0 <= gap <= 1.4 * max(it1['h'], it2['h']):
                    cluster.append(it2)
                    used.add(j)
                    
        # Check vertical title merge (Designed for / introductory programming)
        if len(cluster) == 1:
            for j, it2 in enumerate(items_to_process[i+1:], i+1):
                if j in used:
                    continue
                x_overlap = min(it1['box'][2], it2['box'][2]) - max(it1['box'][0], it2['box'][0])
                v_gap = it2['box'][1] - it1['box'][3]
                if x_overlap > 0.4 * min(it1['w'], it2['w']) and 0 <= v_gap <= 0.8 * it1['h']:
                    comb = it1['text'] + " " + it2['text']
                    if any(k in comb for k in ['Designed', 'Rich', 'Attract', 'Expand', 'Course', 'Attachment', 'Lead']):
                        cluster.append(it2)
                        used.add(j)
                        break
                        
        all_pts = np.concatenate([c['pts'] for c in cluster], axis=0)
        c_min_x = max(0, int(np.min(all_pts[:, 0])) - 2)
        c_max_x = min(w, int(np.max(all_pts[:, 0])) + 2)
        c_min_y = max(0, int(np.min(all_pts[:, 1])) - 2)
        c_max_y = min(h, int(np.max(all_pts[:, 1])) + 2)
        
        comb_text = " ".join([c['text'] for c in cluster])
        vn_text = translate_phrase_v3(comb_text)
        
        # Calculate available width with strict collision prevention
        closest_right_x = w
        for other in all_detected:
            if other['box'][0] > c_max_x - 5:
                # Same vertical band
                if abs(other['cy'] - ((c_min_y + c_max_y)/2)) < max(c_max_y - c_min_y, other['h']) * 0.9:
                    if other['box'][0] < closest_right_x:
                        closest_right_x = other['box'][0]
                        
        max_safe_w = max(c_max_x - c_min_x, int(closest_right_x - c_min_x - 8))
        
        merged_items.append({
            'box': (c_min_x, c_min_y, c_max_x, c_max_y),
            'orig_text': comb_text,
            'vn_text': vn_text,
            'orig_h': np.mean([c['h'] for c in cluster]),
            'max_w': max_safe_w,
            'pts': all_pts
        })
        
    # 3. Create Inpaint Mask
    mask = np.zeros((h, w), dtype=np.uint8)
    for it in merged_items:
        cv2.rectangle(mask, (it['box'][0], it['box'][1]), (it['box'][2], it['box'][3]), 255, -1)
        
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated_mask = cv2.dilate(mask, kernel, iterations=2)
    inpainted_bgr = cv2.inpaint(img_bgr, dilated_mask, inpaintRadius=4, flags=cv2.INPAINT_TELEA)
    
    img_pil = Image.fromarray(cv2.cvtColor(inpainted_bgr, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    # 4. Render Typography with Uniform Font Size & Word Wrap
    for it in merged_items:
        bx1, by1, bx2, by2 = it['box']
        bw = bx2 - bx1
        bh = by2 - by1
        vn_t = it['vn_text']
        
        if not vn_t or vn_t.upper() in PROTECTED_BRANDS:
            continue
            
        crop = inpainted_bgr[by1:by2, bx1:bx2]
        mean_c = crop.mean(axis=(0, 1))
        lum = 0.114 * mean_c[0] + 0.587 * mean_c[1] + 0.299 * mean_c[2]
        text_color = (20, 20, 20) if lum > 135 else (255, 255, 255)
        
        base_font_size = max(11, int(it['orig_h'] * 0.82))
        avail_w = it['max_w']
        
        font_size = base_font_size
        while font_size >= 10:
            font = ImageFont.truetype(font_path, font_size)
            lines = wrap_text_to_width(draw, vn_t, font, avail_w)
            line_height = int(font_size * 1.25)
            total_text_h = len(lines) * line_height
            if total_text_h <= max(bh * 1.5, line_height + 4):
                break
            font_size -= 1
            
        font = ImageFont.truetype(font_path, font_size)
        lines = wrap_text_to_width(draw, vn_t, font, avail_w)
        line_height = int(font_size * 1.25)
        total_text_h = len(lines) * line_height
        
        start_y = by1 + max(0, (bh - total_text_h) // 2)
        for line_idx, line in enumerate(lines):
            draw.text((bx1 + 2, start_y + line_idx * line_height), line, fill=text_color, font=font)
            
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if out_path.lower().endswith(('.jpg', '.jpeg')):
        img_pil.save(out_path, quality=98)
    else:
        img_pil.save(out_path)
    return merged_items

def main():
    print("==========================================================================")
    print("   KHỞI ĐỘNG HỆ THỐNG AI DỊCH ẢNH NÂNG CẤP V3 (BLOCK MERGING & TYPO)     ")
    print("==========================================================================")
    
    engine = RapidOCR()
    font_path = r"C:\Windows\Fonts\segoeui.ttf"
    if not os.path.exists(font_path):
        font_path = r"C:\Windows\Fonts\arial.ttf"
        
    print(f"Font chữ               : {font_path}")
    print(f"Thư mục nguồn (ảnh gốc): {SRC_DIR}")
    print(f"Thư mục đích (ảnh dịch): {OUT_DIR}")
    print("--------------------------------------------------------------------------")
    
    kit_folders = sorted([f for f in os.listdir(SRC_DIR) if os.path.isdir(os.path.join(SRC_DIR, f))])
    kit_folders = [f for f in kit_folders if not f.startswith("JMC-SV-1707")]
    
    total_kits = len(kit_folders)
    print(f"Tổng số bộ sản phẩm cần xử lý: {total_kits} bộ")
    
    all_translated_records = []
    total_imgs_processed = 0
    total_imgs_translated = 0
    
    csv_log_path = os.path.join(OUT_DIR, "DANH_SACH_DOI_CHIEU.csv")
    csv_file = open(csv_log_path, 'w', newline='', encoding='utf-8')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["STT", "Bo_San_Pham", "Ten_File", "Chu_Goc_Gom_Khoi", "Ban_Dich_Tieng_Viet"])
    
    start_time = time.time()
    
    for k_idx, kit in enumerate(kit_folders, 1):
        src_kit_dir = os.path.join(SRC_DIR, kit)
        out_kit_dir = os.path.join(OUT_DIR, kit)
        
        images = sorted([f for f in os.listdir(src_kit_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))])
        print(f"\n[{k_idx}/{total_kits}] BỘ: {kit} ({len(images)} ảnh)", flush=True)
        
        kit_trans_count = 0
        for i_idx, img_name in enumerate(images, 1):
            src_img_p = os.path.join(src_kit_dir, img_name)
            out_img_p = os.path.join(out_kit_dir, img_name)
            
            total_imgs_processed += 1
            t0 = time.time()
            
            try:
                items = process_image_v3(src_img_p, out_img_p, engine, font_path)
            except Exception as e:
                items = None
                print(f"   [{i_idx}/{len(images)}] {img_name:<16} -> Lỗi: {e}", flush=True)
                continue
                
            dt = time.time() - t0
            
            if items:
                kit_trans_count += 1
                total_imgs_translated += 1
                sample = ", ".join([f"{x['orig_text']} -> {x['vn_text']}" for x in items[:2]])
                print(f"   [{i_idx:02d}/{len(images):02d}] {img_name:<16} -> ✅ ĐÃ GOM KHỐI ({len(items)} khối, {dt:.1f}s): {sample[:65]}...", flush=True)
                
                for item in items:
                    csv_writer.writerow([
                        len(all_translated_records) + 1,
                        kit,
                        img_name,
                        item['orig_text'],
                        item['vn_text']
                    ])
                    all_translated_records.append((kit, img_name, item['orig_text'], item['vn_text']))
                csv_file.flush()
            else:
                print(f"   [{i_idx:02d}/{len(images):02d}] {img_name:<16} -> ⚪ Bỏ qua / Không có chữ cần dịch ({dt:.1f}s)", flush=True)
                
        print(f"   >>> Hoàn tất bộ {kit}: {kit_trans_count}/{len(images)} ảnh đã dịch đẹp.", flush=True)
        
    csv_file.close()
    
    elapsed = time.time() - start_time
    print("\n==========================================================================")
    print("                      HOÀN TẤT NÂNG CẤP DỊCH ẢNH V3!                     ")
    print(f"  Thời gian thực thi : {elapsed/60:.1f} phút")
    print(f"  Tổng ảnh đã quét   : {total_imgs_processed} ảnh")
    print(f"  Tổng ảnh đã làm lại: {total_imgs_translated} ảnh")
    print(f"  Thư mục lưu trữ    : {OUT_DIR}")
    print(f"  Bảng tra cứu CSV   : {csv_log_path}")
    print("==========================================================================")

if __name__ == "__main__":
    main()
