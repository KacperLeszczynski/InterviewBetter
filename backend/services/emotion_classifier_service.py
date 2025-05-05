from collections import defaultdict

import librosa
import numpy as np
from sklearn.preprocessing import LabelEncoder
import os
import keras

from models.prediction_model import PredictionModel

MODEL_DIR = "notebooks/audio"


class EmotionClassifierService:
    def __init__(self, model_path="model_v3.keras", classes_path="classes.npy"):
        self.model_path = os.path.join(MODEL_DIR, model_path)
        self.classes_path = os.path.join(MODEL_DIR, classes_path)
        self.model = None
        self.le = None


    def _load(self):
        if self.model is None:
            self.model = keras.models.load_model(self.model_path)
        if self.le is None:
            self.le = LabelEncoder()
            self.le.classes_ = np.load(self.classes_path, allow_pickle=True)

    def get_mel_spectrogram(self, file_path, sr=16000, n_mels=128, duration=4, apply_aug=False, augmenter=None):
        y, sr = librosa.load(file_path, sr=sr, duration=duration)

        if len(y) < sr * duration:
            y = np.pad(y, (0, sr * duration - len(y)))

        if apply_aug and augmenter:
            y = augmenter(samples=y, sample_rate=sr)

        mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=n_mels, )
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

        if mel_spec_db.shape[1] < 128:
            mel_spec_db = np.pad(mel_spec_db, ((0, 0), (0, 128 - mel_spec_db.shape[1])))
        elif mel_spec_db.shape[1] > 128:
            mel_spec_db = mel_spec_db[:, :128]

        return mel_spec_db

    def predict(self, file_path):
        self._load()
        mel_spectrogram = self.get_mel_spectrogram(file_path)
        mel_spectrogram = (mel_spectrogram - mel_spectrogram.mean()) / mel_spectrogram.std()
        mel_spectrogram = mel_spectrogram[np.newaxis, ..., np.newaxis]

        predictions = self.model.predict(mel_spectrogram)

        predicted_index = int(np.argmax(predictions))
        predicted_label = self.le.inverse_transform([predicted_index])[0]
        confidence = float(np.max(predictions))

        return PredictionModel(predicted_class=predicted_label, confidence=confidence)

    @staticmethod
    def get_overall_emotion(emotions: list[list]) -> str | None:
        scores: dict[str, float] = defaultdict(float)
        for emotion_class, conf in emotions:
            scores[emotion_class] += float(conf)

        if len(scores.items()) == 0:
            return 'neutral'

        overall = max(scores.items(), key=lambda p: p[1])[0]
        return overall
