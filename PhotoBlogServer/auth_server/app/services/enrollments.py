"""Pulls enrollment requests from Django, which cannot reach this server directly."""
import json
import logging
import time

import cv2
import numpy as np

from .. import config
from .faces import engine, normalize, store
from .upstream import upstream

log = logging.getLogger(__name__)
PATH = "/api_root/Enrollment/"


def _finish(item_id, status, message):
    body = json.dumps({"status": status, "message": message}).encode()
    upstream.request("PATCH", f"{PATH}{item_id}/", body, "application/json")
    log.info("enrollment id=%s status=%s %s", item_id, status, message)


def _process(item):
    status, data = upstream.request("GET", item["image"])
    if status != 200:
        raise RuntimeError(f"image download returned {status}")
    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    faces = [] if image is None else engine.embeddings(image)
    if len(faces) != 1:
        return _finish(item["id"], "failed", f"얼굴이 1개인 사진만 등록할 수 있습니다. (검출: {len(faces)}개)")
    previous = store.people.get(item["name"])
    store.put(item["name"], normalize(faces[0] if previous is None else previous + faces[0]))
    _finish(item["id"], "done", "등록 완료")


def poll_forever():
    while True:
        try:
            status, data = upstream.request("GET", f"{PATH}?status=pending")
            if status != 200:
                raise RuntimeError(f"listing returned {status}")
            for item in json.loads(data):
                _process(item)
        except Exception as e:  # Upstream outages leave requests pending for the next poll.
            log.warning("enrollment poll failed: %s", e)
        time.sleep(config.ENROLL_POLL_SECONDS)
