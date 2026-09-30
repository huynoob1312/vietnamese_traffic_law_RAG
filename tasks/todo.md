# DANH SÁCH NHIỆM VỤ THỰC HIỆN (TODO LIST)
## DỰ ÁN: RAG LUẬT GIAO THÔNG ĐƯỜNG BỘ — AUTH, HISTORY & REACT UI REDESIGN

---

## Phase 1: Database & Core Auth (Backend Foundation)

### Task 1: Thiết lập kết nối MySQL và định nghĩa SQLAlchemy Models
**Description:** Cấu hình kết nối cơ sở dữ liệu MySQL bằng SQLAlchemy, đọc cấu hình từ biến môi trường `.env`, định nghĩa 3 bảng ORM Models (`User`, `ChatSession`, `ChatMessage`) bám sát cấu trúc tại Bảng 3.8, 3.9, 3.10 trong Báo cáo Đồ án 74DCTT22, và cung cấp script khởi tạo database tự động.

**Acceptance criteria:**
- [x] File `.env` và `src/utils/config.py` hỗ trợ các biến cấu hình MySQL (`MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`).
- [x] SQLAlchemy models `User`, `ChatSession`, `ChatMessage` được định nghĩa chuẩn xác với đầy đủ khóa chính, khóa ngoại, cascade delete và kiểu dữ liệu JSON cho `citations`.
- [x] Script khởi tạo DB tự động tạo CSDL nếu chưa có và sinh đầy đủ các bảng.

**Verification:**
- [x] Test command: `python -m src.db.init_db` chạy thành công không lỗi.
- [x] Manual check: Kiểm tra trong MySQL thấy xuất hiện 3 bảng `users`, `chat_sessions`, `chat_messages` với đúng cấu trúc cột.

**Dependencies:** None  
**Files likely touched:**
- `src/db/__init__.py`
- `src/db/database.py`
- `src/db/models.py`
- `src/db/init_db.py`
- `.env`
- `requirements.txt`

**Estimated scope:** M (3-5 files)

---

### Task 2: Xây dựng Auth Service & Security Utilities
**Description:** Xây dựng các hàm tiện ích bảo mật mật khẩu bằng `bcrypt` (hashing và verify), cấp phát và giải mã JWT token (JSON Web Token) với thuật toán `HS256`, thiết lập thời gian hết hạn token và middleware/dependency trích xuất user hiện tại từ Bearer token.

**Acceptance criteria:**
- [x] Hàm `hash_password(password)` và `verify_password(plain, hashed)` hoạt động chuẩn xác bằng `bcrypt`.
- [x] Hàm `create_access_token(data, expires_delta)` sinh JWT token mang thông tin `user_id`, `username`, `role`.
- [x] FastAPI Dependency `get_current_user` giải mã token từ header `Authorization: Bearer <token>`, trả về User model hoặc raise HTTP 401 nếu không hợp lệ.
- [x] FastAPI Dependency `get_optional_current_user` hỗ trợ chế độ Guest (trả về `None` nếu không có token hoặc token vô danh).

**Verification:**
- [x] Test script chạy kiểm thử hash và token encode/decode hoàn tất mà không gặp ngoại lệ.
- [x] Token giải mã ra đúng thông tin đã nạp.

**Dependencies:** Task 1  
**Files likely touched:**
- `src/auth/__init__.py`
- `src/auth/security.py`
- `src/api/dependencies.py`

**Estimated scope:** S (1-2 files)

---

### Task 3: Xây dựng Auth API Endpoints
**Description:** Hiện thực hóa các API router cho phân hệ xác thực: Đăng ký tài khoản mới (`POST /api/auth/register`), Đăng nhập tài khoản (`POST /api/auth/login`), Đăng xuất (`POST /api/auth/logout`), và Lấy thông tin tài khoản hiện tại (`GET /api/auth/me`).

**Acceptance criteria:**
- [x] `POST /api/auth/register`: Validate dữ liệu (username tối thiểu 3 ký tự, password tối thiểu 6 ký tự), ngăn chặn trùng lặp username (trả về 400 nếu đã tồn tại), băm mật khẩu và trả về 201 kèm Access Token.
- [x] `POST /api/auth/login`: Xác thực thông tin đăng nhập, trả về 401 nếu sai tài khoản/mật khẩu, trả về 200 kèm Access Token nếu đúng.
- [x] `GET /api/auth/me`: Yêu cầu Bearer token hợp lệ, trả về thông tin người dùng (`user_id`, `username`, `role`, `created_at`).
- [x] Đăng ký route `/api/auth` vào ứng dụng FastAPI trong `main.py`.

**Verification:**
- [x] Gửi request test curl/python gọi register -> login -> me hoạt động trả về đúng mã HTTP và payload.

**Dependencies:** Task 2  
**Files likely touched:**
- `src/api/schemas.py`
- `src/api/auth_router.py`
- `main.py`

