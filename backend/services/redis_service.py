import json
import os
import uuid
from datetime import datetime
import ffmpeg
from fastapi import UploadFile
import numpy as np

from models.prediction_model import PredictionModel
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
            "emotions": []
        }))
        return session_id

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

    def add_emotion_to_session(self, session_id: str, predicted_class: PredictionModel):
        key = f"session:{session_id}"
        if not r.exists(key):
            return False

        confidence = float(np.max(predicted_class.confidence))
        if confidence < 0.7:
            return True

        session_data = json.loads(r.get(key))
        session_data["emotions"].append([predicted_class.predicted_class, confidence])

        r.setex(key, self.session_ttl, json.dumps(session_data))
        return True

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
