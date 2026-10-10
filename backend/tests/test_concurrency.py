"""
iBanking Tuition Payment System — Concurrency & Saga Verification Suite
Kiểm thử tự động các kịch bản kiểm soát luồng giao dịch và tranh chấp đồng thời:
  Kịch bản 0: Kiểm soát truy cập trực tiếp và thứ tự quy trình (Workflow Guard)
  Kịch bản 1: Nhiều giao dịch đồng thời trên cùng một tài khoản (Chống thấu chi)
  Kịch bản 2: Nhiều tài khoản cùng thanh toán một khoản học phí (Saga Compensation)
"""

import asyncio
import re
import os
import sys
import time
import httpx

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8877")
MAILPIT_URL = os.getenv("MAILPIT_URL", "http://localhost:8025")
ACCOUNT_URL = os.getenv("ACCOUNT_URL", "http://localhost:8661")
TUITION_URL = os.getenv("TUITION_URL", "http://localhost:8732")
INTERNAL_SERVICE_KEY = os.getenv("INTERNAL_SERVICE_KEY", "super_internal_service_secret_key_2026")

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def log_header(title: str):
    print(f"\n{BOLD}{CYAN}{'=' * 75}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 75}{RESET}")


def log_pass(msg: str):
    print(f"  {GREEN}[PASS]{RESET} {msg}")


def log_fail(msg: str):
    print(f"  {RED}[FAIL]{RESET} {msg}")


def log_info(msg: str):
    print(f"  {YELLOW}[INFO]{RESET} {msg}")


async def check_health(client: httpx.AsyncClient) -> bool:
    try:
        r = await client.get(f"{GATEWAY_URL}/health", timeout=3.0)
        return r.status_code == 200
    except Exception:
        return False


async def login(client: httpx.AsyncClient, username: str, password: str = "Test@123") -> str:
    r = await client.post(
        f"{GATEWAY_URL}/api/accounts/login",
        json={"username": username, "password": password},
    )
    data = r.json()
    if not data.get("success"):
        raise RuntimeError(f"Login failed for {username}: {data}")
    return data["data"]["access_token"]


