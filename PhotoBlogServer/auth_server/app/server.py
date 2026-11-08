import hmac
import json
import logging
import re
import urllib.parse
from http.server import BaseHTTPRequestHandler

from . import config
from .controllers import enroll, health, ingest
from .errors import BadRequest

log = logging.getLogger(__name__)

# method, path pattern, required Authorization header, whether a JSON body is passed, controller
ROUTES = [
    ("GET", r"/health", None, False, health.show),
    ("POST", r"/ingest", config.INGEST_AUTHORIZATION, True, ingest.create),
    ("POST", r"/enroll", config.ADMIN_AUTHORIZATION, True, enroll.create),
    ("DELETE", r"/enroll/([^/]+)", config.ADMIN_AUTHORIZATION, False, enroll.delete),
]


class Handler(BaseHTTPRequestHandler):
    server_version = "auth-server"
    sys_version = ""

    def log_message(self, format, *args):
        log.info("%s %s", self.address_string(), format % args)

    def respond(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def authorized(self, expected):
        supplied = self.headers.get("Authorization", "").encode()
        return hmac.compare_digest(supplied, expected.encode())

    def read_json(self):
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError as e:
            raise BadRequest("Content-Length is required") from e
        if not 0 < length <= config.MAX_BODY_BYTES:
            raise BadRequest("invalid body size")
        try:
            payload = json.loads(self.rfile.read(length))
        except ValueError as e:
            raise BadRequest("invalid json") from e
        if not isinstance(payload, dict):
            raise BadRequest("invalid json")
        return payload

    def dispatch(self):
        for method, pattern, token, has_body, controller in ROUTES:
            match = re.fullmatch(pattern, self.path)
            if method != self.command or not match:
                continue
            if token and not self.authorized(token):
                self.close_connection = True
                return self.respond(401, {"error": "unauthorized"})
            try:
                args = [urllib.parse.unquote(group) for group in match.groups()]
                if has_body:
                    args.append(self.read_json())
                return self.respond(*controller(*args))
            except BadRequest as e:
                self.close_connection = True
                return self.respond(400, {"error": str(e)})
            except Exception:
                log.exception("request failed")
                return self.respond(502, {"error": "processing failed"})
        self.close_connection = True
        self.respond(404, {"error": "not found"})

    do_GET = do_POST = do_DELETE = dispatch
