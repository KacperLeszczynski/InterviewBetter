from fastapi import APIRouter, File, Form, UploadFile, Depends, HTTPException

from core import get_interview_manager
from services.conversation.interview_manager import InterviewManager

router = APIRouter(prefix="/api/interview", tags=["chat"])


@router.post("/start_session")
async def start_session(manager: InterviewManager = Depends(get_interview_manager)):
    session_id = await manager.start_session()
    return {"session_id": session_id}


@router.post("/send_audio")
async def send_audio(
        session_id: str = Form(...),
        transcript: str = Form(...),
        audio: UploadFile = File(...),
        manager: InterviewManager = Depends(get_interview_manager),
):
    await manager.process_audio(session_id, transcript, audio)
    return {"status": "ok"}


@router.post("/start_interview")
async def start_interview(
        session_id: str = Form(...),
        question_type: str = Form(...),
        manager: InterviewManager = Depends(get_interview_manager),
):
    data = manager.start_interview(session_id, question_type)
    return {
        "introduction": data.get("introduction"),
        "question": data.get("question"),
    }


@router.get("/next_question")
async def ask_next_question(
        session_id: str,
        manager: InterviewManager = Depends(get_interview_manager),
):
    data = manager.ask_next_question(session_id)
    return {
        "introduction": data.get("introduction"),
        "question": data.get("question"),
    }


@router.post("/add_message")
async def add_message(
        session_id: str = Form(...),
        manager: InterviewManager = Depends(get_interview_manager),
):
    gradedAnswer = manager.push_transcript_message(session_id)
    return {
        "grade": gradedAnswer.grade,
        "explanation_of_grade": gradedAnswer.explanation_of_grade,
        "follow_up_question": gradedAnswer.follow_up_question
    }


@router.get("/feedback")
async def get_feedback(
        session_id: str,
        manager: InterviewManager = Depends(get_interview_manager),
):
    feedback = manager.get_feedback(session_id)
    return {
        "grade": feedback.grade,
        "feedbacks": feedback.feedback,
    }
