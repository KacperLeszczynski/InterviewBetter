from fastapi import APIRouter, File, Form, UploadFile, Depends, HTTPException

from core import get_redis_service, get_emotion_classifier_service, get_openai_service
from services import RedisService, EmotionClassifierService, OpenAiService

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
        emotion_classifier_service: EmotionClassifierService = Depends(get_emotion_classifier_service),
        openai_service: OpenAiService = Depends(get_openai_service)
):
    corrected_transcript = openai_service.correct_transcript(transcript)
    file_path = await redis_service.add_to_history(session_id, corrected_transcript, audio)
    if file_path is None:
        raise HTTPException(status_code=404, detail="Session not found")

    prediction = emotion_classifier_service.predict(file_path)
    is_ok = redis_service.add_emotion_to_session(session_id, prediction)

    if not is_ok:
        raise HTTPException(status_code=404, detail="Error while adding predicted class")

    return {"status": "ok"}

@router.post("/introduction_message")
async def start_interview(
        session_id: str = Form(...),
        openai_service: OpenAiService = Depends(get_openai_service)
):
    introduction = openai_service.start_interview(session_id)
    return {"introduction": introduction}



@router.post("/add_message")
async def add_message(
        session_id: str = Form(...),
        redis_service: RedisService = Depends(get_redis_service),
        openai_service: OpenAiService = Depends(get_openai_service)
):
    transcript = redis_service.get_whole_transcript(session_id)
    openai_service.add_interview_message(session_id, transcript)