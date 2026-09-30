# KẾ HOẠCH TRIỂN KHAI (IMPLEMENTATION PLAN)
## DỰ ÁN: RAG LUẬT GIAO THÔNG ĐƯỜNG BỘ VIỆT NAM — AUTH, HISTORY & REACT UI REDESIGN

## 1. TỔNG QUAN (OVERVIEW)
Dự án nhằm tái cấu trúc và mở rộng hệ thống RAG Hỏi đáp Luật Giao thông Việt Nam hiện tại:
1. Xây dựng cơ sở dữ liệu MySQL lưu trữ người dùng và phiên/tin nhắn lịch sử trò chuyện.
2. Xây dựng hệ thống xác thực (Auth: Đăng ký, Đăng nhập, Đăng xuất) bằng JWT Bearer Token.
3. Nâng cấp API RAG Chat sang Server-Sent Events (SSE) để truyền dữ liệu thời gian thực kèm siêu dữ liệu nguồn luật trích dẫn (`citations`).
4. Thay thế giao diện Streamlit cũ bằng ứng dụng web hiện đại React (Vite) + Tailwind CSS tuân thủ nghiêm ngặt ngôn ngữ thiết kế Perplexity AI Research Terminal tại `DESIGN.md`.

---

## 2. QUYẾT ĐỊNH KIẾN TRÚC (ARCHITECTURE DECISIONS)

- **Hệ quản trị CSDL:** MySQL (chuẩn theo Đồ án 74DCTT22), kết nối qua `SQLAlchemy` (hỗ trợ pool kết nối và ORM) kết hợp driver `pymysql` hoặc `mysql-connector-python`.
- **Cơ chế xác thực:** JWT (JSON Web Token) thuật toán `HS256`, mật khẩu băm một chiều với `bcrypt`. Token được lưu ở `localStorage` trên trình duyệt và gửi qua header `Authorization: Bearer <token>`.
- **Giao thức Streaming RAG:** Server-Sent Events (SSE) `text/event-stream` thông qua FastAPI `StreamingResponse`. Định dạng event chuẩn hóa:
  - `event: session` (gửi session_id)
  - `event: delta` (gửi từng chunk văn bản sinh ra từ LLM)
  - `event: citations` (gửi mảng JSON siêu dữ liệu Điều/Khoản luật)
  - `event: done` (báo hiệu hoàn tất)
- **Chính sách người dùng:** Hỗ trợ chế độ Khách vãng lai (Guest). Khách vẫn có thể tra cứu RAG bình thường; khi đăng nhập, hệ thống sẽ tự động đồng bộ và lưu lịch sử vào MySQL.
- **Frontend Stack:** React 18 + Vite + Tailwind CSS. Áp dụng bảng màu `DESIGN.md` (Canvas `#faf8f5`, Charcoal `#27251e`, Deep Teal `#016a71`, nút bo pill `9999px`, khung chat 640px).

---

## 3. DANH SÁCH GIAI ĐOẠN VÀ NHIỆM VỤ (PHASES & TASKS)

### Phase 1: Database & Core Auth (Backend Foundation)
- [ ] **Task 1:** Thiết lập kết nối MySQL và định nghĩa SQLAlchemy Models (`users`, `chat_sessions`, `chat_messages`)
- [ ] **Task 2:** Xây dựng Auth Service & Security Utilities (`bcrypt` hashing, JWT token handling)
- [ ] **Task 3:** Xây dựng Auth API Endpoints (`/api/auth/register`, `/api/auth/login`, `/api/auth/me`)

#### Checkpoint 1: Database & Auth
- [ ] Kết nối MySQL thành công, bảng tự động tạo hoặc migrate đúng schema
- [ ] Đăng ký, đăng nhập tài khoản trả về JWT token hợp lệ
- [ ] Endpoint `/api/auth/me` xác thực đúng user

---

