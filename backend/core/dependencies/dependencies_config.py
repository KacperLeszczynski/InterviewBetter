from functools import lru_cache

from core import settings
from services import RedisService, EmotionClassifierService, OpenAiService


@lru_cache()
def get_redis_service() -> RedisService:
    return RedisService()


@lru_cache()
def get_emotion_classifier_service() -> EmotionClassifierService:
    return EmotionClassifierService()


@lru_cache()
def get_openai_service() -> OpenAiService:
    return OpenAiService(get_redis_service(), settings.OPENAI_API_KEY)