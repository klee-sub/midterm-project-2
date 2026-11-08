import logging

from .. import config
from ..errors import BadRequest
from ..services.faces import identify
from ..services.images import decode_image, encode_jpeg
from ..services.llm import describe
from ..services.upstream import upstream

log = logging.getLogger(__name__)


def _has_person(payload):
    objects = payload.get("objects", [])
    if not isinstance(objects, list):
        raise BadRequest("objects must be a list")
    return "person" in objects


def create(payload):
    image = decode_image(payload.get("image", ""))
    fields = {
        key: str(payload[key])
        for key in ("title", "text", "created_date", "published_date")
        if payload.get(key) is not None
    }
    if not fields.get("title") or "text" not in fields:
        raise BadRequest("title and text are required")

    tags = identify(image) if _has_person(payload) else []
    jpeg = encode_jpeg(image, config.UPSTREAM_MAX_WIDTH)
    if config.LLM_ENABLED and "auth:unknown" in tags:
        description = describe(jpeg)
        if description:
            fields["text"] = f"{fields['text']}\n[자동 설명] {description}"

    status, _ = upstream.create_post(fields, tags, jpeg)
    log.info("forwarded title=%s tags=%s upstream=%s", fields["title"], tags, status)
    return (201 if status == 201 else 502), {"upstream_status": status, "tags": tags}
