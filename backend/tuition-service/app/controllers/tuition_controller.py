from app.schemas.tuition_schema import PayTuitionRequest, RevertTuitionRequest
from app.services.tuition_service import get_tuition, pay_tuition, revert_tuition
from app.utils.response_util import success


async def get_student_controller(mssv: str):
    return success(await get_tuition(mssv))


async def pay_controller(body: PayTuitionRequest):
    return success(await pay_tuition(body.student_id, body.paid_by, body.transaction_id))


async def revert_controller(body: RevertTuitionRequest):
    return success(await revert_tuition(body.student_id, body.transaction_id))
