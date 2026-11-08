import base64
import os

_ingest_login = f'{os.environ["INGEST_USERNAME"]}:{os.environ["INGEST_PASSWORD"]}'
INGEST_AUTHORIZATION = "Basic " + base64.b64encode(_ingest_login.encode()).decode()
ADMIN_AUTHORIZATION = "Bearer " + os.environ["ADMIN_TOKEN"]
UPSTREAM_URL = os.environ["UPSTREAM_URL"].rstrip("/")
UPSTREAM_USERNAME = os.environ["UPSTREAM_USERNAME"]
UPSTREAM_PASSWORD = os.environ["UPSTREAM_PASSWORD"]

PORT = int(os.getenv("PORT", "9000"))
MODEL_DIR = os.getenv("MODEL_DIR", "/models")
DATA_FILE = os.getenv("DATA_FILE", "/data/faces.json")
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "0.363"))
MIN_FACE_WIDTH = int(os.getenv("MIN_FACE_WIDTH", "40"))
UPSTREAM_MAX_WIDTH = int(os.getenv("UPSTREAM_MAX_WIDTH", "640"))
MAX_BODY_BYTES = int(os.getenv("MAX_BODY_BYTES", str(20 * 1024 * 1024)))
UPSTREAM_TIMEOUT = int(os.getenv("UPSTREAM_TIMEOUT_SECONDS", "30"))

ENROLL_POLL_SECONDS = int(os.getenv("ENROLL_POLL_SECONDS", "10"))

LLM_ENABLED = os.getenv("LLM_DESCRIPTION_ENABLED", "false").lower() == "true"
LLM_URL = os.getenv("LLM_URL", "http://vllm.maybelab.internal:8080").rstrip("/")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen3.8-Flash-Next Uncensored NVFP4")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
