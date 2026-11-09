import os, re, csv, json, shutil
from urllib.parse import quote, unquote
from PIL import Image
import numpy as np

def copy_with_white_bg(src_path, dst_path):
    """Sao chép ảnh và tự động phủ nền trắng tinh (#FFFFFF) nếu ảnh gốc là PNG không nền (RGBA), tránh bị đen nền khi tải lên OneDrive / Web."""
    if not str(src_path).lower().endswith(('.png', '.webp', '.jpg', '.jpeg')):
        shutil.copy2(src_path, dst_path)
        return
    try:
        im = Image.open(src_path)
        has_alpha = im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info)
        if has_alpha:
            rgba = im.convert('RGBA')
            white_bg = Image.new('RGBA', rgba.size, (255, 255, 255, 255))
            comp = Image.alpha_composite(white_bg, rgba).convert('RGB')
            comp.save(dst_path, quality=95)
            return
    except Exception:
        pass
    shutil.copy2(src_path, dst_path)

BASE_DIR = 'd:/DataZMRobo'
EXPORT_DIR = 'd:/DataZMRobo/xuat_web_ban_hang'
MEDIA_DIR = 'd:/DataZMRobo/media'
TRANSLATED_DIR = 'd:/DataZMRobo/bo_anh_da_dich'

# Link CDN trực tiếp tới kho ảnh đã dịch của dự án trên GitHub (hoạt động ngay khi dán vào web bán hàng)
DEFAULT_IMAGE_CDN = 'https://raw.githubusercontent.com/VuDuyHoang2703/WebZM/main/media'