async def get_profile(client: httpx.AsyncClient, token: str) -> dict:
    r = await client.get(
        f"{GATEWAY_URL}/api/accounts/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    return r.json()["data"]


async def get_otp_from_mailpit(client: httpx.AsyncClient, email: str, max_retries: int = 10) -> str:
    """Truy vấn REST API của Mailpit để lấy mã OTP 6 số mới nhất gửi đến email."""
    for _ in range(max_retries):
        await asyncio.sleep(0.5)
        try:
            r = await client.get(f"{MAILPIT_URL}/api/v1/messages")
            messages = r.json().get("messages", [])
            for msg in messages:
                to_addresses = [addr["Address"] for addr in msg.get("To", [])]
                if email in to_addresses and "OTP" in msg.get("Subject", ""):
                    # Lấy chi tiết nội dung email
                    msg_id = msg["ID"]
                    detail = await client.get(f"{MAILPIT_URL}/api/v1/message/{msg_id}")
                    body = detail.json().get("Text", "")
                    match = re.search(r"(\d{6})", body)
                    if match:
                        return match.group(1)
        except Exception:
            pass
    raise RuntimeError(f"Không tìm thấy email chứa mã OTP gửi tới {email} trong Mailpit")


# ─────────────────────────────────────────────────────────────────────────────
# KỊCH BẢN 0: KIỂM THỬ WORKFLOW GUARD (BẢO VỆ ENDPOINT NỘI BỘ)
# ─────────────────────────────────────────────────────────────────────────────
async def test_scenario_0_workflow_guard(client: httpx.AsyncClient) -> bool:
    log_header("KỊCH BẢN 0: WORKFLOW GUARD (NGĂN CHẶN TRUY CẬP TRỰC TIẾP ENDPOINT NỘI BỘ)")
    log_info("Mục tiêu: Đảm bảo Client bên ngoài không thể gọi trực tiếp các thao tác nội bộ")
    log_info("(Ví dụ: gạch nợ học phí, hoàn tiền tài khoản, tạo OTP trực tiếp qua Gateway)")

    token = await login(client, "user02", "Test@123")
    passed = True

    # 1. Thử gọi trực tiếp /api/tuitions/pay
    r_pay = await client.post(
        f"{GATEWAY_URL}/api/tuitions/pay",
        headers={"Authorization": f"Bearer {token}"},
        json={"student_id": "521H0001", "paid_by": "tester", "transaction_id": "DIRECT_CALL"},
    )
    if r_pay.status_code == 403 and r_pay.json().get("error", {}).get("code") == "WORKFLOW_VIOLATION":
        log_pass("Chặn thành công truy cập trực tiếp /api/tuitions/pay (403 WORKFLOW_VIOLATION)")
    else:
        log_fail(f"Lỗi: Không chặn được /api/tuitions/pay (status={r_pay.status_code})")
        passed = False

    # 2. Thử gọi trực tiếp /api/accounts/refund
    r_refund = await client.post(
        f"{GATEWAY_URL}/api/accounts/refund",
        headers={"Authorization": f"Bearer {token}", "X-Service-Role": "internal"},
        json={"amount": 1_000_000, "transaction_id": "DIRECT_CALL"},
    )
    if r_refund.status_code == 403 and r_refund.json().get("error", {}).get("code") == "WORKFLOW_VIOLATION":
        log_pass("Chặn thành công truy cập trực tiếp /api/accounts/refund (403 WORKFLOW_VIOLATION)")
    else:
        log_fail(f"Lỗi: Không chặn được /api/accounts/refund (status={r_refund.status_code})")
        passed = False

    # 3. Thử gọi trực tiếp /api/notifications/otp/generate
    r_otp = await client.post(
        f"{GATEWAY_URL}/api/notifications/otp/generate",
        json={"payment_id": "999", "email": "test@domain.com"},
    )
    if r_otp.status_code == 403 and r_otp.json().get("error", {}).get("code") == "WORKFLOW_VIOLATION":
        log_pass("Chặn thành công truy cập trực tiếp /api/notifications/otp/generate (403 WORKFLOW_VIOLATION)")
    else:
        log_fail(f"Lỗi: Không chặn được /api/notifications/otp/generate (status={r_otp.status_code})")
        passed = False

    # 4. Thử gọi trực tiếp vào Service nội bộ mà KHÔNG CÓ X-Internal-Token
    try:
        r_internal_no_token = await client.post(
            f"{TUITION_URL}/api/tuitions/pay",
            json={"student_id": "521H0001", "paid_by": "tester", "transaction_id": "UNAUTHORIZED_DIRECT"},
        )
        if r_internal_no_token.status_code == 403:
            log_pass("Chặn thành công truy cập trực tiếp port nội bộ thiếu X-Internal-Token (403 Forbidden)")
        else:
            log_fail(f"Lỗi: Port nội bộ không chặn request thiếu X-Internal-Token (status={r_internal_no_token.status_code})")
            passed = False
    except Exception as exc:
        log_info(f"Port nội bộ đã được cô lập hoàn toàn ({exc}).")

    if passed:
        log_pass("Kiểm thử Workflow Guard thành công: Hệ thống bảo vệ toàn vẹn luồng điều phối!\n")
    return passed


# ─────────────────────────────────────────────────────────────────────────────
# KỊCH BẢN 1: CONCURRENCY TRÊN CÙNG MỘT TÀI KHOẢN
# ─────────────────────────────────────────────────────────────────────────────
async def test_scenario_1_overdraw(client: httpx.AsyncClient):
    log_header("KỊCH BẢN 1: NHIỀU GIAO DỊCH ĐỒNG THỜI TRÊN CÙNG MỘT TÀI KHOẢN")
    log_info("Tài khoản: 'user02' | Số dư ban đầu: 2,300,000 VND")
    log_info("Mục tiêu: Bắn 2 yêu cầu trừ 1,500,000 VND ĐỒNG THỜI (Tổng cần 3,000,000 VND > 2,300,000 VND)")

    token = await login(client, "user02", "Test@123")
    initial_profile = await get_profile(client, token)
    initial_balance = initial_profile["balance"]
    log_info(f"Số dư thực tế trước khi test: {initial_balance:,.0f} VND")

    deduct_amount = 1_500_000.0

    async def send_deduct(req_id: int):
        t0 = time.perf_counter()
        resp = await client.post(
            f"{ACCOUNT_URL}/api/accounts/deduct",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Internal-Token": INTERNAL_SERVICE_KEY,
            },
            json={"amount": deduct_amount, "transaction_id": f"TEST_TX_{req_id}_{int(time.time())}"},
        )
        t_elapsed = (time.perf_counter() - t0) * 1000
        return req_id, resp.status_code, resp.json(), t_elapsed

    # Bắn 2 requests gần như cùng lúc
    results = await asyncio.gather(send_deduct(1), send_deduct(2))

    success_count = 0
    fail_count = 0

    for req_id, status_code, body, elapsed in results:
        if status_code == 200 and body.get("success"):
            success_count += 1
            log_info(f"Request #{req_id}: {GREEN}THÀNH CÔNG (200 OK){RESET} - Thời gian: {elapsed:.1f}ms - Balance mới: {body['data']['balance']:,.0f} VND")
        else:
            fail_count += 1
            err_msg = body.get("error", {}).get("message", "N/A")
            log_info(f"Request #{req_id}: {YELLOW}BỊ CHẶN ({status_code}){RESET} - Lỗi: '{err_msg}' - Thời gian: {elapsed:.1f}ms")

    # Kiểm tra số dư cuối cùng
    final_profile = await get_profile(client, token)
    final_balance = final_profile["balance"]
    log_info(f"Số dư thực tế sau khi test: {final_balance:,.0f} VND")

    # Assertions
    passed = True
    if success_count == 1 and fail_count == 1:
        log_pass("Chính xác 1 request thành công và 1 request bị từ chối do không đủ tiền!")
    else:
        log_fail(f"Không đạt yêu cầu: {success_count} thành công, {fail_count} thất bại")
        passed = False

    if final_balance >= 0 and final_balance == initial_balance - deduct_amount:
        log_pass(f"Số dư tài khoản chính xác ({final_balance:,.0f} VND), tài khoản không bao giờ bị âm!")
    else:
        log_fail(f"Số dư sai lệch: {final_balance:,.0f} VND")
        passed = False

    # Hoàn tiền lại cho tài khoản để sạch dữ liệu
    await client.post(
        f"{ACCOUNT_URL}/api/accounts/refund",
        headers={"Authorization": f"Bearer {token}", "X-Internal-Token": INTERNAL_SERVICE_KEY},
        json={"amount": deduct_amount, "transaction_id": f"CLEANUP_{time.time_ns()}"},
    )
    log_info(f"Đã hoàn trả 1,500,000 VND về tài khoản user02 để reset dữ liệu.\n")
    return passed


