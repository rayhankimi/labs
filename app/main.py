"""
Endpoints for ops scneario :
  GET  /               -> base info
  GET  /health         -> health check
  GET  /items          -> list item (in-memory)
  POST /items          -> add item  {"name": "..."}
  GET  /slow?seconds=3 -> simulate slow request based on params
  GET  /error          -> designated endpoint to throw error (500)
  GET  /crash          -> crash the system
  GET  /config         -> quick debug to see env file
  GET  /whoami         -> print user, pid, and host process
"""

import logging
import os
import socket
import sys
import time
import uuid

from fastapi import FastAPI, Request
from pydantic import BaseModel

APP_NAME = os.getenv("APP_NAME", "fastapi-lab")
APP_ENV = os.getenv("APP_ENV", "dev")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE")  # just rely on stdout, please dont fill this
SECRET_TOKEN = os.getenv("SECRET_TOKEN", "")  # masking check for accidental purposes

LOG_FORMAT = "%(asctime)s %(levelname)-7s %(name)s %(message)s"
handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
if LOG_FILE:
    handlers.append(logging.FileHandler(LOG_FILE))
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT, handlers=handlers)
log = logging.getLogger(APP_NAME)

app = FastAPI(title=APP_NAME)
START_TIME = time.time()
ITEMS: list[dict] = []


class Item(BaseModel):
    name: str


@app.middleware("http")
async def access_log(request: Request, call_next):
    req_id = uuid.uuid4().hex[:8]
    t0 = time.perf_counter()
    try:
        response = await call_next(request)
        status = response.status_code
    except Exception:
        # log traceback lengkap, lalu lempar lagi supaya jadi 500
        log.exception("req=%s %s %s unhandled error", req_id, request.method, request.url.path)
        raise
    ms = (time.perf_counter() - t0) * 1000
    client = request.client.host if request.client else "-"
    log.info(
        "req=%s %s %s status=%s dur=%.1fms client=%s",
        req_id, request.method, request.url.path, status, ms, client,
    )
    response.headers["X-Request-ID"] = req_id
    return response


@app.on_event("startup")
async def on_startup():
    log.info("starting %s env=%s pid=%s log_level=%s", APP_NAME, APP_ENV, os.getpid(), LOG_LEVEL)


@app.on_event("shutdown")
async def on_shutdown():
    log.info("shutting down %s pid=%s", APP_NAME, os.getpid())


@app.get("/")
def root():
    return {"app": APP_NAME, "env": APP_ENV, "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok", "uptime_s": round(time.time() - START_TIME, 1)}


@app.get("/items")
def list_items():
    return ITEMS


@app.post("/items", status_code=201)
def create_item(item: Item):
    new = {"id": len(ITEMS) + 1, "name": item.name}
    ITEMS.append(new)
    log.info("item created id=%s name=%s", new["id"], new["name"])
    return new


@app.get("/slow")
def slow(seconds: float = 3):
    log.warning("slow request requested seconds=%s", seconds)
    time.sleep(seconds)
    return {"slept": seconds}


@app.get("/error")
def error():
    log.error("about to raise on purpose")
    raise RuntimeError("boom: error endpoint dipanggil")


@app.get("/crash")
def crash():
    log.critical("crash endpoint dipanggil, proses akan mati sekarang")
    sys.stdout.flush()
    os._exit(1)  # keluar paksa, bukan exception -> systemd harus restart


@app.get("/config")
def config():
    return {
        "APP_NAME": APP_NAME,
        "APP_ENV": APP_ENV,
        "LOG_LEVEL": LOG_LEVEL,
        "LOG_FILE": LOG_FILE,
        "SECRET_TOKEN": ("***" + SECRET_TOKEN[-3:]) if SECRET_TOKEN else None,
    }


@app.get("/whoami")
def whoami():
    import pwd
    return {
        "user": pwd.getpwuid(os.getuid()).pw_name,
        "uid": os.getuid(),
        "pid": os.getpid(),
        "hostname": socket.gethostname(),
        "cwd": os.getcwd(),
    }