**Estimated scope:** M (3 files)

---

## Checkpoint: Foundation (Sau Tasks 1-3)
- [x] Database MySQL và các bảng đã sẵn sàng
- [x] Hệ thống Auth (Register, Login, Me) hoạt động trơn tru và trả về JWT token
- [x] Sẵn sàng bước sang Phase 2

---

## Phase 2: Chat History & RAG Citations API (Backend Enhancement)

### Task 4: Xây dựng Chat History API Endpoints
**Description:** Xây dựng các API endpoint phục vụ việc quản lý phiên trò chuyện và xem lịch sử chi tiết cho người dùng đã đăng nhập: lấy danh sách các phiên chat (`GET /api/sessions`), lấy chi tiết tin nhắn trong một phiên (`GET /api/sessions/{session_id}`), cập nhật tiêu đề (`PATCH /api/sessions/{session_id}`) và xóa phiên (`DELETE /api/sessions/{session_id}`).

**Acceptance criteria:**
- [x] `GET /api/sessions`: Trả về danh sách phiên của user hiện tại, sắp xếp theo thời gian cập nhật mới nhất (`updated_at DESC`).
- [x] `POST /api/sessions`: Tạo một phiên chat mới với UUID định dạng chuẩn.
- [x] `GET /api/sessions/{session_id}`: Trả về đầy đủ danh sách tin nhắn (`user` và `ai`), bao gồm cả siêu dữ liệu `citations` của AI. Chặn truy cập nếu session không thuộc về user (403/404).
- [x] `DELETE /api/sessions/{session_id}`: Xóa phiên và tự động xóa các tin nhắn liên quan (cascade).

**Verification:**
- [x] Gọi API tạo phiên, thêm tin nhắn, lấy danh sách, kiểm tra trả về đúng cấu trúc JSON.
- [x] Xóa phiên thành công và không còn xuất hiện trong danh sách.

**Dependencies:** Task 3  
**Files likely touched:**
- `src/api/schemas.py`
- `src/api/history_router.py`
- `main.py`

**Estimated scope:** M (3 files)

---

### Task 5: Nâng cấp RAG Pipeline: Rút trích Citations & Xây dựng SSE Streaming Endpoint
**Description:** Tái cấu trúc hàm xử lý retrieval trong `rag_chain.py` để trích xuất đầy đủ siêu dữ liệu nguồn luật (`citations`: tên văn bản, Điều, Khoản, Điểm, nội dung đoạn văn) từ các chunks thu thập được. Nâng cấp endpoint `/api/chat/stream` sang chuẩn Server-Sent Events (SSE) trả về luồng token gõ chữ kèm mảng citations; tự động lưu tin nhắn người dùng và câu trả lời AI vào MySQL nếu có user đăng nhập.

**Acceptance criteria:**
- [x] `build_rag_chain` trích xuất danh sách tài liệu tham chiếu rút gọn (loại bỏ trùng lặp metadata) để gửi kèm câu trả lời.
- [x] Endpoint `POST /api/chat/stream` phát luồng Server-Sent Events chuẩn (`event: session`, `event: delta`, `event: citations`, `event: done`).
- [x] Nếu người dùng đã đăng nhập (kèm Bearer token), tự động tạo phiên mới nếu chưa có và lưu tin nhắn `user` cùng tin nhắn `ai` (kèm JSON `citations`) vào MySQL.
- [x] Nếu là Khách vãng lai (Guest), hệ thống vẫn trả lời và stream trích dẫn đầy đủ bình thường nhưng không ghi DB.

**Verification:**
- [x] Test stream gọi POST `/api/chat/stream` nhận được các event text delta và event citations chứa metadata Điều/Khoản luật hợp lệ.
- [x] Kiểm tra bảng `chat_messages` thấy dữ liệu được lưu sau khi stream kết thúc đối với user đã đăng nhập.

**Dependencies:** Task 4  
**Files likely touched:**
- `src/retrieval/rag_chain.py`
- `src/api/routers.py` hoặc `src/api/chat_router.py`
- `src/api/schemas.py`

**Estimated scope:** M (3 files)

---

## Checkpoint: Core Backend (Sau Tasks 4-5)
- [x] Lịch sử chat được lưu trữ và truy xuất đầy đủ qua API
- [x] RAG Streaming SSE trả về cả nội dung văn bản và nguồn trích dẫn pháp lý chính xác
- [x] Toàn bộ Backend sẵn sàng để kết nối Frontend

---

## Phase 3: Frontend Setup & Design System (React + Tailwind)