# ─────────────────────────────────────────────────────────────────────────────
# KỊCH BẢN 2: NHIỀU TÀI KHOẢN CÙNG THANH TOÁN 1 KHOẢN HỌC PHÍ (SAGA COMPENSATION)
# ─────────────────────────────────────────────────────────────────────────────
async def test_scenario_2_double_payment(client: httpx.AsyncClient):
    log_header("KỊCH BẢN 2: NHIỀU TÀI KHOẢN CÙNG THANH TOÁN 1 KHOẢN HỌC PHÍ (SAGA ROLLBACK)")
    student_id = "523H0089"  # Vo Minh Khoa - 4,720,000 VND
    log_info(f"Mã sinh viên nợ học phí: {student_id} (Số tiền: 4,720,000 VND)")

    # Đảm bảo khoản học phí ở trạng thái UNPAID
    await client.post(
        f"{TUITION_URL}/api/tuitions/revert",
        headers={"X-Internal-Token": INTERNAL_SERVICE_KEY},
        json={"student_id": student_id, "transaction_id": ""},
    )

    # Đăng nhập 2 tài khoản khác nhau
    token_1 = await login(client, "user01", "Test@123")  # Dư 7.5tr
    token_2 = await login(client, "user03", "Test@123")  # Dư 12tr

    p1_before = await get_profile(client, token_1)
    p2_before = await get_profile(client, token_2)

    # Tự động nạp hoàn số dư nếu tài khoản bị trừ từ các lần test trước
    if p1_before["balance"] < 4_720_000:
        diff = 7_500_000.0 - p1_before["balance"]
        await client.post(f"{ACCOUNT_URL}/api/accounts/refund", headers={"Authorization": f"Bearer {token_1}", "X-Internal-Token": INTERNAL_SERVICE_KEY}, json={"amount": diff, "transaction_id": f"PRETEST_RESET_{time.time_ns()}"})
        p1_before = await get_profile(client, token_1)

    if p2_before["balance"] < 4_720_000:
        diff = 12_000_000.0 - p2_before["balance"]
        await client.post(f"{ACCOUNT_URL}/api/accounts/refund", headers={"Authorization": f"Bearer {token_2}", "X-Internal-Token": INTERNAL_SERVICE_KEY}, json={"amount": diff, "transaction_id": f"PRETEST_RESET_{time.time_ns()}"})
        p2_before = await get_profile(client, token_2)

    log_info(f"Tài khoản 1 (user01) số dư ban đầu: {p1_before['balance']:,.0f} VND")
    log_info(f"Tài khoản 2 (user03) số dư ban đầu: {p2_before['balance']:,.0f} VND")

    # Bước 1: Cả 2 cùng initiate giao dịch
    log_info("Cả 2 tài khoản đồng thời gọi POST /api/payments/initiate...")
    r1 = await client.post(
        f"{GATEWAY_URL}/api/payments/initiate",
        headers={"Authorization": f"Bearer {token_1}"},
        json={"student_id": student_id},
    )
    r2 = await client.post(
        f"{GATEWAY_URL}/api/payments/initiate",
        headers={"Authorization": f"Bearer {token_2}"},
        json={"student_id": student_id},
    )

    p1_data = r1.json()["data"]
    p2_data = r2.json()["data"]
    payment_id_1 = p1_data["payment_id"]
    payment_id_2 = p2_data["payment_id"]

    log_info(f"Tạo Payment 1: ID={payment_id_1} | Tạo Payment 2: ID={payment_id_2}")

    # Bước 2: Lấy mã OTP từ Mailpit
    log_info("Đang đọc mã OTP từ Mailpit cho cả 2 người dùng...")
    otp_1 = await get_otp_from_mailpit(client, p1_before["email"])
    otp_2 = await get_otp_from_mailpit(client, p2_before["email"])
    log_info(f"OTP Tài khoản 1: {otp_1} | OTP Tài khoản 2: {otp_2}")

    # Bước 3: Cả 2 cùng bấm xác nhận OTP ĐỒNG THỜI
    log_info(f"{BOLD}ĐANG BẮN 2 REQUEST CONFIRM ĐỒNG THỜI QUA ASYNCIO GATHER...{RESET}")

    async def confirm_payment(user_label: str, token: str, pay_id: str, otp: str):
        t0 = time.perf_counter()
        resp = await client.post(
            f"{GATEWAY_URL}/api/payments/confirm",
            headers={"Authorization": f"Bearer {token}"},
            json={"payment_id": pay_id, "otp_code": otp},
        )
        t_elapsed = (time.perf_counter() - t0) * 1000
        return user_label, resp.status_code, resp.json(), t_elapsed

    results = await asyncio.gather(
        confirm_payment("user01", token_1, payment_id_1, otp_1),
        confirm_payment("user03", token_2, payment_id_2, otp_2),
    )

    success_user = None
    failed_user = None

    for user_label, status_code, body, elapsed in results:
        if status_code == 200 and body.get("success"):
            success_user = user_label
            log_info(f"Người dùng [{user_label}]: {GREEN}THANH TOÁN THÀNH CÔNG (200 OK){RESET} ({elapsed:.1f}ms)")
        else:
            failed_user = user_label
            err_code = body.get("error", {}).get("code", "N/A")
            err_msg = body.get("error", {}).get("message", "N/A")
            log_info(f"Người dùng [{user_label}]: {YELLOW}BỊ TỪ CHỐI ({status_code} {err_code}){RESET} ({elapsed:.1f}ms)")
            log_info(f"Chi tiết thông báo lỗi: '{err_msg}'")

    # Bước 4: Kiểm tra tính nhất quán sau giao dịch
    p1_after = await get_profile(client, token_1)
    p2_after = await get_profile(client, token_2)
    tuition_check = (await client.get(f"{GATEWAY_URL}/api/tuitions/students/{student_id}")).json()["data"]

    log_info(f"Trạng thái học phí MSSV {student_id}: {BOLD}{tuition_check['status']}{RESET}")
    log_info(f"Tài khoản 1 (user01) số dư sau: {p1_after['balance']:,.0f} VND")
    log_info(f"Tài khoản 2 (user03) số dư sau: {p2_after['balance']:,.0f} VND")

    passed = True
    # Kiểm tra chỉ 1 bên thành công
    if success_user and failed_user:
        log_pass("Chính xác chỉ 1 người thanh toán thành công, người còn lại bị từ chối!")
    else:
        log_fail(f"Kết quả không như kỳ vọng: Thành công={success_user}, Thất bại={failed_user}")
        passed = False

    # Kiểm tra Saga Compensation: Người bị từ chối không bị mất tiền
    expected_failed_balance = p1_before["balance"] if failed_user == "user01" else p2_before["balance"]
    actual_failed_balance = p1_after["balance"] if failed_user == "user01" else p2_after["balance"]

    if actual_failed_balance == expected_failed_balance:
        log_pass(f"Cơ chế bù trừ Saga hoạt động hoàn hảo: Người bị từ chối [{failed_user}] đã được tự động hoàn tiền ({actual_failed_balance:,.0f} VND), không bị trừ xu nào!")
    else:
        log_fail(f"Lỗi bù trừ tiền của [{failed_user}]: Ban đầu {expected_failed_balance:,.0f}, Hiện tại {actual_failed_balance:,.0f}")
        passed = False

    # Dọn dẹp dữ liệu sau test để kịch bản có thể chạy lặp lại nhiều lần
    log_info("Dọn dẹp môi trường test (hoàn tiền người thanh toán và revert học phí về UNPAID)...")
    if success_user == "user01":
        await client.post(
            f"{ACCOUNT_URL}/api/accounts/refund",
            headers={"Authorization": f"Bearer {token_1}", "X-Internal-Token": INTERNAL_SERVICE_KEY},
            json={"amount": 4_720_000.0, "transaction_id": f"CLEANUP_{time.time_ns()}"},
        )
    elif success_user == "user03":
        await client.post(
            f"{ACCOUNT_URL}/api/accounts/refund",
            headers={"Authorization": f"Bearer {token_2}", "X-Internal-Token": INTERNAL_SERVICE_KEY},
            json={"amount": 4_720_000.0, "transaction_id": f"CLEANUP_{time.time_ns()}"},
        )

    await client.post(
        f"{TUITION_URL}/api/tuitions/revert",
        headers={"X-Internal-Token": INTERNAL_SERVICE_KEY},
        json={"student_id": student_id, "transaction_id": ""},
    )
    log_info("Đã khôi phục hoàn toàn dữ liệu về trạng thái ban đầu.\n")

    return passed


