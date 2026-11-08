import json
import threading
import urllib.error
import urllib.parse
import urllib.request
import uuid

from .. import config


def multipart(fields, tags, jpeg):
    boundary = uuid.uuid4().hex
    parts = []
    # DRF reads a multipart list field per repeated key, so each tag is its own part.
    for name, value in [*fields.items(), *(("tags", t) for t in tags)]:
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
        )
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="detected.jpg"\r\n'
        "Content-Type: image/jpeg\r\n\r\n".encode()
    )
    parts.extend([jpeg, f"\r\n--{boundary}--\r\n".encode()])
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


class Upstream:
    def __init__(self):
        self.lock = threading.Lock()
        self.token = None

    def _login(self):
        body = urllib.parse.urlencode(
            {"username": config.UPSTREAM_USERNAME, "password": config.UPSTREAM_PASSWORD}
        ).encode()
        url = f"{config.UPSTREAM_URL}/api-token-auth/"
        with urllib.request.urlopen(url, body, timeout=config.UPSTREAM_TIMEOUT) as res:
            return json.load(res)["token"]

    def _send(self, method, url, body, content_type, token):
        headers = {"Authorization": f"Token {token}", "Accept": "application/json"}
        if content_type:
            headers["Content-Type"] = content_type
        request = urllib.request.Request(url, data=body, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=config.UPSTREAM_TIMEOUT) as res:
                return res.status, res.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def request(self, method, url, body=None, content_type=None):
        """Send an authenticated request, logging in again once if the token is rejected."""
        if url.startswith("/"):
            url = config.UPSTREAM_URL + url
        with self.lock:
            if self.token is None:
                self.token = self._login()
            token = self.token
        status, payload = self._send(method, url, body, content_type, token)
        if status == 401:
            with self.lock:
                self.token = self._login()
                token = self.token
            status, payload = self._send(method, url, body, content_type, token)
        return status, payload

    def create_post(self, fields, tags, jpeg):
        body, content_type = multipart(fields, tags, jpeg)
        return self.request("POST", "/api_root/Post/", body, content_type)


upstream = Upstream()
