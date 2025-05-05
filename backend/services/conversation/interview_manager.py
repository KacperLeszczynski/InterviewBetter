from typing import Any

from fastapi import HTTPException, UploadFile

from models import GradedAnswer
from models.final_grade_model import FinalGrade
from services.redis_service import RedisService
from services.emotion_classifier_service import EmotionClassifierService
from services.conversation.openai_service import OpenAiService
from services.conversation.chroma_service import ChromaService
from services.conversation.conversation_controller import ConversationController


class InterviewManager:
    """Coordinates the whole interview flow (session ↔ audio ↔ emotions ↔ OpenAI)."""

    def __init__(
        self,
        redis_service: RedisService,
        openai_service: OpenAiService,
        emotion_classifier: EmotionClassifierService,
        chroma_service: ChromaService,
        conversation_controller: ConversationController,
    ) -> None:
        self.redis = redis_service
        self.openai = openai_service
        self.emotion_cls = emotion_classifier
        self.chroma = chroma_service
        self.conversation_controller = conversation_controller

    async def start_session(self) -> str:
        return self.redis.init_session()

    async def process_audio(
        self, session_id: str, transcript: str, audio: UploadFile
    ) -> None:
        # corrected = self.openai.correct_transcript(transcript)
        timestamp, filename, filepath = self.redis.prepare_data(session_id)

        with open(filepath, "wb") as f:
            f.write(await audio.read())

        converted_filepath = self.redis.convert_audio(filepath)
        transcript = self.openai.create_transcript_from_audio(converted_filepath)

        file_path = self.redis.add_transcript_to_history(
            session_id, transcript, converted_filepath, timestamp
        )

        if file_path is None:
            raise HTTPException(status_code=404, detail="Session not found")

        prediction = self.emotion_cls.predict(file_path)
        if not self.redis.add_emotion_to_session(session_id, prediction):
            raise HTTPException(status_code=500, detail="Cannot save emotion data")

    def start_interview(self, session_id: str, question_type: str) -> dict[str, Any]:
        return self.openai.start_interview(session_id, question_type)

    def ask_next_question(self, session_id: str) -> dict[str, Any]:
        return self.openai.ask_next_question(session_id)

    def push_transcript_message(self, session_id: str) -> GradedAnswer:
        transcript = self.redis.get_whole_transcript(session_id)
        emotions = self.redis.get_emotions(session_id)
        self.redis.reset_emotions(session_id)
        question = self.redis.get_question(session_id)
        follow_up_question = self.redis.get_follow_up_question(session_id)
        overall_emotion = self.emotion_cls.get_overall_emotion(emotions)
        ideal_answer = self.chroma.get_ideal_document(question=question, user_answer=transcript)

        self.conversation_controller.register_assistant(session_id, question)

        if self.conversation_controller.register_user(session_id, transcript):
            final_grade: FinalGrade = self.openai.create_final_grade(session_id)
            self.redis.add_feedback(session_id, final_grade)
            self.redis.delete_current_question(session_id)
            self.redis.finalize_conversation(session_id)

            return GradedAnswer(grade=0, explanation_of_grade="DONE", follow_up_question="DONE")

        graded: GradedAnswer = self.openai.add_interview_message(
            session_id=session_id,
            answer=transcript,
            emotion=overall_emotion,
            ideal_answer=ideal_answer,
            follow_up_question=follow_up_question,
            question=question,
        )

        self.redis.set_follow_up_question(session_id, graded.follow_up_question)

        return graded
