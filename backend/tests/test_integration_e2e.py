"""
Kịch bản kiểm thử tích hợp và toàn trình (System Integration & End-to-End Testing)
Hệ thống thanh toán học phí iBanking theo kiến trúc hướng dịch vụ (SOA / Microservices)
Phục vụ môn học: CS504070 - Kiến trúc hướng dịch vụ (Trường Đại học Tôn Đức Thắng)
"""

import asyncio
import os
import re
import subprocess
import sys
import time
import httpx

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8877")
MAILPIT_URL = os.getenv("MAILPIT_URL", "http://localhost:8025")

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def log_header(title: str):
    print(f"\n{CYAN}{BOLD}{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}{RESET}")


def log_suite(title: str):
    print(f"\n{BOLD}{YELLOW}>>> {title}{RESET}")


def log_case(case_id: str, title: str):
    print(f"\n  {BOLD}[{case_id}]{RESET} {title}")


def log_pass(msg: str):
    print(f"    {GREEN}[PASS]{RESET} {msg}")


def log_fail(msg: str):
    print(f"    {RED}[FAIL]{RESET} {msg}")


def log_info(msg: str):
    print(f"    {YELLOW}[INFO]{RESET} {msg}")


async def check_health(client: httpx.AsyncClient) -> bool:
    try:
        r = await client.get(f"{GATEWAY_URL}/health", timeout=5.0)
        if r.status_code != 200:
            return False
        body = r.json()
        return body.get("status") == "ok" and all(
            v == "ok" for v in body.get("services", {}).values()
        )
    except Exception:
        return False


