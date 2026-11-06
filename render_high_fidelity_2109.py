import os
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROD_DIR = os.path.join(BASE_DIR, "media", "stemtown", "static", "products", "JMC-NY-2109")

FONT_BOLD = "C:\\Windows\\Fonts\\arialbd.ttf"
FONT_REG = "C:\\Windows\\Fonts\\arial.ttf"

def get_font(size, bold=True):
    path = FONT_BOLD if bold else FONT_REG
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def draw_centered_text(draw, box, text, font, fill):
    """Vẽ text căn giữa chính xác trong bounding box [x1, y1, x2, y2]"""
    x1, y1, x2, y2 = box
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = x1 + (x2 - x1 - tw) // 2
    ty = y1 + (y2 - y1 - th) // 2 - bbox[1]
    draw.text((tx, ty), text, font=font, fill=fill)

def render_image_1():
    path = os.path.join(PROD_DIR, "1.jpg")
    img = Image.open(path).convert("RGB")
    draw = ImageDraw.Draw(img)

    c_canvas = (97, 195, 208)
    c_white = (255, 255, 255)

    draw.rectangle([280, 630, 580, 745], fill=c_canvas)
    f_logo_title = get_font(38, bold=True)
    draw.text((310, 640), "ROBOT", fill=c_white, font=f_logo_title)
    draw.text((300, 688), "CẢM BIẾN", fill=c_white, font=f_logo_title)

    img.save(path, quality=96)
    print("✓ Đã hoàn thiện 1.jpg")

def render_image_2():
    path = os.path.join(PROD_DIR, "2.jpg")
    img = Image.open(path).convert("RGB")
    draw = ImageDraw.Draw(img)

    c_hdr_bg = (86, 169, 183)
    c_val_bg = (97, 195, 208)
    c_white = (255, 255, 255)
    c_text_hdr = (25, 40, 50)
    c_text_val = (10, 20, 30)

    rows = [
        (18, 52),
        (54, 88),
        (90, 123),
        (125, 158),
        (160, 194)
    ]
    cols = [
        (56, 206, c_hdr_bg, c_text_hdr),
        (208, 361, c_val_bg, c_text_val),
        (363, 513, c_hdr_bg, c_text_hdr),
        (515, 692, c_val_bg, c_text_val)
    ]

    font_tbl = get_font(13, bold=True)

    data = [
        ["Tên sản phẩm", "Bộ Cảm biến Robot", "Mã hiệu / Model", "2109"],
        ["Chất liệu", "Nhựa ABS cao cấp", "Quy cách đóng gói", "Hộp nhựa + Hộp màu"],
        ["Trọng lượng", "1.0 kg", "Kích thước", "37 × 23 × 5.8 cm"],
        ["Số chi tiết", "19 chi tiết", "Độ tuổi phù hợp", "6+ tuổi"],
        ["Hướng dẫn sử dụng", "Kèm theo (Sách HDSD)", "Chứng nhận", "Tiêu chuẩn 3C / CE"]
    ]

    for r_idx, (y1, y2) in enumerate(rows):
        for c_idx, (x1, x2, bg, tc) in enumerate(cols):
            draw.rectangle([x1, y1, x2, y2], fill=bg)
            text = data[r_idx][c_idx]
            if text:
                draw_centered_text(draw, [x1, y1, x2, y2], text, font_tbl, tc)

    draw.rectangle([55, 17, 693, 195], outline=c_white, width=2)
    for y in [53, 89, 124, 159]:
        draw.line([(55, y), (693, y)], fill=c_white, width=2)
    for x in [207, 362, 514]:
        draw.line([(x, 17), (x, 195)], fill=c_white, width=2)

    draw.rectangle([100, 465, 650, 498], fill=c_val_bg)
    font_steam = get_font(14, bold=True)
    steam_items = [
        (177, "Khoa học"),
        (275, "Công nghệ"),
        (373, "Kỹ thuật"),
        (472, "Nghệ thuật"),
        (570, "Toán học")
    ]
    for cx, label in steam_items:
        draw_centered_text(draw, [cx - 50, 468, cx + 50, 495], label, font_steam, c_text_hdr)

    draw.rectangle([35, 512, 715, 678], fill=(86, 185, 198))
    font_desc = get_font(14, bold=True)
    desc_lines = [
        "Bộ sản phẩm được trang bị 13 mô-đun cảm biến, 1 adapter Bluetooth và 5 cáp kết nối.",
        "Các cảm biến tương thích hoàn hảo với bộ điều khiển E6 RCU của Technology Storm.",
        "Bộ cảm biến mở rộng nhiều phương thức thử nghiệm và lập trình điều khiển thông minh,",
        "giúp nội dung giảng dạy robot phong phú hơn và mang lại trải nghiệm học tập sáng tạo."
    ]
    line_y = 530
    for line in desc_lines:
        draw_centered_text(draw, [35, line_y, 715, line_y + 24], line, font_desc, (25, 45, 55))
        line_y += 34

    img.save(path, quality=96)
    print("✓ Đã dựng lại hoàn hảo 2.jpg")