# ─────────────────────────────────────────────────────────────────────────────
# KỊCH BẢN 3: KIỂM THỬ TÍNH BẤT BIẾN (IDEMPOTENCY-KEY TẠI GATEWAY)
# ─────────────────────────────────────────────────────────────────────────────
async def test_scenario_3_idempotency_key(client: httpx.AsyncClient) -> bool:
    log_header("KỊCH BẢN 3: KIỂM THỬ TÍNH BẤT BIẾN (IDEMPOTENCY-KEY TẠI GATEWAY)")
    log_info("Mục tiêu: Gửi 2 request xác nhận thanh toán với cùng Idempotency-Key:")
    log_info("  - Lần 1: Xử lý bình thường (X-Idempotent-Replay: false).")
    log_info("  - Lần 2: Gateway chặn từ ngoài và trả về response cache (X-Idempotent-Replay: true, X-Cache-Lookup: HIT).")
    log_info("  - Số dư tài khoản chỉ bị trừ ĐÚNG 1 LẦN, không bị trừ đúp.\n")

    token = await login(client, "user03")  # Le Hoang Cuong (12,000,000 VND)
    profile_before = await get_profile(client, token)
    student_id = "522H0041"  # Hoang Thi Yen (3,280,000 VND)

    # 1. Khởi tạo thanh toán
    init_res = await client.post(
        f"{GATEWAY_URL}/api/payments/initiate",
        headers={"Authorization": f"Bearer {token}"},
        json={"student_id": student_id},
    )
    init_data = init_res.json()
    if not init_data.get("success"):
        log_fail(f"Khởi tạo giao dịch thất bại: {init_data}")
        return False

    payment_id = init_data["data"]["payment_id"]
    log_pass(f"Khởi tạo giao dịch #{payment_id} thành công.")

    # 2. Lấy OTP từ Mailpit
    otp = await get_otp_from_mailpit(client, profile_before["email"])
    log_pass(f"Đã nhận OTP từ Mailpit: {otp}")

    idempotency_key = f"test-idemp-key-{payment_id}-{time.time_ns()}"

    # 3. Gửi Request Lần 1 kèm Idempotency-Key
    log_info(f"Gửi request Lần 1 với Header Idempotency-Key: {idempotency_key}...")
    res_1 = await client.post(
        f"{GATEWAY_URL}/api/payments/confirm",
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": idempotency_key,
        },
        json={"payment_id": payment_id, "otp_code": otp},
    )

    data_1 = res_1.json()
    if not data_1.get("success"):
        log_fail(f"Lần 1 thanh toán thất bại: {data_1}")
        return False
    log_pass(f"Lần 1 thành công: HTTP {res_1.status_code}, Replay={res_1.headers.get('x-idempotent-replay', 'false')}")

    # 4. Gửi Request Lần 2 với CÙNG Idempotency-Key (Mô phỏng mạng gửi lại hoặc user bấm đúp)
    log_info("Gửi request Lần 2 (trùng lặp) với CÙNG Header Idempotency-Key...")
    res_2 = await client.post(
        f"{GATEWAY_URL}/api/payments/confirm",
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": idempotency_key,
        },
        json={"payment_id": payment_id, "otp_code": otp},
    )

    data_2 = res_2.json()
    replay_header = res_2.headers.get("x-idempotent-replay")
    cache_header = res_2.headers.get("x-cache-lookup")

    passed = True
    if res_2.status_code == 200 and data_2.get("success") and replay_header == "true":
        log_pass(f"Lần 2 thành công tuyệt đối từ Gateway Cache: HTTP {res_2.status_code}, Cache-Lookup={cache_header}, Replay={replay_header}")
    else:
        log_fail(f"Lần 2 thất bại hoặc không nhận diện được Idempotency: HTTP {res_2.status_code}, Body={data_2}")
        passed = False

    # 5. Kiểm tra số dư chỉ bị trừ 1 lần
    profile_after = await get_profile(client, token)
    expected_balance = profile_before["balance"] - 3_280_000.0
    actual_balance = profile_after["balance"]

    if actual_balance == expected_balance:
        log_pass(f"Số dư tài khoản chính xác: {actual_balance:,.0f} VND (Chỉ bị trừ 1 lần duy nhất 3,280,000 VND).")
    else:
        log_fail(f"Số dư bị sai lệch: Kỳ vọng {expected_balance:,.0f} VND, Thực tế {actual_balance:,.0f} VND")
        passed = False

    # 6. Dọn dẹp
    log_info("Dọn dẹp môi trường test Kịch bản 3...")
    await client.post(
        f"{ACCOUNT_URL}/api/accounts/refund",
        headers={"Authorization": f"Bearer {token}", "X-Internal-Token": INTERNAL_SERVICE_KEY},
        json={"amount": 3_280_000.0, "transaction_id": f"CLEANUP_{time.time_ns()}"},
    )
    await client.post(
        f"{TUITION_URL}/api/tuitions/revert",
        headers={"X-Internal-Token": INTERNAL_SERVICE_KEY},
        json={"student_id": student_id, "transaction_id": ""},
    )
    log_info("Đã hoàn tiền và khôi phục nợ học phí về UNPAID thành công.\n")

    return passed


