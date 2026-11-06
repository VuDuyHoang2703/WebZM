"""
Full System High-Quality Vietnamese Translator
- Khôi phục từ dữ liệu gốc sạch (data_raw/)
- Dịch đúng ngữ cảnh STEM / Robotics, chuẩn ngữ pháp tiếng Việt (Danh từ trước, tính từ sau)
- Giữ nguyên 100% tên tất cả các bộ Kit tiếng Anh
- Khắc phục triệt để lỗi "điện tửPhụ kiện", "Tòa nhà Số chi tiết", "Xe bội thu", v.v.
"""

import os
import sys
import json
import csv
import re
import time
import ssl
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data_raw")
DATA_DIR = os.path.join(BASE_DIR, "data")
CACHE_FILE = os.path.join(DATA_DIR, "translation_cache.json")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(RAW_DIR, exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
}

# 1. Danh sách tên các bộ Kit bắt buộc giữ nguyên tiếng Anh
KIT_NAMES = {
    355: "Gamma Series",
    353: "2026 Super AI SmartCraft Challenge",
    352: "2026 Super AI - Star Cruise",
    351: "2026 Super AI - Star Journey",
    349: "Innovation Storm",
    130: "WiseBot",
    89: "Beta Set",
    128: "Alpha Set D",
    86: "Alpha Set C",
    69: "WiseChild 2",
    68: "Defender WiseKit",
    90: "Mini Creation",
    67: "Intelligence Storm",
    92: "AI Storm",
    60: "Engineering Set",
    83: "Alpha Set B",
    79: "Robot Sensor",
    76: "2022 SUPER AI Super Track Competition",
    62: "Creative Expansion",
    80: "Alpha Set A",
    55: "RoboMaker",
    54: "RoboRun",
    78: "2022 NOC Competition Intelligent Catering Robot",
    77: "2022 RIC Robotics Innocation Challenge Competition",
    35: "Technology Storm Kit2",
    309: "Super AI - Mars Exploration",
    95: "2025 Super AI - Interstellar Legend",
    91: "2024 Super AI - Interstellar Crossing",
    302: "Early Soccer Robotics Kit",
    129: "AI Storm - Rubik's Cube Solving Robot Set",
    85: "Alpha X",
    120: "WiseBot"
}

# 2. Danh mục chính
PARENT_TRANS = {
    "Education": "Giáo dục",
    "Competition": "Thi đấu",
    "Electronic": "Linh kiện điện tử",
    "Plastic": "Linh kiện cơ khí nhựa"
}

# 3. Danh mục con
SUB_TRANS = {
    "kit": "Bộ Kit",
    "motor and driver": "Động cơ & Mạch điều khiển",
    "other": "Khác",
    "Others": "Khác",
    "RCU": "Bộ điều khiển trung tâm (RCU)",
    "Handle": "Tay cầm điều khiển",
    "Actuator": "Động cơ & Cơ cấu chấp hành",
    "Sensor": "Cảm biến",
    "Cable": "Dây cáp kết nối",
    "Wheel": "Bánh xe & Bánh đa hướng",
    "Beam": "Thanh dầm (Beam)",
    "Angular Beam": "Thanh dầm chữ L (Angular Beam)",
    "Peg": "Chốt cắm (Peg)",
    "Axle": "Trục quay (Axle)",
    "Gear": "Bánh răng & Băng xích (Gear)",
    "Frame": "Khung dầm chữ nhật (Frame)",
    "Plate": "Tấm ghép (Plate)",
    "Angular Block": "Khối góc (Angular Block)",
    "Cross Block": "Khối chữ thập (Cross Block)"
}

def clean_text(t):
    if not t: return ""
    t = t.replace('\xa0', ' ').replace('\u3000', ' ').replace('\u202f', ' ').replace('\u2013', '–')
    t = re.sub(r'\s+', ' ', t).strip()
    return t