def render_image_3():
    path = os.path.join(PROD_DIR, "3.jpg")
    img = Image.open(path).convert("RGB")
    draw = ImageDraw.Draw(img)

    c_canvas = (97, 195, 208)
    c_white = (255, 255, 255)
    c_pill_bg = (13, 134, 155)
    c_dark_navy = (20, 35, 45)

    # 1. CẢM BIẾN ĐO CỰ LY HỒNG NGOẠI
    draw.rectangle([390, 95, 680, 275], fill=c_canvas)
    f_title_main = get_font(32, bold=True)
    f_title_sub = get_font(24, bold=True)
    draw.text((395, 115), "CẢM BIẾN", fill=c_white, font=f_title_main)
    draw.text((395, 160), "HỒNG NGOẠI", fill=c_white, font=f_title_main)
    draw.text((395, 215), "Đo cự ly (Infrared Ranging)", fill=c_white, font=f_title_sub)

    draw.rounded_rectangle([115, 391, 392, 494], radius=16, fill=c_white)
    f_badge_hdr = get_font(24, bold=True)
    f_badge_val = get_font(20, bold=True)
    draw.text((135, 405), "Chức năng:", fill=c_dark_navy, font=f_badge_hdr)
    draw.text((135, 445), "Đo cự ly bằng tia hồng ngoại", fill=c_dark_navy, font=f_badge_val)

    draw.rounded_rectangle([195, 524, 485, 554], radius=15, fill=c_pill_bg, outline=c_white, width=2)
    f_pill = get_font(13, bold=True)
    draw_centered_text(draw, [195, 524, 485, 554], "Đo khoảng cách nhận diện chuẩn P1", f_pill, c_white)

    # 2. CẢM BIẾN ĐO CỰ LY TIA LASER
    draw.rectangle([390, 645, 680, 820], fill=c_canvas)
    draw.text((395, 665), "CẢM BIẾN", fill=c_white, font=f_title_main)
    draw.text((395, 710), "TIA LASER", fill=c_white, font=f_title_main)
    draw.text((395, 765), "Đo cự ly (Laser Ranging)", fill=c_white, font=f_title_sub)
    draw.rounded_rectangle([615, 768, 645, 792], radius=6, fill=c_white)
    f_x1 = get_font(12, bold=True)
    draw_centered_text(draw, [615, 768, 645, 792], "x1", f_x1, c_dark_navy)

    draw.rounded_rectangle([83, 923, 333, 1024], radius=16, fill=c_white)
    draw.text((105, 937), "Chức năng:", fill=c_dark_navy, font=f_badge_hdr)
    draw.text((105, 977), "Đo cự ly bằng tia Laser", fill=c_dark_navy, font=f_badge_val)

    draw.rounded_rectangle([175, 1054, 555, 1086], radius=16, fill=c_pill_bg, outline=c_white, width=2)
    draw_centered_text(draw, [175, 1054, 555, 1086], "Đọc tiêu chuẩn định vị mẫu P1 bằng tia Laser", f_pill, c_white)

    img.save(path, quality=96)
    print("✓ Đã dựng lại hoàn hảo 3.jpg")

