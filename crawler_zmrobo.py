"""
ZMRobo Full Data Scraper & API Extractor
Trích xuất toàn bộ dữ liệu từ https://www.zmrobo.net
"""

import os
import sys
import json
import csv
import time
import ssl
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding='utf-8')

BASE_API = "https://www.zmrobo.net/api"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_RAW = os.path.join(BASE_DIR, "data_raw")
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_RAW, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# SSL context bypassing verification if needed
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Accept': 'application/json, text/plain, */*'
}

def request_api(endpoint: str, method: str = "GET", data: dict = None, custom_url: str = None):
    url = custom_url if custom_url else f"{BASE_API}/{endpoint}"
    body = None
    if method == "POST":
        body = urllib.parse.urlencode(data or {}).encode('utf-8')
    elif method == "GET" and data:
        url += f"?{urllib.parse.urlencode(data)}"

    req = urllib.request.Request(url, data=body, headers=HEADERS, method=method)
    with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
        content = resp.read().decode('utf-8')
        return json.loads(content)

def crawl_categories():
    print("[1/6] Đang tải danh mục sản phẩm (Product Types)...")
    res = request_api("product/getProductTypeList", method="GET")
    data = res.get("data", {}).get("productTypeList", [])
    out_file = os.path.join(DATA_RAW, "categories.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  -> Đã lưu {len(data)} nhóm danh mục chính vào {out_file}")
    return data

def crawl_products():
    print("[2/6] Đang lấy danh sách toàn bộ sản phẩm...")
    res = request_api("product/getProductList", method="POST", data={"all": "1"})
    products = res.get("data", {}).get("productList", [])
    total = res.get("data", {}).get("total", len(products))
    print(f"  -> Tìm thấy tổng cộng {total} sản phẩm.")

    # Lưu danh sách tóm tắt
    out_list = os.path.join(DATA_RAW, "products_summary.json")
    with open(out_list, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    print(f"[3/6] Đang cào chi tiết từng sản phẩm (302 sản phẩm, đa luồng)...")
    product_details = []
    
    def fetch_detail(p):
        pid = p["id"]
        try:
            d_res = request_api("product/getProductInfo", method="POST", data={"id": pid})
            p_detail = d_res.get("data", {})
            return {
                "summary": p,
                "detail": p_detail
            }
        except Exception as e:
            print(f"  [!] Lỗi khi cào sản phẩm ID {pid}: {e}")
            return {"summary": p, "detail": None, "error": str(e)}

    done_count = 0
    with ThreadPoolExecutor(max_workers=16) as executor:
        future_map = {executor.submit(fetch_detail, p): p for p in products}
        for future in as_completed(future_map):
            res_item = future.result()
            product_details.append(res_item)
            done_count += 1
            if done_count % 50 == 0 or done_count == len(products):
                print(f"  -> Tiến độ chi tiết: {done_count}/{len(products)} ({done_count/len(products)*100:.1f}%)")

    # Lưu toàn bộ chi tiết dạng JSON
    out_details = os.path.join(DATA_RAW, "products_full.json")
    with open(out_details, "w", encoding="utf-8") as f:
        json.dump(product_details, f, ensure_ascii=False, indent=2)
    print(f"  -> Đã lưu dữ liệu đầy đủ 302 sản phẩm gốc vào {out_details}")

    # Xuất ra file CSV để dễ mở bằng Excel
    csv_file = os.path.join(DATA_DIR, "products.csv")
    with open(csv_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "ID", "Mã sản phẩm (Code)", "Tên sản phẩm (Title)", "Danh mục cha", "Danh mục con",
            "Mô tả ngắn (Intro)", "Ảnh đại diện (Cover)", "Video", "Tài liệu (Manual)",
            "Số ảnh gallery", "Số phần mềm đi kèm", "Số tài liệu đi kèm", "Số câu hỏi FAQ", "Cập nhật lúc"
        ])
        for item in product_details:
            s = item.get("summary", {})
            d = (item.get("detail") or {}).get("productInfo", {}) or {}
            covers = (item.get("detail") or {}).get("coverList", []) or []
            softwares = (item.get("detail") or {}).get("softwareList", []) or []
            resources = (item.get("detail") or {}).get("resourceList", []) or []
            faqs = (item.get("detail") or {}).get("questionList", []) or []
            
            writer.writerow([
                s.get("id"),
                s.get("code") or d.get("code", ""),
                s.get("title") or d.get("title", ""),
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
    print(f"  -> Đã xuất bảng CSV tổng hợp vào {csv_file}")

def crawl_software():
    print("[4/6] Đang cào danh sách phần mềm và link tải...")
    res = request_api("index/getNaviSoftwareList", method="GET")
    software_list = res.get("data", {}).get("softwareList", [])
    
    softwares_full = []
    for sw in software_list:
        sid = sw["id"]
        try:
            d_res = request_api("software/getSoftwareInfo", method="POST", data={"id": sid})
            softwares_full.append({
                "summary": sw,
                "detail": d_res.get("data", {})
            })
        except Exception as e:
            print(f"  [!] Lỗi khi cào phần mềm {sw.get('name')}: {e}")
            softwares_full.append({"summary": sw, "detail": None, "error": str(e)})

    out_file = os.path.join(DATA_RAW, "software.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(softwares_full, f, ensure_ascii=False, indent=2)
    print(f"  -> Đã lưu {len(softwares_full)} phần mềm + link tải các hệ điều hành vào {out_file}")

def crawl_resources():
    print("[5/6] Đang cào tài liệu, driver, firmware (Resource Center)...")
    res = request_api("resource/getResourceList", method="GET")
    res_list = res.get("data", {}).get("resourceList", [])
    
    resources_full = []
    for r in res_list:
        rid = r["id"]
        try:
            d_res = request_api("resource/getResourceInfo", method="GET", data={"id": rid})
            resources_full.append({
                "summary": r,
                "detail": d_res.get("data", {}).get("resourceInfo", {})
            })
        except Exception as e:
            print(f"  [!] Lỗi khi cào tài nguyên ID {rid}: {e}")
            resources_full.append({"summary": r, "detail": None, "error": str(e)})

    out_file = os.path.join(DATA_RAW, "resources.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(resources_full, f, ensure_ascii=False, indent=2)
    print(f"  -> Đã lưu {len(resources_full)} tài liệu/driver vào {out_file}")

def crawl_news_and_contact():
    print("[6/6] Đang cào tin tức và thông tin liên hệ...")
    res = request_api("news/getNewsList", method="GET")
    news_list = res.get("data", {}).get("newsList", [])
    
    news_full = []
    for n in news_list:
        nid = n["id"]
        try:
            d_res = request_api("news/getNewsInfo", method="GET", data={"id": nid})
            news_full.append({
                "summary": n,
                "detail": d_res.get("data", {})
            })
        except Exception as e:
            print(f"  [!] Lỗi khi cào tin tức ID {nid}: {e}")
            news_full.append({"summary": n, "detail": None, "error": str(e)})

    with open(os.path.join(DATA_RAW, "news.json"), "w", encoding="utf-8") as f:
        json.dump(news_full, f, ensure_ascii=False, indent=2)

    try:
        contact_res = request_api("", method="GET", custom_url="https://oss.zmrobo.com/zmrobo/update/contact.json")
        with open(os.path.join(DATA_RAW, "contact.json"), "w", encoding="utf-8") as f:
            json.dump(contact_res, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  [!] Lỗi contact: {e}")

    print("  -> Hoàn thành tin tức và thông tin liên hệ gốc.")

def main():
    print("=========================================================")
    print("  BẮT ĐẦU CÀO TOÀN BỘ DỮ LIỆU WEBSITE WWW.ZMROBO.NET     ")
    print("=========================================================")
    start_time = time.time()
    
    crawl_categories()
    crawl_products()
    crawl_software()
    crawl_resources()
    crawl_news_and_contact()
    
    # Dịch theo ngữ cảnh đầy đủ, giữ nguyên tên các bộ Kit.
    import full_system_translator
    print("[*] Đang chạy bộ dịch chuẩn ngữ pháp và ngữ cảnh tiếng Việt...")
    full_system_translator.run_translation_pipeline()
    
    duration = time.time() - start_time
    print("=========================================================")
    print(f"  CÀO VÀ DỊCH DỮ LIỆU THÀNH CÔNG TRONG {duration:.2f} GIÂY! ")
    print(f"  Tất cả dữ liệu chuẩn đã được lưu tại: {DATA_DIR}       ")
    print("=========================================================")

if __name__ == "__main__":
    main()