# 4. Dịch chuẩn tên sản phẩm linh kiện & phụ kiện (Danh từ trước, tính từ sau)
def translate_product_title(orig_title, pid):
    if pid in KIT_NAMES:
        return KIT_NAMES[pid]

    t = clean_text(orig_title)
    
    # Chuẩn hóa đơn vị
    t = re.sub(r'(\d+)\s*PCS', r'\1 chi tiết', t, flags=re.IGNORECASE)
    t = re.sub(r'(\d+)\s*Pack', r'Gói \1 chi tiết', t, flags=re.IGNORECASE)

    patterns = [
        # Cameras & Vision
        (r'^FPV Camera$', 'Camera FPV'),
        (r'^USB Camera$', 'Camera USB'),
        (r'^Scaning Camera$', 'Camera quét mã (Scanning Camera)'),
        (r'^Scanning Camera$', 'Camera quét mã (Scanning Camera)'),
        (r'^WiFi Camera$', 'Camera Wi-Fi'),
        (r'^AI Vision Module \(Artificial Intelligence Version\)$', 'Mô-đun thị giác AI (Bản trí tuệ nhân tạo)'),
        (r'^AI Vision Module$', 'Mô-đun thị giác AI'),
        (r'^Intelligent Eye$', 'Mắt thần thông minh (Intelligent Eye)'),

        # Cables
        (r'6P to 4-Pin Female Dupont Adapter Cable Pack [–-] (\d+) chi tiết [–-] For Serial Port [–-] (\d+)cm', r'Bộ cáp chuyển đổi 6P sang Dupont 4-Pin cái cho cổng Serial \2cm (Gói \1 sợi)'),
        (r'Black Flexible Ribbon Cable Pack D [–-] (\d+) chi tiết [–-] RJ11 to TX1\.25 [–-] (\d+)cm', r'Bộ cáp dẹt mềm đen D RJ11 sang TX1.25 \2cm (Gói \1 sợi)'),
        (r'Black Flexible Ribbon Cable Pack A [–-] (\d+) chi tiết [–-] RJ11 to TX1\.25 [–-] (\d+)cm', r'Bộ cáp dẹt mềm đen A RJ11 sang TX1.25 \2cm (Gói \1 sợi)'),
        (r'Black Flexible Ribbon Cable Pack B [–-] (\d+) chi tiết [–-] RJ11 to RJ11 [–-] (\d+)cm', r'Bộ cáp dẹt mềm đen B RJ11 sang RJ11 \2cm (Gói \1 sợi)'),
        (r'6P to 2-Pin Female Dupont Adapter Cable Pack [–-] (\d+) chi tiết [–-] For Motor [–-] (\d+)cm', r'Bộ cáp chuyển đổi 6P sang Dupont 2-Pin cái cho động cơ \2cm (Gói \1 sợi)'),
        (r'6P to 3-Pin Female Dupont Adapter Cable Pack [–-] (\d+) chi tiết [–-] For TX1\.25 6P Servo [–-] (\d+)cm', r'Bộ cáp chuyển đổi 6P sang Dupont 3-Pin cái cho Servo TX1.25 \2cm (Gói \1 sợi)'),
        (r'6P to 3-Pin Male Dupont Adapter Cable Pack [–-] (\d+) chi tiết [–-] For 3-Wire Servo [–-] (\d+)cm', r'Bộ cáp chuyển đổi 6P sang Dupont 3-Pin đực cho Servo 3 dây \2cm (Gói \1 sợi)'),
        (r'Connection Cable Pack [–-] (\d+) chi tiết [–-] (\d+)cm', r'Bộ dây cáp kết nối \2cm (Gói \1 sợi)'),
        (r'Connection Cables \(Various Lengths\)', r'Bộ dây cáp kết nối (Nhiều độ dài khác nhau)'),
        (r'RJ11 to 3-Pin Dupont Adapter Cable', r'Cáp chuyển đổi RJ11 sang Dupont 3-Pin'),
        (r'Connection Example', r'Mẫu sơ đồ đấu nối dây'),

        # Sensors
        (r'^Ultrasonic Sensor$', 'Cảm biến siêu âm'),
        (r'^UItrasonic sensor$', 'Cảm biến siêu âm'),
        (r'^Color Sensor \(Building Block Version\)$', 'Cảm biến màu sắc (Bản lắp ghép)'),
        (r'^Color Sensor$', 'Cảm biến màu sắc'),
        (r'^Color sensor$', 'Cảm biến màu sắc'),
        (r'^Color Lamp$', 'Đèn LED đa màu'),
        (r'^Photosensitive Sensor$', 'Cảm biến ánh sáng (quang trở)'),
        (r'^Light Sensor \(Competition Version\)$', 'Cảm biến ánh sáng (Bản thi đấu)'),
        (r'^Photoelectric Sensor$', 'Cảm biến quang điện'),
        (r'^Mini Photoelectric Sensor$', 'Cảm biến quang điện mini'),
        (r'^Sound Detection Sensor$', 'Cảm biến âm thanh'),
        (r'^MIC Sensor$', 'Cảm biến âm thanh (Micro)'),
        (r'^Tracking Module$', 'Mô-đun cảm biến dò đường (Line Tracking)'),
        (r'^Intelligent tracking module$', 'Mô-đun cảm biến dò đường thông minh'),
        (r'^Infrared ranging sensor$', 'Cảm biến đo khoảng cách hồng ngoại'),
        (r'^Infrared Ranging Sensor$', 'Cảm biến đo khoảng cách hồng ngoại'),
        (r'^IR Range Finder$', 'Cảm biến đo khoảng cách hồng ngoại (IR Range Finder)'),
        (r'^IR Receiver$', 'Đầu thu hồng ngoại (IR Receiver)'),
        (r'^Infrared Compound Eye Module$', 'Mô-đun mắt kép hồng ngoại (Compound Eye)'),
        (r'^Gesture sensor$', 'Cảm biến nhận diện cử chỉ'),
        (r'^Laser ranging sensor$', 'Cảm biến đo khoảng cách Laser'),
        (r'^Temperature and Humidity Sensor$', 'Cảm biến nhiệt độ và độ ẩm'),
        (r'^Barometric Sensor$', 'Cảm biến áp suất khí quyển'),
        (r'^Magnetic Sensor$', 'Cảm biến từ tính'),
        (r'^Flame Sensor$', 'Cảm biến phát hiện lửa (Flame Sensor)'),
        (r'^Tilt Sensor$', 'Cảm biến độ nghiêng'),
        (r'^Button Sensor$', 'Cảm biến nút bấm'),
        (r'^Potentiometer Sensor$', 'Cảm biến chiết áp biến trở'),
        (r'^Touch sensor$', 'Cảm biến chạm'),
        (r'^Attitude Sensor V1\.1$', 'Cảm biến góc nghiêng & con quay hồi chuyển Gyro V1.1 (Attitude Sensor)'),
        (r'^Air Pump Module$', 'Mô-đun máy bơm khí nén'),
        (r'^Fan Module$', 'Mô-đun quạt gió mini'),
        (r'^Voice Recording Module$', 'Mô-đun ghi âm giọng nói'),
        (r'^IoT Module$', 'Mô-đun truyền thông IoT'),
        (r'^16x16blue dot matrix$', 'Màn hình LED ma trận 16×16 (Xanh dương)'),
        (r'^Blueteeth Adapter$', 'Bộ thu phát Bluetooth (Bluetooth Adapter)'),
        (r'^2\.4G Wireless Transceiver \(Building Block Version\)$', 'Bộ thu phát sóng không dây 2.4G (Bản lắp ghép)'),
        (r'^IC Card Reader$', 'Đầu đọc thẻ IC'),
        (r'^OID Module$', 'Mô-đun nhận dạng quang học OID'),
        (r'^RFID LED Module \(Discontinue\)$', 'Mô-đun RFID LED (Ngừng sản xuất)'),
        (r'^LED Module$', 'Mô-đun đèn LED'),

        # Actuators & Motors
        (r'^Large Angle Servo Motor$', 'Động cơ Servo góc quay lớn'),
        (r'^Mini Servo Motor$', 'Động cơ Mini Servo'),
        (r'^Mini Servo motor$', 'Động cơ Mini Servo'),
        (r'^Servo Motor \(VS-1\)$', 'Động cơ Servo (VS-1)'),
        (r'^Digital Servo Motor \(Competition Version\)$', 'Động cơ Servo kỹ thuật số (Bản thi đấu)'),
        (r'^Mini Digital Servo$', 'Động cơ Servo kỹ thuật số mini'),
        (r'^Large Geared Motor 7\.4V \(with Encoder\)$', 'Động cơ giảm tốc lớn 7.4V (có Encoder)'),
        (r'^Medium Geared Motor 3\.7V\(with Encoder\)$', 'Động cơ giảm tốc trung 3.7V (có Encoder)'),
        (r'^Mediumm Geared Motor 7\.4V\(with Encoder\)$', 'Động cơ giảm tốc trung 7.4V (có Encoder)'),
        (r'^Geared Motor\(Competition Version\)$', 'Động cơ giảm tốc (Bản thi đấu)'),
        (r'^Low-Speed Motor \(Turntable Version\)$', 'Động cơ tốc độ thấp (Bản mâm xoay)'),
        (r'^High-Speed Motor \(Turntable Version\)$', 'Động cơ tốc độ cao (Bản mâm xoay)'),
        (r'^Low-Speed Motor$', 'Động cơ tốc độ thấp'),
        (r'^High-Speed Motor$', 'Động cơ tốc độ cao'),
        (r'^Medium Motor$', 'Động cơ cỡ vừa'),
        (r'^Large Motor$', 'Động cơ cỡ lớn'),
        (r'^Two port motor power module$', 'Mô-đun cấp nguồn động cơ 2 cổng'),
        (r'^Sensor & Motor Serial Extension Module$', 'Mô-đun mở rộng nối tiếp cảm biến & động cơ'),
        (r'^Joinmax Motor (\d+)$', r'Động cơ Joinmax \1'),
        (r'^Motor Driver JMP-BE-(\d+)$', r'Mạch điều khiển động cơ JMP-BE-\1'),
        (r'^Motor Driver (\d+) \(5channal 5motor\)$', r'Mạch điều khiển động cơ \1 (5 kênh 5 động cơ)'),
        (r'^Motor Driver (\d+) \(4channal 4motor\)$', r'Mạch điều khiển động cơ \1 (4 kênh 4 động cơ)'),
        (r'^Motor Driver (\d+) \(4C4M\)$', r'Mạch điều khiển động cơ \1 (4 kênh 4 động cơ)'),
        (r'^Motor (\d+)$', r'Động cơ \1'),

        # RCU Controllers
        (r'^Smart Motor Hub$', 'Bộ điều khiển động cơ thông minh (Motor Hub)'),
        (r'^Smart Pen$', 'Bút lập trình thông minh (Smart Pen)'),
        (r'^AI Storm Controller$', 'Bộ điều khiển trung tâm AI Storm'),
        (r'^E6 Battery Charging Base$', 'Đế sạc pin Lithium E6'),
        (r'^Lithium battery$', 'Pin sạc Lithium'),
        (r'^X4-RCU$', 'Bộ điều khiển X4-RCU'),
        (r'^M6- RCU$', 'Bộ điều khiển M6-RCU'),
        (r'^M5-RCU$', 'Bộ điều khiển M5-RCU'),
        (r'^C6-RCU$', 'Bộ điều khiển C6-RCU'),
        (r'^E6-RCU$', 'Bộ điều khiển E6-RCU'),

        # Handles
        (r'^2\.4G Remote Control Handle \(Basic Version\)$', 'Tay cầm điều khiển từ xa 2.4G (Bản tiêu chuẩn)'),
        (r'^2\.\s*4G Remote Control Handle Professional Ver\.$', 'Tay cầm điều khiển từ xa 2.4G (Bản chuyên nghiệp)'),
        (r'^Bluetooth remote control handle$', 'Tay cầm điều khiển từ xa Bluetooth'),

        # Beams
        (r'Beam (\d+)M with Staggered Holes', r'Thanh dầm \1 lỗ so le'),
        (r'L-shaped Interlocking Beam', r'Thanh dầm khóa chữ L'),
        (r'Cross-hole Beam (\d+)M', r'Thanh dầm lỗ chữ thập \1 lỗ'),
        (r'Cross-hole Rubber Beam', r'Thanh dầm cao su lỗ chữ thập'),
        (r'H-shaped Interlocking Beam', r'Thanh dầm khóa chữ H'),
        (r'T-shaped Angular Beam (\d+x\d+)M', r'Thanh dầm góc chữ T \1 lỗ'),
        (r'Double Angle Beam (\d+x\d+)M', r'Thanh dầm góc đôi \1 lỗ'),
        (r'Angular Beam \(Off-white\) (\d+x\d+)M', r'Thanh dầm góc (Trắng ngà) \1 lỗ'),
        (r'Angular Beam \(Grey\) (\d+x\d+)M', r'Thanh dầm góc (Xám) \1 lỗ'),
        (r'Angular Beam (\d+x\d+)M', r'Thanh dầm chữ L \1 lỗ'),
        (r'Angular Beam', r'Thanh dầm chữ L'),
        (r'Beam (\d+(?:\.\d+)?)M', r'Thanh dầm \1 lỗ'),
        (r'Frame Beam (\d+[×x]\d+)M', r'Khung dầm chữ nhật \1 lỗ'),
        (r'Large Frame Beam (\d+[×x]\d+)M', r'Khung dầm chữ nhật lớn \1 lỗ'),

        # Wheels
        (r'(\d+mm\s*[x×]\s*\d+mm)\s*Competition Wheel Pack', r'Bộ bánh xe thi đấu \1'),
        (r'(\d+mm\s*[x×]\s*\d+mm)\s*Wheel Pack,\s*Black', r'Bộ bánh xe đen \1'),
        (r'(\d+mm\s*[x×]\s*\d+mm)\s*Wheel Pack,\s*Blue', r'Bộ bánh xe xanh dương \1'),
        (r'(\d+mm\s*[x×]\s*\d+mm)\s*Wheel Pack', r'Bộ bánh xe \1'),
        (r'(\d+x\d+mm)\s*Wheel Pact', r'Bộ bánh xe \1'),
        (r'Guide Wheel Pack', r'Bộ bánh dẫn hướng'),
        (r'(\d+mm)\s*Omni Wheel Pack\s*\((\d+)\s*(?:PCS|chi tiết)\)', r'Bộ bánh xe đa hướng Omni \1 (Gói \2 bánh)'),
        (r'(\d+mm\s*[×x]\s*\d+mm)\s*Omni Wheel Pack \(2 Hex Holes\)', r'Bộ bánh xe đa hướng Omni \1 (2 lỗ lục giác)'),
        (r'Universal Wheel Pack \(42mm Plastic Ball\)', r'Bộ bánh xe mắt trâu đa hướng (Bi nhựa 42mm)'),
        (r'Mecanum Wheel \((L|R) Type\) - (\d+mm)', r'Bánh xe Mecanum \2 (Loại \1)'),
        (r'Omni-directional Wheel Hub', r'Trục bánh xe đa hướng Omni'),
        (r'Omni-directional Wheel Roller', r'Con lăn bánh xe đa hướng Omni'),
        (r'Omnidirectional Wheel Assembly', r'Cụm bánh xe đa hướng Omni'),
        (r'Competition Wheel Hub \(Black\)', r'Trục bánh xe thi đấu (Đen)'),
        (r'Tire (\d+) \([ØO\?]?(\d+)mm\)', r'Lốp xe \1 (Ø\2mm)'),
        (r'Tyre (\d+) \([ØO\?]?(\d+)mm\)', r'Lốp xe \1 (Ø\2mm)'),
        (r'Super Soft Tire for Competition', r'Bộ lốp siêu mềm thi đấu'),
        (r'Wheel (\d+[×x]\d+)', r'Bánh xe \1'),
        (r'Rim (\d+[×x]\d+)', r'Vành bánh xe \1'),
        (r'Tire Skin (\d+[×x]\d+)', r'Vỏ lốp xe \1'),
        (r'Wheel Hub', r'Trục bánh xe'),
        (r'Steel Ball Small Wheel Assembly', r'Cụm bánh xe mắt trâu kim loại nhỏ'),
        (r'Steel Ball Small Wheel', r'Bánh xe mắt trâu kim loại nhỏ'),
        (r'30 Pulley Combination Pack', r'Bộ cụm ròng rọc 30 bánh đai'),

        # Gears & Tracks
        (r'Crown Gear (\d+)T', r'Bánh răng vương miện \1 răng'),
        (r'Double Bevel Gear (\d+)T', r'Bánh răng côn đôi \1 răng'),
        (r'Bevel Gear (\d+)T', r'Bánh răng côn \1 răng'),
        (r'Gear (\d+)T', r'Bánh răng thẳng \1 răng'),
        (r'Cross Gear', r'Bánh răng chữ thập'),
        (r'Large Gear', r'Bánh răng lớn'),
        (r'Gearbox', r'Hộp số'),
        (r'Differential Gear', r'Bộ vi sai bánh răng'),
        (r'Differential Assembly', r'Cụm bộ vi sai'),
        (r'Turntable Assembly', r'Cụm mâm xoay'),
        (r'Large Turntable Top', r'Mặt trên mâm xoay lớn'),
        (r'Large Turntable Base', r'Đế mâm xoay lớn'),
        (r'Turntable Base', r'Đế mâm xoay'),
        (r'Turntable Top', r'Mặt trên mâm xoay'),
        (r'Track Pieces', r'Mắt xích xe tăng'),
        (r'Track Hub', r'Bánh dẫn hướng xích'),
        (r'Rack Gear', r'Thanh răng (Rack Gear)'),
        (r'Worm Building Block', r'Trục vít bánh vít (Worm Gear)'),
        (r'Cam Connector', r'Khớp nối lệch tâm Cam'),

        # Pegs, Axles, Blocks, Plates
        (r'Square Peg \(E6-RCU Version\)', r'Chốt cắm vuông (Bản E6-RCU)'),
        (r'Cross Peg \(E6-RCU Version\)', r'Chốt cắm chữ thập (Bản E6-RCU)'),
        (r'Straight Peg 3M \(E6-RCU Version\)', r'Chốt cắm thẳng 3 lỗ (Bản E6-RCU)'),
        (r'Single Peg 2M \(E6-RCU Version\)', r'Chốt cắm đơn 2 lỗ (Bản E6-RCU)'),
        (r'Square Peg', r'Chốt cắm vuông'),
        (r'Cross Peg', r'Chốt cắm chữ thập'),
        (r'Straight Peg 3M', r'Chốt cắm thẳng 3 lỗ'),
        (r'Single Peg 2M', r'Chốt cắm đơn 2 lỗ'),
        (r'Connector Peg with Friction and Axle', r'Chốt cắm nối có ma sát kèm trục'),
        (r'Connector Peg with Axle', r'Chốt cắm nối kèm trục'),
        (r'Friction Axle Peg with Extension', r'Chốt cắm ma sát có phần nối dài'),
        (r'Friction Axle Peg with Stop', r'Chốt cắm ma sát có cữ chặn'),
        (r'Friction Axle Peg', r'Chốt cắm ma sát'),
        (r'Connector Peg (\d+)M', r'Chốt cắm nối \1 lỗ'),
        (r'Connector Peg with Bushing', r'Chốt cắm nối kèm vòng đệm'),
        (r'Connector Peg', r'Chốt cắm nối'),
        (r'Bushing (\d+(?:\.\d+)?)M', r'Vòng đệm bạc lót \1 lỗ'),
        (r'Axle Connector Pack', r'Gói khớp nối trục quay'),
        (r'Axle Connector', r'Khớp nối trục quay'),
        (r'Mixed-Length Axle', r'Bộ trục quay nhiều độ dài'),
        (r'(\d+mm)\s*Axle with Stop', r'Trục quay \1 có cữ chặn'),
        (r'(\d+mm)\s*Axle', r'Trục quay \1'),
        (r'Axle (\d+)M with Stop', r'Trục quay \1 lỗ có cữ chặn'),
        (r'Axle (\d+(?:\.\d+)?)M', r'Trục quay \1 lỗ'),
        (r'Angular Block (\d+)[°\?]? with Cross Hole', r'Khối góc \1° có lỗ chữ thập'),
        (r'Angular Block (\d+)[°\?]?', r'Khối góc \1°'),
        (r'Cross Block (\d+)M', r'Khối chữ thập \1 lỗ'),
        (r'Cross Block', r'Khối chữ thập'),
        (r'Universal Joint', r'Khớp nối vạn năng (Universal Joint)'),
        (r'Triangular Plate', r'Tấm ghép hình tam giác'),
        (r'Plate Component', r'Chi tiết tấm ghép'),
        (r'(\d+x\d+mm)\s*Plate', r'Tấm ghép \1'),
        (r'Plate (\d+[×x]\d+)M', r'Tấm ghép \1 lỗ'),
        (r'Plate (\d+)M', r'Tấm ghép \1 lỗ'),
        (r'Appearance Parts (\d+[×x]\d+)M', r'Chi tiết vỏ trang trí \1 lỗ'),
        (r'Locking Parts', r'Phụ kiện khóa chốt'),
        (r'Pointer', r'Kim chỉ góc / Con trỏ'),
        (r'Rubber Anti-Slip Block', r'Khối cao su chống trượt'),
        (r'Soft Rubber Components', r'Chi tiết cao su mềm'),
        (r'Motor Shaft Components', r'Bộ phụ kiện trục động cơ'),
        (r'10-Shaft Transparent Gearbox \(For WiseChild 2\)', 'Hộp số trong suốt 10 trục (Dành cho WiseChild 2)'),
        (r'Rubber Bands, Red \(For JMC-NY-2107\)', 'Dây chun cao su đỏ đàn hồi (Dành cho JMC-NY-2107)'),
        (r'6mm [×x] 10mm Cylindrical Magnets', 'Nam châm hình trụ 6mm × 10mm'),
        (r'Disassembly Tool', 'Dụng cụ tháo lắp chi tiết')
    ]

    res = t
    for pat, rep in patterns:
        res = re.sub(pat, rep, res, flags=re.IGNORECASE)

    res = re.sub(r'\s+', ' ', res).strip()
    return res

# 5. Xử lý bảo vệ tên Kit trong câu văn
ALL_KIT_LIST = list(set(KIT_NAMES.values()))
ALL_KIT_LIST.sort(key=lambda x: -len(x))

def protect_kits(text):
    protected = {}
    for i, name in enumerate(ALL_KIT_LIST):
        token = f"ZMKIT{i}X"
        if name in text:
            protected[token] = name
            text = text.replace(name, token)
    return text, protected

def restore_kits(text, protected):
    for token, original in protected.items():
        text = text.replace(token, original)
        text = re.sub(rf"ZM\s*KIT\s*{token.replace('ZMKIT', '').replace('X', '')}\s*X", original, text, flags=re.IGNORECASE)
    return text

# 6. Hiệu chỉnh thuật ngữ STEM / Robotics chuẩn tiếng Việt sau khi dịch máy
def post_process_stem(vi):
    rules = [
        # Building blocks
        (r'\bcác khối xây dựng\b', 'các chi tiết lắp ghép'),
        (r'\bkhối xây dựng\b', 'chi tiết lắp ghép'),
        (r'\bKhối xây dựng\b', 'Chi tiết lắp ghép'),
        (r'\bcác khối lắp ráp\b', 'các chi tiết lắp ghép'),
        (r'\bkhối lắp ráp\b', 'chi tiết lắp ghép'),
        (r'\bKhối lắp ráp\b', 'Chi tiết lắp ghép'),
        (r'\bTòa nhà\b', 'Mô hình lắp ghép'),
        (r'\btòa nhà\b', 'mô hình lắp ghép'),
        
        # Bumper car
        (r'\bxe bội thu\b', 'xe điện đụng'),
        (r'\bXe bội thu\b', 'Xe điện đụng'),

        # Flame sensor
        (r'\bcảm biến ngọn lửa\b', 'cảm biến phát hiện lửa'),
        (r'\bCảm biến ngọn lửa\b', 'Cảm biến phát hiện lửa'),

        # Attitude sensor
        (r'\bcảm biến tư thế\b', 'cảm biến góc nghiêng & con quay hồi chuyển'),
        (r'\bCảm biến tư thế\b', 'Cảm biến góc nghiêng & con quay hồi chuyển'),

        # Dot matrix
        (r'\bmàn hình ma trận điểm\b', 'màn hình LED ma trận'),
        (r'\bma trận điểm\b', 'LED ma trận'),
        (r'\bMa trận điểm\b', 'LED ma trận'),

        # Bluetooth
        (r'\bbộ điều hợp Blueteeth\b', 'bộ thu phát Bluetooth'),
        (r'\bBộ điều hợp Blueteeth\b', 'Bộ thu phát Bluetooth'),
        (r'\bBlueteeth\b', 'Bluetooth'),

        # Other STEM terms
        (r'\bmáy bơm không khí\b', 'máy bơm khí nén'),
        (r'\bchó cưng điện tử\b', 'robot chó cưng điện tử'),
        (r'\bChó cưng điện tử\b', 'Robot chó cưng điện tử'),
        (r'\bcánh tay cơ khí\b', 'cánh tay robot'),
        (r'\bvòng đu quay\b', 'vòng đu quay đứng'),
        (r'\bloại loại\b', 'loại'),
        (r'\bMã sản phẩm \(Model\)\b', 'mô hình'),
        (r'\bchương trình đồ họa\b', 'lập trình đồ họa'),
    ]
    for p, r in rules:
        vi = re.sub(p, r, vi, flags=re.IGNORECASE)
    
    # Viết hoa chữ cái đầu câu nếu cần
    if vi and len(vi) > 1 and vi[0].islower() and not vi.startswith('http'):
        vi = vi[0].upper() + vi[1:]
    return vi

