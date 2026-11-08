import logging
import threading
from http.server import ThreadingHTTPServer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

from . import config  # noqa: E402
from .server import Handler  # noqa: E402
from .services.enrollments import poll_forever  # noqa: E402

logging.getLogger(__name__).info(
    "listening on %s, upstream=%s, llm=%s", config.PORT, config.UPSTREAM_URL, config.LLM_ENABLED
)
threading.Thread(target=poll_forever, daemon=True).start()
ThreadingHTTPServer(("0.0.0.0", config.PORT), Handler).serve_forever()