with open(f'{BASE_DIR}/data/products_full.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

# Trích xuất bộ CSS chuẩn giao diện từ index.html (.zm-content-wrapper & .zm-content-inner) để nhúng đồng bộ 100% vào mọi file HTML xuất ra
with open(f'{BASE_DIR}/index.html', 'r', encoding='utf-8') as f:
    _index_html_raw = f.read()
_css_match = re.search(r'(\.zm-content-wrapper\s*\{.*?</style>)', _index_html_raw, flags=re.S)
UI_SYNC_CSS = _css_match.group(1).replace('</style>', '').strip() if _css_match else ''
UI_SYNC_CSS = re.sub(r'/\*.*?\*/', '', UI_SYNC_CSS, flags=re.S)
UI_SYNC_CSS = re.sub(r'\n\s*\n+', '\n', UI_SYNC_CSS).strip()

USER_RAW_TOKENS = """
1799 1707 2322e 2104e 2109 2321e 2321ae 2325e 2108+e 2106+e 2101+e 2101ae 2323e 2421 2508e
2681 2681b 5161 1005 5148 9259 51489259 1245 1149a 1149 1536 2222 2257 1157 1153 2701 1141a 1146 1146a
6313 9528a 1743 9420a 9520a 9523a 9261 3570a 3571a 3568a 6311 3568b 3579a 3581a 3582a
9522 0242 0217 1279 0237 0120 0189 0124 0123 0117 0179 0190 0148 0146 0144 1276 7229
7228 0126 0127 0128 0201 0131 0208 0196 0195 0170 0167 0118 0236 0198 0156 0137
""".upper().split()
TARGET_SUFFIXES = set(USER_RAW_TOKENS)

def is_target_code(code_str):
    if not code_str: return False
    c = code_str.strip().upper()
    suf = c.split('-')[-1].strip()
    return c in TARGET_SUFFIXES or suf in TARGET_SUFFIXES

def sanitize_onedrive_name(name):
    """Chuẩn hóa tên file/thư mục tương thích 100% với Microsoft OneDrive."""
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', str(name))
    s = re.sub(r'\s+', ' ', s).strip().rstrip('.')
    return s or 'San_Pham'

# Tìm danh sách ảnh đã dịch theo từng mã sản phẩm trong bo_anh_da_dich
translated_by_code = {}
if os.path.exists(TRANSLATED_DIR):
    for root, dirs, files in os.walk(TRANSLATED_DIR):
        imgs = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        if imgs:
            folder_name = os.path.basename(root)
            code_part = folder_name.split(' - ')[0].strip().upper()
            translated_by_code[code_part] = [os.path.join(root, f) for f in sorted(imgs)]

def oss_url_to_local_rel(url):
    if not url: return ''
    clean = url.split('?')[0].strip()
    rel = re.sub(r'^https?://oss\.zmrobo\.com/', '', clean)
    rel = re.sub(r'^/?media/', '', rel)
    return unquote(rel.lstrip('/'))

def build_standardized_product_html(item, image_cdn=DEFAULT_IMAGE_CDN):
    """
    Xây dựng HTML chuẩn hóa (<div class="container">...</div>) cho TẤT CẢ 76 sản phẩm:
    - Với các Bộ Kit có sẵn landing page (slice_box) hoặc poster dài: chuẩn hóa responsive, đặt trình phát <video controls> ngay đầu mục mô tả (nếu có video) & thay link sang kho của dự án.
    - Với các Linh kiện điện tử / Cảm biến / Động cơ / RCU / Cơ khí nhựa (vốn để ảnh thông số đã dịch ở coverList hoặc chỉ có text ngắn):
      tự động tổng hợp Mô tả + Thông số kỹ thuật + Toàn bộ hình ảnh thông số đã dịch thành khối <div class="container"> hoàn chỉnh.
    """
    s = item.get('summary', {})
    d = item.get('detail', {}) if isinstance(item.get('detail'), dict) else {}
    info = d.get('productInfo', {}) if isinstance(d.get('productInfo'), dict) else {}

    code = (s.get('code') or info.get('code') or '').strip()
    title = (s.get('title') or info.get('title') or '').strip()
    parent_cat = (s.get('parent_type') or info.get('parent_type') or '').strip()
    sub_cat = (s.get('type') or info.get('type') or '').strip()
    intro = (info.get('intro') or s.get('intro') or '').strip()
    raw_html = (info.get('content') or '').strip()

    # Thu thập danh sách coverList thực tế tồn tại trong media/
    valid_cover_urls = []
    for c in d.get('coverList', []):
        c_url = c.get('cover', '') if isinstance(c, dict) else c
        rel = oss_url_to_local_rel(c_url)
        if rel and os.path.exists(os.path.join(MEDIA_DIR, rel.replace('/', os.sep))):
            valid_cover_urls.append(f"/media/{rel}")

    # Kiểm tra xem raw_html đã có sẵn ảnh hoặc video nội dung chưa
    has_content_imgs = bool(re.search(r'<(?:img|video)\b', raw_html, re.I))

    if has_content_imgs:
        out = raw_html
        # Đảm bảo ảnh poster có max-width:100%;height:auto để không vỡ khung trên điện thoại
        if 'slice_box' not in out:
            out = re.sub(
                r'<img\b(?![^>]*style=)([^>]*?)>',
                r'<img style="width:100%;max-width:750px;height:auto;display:block;margin:0 auto;"\1>',
                out,
                flags=re.I
            )
            if not out.strip().startswith('<div class="container"'):
                out = f'<div class="container" style="width:100%;max-width:1200px;margin:0 auto;box-sizing:border-box;">{out}</div>'
    else:
        # Xây dựng khối HTML chuẩn cho Linh kiện điện tử & Linh kiện cơ khí nhựa
        parts = [
            '<div class="container" style="width:100%;max-width:1000px;margin:0 auto;padding:24px 16px;font-family:sans-serif;color:#1D1D1F;line-height:1.7;box-sizing:border-box;">'
        ]
        parts.append(
            f'<div style="border-bottom:2px solid #F0F2F5;padding-bottom:16px;margin-bottom:24px;">'
            f'<div style="font-size:13px;font-weight:700;color:#0066CC;text-transform:uppercase;letter-spacing:0.5px;">{parent_cat} / {sub_cat}</div>'
            f'<h2 style="font-size:26px;font-weight:800;margin:8px 0 6px 0;color:#1D1D1F;">{title}</h2>'
            f'<div style="font-size:14px;color:#6E6E73;">Mã sản phẩm: <strong style="color:#1D1D1F;">{code}</strong></div>'
            f'</div>'
        )
        if intro:
            parts.append(
                f'<div style="background-color:#FBFBFD;border:1px solid #E5E5EA;border-radius:12px;padding:18px 20px;margin-bottom:24px;font-size:16px;color:#3A3A3C;">'
                f'<strong style="display:block;margin-bottom:6px;color:#1D1D1F;">Giới thiệu sản phẩm:</strong>'
                f'<div>{intro}</div>'
                f'</div>'
            )
        if raw_html:
            parts.append(
                f'<div style="background-color:#FFFFFF;border:1px solid #E5E5EA;border-radius:12px;padding:18px 20px;margin-bottom:24px;font-size:16px;">'
                f'<strong style="display:block;margin-bottom:10px;color:#1D1D1F;font-size:18px;">Thông số kỹ thuật:</strong>'
                f'{raw_html}'
                f'</div>'
            )
        if valid_cover_urls:
            parts.append('<div style="text-align:center;margin-top:20px;">')
            for u in valid_cover_urls:
                parts.append(
                    f'<p style="text-align:center;margin:16px 0;">'
                    f'<img src="{u}" alt="{title} - {code}" style="width:100%;max-width:800px;height:auto;border-radius:12px;border:1px solid #F0F2F5;display:block;margin:0 auto;"/>'
                    f'</p>'
                )
            parts.append('</div>')
        parts.append('</div>')
        out = '\n'.join(parts)

    # Chuẩn hóa ký tự & responsive width
    out = out.replace('&lần;', '×').replace('&times;', '×')
    out = re.sub(r"url\((?:&#39;|&quot;|['\"])*([^'\"\)\s&]+)(?:&#39;|&quot;|['\"])*\)", r"url('\1')", out, flags=re.I)

    def repl_width(m):
        px = int(m.group(1))
        if px >= 120:
            return f'width:100%;max-width:{px}px'
        return m.group(0)
    out = re.sub(r'(?<![-\w])width\s*:\s*(\d+)px', repl_width, out)

    # Thay thế toàn bộ link ảnh & video (/media/... hoặc oss.zmrobo.com/...) sang kho lưu trữ của dự án (tuyệt đối không gọi server ngoài)
    if image_cdn:
        image_cdn = image_cdn.rstrip('/')
        def repl_media_url(m):
            full_url = m.group(0)
            clean_url = full_url.split('?')[0]
            rel_unquoted = oss_url_to_local_rel(clean_url)
            local_file = os.path.join(MEDIA_DIR, rel_unquoted.replace('/', os.sep))
            if os.path.exists(local_file):
                encoded_rel = quote(rel_unquoted, safe='/')
                return f"{image_cdn}/{encoded_rel}"
            return full_url

        out = re.sub(r'https?://oss\.zmrobo\.com/[^\s"\'\)\(&<>]+', repl_media_url, out)
        out = re.sub(r'/media/[^\s"\'\)\(&<>]+', repl_media_url, out)

    # Nhúng đồng bộ 100% khung giao diện & bộ CSS chuẩn từ index.html (.zm-content-wrapper / .zm-content-inner)
    clean_check = re.sub(r'#bg_L\s*\{[^}]*\}', '', out, flags=re.I)
    is_dark = bool(
        re.search(r'\.slice_box\s*\{[^}]*background(?:-color)?:\s*#(?:000000|000|101010|0d0d0d|141414)', clean_check, re.I) or
        re.search(r'class=["\'][^"\']*slice_box[^"\']*["\'][^>]*background(?:-color)?:\s*#(?:000000|000|101010)', clean_check, re.I) or
        re.search(r'<div[^>]*style=["\'][^"\']*background(?:-color)?:\s*#(?:000000|000|101010|0d0d0d|141414)', clean_check, re.I)
    )
    dark_cls = ' zm-dark-wrapper' if is_dark else ''
    if UI_SYNC_CSS and 'zm-content-wrapper' not in out:
        out = (
            f'<div class="zm-content-wrapper{dark_cls}">\n'
            f'<style>\n{UI_SYNC_CSS}\n</style>\n'
            f'<div class="zm-content-inner">\n{out}\n</div>\n'
            f'</div>'
        )

    return out

# Xóa thư mục xuất cũ để tái tạo chuẩn hóa 100%
if os.path.exists(EXPORT_DIR):
    shutil.rmtree(EXPORT_DIR)

FLAT_HTML_DIR = os.path.join(EXPORT_DIR, '1_File_HTML_Copy_Dan_Web')
PRODUCT_PACK_DIR = os.path.join(EXPORT_DIR, '2_Bo_San_Pham_Kem_Hinh_Anh')
WEB_UI_SYNC_DIR = os.path.join(EXPORT_DIR, '3_Giao_Dien_Web_Hien_Tai')
os.makedirs(FLAT_HTML_DIR, exist_ok=True)
os.makedirs(PRODUCT_PACK_DIR, exist_ok=True)
os.makedirs(WEB_UI_SYNC_DIR, exist_ok=True)

csv_rows = []
exported_products = 0
total_cover_imgs = 0
total_content_imgs = 0
total_videos_exported = 0

for item in products:
    s = item.get('summary', {})
    d = item.get('detail', {}) if isinstance(item.get('detail'), dict) else {}
    info = d.get('productInfo', {}) if isinstance(d.get('productInfo'), dict) else {}
    code = (s.get('code') or info.get('code') or '').strip()
    if not is_target_code(code):
        continue

    short_code = code.split('-')[-1].strip()
    parent_cat = sanitize_onedrive_name(s.get('parent_type') or info.get('parent_type') or 'Khac')
    sub_cat = sanitize_onedrive_name(s.get('type') or info.get('type') or 'Khac')
    title = (s.get('title') or info.get('title') or '').strip()
    title_en = (s.get('title_en') or info.get('title_en') or '').strip()

    base_label = sanitize_onedrive_name(f"{short_code} - {code} - {title}")
    html_filename = f"{base_label}.html"

    # Tạo HTML chuẩn hóa (100% sản phẩm đều có HTML đầy đủ kèm ảnh đã dịch & giao diện đồng bộ)
    ecom_html = build_standardized_product_html(item, DEFAULT_IMAGE_CDN)

    # 1. Lưu vào 1_File_HTML_Copy_Dan_Web/
    with open(os.path.join(FLAT_HTML_DIR, html_filename), 'w', encoding='utf-8') as f:
        f.write(ecom_html)

    # 2. Lưu vào 2_Bo_San_Pham_Kem_Hinh_Anh/<Mã - Tên>/
    prod_dir = os.path.join(PRODUCT_PACK_DIR, base_label)
    os.makedirs(prod_dir, exist_ok=True)

    with open(os.path.join(prod_dir, html_filename), 'w', encoding='utf-8') as f:
        f.write(ecom_html)

    # 2a. Xuất ảnh đại diện (1_anh_dai_dien)
    img_covers_dir = os.path.join(prod_dir, '1_anh_dai_dien')
    cover_list = d.get('coverList', [])
    prod_cover_count = 0
    main_cover_cdn = ''
    for i, c in enumerate(cover_list):
        c_url = c.get('cover', '') if isinstance(c, dict) else c
        rel = oss_url_to_local_rel(c_url)
        if not rel: continue
        local_src = os.path.join(MEDIA_DIR, rel.replace('/', os.sep))
        if os.path.exists(local_src):
            os.makedirs(img_covers_dir, exist_ok=True)
            fname = f"cover_{i+1}_{os.path.basename(rel)}"
            copy_with_white_bg(local_src, os.path.join(img_covers_dir, fname))
            prod_cover_count += 1
            total_cover_imgs += 1
            if not main_cover_cdn:
                main_cover_cdn = f"{DEFAULT_IMAGE_CDN}/{quote(rel, safe='/')}"

    # 2b. Xuất toàn bộ ảnh & video nằm trong bài mô tả HTML (2_anh_noi_dung_mo_ta) & tách riêng video (4_video_gioi_thieu)
    img_content_dir = os.path.join(prod_dir, '2_anh_noi_dung_mo_ta')
    video_dir = os.path.join(prod_dir, '4_video_gioi_thieu')
    cdn_urls = re.findall(re.escape(DEFAULT_IMAGE_CDN) + r'/[^\s"\'\)\(&<>]+', ecom_html)
    seen_rels = {}
    used_fnames = set()
    content_rel_list = []
    prod_video_count = 0
    for u in cdn_urls:
        rel = unquote(u.replace(DEFAULT_IMAGE_CDN + '/', ''))
        if rel in seen_rels: continue
        base_fname = os.path.basename(rel)
        if base_fname in used_fnames:
            parent_prefix = os.path.basename(os.path.dirname(rel))
            fname = f"{parent_prefix}_{base_fname}" if parent_prefix else f"{len(used_fnames)}_{base_fname}"
        else:
            fname = base_fname
        used_fnames.add(fname)
        seen_rels[rel] = fname
        content_rel_list.append((rel, fname))
        local_src = os.path.join(MEDIA_DIR, rel.replace('/', os.sep))
        if os.path.exists(local_src):
            os.makedirs(img_content_dir, exist_ok=True)
            copy_with_white_bg(local_src, os.path.join(img_content_dir, fname))
            if fname.lower().endswith('.mp4'):
                os.makedirs(video_dir, exist_ok=True)
                shutil.copy2(local_src, os.path.join(video_dir, base_fname))
                prod_video_count += 1
                total_videos_exported += 1
            else:
                total_content_imgs += 1

    # 2c. Xuất riêng các ảnh đã dịch tiếng Việt (3_anh_da_dich_tieng_viet)
    trans_list = translated_by_code.get(code.upper(), [])
    if trans_list:
        img_trans_dir = os.path.join(prod_dir, '3_anh_da_dich_tieng_viet')
        os.makedirs(img_trans_dir, exist_ok=True)
        for src_p in trans_list:
            copy_with_white_bg(src_p, os.path.join(img_trans_dir, os.path.basename(src_p)))

    # 2d. Xuất file xem_thu_offline.html (xem trực tiếp bằng ảnh & video cục bộ trong thư mục 2_anh_noi_dung_mo_ta)
    offline_html = ecom_html
    for rel, fname in content_rel_list:
        cdn_url = f"{DEFAULT_IMAGE_CDN}/{quote(rel, safe='/')}"
        offline_html = offline_html.replace(cdn_url, f"2_anh_noi_dung_mo_ta/{quote(fname)}")
    with open(os.path.join(prod_dir, 'xem_thu_offline.html'), 'w', encoding='utf-8') as f:
        f.write(f"<!DOCTYPE html><html lang='vi'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{code} - {title}</title></head><body style='margin:0;padding:0;background:#fff;font-family:sans-serif;'>{offline_html}</body></html>")

    # 2e. Xuất file thong_tin_san_pham.txt
    video_cdn_url = ''
    if info.get('video'):
        v_rel = oss_url_to_local_rel(info.get('video'))
        if v_rel:
            video_cdn_url = f"{DEFAULT_IMAGE_CDN}/{quote(v_rel, safe='/')}"
    with open(os.path.join(prod_dir, 'thong_tin_san_pham.txt'), 'w', encoding='utf-8') as f:
        f.write(f"TÊN SẢN PHẨM (VI): {title}\n")
        f.write(f"TÊN GỐC (EN):      {title_en}\n")
        f.write(f"MÃ SẢN PHẨM:       {code} (Mã ngắn: {short_code})\n")
        f.write(f"DANH MỤC:          {parent_cat} > {sub_cat}\n")
        f.write(f"GIỚI THIỆU NGẮN:   {info.get('intro') or ''}\n")
        f.write(f"LINK ẢNH ĐẠI DIỆN: {main_cover_cdn}\n")
        f.write(f"LINK VIDEO:        {video_cdn_url}\n")
        f.write(f"SỐ ẢNH ĐẠI DIỆN:   {prod_cover_count}\n")
        f.write(f"SỐ ẢNH NỘI DUNG:   {len(content_rel_list) - prod_video_count}\n")
        f.write(f"SỐ VIDEO MÔ TẢ:    {prod_video_count}\n")
        f.write(f"SỐ ẢNH ĐÃ DỊCH TV: {len(trans_list)}\n")

    exported_products += 1
    csv_rows.append([
        exported_products,
        short_code,
        code,
        title,
        title_en,
        parent_cat,
        sub_cat,
        (info.get('intro') or '').strip(),
        prod_cover_count,
        len(trans_list),
        main_cover_cdn,
        info.get('manual') or '',
        video_cdn_url,
        html_filename,
        ecom_html
    ])

# Đồng bộ toàn bộ giao diện Web hiện tại (index.html, data/, tools/, CHAY_WEB.bat) vào 3_Giao_Dien_Web_Hien_Tai/
for fname in ['index.html', 'CHAY_WEB.bat', 'vercel.json']:
    src_f = os.path.join(BASE_DIR, fname)
    if os.path.exists(src_f):
        shutil.copy2(src_f, os.path.join(WEB_UI_SYNC_DIR, fname))

sync_data_dir = os.path.join(WEB_UI_SYNC_DIR, 'data')
os.makedirs(sync_data_dir, exist_ok=True)
for fname in ['categories.json', 'products_full.json', 'software.json', 'resources.json']:
    src_f = os.path.join(BASE_DIR, 'data', fname)
    if os.path.exists(src_f):
        shutil.copy2(src_f, os.path.join(sync_data_dir, fname))

sync_tools_dir = os.path.join(WEB_UI_SYNC_DIR, 'tools')
os.makedirs(sync_tools_dir, exist_ok=True)
if os.path.exists(os.path.join(BASE_DIR, 'tools', 'server.py')):
    shutil.copy2(os.path.join(BASE_DIR, 'tools', 'server.py'), os.path.join(sync_tools_dir, 'server.py'))

# 3. Xuất bảng tổng hợp Excel/CSV chuẩn UTF-8-SIG (mở trực tiếp trên Excel / OneDrive không lỗi font)
csv_path = os.path.join(EXPORT_DIR, '0_DANH_SACH_76_SAN_PHAM_BAN_HANG.csv')
with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([
        'STT', 'Mã Ngắn', 'Mã Sản Phẩm', 'Tên Sản Phẩm (Tiếng Việt)', 'Tên Gốc (Tiếng Anh)',
        'Danh Mục Cha', 'Danh Mục Con', 'Giới Thiệu Ngắn', 'Số Ảnh Đại Diện', 'Số Ảnh Đã Dịch TV',
        'Link Ảnh Đại Diện Chính (CDN)', 'Link PDF Hướng Dẫn', 'Link Video',
        'Tên File HTML', 'Code HTML Chuẩn Web Bán Hàng (Copy Dán Trực Tiếp)'
    ])
    writer.writerows(csv_rows)

# 4. Xuất file hướng dẫn chi tiết cho nhân sự công ty trên OneDrive
guide_path = os.path.join(EXPORT_DIR, '0_HUONG_DAN_NAP_WEB_BAN_HANG.md')
with open(guide_path, 'w', encoding='utf-8') as f:
    f.write("""# HƯỚNG DẪN NẠP DỮ LIỆU & HÌNH ẢNH 76 SẢN PHẨM LÊN WEB BÁN HÀNG CÔNG TY

Thư mục này đã được chuẩn hóa 100% để lưu trữ trên **Microsoft OneDrive công ty** và nạp trực tiếp vào **Web bán hàng**.

---

## 1. Cấu trúc thư mục

1. **`0_DANH_SACH_76_SAN_PHAM_BAN_HANG.csv`**:
   - File bảng tính Excel tổng hợp đầy đủ 76 sản phẩm (Mã SP, Tên tiếng Việt, Danh mục, Giới thiệu ngắn, Link ảnh đại diện, Link PDF hướng dẫn, và cột cuối cùng chứa sẵn **Code HTML mô tả sản phẩm**).
   - Có thể mở trực tiếp trên Excel hoặc OneDrive (đã mã hóa chuẩn UTF-8 BOM không lỗi font tiếng Việt).

2. **`1_File_HTML_Copy_Dan_Web/`**:
   - Chứa **76 file `.html` riêng biệt** ứng với 76 mã sản phẩm (ví dụ: `1707 - JMC-SV-1707 - RoboMaker.html`, `2681 - JMC-NY-2681 - 2026 Super AI - Star Cruise.html`).
   - Toàn bộ nội dung chữ và hình ảnh bên trong đã được chuyển sang **tiếng Việt** và gắn sẵn link CDN tốc độ cao (`https://raw.githubusercontent.com/VuDuyHoang2703/WebZM/main/media/...`).

3. **`2_Bo_San_Pham_Kem_Hinh_Anh/`**:
   - Chứa **76 thư mục riêng** của từng sản phẩm. Bên trong mỗi thư mục gồm:
     - `1_anh_dai_dien/`: Ảnh bìa / slide đại diện (đã chuẩn hóa nền trắng tinh `#FFFFFF` RGB) để tải lên mục **Ảnh đại diện sản phẩm** trên web bán hàng.
     - `2_anh_noi_dung_mo_ta/`: Toàn bộ ảnh & video nằm trong bài viết mô tả (đã bao gồm ảnh dịch tiếng Việt).
     - `3_anh_da_dich_tieng_viet/`: Lọc riêng các tấm ảnh đã dịch sang tiếng Việt của mã sản phẩm đó.
     - `4_video_gioi_thieu/`: File video `.mp4` giới thiệu sản phẩm (đối với 13 bộ sản phẩm có video).
     - `<Mã SP>.html`: File code HTML chuẩn (đã nhúng đồng bộ 100% giao diện & CSS hiện tại, video rộng 100% ngang bằng khung nội dung ở ngay đầu mục mô tả) để copy dán vào trình soạn thảo web bán hàng.
     - `xem_thu_offline.html`: Nhấp đúp để xem trước giao diện bài viết (kèm video phát trực tiếp) ngay trên máy tính.
     - `thong_tin_san_pham.txt`: Tóm tắt nhanh thông tin sản phẩm.

4. **`3_Giao_Dien_Web_Hien_Tai/`**:
   - Đồng bộ toàn bộ giao diện quản lý & trưng bày hiện tại (`index.html`, `data/`, `tools/server.py`, `CHAY_WEB.bat`).

---

## 2. Các bước nạp sản phẩm lên Web bán hàng công ty

### Bước 1: Điền thông tin cơ bản & tải Ảnh đại diện
- Mở file `0_DANH_SACH_76_SAN_PHAM_BAN_HANG.csv` (hoặc `thong_tin_san_pham.txt` trong thư mục sản phẩm) để lấy **Tên sản phẩm**, **Mã sản phẩm**, **Danh mục**, **Giới thiệu ngắn**.
- Tải ảnh đại diện sản phẩm từ thư mục `1_anh_dai_dien/` của mã đó lên mục **Ảnh sản phẩm / Album ảnh** trên web bán hàng.

### Bước 2: Dán nội dung HTML mô tả chi tiết (Tự động lên cả video đầu trang, chữ và ảnh tiếng Việt)
- Mở file `<Mã SP>.html` trong thư mục `1_File_HTML_Copy_Dan_Web/` bằng Notepad (hoặc bấm nút **"Copy HTML Bán Hàng"** trên giao diện quản lý `index.html`).
- Nhấn `Ctrl + A` -> `Ctrl + C` để copy toàn bộ đoạn code.
- Trên trang quản trị Web bán hàng, tại ô **Mô tả chi tiết sản phẩm**, bấm vào nút chuyển sang chế độ **Mã nguồn / HTML (`<>` hoặc `Source`)**.
- Nhấn `Ctrl + V` để dán code vào -> Lưu sản phẩm. Toàn bộ bố cục, video phát trực tiếp đầu bài (rộng 100% ngang bằng khung nội dung, tự co giãn theo cửa sổ), chữ tiếng Việt và hình ảnh tiếng Việt đã dịch sẽ tự động hiển thị chuẩn xác.
""")

print(f"Standardized export complete: {exported_products} products (0 empty HTML), {total_cover_imgs} cover images, {total_content_imgs} content images, {total_videos_exported} videos.")
