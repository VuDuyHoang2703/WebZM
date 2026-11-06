import http.server
import socketserver
import socket
import webbrowser
import os
import sys
import urllib.request
import urllib.parse
import mimetypes
import shutil

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, "media")
os.makedirs(MEDIA_DIR, exist_ok=True)
os.chdir(BASE_DIR)

PORT = 8080

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Tập hợp các URL đã xác nhận 404 trên mạng để không bao giờ bị nghẽn thử lại
NOT_FOUND_CACHE = set()

class CachingMediaHandler(http.server.SimpleHTTPRequestHandler):
    def address_string(self):
        # Tối ưu siêu tốc 0ms: Ngăn chặn Windows thực hiện Reverse DNS lookup gây lag 2 giây
        return self.client_address[0]

    def log_message(self, format, *args):
        # Tắt bớt log rác để tránh nghẽn I/O terminal khi load hàng trăm ảnh song song
        if args and str(args[1]) in ['200', '304']:
            return
        super().log_message(format, *args)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Tự động bắt mọi yêu cầu /media/... để phục vụ từ ổ cứng 1ms
        if path.startswith('/media/'):
            rel_media_path = path[len('/media/'):]
            rel_media_path = urllib.parse.unquote(rel_media_path).strip("'\"")
            rel_media_path = rel_media_path.replace('&#39;', '').replace('&quot;', '').strip("'\"")
            rel_media_path = rel_media_path.lstrip('/\\')
            local_file_path = os.path.join(MEDIA_DIR, os.path.normpath(rel_media_path))

            # Bảo mật: không cho phép thoát khỏi thư mục media
            if not os.path.abspath(local_file_path).startswith(os.path.abspath(MEDIA_DIR)):
                self.send_error(403, "Access denied")
                return

            # Nếu chưa có trong máy và chưa từng bị 404, tải nhanh từ oss.zmrobo.com
            if not os.path.exists(local_file_path):
                if rel_media_path in NOT_FOUND_CACHE:
                    self.send_error(404, "File not found (cached 404)")
                    return

                remote_url = f"https://oss.zmrobo.com/{rel_media_path}"
                try:
                    req = urllib.request.Request(remote_url, headers=HEADERS)
                    with urllib.request.urlopen(req, timeout=3) as resp:
                        if resp.status == 200:
                            data = resp.read()
                            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                            with open(local_file_path, 'wb') as f:
                                f.write(data)
                        else:
                            NOT_FOUND_CACHE.add(rel_media_path)
                            self.send_error(resp.status, "Remote file not found")
                            return
                except Exception as e:
                    NOT_FOUND_CACHE.add(rel_media_path)
                    self.send_error(404, f"Media fetch error: {e}")
                    return

            # Phục vụ trực tiếp từ ổ cứng với tốc độ 1ms và cache vĩnh viễn trên trình duyệt
            try:
                file_size = os.path.getsize(local_file_path)
                mime_type, _ = mimetypes.guess_type(local_file_path)
                if not mime_type:
                    mime_type = 'application/octet-stream'

                self.send_response(200)
                self.send_header('Content-Type', mime_type)
                self.send_header('Content-Length', str(file_size))
                self.send_header('Cache-Control', 'public, max-age=31536000, immutable')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()

                with open(local_file_path, 'rb') as f:
                    shutil.copyfileobj(f, self.wfile, length=64 * 1024)
                return
            except Exception as e:
                return

        return super().do_GET()

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

class DualStackThreadingServer(socketserver.ThreadingTCPServer):
    # Hỗ trợ đồng thời cả IPv6 (::1, localhost) và IPv4 (127.0.0.1) trên Windows
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
            with DualStackThreadingServer(("::", PORT), CachingMediaHandler) as httpd:
                url = f"http://127.0.0.1:{PORT}/index.html"
                print("========================================================")
                print("  ZMROBO PRODUCT SHOWCASE - MÁY CHỦ BỘ NHỚ ĐỆM TỐC ĐỘ CAO")
                print(f"  Truy cập tại: {url}")
                print(f"  Hoặc:        http://localhost:{PORT}/index.html")
                print(f"  Thư mục cache ảnh: {MEDIA_DIR}")
                print("  (Tốc độ load ảnh siêu tốc: 1ms từ ổ cứng)")
                print("========================================================")
                webbrowser.open(url)
                httpd.serve_forever()
                break
        except OSError as e:
            if "address already in use" in str(e).lower() or getattr(e, 'errno', 0) == 10048:
                PORT += 1
            else:
                # Fallback sang IPv4 nếu môi trường không có IPv6
                try:
                    with socketserver.ThreadingTCPServer(("", PORT), CachingMediaHandler) as httpd:
                        httpd.serve_forever()
                        break
                except Exception:
                    PORT += 1

if __name__ == "__main__":
    start_server()
