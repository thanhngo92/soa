# Frontend Application

Giao diện người dùng của hệ thống thanh toán học phí iBanking, xây dựng bằng React 18, Vite, Tailwind CSS, Shadcn UI và Axios.

* **Port:** `3000`
* **API Gateway Base URL:** `http://localhost:8877/api`

---

## 1. Các Chức Năng Giao Diện

1. **Đăng nhập (`/login`):** Xác thực tài khoản người dùng, lưu trữ JWT Bearer Token và điều hướng vào trang thanh toán.
2. **Tra cứu & Thanh toán học phí (`/`):**
   * Hiển thị thông tin chủ tài khoản và số dư khả dụng (`GET /api/accounts/me`).
   * Tự động tra cứu công nợ học phí khi nhập mã số sinh viên hợp lệ (`GET /api/tuitions/students/{mssv}`).
   * Kiểm tra điều kiện số dư, xác nhận điều khoản và khởi tạo giao dịch thanh toán (`POST /api/payments/initiate`).
3. **Xác thực OTP (`OtpModal`):**
   * Đồng hồ đếm ngược thời gian hiệu lực 5 phút.
   * Hỗ trợ nhập lại tối đa 3 lần khi sai mã OTP và tự động khóa ô nhập khi giao dịch vượt quá số lần thử hoặc hết hạn.
   * Hiển thị biên lai điện tử (`ReceiptModal`) và cập nhật lại số dư ngay sau khi thanh toán thành công.
4. **Lịch sử giao dịch (`/history`):** Hiển thị danh sách các giao dịch đã thực hiện kèm trạng thái (`SUCCESS`, `PROCESSING`, `PENDING`, `FAILED`) và nguyên nhân lỗi chi tiết.

---

## 2. Cấu Trúc Thư Mục

```text
frontend/
|-- index.html
|-- vite.config.js
|-- package.json
|-- tailwind.config.js
|-- postcss.config.js
|-- README.md
+-- src/
    |-- main.jsx                 # Khởi tạo React DOM
    |-- App.jsx                  # Định tuyến React Router & Navbar
    |-- index.css                # Cấu hình Tailwind CSS
    |-- lib/
    |   |-- api.js               # Cấu hình Axios instance & JWT Interceptors
    |   +-- utils.js             # Hàm tiện ích gộp class CSS
    |-- utils/
    |   |-- formatters.js        # Định dạng tiền tệ VND và thời gian chuẩn GMT+7
    |   +-- validators.js        # Kiểm tra định dạng MSSV và mã OTP 6 chữ số
    |-- services/
    |   |-- authService.js       # Gọi API /accounts/login, /accounts/me
    |   |-- tuitionService.js    # Gọi API /tuitions/students/{mssv}
    |   +-- paymentService.js    # Gọi API /payments/initiate, /confirm, /history
    |-- context/
    |   +-- AuthContext.jsx      # Quản lý trạng thái đăng nhập và thông tin tài khoản
    |-- hooks/
    |   |-- useAuth.js           # Hook truy cập AuthContext
    |   +-- useCountdown.js      # Hook đếm ngược 300 giây cho OTP
    |-- components/
    |   |-- Navbar.jsx           # Thanh điều hướng
    |   |-- ProtectedRoute.jsx   # Bảo vệ các route yêu cầu đăng nhập
    |   |-- OtpModal.jsx         # Hộp thoại xác thực OTP
    |   |-- ReceiptModal.jsx     # Hộp thoại biên nhận giao dịch
    |   +-- ui/                  # Các thành phần giao diện cơ sở
    +-- pages/
        |-- LoginPage.jsx        # Trang đăng nhập
        |-- TuitionPaymentPage.jsx # Trang tra cứu và thanh toán học phí
        +-- HistoryPage.jsx      # Trang lịch sử giao dịch
```

---

## 3. Hướng Dẫn Chạy Môi Trường Phát Triển

```bash
cd frontend
npm install
npm run dev
```

* Giao diện Web: [http://localhost:3000](http://localhost:3000)
* Hộp thư Mailpit (xem mã OTP): [http://localhost:8025](http://localhost:8025)
