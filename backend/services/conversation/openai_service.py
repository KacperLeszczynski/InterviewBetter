from typing import Any, Dict

from fastapi import UploadFile

from models import GradedAnswer
from services.conversation.whisper_service import WhisperService
from services.redis_service import RedisService
from services.conversation.transcript_corrector_service import TranscriptCorrectorService
from services.conversation.interview_conversation_service import InterviewConversationService
from services.conversation.sql_service import SqlService


class OpenAiService:

    def __init__(
        self, redis_service: RedisService, sql_service: SqlService, whisper_service: WhisperService, api_key: str
    ) -> None:
        self.redis_service = redis_service
        self.sql_service = sql_service

        self.transcript_corrector = TranscriptCorrectorService(api_key)
        self.interview_conversation = InterviewConversationService(
            redis_service, api_key
        )
        self.whisper_service = whisper_service

    def correct_transcript(self, transcript: str) -> str:
        return self.transcript_corrector.correct_transcript_with_tech_terms(transcript)

    def create_transcript_from_audio(self, audio_path: str) -> str:
        return self.whisper_service.transcribe(audio_path)

    def translate_audio(self, transcript: str) -> str:
        return self.transcript_corrector.correct_transcript_with_tech_terms(transcript)

    def start_interview(
        self, session_id: str, question_type: str
    ) -> Dict[str, Any]:
        questions = self.sql_service.get_random_questions_by_type(question_type)
        self.redis_service.add_questions(session_id, questions)
        return self.interview_conversation.ask_question(session_id)

    def ask_next_question(
        self, session_id: str
    ) -> Dict[str, Any]:
        return self.interview_conversation.ask_question(session_id)

    def add_interview_message(
        self, *, session_id: str, answer: str, emotion: str | None, ideal_answer: str, follow_up_question: str, question: str
    ) -> GradedAnswer:
        return self.interview_conversation.add_message(
            session_id=session_id,
            answer=answer,
            emotion=emotion,
            follow_up_question=follow_up_question,
            question=question,
            ideal_answer=ideal_answer
        )

    def create_final_grade(self, session_id: str):
        return self.interview_conversation.create_final_grade(session_id)
