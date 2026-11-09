from fastapi import APIRouter, Depends
from app.core import success, verify_internal_token, verify_user_or_internal
from app.tuitions.schemas import PayTuitionRequest
from app.tuitions.service import get_tuition, get_tuition_by_id, pay_tuition

router = APIRouter()


@router.get("/students/{mssv}")
async def get_student_endpoint(mssv: str, _=Depends(verify_user_or_internal)):
    return success(await get_tuition(mssv))


@router.get("/records/{tuition_id}")
async def get_tuition_by_id_endpoint(tuition_id: int, _=Depends(verify_user_or_internal)):
    return success(await get_tuition_by_id(tuition_id))


@router.post("/pay")
async def pay_endpoint(body: PayTuitionRequest, _=Depends(verify_internal_token)):
    return success(
        await pay_tuition(
            tuition_id=body.tuition_id,
            mssv=body.student_id,
            semester=body.semester,
            amount=body.amount,
        )
    )
