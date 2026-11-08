from fastapi import APIRouter
from app.controllers.account_controller import login_controller, me_controller, deduct_controller, refund_controller

router = APIRouter()
router.add_api_route("/login",  login_controller,  methods=["POST"])
router.add_api_route("/me",     me_controller,     methods=["GET"])
router.add_api_route("/deduct", deduct_controller, methods=["POST"])
router.add_api_route("/refund", refund_controller, methods=["POST"])