### Task 6: Khởi tạo dự án React + Vite và cấu hình Tailwind CSS theo DESIGN.md
**Description:** Cài đặt môi trường Node.js (nếu chưa có), khởi tạo dự án React Single Page App với Vite trong thư mục `frontend/`, thiết lập Tailwind CSS và khai báo toàn bộ Design Tokens theo đúng tài liệu `DESIGN.md` (Aged paper `#faf8f5`, Charcoal `#27251e`, Deep Teal `#016a71`, Pebble `#d1d1cd`, border radius pill `9999px`, font Inter/pplxSans).

**Acceptance criteria:**
- [x] Ứng dụng Vite React được khởi tạo hoàn chỉnh trong `frontend/`.
- [x] Cấu hình Tailwind CSS và file CSS biến số chứa đầy đủ các token màu sắc, typography và border-radius từ `DESIGN.md`.
- [x] File giao diện mẫu hiển thị đúng màu nền canvas `#faf8f5`, thanh tìm kiếm bo viền `12px` và nút pill `9999px`.

**Verification:**
- [x] `npm run build` hoặc `npm run dev` khởi động thành công không lỗi.
- [x] Mở trình duyệt thấy canvas nền `#faf8f5` và các màu sắc chuẩn xác.

**Dependencies:** None (hoặc Task 5)  
**Files likely touched:**
- `frontend/package.json`
- `frontend/vite.config.js`
- `frontend/tailwind.config.js`
- `frontend/src/index.css`
- `frontend/src/App.jsx`

**Estimated scope:** M (4-5 files)

---

### Task 7: Xây dựng API Client, State Management & SSE Reader
**Description:** Tạo cấu hình Axios client với interceptor tự động gắn `Authorization: Bearer <token>` và xử lý lỗi 401. Xây dựng `AuthContext` (quản lý trạng thái login, user info, lưu trữ token `localStorage`) và `ChatContext` (quản lý danh sách phiên, phiên hiện tại, danh sách tin nhắn, trạng thái streaming). Viết utility đọc luồng Server-Sent Events qua `fetch` + `ReadableStream`.

**Acceptance criteria:**
- [x] `api.js`: Tự động đính kèm token từ `localStorage` vào header request; nếu gặp 401 thì tự động clear session.
- [x] `AuthContext`: Cung cấp các hàm `login`, `register`, `logout` và biến trạng thái `user`, `isAuthenticated`.
- [x] `ChatContext`: Cung cấp hàm `fetchSessions`, `selectSession`, `deleteSession`, `sendMessageStream`, và `createNewChat`.
- [x] `sse.js`: Xử lý phân tích luồng SSE từ backend, giải mã các sự kiện `delta`, `citations`, `done` và cập nhật trực tiếp vào message state.

**Verification:**
- [x] Thử nghiệm gọi fetch session và auth từ React context hoạt động ổn định.

**Dependencies:** Task 6  
**Files likely touched:**
- `frontend/src/services/api.js`
- `frontend/src/services/sse.js`
- `frontend/src/context/AuthContext.jsx`
- `frontend/src/context/ChatContext.jsx`

**Estimated scope:** M (4 files)

---

## Checkpoint: Frontend Baseline (Sau Tasks 6-7)
- [x] Ứng dụng React kết nối được với FastAPI backend qua HTTP và SSE
- [x] State auth và state chat sẵn sàng cho các component giao diện

---

## Phase 4: Frontend UI Components & End-to-End Integration

### Task 8: Xây dựng Modal Đăng ký / Đăng nhập (AuthModal)
**Description:** Xây dựng component `AuthModal` hiển thị hộp thoại đăng nhập / đăng ký thanh lịch, bo góc `16px`, nền trắng trên lớp phủ làm mờ nhẹ, cho phép chuyển đổi tab mượt mà giữa "Đăng nhập" và "Đăng ký", kiểm tra tính hợp lệ dữ liệu (validation), hiển thị thông báo lỗi rõ ràng và tích hợp với `AuthContext`.

**Acceptance criteria:**
- [x] Hộp thoại đăng nhập/đăng ký có thể mở từ Sidebar hoặc nút hành động khi người dùng chưa đăng nhập.
- [x] Chuyển đổi tab linh hoạt giữa Form Đăng nhập và Form Đăng ký.
- [x] Kiểm tra lỗi nhập liệu: tên tài khoản rỗng, mật khẩu dưới 6 ký tự, mật khẩu nhập lại không khớp.
- [x] Khi submit thành công: Đóng modal, hiển thị thông báo chào mừng, tự động tải lịch sử chat của user.

**Verification:**
- [x] Thử đăng ký tài khoản mới trực tiếp trên UI -> thành công chuyển sang trạng thái đã đăng nhập.
- [x] Thử đăng nhập tài khoản có sẵn -> nhận diện đúng tên người dùng trên giao diện.

**Dependencies:** Task 7  
**Files likely touched:**
- `frontend/src/components/AuthModal.jsx`
- `frontend/src/App.jsx`

**Estimated scope:** S (1-2 files)

---