### Phase 2: Chat History & RAG Citations API (Backend Enhancement)
- [ ] **Task 4:** Xây dựng Chat History API Endpoints (`/api/sessions`, chi tiết phiên, xóa phiên)
- [ ] **Task 5:** Nâng cấp RAG Pipeline: Rút trích Citations và xây dựng SSE Streaming Endpoint (`/api/chat/stream`)

#### Checkpoint 2: Streaming & History Persistence
- [ ] Tạo phiên chat, tải danh sách lịch sử và chi tiết tin nhắn qua API thành công
- [ ] Luồng SSE stream trả về cả text chunk và mảng `citations` pháp lý
- [ ] Tin nhắn và citations được lưu chính xác vào MySQL khi user đã đăng nhập

---

### Phase 3: Frontend Setup & Design System (React + Tailwind)
- [ ] **Task 6:** Khởi tạo dự án React + Vite trong `frontend/` và cấu hình Tailwind CSS theo `DESIGN.md`
- [ ] **Task 7:** Xây dựng API Client, State Management (AuthContext & ChatContext) và bộ đọc luồng SSE

#### Checkpoint 3: React Foundation & Theme Active
- [ ] Dự án React Vite build và chạy thành công
- [ ] Toàn bộ CSS variables và tokens từ `DESIGN.md` (Aged paper `#faf8f5`, Charcoal `#27251e`, Pebble border) được áp dụng
- [ ] Context quản lý auth state và chat state hoạt động ổn định

---

### Phase 4: Frontend UI Components & End-to-End Integration
- [ ] **Task 8:** Xây dựng Modal Đăng ký / Đăng nhập (AuthModal) chuẩn Perplexity style
- [ ] **Task 9:** Xây dựng Sidebar 220px (Quản lý phiên, Nhóm lịch sử, Nút New Chat, Profile/Logout)
- [ ] **Task 10:** Xây dựng Vùng Chat 640px (Hero Search, Streaming Response, Citation Cards Drawer)

#### Checkpoint 4: Complete System Verification
- [ ] Toàn bộ luồng đăng ký -> đăng nhập -> hỏi đáp RAG -> hiển thị trích dẫn -> lưu lịch sử hoạt động trơn tru
- [ ] Chế độ Guest hoạt động bình thường mà không cần đăng nhập
- [ ] Giao diện đáp ứng 100% tiêu chí thẩm mỹ trong `DESIGN.md`

---

## 4. QUẢN TRỊ RỦI RO (RISKS AND MITIGATIONS)

| Rủi ro | Mức độ | Biện pháp giảm thiểu |
|---|---|---|
| Môi trường chưa cài Node.js / npm trong PATH | Cao | Cài đặt Node.js LTS qua `winget install OpenJS.NodeJS.LTS` hoặc cung cấp hướng dẫn khởi động |
| MySQL Server cục bộ chưa bật hoặc chưa tạo Database | Trung bình | Cung cấp script kiểm tra/khởi tạo CSDL tự động trong code (`CREATE DATABASE IF NOT EXISTS`), hướng dẫn cấu hình `.env` |
| RAG Chain mất nhiều thời gian sinh Multi-query gây trễ stream | Thấp | Tối ưu luồng song song `ThreadPoolExecutor`, trả sự kiện khởi đầu ngay khi retrieval hoàn tất |
| Token hết hạn trong quá trình sử dụng | Thấp | Xử lý lỗi 401 tự động ở Axios Interceptor, xóa token và đưa về trạng thái Guest |

---

## 5. CÂU HỎI MỞ & LƯU Ý (OPEN QUESTIONS & NOTES)
- Cần đảm bảo thông tin kết nối MySQL trong file `.env` khớp với MySQL Server đang chạy trên máy (user, password, host, port, database name).
- Nhánh Git `feat/auth-history-ui-redesign` đã tạo sẵn sàng ở local, khi người dùng phân quyền repo GitHub thì có thể push ngay lập tức.