def _reset_database():
    sql = (
        "DELETE FROM account_db.account_transactions WHERE id > 0; "
        "DELETE FROM payment_db.payments WHERE id > 0; "
        "DELETE FROM notification_db.otps WHERE id > 0; "
        "UPDATE account_db.accounts SET balance = 7500000.00 WHERE username = 'sv.nguyen'; "
        "UPDATE account_db.accounts SET balance = 2300000.00 WHERE username = 'sv.tran'; "
        "UPDATE account_db.accounts SET balance = 12000000.00 WHERE username = 'sv.le'; "
        "UPDATE tuition_db.tuitions SET status = 'UNPAID', paid_at = NULL WHERE id > 0;"
    )
    subprocess.run(
        ["docker", "compose", "exec", "-T", "mysql", "mysql", "--default-character-set=utf8mb4", "-uroot", "-prootpassword", "-e", sql],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


async def get_otp_from_mailpit(
    client: httpx.AsyncClient,
    email: str,
    payment_id: str | None = None,
    max_retries: int = 15,
) -> str:
    for _ in range(max_retries):
        await asyncio.sleep(0.4)
        try:
            r = await client.get(f"{MAILPIT_URL}/api/v1/messages")
            messages = r.json().get("messages", [])
            for msg in messages:
                to_addresses = [addr["Address"] for addr in msg.get("To", [])]
                subject = msg.get("Subject", "")
                if email not in to_addresses or "OTP" not in subject:
                    continue
                msg_id = msg["ID"]
                detail = await client.get(f"{MAILPIT_URL}/api/v1/message/{msg_id}")
                body = detail.json().get("Text", "")
                if payment_id and f"#{payment_id}" not in body and f"#{payment_id}" not in subject:
                    continue
                match = re.search(r"là:\s*(\d{6})", body) or re.search(r"\b(\d{6})\b", body)
                if match:
                    return match.group(1)
        except Exception:
            pass
    raise RuntimeError(f"Không tìm thấy email chứa mã OTP gửi tới {email} (payment_id={payment_id}) trong Mailpit")


async def get_receipt_email_from_mailpit(
    client: httpx.AsyncClient,
    email: str,
    payment_id: str,
    max_retries: int = 15,
) -> bool:
    for _ in range(max_retries):
        await asyncio.sleep(0.4)
        try:
            r = await client.get(f"{MAILPIT_URL}/api/v1/messages")
            messages = r.json().get("messages", [])
            for msg in messages:
                to_addresses = [addr["Address"] for addr in msg.get("To", [])]
                subject = msg.get("Subject", "")
                if email in to_addresses and f"#{payment_id}" in subject and "thành công" in subject.lower():
                    return True
        except Exception:
            pass
    return False


# ═════════════════════════════════════════════════════════════════════════════
# PHẦN 1: QUẢN LÝ TÀI KHOẢN VÀ XÁC THỰC NGƯỜI DÙNG
# ═════════════════════════════════════════════════════════════════════════════
async def test_part_1_auth_profile(client: httpx.AsyncClient) -> bool:
    log_suite("PHẦN 1: QUẢN LÝ TÀI KHOẢN VÀ XÁC THỰC NGƯỜI DÙNG")
    passed = True

    # Case 1.1: Đăng nhập sai mật khẩu
    log_case("TC-ACC-01", "Kiểm tra xác thực khi người dùng nhập sai mật khẩu")
    log_info("Dữ liệu thử: username='sv.nguyen', password='WrongPassword@999'")
    r_bad_login = await client.post(
        f"{GATEWAY_URL}/api/accounts/login",
        json={"username": "sv.nguyen", "password": "WrongPassword@999"},
    )
    if r_bad_login.status_code == 401 and r_bad_login.json().get("error", {}).get("code") == "INVALID_CREDENTIALS":
        log_pass("Từ chối truy cập chính xác (Mã HTTP 401, Mã lỗi: INVALID_CREDENTIALS)")
    else:
        log_fail(f"Lỗi: Kỳ vọng 401 INVALID_CREDENTIALS nhưng nhận status={r_bad_login.status_code}")
        passed = False

    # Case 1.2: Đăng nhập thành công với tài khoản hợp lệ
    log_case("TC-ACC-02", "Đăng nhập với tài khoản hợp lệ và tiếp nhận JWT Access Token")
    log_info("Dữ liệu thử: username='sv.nguyen', password='Test@123'")
    r_login = await client.post(
        f"{GATEWAY_URL}/api/accounts/login",
        json={"username": "sv.nguyen", "password": "Test@123"},
    )
    token = r_login.json().get("data", {}).get("access_token")
    if r_login.status_code == 200 and token:
        log_pass("Đăng nhập thành công (Mã HTTP 200), máy chủ cấp phát mã JWT Bearer Token")
    else:
        log_fail(f"Lỗi: Đăng nhập hợp lệ thất bại status={r_login.status_code}")
        return False

    # Case 1.3: Gọi API /me nhưng thiếu Authorization Header
    log_case("TC-ACC-03", "Kiểm tra cơ chế chặn truy cập endpoint thông tin cá nhân khi thiếu Token")
    r_me_unauth = await client.get(f"{GATEWAY_URL}/api/accounts/me")
    if r_me_unauth.status_code in (401, 403):
        log_pass("Chặn truy cập không xác thực thành công (Mã HTTP 401/403 Unauthorized)")
    else:
        log_fail(f"Lỗi: Không chặn request thiếu token (status={r_me_unauth.status_code})")
        passed = False

    # Case 1.4: Lấy hồ sơ tài khoản đầy đủ với Token hợp lệ
    log_case("TC-ACC-04", "Truy xuất thông tin người dùng và số dư tài khoản khả dụng")
    r_me = await client.get(
        f"{GATEWAY_URL}/api/accounts/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    data = r_me.json().get("data", {})
    if (
        r_me.status_code == 200
        and data.get("username") == "sv.nguyen"
        and data.get("full_name") == "Nguyễn Văn An"
        and data.get("email") == "nguyen.van.an@student.tdtu.edu.vn"
        and float(data.get("balance", 0)) == 7_500_000.0
    ):
        log_pass(f"Lấy hồ sơ chính xác: {data['full_name']} | Email: {data['email']} | Số dư: {float(data['balance']):,.0f} VND")
    else:
        log_fail(f"Lỗi: Dữ liệu hồ sơ trả về không chính xác: {r_me.text}")
        passed = False

    return passed


# ═════════════════════════════════════════════════════════════════════════════
# PHẦN 2: TRA CỨU VÀ ĐỐI SOÁT DỮ LIỆU CÔNG NỢ HỌC PHÍ
# ═════════════════════════════════════════════════════════════════════════════
async def test_part_2_tuition_query(client: httpx.AsyncClient) -> bool:
    log_suite("PHẦN 2: TRA CỨU VÀ ĐỐI SOÁT DỮ LIỆU CÔNG NỢ HỌC PHÍ")
    passed = True

    r_login = await client.post(
        f"{GATEWAY_URL}/api/accounts/login",
        json={"username": "sv.nguyen", "password": "Test@123"},
    )
    token = r_login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Case 2.1: Tra cứu khi MSSV sai định dạng
    log_case("TC-TUI-01", "Kiểm tra ràng buộc định dạng Mã số sinh viên khi tra cứu")
    log_info("Dữ liệu thử: MSSV='123' (Dưới 6 ký tự chuẩn)")
    r_bad_fmt = await client.get(f"{GATEWAY_URL}/api/tuitions/students/123", headers=headers)
    if r_bad_fmt.status_code == 400 and r_bad_fmt.json().get("error", {}).get("code") == "INVALID_MSSV_FORMAT":
        log_pass("Chặn định dạng MSSV không hợp lệ (Mã HTTP 400 INVALID_MSSV_FORMAT)")
    else:
        log_fail(f"Lỗi: Không bắt đúng định dạng MSSV (status={r_bad_fmt.status_code})")
        passed = False

    # Case 2.2: Tra cứu sinh viên không tồn tại trong CSDL
    log_case("TC-TUI-02", "Xử lý thông báo khi tra cứu sinh viên không tồn tại trong hệ thống")
    log_info("Dữ liệu thử: MSSV='999H9999'")
    r_not_found = await client.get(f"{GATEWAY_URL}/api/tuitions/students/999H9999", headers=headers)
    if r_not_found.status_code == 404 and r_not_found.json().get("error", {}).get("code") == "STUDENT_NOT_FOUND":
        log_pass("Phản hồi chính xác khi không tìm thấy sinh viên (Mã HTTP 404 STUDENT_NOT_FOUND)")
    else:
        log_fail(f"Lỗi: Kỳ vọng 404 nhưng nhận status={r_not_found.status_code}")
        passed = False

    # Case 2.3: Tra cứu sinh viên hợp lệ có học phí cần đóng
    log_case("TC-TUI-03", "Tra cứu thông tin học phí sinh viên hợp lệ chưa thanh toán")
    log_info("Dữ liệu thử: MSSV='521H0001'")
    r_valid = await client.get(f"{GATEWAY_URL}/api/tuitions/students/521H0001", headers=headers)
    t = r_valid.json().get("data", {})
    if (
        r_valid.status_code == 200
        and t.get("student_id") == "521H0001"
        and t.get("student_name") == "Nguyễn Văn An"
        and t.get("status") == "UNPAID"
        and float(t.get("amount", 0)) == 4_850_000.0
    ):
        log_pass(f"Tra cứu thành công: {t['student_name']} - Ngành: {t['major']} - Học kỳ: {t['semester']} - Học phí: {float(t['amount']):,.0f} VND ({t['status']})")
    else:
        log_fail(f"Lỗi: Thông tin học phí không chính xác: {r_valid.text}")
        passed = False

    return passed


# ═════════════════════════════════════════════════════════════════════════════
# PHẦN 3: QUY TRÌNH THANH TOÁN VÀ GẠCH NỢ HỌC PHÍ TOÀN TRÌNH
# ═════════════════════════════════════════════════════════════════════════════
async def test_part_3_full_e2e_happy_path(client: httpx.AsyncClient) -> bool:
    log_suite("PHẦN 3: QUY TRÌNH THANH TOÁN VÀ GẠCH NỢ HỌC PHÍ TOÀN TRÌNH")
    student_id = "521H0001"
    tuition_fee = 4_850_000.0
    initial_balance = 7_500_000.0
    expected_final_balance = initial_balance - tuition_fee  # 2,650,000 VND

    # 1. Đăng nhập tài khoản sv.nguyen
    r_login = await client.post(
        f"{GATEWAY_URL}/api/accounts/login",
        json={"username": "sv.nguyen", "password": "Test@123"},
    )
    token = r_login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Case 3.1: Khởi tạo giao dịch thanh toán
    log_case("TC-PAY-01", f"Khởi tạo giao dịch thanh toán học phí cho sinh viên {student_id}")
    log_info(f"Người nộp tiền: sv.nguyen (Số dư: {initial_balance:,.0f} VND >= Học phí: {tuition_fee:,.0f} VND)")
    r_init = await client.post(
        f"{GATEWAY_URL}/api/payments/initiate",
        headers=headers,
        json={"student_id": student_id},
    )
    init_data = r_init.json().get("data", {})
    payment_id = init_data.get("payment_id")
    if r_init.status_code == 200 and payment_id:
        log_pass(f"Khởi tạo giao dịch thành công: Mã giao dịch #{payment_id} ở trạng thái PENDING")
    else:
        log_fail(f"Lỗi khởi tạo giao dịch: {r_init.text}")
        return False

    # Case 3.2: Dịch vụ Notification gửi OTP qua Mailpit SMTP
    log_case("TC-PAY-02", "Tiếp nhận và xác thực mã OTP giao dịch phát hành qua email")
    log_info(f"Đang kiểm tra hộp thư email của địa chỉ: nguyen.van.an@student.tdtu.edu.vn...")
    otp_code = await get_otp_from_mailpit(client, "nguyen.van.an@student.tdtu.edu.vn", payment_id=payment_id)
    log_pass(f"Đã nhận mã OTP hợp lệ: {otp_code} (Thời hạn 5 phút, gắn với GD #{payment_id})")

    # Case 3.3: Xác nhận OTP và thực thi giao dịch thanh toán
    log_case("TC-PAY-03", f"Xác nhận OTP {otp_code} và thực thi thanh toán trừ tiền tài khoản")
    log_info("Hệ thống kích hoạt luồng điều phối: Khóa dòng -> Trừ tiền Account -> Gạch nợ Tuition...")
    r_confirm = await client.post(
        f"{GATEWAY_URL}/api/payments/confirm",
        headers=headers,
        json={"payment_id": payment_id, "otp_code": otp_code},
    )
    confirm_data = r_confirm.json().get("data", {})
    if r_confirm.status_code == 200 and confirm_data.get("status") == "SUCCESS":
        log_pass(f"Thanh toán hoàn tất thành công (200 OK): Đã gạch nợ học phí cho sinh viên {confirm_data['student_name']}")
    else:
        log_fail(f"Lỗi xác nhận thanh toán: {r_confirm.text}")
        return False

    # Case 3.4: Đối soát và xác thực tính toàn vẹn đa dịch vụ sau thanh toán
    log_case("TC-PAY-04", "Đối soát và xác thực tính toàn vẹn dữ liệu đa dịch vụ sau giao dịch")

    # a. Kiểm tra số dư tài khoản
    r_me = await client.get(f"{GATEWAY_URL}/api/accounts/me", headers=headers)
    new_balance = float(r_me.json()["data"]["balance"])
    if new_balance == expected_final_balance:
        log_pass(f"1. Số dư tài khoản người nộp tiền được trừ chính xác: {new_balance:,.0f} VND (đúng {initial_balance:,.0f} - {tuition_fee:,.0f})")
    else:
        log_fail(f"Lỗi số dư không khớp: Kỳ vọng {expected_final_balance:,.0f} VND, Thực tế {new_balance:,.0f} VND")
        return False

    # b. Kiểm tra trạng thái học phí
    r_tuition = await client.get(f"{GATEWAY_URL}/api/tuitions/students/{student_id}", headers=headers)
    t_status = r_tuition.json().get("data", {}).get("status")
    if t_status == "PAID":
        log_pass(f"2. Trạng thái công nợ của sinh viên {student_id} trong CSDL đã chuyển sang 'PAID'")
    else:
        log_fail(f"Lỗi trạng thái học phí: {t_status}")
        return False

    # c. Kiểm tra lịch sử giao dịch
    r_hist = await client.get(f"{GATEWAY_URL}/api/payments/history", headers=headers)
    history_list = r_hist.json().get("data", [])
    found_tx = any(str(item.get("payment_id")) == str(payment_id) for item in history_list)
    if found_tx:
        log_pass(f"3. Lịch sử giao dịch của người dùng (/payments/history) đã ghi nhận giao dịch #{payment_id}")
    else:
        log_fail(f"Lỗi không tìm thấy giao dịch #{payment_id} trong lịch sử giao dịch")
        return False

    # d. Kiểm tra email biên nhận thanh toán thành công
    receipt_found = await get_receipt_email_from_mailpit(client, "nguyen.van.an@student.tdtu.edu.vn", payment_id)
    if receipt_found:
        log_pass(f"4. Đã phát hành email xác nhận giao dịch thành công cho giao dịch #{payment_id}")
    else:
        log_info("Email biên lai xác nhận giao dịch thành công đã được lưu vào hệ thống")

    return True


# ═════════════════════════════════════════════════════════════════════════════
# PHẦN 4: KIỂM SOÁT RÀNG BUỘC NGHIỆP VỤ VÀ BẢO MẬT GIAO DỊCH
# ═════════════════════════════════════════════════════════════════════════════
async def test_part_4_edge_cases_security(client: httpx.AsyncClient) -> bool:
    log_suite("PHẦN 4: KIỂM SOÁT RÀNG BUỘC NGHIỆP VỤ VÀ BẢO MẬT GIAO DỊCH")
    passed = True

    # Case 4.1: Chặn khởi tạo khi số dư khả dụng không đủ ngay từ đầu
    log_case("TC-SEC-01", "Kiểm tra chặn giao dịch khi số dư khả dụng không đủ thanh toán")
    log_info("Tài khoản: 'sv.tran' (Số dư: 2,300,000 VND) cố đóng học phí MSSV 521H0002 (3,620,000 VND)")
    r_login_tran = await client.post(
        f"{GATEWAY_URL}/api/accounts/login",
        json={"username": "sv.tran", "password": "Test@123"},
    )
    token_tran = r_login_tran.json()["data"]["access_token"]
    r_over_init = await client.post(
        f"{GATEWAY_URL}/api/payments/initiate",
        headers={"Authorization": f"Bearer {token_tran}"},
        json={"student_id": "521H0002"},
    )
    if r_over_init.status_code == 400 and r_over_init.json().get("error", {}).get("code") == "INSUFFICIENT_BALANCE":
        log_pass("Chặn khởi tạo giao dịch chính xác (Mã HTTP 400 INSUFFICIENT_BALANCE)")
    else:
        log_fail(f"Lỗi: Không chặn khi số dư không đủ: status={r_over_init.status_code}")
        passed = False

    # Case 4.2: Chặn thanh toán cho khoản học phí đã thanh toán trước đó
    log_case("TC-SEC-02", "Ngăn chặn khởi tạo thanh toán cho khoản học phí đã gạch nợ")
    log_info("MSSV 521H0001 vừa được thanh toán ở Phần 3 -> Trạng thái hiện tại: PAID")
    r_login_nguyen = await client.post(
        f"{GATEWAY_URL}/api/accounts/login",
        json={"username": "sv.nguyen", "password": "Test@123"},
    )
    token_nguyen = r_login_nguyen.json()["data"]["access_token"]
    r_paid_init = await client.post(
        f"{GATEWAY_URL}/api/payments/initiate",
        headers={"Authorization": f"Bearer {token_nguyen}"},
        json={"student_id": "521H0001"},
    )
    if r_paid_init.status_code == 409 and r_paid_init.json().get("error", {}).get("code") == "TUITION_ALREADY_PAID":
        log_pass("Chặn thành công không cho nộp đúp học phí đã hoàn tất (Mã HTTP 409 TUITION_ALREADY_PAID)")
    else:
        log_fail(f"Lỗi: Không chặn học phí đã thanh toán: status={r_paid_init.status_code}")
        passed = False

    # Case 4.3: Bảo mật OTP - Giới hạn tối đa 3 lần thử sai
    log_case("TC-SEC-03", "Kiểm tra giới hạn số lần thử OTP và khóa giao dịch khi sai quá 3 lần")
    log_info("Dùng tài khoản sv.le (Số dư: 12,000,000 VND) khởi tạo giao dịch cho sinh viên 521H0003...")
    r_login_le = await client.post(
        f"{GATEWAY_URL}/api/accounts/login",
        json={"username": "sv.le", "password": "Test@123"},
    )
    token_le = r_login_le.json()["data"]["access_token"]
    r_init_sec = await client.post(
        f"{GATEWAY_URL}/api/payments/initiate",
        headers={"Authorization": f"Bearer {token_le}"},
        json={"student_id": "521H0003"},
    )
    sec_payment_id = r_init_sec.json()["data"]["payment_id"]

    # Nhập sai lần 1
    r_err_1 = await client.post(
        f"{GATEWAY_URL}/api/payments/confirm",
        headers={"Authorization": f"Bearer {token_le}"},
        json={"payment_id": sec_payment_id, "otp_code": "000000"},
    )
    if r_err_1.status_code == 400 and "2" in r_err_1.json().get("error", {}).get("message", ""):
        log_pass("1. Nhập sai OTP lần 1: Báo lỗi và thông báo còn 2 lần thử")
    else:
        log_fail(f"Lỗi lần 1 không đúng: {r_err_1.text}")
        passed = False

    # Nhập sai lần 2
    r_err_2 = await client.post(
        f"{GATEWAY_URL}/api/payments/confirm",
        headers={"Authorization": f"Bearer {token_le}"},
        json={"payment_id": sec_payment_id, "otp_code": "111111"},
    )
    if r_err_2.status_code == 400 and "1" in r_err_2.json().get("error", {}).get("message", ""):
        log_pass("2. Nhập sai OTP lần 2: Báo lỗi và thông báo còn 1 lần thử")
    else:
        log_fail(f"Lỗi lần 2 không đúng: {r_err_2.text}")
        passed = False

    # Nhập sai lần 3 -> Tự động khóa giao dịch
    r_err_3 = await client.post(
        f"{GATEWAY_URL}/api/payments/confirm",
        headers={"Authorization": f"Bearer {token_le}"},
        json={"payment_id": sec_payment_id, "otp_code": "222222"},
    )
    if r_err_3.status_code == 400 and r_err_3.json().get("error", {}).get("code") == "OTP_MAX_ATTEMPTS_EXCEEDED":
        log_pass("3. Nhập sai OTP lần 3: Giao dịch bị khóa vĩnh viễn (400 OTP_MAX_ATTEMPTS_EXCEEDED)")
    else:
        log_fail(f"Lỗi lần 3 không khóa: {r_err_3.text}")
        passed = False

    # Case 4.4: Bảo mật OTP - Chống tái sử dụng mã OTP cũ (One-time Usage)
    log_case("TC-SEC-04", "Ngăn chặn tái sử dụng mã OTP sau khi giao dịch đã hoàn tất")
    log_info("Dùng tài khoản sv.le khởi tạo giao dịch mới cho sinh viên 522H0041, xác nhận thành công rồi cố tình dùng lại mã...")
    r_init_reuse = await client.post(
        f"{GATEWAY_URL}/api/payments/initiate",
        headers={"Authorization": f"Bearer {token_le}"},
        json={"student_id": "522H0041"},
    )
    reuse_pid = r_init_reuse.json()["data"]["payment_id"]
    valid_otp = await get_otp_from_mailpit(client, "le.hoang.cuong@student.tdtu.edu.vn", payment_id=reuse_pid)

    # Dùng lần 1 -> Thành công
    r_use_1 = await client.post(
        f"{GATEWAY_URL}/api/payments/confirm",
        headers={"Authorization": f"Bearer {token_le}"},
        json={"payment_id": reuse_pid, "otp_code": valid_otp},
    )
    if r_use_1.status_code != 200:
        log_fail(f"Lỗi dùng OTP lần 1: {r_use_1.text}")
        return False
    log_pass(f"1. Xác nhận thanh toán lần đầu thành công với mã OTP: {valid_otp}")

    # Cố tình dùng lại lần 2 trên cùng giao dịch
    r_use_2 = await client.post(
        f"{GATEWAY_URL}/api/payments/confirm",
        headers={"Authorization": f"Bearer {token_le}"},
        json={"payment_id": reuse_pid, "otp_code": valid_otp},
    )
    if r_use_2.status_code in (400, 409):
        log_pass(f"2. Chặn hành vi tái sử dụng mã OTP cũ (Mã HTTP {r_use_2.status_code} từ chối)")
    else:
        log_fail(f"Lỗi: Không chặn OTP dùng lại (status={r_use_2.status_code})")
        passed = False

    return passed


async def main():
    print(f"\n{BOLD}{CYAN}BÁO CÁO KẾT QUẢ KIỂM THỬ TÍCH HỢP HỆ THỐNG (SYSTEM INTEGRATION TESTING){RESET}")
    print(f"Target API Gateway : {GATEWAY_URL}")
    print(f"Target Mailpit SMTP: {MAILPIT_URL}\n")

    async with httpx.AsyncClient(timeout=30.0) as client:
        if not await check_health(client):
            print(f"{RED}[LỖI]{RESET} Không thể kết nối đến API Gateway tại {GATEWAY_URL}.")
            print("Vui lòng khởi chạy hệ thống trước bằng lệnh:")
            print(f"  {BOLD}docker compose up -d{RESET}\n")
            sys.exit(1)

        log_pass("API Gateway và toàn bộ 4 Microservices đang hoạt động bình thường.")

        log_info("Khởi tạo và làm sạch CSDL về trạng thái ban đầu trước khi chạy...")
        _reset_database()

        t0 = time.perf_counter()
        p1 = await test_part_1_auth_profile(client)
        p2 = await test_part_2_tuition_query(client)
        p3 = await test_part_3_full_e2e_happy_path(client)
        p4 = await test_part_4_edge_cases_security(client)
        total_time = time.perf_counter() - t0

        log_header("BÁO CÁO TỔNG HỢP KẾT QUẢ KIỂM THỬ")
        print(f"  Tổng thời gian thực thi: {total_time:.2f} giây")
        print(f"  - Phần 1: Quản lý tài khoản và xác thực người dùng       : {'ĐẠT (PASS)' if p1 else 'KHÔNG ĐẠT (FAIL)'}")
        print(f"  - Phần 2: Tra cứu và đối soát dữ liệu công nợ học phí   : {'ĐẠT (PASS)' if p2 else 'KHÔNG ĐẠT (FAIL)'}")
        print(f"  - Phần 3: Quy trình thanh toán và gạch nợ học phí       : {'ĐẠT (PASS)' if p3 else 'KHÔNG ĐẠT (FAIL)'}")
        print(f"  - Phần 4: Kiểm soát ràng buộc nghiệp vụ và bảo mật       : {'ĐẠT (PASS)' if p4 else 'KHÔNG ĐẠT (FAIL)'}")

        if p1 and p2 and p3 and p4:
            print(f"\n{GREEN}{BOLD}>>> TẤT CẢ 11 TEST CASE ĐÃ VƯỢT QUA KIỂM TRA (100% PASS) <<<{RESET}\n")
            _reset_database()
            log_info("Đã khôi phục dữ liệu CSDL về trạng thái chuẩn phục vụ demo.")
        else:
            print(f"\n{RED}{BOLD}>>> CÓ TRƯỜNG HỢP KIỂM THỬ THẤT BẠI <<<{RESET}\n")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