def render_image_4():
    path = os.path.join(PROD_DIR, "4.jpg")
    img = Image.open(path).convert("RGB")
    draw = ImageDraw.Draw(img)

    c_canvas = (97, 195, 208)
    c_white = (255, 255, 255)
    c_pill_bg = (13, 134, 155)
    c_dark_navy = (20, 35, 45)

    f_title_main = get_font(32, bold=True)
    f_title_sub = get_font(22, bold=True)
    f_badge_hdr = get_font(24, bold=True)
    f_badge_val = get_font(20, bold=True)
    f_pill = get_font(13, bold=True)

    # 1. CẢM BIẾN CỬ CHỈ (Gesture Sensor)
    draw.rectangle([45, 70, 300, 180], fill=c_canvas)
    draw.text((50, 80), "CẢM BIẾN", fill=c_white, font=f_title_main)
    draw.text((50, 125), "CỬ CHỈ", fill=c_white, font=f_title_main)
    draw.rounded_rectangle([180, 135, 210, 158], radius=6, fill=c_white)
    f_x1 = get_font(12, bold=True)
    draw_centered_text(draw, [180, 135, 210, 158], "x1", f_x1, c_dark_navy)

    draw.rounded_rectangle([71, 265, 516, 367], radius=16, fill=c_white)
    draw.text((95, 280), "Chức năng:", fill=c_dark_navy, font=f_badge_hdr)
    draw.text((95, 320), "Nhận diện vẫy tay & cử chỉ không gian", fill=c_dark_navy, font=f_badge_val)

    draw.rounded_rectangle([192, 467, 499, 499], radius=16, fill=c_pill_bg, outline=c_white, width=2)
    draw_centered_text(draw, [192, 467, 499, 499], "Nhận diện cử chỉ tiêu chuẩn P1", f_pill, c_white)

    # 2. HỆ THỐNG THAM CHIẾU HƯỚNG & TƯ THẾ (AHRS)
    draw.rectangle([35, 550, 480, 690], fill=c_canvas)
    draw.text((40, 560), "HỆ THỐNG ĐỊNH HƯỚNG", fill=c_white, font=get_font(28, bold=True))
    draw.text((40, 605), "& THAM CHIẾU TƯ THẾ", fill=c_white, font=get_font(28, bold=True))
    draw.text((40, 650), "Hệ thống AHRS chuyên dụng", fill=c_white, font=f_title_sub)

    draw.rounded_rectangle([53, 820, 395, 939], radius=16, fill=c_white)
    draw.text((75, 835), "Chức năng:", fill=c_dark_navy, font=f_badge_hdr)
    draw.text((75, 875), "Xác định tư thế & góc nghiêng 3D", fill=c_dark_navy, font=get_font(18, bold=True))
    draw.text((75, 905), "Cảm biến vận tốc góc chính xác cao", fill=c_dark_navy, font=get_font(18, bold=True))

    draw.rounded_rectangle([135, 1012, 475, 1042], radius=15, fill=c_pill_bg, outline=c_white, width=2)
    draw_centered_text(draw, [135, 1012, 475, 1042], "Đọc cảm biến tư thế & định hướng P1", f_pill, c_white)

    draw.rounded_rectangle([20, 1058, 730, 1088], radius=15, fill=c_pill_bg, outline=c_white, width=2)
    draw_centered_text(draw, [20, 1058, 730, 1088], "Hiệu chỉnh phương vị nằm ngang theo mẫu P1 tiêu chuẩn", f_pill, c_white)

    img.save(path, quality=96)
    print("✓ Đã dựng lại hoàn hảo 4.jpg")

