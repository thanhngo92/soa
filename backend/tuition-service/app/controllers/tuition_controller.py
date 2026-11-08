from fastapi import Depends
from app.schemas.tuition_schema import PayTuitionRequest
from app.services.tuition_service import get_tuition, get_tuition_by_id, pay_tuition
from app.middlewares.auth_middleware import verify_internal_token, verify_user_or_internal
from app.utils.response_util import success


async def get_student_controller(mssv: str, _=Depends(verify_user_or_internal)):
    return success(await get_tuition(mssv))


async def get_tuition_by_id_controller(tuition_id: int, _=Depends(verify_user_or_internal)):
    return success(await get_tuition_by_id(tuition_id))


async def pay_controller(body: PayTuitionRequest, _=Depends(verify_internal_token)):
    return success(
        await pay_tuition(
            tuition_id=body.tuition_id,
            mssv=body.student_id,
            semester=body.semester,
            amount=body.amount,
        )
    )
