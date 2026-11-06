# Sổ tay dự án ZMRobo Data Viewer

Tài liệu này tóm lược cấu trúc, luồng hoạt động và cách vận hành dự án dựa trên mã nguồn cùng dữ liệu đang có trong thư mục `data/`. Số lượng bản ghi bên dưới là ảnh chụp tại thời điểm lập sổ tay; có thể thay đổi khi lấy dữ liệu mới.

## 1. Dự án dùng để làm gì?

Dự án lưu dữ liệu ZMRobo dưới dạng JSON/CSV và cung cấp giao diện web tiếng Việt để tra cứu sản phẩm, phần mềm, tài nguyên và tin tức. Mở giao diện chỉ cần chạy `view_data.bat`; tuy nhiên bản dữ liệu hiện tại vẫn còn một số bản dịch cũ chưa được hiệu đính và cần chạy lại bộ dịch theo ngữ cảnh một lần để làm mới.

Các thành phần chính:

1. **Dữ liệu có sẵn:** giao diện đọc trực tiếp các tệp trong `data/`; không dịch dữ liệu khi mở trang.
2. **Tra cứu:** chạy máy chủ HTTP cục bộ để trình duyệt đọc các tệp dữ liệu và hiển thị giao diện.
3. **Cập nhật tùy chọn:** crawler có thể lấy dữ liệu mới và chạy quy trình dịch; không cần bước này để xem dữ liệu hiện có.

## 2. Bắt đầu nhanh trên Windows

### Xem dữ liệu hiện có

1. Mở thư mục dự án.
2. Nhấp đúp `view_data.bat`, hoặc mở PowerShell tại thư mục dự án và chạy:

   ```powershell
   .\view_data.bat
   ```

3. Trình duyệt sẽ mở trang xem dữ liệu. Nếu cổng mặc định `8080` đang bận, máy chủ thử cổng tiếp theo.
4. Đóng cửa sổ máy chủ hoặc nhấn `Ctrl+C` trong cửa sổ dòng lệnh để dừng.

Có thể chạy thủ công bằng `python server.py`.

### Lấy dữ liệu mới

Chỉ khi muốn cập nhật dữ liệu, chạy `run_crawler.bat`. Trình thu thập cần Internet để gọi các API ZMRobo và tải dữ liệu mới.

**Lưu ý:** `crawler_zmrobo.py` gọi `full_system_translator.run_translation_pipeline()` sau khi tải dữ liệu. Bộ dịch hiện dùng endpoint Google Translate và cần Internet, không cần `GEMINI_API_KEY`. Nếu chỉ muốn xem dữ liệu hiện có, không chạy crawler; chỉ cần `view_data.bat`.

## 3. Bản đồ thư mục và tệp

| Tệp/thư mục | Vai trò |
|---|---|
| `crawler_zmrobo.py` | Gọi API, thu thập danh mục, sản phẩm, phần mềm, tài nguyên, tin tức và liên hệ; ghi dữ liệu xuống `data/`. |
| `apply_full_translation.py` | Tệp dịch theo quy tắc cũ, hiện không còn được gọi trong luồng crawler. |
| `full_system_translator.py` | Thu thập từng trường/cả đoạn HTML, yêu cầu Gemini dịch theo ngữ cảnh, lưu cache riêng và cập nhật JSON/CSV. |
| `run_crawler.bat` | Khởi chạy trình cào bằng lệnh `python crawler_zmrobo.py`. |
| `server.py` | Phục vụ các tệp tĩnh qua HTTP và mở trình duyệt tới giao diện. |
| `view_data.bat` | Khởi chạy máy chủ xem dữ liệu. |
| `index.html` | Giao diện người dùng, bộ lọc/tìm kiếm và cách hiển thị dữ liệu JSON. |
| `README.md` | Tài liệu giới thiệu/API ban đầu; sổ tay này bổ sung luồng chạy và các lưu ý đối chiếu mã nguồn. |
| `data/` | Dữ liệu đã thu thập, dữ liệu đã dịch và bộ nhớ dịch. |
| `.venv/`, `__pycache__/` | Thư mục môi trường Python và bộ nhớ đệm Python có trong workspace. Các tệp `.bat` hiện gọi `python` theo PATH, không tự kích hoạt `.venv`. |

Các chương trình Python trong dự án chủ yếu dùng thư viện chuẩn; hiện không có tệp manifest phụ thuộc như `requirements.txt`.

## 4. Luồng dữ liệu

### Khi thu thập

`crawler_zmrobo.py` thực hiện lần lượt:

1. Lấy cây danh mục.
2. Lấy danh sách sản phẩm, lưu bản tóm tắt và tải chi tiết từng sản phẩm. Chi tiết sản phẩm được gọi đồng thời với tối đa 8 luồng.
3. Tạo `products.csv`.
4. Lấy danh sách phần mềm và thông tin tải xuống.
5. Lấy danh sách tài nguyên, driver và firmware cùng chi tiết.
6. Lấy danh sách tin tức, chi tiết từng tin và tệp liên hệ từ kho OSS.
7. Chạy bộ dịch Gemini theo ngữ cảnh đầy đủ.