def render_image_5():
    path = os.path.join(PROD_DIR, "5.jpg")
    img = Image.open(path).convert("RGB")
    draw = ImageDraw.Draw(img)

    c_canvas = (97, 195, 208)
    c_white = (255, 255, 255)
    c_pill_bg = (13, 134, 155)
    c_dark_navy = (20, 35, 45)

    f_title = get_font(32, bold=True)
    f_badge_hdr = get_font(24, bold=True)
    f_badge_val = get_font(20, bold=True)
    f_pill = get_font(13, bold=True)

    # 1. CẢM BIẾN TỪ TÍNH (Magnetic Sensor)
    draw.rectangle([50, 160, 320, 275], fill=c_canvas)
    draw.text((55, 175), "CẢM BIẾN", fill=c_white, font=f_title)
    draw.text((55, 225), "TỪ TÍNH", fill=c_white, font=f_title)
    draw.rounded_rectangle([200, 235, 230, 258], radius=6, fill=c_white)
    f_x1 = get_font(12, bold=True)
    draw_centered_text(draw, [200, 235, 230, 258], "x1", f_x1, c_dark_navy)

    draw.rounded_rectangle([50, 350, 725, 440], radius=16, fill=c_white)
    draw.text((75, 360), "Chức năng:", fill=c_dark_navy, font=f_badge_hdr)
    draw.text((75, 400), "Phát hiện chính xác cường độ và hướng của từ trường", fill=c_dark_navy, font=f_badge_val)

    draw.rounded_rectangle([85, 470, 620, 500], radius=15, fill=c_pill_bg, outline=c_white, width=2)
    draw_centered_text(draw, [85, 470, 620, 500], "Đọc dữ liệu cường độ từ trường phát hiện P1", f_pill, c_white)

    draw.rounded_rectangle([85, 515, 620, 545], radius=15, fill=c_pill_bg, outline=c_white, width=2)
    draw_centered_text(draw, [85, 515, 620, 545], "Đọc dữ liệu hướng từ trường phát hiện P1", f_pill, c_white)

    # 2. CẢM BIẾN KHÍ ÁP (Barometric Sensor)
    draw.rectangle([50, 710, 420, 835], fill=c_canvas)
    draw.text((55, 725), "CẢM BIẾN", fill=c_white, font=f_title)
    draw.text((55, 775), "KHÍ ÁP", fill=c_white, font=f_title)

    draw.rounded_rectangle([55, 990, 600, 1080], radius=16, fill=c_white)
    draw.text((80, 1000), "Chức năng:", fill=c_dark_navy, font=f_badge_hdr)
    draw.text((80, 1040), "Đo lường cường độ áp suất khí quyển môi trường", fill=c_dark_navy, font=f_badge_val)

    draw.rounded_rectangle([105, 1092, 500, 1122], radius=15, fill=c_pill_bg, outline=c_white, width=2)
    draw_centered_text(draw, [105, 1092, 500, 1122], "Đọc dữ liệu áp suất khí quyển phát hiện P1", f_pill, c_white)

    img.save(path, quality=96)
    print("✓ Đã hoàn thiện 5.jpg")

def render_image_6():
    path = os.path.join(PROD_DIR, "6.jpg")
    img = Image.open(path).convert("RGB")
    draw = ImageDraw.Draw(img)

    c_canvas = (97, 195, 208)
    c_white = (255, 255, 255)
    c_pill_bg = (13, 134, 155)
    c_dark_navy = (20, 35, 45)

    f_title = get_font(30, bold=True)
    f_badge_hdr = get_font(24, bold=True)
    f_badge_val = get_font(20, bold=True)
    f_pill = get_font(13, bold=True)

    # 1. CẢM BIẾN NHIỆT ĐỘ & ĐỘ ẨM
    draw.rectangle([440, 245, 735, 385], fill=c_canvas)
    draw.text((450, 255), "CẢM BIẾN", fill=c_white, font=f_title)
    draw.text((450, 295), "NHIỆT ĐỘ", fill=c_white, font=f_title)
    draw.text((450, 335), "& ĐỘ ẨM", fill=c_white, font=f_title)

    draw.rounded_rectangle([60, 355, 725, 445], radius=16, fill=c_white)
    draw.text((85, 365), "Chức năng:", fill=c_dark_navy, font=f_badge_hdr)
    draw.text((85, 405), "Đo lường nhiệt độ và độ ẩm môi trường xung quanh", fill=c_dark_navy, font=f_badge_val)

    draw.rounded_rectangle([75, 465, 580, 495], radius=15, fill=c_pill_bg, outline=c_white, width=2)
    draw_centered_text(draw, [75, 465, 580, 495], "Đọc dữ liệu độ ẩm và nhiệt độ môi trường P1", f_pill, c_white)

    # 2. MẮT THẦN THÔNG MINH (Intelligent Eye x2)
    draw.rectangle([415, 580, 735, 700], fill=c_canvas)
    draw.text((425, 595), "MẮT THẦN", fill=c_white, font=f_title)
    draw.text((425, 640), "THÔNG MINH", fill=c_white, font=f_title)
    draw.rounded_rectangle([635, 645, 675, 675], radius=6, fill=c_white)
    f_x2 = get_font(14, bold=True)
    draw_centered_text(draw, [635, 645, 675, 675], "x2", f_x2, c_dark_navy)

    draw.rounded_rectangle([395, 720, 740, 850], radius=16, fill=c_white)
    draw.text((415, 730), "Chức năng:", fill=c_dark_navy, font=f_badge_hdr)
    draw.text((415, 770), "Vòng đèn LED đa sắc lập trình", fill=c_dark_navy, font=get_font(18, bold=True))
    draw.text((415, 805), "Giao tiếp và nhận diện hồng ngoại", fill=c_dark_navy, font=get_font(18, bold=True))

    img.save(path, quality=96)
    print("✓ Đã hoàn thiện 6.jpg")

