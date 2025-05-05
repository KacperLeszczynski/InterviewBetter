from functools import lru_cache

from core import settings
from services import (
    RedisService,
    EmotionClassifierService,
    OpenAiService,
    SqlService,
    InterviewManager, ChromaService, ConversationController, WhisperService
)


@lru_cache()
def get_redis_service() -> RedisService:
    return RedisService()


@lru_cache()
def get_sql_service() -> SqlService:
    return SqlService()


@lru_cache()
def get_emotion_classifier_service() -> EmotionClassifierService:
    return EmotionClassifierService()


@lru_cache()
def get_openai_service() -> OpenAiService:
    print(settings.openai_api_key)
    return OpenAiService(
        get_redis_service(), get_sql_service(), get_whisper_service(), settings.openai_api_key
    )


@lru_cache()
def get_chroma_service() -> ChromaService:
    return ChromaService()

@lru_cache()
def get_whisper_service() -> WhisperService:
    return WhisperService()

@lru_cache()
def get_conversation_controller() -> ConversationController:
    return ConversationController(get_redis_service())

@lru_cache()
def get_interview_manager() -> InterviewManager:
    return InterviewManager(
        get_redis_service(),
        get_openai_service(),
        get_emotion_classifier_service(),
        get_chroma_service(),
        get_conversation_controller()
    )
