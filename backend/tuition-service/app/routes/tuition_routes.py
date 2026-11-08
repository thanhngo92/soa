from fastapi import APIRouter
from app.controllers.tuition_controller import (
    get_student_controller,
    get_tuition_by_id_controller,
    pay_controller,
)

router = APIRouter()
router.add_api_route("/students/{mssv}",      get_student_controller,       methods=["GET"])
router.add_api_route("/records/{tuition_id}", get_tuition_by_id_controller, methods=["GET"])
router.add_api_route("/pay",                  pay_controller,               methods=["POST"])
