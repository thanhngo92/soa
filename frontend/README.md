# Frontend Application — Tài Liệu Triển Khai Chi Tiết (Member 3)

> **Dự án:** iBanking Tuition Payment System (SOA)  
> **Người phụ trách:** **Member 3** (Payment Service + API Gateway + Frontend Integration)  
> **Công nghệ:** React 18 • Vite • Tailwind CSS • Shadcn UI • Axios • Lucide React  
> **Port:** `3659`  
> **API Gateway Base URL:** `http://localhost:8877/api`

---

## 1. Mục Tiêu & Phạm Vi Công Việc (Member 3)

Frontend cung cấp giao diện người dùng hiện đại, bảo mật và trực quan để thực hiện quy trình thanh toán học phí đại học:
1. **Đăng nhập iBanking (`/login`)**: Nhập username/password, lưu trữ JWT Bearer Token trong `localStorage` và `AuthContext`.
2. **Trang chủ & Tra cứu học phí (`/`)**:
   * Hiển thị thông tin sinh viên đăng nhập & số dư khả dụng (`GET /api/accounts/me`).
   * Tìm kiếm học phí theo MSSV (`GET /api/tuitions/students/{mssv}`).
   * Nút "Khởi tạo thanh toán" kích hoạt `POST /api/payments/initiate` và mở Modal nhập OTP.
3. **Modal Nhập OTP (`OtpModal`)**:
   * Đếm ngược thời gian hiệu lực OTP (5 phút / 300 giây).
   * Nhập 6 chữ số OTP và bấm xác nhận (`POST /api/payments/confirm`).
   * Tự động hiển thị `ReceiptModal` (Biên nhận thanh toán) khi thành công.
4. **Lịch sử giao dịch (`/history`)**: Hiển thị bảng danh sách các giao dịch thanh toán kèm trạng thái (`SUCCESS`, `FAILED`, `PENDING`).

---

## 2. Luồng Dữ Liệu & Kiến Trúc Frontend

```text
page ──> component ──> utils ──> hooks ──> context ──> services ──> API Gateway (:8877)
```

---

## 3. Cấu Trúc Thư Mục Chi Tiết

```text
frontend/
├── index.html
├── vite.config.js               # Dev server port 3659, cấu hình alias '@' -> '/src'
├── package.json
├── tailwind.config.js           # Theme, bảng màu, animation
├── postcss.config.js
├── README.md                    # Tài liệu hướng dẫn này
│
└── src/
    ├── main.jsx                 # Entrypoint khởi tạo React DOM
    ├── App.jsx                  # Root Component: React Router & AuthProvider
    ├── index.css                # Tailwind directives & CSS variables
    │
    ├── lib/                     # Utilities hạ tầng
    │   ├── api.js               # Axios instance cấu hình Base URL http://localhost:8877/api & Interceptors
    │   └── utils.js             # Hàm cn (clsx + twMerge)
    │
    ├── utils/                   # Hàm tiện ích thuần túy
    │   ├── formatters.js        # Định dạng tiền tệ VND, ngày tháng
    │   └── validators.js        # Kiểm tra định dạng form
    │
    ├── services/                # Tầng gọi API Gateway
    │   ├── authService.js       # Gọi /api/accounts/login, /api/accounts/me
    │   ├── tuitionService.js    # Gọi /api/tuitions/students/{mssv}
    │   └── paymentService.js    # Gọi /api/payments/initiate, /confirm, /history
    │
    ├── context/                 # Quản lý State toàn cục
    │   └── AuthContext.jsx      # Quản lý token, user profile, login/logout
    │
    ├── hooks/                   # Custom Hooks
    │   ├── useAuth.js           # Hook truy xuất AuthContext
    │   └── useCountdown.js      # Hook đếm ngược thời gian hết hạn OTP (5 phút)
    │
    ├── components/              # UI Components
    │   ├── Navbar.jsx           # Thanh điều hướng (Hiển thị tên người dùng, số dư, nút Logout)
    │   ├── ProtectedRoute.jsx   # Guard bảo vệ route cần đăng nhập
    │   ├── OtpModal.jsx         # Hộp thoại nhập OTP 6 số
    │   ├── ReceiptModal.jsx     # Hộp thoại biên lai thanh toán thành công
    │   │
    │   └── ui/                  # Shadcn UI primitives (button, input, card, badge, dialog, separator)
    │
    └── pages/                   # Các trang giao diện
        ├── LoginPage.jsx        # Trang đăng nhập
        ├── TuitionPaymentPage.jsx # Trang tra cứu và thanh toán học phí
        └── HistoryPage.jsx      # Trang xem lịch sử giao dịch
```

---

## 4. Tài Khoản & Dữ Liệu Mẫu Để Kiểm Thử Giao Diện

### 4.1 Tài khoản Đăng nhập:
| Username | Password | Tên sinh viên | Số dư khả dụng |
|:---|:---|:---|:---|
| `user01` | `Test@123` | Nguyen Van An | **7,500,000 VND** |
| `user02` | `Test@123` | Tran Thi Bao | **2,300,000 VND** |
| `user03` | `Test@123` | Le Hoang Cuong | **12,000,000 VND** |

### 4.2 Mã Số Sinh Viên (MSSV) cần tra cứu học phí:
* `521H0001` (4,850,000 VND - `UNPAID`)
* `521H0002` (3,620,000 VND - `UNPAID`)
* `521H0003` (5,130,000 VND - `UNPAID`)
* `522H0017` (3,975,000 VND - `UNPAID`)

---

## 5. Hướng Dẫn Cài Đặt & Chạy Frontend

```bash
# 1. Di chuyển vào thư mục frontend
cd frontend

# 2. Cài đặt các gói thư viện
npm install

# 3. Khởi chạy Vite Dev Server (Port 3659)
npm run dev
```

* Mở trình duyệt truy cập: **[http://localhost:3659](http://localhost:3659)**
* Xem mã OTP nhận được tại Web Mailpit: **[http://localhost:8025](http://localhost:8025)**

---

## 6. Bảng Kiểm Tra Nghiệm Thu (Checklist Cho Member 3)

- [ ] Đăng nhập thành công với tài khoản mẫu $\rightarrow$ Lưu JWT token vào `localStorage` và chuyển đến trang chính.
- [ ] Navbar hiển thị đúng Họ tên sinh viên và Số dư tài khoản được format tiền tệ VND.
- [ ] Tra cứu MSSV hợp lệ hiển thị đúng bảng thông tin hóa đơn (Họ tên, Ngành, Học kỳ, Học phí, Trạng thái).
- [ ] Bấm "Thanh toán" mở Modal OTP, đồng thời Mailpit nhận được email chứa OTP 6 số.
- [ ] Đếm ngược 5 phút trong OTP modal hoạt động chính xác.
- [ ] Nhập đúng OTP $\rightarrow$ Hiển thị Modal Biên lai thành công, số dư trên Navbar tự động cập nhật giảm.
- [ ] Nhập sai OTP $\rightarrow$ Hiển thị thông báo lỗi trực quan màu đỏ.
- [ ] Trang Lịch sử (`/history`) tải và hiển thị danh sách các giao dịch đã thực hiện.
