from fastapi import APIRouter
from app.controllers.payment_controller import initiate_controller, confirm_controller, history_controller

router = APIRouter()
router.add_api_route("/initiate", initiate_controller, methods=["POST"])
router.add_api_route("/confirm",  confirm_controller,  methods=["POST"])
router.add_api_route("/history",  history_controller,  methods=["GET"])