### Task 9: Xây dựng Sidebar 220px (Quản lý phiên, Lịch sử, User Profile)
**Description:** Xây dựng thanh điều hướng bên trái rộng 220px theo đúng tài liệu `DESIGN.md`: logo & tiêu đề ứng dụng, nút "Cuộc trò chuyện mới" dạng pill `9999px`, danh sách lịch sử tra cứu nhóm theo thời gian (Hôm nay, 7 ngày trước, Cũ hơn) với hiệu ứng hover và nút xóa phiên, chân sidebar hiển thị User Profile (avatar, username, icon đăng xuất) hoặc nút "Đăng nhập / Đăng ký".

**Acceptance criteria:**
- [x] Chiều rộng sidebar cố định 220px, nền `#faf8f5`, viền phải 1px `#d1d1cd`.
- [x] Nút `+ Cuộc trò chuyện mới` đặt lại trạng thái về màn hình chat trống.
- [x] Các mục lịch sử hiển thị tiêu đề gọn gàng, highlight mục đang chọn bằng nền `#e8e6e1` và điểm nhấn `#016a71`. Icon xóa phiên hiển thị khi hover.
- [x] Khu vực dưới cùng hiển thị tên người dùng và nút Đăng xuất (nếu đã login) hoặc nút Đăng nhập (nếu là Guest).

**Verification:**
- [x] Nhấp chọn các phiên khác nhau: màn hình trung tâm cập nhật đúng nội dung hội thoại của phiên đó.
- [x] Bấm xóa phiên: danh sách lập tức loại bỏ phiên vừa xóa.

**Dependencies:** Task 8  
**Files likely touched:**
- `frontend/src/components/Sidebar.jsx`
- `frontend/src/App.jsx`

**Estimated scope:** S (1-2 files)

---

### Task 10: Xây dựng Vùng Chat Trung tâm 640px (Hero Search, Streaming & Citations Drawer)
**Description:** Xây dựng giao diện khu vực trò chuyện chính (tối đa 640px căn giữa): màn hình khởi đầu hiển thị lời chào và các thẻ gợi ý câu hỏi mẫu; màn hình hội thoại hiển thị bong bóng tin nhắn người dùng và câu trả lời AI với hiệu ứng gõ chữ (streaming text); component `CitationCard` hiển thị danh sách trích dẫn nguồn luật (Nghị định, Điều, Khoản, Trích lục) có thể đóng/mở trực quan; thanh nhập liệu 640px bo góc `12px` với nút gửi tròn `28x28px`.

**Acceptance criteria:**
- [x] Vùng chat giới hạn tối đa 640px căn giữa hoàn hảo trên nền `#faf8f5`.
- [x] Trạng thái chưa chat: Hiển thị logo, tiêu đề "Trợ lý Luật Giao thông Việt Nam" và các câu hỏi mẫu gợi ý (nhấp vào tự động điền và gửi).
- [x] Thanh tìm kiếm: Bo góc `12px`, nền trắng `#ffffff`, viền `1px #d1d1cd`, nút submit tròn `28x28px` `#27251e` có icon mũi tên trắng. Hỗ trợ phím Enter để gửi.
- [x] Luồng streaming hiển thị mượt mà từng từ khi AI trả lời.
- [x] Dưới câu trả lời AI có nút pill "Nguồn tham chiếu (n)". Bấm vào mở rộng danh sách thẻ trích dẫn nguồn luật chi tiết (Điều, Khoản, Nội dung trích đoạn).

**Verification:**
- [x] Đặt câu hỏi thực tế (ví dụ: "Không đội mũ bảo hiểm bị phạt bao nhiêu?"): AI stream câu trả lời từng từ và hiển thị hộp trích dẫn Nghị định 100/2019/NĐ-CP chuẩn xác.
- [x] Kiểm tra trên cả chế độ Guest và chế độ User đã đăng nhập.

**Dependencies:** Task 9  
**Files likely touched:**
- `frontend/src/components/ChatArea.jsx`
- `frontend/src/components/SearchInput.jsx`
- `frontend/src/components/CitationCard.jsx`
- `frontend/src/App.jsx`

**Estimated scope:** M (3-4 files)

---

## Checkpoint: Toàn diện hệ thống (End-to-End Verification)
- [x] Kiểm thử luồng Đăng ký -> Đăng nhập -> Tạo phiên chat -> Hỏi đáp RAG -> Xem trích dẫn Citations -> Đổi phiên chat -> Xóa phiên chat -> Đăng xuất.
- [x] Kiểm thử luồng Guest: Khách vãng lai hỏi đáp bình thường không bị gián đoạn.
- [x] So sánh giao diện với `DESIGN.md`: Đúng bảng màu `#faf8f5`, font Inter/pplxSans, border hairline 1px `#d1d1cd`, nút bo tròn pill `9999px`.
