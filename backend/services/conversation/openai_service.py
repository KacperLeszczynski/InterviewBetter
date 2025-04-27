from services import RedisService
from services.conversation import TranscriptCorrectorService, InterviewConversationService


class OpenAiService:
    def __init__(self, redis_service: RedisService, api_key: str):
        self.redis_service = redis_service
        self.transcript_corrector = TranscriptCorrectorService(api_key)
        self.interview_conversation = InterviewConversationService(redis_service, api_key)

    def correct_transcript(self, transcript: str) -> str:
        return self.transcript_corrector.correct_transcript_with_tech_terms(transcript)

    def start_interview(self, session_id) -> str:
        return self.interview_conversation.start_interview(session_id)

    def add_interview_message(self, session_id: str, message: str):
        self.interview_conversation.add_message(session_id, message)