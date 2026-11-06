"""
Tool tải và lưu trữ toàn bộ hình ảnh / media ZMRobo về máy cục bộ.
- Tải đa luồng siêu tốc (20 threads song song)
- Tự động bỏ qua các file đã tải sẵn
- Đảm bảo web chạy 100% Offline mượt mà, không phụ thuộc vào mạng quốc tế / Trung Quốc
"""

import os
import sys
import json
import re
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, "media")
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(MEDIA_DIR, exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
}

def collect_all_media_urls():
    urls = set()
    
    # 1. Từ products_full.json
    prod_file = os.path.join(DATA_DIR, 'products_full.json')
    if os.path.exists(prod_file):
        with open(prod_file, 'r', encoding='utf-8') as f:
            products = json.load(f)
        for p in products:
            s = p.get('summary', {})
            cov = s.get('cover')
            if cov and cov.startswith('https://oss.zmrobo.com/'):
                urls.add(cov)
            
            d = p.get('detail', {})
            for c in d.get('coverList', []):
                u = c.get('url') if isinstance(c, dict) else c
                if u and u.startswith('https://oss.zmrobo.com/'):
                    urls.add(u)
            
            content = d.get('productInfo', {}).get('content', '')
            for m in re.finditer(r'src=["\'](https://oss\.zmrobo\.com/[^"\']+)["\']', content):
                urls.add(m.group(1))
            for m in re.finditer(r'url\(["\']?(https://oss\.zmrobo\.com/[^"\'\)\s]+)["\']?\)', content):
                urls.add(m.group(1))

    # 2. Từ categories.json
    cat_file = os.path.join(DATA_DIR, 'categories.json')
    if os.path.exists(cat_file):
        with open(cat_file, 'r', encoding='utf-8') as f:
            cats = json.load(f)
        for c in cats:
            for item in c.get('list', []):
                cov = item.get('cover')
                if cov and cov.startswith('https://oss.zmrobo.com/'):
                    urls.add(cov)

    # 3. Từ software.json
    soft_file = os.path.join(DATA_DIR, 'software.json')
    if os.path.exists(soft_file):
        with open(soft_file, 'r', encoding='utf-8') as f:
            soft = json.load(f)
        for s in soft:
            cov = s.get('cover')
            if cov and cov.startswith('https://oss.zmrobo.com/'):
                urls.add(cov)

    return sorted(list(urls))

def download_file(url):
    rel_path = url[len('https://oss.zmrobo.com/'):]
    rel_path = urllib.parse.unquote(rel_path)
    local_path = os.path.join(MEDIA_DIR, os.path.normpath(rel_path))
    
    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
        return url, True, "exists"
    
    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
            with open(local_path, 'wb') as out:
                out.write(data)
        return url, True, "downloaded"
    except Exception as e:
        return url, False, str(e)

def main():
    print("========================================================")
    print("   ZMROBO MEDIA DOWNLOADER - TẢI TOÀN BỘ ẢNH & ICON     ")
    print("========================================================")
    print("Dang quét toàn bộ liên kết hình ảnh và biểu tượng trong hệ thống...")
    
    urls = collect_all_media_urls()
    total = len(urls)
    print(f"-> Tìm thấy tổng cộng: {total} tệp hình ảnh & media.")
    print("Bắt đầu tải đa luồng (20 luồng song song)...")
    print("--------------------------------------------------------")

    done = 0
    downloaded_count = 0
    exists_count = 0
    failed_count = 0

    with ThreadPoolExecutor(max_workers=20) as executor:
        for url, ok, msg in executor.map(download_file, urls):
            done += 1
            if ok:
                if msg == "downloaded":
                    downloaded_count += 1
                else:
                    exists_count += 1
            else:
                failed_count += 1

            if done % 20 == 0 or done == total:
                pct = (done / total) * 100
                print(f"[{done:4d}/{total}] {pct:5.1f}% | Đã có: {exists_count} | Tải mới: {downloaded_count} | Lỗi: {failed_count}")

    print("========================================================")
    print(f"HOÀN TẤT!")
    print(f"- Tổng số: {total}")
    print(f"- Đã lưu trữ cục bộ: {exists_count + downloaded_count}")
    print(f"- Tải mới thành công: {downloaded_count}")
    print(f"- Lỗi/Không tồn tại trên server gốc: {failed_count}")
    print(f"- Thư mục lưu trữ: {MEDIA_DIR}")
    print("========================================================")

if __name__ == "__main__":
    main()

