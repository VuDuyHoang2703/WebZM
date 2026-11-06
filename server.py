import http.server
import socketserver
import socket
import webbrowser
import os
import sys
import urllib.parse
import mimetypes
import shutil
import time

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, "media")
os.makedirs(MEDIA_DIR, exist_ok=True)
os.chdir(BASE_DIR)

PORT = 8080

class LocalMediaHandler(http.server.SimpleHTTPRequestHandler):
    def address_string(self):
        # Tối ưu 0ms: Ngăn Windows reverse DNS lookup
        return self.client_address[0]

    def log_message(self, format, *args):
        # Tắt log các request thành công để tránh nghẽn terminal I/O
        if args and str(args[1]) in ['200', '304']:
            return
        super().log_message(format, *args)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Tự động bắt mọi yêu cầu /media/... để phục vụ trực tiếp 100% từ ổ cứng
        if path.startswith('/media/'):
            rel_media_path = path[len('/media/'):]
            rel_media_path = urllib.parse.unquote(rel_media_path).strip("'\"").rstrip('\\')
            rel_media_path = rel_media_path.replace('&#39;', '').replace('&quot;', '').strip("'\"")
            rel_media_path = rel_media_path.lstrip('/\\')
            local_file_path = os.path.join(MEDIA_DIR, os.path.normpath(rel_media_path))

            # Bảo mật
            if not os.path.abspath(local_file_path).startswith(os.path.abspath(MEDIA_DIR)):
                self.send_error(403, "Access denied")
                return

            # Nếu tệp tồn tại trên ổ cứng: phục vụ siêu tốc 1ms với cache vĩnh viễn
            if os.path.exists(local_file_path) and os.path.isfile(local_file_path):
                try:
                    file_size = os.path.getsize(local_file_path)
                    mime_type, _ = mimetypes.guess_type(local_file_path)
                    if not mime_type:
                        mime_type = 'application/octet-stream'

                    self.send_response(200)
                    self.send_header('Content-Type', mime_type)
                    self.send_header('Content-Length', str(file_size))
                    self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                    self.send_header('Pragma', 'no-cache')
                    self.send_header('Expires', '0')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()

                    with open(local_file_path, 'rb') as f:
                        shutil.copyfileobj(f, self.wfile, length=64 * 1024)
                    return
                except Exception:
                    return

            # Nếu tệp không tồn tại: trả về 404 NGAY LẬP TỨC (0ms), tuyệt đối không kết nối ra ngoài gây treo
            self.send_error(404, "File not found locally")
            return

        return super().do_GET()

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

class DualStackThreadingServer(socketserver.ThreadingTCPServer):
    address_family = socket.AF_INET6
    daemon_threads = True

    def server_bind(self):
        try:
            self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        except Exception:
            pass
        super().server_bind()

def start_server():
    global PORT
    socketserver.TCPServer.allow_reuse_address = True
    while True:
        try:
            with DualStackThreadingServer(("::", PORT), LocalMediaHandler) as httpd:
                t_stamp = int(time.time())
                url = f"http://127.0.0.1:{PORT}/index.html?t={t_stamp}"
                print("========================================================")
                print("  ZMROBO PRODUCT SHOWCASE - MÁY CHỦ BỘ NHỚ ĐỆM TỐC ĐỘ CAO")
                print(f"  Truy cập tại: {url}")
                print(f"  Hoặc:        http://localhost:{PORT}/index.html?t={t_stamp}")
                print(f"  Thư mục media cục bộ: {MEDIA_DIR}")
                print("  (Chế độ chống cache: Tự động tải 100% tệp mới nhất từ ổ cứng)")
                print("========================================================")
                webbrowser.open(url)
                httpd.serve_forever()
                break
        except OSError as e:
            if "address already in use" in str(e).lower() or getattr(e, 'errno', 0) == 10048:
                PORT += 1
            else:
                try:
                    with socketserver.ThreadingTCPServer(("", PORT), LocalMediaHandler) as httpd:
                        httpd.serve_forever()
                        break
                except Exception:
                    PORT += 1

if __name__ == "__main__":
    start_server()
