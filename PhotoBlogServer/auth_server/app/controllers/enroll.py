import re

import numpy as np

from ..errors import BadRequest
from ..services.faces import engine, normalize, store
from ..services.images import decode_image

NAME_RE = re.compile(r"^[\w-]{1,30}$")
RESERVED_NAMES = ("unknown", "no-face")


def create(payload):
    name = payload.get("name", "")
    images = payload.get("images", [])
    if not NAME_RE.match(name) or name in RESERVED_NAMES:
        raise BadRequest("invalid name")
    if not isinstance(images, list) or not images:
        raise BadRequest("images are required")
    embeddings = []
    for index, value in enumerate(images):
        found = engine.embeddings(decode_image(value))
        if len(found) != 1:
            raise BadRequest(f"image {index} must contain exactly one face, found {len(found)}")
        embeddings.append(found[0])
    store.put(name, normalize(np.mean(embeddings, axis=0)))
    return 201, {"name": name, "images": len(embeddings)}


def delete(name):
    if store.remove(name):
        return 200, {"deleted": name}
    return 404, {"error": "not found"}
