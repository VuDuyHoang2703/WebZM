"""
HỆ THỐNG AI OCR & DỊCH ẢNH TỰ ĐỘNG - ZMROBO (CONTINUOUS BACKGROUND RUNNER)
- Quét từng hình ảnh trong hệ thống
- Tự động nhận diện chữ tiếng Anh / tiếng Trung bằng RapidOCR
- Dịch sang tiếng Việt chuẩn thuật ngữ Robotics & STEM
- Vẽ đè tiếng Việt sắc nét trực tiếp lên ảnh
- Tự động lưu tiến độ vào data/ocr_image_registry.json
"""

import os
import sys
import json
import re
import time
import argparse
import urllib.request
import urllib.parse
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, "media")
DATA_DIR = os.path.join(BASE_DIR, "data")
REGISTRY_FILE = os.path.join(DATA_DIR, "ocr_image_registry.json")

os.makedirs(DATA_DIR, exist_ok=True)

# 1. Từ điển chuyên ngành STEM / Robotics ưu tiên cao
STEM_GLOSSARY = {
    # Tên mô hình sa bàn & thi đấu
    'Star Map Decoding Model': 'Mô hình Giải mã Bản đồ sao',
    'Energy Refill Model': 'Mô hình Nạp Năng lượng',
    'Beacon Model': 'Mô hình Hải đăng',
    'SuperTrackompetition': 'Cuộc thi Siêu Đường đua',
    'SuperTrack Competition': 'Cuộc thi Siêu Đường đua',
    'Super Track Competition': 'Cuộc thi Siêu Đường đua',
    'SUPERAI': 'SUPER AI',
    'Super AI': 'Super AI',
    'End': 'Vạch Đích',
    'Start': 'Vạch Xuất phát',
    'Competition Area': 'Khu vực Thi đấu',
    'Task Area': 'Khu vực Nhiệm vụ',
    'Field Map': 'Bản đồ thi đấu',
    'Competition Field Map': 'Bản đồ sân thi đấu',
    'Task Props': 'Đạo cụ nhiệm vụ',
    'Robot Model': 'Mô hình Robot',
    'Early Soccer': 'Robot Đá bóng Vỡ lòng',
    
    # Bộ điều khiển & Cảm biến
    'Controller': 'Bộ điều khiển',
    'Main Controller': 'Bộ điều khiển chính',
    'Master Controller': 'Bộ điều khiển trung tâm',
    'Micro Controller': 'Vi điều khiển',
    'Smart Controller': 'Bộ điều khiển thông minh',
    'Tracking Sensor': 'Cảm biến dò đường',
    'Smart Tracking Sensor': 'Cảm biến theo dõi thông minh',
    'Ultrasonic Sensor': 'Cảm biến siêu âm',
    'Color Sensor': 'Cảm biến màu sắc',
    'Light Sensor': 'Cảm biến ánh sáng',
    'Touch Sensor': 'Cảm biến chạm',
    'Sound Sensor': 'Cảm biến âm thanh',
    'Infrared Sensor': 'Cảm biến hồng ngoại',
    'Temperature Sensor': 'Cảm biến nhiệt độ',
    'Flame Sensor': 'Cảm biến ngọn lửa',
    'Hall Sensor': 'Cảm biến Hall',
    'Magnetic Sensor': 'Cảm biến từ tính',
    'Gyro Sensor': 'Cảm biến con quay hồi chuyển',
    'Weight Sensor': 'Cảm biến trọng lượng',
    'Pressure Sensor': 'Cảm biến áp suất',
    'Gas Sensor': 'Cảm biến chất khí',
    'Voice Module': 'Mô-đun giọng nói',
    'Speech Recognition': 'Nhận dạng giọng nói',
    'Display Module': 'Mô-đun màn hình',
    'LED Module': 'Mô-đun LED',
    'Buzzer Module': 'Mô-đun còi báo',
    
    # Động cơ & Cơ khí
    'Digital Servo': 'Servo kỹ thuật số',
    'Digital Servo Small': 'Servo kỹ thuật số nhỏ',
    'Motor': 'Động cơ',
    'DC Motor': 'Động cơ DC',
    'Geared Motor': 'Động cơ giảm tốc',
    'Stepper Motor': 'Động cơ bước',
    'High Torque': 'Mô-men xoắn cao',
    'Metal Gear': 'Bánh răng kim loại',
    'Quiet and Durable': 'Yên tĩnh và bền bỉ',
    'Robotic Arm': 'Cánh tay robot',
    'Chassis': 'Khung gầm',
    'Wheel': 'Bánh xe',
    'Track Wheel': 'Bánh xích',
    'Omni Wheel': 'Bánh xe đa hướng',
    'Mecanum Wheel': 'Bánh xe Mecanum',
    
    # Tiếng Trung chuyên ngành
    '智能循迹传感器': 'Cảm biến dò đường thông minh',
    '超声波传感器': 'Cảm biến siêu âm',
    '颜色传感器': 'Cảm biến màu sắc',
    '主控器': 'Bộ điều khiển chính',
    '微型控制器': 'Bộ vi điều khiển',
    '数字舵机': 'Servo kỹ thuật số',
    '减速电机': 'Động cơ giảm tốc',
    '直流电机': 'Động cơ DC',
    '金属齿轮': 'Bánh răng kim loại',
    '大扭矩': 'Mô-men xoắn cao',
    '超级轨迹赛': 'Cuộc thi Siêu Đường đua',
    '星际巡航': 'Hành trình Ngôi sao',
    '星际探索': 'Thám hiểm Ngôi sao',
    '火星探索': 'Thám hiểm Sao Hỏa',
    '比赛地图': 'Bản đồ thi đấu',
    '终点': 'Vạch Đích',
    '起点': 'Vạch Xuất phát',
    '任务区': 'Khu vực Nhiệm vụ',
    '学校荣誉': 'Danh dự của trường',
}

