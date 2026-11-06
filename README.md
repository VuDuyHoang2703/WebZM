# ZMROBO DATA SCRAPER & FULL API DOCUMENTATION

Dự án thu thập dữ liệu từ [zmrobo.net](https://www.zmrobo.net), lưu thành các tệp JSON/CSV và cung cấp giao diện tiếng Việt để tra cứu.

---

## 1. Nguyên nhân 2 API của bạn bị lỗi 404

Trong danh sách bạn gửi:
1. `https://www.zmrobo.net/api/index/getNaviSoftwareList` -> **ĐÚNG** (GET trả về danh sách phần mềm).
2. `https://www.zmrobo.net/api/index/getProductList` -> **SAI ĐƯỜNG DẪN VÀ METHOD**.
   - Đường dẫn đúng: `POST https://www.zmrobo.net/api/product/getProductList` (nằm ở `/product/`, không phải `/index/`, và bắt buộc dùng method **POST**).
3. `https://www.zmrobo.net/api/index/getProductTypeList` -> **SAI ĐƯỜNG DẪN**.
   - Đường dẫn đúng: `GET https://www.zmrobo.net/api/product/getProductTypeList` (nằm ở `/product/`, không phải `/index/`).

---

## 2. Danh mục toàn bộ API của website (Trích xuất từ Bundle Javascript)

Base URL: `https://www.zmrobo.net/api/`  
Header yêu cầu:
```http
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
```

### A. Nhóm Sản phẩm (Products)
| Tên API | Method | Đường dẫn API | Tham số (Payload) | Mô tả |
| :--- | :---: | :--- | :--- | :--- |
| **Phân loại sản phẩm** | `GET` | `/product/getProductTypeList` | Không có | Lấy cây danh mục sản phẩm (Education, Competition, Electronic, Plastic và các sub-category) |
| **Danh sách sản phẩm** | `POST` | `/product/getProductList` | `all=1` hoặc `{}` | Lấy toàn bộ 302 sản phẩm của website |
| **Chi tiết sản phẩm** | `POST` | `/product/getProductInfo` | `id={product_id}` hoặc `code={code}` | Thông số, mô tả chi tiết HTML, gallery ảnh, video, sách hướng dẫn (manual), phần mềm & tài liệu liên kết, FAQ |
| **Menu sản phẩm** | `GET` | `/index/getNaviProductList` | Không có | Cây danh mục sản phẩm phục vụ hiển thị navbar |

### B. Nhóm Phần mềm (Software)
| Tên API | Method | Đường dẫn API | Tham số (Payload) | Mô tả |
| :--- | :---: | :--- | :--- | :--- |
| **Danh sách phần mềm** | `GET` | `/index/getNaviSoftwareList` | Không có | 8 phần mềm chính của ZMRobo (RoboMaker, RoboCode, ...) |
| **Chi tiết & Link tải** | `POST` | `/software/getSoftwareInfo` | `id={software_id}` | Lấy link tải cài đặt cho Windows, macOS, Android, iOS, lịch sử các phiên bản |

### C. Nhóm Tài nguyên & Driver (Resource Center)
| Tên API | Method | Đường dẫn API | Tham số (Payload) | Mô tả |
| :--- | :---: | :--- | :--- | :--- |
| **Danh sách tài nguyên** | `GET` | `/resource/getResourceList` | `keyword=""` (tuỳ chọn) | 37 tài liệu hướng dẫn, driver, firmware |
| **Chi tiết & Link tải** | `GET` | `/resource/getResourceInfo` | `id={resource_id}` | Link tải trực tiếp file exe, zip, pdf từ OSS |

### D. Tin tức & Trang chủ (News & Home)
| Tên API | Method | Đường dẫn API | Tham số (Payload) | Mô tả |
| :--- | :---: | :--- | :--- | :--- |
| **Trang chủ & Banner** | `GET` | `/index/getHomeData` | Không có | Danh sách banner trang chủ, tin nổi bật |
| **Danh sách tin tức** | `GET` | `/news/getNewsList` | Không có | Danh sách bài viết tin tức, bộ lọc theo năm |
| **Chi tiết tin tức** | `GET` | `/news/getNewsInfo` | `id={news_id}` | Nội dung bài viết chi tiết |
| **Gợi ý tìm kiếm** | `GET` | `/index/beforeSearchList` | Không có | Từ khóa hot / tìm kiếm nhiều |
| **Tìm kiếm toàn cục** | `POST` | `/index/searchGlobal` | `keyword={tu_khoa}` | Tìm kiếm sản phẩm, tin tức theo từ khóa |

### E. File cấu hình tĩnh (OSS)
- Liên hệ công ty: `https://oss.zmrobo.com/zmrobo/update/contact.json`
- Namecard hỗ trợ: `https://oss.zmrobo.com/zmrobo/update/namecard_support.json`

---

## 3. Cấu trúc thư mục dữ liệu đã cào

Dữ liệu đã được cào về và lưu trong thư mục `d:\DataZMRobo\data`:

```
d:\DataZMRobo\data\
│
├── categories.json          # Cây danh mục sản phẩm đầy đủ
├── products_summary.json    # Danh sách tóm tắt 302 sản phẩm
├── products_full.json       # Chi tiết toàn diện 302 sản phẩm (1.18 MB)
├── products.csv             # Bảng tính Excel tổng hợp 302 sản phẩm
├── software.json            # 8 phần mềm + toàn bộ link tải cho các hệ điều hành
├── resources.json           # 37 file tài liệu, driver + link download trực tiếp
├── news.json                # Toàn bộ tin tức & bài viết
└── contact.json             # Thông tin liên hệ
```

---

## 4. Mở giao diện xem dữ liệu

Dữ liệu hiện có trong thư mục `data/` đã nằm sẵn trong dự án; mở giao diện không tự chạy bước dịch. Để xem, chỉ cần nhấp đúp **[`view_data.bat`](./view_data.bat)**. Tệp này khởi động máy chủ cục bộ và tự động mở trình duyệt:
   - **Tab Sản phẩm**: Cây lọc danh mục (Giáo dục, Thi đấu, Linh kiện điện tử, Linh kiện nhựa), tìm kiếm theo tên hoặc mã sản phẩm, xem chi tiết (ảnh gallery, video, link tải manual PDF, Q&A).
   - **Tab Phần mềm**: Xem 8 phần mềm chính (RoboMaker, RoboCode, Scratch3...) kèm nút tải trực tiếp cho Windows, macOS, Android, iOS.
   - **Tab Tài liệu & Driver**: Tìm kiếm và tải trực tiếp 37 driver, firmware, tài liệu hướng dẫn.
   - **Tab Tin tức**: Xem danh sách và nội dung đầy đủ các bài viết tin tức.

Không cần chạy trình dịch để mở hoặc xem dữ liệu đã có. Không đóng cửa sổ dòng lệnh của máy chủ khi vẫn muốn tiếp tục sử dụng giao diện; nhấn `Ctrl+C` để dừng.

Lưu ý: bản dữ liệu hiện tại vẫn có một số nội dung dịch cũ chưa được hiệu đính. Sau khi chạy lại bộ dịch theo ngữ cảnh một lần để cập nhật dữ liệu, các lần xem tiếp theo chỉ cần mở `view_data.bat`.

## 5. Tùy chọn: cập nhật dữ liệu nguồn

Chỉ chạy `run_crawler.bat` khi muốn tải dữ liệu mới từ zmrobo.net. Tác vụ này ghi đè một số tệp trong `data/` và tiếp tục chạy các bước dịch tự động.

Việc cập nhật cần Internet tới website ZMRobo; bước dịch tự động dùng endpoint Google Translate và cũng cần Internet, không cần `GEMINI_API_KEY`. Nếu mục tiêu chỉ là tra cứu dữ liệu hiện có, không chạy `run_crawler.bat`; hãy mở `view_data.bat`.
