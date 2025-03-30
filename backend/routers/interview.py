from fastapi import APIRouter, File, Form, UploadFile, Depends, HTTPException

from services.redis_service import RedisService

router = APIRouter(prefix="/api/interview", tags=["chat"])


def get_redis_service() -> RedisService:
    return RedisService()


@router.post("/start_session")
async def start_session(redis_service: RedisService = Depends(get_redis_service)):
    session_id = redis_service.init_session()
    return {"session_id": session_id}


@router.post("/send_audio")
async def send_audio(
        session_id: str = Form(...),
        transcript: str = Form(...),
        audio: UploadFile = File(...),
        redis_service: RedisService = Depends(get_redis_service)
):
    is_ok = await redis_service.add_to_history(session_id, transcript, audio)
    if not is_ok:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"status": "ok"}
