import json
import logging
import os
import threading

import cv2
import numpy as np

from .. import config

log = logging.getLogger(__name__)


def normalize(vector):
    return vector / np.linalg.norm(vector)


class FaceEngine:
    """YuNet detection and SFace embeddings. OpenCV objects are not thread safe."""

    def __init__(self):
        self.lock = threading.Lock()
        self.detector = cv2.FaceDetectorYN.create(
            f"{config.MODEL_DIR}/face_detection_yunet_2023mar.onnx", "", (320, 320), 0.8, 0.3, 5000
        )
        self.recognizer = cv2.FaceRecognizerSF.create(
            f"{config.MODEL_DIR}/face_recognition_sface_2021dec.onnx", ""
        )

    def embeddings(self, image):
        height, width = image.shape[:2]
        result = []
        with self.lock:
            self.detector.setInputSize((width, height))
            _, faces = self.detector.detect(image)
            for face in [] if faces is None else faces:
                if face[2] < config.MIN_FACE_WIDTH:
                    continue
                aligned = self.recognizer.alignCrop(image, face)
                result.append(normalize(self.recognizer.feature(aligned).flatten()))
        return result


class FaceStore:
    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        self.people = {}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                self.people = {k: np.array(v) for k, v in json.load(f).items()}

    def _save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        temp = f"{self.path}.tmp"
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({k: v.tolist() for k, v in self.people.items()}, f)
        os.replace(temp, self.path)

    def put(self, name, embedding):
        with self.lock:
            self.people[name] = embedding
            self._save()

    def remove(self, name):
        with self.lock:
            found = self.people.pop(name, None) is not None
            if found:
                self._save()
        return found

    def best_match(self, embedding):
        with self.lock:
            scored = [(float(np.dot(embedding, v)), k) for k, v in self.people.items()]
        return max(scored, default=(-1.0, None))


engine = FaceEngine()
store = FaceStore(config.DATA_FILE)


def identify(image):
    """Return auth tags, deduplicated in detection order."""
    embeddings = engine.embeddings(image)
    if not embeddings:
        return ["auth:no-face"]
    tags = []
    for embedding in embeddings:
        score, name = store.best_match(embedding)
        tag = f"auth:{name}" if name and score >= config.MATCH_THRESHOLD else "auth:unknown"
        log.info("face score=%.3f result=%s", score, tag)
        if tag not in tags:
            tags.append(tag)
    return tags
