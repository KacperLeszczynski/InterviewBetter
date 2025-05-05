from typing import Optional

from sentence_transformers import CrossEncoder

from services.redis_service import RedisService


class ConversationController:
    def __init__(
            self,
            redis_service: RedisService,
            model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
            threshold: float = -1,
    ):
        self.redis = redis_service
        self.reranker = CrossEncoder(model_name)
        self.threshold = threshold

    def register_assistant(self, session_id: str, follow_up_q: str) -> None:
        if follow_up_q == "DONE":
            self.redis.reset_missed(session_id)
            self.redis.reset_followups(session_id)
            self.redis.set_follow_up_question(session_id, None)
        else:
            self.redis.set_follow_up_question(session_id, follow_up_q)
            self.redis.reset_missed(session_id)
            self.redis.incr_followups(session_id)

    def register_user(self, session_id: str, user_ans: str) -> bool:
        count, missed = self.redis.get_counters(session_id)
        pending: Optional[str] = self.redis.get_follow_up_question(session_id)

        if count >= 5:
            self.redis.reset_followups(session_id)
            return True

        if pending and not self._is_related(user_ans, pending):
            missed = self.redis.incr_missed(session_id)
        elif pending:
            self.redis.reset_missed(session_id)
            self.redis.set_follow_up_question(session_id, None)
            missed = 0

        if missed >= 2:
            self.redis.reset_missed(session_id)
            self.redis.set_follow_up_question(session_id, None)
            return True
        return False

    def _is_related(self, user_ans: str, follow_up_q: str) -> bool:
        score = float(self.reranker.predict([(follow_up_q, user_ans)])[0])
        return score >= self.threshold