Các lỗi tải chi tiết từng mục thường được in ra và mục đó vẫn được lưu cùng thông tin lỗi; lỗi tổng thể của yêu cầu API có thể làm dừng tiến trình. Sau khi thu thập, các tệp JSON được ghi đè bằng kết quả mới.

### Khi chuẩn bị bản dịch

`full_system_translator.py` dùng trong quy trình cập nhật/hiệu đính dữ liệu. Nội dung HTML được gom theo đoạn, khối hoặc cụm định dạng trước khi dịch; các nút chữ rời không còn được gửi dịch riêng lẻ. Cache `translation_cache_contextual.json` tách biệt với cache cũ để dịch lại theo ngữ cảnh. Bộ dịch cần Internet tới Google Translate. Nếu cần tạo lại dữ liệu đã dịch mà không thu thập lại từ website, có thể chạy `python full_system_translator.py` một lần; những lần xem sau chỉ cần chạy `view_data.bat`.

Nếu Gemini gặp một số lỗi quá tải hoặc quota, chương trình có thể thử model dự phòng. Nếu quá trình dịch bị gián đoạn, cache cùng các bản dịch đã lưu được giữ lại để có thể chạy lại.

### Khi mở giao diện

`server.py` phục vụ thư mục dự án qua HTTP. `index.html` tải các tệp `categories.json`, `products_full.json`, `software.json`, `resources.json` và `news.json`, sau đó dựng các tab. Giao diện đọc dữ liệu đã lưu, không tự gọi API ZMRobo.

## 5. Dữ liệu trong `data/`

| Tệp | Nội dung / cấu trúc |
|---|---|
| `categories.json` | Cây danh mục; mỗi nhóm có `childrenList`. Các trường tiếng Anh gốc có thể được giữ ở `title_en`. |
| `products_summary.json` | Danh sách sản phẩm gọn, gồm mã, tên, danh mục và ảnh đại diện. |
| `products_full.json` | Danh sách sản phẩm đầy đủ, mỗi phần tử có `summary` và `detail`; chi tiết có thể gồm `productInfo`, `coverList`, `resourceList`, `otherResourceList`, `softwareList`, `questionList`. |
| `products.csv` | Bảng tổng hợp sản phẩm, tiện mở bằng Excel; được ghi UTF-8 có BOM. |
| `software.json` | Phần mềm, thông tin giới thiệu, các bản tải xuống, lịch sử phiên bản và mô-đun. |
| `resources.json` | Tài liệu/driver/firmware, thông tin phiên bản và URL tải. |
| `news.json` | Tin tức gồm `summary` và `detail`, có thể kèm tin trước/sau. |
| `contact.json` | Danh sách thông tin liên hệ lấy từ kho OSS; giao diện hiện tại không tải tệp này. |
| `translation_cache_contextual.json` | Cache mới cho bản dịch theo ngữ cảnh, được `full_system_translator.py` sử dụng. |
| `translation_cache_gemini.json`, `translation_cache.json`, `translation_cache_v2.json` | Cache cũ có sẵn; không được bộ dịch theo ngữ cảnh hiện tại sử dụng. |

Tại thời điểm lập tài liệu, dữ liệu gồm 4 nhóm danh mục, 302 sản phẩm, 8 phần mềm, 37 tài nguyên, 9 tin tức và 30 bản ghi liên hệ. Số lượng thực tế phụ thuộc dữ liệu API ở lần cập nhật gần nhất.

## 6. Giao diện tra cứu

- **Sản phẩm:** lọc theo danh mục cha/con; tìm theo tên tiếng Việt, tên tiếng Anh hoặc mã; sắp xếp theo ID hoặc tên. Danh sách hiển thị 24 sản phẩm mỗi lần và có nút xem thêm.
- **Chi tiết sản phẩm:** xem ảnh, mô tả, HTML giới thiệu, video, sách hướng dẫn, phần mềm tương thích, tài nguyên đính kèm và FAQ nếu có. Đường dẫn `#product-{id}` có thể mở thẳng một sản phẩm.
- **Phần mềm:** xem phần giới thiệu và liên kết tải theo nền tảng.
- **Tài liệu / Driver:** lọc theo tiêu đề và mở liên kết tải nếu có.
- **Tin tức:** xem danh sách và mở nội dung trong hộp thoại; nhấn `Escape` để đóng.

Một số kiểu chữ/giao diện được nạp từ CDN bên ngoài, vì vậy khi không có Internet phần dữ liệu cục bộ vẫn có thể được phục vụ nhưng kiểu dáng hoặc biểu tượng có thể không hiển thị đầy đủ.

## 7. API nguồn được trình cào sử dụng

Base URL: `https://www.zmrobo.net/api`. Các đường dẫn dưới đây được gọi trong `crawler_zmrobo.py`.

