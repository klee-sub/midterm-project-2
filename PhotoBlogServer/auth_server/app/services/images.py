import base64

import cv2
import numpy as np

from ..errors import BadRequest


def decode_image(value):
    try:
        data = np.frombuffer(base64.b64decode(value, validate=True), np.uint8)
        image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    except (ValueError, TypeError, cv2.error) as e:
        raise BadRequest("invalid image") from e
    if image is None:
        raise BadRequest("invalid image")
    return image


def encode_jpeg(image, max_width=None):
    height, width = image.shape[:2]
    if max_width and width > max_width:
        size = (max_width, round(height * max_width / width))
        image = cv2.resize(image, size, interpolation=cv2.INTER_AREA)
    return cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 85])[1].tobytes()