def render_image_7():
    path = os.path.join(PROD_DIR, "7.jpg")
    img = Image.open(path).convert("RGB")
    draw = ImageDraw.Draw(img)

    c_canvas = (97, 195, 208)
    c_white = (255, 255, 255)
    c_dark_navy = (20, 35, 45)

    f_title = get_font(30, bold=True)

    # Tiêu đề Ma trận LED
    draw.rectangle([55, 40, 310, 200], fill=c_canvas)
    draw.text((60, 48), "MA TRẬN LED", fill=c_white, font=f_title)
    draw.text((60, 95), "ÁNH SÁNG XANH", fill=c_white, font=f_title)
    draw.text((60, 145), "16 × 16 ĐIỂM", fill=c_white, font=f_title)

    # Tiêu đề Camera Quét
    draw.rectangle([50, 1175, 290, 1300], fill=c_canvas)
    draw.text((55, 1185), "CAMERA", fill=c_white, font=f_title)
    draw.text((55, 1235), "QUÉT MÃ", fill=c_white, font=f_title)

    draw.rounded_rectangle([300, 1175, 650, 1310], radius=16, fill=c_white)
    draw.text((315, 1185), "Chức năng:", fill=c_dark_navy, font=get_font(22, bold=True))
    draw.text((315, 1225), "Quét mã QR tiêu chuẩn", fill=c_dark_navy, font=get_font(18, bold=True))
    draw.text((315, 1265), "Quét mã vạch sản phẩm", fill=c_dark_navy, font=get_font(18, bold=True))

    img.save(path, quality=96)
    print("✓ Đã hoàn thiện 7.jpg")

def render_image_8():
    path = os.path.join(PROD_DIR, "8.jpg")
    img = Image.open(path).convert("RGB")
    draw = ImageDraw.Draw(img)

    c_canvas = (97, 195, 208)
    c_white = (255, 255, 255)
    c_dark_navy = (20, 35, 45)

    f_title = get_font(34, bold=True)

    draw.rectangle([180, 45, 650, 105], fill=c_canvas)
    draw.text((195, 50), "MÔ-ĐUN THỊ GIÁC AI", fill=c_white, font=f_title)

    draw.rounded_rectangle([50, 380, 330, 505], radius=16, fill=c_white)
    draw.text((70, 390), "Chức năng:", fill=c_dark_navy, font=get_font(22, bold=True))
    draw.text((70, 430), "Thị giác máy tính (AI)", fill=c_dark_navy, font=get_font(18, bold=True))
    draw.text((70, 468), "Nhận diện giọng nói", fill=c_dark_navy, font=get_font(18, bold=True))

    img.save(path, quality=96)
    print("✓ Đã hoàn thiện 8.jpg")

def render_image_9():
    path = os.path.join(PROD_DIR, "9.jpg")
    img = Image.open(path).convert("RGB")
    draw = ImageDraw.Draw(img)

    c_canvas = (97, 195, 208)
    c_white = (255, 255, 255)
    c_dark_navy = (20, 35, 45)

    f_title = get_font(34, bold=True)

    draw.rectangle([85, 75, 660, 140], fill=c_canvas)
    draw.text((95, 82), "BỘ CHUYỂN ĐỔI BLUETOOTH", fill=c_white, font=f_title)

    draw.rounded_rectangle([95, 260, 520, 355], radius=16, fill=c_white)
    draw.text((115, 270), "Chức năng:", fill=c_dark_navy, font=get_font(22, bold=True))
    draw.text((115, 310), "Giao tiếp & truyền dữ liệu Bluetooth", fill=c_dark_navy, font=get_font(18, bold=True))

    img.save(path, quality=96)
    print("✓ Đã hoàn thiện 9.jpg")

if __name__ == "__main__":
    render_image_1()
    render_image_2()
    render_image_3()
    render_image_4()
    render_image_5()
    render_image_6()
    render_image_7()
    render_image_8()
    render_image_9()
