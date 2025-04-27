from fastapi import APIRouter, File, Form, UploadFile, Depends, HTTPException

from dependencies.dependencies_config import get_redis_service, get_emotion_classifier_service
from services.emotion_classifier_service import EmotionClassifierService
from services.redis_service import RedisService

router = APIRouter(prefix="/api/interview", tags=["chat"])


@router.post("/start_session")
async def start_session(redis_service: RedisService = Depends(get_redis_service)):
    session_id = redis_service.init_session()
    return {"session_id": session_id}


@router.post("/send_audio")
async def send_audio(
        session_id: str = Form(...),
        transcript: str = Form(...),
        audio: UploadFile = File(...),
        redis_service: RedisService = Depends(get_redis_service),
        emotion_classifier_service: EmotionClassifierService = Depends(get_emotion_classifier_service)
):
    file_path = await redis_service.add_to_history(session_id, transcript, audio)
    if file_path is None:
        raise HTTPException(status_code=404, detail="Session not found")

    prediction = emotion_classifier_service.predict(file_path)
    is_ok = redis_service.add_emotion_to_session(session_id, prediction)

    if not is_ok:
        raise HTTPException(status_code=404, detail="Error while adding predicted class")

    return {"status": "ok"}