# 2. Dịch văn bản thông minh (kết hợp Glossary + Google Translate API)
def translate_text(text):
    text_clean = text.strip()
    if not text_clean:
        return ""
        
    # Bỏ qua nếu chỉ là số hoặc mã kỹ thuật (ví dụ: 3000mm, 2026, JMC-NY-2681)
    if re.match(r'^[\d\s\.,\-\+\*\/xX%]+$', text_clean):
        return text_clean
    if re.match(r'^\d+\s*(?:mm|cm|m|kg|g|V|A|mAh|rpm)$', text_clean, re.IGNORECASE):
        return text_clean
    if re.match(r'^[A-Z0-9]{2,4}\-[A-Z0-9]{2,4}\-[A-Z0-9]{3,6}$', text_clean):
        return text_clean

    # Kiểm tra trong từ điển chuyên ngành trước
    if text_clean in STEM_GLOSSARY:
        return STEM_GLOSSARY[text_clean]

    for k, v in STEM_GLOSSARY.items():
        if k.lower() == text_clean.lower():
            return v

    # Fallback: Dịch qua Google Translate API
    try:
        url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=vi&dt=t&q=' + urllib.parse.quote(text_clean)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            translated = ''.join([part[0] for part in data[0] if part[0]]).strip()
            if translated:
                return translated
    except Exception:
        pass

    return text_clean

# 3. Quản lý Registry lưu tiến độ
def load_registry():
    if os.path.exists(REGISTRY_FILE):
        try:
            with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"summary": {"total_images": 0, "translated": 0, "no_text": 0, "pending": 0, "errors": 0}, "images": {}}

