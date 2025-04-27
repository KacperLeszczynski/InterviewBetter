from functools import lru_cache

from services.emotion_classifier_service import EmotionClassifierService
from services.redis_service import RedisService


@lru_cache()
def get_redis_service() -> RedisService:
    return RedisService()

@lru_cache()
def get_emotion_classifier_service() -> EmotionClassifierService:
    return EmotionClassifierService()