| Dữ liệu | Phương thức và đường dẫn | Tham số chính |
|---|---|---|
| Danh mục sản phẩm | `GET /product/getProductTypeList` | Không có |
| Danh sách sản phẩm | `POST /product/getProductList` | `all=1` |
| Chi tiết sản phẩm | `POST /product/getProductInfo` | `id` |
| Danh sách phần mềm | `GET /index/getNaviSoftwareList` | Không có |
| Chi tiết phần mềm | `POST /software/getSoftwareInfo` | `id` |
| Danh sách tài nguyên | `GET /resource/getResourceList` | Không có |
| Chi tiết tài nguyên | `GET /resource/getResourceInfo` | `id` |
| Danh sách tin tức | `GET /news/getNewsList` | Không có |
| Chi tiết tin tức | `GET /news/getNewsInfo` | `id` |
| Thông tin liên hệ | `GET https://oss.zmrobo.com/zmrobo/update/contact.json` | URL OSS trực tiếp |

Trình cào gửi header `User-Agent` và `Content-Type` dạng form. Mã nguồn hiện tạo SSL context không kiểm tra chứng chỉ máy chủ; cần lưu ý điều này khi vận hành qua mạng không tin cậy.

## 8. Bộ dịch (chỉ dùng khi cập nhật dữ liệu)

- Bộ dịch hiện gửi nội dung tới endpoint Google Translate; cần kết nối Internet.
- Không cần khóa API Gemini.
- Không có tệp BAT dịch riêng; để xem dữ liệu, chỉ chạy `view_data.bat`.
- Cache dùng cho các lần dịch theo ngữ cảnh: `data/translation_cache_contextual.json`.
- Tên bộ kit và thẻ HTML được bảo vệ bằng mã giữ chỗ trong lúc dịch để hạn chế thay đổi.
- Bộ dịch xử lý cả nội dung HTML; nội dung trong thẻ `script` và `style` được giữ nguyên.
- Bản dịch được ghi vào các trường tiếng Việt, còn tên tiếng Anh gốc được giữ ở các trường như `title_en` khi có áp dụng.

## 9. Xử lý sự cố thường gặp

| Hiện tượng | Hướng xử lý |
|---|---|
| Không tìm thấy Python | Cài Python 3, bảo đảm `python`/`python.exe` có trong PATH; mở lại cửa sổ dòng lệnh sau khi cài. |
| Trang mở nhưng dữ liệu trống | Chạy từ `view_data.bat`/`server.py`, kiểm tra các tệp JSON cần thiết trong `data/` và xem thông báo lỗi trong cửa sổ máy chủ hoặc Developer Console của trình duyệt. |
| Cổng 8080 đang được sử dụng | Máy chủ tự thử cổng kế tiếp; dùng URL được in ra trong cửa sổ thay vì giả định luôn là cổng 8080. |
| Bước dịch không kết nối được | Kiểm tra kết nối Internet tới Google Translate. Cache đã lưu được giữ lại để có thể chạy lại. |
| Cào dữ liệu thất bại | Kiểm tra kết nối Internet, API nguồn và lỗi trong cửa sổ dòng lệnh; xác nhận các JSON vẫn hợp lệ trước khi tiếp tục dịch. |
| Không thấy kiểu giao diện/biểu tượng | Kiểm tra kết nối tới CDN Tailwind CSS, Font Awesome và Google Fonts mà `index.html` tham chiếu. |

## 10. Lưu ý vận hành và bảo toàn dữ liệu

- Sao lưu thư mục `data/` trước khi cào lại vì các tệp dữ liệu đầu ra bị ghi đè.
- Chỉ cần xem dữ liệu hiện có thì chạy `view_data.bat`; không cần chạy crawler hoặc bộ dịch.
- Không chỉnh sửa cache trong lúc bộ dịch đang chạy.
- `apply_full_translation.py` là bộ dịch quy tắc cũ và không còn được crawler gọi; tránh chạy tệp này lên dữ liệu vì các thay thế rời rạc có thể làm câu bị pha trộn hoặc sai ngữ pháp.
- Máy chủ trong `server.py` dùng HTTP server tĩnh đơn giản và bind trên mọi giao diện mạng của máy, dù URL trình duyệt in ra là `localhost`. Chỉ chạy trong mạng tin cậy và dừng máy chủ khi không sử dụng; máy chủ này không có xác thực.
- Dữ liệu chứa liên kết và nội dung lấy từ website bên ngoài; tính sẵn có của ảnh, video và tệp tải phụ thuộc dịch vụ nguồn.

## 11. Tham khảo thêm

- [README.md](./README.md): danh mục API và mô tả giao diện ban đầu.
- [crawler_zmrobo.py](./crawler_zmrobo.py): chi tiết các yêu cầu thu thập dữ liệu.
- [full_system_translator.py](./full_system_translator.py): xử lý dịch, cache và cập nhật dữ liệu.
- [index.html](./index.html): cấu trúc giao diện và logic tra cứu.
