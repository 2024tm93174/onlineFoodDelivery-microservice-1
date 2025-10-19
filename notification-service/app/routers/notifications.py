from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/notifications", tags=["notifications"])

class NotifIn(BaseModel):
    order_id: int
    type: str

@router.post("", status_code=202)
def notify(payload: NotifIn):
    # For demo, just log to stdout; in real service we'd persist and send email/SMS
    print(f"[NOTIFY] order={payload.order_id} type={payload.type}")
    return {"accepted": True}
