import http.server
import socketserver
import webbrowser
import os
import sys
import urllib.request
import urllib.parse
import mimetypes

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, "media")
os.makedirs(MEDIA_DIR, exist_ok=True)
os.chdir(BASE_DIR)

PORT = 8080

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

class CachingMediaHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Tự động bắt mọi yêu cầu /media/... để phục vụ từ ổ cứng hoặc tự động tải về lưu cache
        if path.startswith('/media/'):
            rel_media_path = path[len('/media/'):]
            rel_media_path = urllib.parse.unquote(rel_media_path).strip("'\"")
            rel_media_path = rel_media_path.replace('&#39;', '').replace('&quot;', '').strip("'\"")
            local_file_path = os.path.join(MEDIA_DIR, os.path.normpath(rel_media_path))

            # Bảo mật: không cho phép thoát khỏi thư mục media
            if not os.path.abspath(local_file_path).startswith(os.path.abspath(MEDIA_DIR)):
                self.send_error(403, "Access denied")
                return

            # Nếu chưa có trong máy, tự động tải từ oss.zmrobo.com về lưu vào ổ cứng
            if not os.path.exists(local_file_path):
                remote_url = f"https://oss.zmrobo.com/{rel_media_path}"
                try:
                    req = urllib.request.Request(remote_url, headers=HEADERS)
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        if resp.status == 200:
                            data = resp.read()
                            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                            with open(local_file_path, 'wb') as f:
                                f.write(data)
                        else:
                            self.send_error(resp.status, "Remote file not found")
                            return
                except Exception as e:
                    self.send_error(404, f"Media fetch error: {e}")
                    return

            # Phục vụ trực tiếp từ ổ cứng với tốc độ 1ms và lưu cache trình duyệt 1 năm
            try:
                with open(local_file_path, 'rb') as f:
                    content = f.read()

                mime_type, _ = mimetypes.guess_type(local_file_path)
                if not mime_type:
                    mime_type = 'application/octet-stream'

                self.send_response(200)
                self.send_header('Content-Type', mime_type)
                self.send_header('Content-Length', str(len(content)))
                self.send_header('Cache-Control', 'public, max-age=31536000, immutable')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(content)
                return
            except Exception as e:
                self.send_error(500, f"Error reading file: {e}")
                return

        return super().do_GET()

    def end_headers(self):
        # Bật CORS cho toàn bộ API và tệp tĩnh
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

def start_server():
    global PORT
    socketserver.TCPServer.allow_reuse_address = True
    while True:
        try:
            with socketserver.ThreadingTCPServer(("", PORT), CachingMediaHandler) as httpd:
                url = f"http://localhost:{PORT}/index.html"
                print("========================================================")
                print("  ZMROBO DATA VIEWER - MÁY CHỦ BỘ NHỚ ĐỆM TỐC ĐỘ CAO (MULTI-THREADED)")
                print(f"  Truy cập tại: {url}")
                print(f"  Thư mục cache ảnh: {MEDIA_DIR}")
                print("  (Tự động phục vụ ảnh siêu tốc từ ổ cứng 1ms)")
                print("  Nhấn Ctrl + C để dừng máy chủ.")
                print("========================================================")
                webbrowser.open(url)
                httpd.serve_forever()
                break
        except OSError as e:
            if "address already in use" in str(e).lower() or e.errno == 10048:
                PORT += 1
            else:
                raise e

if __name__ == "__main__":
    start_server()