def save_registry(registry):
    total = len(registry["images"])
    trans_count = sum(1 for v in registry["images"].values() if v.get("status") == "translated")
    no_text_count = sum(1 for v in registry["images"].values() if v.get("status") == "no_text")
    error_count = sum(1 for v in registry["images"].values() if v.get("status") == "error")
    pending_count = total - trans_count - no_text_count - error_count

    registry["summary"] = {
        "total_images": total,
        "translated": trans_count,
        "no_text": no_text_count,
        "pending": pending_count,
        "errors": error_count,
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    temp_file = REGISTRY_FILE + ".tmp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    if os.path.exists(REGISTRY_FILE):
        os.replace(temp_file, REGISTRY_FILE)
    else:
        os.rename(temp_file, REGISTRY_FILE)

def scan_all_images(registry):
    all_files = []
    for root, dirs, files in os.walk(MEDIA_DIR):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in ['.png', '.jpg', '.jpeg']:
                if f.startswith('icon-') or f.endswith('_demo.png'):
                    continue
                full_p = os.path.join(root, f)
                rel_p = os.path.relpath(full_p, BASE_DIR).replace('\\', '/')
                all_files.append(rel_p)

    def sort_priority(path):
        score = 100
        p_lower = path.lower()
        if 'images/' in p_lower: score -= 50
        if 'cover/' in p_lower: score -= 40
        if '1.png' in p_lower or '3.png' in p_lower or '2.png' in p_lower: score -= 30
        if 'jmc-' in p_lower: score -= 20
        return score

    all_files.sort(key=sort_priority)

    for rel_p in all_files:
        if rel_p not in registry["images"]:
            registry["images"][rel_p] = {
                "status": "pending",
                "text_count": 0,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }

    save_registry(registry)

# 4. Xử lý OCR và vẽ đè bản dịch tiếng Việt lên một tấm ảnh
def process_single_image(rel_p, engine, font_path):
    full_p = os.path.join(BASE_DIR, os.path.normpath(rel_p))
    if not os.path.exists(full_p):
        return {"status": "error", "error": "File not found"}

    try:
        res, _ = engine(full_p)
    except Exception as e:
        return {"status": "error", "error": str(e)}

    valid_texts = []
    if res:
        for box, text, score in res:
            text_str = text.strip()
            if score >= 0.55 and len(text_str) >= 2 and any(c.isalnum() for c in text_str):
                if re.match(r'^\d+$', text_str) and len(text_str) <= 3:
                    continue
                valid_texts.append((box, text_str, score))

    if not valid_texts:
        return {"status": "no_text", "text_count": 0}

    try:
        img = Image.open(full_p).convert('RGBA')
        draw = ImageDraw.Draw(img)
        
        translated_items = []
        modified = 0

        for box, original_text, score in valid_texts:
            vn_text = translate_text(original_text)
            
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            min_x, max_x = max(0, int(min(xs))), min(img.width, int(max(xs)))
            min_y, max_y = max(0, int(min(ys))), min(img.height, int(max(ys)))
            w = max_x - min_x
            h = max_y - min_y
            
            if w <= 4 or h <= 4:
                continue

            pad = max(2, int(h * 0.1))
            crop_box = (max(0, min_x - pad), max(0, min_y - pad), min(img.width, max_x + pad), min(img.height, max_y + pad))
            
            bg_color = img.getpixel((crop_box[0], crop_box[1]))
            draw.rectangle(crop_box, fill=bg_color)
            
            luminance = (0.299 * bg_color[0] + 0.587 * bg_color[1] + 0.114 * bg_color[2])
            text_color = (15, 15, 15, 255) if luminance > 128 else (250, 250, 250, 255)
            
            font_size = max(11, int(h * 0.72))
            try:
                font = ImageFont.truetype(font_path, font_size)
            except Exception:
                font = ImageFont.load_default()

            draw.text((min_x, min_y), vn_text, fill=text_color, font=font)
            modified += 1
            translated_items.append({
                "original": original_text,
                "translated": vn_text,
                "score": round(float(score), 2)
            })

        if full_p.lower().endswith(('.jpg', '.jpeg')):
            img.convert('RGB').save(full_p, quality=95)
        else:
            img.save(full_p)

        return {
            "status": "translated",
            "text_count": modified,
            "items": translated_items,
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}

# 5. Hàm chạy chính (Main Runner)
def run_pipeline(limit=None):
    registry = load_registry()
    scan_all_images(registry)

    pending_list = [p for p, v in registry["images"].items() if v.get("status") == "pending"]

    print("==========================================================================")
    print("  BẮT ĐẦU QUY TRÌNH AI OCR & DỊCH ẢNH TỰ ĐỘNG                             ")
    print(f"  Tổng ảnh: {len(registry['images'])} | Đã dịch: {registry['summary']['translated']} | Không có chữ: {registry['summary']['no_text']} | Còn lại: {len(pending_list)}")
    print("  (Tiến độ được lưu liên tục. Bạn có thể nhấn Ctrl + C bất cứ lúc nào!)    ")
    print("==========================================================================")

    if not pending_list:
        print(">>> Toàn bộ hình ảnh đã được xử lý xong! Không còn ảnh nào ở trạng thái pending.")
        return

    print(">>> Đang nạp mô hình RapidOCR...")
    from rapidocr_onnxruntime import RapidOCR
    engine = RapidOCR()

    font_path = "C:\\Windows\\Fonts\\arialbd.ttf"
    if not os.path.exists(font_path):
        font_path = "C:\\Windows\\Fonts\\arial.ttf"

    count = 0
    max_process = limit if limit else len(pending_list)
    unsaved_no_text = 0

    for i, rel_p in enumerate(pending_list[:max_process], 1):
        filename = os.path.basename(rel_p)
        print(f"[{i}/{max_process}] Đang đọc: {rel_p} ... ", end="", flush=True)
        
        t0 = time.time()
        try:
            result = process_single_image(rel_p, engine, font_path)
        except Exception as e:
            result = {"status": "error", "error": str(e)}
        dt = time.time() - t0

        status = result.get("status")
        registry["images"][rel_p].update(result)

        if status == "translated":
            save_registry(registry)
            items = result.get("items", [])
            sample = ", ".join([f"{x['original']} -> {x['translated']}" for x in items[:2]])
            print(f"✅ ĐÃ DỊCH ({len(items)} chữ, {dt:.1f}s): {sample}", flush=True)
            count += 1
            unsaved_no_text = 0
        elif status == "no_text":
            unsaved_no_text += 1
            if unsaved_no_text >= 10:
                save_registry(registry)
                unsaved_no_text = 0
            print(f"⚪ Không có chữ ({dt:.1f}s)", flush=True)
        else:
            save_registry(registry)
            print(f"❌ Lỗi ({result.get('error')})", flush=True)

    save_registry(registry)
    print("\n==========================================================================")
    print(f"  HOÀN TẤT ĐỢT XỬ LÝ! Đã dịch xong {count} ảnh.")
    print(f"  Tổng trạng thái: Đã dịch: {registry['summary']['translated']} | Không có chữ: {registry['summary']['no_text']} | Còn lại: {registry['summary']['pending']}")
    print(f"  Tiến độ đã được lưu vào: {REGISTRY_FILE}")
    print("==========================================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI OCR Image Translator for ZMRobo")
    parser.add_argument("--limit", type=int, default=None, help="Số lượng ảnh tối đa cần xử lý trong đợt này")
    parser.add_argument("--init-only", action="store_true", help="Chỉ khởi tạo danh sách mà không chạy dịch")
    args = parser.parse_args()

    if args.init_only:
        reg = load_registry()
        scan_all_images(reg)
    else:
        run_pipeline(limit=args.limit)
