from fastapi import Depends
from app.schemas.tuition_schema import PayTuitionRequest, RevertTuitionRequest
from app.services.tuition_service import get_tuition, pay_tuition, revert_tuition
from app.middlewares.auth_middleware import verify_internal_token
from app.utils.response_util import success


async def get_student_controller(mssv: str):
    return success(await get_tuition(mssv))


async def pay_controller(body: PayTuitionRequest, _=Depends(verify_internal_token)):
    return success(await pay_tuition(body.student_id, body.paid_by, body.transaction_id, body.semester))


async def revert_controller(body: RevertTuitionRequest, _=Depends(verify_internal_token)):
    return success(await revert_tuition(body.student_id, body.transaction_id, body.semester))