# 7. Dịch một lô câu văn qua Google Translate
def translate_batch_google(batch_texts):
    if not batch_texts:
        return []

    prot_all = []
    prot_batch = []
    for t in batch_texts:
        p_t, p_d = protect_kits(t)
        prot_batch.append(p_t)
        prot_all.append(p_d)

    combined = "\n".join(prot_batch)
    url = 'https://translate.googleapis.com/translate_a/single?client=dict-chrome-ex&sl=en&tl=vi&dt=t'
    post_data = urllib.parse.urlencode({'q': combined}).encode('utf-8')
    req = urllib.request.Request(url, data=post_data, headers=HEADERS, method='POST')

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            data = json.loads(r.read().decode('utf-8'))
            raw_full = ''.join([item[0] for item in data[0] if item[0]])
            lines = raw_full.split('\n')
            results = []
            for i, p_dict in enumerate(prot_all):
                line = lines[i].strip() if i < len(lines) else batch_texts[i]
                line = restore_kits(line, p_dict)
                line = post_process_stem(line)
                results.append(line)
            return results
    except Exception as e:
        print(f"  [!] Lỗi dịch lô: {e}")
        return batch_texts

# 8. Xử lý dịch thẻ HTML chuyên nghiệp
def translate_html_content(html, trans_map):
    if not html:
        return ""

    # Chuẩn hóa triệt để lỗi dấu ngoặc kép bên trong style url("...') gây đóng thẻ style sớm và mất background
    html = re.sub(r'url\(["\']?([^"\'\)\s]+)["\']?\)', r"url('\1')", html)

    # Căn giữa toàn bộ hình ảnh và video dạng poster cuộn (Product 60, 69, 79, v.v.)
    html = re.sub(r'<p\s+style=["\']text-align:\s*left;?["\']>', '<p style="text-align: center;">', html, flags=re.IGNORECASE)

    # Căn giữa toàn bộ bảng biểu (table) và sửa lỗi ký tự nhân &times; bị dịch thành &lần;
    html = html.replace('&lần;', '×').replace('&times;', '×')
    html = re.sub(r'CẢNG\s+(\d+)', r'CỔNG \1', html)
    html = html.replace('Cảng xe máy', 'Cổng động cơ')
    html = html.replace('Cảng cho RCU', 'Cổng kết nối RCU')
    html = html.replace('Cảng cho động cơ', 'Cổng kết nối động cơ')
    html = html.replace('người lái xe không nên cung cấp điện áp lớn hơn', 'mạch điều khiển không nên được cấp điện áp lớn hơn')
    html = re.sub(r'<table(?![^>]*align=)', '<table align="center" style="margin: 20px auto;"', html, flags=re.IGNORECASE)

    # A. Xử lý chuẩn xác các cặp tiêu đề Gradient liên tiếp (Đảo đúng ngữ pháp tiếng Việt)
    html = re.sub(
        r'<span class=[\"\x27]gradient_tittle[0-9]*[\"\x27]>\s*Electronic\s*</span>(?:\s*(?:&nbsp;)*\s*)<span class=[\"\x27]gradient_tittle[0-9]*[\"\x27]>\s*Accessories\s*</span>',
        '<span class="gradient_tittle">Linh kiện</span>&nbsp;<span class="gradient_tittle2">điện tử</span>',
        html, flags=re.IGNORECASE
    )
    html = re.sub(
        r'<span class=[\"\x27]gradient_tittle[0-9]*[\"\x27]>\s*Innovation Storm\s*</span>(?:\s*(?:&nbsp;)*\s*)<span class=[\"\x27]gradient_tittle[0-9]*[\"\x27]>\s*Robot Set\s*</span>',
        '<span class="gradient_tittle">Bộ Robot</span>&nbsp;<span class="gradient_tittle2">Innovation Storm</span>',
        html, flags=re.IGNORECASE
    )
    html = re.sub(
        r'<span class=[\"\x27]gradient_tittle[0-9]*[\"\x27]>\s*Multiple\s*</span>(?:\s*(?:&nbsp;)*\s*)<span class=[\"\x27]gradient_tittle[0-9]*[\"\x27]>\s*Programming Modes and Languages\s*</span>',
        '<span class="gradient_tittle">Đa dạng</span>&nbsp;<span class="gradient_tittle2">chế độ và ngôn ngữ lập trình</span>',
        html, flags=re.IGNORECASE
    )
    html = re.sub(
        r'<span class=[\"\x27]gradient_tittle[0-9]*[\"\x27]>\s*80 types of building blocks,?\s*</span>(?:\s*(?:&nbsp;)*\s*)<span class=[\"\x27]gradient_tittle[0-9]*[\"\x27]>\s*428\+\s*accessories\s*</span>',
        '<span class="gradient_tittle">80 loại chi tiết kết cấu,</span>&nbsp;<span class="gradient_tittle2">428+ phụ kiện</span>',
        html, flags=re.IGNORECASE
    )
    html = re.sub(
        r'<span class=[\"\x27]gradient_tittle[0-9]*[\"\x27]>\s*Model\s*</span>(?:\s*(?:&nbsp;)*\s*)<span class=[\"\x27]gradient_tittle[0-9]*[\"\x27]>\s*Showcase\s*</span>',
        '<span class="gradient_tittle">Trưng bày</span>&nbsp;<span class="gradient_tittle2">mô hình</span>',
        html, flags=re.IGNORECASE
    )

    # A1b. Khắc phục lỗi công thức số mũ toán học 10^19 tại Bộ Robot Rubik (PID 129) gây vỡ gradient_tittle
    html = re.sub(
        r'<span class=[\"\x27]gradient_tittle[\"\x27][^>]*>\s*(?:Handles|Xử lý)\s*4[.,]33\s*[×x*]\s*10\s*<div[^>]*>\s*\^?19\s*</div>\s*(?:combinations with precision and ease|Sự kết hợp một cách chính xác và dễ dàng)\.?\s*</span>(?:\s*</span>)?',
        '<span class="gradient_tittle" style="font-size:32px;">Xử lý 4,33 × 10¹⁹ tổ hợp một cách chính xác và dễ dàng.</span>',
        html, flags=re.IGNORECASE
    )

    # A2. Xử lý chuẩn các cụm từ icon AI CAM & Sensor có thẻ <br/> (Ngữ pháp chuẩn, ngắn gọn không vỡ ô)
    # A2a. Xử lý dạng AI CAM icon: >Word</tag><tag>Word< (2 text nodes riêng biệt, không có <br/>)
    # Ghép thành 1 cụm dịch chuẩn trước khi repl() chạy
    _cam_pairs = [
        ('Face', 'Recognition', 'Nhận diện khuôn mặt', 'Nhận diện khuôn mặt'),
        ('Color', 'Detection', 'Nhận diện màu sắc', 'Nhận diện màu sắc'),
        ('Tag', 'Detection', 'Nhận diện thẻ mã', 'Nhận diện thẻ mã'),
        ('Object', 'Detection', 'Phát hiện vật thể', 'Phát hiện vật thể'),
        ('Image', 'Recognition', 'Nhận diện hình ảnh', 'Nhận diện hình ảnh'),
        ('Digit', 'Recognition', 'Nhận diện chữ số', 'Nhận diện chữ số'),
        ('Gesture', 'Recognition', 'Nhận diện cử chỉ', 'Nhận diện cử chỉ'),
        ('Road', 'Detection', 'Nhận diện đường đi', 'Nhận diện đường đi'),
        ('Human', 'Detection', 'Nhận diện người', 'Nhận diện người'),
        ('Object', 'Classification', 'Phân loại đối tượng', 'Phân loại đối tượng'),
    ]
    for w1, w2, combined, _label in _cam_pairs:
        # Match: >Word1</anytag><anytag>Word2< — merge into single node with translated value
        html = re.sub(
            rf'>(\s*){re.escape(w1)}(\s*)<(/?\w+[^>]*)>\s*<(\w+[^>]*)>(\s*){re.escape(w2)}(\s*)<',
            rf'>\1{combined}\2<\3><\4>\5\6<',
            html, flags=re.IGNORECASE
        )
        # Also match where they're in the SAME tag with <br/> — dùng __BR__ để không bị C0 xóa
        combined_br = combined.replace('<br/>', '__BR__')
        html = re.sub(rf'{re.escape(w1)}<br\s*/?>{re.escape(w2)}', combined_br, html, flags=re.IGNORECASE)

    # A2b. Xử lý các cụm có thẻ <br/> ở giữa TRƯỚC KHI repl() chạy (vì repl() tách theo thẻ <br/> sẽ làm đảo ngữ pháp từng nửa)
    br_subs = [
        (r'2\.4(?:&quot;|")\s*Capacitive<br\s*/?>Touchscreen', 'Màn hình cảm ứng<br/>điện dung 2.4"'),
        (r'3\.2(?:&quot;|")\s*Capacitive<br\s*/?>Touchscreen', 'Màn hình cảm ứng<br/>điện dung 3.2"'),
        (r'Cortex-M7<br\s*/?>Processor', 'Bộ xử lý<br/>Cortex-M7'),
        (r'2600mAh<br\s*/?>Lithium Battery', 'Pin Lithium<br/>2600mAh'),
        (r'● After-School Training Institutions, Youth<br\s*/?>Activity Centers, Programming Workshops', '● Các trung tâm đào tạo ngoại khóa, nhà thiếu nhi, câu lạc bộ lập trình'),
        (r'Students can consider different\s+task\s*<br\s*/?>categories,\s*relevant task settings,\s*and\s*<br\s*/?>various route planning solutions\.', 'Học sinh có thể xem xét các hạng mục nhiệm vụ khác nhau, các thiết lập nhiệm vụ liên quan và các giải pháp lập kế hoạch lộ trình đa dạng.'),
        (r'It supports drag-and-drop graphical programming and seamless transition to Python and C, empowering both creativity<br\s*/?>and professional development\.', 'Hỗ trợ lập trình đồ họa kéo thả và chuyển đổi liền mạch sang Python và C, phát huy tối đa khả năng sáng tạo<br/>lẫn phát triển chuyên sâu.'),
        (r'The building blocks feature high-quality materials and rigorous quality control, with an exquisite appearance, precise structure, and<br\s*/?>a comfortable feel\.', 'Các chi tiết lắp ghép được làm từ vật liệu chất lượng cao và kiểm soát chất lượng nghiêm ngặt, mang lại vẻ ngoài tinh tế, kết cấu chính xác cùng<br/>cảm giác cầm nắm thoải mái.'),
        (r'<div>\s*The\s*<span([^>]*)>\s*E7-RCU\s*</span>\s*features a high-capacity battery and multiple expansion ports, supporting a wide range of electronic parts with versatile building components\.\s*</div>', r'<div>Bộ điều khiển <span\1>E7-RCU</span> sở hữu pin dung lượng cao và nhiều cổng mở rộng, hỗ trợ đa dạng linh kiện điện tử cùng các chi tiết lắp ghép linh hoạt.</div>'),
        (r'<div class="icon_2_font1">\s*Model\s*</div>', '<div class="icon_2_font1">Mã sản phẩm</div>'),
        # Lesson titles with <br/>
        (r'Animated Emoticon<br\s*/?>Robot', 'Robot biểu cảm<br/>hoạt hình'),
        (r'Bicycle Riding Robot<br\s*/?>Musician', 'Robot nhạc công<br/>đi xe đạp'),
        (r'Bicycling<br\s*/?>Little Dinosaur', 'Khủng long nhỏ<br/>đi xe đạp'),
        (r'Catapult Car<br\s*/?>Pullback Car', 'Xe bắn đá &<br/>Xe dây cót'),
        (r'Pirate Ship<br\s*/?>Music Box', 'Tàu cướp biển &<br/>Hộp âm nhạc'),
        (r'Obstacle Avoidance<br\s*/?>Robot 1', 'Robot tránh<br/>vật cản 1'),
        (r'Obstacle Avoidance<br\s*/?>Robot 2', 'Robot tránh<br/>vật cản 2'),
        (r'Obstacle Avoidance<br\s*/?>in Snow', 'Robot vượt tuyết<br/>tránh vật cản'),
        (r'Super Trajectory<br\s*/?>Robot 1', 'Robot siêu quỹ đạo 1'),
        (r'Super Trajectory<br\s*/?>Robot 2', 'Robot siêu quỹ đạo 2'),
        (r'Super Trajectory<br\s*/?>Robot 3', 'Robot siêu quỹ đạo 3'),
        (r'Super Trajectory<br\s*/?>Robot 4', 'Robot siêu quỹ đạo 4'),
        (r'Cement Mixer<br\s*/?>Truck', 'Xe trộn bê tông'),
        (r'Basketball Shooting<br\s*/?>Machine', 'Máy ném bóng rổ'),
        (r'Treadle Sewing<br\s*/?>Machine', 'Máy may đạp chân'),
        (r'Architectural<br\s*/?>design', 'Thiết kế kiến trúc'),
        (r'Hazard Avoidance<br\s*/?>Robot', 'Robot tránh hiểm họa'),
        (r'Electric Fan<br\s*/?>Rowing', 'Quạt điện & Thuyền chèo'),
        (r'Little Dancer<br\s*/?>Carousel', 'Vũ công nhí & Vòng quay ngựa gỗ'),
        (r'Little Turtle<br\s*/?>Dancing Robot', 'Rùa con & Robot khiêu vũ'),
        (r'High-speed Chainsaw<br\s*/?>Automatic Clothes Hanger<br\s*/?>Blender<br\s*/?>Sliding Door', 'Máy cưa xích tốc độ cao<br/>Giàn phơi tự động<br/>Máy xay sinh tố<br/>Cửa trượt'),
        (r'Penalty Shootout<br\s*/?>Dog-ThemedClock<br\s*/?>Pas DE Deux<br\s*/?>Simple Password', 'Sút luân lưu<br/>Đồng hồ chú chó<br/>Vũ điệu đôi (Pas De Deux)<br/>Mật khẩu đơn giản'),
        (r'High-speed Racer<br\s*/?>Obstacle Avoidance Car<br\s*/?>Little Turtle<br\s*/?>Dancing Robot', 'Xe đua tốc độ cao<br/>Xe tránh vật cản<br/>Rùa nhỏ<br/>Robot khiêu vũ'),
        (r'Burst Drummer<br\s*/?>Pull-up<br\s*/?>Bicycle Riding Robot<br\s*/?>Musician', 'Tay trống sôi động<br/>Robot kéo xà<br/>Robot đi xe đạp<br/>Nhạc công'),
        (r'Gymnast<br\s*/?>Cheerleaders<br\s*/?>Swimmer<br\s*/?>Pastry Maker', 'Vận động viên thể dục<br/>Đội cổ vũ<br/>Vận động viên bơi<br/>Thợ làm bánh'),
        (r'Inchworm<br\s*/?>Magic Dragon<br\s*/?>Running Bull<br\s*/?>Hopping Rabbit', 'Sâu đo<br/>Rồng thần kỳ<br/>Bò tót chạy<br/>Thỏ nhảy'),
        (r'Motorcycle<br\s*/?>Racing Car<br\s*/?>Helicopter<br\s*/?>Rickshaw', 'Xe mô tô<br/>Xe đua<br/>Trực thăng<br/>Xe xích lô'),
        (r'Rocket Car<br\s*/?>Rotating Airplane<br\s*/?>Wire Control Car<br\s*/?>Catapult Pistol', 'Xe tên lửa<br/>Máy bay quay<br/>Xe điều khiển dây<br/>Súng bắn đá'),
        (r'Telescopic Clip<br\s*/?>Gyro Launcher<br\s*/?>Catapult Car<br\s*/?>Pullback Car', 'Kẹp gắp co giãn<br/>Bệ phóng con quay<br/>Xe bắn đá<br/>Xe dây cót'),
        (r'Little Dancer<br\s*/?>Carousel<br\s*/?>Electric Fan<br\s*/?>Rowing', 'Vũ công nhỏ<br/>Vòng quay ngựa gỗ<br/>Quạt điện<br/>Thuyền chèo'),
        (r'Crab<br\s*/?>Hummingbird<br\s*/?>Bigfoot<br\s*/?>Hard Working Miner', 'Con cua<br/>Chim ruồi<br/>Người tuyết Bigfoot<br/>Thợ mỏ chăm chỉ'),
        (r'Pirate Ship<br\s*/?>Music Box<br\s*/?>Bicycling<br\s*/?>Little Dinosaur', 'Tàu cướp biển<br/>Hộp âm nhạc<br/>Đạp xe<br/>Khủng long nhỏ'),
        (r'Ball Holding Robot<br\s*/?>Bell-Striking Robot<br\s*/?>Jump Rope Robot<br\s*/?>Knight Duel', 'Robot giữ bóng<br/>Robot gõ chuông<br/>Robot nhảy dây<br/>Hiệp sĩ đấu kiếm'),
        (r'Gorilla<br\s*/?>Little Saving Assistant<br\s*/?>Cuckoo Clock', 'Khỉ đột<br/>Trợ lý tiết kiệm nhỏ<br/>Đồng hồ chim cúc cu'),
        (r'Lower grades of primary school \(grades 1-3\)\s*<br\s*/?>\s*Upper grades of primary school \(grades 4-6\)\s*<br\s*/?>\s*Junior high school\s*<br\s*/?>\s*High school', 'Tiểu học (Lớp 1–3)<br/>Tiểu học (Lớp 4–6)<br/>Trung học cơ sở<br/>Trung học phổ thông'),
        (r'Junior high school<br\s*/?>\s*High school', 'Trung học cơ sở<br/>Trung học phổ thông'),
        (r'Lesson<br\s*/?>NO\.', 'Số<br/>bài học'),
        (r'Stage 1<br\s*/?>Force and<br\s*/?>Machinery', 'Giai đoạn 1<br/>Lực và Cơ khí'),
        (r'Stage 2<br\s*/?>Engineering<br\s*/?>Challenges', 'Giai đoạn 2<br/>Thử thách Kỹ thuật'),
        (r'Stage 3<br\s*/?>Smart Life', 'Giai đoạn 3<br/>Cuộc sống Thông minh'),
        (r'Temperature And<br\s*/?>Humidity Sensor', 'Cảm biến nhiệt độ<br/>& độ ẩm'),
        (r'Bluetooth Remote<br\s*/?>Control Handle', 'Tay cầm điều khiển<br/>Bluetooth'),
        (r'2\.4G Wireless Communication<br\s*/?>Module', 'Mô-đun giao tiếp<br/>không dây 2.4G'),
        (r'Hydraulic<br\s*/?>Machine', 'Máy thủy lực'),
        (r'Sorting<br\s*/?>Machine', 'Máy phân loại'),
        (r'Mechanical<br\s*/?>Claw', 'Tay kẹp cơ khí'),
        (r'Voice Control<br\s*/?>Vehicle', 'Xe điều khiển<br/>giọng nói'),
        (r'Wired Remote<br\s*/?>Control Vehicle', 'Xe điều khiển<br/>có dây'),
        (r'Sound Level<br\s*/?>Meter', 'Máy đo<br/>cường độ âm'),
        (r'Guess the<br\s*/?>Password', 'Giải mã<br/>mật khẩu'),
        (r'Gravity<br\s*/?>Launch', 'Phóng bằng<br/>trọng lực'),
        (r'Starship<br\s*/?>Docking', 'Ghép nối<br/>tàu vũ trụ'),
        (r'Interstellar<br\s*/?>Vortex', 'Xoáy<br/>liên sao'),
        (r'Star Map<br\s*/?>Decoding', 'Giải mã<br/>bản đồ sao'),
        (r'Energy<br\s*/?>Refill', 'Nạp<br/>năng lượng'),
        (r'Space-time<br\s*/?>Distortion', 'Biến dạng<br/>không - thời gian'),
        (r'Interstellar Scientific<br\s*/?>Research', 'Nghiên cứu khoa học<br/>liên sao'),
        (r'Interactive<br\s*/?>Performance', 'Trình diễn<br/>tương tác'),
        (r'Drama Stage<br\s*/?>Passionate Drummer', 'Sân khấu kịch &<br/>Tay trống sôi động'),
        (r'High-speed Chainsaw<br\s*/?>Automatic Clothes Hanger', 'Máy cưa xích tốc độ cao & Giàn phơi tự động'),
        (r'High-speed Racer<br\s*/?>Obstacle Avoidance Car', 'Xe đua tốc độ cao & Xe tránh vật cản'),
        (r'Rocket Car<br\s*/?>Rotating Airplane', 'Xe tên lửa & Máy bay xoay'),
        (r'Running Bull<br\s*/?>Hopping Rabbit', 'Bò tót chạy & Thỏ nhảy nhót'),
        (r'Sled Dog<br\s*/?>Radar Car', 'Chó kéo xe & Xe radar'),
        (r'Swimmer<br\s*/?>Pastry Maker', 'Vận động viên bơi & Máy làm bánh'),
        (r'Vibrating Sieve<br\s*/?>Machine', 'Máy sàng rung'),
        (r'Wire Control Car<br\s*/?>Catapult Pistol', 'Xe điều khiển dây & Súng bắn đá'),
        (r'Blackout Zone<br\s*/?>Model', 'Mô hình khu vực<br/>mất điện'),
        (r'Wormhole Observation<br\s*/?>Model', 'Mô hình trạm quan sát<br/>lỗ sâu'),
        (r'Space-Time Channel<br\s*/?>Model', 'Mô hình cổng<br/>không - thời gian'),
        (r'Space-Time Energy<br\s*/?>Conversion Model', 'Mô hình chuyển đổi<br/>năng lượng'),
        (r'Delivery Point<br\s*/?>Frame', 'Khung điểm giao hàng'),
    ]
    for p, r in br_subs:
        r_safe = r.replace('<br/>', '__BR__')
        html = re.sub(p, r_safe, html, flags=re.IGNORECASE)

    phrase_subs = [
        (r'Built-in AI algorithms and zero-code AI access make smart creation effortless\.', 'Các thuật toán AI tích hợp sẵn cùng khả năng truy cập AI không cần viết mã giúp việc sáng tạo trở nên dễ dàng.'),
        (r'2\.4&quot; Capacitive<br\s*/?>Touchscreen', 'Màn hình cảm ứng<br/>điện dung 2.4"'),
        (r'3\.2&quot; Capacitive<br\s*/?>Touchscreen', 'Màn hình cảm ứng<br/>điện dung 3.2"'),
        (r'Speech Recognition', 'Nhận dạng giọng nói'),
        (r'Image Learning', 'Học hình ảnh'),
        (r'Vision Recognition', 'Nhận diện thị giác'),
        (r'AI Vision Module V2\.0', 'Mô-đun thị giác AI V2.0'),
        (r'<div>Store</div>', '<div>Kho<br/>ứng dụng</div>'),
        (r'<div>Settings</div>', '<div>Cài đặt</div>'),
        (r'<div>Camera</div>', '<div>Máy ảnh</div>'),
        # Dạng có <br/>
        (r'Face<br\s*/?>Recognition', 'Nhận diện<br/>khuôn mặt'),
        (r'Color<br\s*/?>Detection', 'Nhận diện<br/>màu sắc'),
        (r'Tag<br\s*/?>Detection', 'Nhận diện<br/>thẻ mã'),
        (r'Object<br\s*/?>Detection', 'Phát hiện<br/>vật thể'),
        (r'Image<br\s*/?>Recognition', 'Nhận diện<br/>hình ảnh'),
        (r'Digit<br\s*/?>Recognition', 'Nhận diện<br/>chữ số'),
        (r'Gesture<br\s*/?>Recognition', 'Nhận diện<br/>cử chỉ'),
        (r'Road<br\s*/?>Detection', 'Nhận diện<br/>đường đi'),
        (r'Human<br\s*/?>Detection', 'Nhận diện<br/>người'),
        (r'Object<br\s*/?>Classification', 'Phân loại<br/>đối tượng'),
        (r'Rubik&#39;s Cube Recognition', 'Nhận diện<br/>Rubik'),
        (r'Rubik\'s Cube Recognition', 'Nhận diện<br/>Rubik'),
        (r'Cortex-M7<br\s*/?>Processor', 'Bộ xử lý<br/>Cortex-M7'),
        (r'2600mAh<br\s*/?>Lithium Battery', 'Pin Lithium<br/>2600mAh'),
        
        # Sensor specs & features
        (r'Photoelectric Sensor', 'Cảm biến quang điện'),
        (r'Continuous Signal', 'Tín hiệu liên tục'),
        (r'Fast Response', 'Phản hồi nhanh'),
        (r'Threshold Indicator', 'Chỉ báo ngưỡng'),
        (r'Sunlight Resistant', 'Chống chói sáng'),
        (r'Color Lamp', 'Đèn LED đa màu'),
        (r'Seven-color Display', 'Màn hình hiển thị 7 màu'),
        (r'Diffused Tri-color LED', 'Đèn LED 3 màu khuếch tán'),
        (r'Quick Switching', 'Chuyển đổi trạng thái nhanh'),
        (r'Low Power Consumption', 'Tiết kiệm điện năng'),
        (r'Touch Sensor', 'Cảm biến chạm'),
        (r'Photoelectric Switch', 'Công tắc quang điện'),
        (r'High Sensitivity', 'Độ nhạy cao'),
        (r'Laser Ranging Sensor', 'Cảm biến khoảng cách Laser'),
        (r'Measuring range:?\s*2[\-–]120cm', 'Phạm vi đo: 2–120cm'),
        (r'Accuracy:?\s*±\s*1\s*cm', 'Độ chính xác: ±1 cm'),
        (r'AHRS Sensor', 'Cảm biến góc nghiêng AHRS'),
        (r'Six-axis Attitude Data', 'Dữ liệu góc nghiêng 6 trục'),
        (r'Auto Calibration', 'Tự động hiệu chuẩn'),
        (r'High Responsiveness', 'Độ phản hồi cao'),
        (r'High Precision', 'Độ chính xác cao'),
        (r'Large Geared Motor', 'Động cơ giảm tốc lớn'),
        (r'High Torque', 'Mô-men xoắn cao'),
        (r'Dual-shaft Output', 'Đầu ra trục kép'),
        (r'Quiet &amp; Durable', 'Vận hành êm ái & bền bỉ'),
        (r'Quiet & Durable', 'Vận hành êm ái & bền bỉ'),
        (r'Built-in Encoder Disk', 'Tích hợp đĩa mã hóa Encoder'),
        (r'Digital Servo', 'Servo kỹ thuật số'),
        (r'360° Angle Control', 'Điều khiển góc quay 360°'),
        (r'Wide Voltage Operation', 'Dải điện áp hoạt động rộng'),
        (r'Wear-resistant Gears', 'Bánh răng chống mài mòn'),
        (r'Status Indicator', 'Đèn chỉ báo trạng thái'),
        (r'Long Lifespan', 'Tuổi thọ cao & bền bỉ'),
        (r'I²C Data Transmission', 'Truyền dữ liệu qua cổng I²C'),
        (r'Strong Anti-interference', 'Khả năng chống nhiễu mạnh'),
        (r'Participant Categories', 'Đối tượng tham gia'),
        (r'Getting to Know Python', 'Làm quen với ngôn ngữ Python'),
        (r'Applications of Python', 'Ứng dụng của Python'),
        (r'Curling Game', 'Trò chơi bi sắt đá băng (Curling)'),
        (r'Small Fan', 'Quạt gió mini'),
        (r'Compatible with Universal Phone Cables', 'Tương thích với cáp sạc điện thoại phổ thông'),
        (r'Early Soccer Robotics Kit', 'Bộ Kit Robot đá bóng vỡ lòng (Early Soccer Robotics Kit)'),
        (r'Clip robot', 'Robot kẹp gắp'),
        (r'High-speed Chainsaw', 'Máy cưa xích tốc độ cao'),
        (r'3\.\s*High sensitivity, with a Bop as low as 0\.9 mT', '3. Độ nhạy cao, với ngưỡng Bop thấp tới 0.9 mT'),
        (r'● After-School Training Institutions, Youth<br\s*/?>Activity Centers, Programming Workshops', '● Các trung tâm đào tạo ngoại khóa, nhà thiếu nhi, câu lạc bộ lập trình'),
        (r'Students can consider different\s+task\s*<br\s*/?>categories,\s*relevant task settings,\s*and\s*<br\s*/?>various route planning solutions\.', 'Học sinh có thể xem xét các hạng mục nhiệm vụ khác nhau, các thiết lập nhiệm vụ liên quan và các giải pháp lập kế hoạch lộ trình đa dạng.'),

        # Lesson titles with <br/>
        (r'Animated Emoticon<br\s*/?>Robot', 'Robot biểu cảm<br/>hoạt hình'),
        (r'Bicycle Riding Robot<br\s*/?>Musician', 'Robot nhạc công<br/>đi xe đạp'),
        (r'Bicycling<br\s*/?>Little Dinosaur', 'Khủng long nhỏ<br/>đi xe đạp'),
        (r'Catapult Car<br\s*/?>Pullback Car', 'Xe bắn đá &<br/>Xe dây cót'),
        (r'Pirate Ship<br\s*/?>Music Box', 'Tàu cướp biển &<br/>Hộp âm nhạc'),
        (r'Obstacle Avoidance<br\s*/?>Robot 1', 'Robot tránh<br/>vật cản 1'),
        (r'Obstacle Avoidance<br\s*/?>Robot 2', 'Robot tránh<br/>vật cản 2'),
        (r'Obstacle Avoidance<br\s*/?>in Snow', 'Robot vượt tuyết<br/>tránh vật cản'),
        (r'Super Trajectory<br\s*/?>Robot 1', 'Robot siêu quỹ đạo 1'),
        (r'Super Trajectory<br\s*/?>Robot 2', 'Robot siêu quỹ đạo 2'),
        (r'Super Trajectory<br\s*/?>Robot 3', 'Robot siêu quỹ đạo 3'),
        (r'Super Trajectory<br\s*/?>Robot 4', 'Robot siêu quỹ đạo 4'),
        (r'Cement Mixer<br\s*/?>Truck', 'Xe trộn bê tông'),
        (r'Basketball Shooting<br\s*/?>Machine', 'Máy ném bóng rổ'),
        (r'Treadle Sewing<br\s*/?>Machine', 'Máy may đạp chân'),
        (r'Architectural<br\s*/?>design', 'Thiết kế kiến trúc'),
        (r'Hazard Avoidance<br\s*/?>Robot', 'Robot tránh hiểm họa'),
        (r'Electric Fan<br\s*/?>Rowing', 'Quạt điện & Thuyền chèo'),
        (r'Little Dancer<br\s*/?>Carousel', 'Vũ công nhí & Vòng quay ngựa gỗ'),
        (r'Little Turtle<br\s*/?>Dancing Robot', 'Rùa con & Robot khiêu vũ'),
        (r'High-speed Chainsaw<br\s*/?>Automatic Clothes Hanger<br\s*/?>Blender<br\s*/?>Sliding Door', 'Máy cưa xích tốc độ cao<br/>Giàn phơi tự động<br/>Máy xay sinh tố<br/>Cửa trượt'),
        (r'Penalty Shootout<br\s*/?>Dog-ThemedClock<br\s*/?>Pas DE Deux<br\s*/?>Simple Password', 'Sút luân lưu<br/>Đồng hồ chú chó<br/>Vũ điệu đôi (Pas De Deux)<br/>Mật khẩu đơn giản'),
        (r'High-speed Racer<br\s*/?>Obstacle Avoidance Car<br\s*/?>Little Turtle<br\s*/?>Dancing Robot', 'Xe đua tốc độ cao<br/>Xe tránh vật cản<br/>Rùa nhỏ<br/>Robot khiêu vũ'),
        (r'Burst Drummer<br\s*/?>Pull-up<br\s*/?>Bicycle Riding Robot<br\s*/?>Musician', 'Tay trống sôi động<br/>Robot kéo xà<br/>Robot đi xe đạp<br/>Nhạc công'),
        (r'Gymnast<br\s*/?>Cheerleaders<br\s*/?>Swimmer<br\s*/?>Pastry Maker', 'Vận động viên thể dục<br/>Đội cổ vũ<br/>Vận động viên bơi<br/>Thợ làm bánh'),
        (r'Inchworm<br\s*/?>Magic Dragon<br\s*/?>Running Bull<br\s*/?>Hopping Rabbit', 'Sâu đo<br/>Rồng thần kỳ<br/>Bò tót chạy<br/>Thỏ nhảy'),
        (r'Motorcycle<br\s*/?>Racing Car<br\s*/?>Helicopter<br\s*/?>Rickshaw', 'Xe mô tô<br/>Xe đua<br/>Trực thăng<br/>Xe xích lô'),
        (r'Rocket Car<br\s*/?>Rotating Airplane<br\s*/?>Wire Control Car<br\s*/?>Catapult Pistol', 'Xe tên lửa<br/>Máy bay quay<br/>Xe điều khiển dây<br/>Súng bắn đá'),
        (r'Telescopic Clip<br\s*/?>Gyro Launcher<br\s*/?>Catapult Car<br\s*/?>Pullback Car', 'Kẹp gắp co giãn<br/>Bệ phóng con quay<br/>Xe bắn đá<br/>Xe dây cót'),
        (r'Little Dancer<br\s*/?>Carousel<br\s*/?>Electric Fan<br\s*/?>Rowing', 'Vũ công nhỏ<br/>Vòng quay ngựa gỗ<br/>Quạt điện<br/>Thuyền chèo'),
        (r'Crab<br\s*/?>Hummingbird<br\s*/?>Bigfoot<br\s*/?>Hard Working Miner', 'Con cua<br/>Chim ruồi<br/>Người tuyết Bigfoot<br/>Thợ mỏ chăm chỉ'),
        (r'Pirate Ship<br\s*/?>Music Box<br\s*/?>Bicycling<br\s*/?>Little Dinosaur', 'Tàu cướp biển<br/>Hộp âm nhạc<br/>Đạp xe<br/>Khủng long nhỏ'),
        (r'Ball Holding Robot<br\s*/?>Bell-Striking Robot<br\s*/?>Jump Rope Robot<br\s*/?>Knight Duel', 'Robot giữ bóng<br/>Robot gõ chuông<br/>Robot nhảy dây<br/>Hiệp sĩ đấu kiếm'),
        (r'Gorilla<br\s*/?>Little Saving Assistant<br\s*/?>Cuckoo Clock', 'Khỉ đột<br/>Trợ lý tiết kiệm nhỏ<br/>Đồng hồ chim cúc cu'),
        (r'Lower grades of primary school \(grades 1-3\)\s*<br\s*/?>\s*Upper grades of primary school \(grades 4-6\)\s*<br\s*/?>\s*Junior high school\s*<br\s*/?>\s*High school', 'Tiểu học (Lớp 1–3)<br/>Tiểu học (Lớp 4–6)<br/>Trung học cơ sở<br/>Trung học phổ thông'),
        (r'Junior high school<br\s*/?>\s*High school', 'Trung học cơ sở<br/>Trung học phổ thông'),
        (r'Lesson<br\s*/?>NO\.', 'Số<br/>bài học'),
        (r'Stage 1<br\s*/?>Force and<br\s*/?>Machinery', 'Giai đoạn 1<br/>Lực và Cơ khí'),
        (r'Stage 2<br\s*/?>Engineering<br\s*/?>Challenges', 'Giai đoạn 2<br/>Thử thách Kỹ thuật'),
        (r'Stage 3<br\s*/?>Smart Life', 'Giai đoạn 3<br/>Cuộc sống Thông minh'),
        (r'Temperature And<br\s*/?>Humidity Sensor', 'Cảm biến nhiệt độ<br/>& độ ẩm'),
        (r'Bluetooth Remote<br\s*/?>Control Handle', 'Tay cầm điều khiển<br/>Bluetooth'),
        (r'2\.4G Wireless Communication<br\s*/?>Module', 'Mô-đun giao tiếp<br/>không dây 2.4G'),
        (r'Hydraulic<br\s*/?>Machine', 'Máy thủy lực'),
        (r'Sorting<br\s*/?>Machine', 'Máy phân loại'),
        (r'Mechanical<br\s*/?>Claw', 'Tay kẹp cơ khí'),
        (r'Voice Control<br\s*/?>Vehicle', 'Xe điều khiển<br/>giọng nói'),
        (r'Wired Remote<br\s*/?>Control Vehicle', 'Xe điều khiển<br/>có dây'),
        (r'Sound Level<br\s*/?>Meter', 'Máy đo<br/>cường độ âm'),
        (r'Guess the<br\s*/?>Password', 'Giải mã<br/>mật khẩu'),
        (r'Gravity<br\s*/?>Launch', 'Phóng bằng<br/>trọng lực'),
        (r'Starship<br\s*/?>Docking', 'Ghép nối<br/>tàu vũ trụ'),
        (r'Interstellar<br\s*/?>Vortex', 'Xoáy<br/>liên sao'),
        (r'Star Map<br\s*/?>Decoding', 'Giải mã<br/>bản đồ sao'),
        (r'Energy<br\s*/?>Refill', 'Nạp<br/>năng lượng'),
        (r'Space-time<br\s*/?>Distortion', 'Biến dạng<br/>không - thời gian'),
        (r'Interstellar Scientific<br\s*/?>Research', 'Nghiên cứu khoa học<br/>liên sao'),
        (r'Interactive<br\s*/?>Performance', 'Trình diễn<br/>tương tác'),
        (r'Drama Stage<br\s*/?>Passionate Drummer', 'Sân khấu kịch &<br/>Tay trống sôi động'),
        (r'High-speed Chainsaw<br\s*/?>Automatic Clothes Hanger', 'Máy cưa xích tốc độ cao & Giàn phơi tự động'),
        (r'High-speed Racer<br\s*/?>Obstacle Avoidance Car', 'Xe đua tốc độ cao & Xe tránh vật cản'),
        (r'Rocket Car<br\s*/?>Rotating Airplane', 'Xe tên lửa & Máy bay xoay'),
        (r'Running Bull<br\s*/?>Hopping Rabbit', 'Bò tót chạy & Thỏ nhảy nhót'),
        (r'Sled Dog<br\s*/?>Radar Car', 'Chó kéo xe & Xe radar'),
        (r'Swimmer<br\s*/?>Pastry Maker', 'Vận động viên bơi & Máy làm bánh'),
        (r'Vibrating Sieve<br\s*/?>Machine', 'Máy sàng rung'),
        (r'Wire Control Car<br\s*/?>Catapult Pistol', 'Xe điều khiển dây & Súng bắn đá'),
        (r'Blackout Zone<br\s*/?>Model', 'Mô hình khu vực<br/>mất điện'),
        (r'Wormhole Observation<br\s*/?>Model', 'Mô hình trạm quan sát<br/>lỗ sâu'),
        (r'Space-Time Channel<br\s*/?>Model', 'Mô hình cổng<br/>không - thời gian'),
        (r'Space-Time Energy<br\s*/?>Conversion Model', 'Mô hình chuyển đổi<br/>năng lượng'),
        (r'Delivery Point<br\s*/?>Frame', 'Khung điểm giao hàng'),
        # Servo rotation
        (r'0[–\-]270°\s*servo\s*rotation', 'Servo xoay 0–270°'),
        (r'0[–\-]270°\s*xoay servo', 'Servo xoay 0–270°'),
        # RAM/ROM
        (r'2G\s+RAM[,\s]+16G\s+ROM', 'RAM 2GB, ROM 16GB'),
        (r'RAM\s*2G[,\s]+ROM\s*16G', 'RAM 2GB, ROM 16GB'),
    ]

    # A3. Sửa các bản dịch bị đảo ngữ pháp do Google Translate (Danh từ trước, tính từ sau)
    fix_subs = [
        (r'AHRS Cảm biến', 'Cảm biến AHRS'),
        (r'I²C Truyền dữ liệu', 'Truyền dữ liệu I²C'),
        (r'Mô-men Xoắn Cao', 'Mô-men xoắn cao'),
        (r'360° Điều khiển góc', 'Điều khiển góc quay 360°'),
        (r'Dữ liệu thái độ sáu trục', 'Dữ liệu góc nghiêng 6 trục'),
        (r'Tự động hiệu chỉnh', 'Tự động hiệu chuẩn'),
        (r'Chống ánh nắng', 'Chống chói sáng'),
        (r'chống nắng', 'chống nhiễu ánh sáng mặt trời'),
        (r'Đèn báo ngưỡng', 'Đèn chỉ báo ngưỡng'),
        (r'Màn hình bảy màu', 'Màn hình hiển thị 7 màu'),
        (r'LED ba màu khuếch tán', 'Đèn LED 3 màu khuếch tán'),
        (r'Chuyển đổi nhanh', 'Chuyển đổi trạng thái nhanh'),
        (r'Tiêu thụ điện năng thấp', 'Tiết kiệm điện năng'),
        (r'Chỉ báo trạng thái', 'Đèn chỉ báo trạng thái'),
        (r'Tuổi thọ dài', 'Tuổi thọ cao & bền bỉ'),
        (r'Cảm biến dao động laser', 'Cảm biến khoảng cách Laser'),
        (r'Chống nhiễu mạnh', 'Khả năng chống nhiễu mạnh'),
        (r'Phạm vi đo:2', 'Phạm vi đo: 2'),
        (r'Yên tĩnh & Bền bỉ', 'Vận hành êm ái & bền bỉ'),
        (r'Đĩa mã hóa tích hợp', 'Tích hợp đĩa mã hóa'),
        (r'Hoạt động điện áp rộng', 'Dải điện áp hoạt động rộng'),
        (r'Bánh răng chịu mài mòn', 'Bánh răng chống mài mòn'),
        (r'Chế độ lập trình và ngôn ngữ', 'Đa dạng chế độ và ngôn ngữ lập trình'),
        (r'3\.2" Điện dung\s*\n?\s*Màn hình cảm ứng', 'Màn hình cảm ứng điện dung 3.2"'),
        (r'2\.4" Điện dung\s*\n?\s*Màn hình cảm ứng', 'Màn hình cảm ứng điện dung 2.4"'),
        (r'Học hình ảnh \(Image Learning\)', 'Học hình ảnh'),
        (r'Nhận dạng tầm nhìn', 'Nhận diện thị giác'),
        (r'Nhận dạng khối Rubik', 'Nhận diện Rubik'),
        (r'Nhận dạng giọng nói', 'Nhận dạng giọng nói'),
        (r'Pullback Xe', 'Xe dây cót'),
        (r'ABS, v\.v\.', 'ABS, v.v.'),
        (r'2600 mAh pin lithium', 'Pin Lithium 2600mAh'),
        (r'và phát triển chuyên nghiệp\.', 'và phát triển chuyên sâu.'),
        (r'Xoay servo 0[–\-]270°', 'Servo xoay 0–270°'),
        (r'RAM 2G,\s*ROM 16G', 'RAM 2GB, ROM 16GB'),
    ]

    # B0. Khắc phục triệt để lỗi tràn khung và bị cắt ngang trên các khối card đồ họa ZMRobo
    html = re.sub(
        r'height\s*:\s*652px;?([^\x22\x27]*background-image:[^\x22\x27]*3-bg-2\.png)',
        r'min-height:652px;height:auto;padding-bottom:30px;\1',
        html, flags=re.IGNORECASE
    )
    html = re.sub(
        r'(background-image:[^\x22\x27]*3-bg-2\.png[^\x22\x27]*)height\s*:\s*652px;?',
        r'\1min-height:652px;height:auto;padding-bottom:30px;',
        html, flags=re.IGNORECASE
    )
    html = re.sub(
        r'height\s*:\s*1360px;?([^\x22\x27]*background-image:[^\x22\x27]*3-bg-3\.png)',
        r'min-height:1520px;height:auto;padding-bottom:60px;\1',
        html, flags=re.IGNORECASE
    )
    html = re.sub(
        r'(background-image:[^\x22\x27]*3-bg-3\.png[^\x22\x27]*)height\s*:\s*1360px;?',
        r'\1min-height:1520px;height:auto;padding-bottom:60px;',
        html, flags=re.IGNORECASE
    )
    # Chuyển tất cả các khối card lớn có height cố định (354px, 400px, 512px, 527px, 588px, 630px, 667px, 730px, 780px, 787px, 1000px, 1100px, 1712px, 1725px, 2700px) sang min-height + height:auto để không bao giờ cắt chữ tiếng Việt
    def _expand_fixed_card_height(m):
        style_str = m.group(1)
        if 'position:absolute' in style_str.replace(' ', '') or 'position:fixed' in style_str.replace(' ', ''):
            return m.group(0)
        style_new = re.sub(
            r'(?<![-\w])height\s*:\s*(354|360|400|428|500|512|527|588|630|667|730|780|787|1000|1100|1712|1725|2700)px\s*;?',
            r'min-height:\1px;height:auto;padding-bottom:32px;',
            style_str,
            flags=re.IGNORECASE
        )
        return f'style="{style_new}"'

    html = re.sub(r'style=["\x27]([^"\x27]+)["\x27]', _expand_fixed_card_height, html)

    # B. Tạm ẩn style và script
    stashed = []
    def stash(m):
        stashed.append(m.group(0))
        return f"__STASH_{len(stashed)-1}__"

    html = re.sub(r'<(style|script)[^>]*>.*?</\1>', stash, html, flags=re.DOTALL)

    # C0. Tạm gom các thẻ <br/> nằm giữa câu văn thành khoảng trắng để dịch trọn vẹn cả câu chuẩn ngữ pháp
    html = re.sub(r'<br\s*/?>', ' ', html, flags=re.IGNORECASE)

    # C. Thay thế text nodes từ bộ nhớ đệm cache TRƯỚC KHI chạy phrase_subs
    # (Để tránh việc phrase_subs thay thế 1 cụm từ bên trong câu tiếng Anh làm mất khớp key của cả câu)
    def repl(m):
        full = m.group(1)
        stripped = full.strip()
        cleaned = re.sub(r'\s+', ' ', stripped)
        # BẢO VỆ TUYỆT ĐỐI CÁC THỰC THỂ KHOẢNG TRẮNG / DẤU CÁCH HTML
        # Không bao giờ xóa hoặc biến &nbsp; thành rỗng
        if cleaned in ('&nbsp;', '&nbsp;&nbsp;', '&ensp;', '&emsp;', '&#160;', '&#xA0;'):
            return m.group(0)
        if not re.search(r'[a-zA-Z0-9\u00C0-\u024F\u1E00-\u1EFF]', cleaned):
            return m.group(0)
        if cleaned in trans_map:
            leading = full[:len(full) - len(full.lstrip())]
            trailing = full[len(full.rstrip()):]
            return f">{leading}{trans_map[cleaned]}{trailing}<"
        return m.group(0)

    html = re.sub(r'>([^<]+)<', repl, html)

    # C2. Áp dụng phrase_subs và fix_subs SAU KHI đã dịch các câu nguyên vẹn
    for p, r in phrase_subs:
        html = re.sub(p, r, html, flags=re.IGNORECASE)

    for p, r in fix_subs:
        html = re.sub(p, r, html)

    # E. KHẮC PHỤC TRIỆT ĐỂ LỖI CHỮ DÍNH VÀO NHAU (ĐẢM BẢO ĐÚNG 1 KHOẢNG CÁCH TỰ NHIÊN, KHÔNG BỊ KÉP):
    # E1. Đảm bảo các cặp tiêu đề Gradient luôn có đúng 1 khoảng cách chuẩn (&nbsp;)
    html = re.sub(
        r'(</span>)(?:\s*(?:&nbsp;)*\s*)(<span class=[\"\x27]gradient_tittle2[\"\x27]>)',
        r'\1&nbsp;\2',
        html, flags=re.IGNORECASE
    )
    # E2. Cặp thẻ Part List (>Phụ kiện</strong><strong>Danh sách< -> >Danh sách phụ kiện<)
    html = re.sub(
        r'>\s*Phụ kiện\s*</strong>\s*<strong>\s*Danh sách\s*<',
        r'>Danh sách phụ kiện</strong><strong><',
        html, flags=re.IGNORECASE
    )
    html = re.sub(
        r'(</(?:strong|b)>)(?:\s*(?:&nbsp;)*\s*)(<(?:strong|b)>)',
        r'\1&nbsp;\2',
        html, flags=re.IGNORECASE
    )
    # E3. Sửa ký tự bullet Wingdings bị dịch nhầm thành "Tôi" (PID 319)
    html = re.sub(
        r'<span style=[\"\x27][^\"\x27]*Wingdings[^\"\x27]*[\"\x27]>\s*(?:l|Tôi|I)\s*</span>',
        r'<span style="font-size:16px;">●</span>&nbsp;',
        html, flags=re.IGNORECASE
    )
    # E4. Quy tắc tổng quát cho các thẻ inline liền kề (span, strong, b, em, i) có chữ/số cả 2 bên mà không có khoảng trắng hay margin
    html = re.sub(
        r'([a-zA-Z0-9\u00C0-\u024F\u1E00-\u1EFF])</(span|strong|b|em|i)><(span|strong|b|em|i)(?![^>]*margin)[^>]*>([a-zA-Z0-9\u00C0-\u024F\u1E00-\u1EFF])',
        r'\1</\2>&nbsp;<\3>\4',
        html
    )
    # E5. Sửa lỗi dính số vào sau chữ (Động cơ1 -> Động cơ 1, Bước1 -> Bước 1)
    html = re.sub(r'(Động cơ|Cổng|Bước|Bài|Cấp độ|Phần)([0-9]+)', r'\1 \2', html)

    # Khôi phục thẻ <br/> đã bảo vệ từ br_subs
    html = html.replace('__BR__', '<br/>')

    # D. Khôi phục style và script
    for i, orig in enumerate(stashed):
        html = html.replace(f"__STASH_{i}__", orig)

    # F. CHUẨN HÓA KHOẢNG TRẮNG: Xóa bỏ triệt để tình trạng 2 dấu cách (do thừa \xa0 hoặc space + &nbsp;)
    # F1. Chuẩn hóa chuỗi \xa0 (non-breaking space của Unicode) và khoảng trắng liền kề thành đúng 1 dấu cách thường
    html = re.sub(r'[ \t\u00A0]{2,}', ' ', html)
    # F2. Xóa khoảng cách thừa nếu có dấu cách đứng sát &nbsp; (ví dụ ' &nbsp;' hoặc '&nbsp; ' -> '&nbsp;')
    html = re.sub(r'[ \t]+&nbsp;|&nbsp;[ \t]+', '&nbsp;', html)
    # F3. Chuẩn hóa nhiều &nbsp; liên tiếp thành đúng 1 &nbsp;
    html = re.sub(r'(?:&nbsp;){2,}', '&nbsp;', html)

    return html

