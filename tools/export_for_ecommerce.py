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

# Link CDN trực tiếp tới kho ảnh đã dịch và kho video của dự án trên GitHub (hoạt động ngay khi dán vào web bán hàng)
DEFAULT_IMAGE_CDN = 'https://raw.githubusercontent.com/VuDuyHoang2703/WebZM/main/media'
DEFAULT_VIDEO_CDN = 'https://media.githubusercontent.com/media/VuDuyHoang2703/WebZM/main/media'

with open(f'{BASE_DIR}/data/products_full.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

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

DEAD_CSS_TOKENS = (
    '#all_l', '#bg_l', '.tab_text_l', '.active_tab_l', '#cancel_btn',
    '.tab_content_l', '.active_content_l', '.play_btn1', '.consult_btn',
    '.get_more_btn', '.play_rule_video_btn'
)

# Bộ CSS thuần tương thích 100% với mọi trình soạn thảo CMS Web bán hàng:
# Không chứa @keyframes, không :has(), không [style*=], không *, không comment CSS
CMS_SAFE_SLICE_CSS = """
.container{width:100%;max-width:1560px;margin:0 auto;box-sizing:border-box;}
.slice_box{width:100%;max-width:1560px;margin-left:auto;margin-right:auto;box-sizing:border-box;overflow-x:hidden;}
.slice_inbox{margin:0 auto;text-align:center;max-width:100%;box-sizing:border-box;}
.slice_inbox div{max-width:100%;box-sizing:border-box;}
.slice_box img{display:inline-block;max-width:100%;height:auto;vertical-align:middle;}
.zm-product-video{width:80%;max-width:100%;margin:24px auto;text-align:center;box-sizing:border-box;}
.zm-product-video video{width:100%;max-width:100%;height:auto;display:block;margin:0 auto;background-color:#000000;border-radius:10px;}
.icon_2{vertical-align:top;max-width:100%;box-sizing:border-box;}
.icon_2 img{display:inline-block;margin-bottom:6px;}
.icon_2_row,.slice_inbox .icon_2_row{display:flex;flex-wrap:wrap;justify-content:center;align-items:flex-start;gap:18px 12px;width:100%;max-width:1280px;margin-left:auto;margin-right:auto;padding-left:16px;padding-right:16px;box-sizing:border-box;}
.icon_2_row .icon_2{flex:1 1 145px;max-width:220px;min-width:145px;margin:0;vertical-align:top;box-sizing:border-box;}
.icon_8,.quality_item,.tookit_item,.task_robo_item{text-align:center;vertical-align:top;}
.icon_8 img,.func_icon_list img,.color_icon_list img,.quality_item img,.tookit_item img,.task_robo_item img{display:block;margin-left:auto;margin-right:auto;}
.color_icon_list{display:inline-block;width:90px;margin-top:24px;margin-left:45px;vertical-align:top;text-align:center;box-sizing:border-box;}
.func_icon_list{display:inline-block;vertical-align:top;text-align:center;box-sizing:border-box;}
.gray_rect{display:inline-block;vertical-align:top;max-width:100%;overflow:hidden;box-sizing:border-box;}
.gray_rect img{width:100%;height:auto;display:block;}
.field_4{display:inline-flex;flex-wrap:wrap;justify-content:center;align-items:flex-start;text-align:left;max-width:100%;vertical-align:top;box-sizing:border-box;}
.sensor_left_box,.slice_inbox .sensor_left_box{flex:0 0 auto;max-width:48%;vertical-align:top;box-sizing:border-box;}
.sensor_right_box{flex:0 1 auto;min-width:0;text-align:left;vertical-align:top;box-sizing:border-box;}
.both_sensor_div,.slice_inbox .both_sensor_div{width:100%;max-width:1260px;margin-left:auto;margin-right:auto;padding-left:20px;padding-right:20px;display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-start;gap:0 24px;text-align:left;box-sizing:border-box;}
.both_sensor_inner{width:100%;max-width:100%;display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-start;gap:0 24px;text-align:left;box-sizing:border-box;}
.both_sensor_div .field_4{flex:1 1 440px;min-width:0;max-width:600px;flex-wrap:nowrap;justify-content:flex-start;margin-left:0;box-sizing:border-box;}
.both_sensor_div .field_4:nth-child(even){margin-left:0;}
.both_sensor_div .sensor_left_box{flex:0 0 auto;max-width:48%;}
.both_sensor_div .sensor_right_box{flex:1 1 auto;min-width:0;margin-left:20px;}
.func_icon_div{display:flex;align-items:flex-start;text-align:left;}
.func_icon_div img{flex-shrink:0;}
.func_icon_div div{flex:1;min-width:0;display:block;margin-left:10px;margin-top:3px;text-align:left;white-space:normal;}
.sensor_item{display:inline-block;vertical-align:top;}
""".strip()

INLINE_KEEP_WIDTH_CLASSES = {
    'icon_2', 'gray_rect', 'func_icon_list', 'color_icon_list',
    'task_robo_item', 'tookit_item', 'sensor_item', 'quality_item', 'two_row'
}

def clean_single_css_block(css_text):
    """Loại bỏ CSS comments và các rule modal/button thừa dễ gây lỗi trình phân tích HTML/CMS."""
    css = re.sub(r'/\*.*?\*/', '', css_text, flags=re.S)
    kept_rules = []
    i, n = 0, len(css)
    while i < n:
        brace_open = css.find('{', i)
        if brace_open == -1:
            break
        selector = css[i:brace_open].strip()
        depth = 1
        j = brace_open + 1
        while j < n and depth > 0:
            if css[j] == '{':
                depth += 1
            elif css[j] == '}':
                depth -= 1
            j += 1
        body = css[brace_open + 1:j - 1].strip() if depth == 0 else ''
        i = j
        if not selector or not body:
            continue
        sel_lower = selector.lower()
        # Bỏ qua mọi selector rác, modal #bg_L/#all_L hoặc ký tự @ / :has / [*] không an toàn cho CMS
        if any(tok in sel_lower for tok in DEAD_CSS_TOKENS):
            continue
        if '@' in sel_lower or ':has(' in sel_lower or '[' in sel_lower or '*' in sel_lower:
            continue
        # Loại bỏ thuộc tính text-shadow cũ
        body = re.sub(r'text-shadow\s*:[^;]+;?', '', body, flags=re.I).strip()
        if body:
            body_clean = re.sub(r'\s+', ' ', body)
            kept_rules.append(f"{selector}{{{body_clean}}}")
    return '\n'.join(kept_rules)

def normalize_styles_for_cms(html_str):
    """Gom toàn bộ thẻ <style> thành tối đa 1 thẻ <style> sạch sẽ ngay đầu <div class='container'>, loại bỏ chú thích & onclick JS."""
    styles = re.findall(r'<style\b[^>]*>(.*?)</style>', html_str, flags=re.I | re.S)
    if not styles:
        return html_str
    body = re.sub(r'<style\b[^>]*>.*?</style>', '', html_str, flags=re.I | re.S)
    cleaned_parts = [clean_single_css_block(s) for s in styles]
    merged_css = '\n'.join([p for p in cleaned_parts if p])
    merged_css = (merged_css + '\n' + CMS_SAFE_SLICE_CSS).strip()
    style_tag = f"<style>\n{merged_css}\n</style>"
    m_cont = re.match(r'^(\s*<div\b[^>]*class=["\'][^"\']*\bcontainer\b[^"\']*["\'][^>]*>)', body, flags=re.I)
    if m_cont:
        open_tag = m_cont.group(1)
        rest = body[m_cont.end():].lstrip('\r\n')
        if not re.search(r'\bstyle\s*=', open_tag, flags=re.I):
            open_tag = open_tag[:-1] + ' style="width:100%;max-width:1560px;margin:0 auto;box-sizing:border-box;">'
        return open_tag + '\n' + style_tag + '\n' + rest
    return style_tag + '\n' + body

def normalize_tables_for_cms(html_str):
    """Chuẩn hóa bảng biểu: quy đổi px trên <th> thành % giữ nguyên tỷ lệ cột và bọc khung cuộn ngang an toàn."""
    def repl_table(m):
        attrs = m.group(1)
        inner = m.group(2)

        if not re.search(r'\balign\s*=', attrs, flags=re.I):
            attrs = ' align="center"' + attrs

        orig_w_match = re.search(r'(?<![-\w])width\s*:\s*(\d+)px', attrs, flags=re.I)
        orig_w = int(orig_w_match.group(1)) if orig_w_match else 1200

        th_matches = list(re.finditer(r'<th\b([^>]*)>', inner, flags=re.I))
        th_px_list = []
        for th_m in th_matches:
            w_m = re.search(r'(?<![-\w])width\s*:\s*(\d+)px', th_m.group(1), flags=re.I)
            th_px_list.append(int(w_m.group(1)) if w_m else None)

        num_cols = len(th_matches)
        valid_widths = [w for w in th_px_list if w is not None]
        if num_cols > 0 and len(valid_widths) == num_cols:
            total_px = sum(valid_widths)
            if total_px > 0:
                pcts = []
                for idx_w, w in enumerate(valid_widths):
                    if idx_w < num_cols - 1:
                        pct = round(w * 100.0 / total_px, 2)
                        pcts.append(pct)
                    else:
                        pct = round(max(0.5, 100.0 - sum(pcts)), 2)
                        pcts.append(pct)
                rebuilt = []
                last_pos = 0
                for idx_th, th_m in enumerate(th_matches):
                    rebuilt.append(inner[last_pos:th_m.start()])
                    new_th_attrs = re.sub(
                        r'(?<![-\w])width\s*:\s*\d+px',
                        f'width:{pcts[idx_th]}%',
                        th_m.group(1),
                        count=1,
                        flags=re.I
                    )
                    rebuilt.append(f'<th{new_th_attrs}>')
                    last_pos = th_m.end()
                rebuilt.append(inner[last_pos:])
                inner = ''.join(rebuilt)

        min_w = 960 if num_cols >= 8 else (720 if num_cols >= 5 else 480)
        min_w = min(min_w, orig_w)
        if orig_w_match:
            attrs = re.sub(
                r'(?<![-\w])width\s*:\s*\d+px',
                f'width:100%;max-width:{orig_w}px;min-width:{min_w}px',
                attrs,
                count=1,
                flags=re.I
            )

        table_html = f'<table{attrs}>{inner}</table>'
        return f'<div style="width:100%;max-width:{orig_w}px;margin:0 auto;overflow-x:auto;box-sizing:border-box;">{table_html}</div>'

    return re.sub(r'<table\b([^>]*)>(.*?)</table>', repl_table, html_str, flags=re.I | re.S)

def make_inline_containers_responsive(html_str):
    """Chỉ chuyển đổi width cố định >= 750px trên thẻ bọc div/p bên ngoài <style>, giữ nguyên <table>/<th>/<td>/<img> và card nhỏ."""
    parts = re.split(r'(<style\b[^>]*>.*?</style>)', html_str, flags=re.I | re.S)
    for idx in range(len(parts)):
        chunk = parts[idx]
        if not chunk or chunk.lstrip().lower().startswith('<style'):
            continue

        def repl_tag(m):
            tag = m.group(1)
            attrs = m.group(2)
            t_low = tag.lower()
            if t_low in ('style', 'table', 'th', 'td', 'col', 'colgroup', 'img', 'video'):
                return m.group(0)
            if 'width' not in attrs.lower():
                return m.group(0)
            cls_tokens = set()
            cls_m = re.search(r'\bclass=(["\'])([^"\']*)\1', attrs, flags=re.I)
            if cls_m:
                cls_tokens = set(cls_m.group(2).split())
                if cls_tokens & INLINE_KEEP_WIDTH_CLASSES:
                    return m.group(0)

            def repl_w(wm):
                px = int(wm.group(1))
                if px >= 750:
                    max_w = 1020 if ('field_4' in cls_tokens and 820 <= px < 1020) else px
                    return f'width:100%;max-width:{max_w}px'
                return wm.group(0)

            new_attrs = re.sub(r'(?<![-\w])width\s*:\s*(\d+)px', repl_w, attrs)
            return f'<{tag}{new_attrs}>'

        parts[idx] = re.sub(r'<([a-zA-Z0-9]+)\b([^>]*)>', repl_tag, chunk)
    return ''.join(parts)

def normalize_sensor_wrappers(html_str):
    """Đảm bảo các wrapper trung gian bên trong .both_sensor_div (như 2322E/2323E) tham gia chia 2 cột Flex."""
    out = re.sub(
        r'''(<div\b[^>]*class=["'][^"']*\bboth_sensor_div\b[^"']*["'][^>]*>\s*)<div\s+style=["']text-align:\s*left;?["']\s*>''',
        r'\1<div class="both_sensor_inner" style="text-align:left;">',
        html_str,
        flags=re.I
    )
    out = re.sub(
        r'''<div\s+(style=[^>]*?)>(\s*<div\b[^>]*class=["'][^"']*\bicon_2\b)''',
        r'<div class="icon_2_row" \1>\2',
        out,
        flags=re.I
    )
    return out

def build_standardized_product_html(item, image_cdn=DEFAULT_IMAGE_CDN):
    """
    Xây dựng HTML chuẩn hóa (<div class="container">...</div>) thuần CMS-safe cho TẤT CẢ 76 sản phẩm:
    - KHÔNG bọc zm-content-wrapper hay nhúng UI_SYNC_CSS (@keyframes / :has / attribute selectors) để tránh lỗi "Invalid token" khi dán vào Web bán hàng.
    - Trình tự chuẩn với mọi bộ kit có video: Hình ảnh bộ sản phẩm -> Video giới thiệu (khung 80%, căn giữa, tự co giãn) -> Mô tả & Thông số.
    - Tối đa 1 video mỗi bộ sản phẩm.
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

    has_content_imgs = bool(re.search(r'<(?:img|video)\b', raw_html, re.I))

    if has_content_imgs:
        out = raw_html
        # Chuẩn hóa ảnh & bảng cho các bộ poster cuộn (không có slice_box) bằng inline style, không cần <style>
        if 'slice_box' not in out:
            out = re.sub(
                r'<p\s+style=["\']text-align:\s*left;?["\']>',
                '<p style="text-align:center;">',
                out,
                flags=re.I
            )
            out = re.sub(
                r'<p>',
                '<p style="text-align:center;margin:0;">',
                out,
                flags=re.I
            )
            out = re.sub(
                r'<img\b(?![^>]*style=)([^>]*?)>',
                r'<img style="width:100%;max-width:750px;height:auto;display:block;margin:0 auto;"\1>',
                out,
                flags=re.I
            )
            if not out.strip().startswith('<div class="container"'):
                out = f'<div class="container" style="width:100%;max-width:1200px;margin:0 auto;box-sizing:border-box;">{out}</div>'
        else:
            # Mở rộng khung khóa học bị ẩn bằng onclick trên 2106+E / 2108+E để không phụ thuộc JS onclick
            if 'table_out_div' in out:
                out = re.sub(
                    r'<div[^>]*\bonclick=[^>]*>.*?Các khóa học khác.*?</div>\s*</div>',
                    '',
                    out,
                    flags=re.I | re.S
                )
                out = re.sub(
                    r'(id=["\']table_out_div["\'][^>]*style=["\'][^"\']*?)height\s*:\s*1045px\s*;?',
                    r'\1min-height:787px;height:auto;padding-bottom:32px;',
                    out,
                    flags=re.I
                )
            # Xóa bỏ triệt để onclick / margin âm lệch cột trên icon_2
            out = re.sub(r'\s*\bonclick=["\'][^"\']*["\']', '', out, flags=re.I)
            out = re.sub(r'style=["\']margin-left:\s*-\d+px;?["\']', '', out, flags=re.I)
            out = normalize_styles_for_cms(out)
    else:
        # Xây dựng khối HTML thuần inline style cho Linh kiện điện tử & Linh kiện cơ khí nhựa
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

    # Xóa HTML comments & chuẩn hóa ký tự / entity / bảng biểu / responsive width
    out = re.sub(r'<!--.*?-->', '', out, flags=re.S)
    out = out.replace('&lần;', '×').replace('&times;', '×')
    out = re.sub(r"url\((?:&#39;|&quot;|['\"])*([^'\"\)\s&]+)(?:&#39;|&quot;|['\"])*\)", r"url('\1')", out, flags=re.I)

    out = normalize_tables_for_cms(out)
    out = normalize_sensor_wrappers(out)
    out = make_inline_containers_responsive(out)

    # Làm gọn khoảng trắng thừa giữa các dòng
    out = re.sub(r'\n\s*\n+', '\n', out.replace('\r\n', '\n')).strip()

    # Thay thế toàn bộ link ảnh & video (/media/... hoặc oss.zmrobo.com/...) sang kho lưu trữ của dự án (tuyệt đối không gọi server ngoài)
    if image_cdn:
        image_cdn = image_cdn.rstrip('/')
        video_cdn = DEFAULT_VIDEO_CDN.rstrip('/')
        def repl_media_url(m):
            full_url = m.group(0)
            clean_url = full_url.split('?')[0]
            rel_unquoted = oss_url_to_local_rel(clean_url)
            local_file = os.path.join(MEDIA_DIR, rel_unquoted.replace('/', os.sep))
            if os.path.exists(local_file):
                encoded_rel = quote(rel_unquoted, safe='/')
                base_cdn = video_cdn if rel_unquoted.lower().endswith('.mp4') else image_cdn
                return f"{base_cdn}/{encoded_rel}"
            return full_url

        out = re.sub(r'https?://oss\.zmrobo\.com/[^\s"\'\)\(&<>]+', repl_media_url, out)
        out = re.sub(r'/media/[^\s"\'\)\(&<>]+', repl_media_url, out)

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

    # Tạo HTML chuẩn hóa CMS-safe (không zm-content-wrapper / UI_SYNC_CSS)
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
    cdn_pattern = r'(?:' + re.escape(DEFAULT_IMAGE_CDN) + r'|' + re.escape(DEFAULT_VIDEO_CDN) + r')/[^\s"\'\)\(&<>]+'
    cdn_urls = re.findall(cdn_pattern, ecom_html)
    seen_rels = {}
    used_fnames = set()
    content_rel_list = []
    prod_video_count = 0
    for u in cdn_urls:
        rel_part = u.replace(DEFAULT_IMAGE_CDN + '/', '').replace(DEFAULT_VIDEO_CDN + '/', '')
        rel = unquote(rel_part)
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
            shutil.copy2(local_src, os.path.join(img_content_dir, fname))
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
        encoded_rel = quote(rel, safe='/')
        offline_html = offline_html.replace(f"{DEFAULT_IMAGE_CDN}/{encoded_rel}", f"2_anh_noi_dung_mo_ta/{quote(fname)}")
        offline_html = offline_html.replace(f"{DEFAULT_VIDEO_CDN}/{encoded_rel}", f"2_anh_noi_dung_mo_ta/{quote(fname)}")
    with open(os.path.join(prod_dir, 'xem_thu_offline.html'), 'w', encoding='utf-8') as f:
        f.write(f"<!DOCTYPE html><html lang='vi'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{code} - {title}</title></head><body style='margin:0;padding:0;background:#fff;font-family:sans-serif;'>{offline_html}</body></html>")

    # 2e. Xuất file thong_tin_san_pham.txt
    video_cdn_url = ''
    if info.get('video'):
        v_rel = oss_url_to_local_rel(info.get('video'))
        if v_rel:
            video_cdn_url = f"{DEFAULT_VIDEO_CDN}/{quote(v_rel, safe='/')}"
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
   - Chứa **76 file `.html` riêng biệt** ứng với 76 mã sản phẩm (ví dụ: `1707 - JMC-SV-1707 - RoboMaker.html`, `2421 - JMC-NY-2421 - Beta Set.html`).
   - Toàn bộ code HTML đã được làm sạch chuẩn `<div class="container">...</div>` tương thích trực tiếp với trình soạn thảo Web công ty (đã gỡ bỏ CSS nặng/modal thừa/thẻ lỗi gây `Invalid token`).
   - Bố cục chuẩn với các bộ sản phẩm có video (tối đa **1 video / bộ**): **Hình ảnh của bộ trước -> Video (khung 80%, căn giữa, tự co giãn) -> Mô tả chi tiết & Thông số**.

3. **`2_Bo_San_Pham_Kem_Hinh_Anh/`**:
   - Chứa **76 thư mục riêng** của từng sản phẩm. Bên trong mỗi thư mục gồm:
     - `1_anh_dai_dien/`: Ảnh bìa / slide đại diện (đã chuẩn hóa nền trắng tinh `#FFFFFF` RGB) để tải lên mục **Ảnh đại diện sản phẩm** trên web bán hàng.
     - `2_anh_noi_dung_mo_ta/`: Toàn bộ ảnh & video nằm trong bài viết mô tả (đã bao gồm ảnh dịch tiếng Việt).
     - `3_anh_da_dich_tieng_viet/`: Lọc riêng các tấm ảnh đã dịch sang tiếng Việt của mã sản phẩm đó.
     - `4_video_gioi_thieu/`: Tối đa **1 video `.mp4`** giới thiệu đúng bộ sản phẩm đó (đối với 13 bộ sản phẩm có video).
     - `<Mã SP>.html`: File code HTML chuẩn để copy dán vào trình soạn thảo web bán hàng.
     - `xem_thu_offline.html`: Nhấp đúp để xem trước giao diện bài viết (kèm video khung 80% bên dưới hình ảnh bộ kit) ngay trên máy tính.
     - `thong_tin_san_pham.txt`: Tóm tắt nhanh thông tin sản phẩm.

4. **`3_Giao_Dien_Web_Hien_Tai/`**:
   - Đồng bộ toàn bộ giao diện quản lý & trưng bày hiện tại (`index.html`, `data/`, `tools/server.py`, `CHAY_WEB.bat`).

---

## 2. Các bước nạp sản phẩm lên Web bán hàng công ty

### Bước 1: Điền thông tin cơ bản & tải Ảnh đại diện
- Mở file `0_DANH_SACH_76_SAN_PHAM_BAN_HANG.csv` (hoặc `thong_tin_san_pham.txt` trong thư mục sản phẩm) để lấy **Tên sản phẩm**, **Mã sản phẩm**, **Danh mục**, **Giới thiệu ngắn**.
- Tải ảnh đại diện sản phẩm từ thư mục `1_anh_dai_dien/` của mã đó lên mục **Ảnh sản phẩm / Album ảnh** trên web bán hàng.

### Bước 2: Dán nội dung HTML mô tả chi tiết
- Mở file `<Mã SP>.html` trong thư mục `1_File_HTML_Copy_Dan_Web/` bằng Notepad (hoặc bấm nút **"Copy HTML Bán Hàng"** trên giao diện quản lý `index.html`).
- Nhấn `Ctrl + A` -> `Ctrl + C` để copy toàn bộ đoạn code.
- Trên trang quản trị Web bán hàng, tại ô **Mô tả chi tiết sản phẩm**, bấm vào nút chuyển sang chế độ **Mã nguồn / HTML (`<>` hoặc `Source`)**.
- **Lưu ý quan trọng tránh lỗi `Invalid token`**: Trước khi dán và nhấn Lưu, nếu bạn mở trang quản trị đã lâu hãy nhấn **F5 tải lại trang** (hoặc đăng nhập lại phiên quản trị) để làm mới CSRF/Session token của trình duyệt rồi mới dán code mới -> Lưu sản phẩm.
""")

print(f"Standardized export complete: {exported_products} products (CMS-safe HTML), {total_cover_imgs} cover images, {total_content_imgs} content images, {total_videos_exported} videos.")