async def main():
    print(f"\n{BOLD}{CYAN}KIỂM THỬ TỰ ĐỘNG CONCURRENCY & TRANSACTION CONSISTENCY (SOA iBanking){RESET}")
    print(f"Target API Gateway: {GATEWAY_URL}")
    print(f"Target Mailpit     : {MAILPIT_URL}\n")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Kiểm tra hệ thống đã chạy chưa
        if not await check_health(client):
            print(f"{RED}[LỖI]{RESET} Không thể kết nối đến API Gateway tại {GATEWAY_URL}.")
            print("Vui lòng khởi chạy hệ thống trước bằng lệnh:")
            print(f"  {BOLD}docker compose up -d{RESET}\n")
            sys.exit(1)

        log_pass("API Gateway và các Microservices đang hoạt động bình thường.")

        p0 = await test_scenario_0_workflow_guard(client)
        p1 = await test_scenario_1_overdraw(client)
        p2 = await test_scenario_2_double_payment(client)
        p3 = await test_scenario_3_idempotency_key(client)

        log_header("TỔNG KẾT KẾT QUẢ KIỂM THỬ")
        if p0 and p1 and p2 and p3:
            print(f"\n{GREEN}{BOLD}>>> TẤT CẢ CÁC BÀI KIỂM THỬ ĐÃ HOÀN TẤT THÀNH CÔNG (PASS 4/4) <<<{RESET}\n")
        else:
            print(f"\n{RED}{BOLD}>>> CÓ BÀI KIỂM THỬ KHÔNG THÀNH CÔNG <<<{RESET}\n")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