def is_translatable(text):
    if not text: return False
    text = text.strip()
    if len(text) < 2 or text.isdigit(): return False
    if text.startswith('http://') or text.startswith('https://') or text.startswith('data:'): return False
    if text.startswith('&#') or text.startswith('&nbsp;'): return False
    letters = re.findall(r'[a-zA-Z]', text)
    return len(letters) >= 2

def run_translation_pipeline():
    print("==========================================================================")
    print("  BẮT ĐẦU QUY TRÌNH DỊCH TOÀN BỘ HỆ THỐNG ZMROBO SANG TIẾNG VIỆT CHUẨN   ")
    print("  (Khôi phục dữ liệu sạch, đúng ngữ pháp tiếng Việt, giữ tên Kit)         ")
    print("==========================================================================")

    # 1. Đọc dữ liệu gốc sạch từ data_raw/
    with open(os.path.join(RAW_DIR, "categories.json"), encoding='utf-8') as f:
        cats_raw = json.load(f)
    with open(os.path.join(RAW_DIR, "products_summary.json"), encoding='utf-8') as f:
        prods_sum_raw = json.load(f)
    with open(os.path.join(RAW_DIR, "products_full.json"), encoding='utf-8') as f:
        prods_full_raw = json.load(f)
    with open(os.path.join(RAW_DIR, "software.json"), encoding='utf-8') as f:
        software_raw = json.load(f)
    with open(os.path.join(RAW_DIR, "resources.json"), encoding='utf-8') as f:
        resources_raw = json.load(f)
    with open(os.path.join(RAW_DIR, "news.json"), encoding='utf-8') as f:
        news_raw = json.load(f)
    with open(os.path.join(RAW_DIR, "contact.json"), encoding='utf-8') as f:
        contact_raw = json.load(f)

    # 2. Xử lý Categories
    print("[1/6] Đang xử lý Categories (Cây danh mục chuẩn tiếng Việt)...")
    cats_vi = []
    for c in cats_raw:
        c_copy = dict(c)
        orig_title = c.get('title', '')
        c_copy['title_en'] = orig_title
        c_copy['title'] = PARENT_TRANS.get(orig_title, orig_title)
        new_children = []
        for sub in c.get('childrenList', []):
            sub_copy = dict(sub)
            s_orig = sub.get('title', '')
            sub_copy['title_en'] = s_orig
            sub_copy['title'] = SUB_TRANS.get(s_orig, s_orig)
            new_children.append(sub_copy)
        c_copy['childrenList'] = new_children
        cats_vi.append(c_copy)

    with open(os.path.join(DATA_DIR, "categories.json"), 'w', encoding='utf-8') as f:
        json.dump(cats_vi, f, ensure_ascii=False, indent=2)
    print(" -> Đã lưu data/categories.json")

    # 3. Thu thập toàn bộ các chuỗi/đoạn văn cần dịch từ dữ liệu gốc
    print("[2/6] Đang thu thập các chuỗi văn bản từ dữ liệu gốc...")
    to_translate = set()

    # Product intros and content nodes
    for p in prods_full_raw:
        d = (p.get('detail') or {}).get('productInfo', {}) or {}
        intro = d.get('intro', '')
        if is_translatable(intro):
            to_translate.add(re.sub(r'\s+', ' ', intro.strip()))
        
        c = d.get('content', '')
        if c:
            c_clean = re.sub(r'<(style|script)[^>]*>.*?</\1>', ' ', c, flags=re.DOTALL)
            c_clean = re.sub(r'<br\s*/?>', ' ', c_clean, flags=re.IGNORECASE)
            nodes = re.findall(r'>([^<]+)<', c_clean)
            for node in nodes:
                cleaned = re.sub(r'\s+', ' ', node.strip())
                if is_translatable(cleaned):
                    to_translate.add(cleaned)

    # Software
    for sw in software_raw:
        d = (sw.get('detail') or {}).get('softwareInfo', {}) or {}
        intro = d.get('intro', '')
        if is_translatable(intro):
            to_translate.add(re.sub(r'\s+', ' ', intro.strip()))
        for h in (sw.get('detail') or {}).get('historyList', []):
            hc = h.get('content', '')
            if is_translatable(hc):
                to_translate.add(re.sub(r'\s+', ' ', hc.strip()))

    # Resources
    for r in resources_raw:
        title = (r.get('summary') or {}).get('title', '')
        if is_translatable(title):
            to_translate.add(re.sub(r'\s+', ' ', title.strip()))
        c = (r.get('detail') or {}).get('content', '')
        if is_translatable(c):
            to_translate.add(re.sub(r'\s+', ' ', c.strip()))

    # News
    for n in news_raw:
        st = (n.get('summary') or {}).get('title', '')
        if is_translatable(st):
            to_translate.add(re.sub(r'\s+', ' ', st.strip()))
        c = (n.get('detail') or {}).get('newsInfo', {}).get('content', '')
        if c:
            c_clean = re.sub(r'<(style|script)[^>]*>.*?</\1>', ' ', c, flags=re.DOTALL)
            c_clean = re.sub(r'<br\s*/?>', ' ', c_clean, flags=re.IGNORECASE)
            nodes = re.findall(r'>([^<]+)<', c_clean)
            for node in nodes:
                cleaned = re.sub(r'\s+', ' ', node.strip())
                if is_translatable(cleaned):
                    to_translate.add(cleaned)

    # Specific sample translations for accuracy
    manual_translations = {
        # === Tên thiết bị & thương hiệu - KHÔNG được dịch ===
        "AI CAM": "AI CAM",
        "AI Storm": "AI Storm",
        "Defender WiseKit": "Defender WiseKit",
        "Beta Set": "Beta Set",
        "Alpha Set A": "Alpha Set A",
        "Alpha Set B": "Alpha Set B",
        "Alpha Set C": "Alpha Set C",
        "Alpha Set D": "Alpha Set D",
        "Intelligence Storm": "Intelligence Storm",
        "Coding Master": "Coding Master",
        "Super Track Race": "Super Track Race",
        "Chip Cortex-M4": "Chip Cortex-M4",
        "Video": "Video",
        "GND (0V)": "GND (0V)",
        "JMP-BE-1548A": "JMP-BE-1548A",
        "JMP-BE-3581A": "JMP-BE-3581A",
        "JMP-BE-3582A": "JMP-BE-3582A",
        "JMP-BE-9528A": "JMP-BE-9528A",
        "JMP-BE-1748": "JMP-BE-1748",
        "JMP-BE-RJ11L20": "JMP-BE-RJ11L20",
        "JMP-BE-RJ11L30": "JMP-BE-RJ11L30",
        "JMP-BE-RJ11L50": "JMP-BE-RJ11L50",
        "JMP-BE-RJ11L110": "JMP-BE-RJ11L110",
        "JMP-BE-RJ11L300": "JMP-BE-RJ11L300",
        "JMP-BE-1131A": "JMP-BE-1131A",
        "Bluetooth 5.0": "Bluetooth 5.0",
        "Bluetooth® 5.0": "Bluetooth® 5.0",
        "radian": "radian",
        "RAM 2G, ROM 16G": "RAM 2GB, ROM 16GB",
        "ABS, v.v.": "ABS, v.v.",
        "Xoay servo 0–270°": "Servo xoay 0–270°",
        "Pin lithium 2600mAh": "Pin Lithium 2600mAh",
        "Pin Lithium 3.7V 2100mah": "Pin Lithium 3.7V - 2100mAh",
        "2G RAM\uff0c16G ROM": "RAM 2GB, ROM 16GB",
        "2G RAM，16G ROM": "RAM 2GB, ROM 16GB",
        "RAM 2G, ROM 16G": "RAM 2GB, ROM 16GB",

        # === Tiêu đề & từ đơn thường gặp ===
        "Electronic": "Linh kiện điện tử",
        "Accessories": "Phụ kiện",
        "Innovation Storm": "Innovation Storm",
        "Robot Set": "Bộ Robot",
        "Multiple": "Đa dạng",
        "Programming Modes and Languages": "Chế độ và ngôn ngữ lập trình",
        "Model": "Mô hình",
        "Showcase": "Trưng bày",

        # === AI CAM icon labels (các từ đơn) ===
        "Store": "Kho ứng dụng",
        "Settings": "Cài đặt",
        "Camera": "Máy ảnh",
        "Face": "Nhận diện khuôn mặt",
        "Recognition": "Nhận diện",
        "Detection": "Phát hiện",
        "Color": "Màu sắc",
        "Tag": "Thẻ mã",
        "Object": "Vật thể",
        "Image": "Hình ảnh",
        "Digit": "Chữ số",
        "Gesture": "Cử chỉ",
        "Road": "Đường đi",
        "Human": "Người",
        "Classification": "Phân loại",
        "Chip": "Vi xử lý",

        # === Phần cứng & thông số kỹ thuật ===
        "Processor": "Bộ xử lý",
        "Electronic": "Linh kiện điện tử",
        "Multiple": "Đa dạng",
        "Speaker": "Loa ngoài",
        "Microphone": "Micrô",
        "Buzzer": "Còi buzzer",
        "Motor": "Động cơ",
        "Material": "Vật liệu",
        "ABS, v.v.": "Nhựa ABS, v.v.",
        "2600mAh": "Pin 2600mAh",
        "Pin Lithium": "Pin Lithium",
        "Bluetooth® 5.0": "Bluetooth® 5.0",
        "Bluetooth 5.0": "Bluetooth 5.0",
        "2G RAM,16G ROM": "RAM 2GB, ROM 16GB",
        "2.4-inch": "Màn hình 2.4 inch",
        "2.4 GHz": "Tần số 2.4 GHz",
        "management": "quản lý",
        "effort.": "dễ dàng.",
        "RFID": "RFID",
        "JMP-BE-1548A": "JMP-BE-1548A",
        "JMP-BE-3582A": "JMP-BE-3582A",
        "JMP-BE-9528A": "JMP-BE-9528A",
        "JMP-BE-1748": "JMP-BE-1748",
        "Cortex-M4": "Cortex-M4",
        "100+ PCS": "100+ chi tiết",
        "3.7V Pin Lithium 2100mah": "Pin Lithium 3.7V - 2100mAh",
        "2600 mAh pin lithium": "Pin Lithium 2600mAh",
        "Mini Digital servo": "Servo kỹ thuật số mini",
        "0–270° xoay servo": "Servo xoay 0–270°",

        # === Bảng thông số kỹ thuật ===
        "PARAMETER": "THÔNG SỐ KỸ THUẬT",
        "Vss": "Vss (Điện áp nguồn âm)",
        "Iss": "Iss (Dòng điện nguồn)",
        "Vih": "Vih (Điện áp vào mức cao)",
        "Vil": "Vil (Điện áp vào mức thấp)",
        "Vout": "Vout (Điện áp ra)",
        "GND (0V)": "GND (0V)",
        "Paramter": "Thông số",
        "deg ree": "độ",
        "rad": "radian",
        "radian": "radian",

        # === Bảng khóa học / bài học ===
        "Unit": "Chủ đề",
        "Unit 1": "Chủ đề 1",
        "Unit 2": "Chủ đề 2",
        "Unit 3": "Chủ đề 3",
        "Unit 4": "Chủ đề 4",
        "Stage": "Giai đoạn",
        "Stage 1": "Giai đoạn 1",
        "Stage 2": "Giai đoạn 2",
        "Stage 3": "Giai đoạn 3",
        "Lesson": "Bài học",
        "Theme": "Chủ đề",
        "Name": "Tên",
        "Machine": "Máy",
        "Blocks": "Chi tiết lắp ghép",
        "Coach": "Hướng dẫn",
        "practice.": "thực hành.",
        "Competition": "Thi đấu",

        # === Tên robot / bài học ===
        "Bridge": "Cầu",
        "House": "Nhà",
        "Spider": "Nhện",
        "Bird": "Chim",
        "Dart": "Phi tiêu",
        "Balance": "Cân bằng",
        "Door": "Cửa",
        "Clock": "Đồng hồ",
        "Push-up": "Chống đẩy",
        "Scorpion": "Bọ cạp",
        "Vehicle": "Phương tiện",
        "Meter": "Đồng hồ đo",
        "Gibbon": "Vượn",
        "Reaction": "Phản xạ",
        "Blender": "Máy xay sinh tố",
        "Pull-up": "Kéo xà",
        "Cheerleaders": "Đội cổ vũ",
        "Swimmer": "Vận động viên bơi",
        "Pastry Maker": "Máy làm bánh",
        "Animals United": "Vương quốc động vật",
        "Inchworm": "Sâu đo",
        "Magic Dragon": "Rồng thần kỳ",
        "Running Bull": "Bò tót chạy",
        "Hopping Rabbit": "Thỏ nhảy",
        "Helicopter": "Máy bay trực thăng",
        "Rickshaw": "Xe xích lô",
        "Gyro Launcher": "Máy phóng con quay",
        "Catapult Car": "Xe bắn đá",
        "Rowing": "Thuyền chèo",
        "Crab": "Con cua",
        "Hummingbird": "Chim ruồi",
        "Bigfoot": "Người tuyết Bigfoot",
        "Hard Working Miner": "Thợ mỏ chăm chỉ",
        "Music Box": "Hộp nhạc",
        "Bicycling": "Đạp xe",
        "Little Dinosaur": "Khủng long nhỏ",
        "Gorilla": "Khỉ đột",
        "Knight Duel": "Hiệp sĩ đấu kiếm",
        "Swing": "Xích đu",
        "Crane": "Cần cẩu",
        "Frame": "Khung",
        "Gravity": "Trọng lực",
        "Energy": "Năng lượng",
        "Interstellar": "Liên sao",
        "Docking": "Ghép nối",
        "Vortex": "Xoáy nước",
        "Starship": "Tàu vũ trụ",
        "Refill": "Bổ sung nhiên liệu",
        "LLaunch": "Phóng tên lửa",
        "Gravity Launch": "Phóng bằng lực hấp dẫn",

        # === Nội dung khóa học ===
        "Focus": "Nội dung trọng tâm",
        "Content": "Nội dung",
        "Case": "Bài thực hành",
        "Topics": "Chủ đề bài học",
        "Lift": "Thang máy",
        "Truck": "Xe tải",
        "Tank": "Xe tăng",
        "Wipers": "Gạt nước",
        "Triangle": "Hình tam giác",
        "mechanical": "cơ khí",
        "Mechanical": "Cơ khí",
        "structural": "cấu trúc",
        "Engineering": "Kỹ thuật",
        "Challenges": "Thử thách",
        "Initialization": "Khởi tạo",
        "Lathe": "Máy tiện",
        "Claw": "Kẹp gắp",
        "Encoding": "Mã hóa",
        "Smart Life": "Cuộc sống thông minh",
        "Trolley": "Xe đẩy hàng",
        "Machinery": "Máy móc",

        # === Bộ Kit & nhãn hiệu ===
        "Alpha Set A": "Alpha Set A",
        "Alpha Set B": "Alpha Set B",
        "Alpha Set C": "Alpha Set C",
        "Alpha Set D": "Alpha Set D",
        "Beta Set": "Beta Set",
        "Defender WiseKit": "Defender WiseKit",
        "Intelligence Storm": "Intelligence Storm",
        "AI Storm": "AI Storm",
        "Super Track Race": "Super Track Race",
        "Coding Master": "Coding Master",
        "Curriculum Of Alpha Set D": "Giáo trình Alpha Set D",
        "Curriculum of Mini Creation": "Giáo trình Mini Creation",

        # === Tên khóa học & nhiệm vụ ===
        "Elementary Missions": "Nhiệm vụ cơ bản",
        "Advanced Missions": "Nhiệm vụ nâng cao",
        "Wheel & Go": "Lăn bánh & Chạy đi",
        "Loop It": "Lặp lại nào",
        "Creative Time": "Giờ sáng tạo",
        "Add-on Sensors (purchased separately)": "Cảm biến mở rộng (mua thêm)",
        "Bluetooth Remote": "Điều khiển Bluetooth",

        # === Hướng dẫn & chú thích ===
        "NOTICE": "LƯU Ý",
        "Download Manual": "Tải sách hướng dẫn",
        "Part": "Phụ kiện",
        "List": "Danh sách",
        "INDICATOR LIGHT": "ĐÈN CHỈ BÁO",
        "brown": "màu nâu",
        "red": "màu đỏ",
        "black": "màu đen",
        "available": "có sẵn",
        "Video": "Video",
        "cards": "thẻ bài",
        "system": "hệ thống",
        "APP": "Ứng dụng",

        # === Tính năng sản phẩm ===
        "FPV": "FPV (Camera góc nhìn thứ nhất)",
        "AHD": "AHD (Camera HD tương tự)",
        "LCD Display": "Màn hình LCD",
        "Image Learning": "Học hình ảnh",
        "Solution Overview (Secondary School Group)": "Tổng quan giải pháp (Nhóm Trung học cơ sở)",
        "Competition Robot Requirements": "Yêu cầu robot thi đấu",
        "Pullback Xe": "Xe dây cót",

        # === Màn hình cảm ứng (đã được tách thành 2 dòng riêng) ===
        "3.2\" Điện dung": "Màn hình 3.2\"",
        "Màn hình cảm ứng": "Màn hình cảm ứng",
        "2.4\" Điện dung": "Màn hình 2.4\"",
        "The Eyes and Mind of Robots": "Đôi mắt và trí tuệ của Robot",
        "Bumper car": "Xe điện đụng",
        "Electronic Pet Dog": "Robot chó cưng điện tử",
        "Carousel": "Vòng quay ngựa gỗ",
        "Ferris wheel": "Vòng đu quay đứng",
        "Robotic Arm": "Cánh tay robot",
        "Conveyor belt": "Băng chuyền tải",
        "Air pump": "Máy bơm khí nén",
        "Flame sensor": "Cảm biến phát hiện lửa",
        "Attitude sensor": "Cảm biến góc nghiêng & con quay hồi chuyển",
        "SmartCraft Competition Set includes 8 electronic components:": "Bộ thi đấu SmartCraft bao gồm 8 linh kiện điện tử:",
        "contains 4 types of electronic accessories": "gồm có 4 loại phụ kiện điện tử",
        "contains 2 types of electronic accessories": "gồm có 2 loại phụ kiện điện tử",
        "Pui Ching Middle School Macau held the completion ceremony for the 'Smart Education Center'": "Trường Trung học Pui Ching (Ma Cao) tổ chức lễ khánh thành 'Trung tâm Giáo dục Thông minh'",
        
        # Sensor & Actuator specs
        "Continuous Signal": "Tín hiệu liên tục",
        "Fast Response": "Phản hồi nhanh",
        "Threshold Indicator": "Chỉ báo ngưỡng",
        "Sunlight Resistant": "Chống chói sáng",
        "Color Lamp": "Đèn LED đa màu",
        "Seven-color Display": "Màn hình hiển thị 7 màu",
        "Diffused Tri-color LED": "Đèn LED 3 màu khuếch tán",
        "Quick Switching": "Chuyển đổi trạng thái nhanh",
        "Low Power Consumption": "Tiết kiệm điện năng",
        "Touch Sensor": "Cảm biến chạm",
        "Photoelectric Switch": "Công tắc quang điện",
        "High Sensitivity": "Độ nhạy cao",
        "Laser Ranging Sensor": "Cảm biến khoảng cách Laser",
        "Measuring range:2–120cm": "Phạm vi đo: 2–120cm",
        "Measuring range: 2-120cm": "Phạm vi đo: 2–120cm",
        "Measuring range:2-120cm": "Phạm vi đo: 2–120cm",
        "Accuracy: ±1 cm": "Độ chính xác: ±1 cm",
        "Accuracy: ± 1 cm": "Độ chính xác: ±1 cm",
        "AHRS Sensor": "Cảm biến góc nghiêng AHRS",
        "Six-axis Attitude Data": "Dữ liệu góc nghiêng 6 trục",
        "Auto Calibration": "Tự động hiệu chuẩn",
        "High Responsiveness": "Độ phản hồi cao",
        "High Precision": "Độ chính xác cao",
        "Large Geared Motor": "Động cơ giảm tốc lớn",
        "High Torque": "Mô-men xoắn cao",
        "Dual-shaft Output": "Đầu ra trục kép",
        "Quiet & Durable": "Vận hành êm ái & bền bỉ",
        "Quiet &amp; Durable": "Vận hành êm ái & bền bỉ",
        "Built-in Encoder Disk": "Tích hợp đĩa mã hóa Encoder",
        "Digital Servo": "Servo kỹ thuật số",
        "360° Angle Control": "Điều khiển góc quay 360°",
        "Wide Voltage Operation": "Dải điện áp hoạt động rộng",
        "Wear-resistant Gears": "Bánh răng chống mài mòn",
        "Status Indicator": "Đèn chỉ báo trạng thái",
        "Long Lifespan": "Tuổi thọ cao & bền bỉ",
        "I²C Data Transmission": "Truyền dữ liệu qua cổng I²C",
        "Strong Anti-interference": "Khả năng chống nhiễu mạnh",
        "Participant Categories": "Đối tượng tham gia",
        "Getting to Know Python": "Làm quen với ngôn ngữ Python",
        "Applications of Python": "Ứng dụng của Python",
        "Curling Game": "Trò chơi bi sắt đá băng (Curling)",
        "Small Fan": "Quạt gió mini",
        "Compatible with Universal Phone Cables": "Tương thích với cáp sạc điện thoại phổ thông",
        "Early Soccer Robotics Kit": "Bộ Kit Robot đá bóng vỡ lòng (Early Soccer Robotics Kit)",
        "Clip robot": "Robot kẹp gắp",
        "High-speed Chainsaw": "Máy cưa xích tốc độ cao",
        "3. High sensitivity, with a Bop as low as 0.9 mT": "3. Độ nhạy cao, với ngưỡng Bop thấp tới 0.9 mT",
        "Acoustic control lamp": "Đèn điều khiển bằng âm thanh",
        "Anti-drop Car": "Xe chống rơi",
        "Anti-theft Door": "Cửa chống trộm",
        "Balancing Bird": "Chim thăng bằng",
        "Barrier Gate": "Thanh chắn Barrier tự động",
        "Ball-Throwing Robot": "Robot ném bóng",
        "Hazard Avoidance Robot": "Robot tránh hiểm họa",
        "Sled Dog": "Chó kéo xe",
        "Radar Car": "Xe radar",
        "An exploration of pulleys": "Khám phá hệ thống ròng rọc",
        "Application and characteristics analysis of worm drive": "Ứng dụng và phân tích đặc tính của bộ truyền trục vít",
        "Application of multi-level gear drive": "Ứng dụng của bộ truyền bánh răng nhiều cấp"
    }

    # Đọc cache nếu có (loại bỏ các key lỗi hoặc dịch giữ nguyên tiếng Anh)
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                old_cache = json.load(f)
                for k, v in old_cache.items():
                    # Bỏ key nguồn có tiếng Việt
                    if any(c in k for c in 'àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđĐ'):
                        continue
                    # Bỏ key nguồn tiếng Anh mà bản dịch vẫn y hệt tiếng Anh (chưa dịch)
                    if k.strip() == v.strip() and len(k) > 2 and re.search(r'[a-zA-Z]{3,}', k):
                        continue
                    cache[k] = post_process_stem(v)
        except Exception:
            cache = {}

    for k, v in manual_translations.items():
        cache[k] = v

    missing = [t for t in to_translate if t not in cache]
    print(f" -> Tổng số chuỗi cần dịch: {len(to_translate)} (Đã có sẵn: {len(to_translate)-len(missing)}, Cần dịch mới: {len(missing)})")

    # 4. Dịch các chuỗi còn thiếu
    if missing:
        print("[3/6] Đang dịch các chuỗi qua API Google Translate (theo ngữ cảnh)...")
        batch_size = 25
        batches = [missing[i:i+batch_size] for i in range(0, len(missing), batch_size)]
        
        def process_batch(idx_batch):
            idx, batch = idx_batch
            trans = translate_batch_google(batch)
            return list(zip(batch, trans))

        with ThreadPoolExecutor(max_workers=5) as ex:
            results = ex.map(process_batch, enumerate(batches))
            count = 0
            for pair_list in results:
                for orig, tr in pair_list:
                    cache[orig] = tr
                count += len(pair_list)
                if count % 100 == 0 or count == len(missing):
                    print(f"   -> Đã hoàn thành {count} / {len(missing)} chuỗi...")

        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        print(" -> Đã lưu bộ nhớ đệm cache sạch vào data/translation_cache.json")

    # 5. Ghi đè vào Products Full & Products Summary
    print("[4/6] Đang áp dụng bản dịch vào Sản phẩm (Summary & Full Detail)...")
    
    # Products Summary
    summary_out = []
    for p in prods_sum_raw:
        pid = p['id']
        p_copy = dict(p)
        orig_title = p.get('title', '')
        orig_parent = p.get('parent_type', '')
        orig_type = p.get('type', '')

        p_copy['title_en'] = orig_title
        p_copy['parent_type_en'] = orig_parent
        p_copy['type_en'] = orig_type

        p_copy['title'] = translate_product_title(orig_title, pid)
        p_copy['parent_type'] = PARENT_TRANS.get(orig_parent, orig_parent)
        p_copy['type'] = SUB_TRANS.get(orig_type, orig_type)
        summary_out.append(p_copy)

    with open(os.path.join(DATA_DIR, "products_summary.json"), 'w', encoding='utf-8') as f:
        json.dump(summary_out, f, ensure_ascii=False, indent=2)

    # Products Full
    full_out = []
    for item in prods_full_raw:
        s = item.get('summary', {})
        d = (item.get('detail') or {}).get('productInfo', {}) or {}
        pid = s.get('id')

        s_copy = dict(s)
        s_copy['title_en'] = s.get('title', '')
        s_copy['parent_type_en'] = s.get('parent_type', '')
        s_copy['type_en'] = s.get('type', '')

        s_copy['title'] = translate_product_title(s.get('title', ''), pid)
        s_copy['parent_type'] = PARENT_TRANS.get(s.get('parent_type', ''), s.get('parent_type', ''))
        s_copy['type'] = SUB_TRANS.get(s.get('type', ''), s.get('type', ''))

        d_copy = dict(d) if d else {}
        if d_copy:
            d_copy['title_en'] = d.get('title', '')
            d_copy['parent_type_en'] = s_copy['parent_type_en']
            d_copy['type_en'] = s_copy['type_en']

            d_copy['title'] = s_copy['title']
            d_copy['parent_type'] = s_copy['parent_type']
            d_copy['type'] = s_copy['type']

            if d.get('intro'):
                intro_clean = re.sub(r'\s+', ' ', d['intro'].strip())
                d_copy['intro'] = cache.get(intro_clean, d['intro'])
            
            if d.get('content'):
                d_copy['content'] = translate_html_content(d['content'], cache)

        # Questions FAQ
        q_list = (item.get('detail') or {}).get('questionList', []) or []
        q_list_out = []
        for q in q_list:
            qc = dict(q)
            question = q.get('question', '')
            answer = q.get('answer', '')
            if 'How to use this kit' in question:
                qc['question'] = 'Làm thế nào để sử dụng bộ kit này?'
                qc['answer'] = 'Vui lòng thực hiện theo sách hướng dẫn sử dụng (sách Manual PDF đi kèm).'
            elif 'suitable for teenage' in question:
                qc['question'] = 'Bộ kit này có phù hợp cho lứa tuổi thanh thiếu niên không?'
                qc['answer'] = 'Hoàn toàn phù hợp!'
            else:
                q_clean = re.sub(r'\s+', ' ', question.strip())
                a_clean = re.sub(r'\s+', ' ', answer.strip())
                qc['question'] = cache.get(q_clean, question)
                qc['answer'] = cache.get(a_clean, answer)
            q_list_out.append(qc)

        detail_wrap = dict(item.get('detail', {}))
        detail_wrap['productInfo'] = d_copy
        detail_wrap['questionList'] = q_list_out

        full_out.append({
            'summary': s_copy,
            'detail': detail_wrap
        })

    with open(os.path.join(DATA_DIR, "products_full.json"), 'w', encoding='utf-8') as f:
        json.dump(full_out, f, ensure_ascii=False, indent=2)
    print(" -> Đã lưu data/products_summary.json và data/products_full.json")

    # 6. Phần mềm, Tài nguyên, Tin tức
    print("[5/6] Đang dịch Phần mềm, Tài nguyên và Tin tức...")
    
    # Software
    sw_out = []
    for item in software_raw:
        sw_copy = dict(item)
        d = (item.get('detail') or {}).get('softwareInfo', {}) or {}
        d_copy = dict(d)
        if d.get('intro'):
            cl = re.sub(r'\s+', ' ', d['intro'].strip())
            d_copy['intro'] = cache.get(cl, d['intro'])
        
        h_list = (item.get('detail') or {}).get('historyList', []) or []
        h_out = []
        for h in h_list:
            hc = dict(h)
            if h.get('content'):
                cl = re.sub(r'\s+', ' ', h['content'].strip())
                hc['content'] = cache.get(cl, h['content'])
            h_out.append(hc)

        det = dict(item.get('detail', {}))
        det['softwareInfo'] = d_copy
        det['historyList'] = h_out
        sw_copy['detail'] = det
        sw_out.append(sw_copy)

    with open(os.path.join(DATA_DIR, "software.json"), 'w', encoding='utf-8') as f:
        json.dump(sw_out, f, ensure_ascii=False, indent=2)

    # Resources
    res_out = []
    for item in resources_raw:
        r_copy = dict(item)
        s = dict(item.get('summary', {}))
        if s.get('title'):
            cl = re.sub(r'\s+', ' ', s['title'].strip())
            s['title'] = cache.get(cl, s['title'])
        r_copy['summary'] = s
        
        d = dict(item.get('detail', {}))
        if d.get('content'):
            cl = re.sub(r'\s+', ' ', d['content'].strip())
            d['content'] = cache.get(cl, d['content'])
        r_copy['detail'] = d
        res_out.append(r_copy)

    with open(os.path.join(DATA_DIR, "resources.json"), 'w', encoding='utf-8') as f:
        json.dump(res_out, f, ensure_ascii=False, indent=2)

    # News
    news_out = []
    for item in news_raw:
        n_copy = dict(item)
        s = dict(item.get('summary', {}))
        if s.get('title'):
            cl = re.sub(r'\s+', ' ', s['title'].strip())
            s['title'] = cache.get(cl, s['title'])
        n_copy['summary'] = s

        d = dict(item.get('detail', {}))
        ni = dict(d.get('newsInfo', {}))
        if ni.get('title'):
            cl = re.sub(r'\s+', ' ', ni['title'].strip())
            ni['title'] = cache.get(cl, ni['title'])
        if ni.get('content'):
            ni['content'] = translate_html_content(ni['content'], cache)
        d['newsInfo'] = ni
        n_copy['detail'] = d
        news_out.append(n_copy)

    with open(os.path.join(DATA_DIR, "news.json"), 'w', encoding='utf-8') as f:
        json.dump(news_out, f, ensure_ascii=False, indent=2)

    with open(os.path.join(DATA_DIR, "contact.json"), 'w', encoding='utf-8') as f:
        json.dump(contact_raw, f, ensure_ascii=False, indent=2)

    # 7. Xuất file CSV song ngữ chuẩn
    print("[6/6] Đang xuất file products.csv chuẩn song ngữ Excel...")
    csv_file = os.path.join(DATA_DIR, "products.csv")
    with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "ID", "Mã sản phẩm (Code)", "Tên sản phẩm (Tiếng Việt)", "Tên gốc (Tiếng Anh)", 
            "Danh mục chính", "Danh mục con", "Mô tả ngắn (Tiếng Việt)", "Ảnh đại diện (Cover)", 
            "Video", "Sách hướng dẫn (Manual)", "Số ảnh gallery", "Số phần mềm đi kèm", 
            "Số tài liệu đi kèm", "Số câu hỏi FAQ", "Cập nhật lúc"
        ])
        for item in full_out:
            s = item.get("summary", {})
            d = (item.get("detail") or {}).get("productInfo", {}) or {}
            covers = (item.get("detail") or {}).get("coverList", []) or []
            softwares = (item.get("detail") or {}).get("softwareList", []) or []
            resources = (item.get("detail") or {}).get("resourceList", []) or []
            faqs = (item.get("detail") or {}).get("questionList", []) or []
            
            writer.writerow([
                s.get("id"),
                s.get("code") or d.get("code", ""),
                s.get("title", ""),
                s.get("title_en", ""),
                s.get("parent_type", ""),
                s.get("type", ""),
                d.get("intro", ""),
                s.get("cover") or d.get("cover", ""),
                d.get("video", ""),
                d.get("manual", ""),
                len(covers),
                len(softwares),
                len(resources),
                len(faqs),
                d.get("update_time", "")
            ])

    print("==========================================================================")
    print("  HOÀN THÀNH TOÀN BỘ TIẾN TRÌNH DỊCH HỆ THỐNG VÀ CẬP NHẬT TẤT CẢ DỮ LIỆU! ")
    print(f"  Tất cả dữ liệu chuẩn tiếng Việt đã lưu tại: {DATA_DIR}                 ")
    print("==========================================================================")

if __name__ == "__main__":
    run_translation_pipeline()
