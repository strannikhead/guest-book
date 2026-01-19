import os
import socket
import time
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ydb

APP_VERSION = os.getenv("APP_VERSION", "0.3.0")
FRONTEND_DOMAIN = "https://guestbook-frontend-for-course-123.website.yandexcloud.net"

app = FastAPI(title="Guestbook API", version=APP_VERSION)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_DOMAIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

driver = None
pool = None
USE_YDB = os.getenv("USE_YDB", "1") == "1"

@app.on_event("startup")
def startup_event():
    global driver, pool
    if USE_YDB:
        # driver = ydb.Driver(
        #     endpoint=os.getenv("YDB_ENDPOINT", "grpcs://ydb.serverless.yandexcloud.net:2135"),
        #     database=os.getenv("YDB_DATABASE", "/ru-central1/.../your-database-id"),
        #     credentials=ydb.iam.MetadataUrlCredentials(),
        # )
        driver = ydb.Driver(
            endpoint=os.getenv("YDB_ENDPOINT"),
            database=os.getenv("YDB_DATABASE"),
            credentials=TokenCredentials(os.getenv("YC_IAM_TOKEN")),
        )
        driver.wait(timeout=10)
        pool = ydb.SessionPool(driver)


class MessageIn(BaseModel):
    author: str
    text: str

class MessageOut(MessageIn):
    id: int
    created_at: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "backend_version": APP_VERSION,
        "instance_id": socket.gethostname(),
    }


@app.get("/messages", response_model=List[MessageOut])
def list_messages():
    if not USE_YDB:
        return []

    def query(session):
        result = session.transaction().execute(
            """
            SELECT id, author, text, created_at
            FROM messages
            ORDER BY id DESC
            LIMIT 50;
            """,
            commit_tx=True,
        )
        return result[0].rows

    rows = pool.retry_operation_sync(query)
    return [
        {"id": r.id, "author": r.author, "text": r.text, "created_at": str(r.created_at)}
        for r in rows
    ]


@app.post("/messages")
def add_message(msg: MessageIn):
    if not USE_YDB:
        return {"status": "ok"}

    msg_id = int(time.time() * 1000)

    def query(session):
        session.transaction().execute(
            """
            DECLARE $id AS Uint64;
            DECLARE $author AS Utf8;
            DECLARE $text AS Utf8;
            DECLARE $created_at AS Timestamp;

            INSERT INTO messages (id, author, text, created_at)
            VALUES ($id, $author, $text, $created_at);
            """,
            {
                "$id": msg_id,
                "$author": msg.author,
                "$text": msg.text,
                "$created_at": int(time.time() * 1_000_000_000),
            },
            commit_tx=True,
        )

    pool.retry_operation_sync(query)
    return {"status": "ok"}
