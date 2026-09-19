from fastapi import APIRouter
from app.controllers.notification_controller import generate_otp_controller, verify_otp_controller, send_success_email_controller

router = APIRouter()
router.add_api_route("/otp/generate",  generate_otp_controller,      methods=["POST"])
router.add_api_route("/otp/verify",    verify_otp_controller,         methods=["POST"])
router.add_api_route("/email/success", send_success_email_controller, methods=["POST"])
