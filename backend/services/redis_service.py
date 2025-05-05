import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Sequence
import random

import ffmpeg
from fastapi import UploadFile
import numpy as np

from models import PredictionModel
from models.final_grade_model import FinalGrade
from redis_client import r

SESSION_TTL = 60 * 30
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class RedisService:
    def __init__(self):
        self.session_ttl = SESSION_TTL
        self.upload_dir = UPLOAD_DIR

    def init_session(self):
        session_id = str(uuid.uuid4())
        r.setex(f"session:{session_id}", self.session_ttl, json.dumps({
            "history": [],
            "emotions": [],
            "messages": [],
            "intro": [],
            "questions": [],
            "question": None,
            "follow_up_question": None,
            "missed_in_a_row": 0,
            "count_followups": 0,
            "feedback": []
        }))
        return session_id

    def add_feedback(self, session_id: str, grade: FinalGrade) -> bool:
        key = f"session:{session_id}"
        if not r.exists(key):
            return False

        session_data = json.loads(r.get(key))
        session_data.setdefault("feedback", [])
        session_data["feedback"].append([grade.feedback, grade.grade])

        r.setex(key, self.session_ttl, json.dumps(session_data))
        return True

    def get_feedback(self, session_id: str) -> list[tuple[str, int]] | None:
        key = f"session:{session_id}"
        if not r.exists(key):
            return None

        session_data = json.loads(r.get(key))
        r.expire(key, self.session_ttl)

        return [(fb, int(gr)) for fb, gr in session_data.get("feedback", [])]

    async def add_to_history(self, session_id: str, transcript: str, audio: UploadFile):
        key = f"session:{session_id}"
        if not r.exists(key):
            return None

        timestamp, filename, filepath = self.prepare_data(session_id)

        with open(filepath, "wb") as f:
            f.write(await audio.read())

        filepath = self.convert_audio(filepath)

        session_data = json.loads(r.get(key))
        session_data["history"].append({
            "timestamp": timestamp,
            "transcript": transcript,
            "audio_url": filepath
        })

        r.setex(key, SESSION_TTL, json.dumps(session_data))

        return filepath

    def add_questions(self, session_id: str, questions: Sequence[str]) -> bool:
        key = f"session:{session_id}"
        if not r.exists(key):
            return False

        session_data = json.loads(r.get(key))

        session_data.setdefault("questions", [])

        if isinstance(questions, str):
            session_data["questions"].append(questions)
        else:
            session_data["questions"].extend(list(questions))

        r.setex(key, self.session_ttl, json.dumps(session_data))
        return True

    def choose_question(self, session_id: str) -> str | None:
        key = f"session:{session_id}"
        if not r.exists(key):
            return None

        session_data = json.loads(r.get(key))
        pool = session_data.get("questions", [])
        if not pool:
            return None

        chosen = random.choice(pool)
        session_data["question"] = chosen

        r.setex(key, self.session_ttl, json.dumps(session_data))
        return chosen

    def get_question(self, session_id: str) -> str | None:
        key = f"session:{session_id}"
        if not r.exists(key):
            return None

        session_data = json.loads(r.get(key))
        r.expire(key, self.session_ttl)
        return session_data.get("question")

    def set_follow_up_question(self, session_id: str, follow_up_question):
        key = f"session:{session_id}"
        if not r.exists(key):
            return None

        session_data = json.loads(r.get(key))
        session_data["follow_up_question"] = follow_up_question

        r.setex(key, self.session_ttl, json.dumps(session_data))

    def get_follow_up_question(self, session_id: str) -> str | None:
        key = f"session:{session_id}"
        if not r.exists(key):
            return None

        session_data = json.loads(r.get(key))
        r.expire(key, self.session_ttl)
        return session_data.get("follow_up_question")

    def delete_current_question(self, session_id: str) -> bool:
        key = f"session:{session_id}"
        if not r.exists(key):
            return False

        session_data = json.loads(r.get(key))
        current = session_data.get("question")
        questions = session_data.get("questions", [])

        if not current or current not in questions:
            return False

        questions.remove(current)
        session_data["question"] = None
        session_data["questions"] = questions

        r.setex(key, self.session_ttl, json.dumps(session_data))
        return True


    def add_transcript_to_history(self, session_id: str, transcript: str, audio_path: str,
                                  timestamp: str) -> str | None:
        key = f"session:{session_id}"
        if not r.exists(key):
            return None

        session_data = json.loads(r.get(key))

        session_data["history"].append({
            "timestamp": timestamp,
            "transcript": transcript,
            "audio_url": audio_path
        })

        r.setex(key, SESSION_TTL, json.dumps(session_data))
        return audio_path


    def incr_followups(self, session_id: str) -> int:
        key = f"session:{session_id}"
        if not r.exists(key):
            return 0

        session_data = json.loads(r.get(key))
        current = int(session_data.get("count_followups", 0)) + 1
        session_data["count_followups"] = current

        r.setex(key, self.session_ttl, json.dumps(session_data))
        return current

    def reset_followups(self, session_id: str) -> None:
        key = f"session:{session_id}"
        if not r.exists(key):
            return

        session_data = json.loads(r.get(key))
        session_data["count_followups"] = 0
        r.setex(key, self.session_ttl, json.dumps(session_data))

    def incr_missed(self, session_id: str) -> int:
        key = f"session:{session_id}"
        if not r.exists(key):
            return 0

        session_data = json.loads(r.get(key))
        current = int(session_data.get("missed_in_a_row", 0)) + 1
        session_data["missed_in_a_row"] = current

        r.setex(key, self.session_ttl, json.dumps(session_data))
        return current

    def reset_missed(self, session_id: str) -> None:
        key = f"session:{session_id}"
        if not r.exists(key):
            return

        session_data = json.loads(r.get(key))
        session_data["missed_in_a_row"] = 0
        r.setex(key, self.session_ttl, json.dumps(session_data))

    def get_counters(self, session_id: str) -> tuple[int, int]:
        key = f"session:{session_id}"
        if not r.exists(key):
            return 0, 0

        session_data = json.loads(r.get(key))
        r.expire(key, self.session_ttl)

        return (
            int(session_data.get("count_followups", 0)),
            int(session_data.get("missed_in_a_row", 0)),
        )

    def add_emotion_to_session(self, session_id: str, predicted_class: PredictionModel):
        key = f"session:{session_id}"
        if not r.exists(key):
            return False

        confidence = float(np.max(predicted_class.confidence))
        if confidence < 0.5:
            return True

        session_data = json.loads(r.get(key))
        session_data["emotions"].append([predicted_class.predicted_class, confidence])

        r.setex(key, self.session_ttl, json.dumps(session_data))
        return True

    def get_emotions(self, session_id: str) -> list[list] | None:
        key = f"session:{session_id}"
        if not r.exists(key):
            return None

        session_data = json.loads(r.get(key))
        r.expire(key, self.session_ttl)
        return session_data.get("emotions", [])

    def reset_emotions(self, session_id: str):
        key = f"session:{session_id}"
        if not r.exists(key):
            return None

        session_data = json.loads(r.get(key))
        session_data["emotions"] = []
        r.setex(key, self.session_ttl, json.dumps(session_data))

    def get_whole_transcript(self, session_id: str) -> str:
        key = f"session:{session_id}"
        if not r.exists(key):
            return ""

        session_data = json.loads(r.get(key))
        history = session_data.get("history", [])
        transcript_list = [entry["transcript"] for entry in history]
        self.reset_history(session_id)

        return " ".join(transcript_list)

    def add_message(self, session_id: str, role: str, content: str) -> None:
        intro_key = self._intro_key(session_id)
        target_key = intro_key if r.llen(intro_key) == 0 else self._msg_key(session_id)
        self._push_message(target_key, role, content)

    def get_all_messages(self, session_id: str) -> List[Dict]:
        return self._read_list(self._intro_key(session_id)) + self._read_list(self._msg_key(session_id))

    def get_history(self, session_id: str) -> str:
        return "\n".join(f"{m['role']}: {m['content']}" for m in self.get_all_messages(session_id))

    def reset_history(self, session_id: str):
        key = f"session:{session_id}"
        if not r.exists(key):
            return None

        session_data = json.loads(r.get(key))
        session_data["history"] = []
        r.setex(key, self.session_ttl, json.dumps(session_data))


    def get_recent_messages(self, session_id: str, limit: int = 5) -> List[Dict]:
        return self.get_all_messages(session_id)[-limit:]

    def clear_messages(self, session_id: str) -> None:
        r.delete(self._msg_key(session_id))
        r.delete(self._intro_key(session_id))

    def finalize_conversation(self, session_id: str) -> Dict | None:
        core_key = f"session:{session_id}"
        if not r.exists(core_key):
            return None

        session_data = json.loads(r.get(core_key))
        convo_snapshot = {
            "ended_at": datetime.utcnow().isoformat(),
            "messages": self.get_all_messages(session_id),
            "history": session_data.get("history", []),
            "emotions": session_data.get("emotions", [])
        }

        r.rpush(f"archive:{session_id}", json.dumps(convo_snapshot))

        session_data["history"] = []
        session_data["emotions"] = []
        session_data["question"] = None
        session_data["messages"] = []
        session_data["follow_up_question"] = None
        session_data["missed_in_a_row"] = 0
        session_data["count_followups"] = 0
        r.setex(core_key, self.session_ttl, json.dumps(session_data))

        self.clear_messages(session_id)

        return convo_snapshot

    def _push_message(self, key: str, role: str, content: str) -> None:
        msg = json.dumps({
            "role": role,
            "content": content,
            "ts": datetime.utcnow().isoformat()
        })
        r.rpush(key, msg)
        r.expire(key, self.session_ttl)

    def _add_intro_message(self, session_id: str, role: str, content: str) -> None:
        self._push_message(self._intro_key(session_id), role, content)

    def _add_normal_message(self, session_id: str, role: str, content: str) -> None:
        self._push_message(self._msg_key(session_id), role, content)

    def _read_list(self, key: str) -> List[Dict]:
        raw = r.lrange(key, 0, -1)
        return [json.loads(m) for m in raw] if raw else []

    def _msg_key(self, session_id: str) -> str:
        return f"session:{session_id}:messages"

    def _intro_key(self, session_id: str) -> str:
        return f"session:{session_id}:intro"

    def convert_audio(self, audio_path):
        wav_path = audio_path.replace(".webm", ".wav")
        ffmpeg.input(audio_path).output(wav_path, ar=16000, ac=1).run(overwrite_output=True)
        os.remove(audio_path)
        return wav_path

    def prepare_data(self, session_id):
        timestamp = datetime.utcnow().isoformat().replace(":", "-").replace(".", "-")
        filename = f"{session_id}_{timestamp}.webm"
        filepath = os.path.join(UPLOAD_DIR, filename)

        return timestamp, filename, filepath
