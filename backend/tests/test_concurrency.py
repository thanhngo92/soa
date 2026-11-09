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
ACCOUNT_URL = os.getenv("ACCOUNT_URL", "http://localhost:8661")
TUITION_URL = os.getenv("TUITION_URL", "http://localhost:8732")
MAILPIT_URL = os.getenv("MAILPIT_URL", "http://localhost:8025")
INTERNAL_SERVICE_KEY = os.getenv("INTERNAL_SERVICE_KEY", "super_internal_service_secret_key_2026")

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def log_header(title: str):
    print(f"\n{CYAN}{BOLD}{'=' * 75}")
    print(f"  {title}")
    print(f"{'=' * 75}{RESET}")


def log_pass(msg: str):
    print(f"  {GREEN}[PASS]{RESET} {msg}")


def log_fail(msg: str):
    print(f"  {RED}[FAIL]{RESET} {msg}")


def log_info(msg: str):
    print(f"  {YELLOW}[INFO]{RESET} {msg}")


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


async def get_otp_from_mailpit(
    client: httpx.AsyncClient,
    email: str,
    payment_id: str | None = None,
    max_retries: int = 12,
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
                if payment_id and f"#{payment_id}" not in subject:
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


def _reset_tuition_and_test_data(student_ids: list[str] | tuple[str, ...]):
    sids_sql = ", ".join(f"'{sid}'" for sid in student_ids)
    sql = (
        f"DELETE FROM account_db.account_transactions WHERE reference_id IN "
        f"(SELECT CAST(id AS CHAR) FROM payment_db.payments WHERE tuition_id IN "
        f"(SELECT id FROM tuition_db.tuitions WHERE student_id IN ({sids_sql}))); "
        f"DELETE FROM payment_db.payments WHERE tuition_id IN "
        f"(SELECT id FROM tuition_db.tuitions WHERE student_id IN ({sids_sql})); "
        f"UPDATE tuition_db.tuitions SET status = 'UNPAID', paid_at = NULL "
        f"WHERE student_id IN ({sids_sql});"
    )
    subprocess.run(
        ["docker", "compose", "exec", "-T", "mysql", "mysql", "-P8552", "-uroot", "-prootpassword", "-e", sql],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


async def _ensure_balance(client: httpx.AsyncClient, token: str, target_balance: float):
    profile = await get_profile(client, token)
    current = float(profile["balance"])
    if current < target_balance:
        diff = target_balance - current
        await client.post(
            f"{ACCOUNT_URL}/api/accounts/refund",
            headers={"Authorization": f"Bearer {token}", "X-Internal-Token": INTERNAL_SERVICE_KEY},
            json={"account_id": profile["id"], "amount": diff, "transaction_id": f"RESET_{time.time_ns()}"},
        )
    elif current > target_balance:
        diff = current - target_balance
        await client.post(
            f"{ACCOUNT_URL}/api/accounts/deduct",
            headers={"Authorization": f"Bearer {token}", "X-Internal-Token": INTERNAL_SERVICE_KEY},
            json={"account_id": profile["id"], "amount": diff, "transaction_id": f"RESET_{time.time_ns()}"},
        )


# [Rubric Tiêu chí 2: Kiến trúc Microservices - Kiểm thử Workflow Guard]
# - Nghiệp vụ: Chặn mọi truy cập trực tiếp từ client ngoài vào endpoint nội bộ (pay, refund, otp).
# - Kỹ thuật: Gateway trả về 403 WORKFLOW_VIOLATION; Port nội bộ từ chối khi thiếu X-Internal-Token.
async def test_scenario_0_workflow_guard(client: httpx.AsyncClient) -> bool:
    log_header("KỊCH BẢN 0: WORKFLOW GUARD (NGĂN CHẶN TRUY CẬP TRỰC TIẾP ENDPOINT NỘI BỘ)")
    log_info("Mục tiêu: Đảm bảo Client bên ngoài không thể gọi trực tiếp các thao tác nội bộ")
    log_info("(Ví dụ: gạch nợ học phí, hoàn tiền tài khoản, tạo OTP trực tiếp qua Gateway)")

    token = await login(client, "sv.tran", "Test@123")
    passed = True

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

    r_otp = await client.post(
        f"{GATEWAY_URL}/api/notifications/otp/generate",
        json={"payment_id": "999", "email": "test@domain.com"},
    )
    if r_otp.status_code == 403 and r_otp.json().get("error", {}).get("code") == "WORKFLOW_VIOLATION":
        log_pass("Chặn thành công truy cập trực tiếp /api/notifications/otp/generate (403 WORKFLOW_VIOLATION)")
    else:
        log_fail(f"Lỗi: Không chặn được /api/notifications/otp/generate (status={r_otp.status_code})")
        passed = False

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


# [Rubric Tiêu chí 6: Kiểm soát tranh chấp đồng thời - Chống thấu chi số dư (E2E Overdraw Protection)]
# - Nghiệp vụ: 1 tài khoản xác nhận đồng thời 2 giao dịch có tổng tiền vượt quá số dư khả dụng.
# - Kỹ thuật: Khóa bi quan FOR UPDATE tại Account Service đảm bảo chính xác 1 GD thành công, 1 GD từ chối.
async def test_scenario_1_overdraw(client: httpx.AsyncClient):
    log_header("KỊCH BẢN 1: NHIỀU GIAO DỊCH ĐỒNG THỜI TRÊN CÙNG MỘT TÀI KHOẢN (CHỐNG THẤU CHI E2E)")
    student_a = "521H0001"
    student_b = "521H0002"

    log_info("Tài khoản: 'sv.nguyen' | Số dư khả dụng: 7,500,000 VND")
    log_info("Khởi tạo 2 giao dịch đóng học phí hợp lệ riêng lẻ nhưng tổng vượt số dư:")
    log_info(f"  - Giao dịch A: MSSV {student_a} (4,850,000 VND <= 7,500,000 VND)")
    log_info(f"  - Giao dịch B: MSSV {student_b} (3,620,000 VND <= 7,500,000 VND)")
    log_info("  -> Tổng 2 giao dịch = 8,470,000 VND > 7,500,000 VND!")

    _reset_tuition_and_test_data((student_a, student_b))

    token = await login(client, "sv.nguyen", "Test@123")
    await _ensure_balance(client, token, 7_500_000.0)
    initial_profile = await get_profile(client, token)
    initial_balance = float(initial_profile["balance"])
    log_info(f"Số dư thực tế trước khi test: {initial_balance:,.0f} VND")

    r_init_a = await client.post(
        f"{GATEWAY_URL}/api/payments/initiate",
        headers={"Authorization": f"Bearer {token}"},
        json={"student_id": student_a},
    )
    r_init_b = await client.post(
        f"{GATEWAY_URL}/api/payments/initiate",
        headers={"Authorization": f"Bearer {token}"},
        json={"student_id": student_b},
    )

    pay_id_a = r_init_a.json()["data"]["payment_id"]
    pay_id_b = r_init_b.json()["data"]["payment_id"]
    log_info(f"Đã khởi tạo qua Gateway -> Payment A: #{pay_id_a} ({student_a}) | Payment B: #{pay_id_b} ({student_b})")

    otp_a = await get_otp_from_mailpit(client, initial_profile["email"], payment_id=pay_id_a)
    otp_b = await get_otp_from_mailpit(client, initial_profile["email"], payment_id=pay_id_b)
    log_info(f"OTP Payment #{pay_id_a}: {otp_a} | OTP Payment #{pay_id_b}: {otp_b}")

    log_info(f"{BOLD}ĐANG BẮN 2 REQUEST POST /api/payments/confirm ĐỒNG THỜI TRÊN CÙNG TÀI KHOẢN...{RESET}")

    async def confirm_tx(label: str, pay_id: str, otp: str):
        t0 = time.perf_counter()
        resp = await client.post(
            f"{GATEWAY_URL}/api/payments/confirm",
            headers={"Authorization": f"Bearer {token}"},
            json={"payment_id": pay_id, "otp_code": otp},
        )
        t_elapsed = (time.perf_counter() - t0) * 1000
        return label, resp.status_code, resp.json(), t_elapsed

    results = await asyncio.gather(
        confirm_tx(f"Payment #{pay_id_a} ({student_a})", pay_id_a, otp_a),
        confirm_tx(f"Payment #{pay_id_b} ({student_b})", pay_id_b, otp_b),
    )

    success_count = 0
    fail_count = 0
    deducted_amount = 0.0
    paid_student = None

    for label, status_code, body, elapsed in results:
        if status_code == 200 and body.get("success"):
            success_count += 1
            deducted_amount = float(body["data"]["amount"])
            paid_student = body["data"]["student_id"]
            log_info(
                f"{label}: {GREEN}THÀNH CÔNG (200 OK){RESET} - Thời gian: {elapsed:.1f}ms "
                f"- Đã trừ: {deducted_amount:,.0f} VND"
            )
        else:
            fail_count += 1
            err_code = body.get("error", {}).get("code", "N/A")
            err_msg = body.get("error", {}).get("message", "N/A")
            log_info(
                f"{label}: {YELLOW}BỊ CHẶN ({status_code} {err_code}){RESET} - Lỗi: '{err_msg}' - Thời gian: {elapsed:.1f}ms"
            )

    final_profile = await get_profile(client, token)
    final_balance = float(final_profile["balance"])
    log_info(f"Số dư thực tế sau khi test: {final_balance:,.0f} VND")

    passed = True
    if success_count == 1 and fail_count == 1:
        log_pass("Chính xác 1 giao dịch thành công và 1 giao dịch bị từ chối do không đủ số dư khả dụng!")
    else:
        log_fail(f"Không đạt yêu cầu: {success_count} thành công, {fail_count} thất bại")
        passed = False

    if final_balance >= 0 and final_balance == initial_balance - deducted_amount:
        log_pass(f"Số dư tài khoản chính xác ({final_balance:,.0f} VND), chống thấu chi tuyệt đối!")
    else:
        log_fail(f"Số dư sai lệch: {final_balance:,.0f} VND")
        passed = False

    await _ensure_balance(client, token, 7_500_000.0)
    _reset_tuition_and_test_data((student_a, student_b))
    log_info("Đã khôi phục số dư tài khoản sv.nguyen và trạng thái học phí về ban đầu.\n")
    return passed


# [Rubric Tiêu chí 6: Saga Rollback & Bù trừ giao dịch - 2 tài khoản thanh toán cùng 1 học phí]
# - Nghiệp vụ: 2 người cùng đóng học phí cho 1 sinh viên tại cùng thời điểm.
# - Kỹ thuật: 1 người thành công gạch nợ; người còn lại bị 409 conflict và được Saga hoàn tiền tự động 100%.
async def test_scenario_2_double_payment(client: httpx.AsyncClient):
    log_header("KỊCH BẢN 2: NHIỀU TÀI KHOẢN CÙNG THANH TOÁN 1 KHOẢN HỌC PHÍ (SAGA ROLLBACK)")
    student_id = "523H0089"
    log_info(f"Mã sinh viên nợ học phí: {student_id} (Số tiền: 4,720,000 VND)")

    _reset_tuition_and_test_data((student_id,))

    token_1 = await login(client, "sv.nguyen", "Test@123")
    token_2 = await login(client, "sv.le", "Test@123")

    await _ensure_balance(client, token_1, 7_500_000.0)
    await _ensure_balance(client, token_2, 12_000_000.0)

    p1_before = await get_profile(client, token_1)
    p2_before = await get_profile(client, token_2)

    log_info(f"Tài khoản 1 (sv.nguyen) số dư ban đầu: {p1_before['balance']:,.0f} VND")
    log_info(f"Tài khoản 2 (sv.le) số dư ban đầu: {p2_before['balance']:,.0f} VND")

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

    log_info("Đang đọc mã OTP từ Mailpit cho cả 2 người dùng...")
    otp_1 = await get_otp_from_mailpit(client, p1_before["email"], payment_id=payment_id_1)
    otp_2 = await get_otp_from_mailpit(client, p2_before["email"], payment_id=payment_id_2)
    log_info(f"OTP Tài khoản 1 (#{payment_id_1}): {otp_1} | OTP Tài khoản 2 (#{payment_id_2}): {otp_2}")

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
        confirm_payment("sv.nguyen", token_1, payment_id_1, otp_1),
        confirm_payment("sv.le", token_2, payment_id_2, otp_2),
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

    p1_after = await get_profile(client, token_1)
    p2_after = await get_profile(client, token_2)
    tuition_check = (
        await client.get(
            f"{GATEWAY_URL}/api/tuitions/students/{student_id}",
            headers={"Authorization": f"Bearer {token_1}"},
        )
    ).json()["data"]

    log_info(f"Trạng thái học phí MSSV {student_id}: {BOLD}{tuition_check['status']}{RESET}")
    log_info(f"Tài khoản 1 (sv.nguyen) số dư sau: {p1_after['balance']:,.0f} VND")
    log_info(f"Tài khoản 2 (sv.le) số dư sau: {p2_after['balance']:,.0f} VND")

    passed = True
    if success_user and failed_user:
        log_pass("Chính xác chỉ 1 người thanh toán thành công, người còn lại bị từ chối!")
    else:
        log_fail(f"Kết quả không như kỳ vọng: Thành công={success_user}, Thất bại={failed_user}")
        passed = False

    expected_failed_balance = p1_before["balance"] if failed_user == "sv.nguyen" else p2_before["balance"]
    actual_failed_balance = p1_after["balance"] if failed_user == "sv.nguyen" else p2_after["balance"]

    if actual_failed_balance == expected_failed_balance:
        log_pass(
            f"Cơ chế bù trừ Saga hoạt động hoàn hảo: Người bị từ chối [{failed_user}] "
            f"đã được tự động hoàn tiền ({actual_failed_balance:,.0f} VND), không bị trừ xu nào!"
        )
    else:
        log_fail(f"Lỗi bù trừ tiền của [{failed_user}]: Ban đầu {expected_failed_balance:,.0f}, Hiện tại {actual_failed_balance:,.0f}")
        passed = False

    log_info("Dọn dẹp môi trường test (hoàn tiền người thanh toán và revert học phí về UNPAID)...")
    await _ensure_balance(client, token_1, 7_500_000.0)
    await _ensure_balance(client, token_2, 12_000_000.0)
    _reset_tuition_and_test_data((student_id,))
    log_info("Đã khôi phục hoàn toàn dữ liệu về trạng thái ban đầu.\n")

    return passed


# [Rubric Tiêu chí 6: Kiểm thử tính bất biến (Idempotency Key tại Gateway)]
# - Nghiệp vụ: Chặn double-click khi mạng lag; gửi lại request với cùng key nhận response từ cache.
# - Kỹ thuật: Gateway nhận diện Idempotency-Key, trả X-Idempotent-Replay: true, tài khoản chỉ bị trừ tiền đúng 1 lần.
async def test_scenario_3_idempotency_key(client: httpx.AsyncClient) -> bool:
    log_header("KỊCH BẢN 3: KIỂM THỬ TÍNH BẤT BIẾN (IDEMPOTENCY-KEY TẠI GATEWAY)")
    log_info("Mục tiêu: Gửi 2 request xác nhận thanh toán với cùng Idempotency-Key:")
    log_info("  - Lần 1: Xử lý bình thường (X-Idempotent-Replay: false).")
    log_info("  - Lần 2: Gateway chặn từ ngoài và trả về response cache (X-Idempotent-Replay: true, X-Cache-Lookup: HIT).")
    log_info("  - Số dư tài khoản chỉ bị trừ ĐÚNG 1 LẦN, không bị trừ đúp.\n")

    student_id = "522H0041"
    _reset_tuition_and_test_data((student_id,))

    token = await login(client, "sv.le")
    await _ensure_balance(client, token, 12_000_000.0)
    profile_before = await get_profile(client, token)

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

    otp = await get_otp_from_mailpit(client, profile_before["email"], payment_id=payment_id)
    log_pass(f"Đã nhận OTP từ Mailpit: {otp}")

    idempotency_key = f"test-idemp-key-{payment_id}-{time.time_ns()}"

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

    profile_after = await get_profile(client, token)
    expected_balance = profile_before["balance"] - 3_280_000.0
    actual_balance = profile_after["balance"]

    if actual_balance == expected_balance:
        log_pass(f"Số dư tài khoản chính xác: {actual_balance:,.0f} VND (Chỉ bị trừ 1 lần duy nhất 3,280,000 VND).")
    else:
        log_fail(f"Số dư bị sai lệch: Kỳ vọng {expected_balance:,.0f} VND, Thực tế {actual_balance:,.0f} VND")
        passed = False

    log_info("Dọn dẹp môi trường test Kịch bản 3...")
    await _ensure_balance(client, token, 12_000_000.0)
    _reset_tuition_and_test_data((student_id,))
    log_info("Đã hoàn tiền và khôi phục nợ học phí về UNPAID thành công.\n")

    return passed


async def main():
    target_scenario = sys.argv[1].strip() if len(sys.argv) > 1 else "all"

    print(f"\n{BOLD}{CYAN}KIỂM THỬ TỰ ĐỘNG CONCURRENCY & TRANSACTION CONSISTENCY (SOA iBanking){RESET}")
    print(f"Target API Gateway: {GATEWAY_URL}")
    print(f"Target Mailpit     : {MAILPIT_URL}\n")

    async with httpx.AsyncClient(timeout=30.0) as client:
        if not await check_health(client):
            print(f"{RED}[LỖI]{RESET} Không thể kết nối đến API Gateway tại {GATEWAY_URL}.")
            print("Vui lòng khởi chạy hệ thống trước bằng lệnh:")
            print(f"  {BOLD}docker compose up -d{RESET}\n")
            sys.exit(1)

        log_pass("API Gateway và các Microservices đang hoạt động bình thường.")

        results = []
        if target_scenario in ["0", "all"]:
            results.append(("Kịch bản 0", await test_scenario_0_workflow_guard(client)))
        if target_scenario in ["1", "all"]:
            results.append(("Kịch bản 1", await test_scenario_1_overdraw(client)))
        if target_scenario in ["2", "all"]:
            results.append(("Kịch bản 2", await test_scenario_2_double_payment(client)))
        if target_scenario in ["3", "all"]:
            results.append(("Kịch bản 3", await test_scenario_3_idempotency_key(client)))

        log_header("TỔNG KẾT KẾT QUẢ KIỂM THỬ")
        all_passed = all(r[1] for r in results)
        if all_passed:
            passed_count = len([r for r in results if r[1]])
            print(f"\n{GREEN}{BOLD}CÁC BÀI KIỂM THỬ ĐÃ HOÀN TẤT THÀNH CÔNG (PASS {passed_count}/{len(results)}){RESET}\n")
        else:
            print(f"\n{RED}{BOLD}CÓ BÀI KIỂM THỬ KHÔNG THÀNH CÔNG{RESET}\n")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
