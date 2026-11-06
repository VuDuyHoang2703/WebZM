import http.server
import socketserver
import webbrowser
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

os.chdir(os.path.dirname(os.path.abspath(__file__)))

PORT = 8080
Handler = http.server.SimpleHTTPRequestHandler

def start_server():
    global PORT
    while True:
        try:
            with socketserver.TCPServer(("", PORT), Handler) as httpd:
                url = f"http://localhost:{PORT}/index.html"
                print("========================================================")
                print("  ZMROBO DATA VIEWER ĐANG CHẠY!")
                print(f"  Truy cập tại: {url}")
                print("  (Đang tự động mở trình duyệt web...)")
                print("  Nhấn Ctrl + C để dừng máy chủ.")
                print("========================================================")
                webbrowser.open(url)
                httpd.serve_forever()
                break
        except OSError as e:
            # Port busy, try next port
            if "address already in use" in str(e).lower() or e.errno == 10048:
                PORT += 1
            else:
                raise e

if __name__ == "__main__":
    start_server()

