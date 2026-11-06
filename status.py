import os
import json
import time

REGISTRY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "ocr_image_registry.json")

def show_status():
    if not os.path.exists(REGISTRY_FILE):
        print("Chưa có dữ liệu tiến độ.")
        return

    with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    summary = data.get("summary", {})
    total = summary.get("total_images", 0)
    translated = summary.get("translated", 0)
    no_text = summary.get("no_text", 0)
    pending = summary.get("pending", 0)
    processed = total - pending
    pct = (processed / total * 100) if total > 0 else 0

    bar_len = 30
    filled = int(bar_len * processed / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_len - filled)

    print("==========================================================================")
    print("           BẢNG THEO DÕI TIẾN ĐỘ AI OCR & DỊCH ẢNH ZMROBO                 ")
    print("==========================================================================")
    print(f" Tiền độ: [{bar}] {pct:.1f}% ({processed}/{total} ảnh)")
    print("--------------------------------------------------------------------------")
    print(f"  ✅ Đã phát hiện chữ & dịch tiếng Việt : {translated} ảnh")
    print(f"  ⚪ Ảnh linh kiện không có chữ (bỏ qua) : {no_text} ảnh")
    print(f"  ⏳ Còn lại đang chờ xử lý              : {pending} ảnh")
    print(f"  ⏱ Lần cập nhật gần nhất               : {summary.get('last_updated', 'N/A')}")
    print("==========================================================================")

    # Liệt kê 5 ảnh vừa dịch gần nhất
    trans_images = [k for k, v in data.get("images", {}).items() if v.get("status") == "translated"]
    if trans_images:
        print(" 5 Ảnh được dịch gần nhất:")
        for p in trans_images[-5:]:
            items = data["images"][p].get("items", [])
            sample = ", ".join([f"{x['original']} -> {x['translated']}" for x in items[:2]])
            print(f"  • {p}")
            print(f"    └── {sample}")
    print("==========================================================================")

if __name__ == "__main__":
    show_status()

