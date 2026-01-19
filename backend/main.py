import logging
import os
import random
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List

import uvicorn
import ydb
from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)

APP_VERSION = os.getenv("APP_VERSION", "0.3.12")
FRONTEND_DOMAIN = os.getenv("FRONTEND_DOMAIN", "https://guestbook-frontend-for-course-123.website.yandexcloud.net")
YDB_ENDPOINT = os.getenv("YDB_ENDPOINT")
YDB_DATABASE = os.getenv("YDB_DATABASE")
PORT = int(os.environ.get('PORT', 8080))
CONTAINER_INSTANCE_ID = str(uuid.uuid4())

driver = None
pool = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global driver, pool

    print("Starting Guestbook API...")

    if not YDB_ENDPOINT or not YDB_DATABASE:
        print("YDB env vars are not set")
        yield
        return

    try:
        driver_config = ydb.DriverConfig(
            YDB_ENDPOINT,
            YDB_DATABASE,
            credentials=ydb.iam.MetadataUrlCredentials(),
        )
        driver = ydb.Driver(driver_config)

        driver.wait(timeout=15, fail_fast=True)
        pool = ydb.SessionPool(driver)

    except Exception as e:
        print(f"❌ YDB init failed: {e}")
        driver = None
        pool = None

    yield

    print("Shutting down Guestbook API...")
    if driver:
        driver.stop()


app = FastAPI(
    title="Guestbook API",
    version=APP_VERSION,
    lifespan=lifespan
)


class MessageIn(BaseModel):
    author: str
    message: str


class MessageOut(BaseModel):
    id: str
    author: str
    message: str
    timestamp: str


@app.get("/health")
def health():
    """Health check endpoint"""
    ydb_status = "connected" if driver and pool else "disconnected"

    return {
        "status": "ok",
        "backend_version": APP_VERSION,
        "instance_id": CONTAINER_INSTANCE_ID,
        "ydb_status": ydb_status,
        "ydb_configured": bool(YDB_ENDPOINT and YDB_DATABASE)
    }


@app.get("/messages", response_model=List[MessageOut])
def list_messages():
    """Получить список сообщений"""
    if not pool:
        print("YDB pool is not available")
        return []

    try:
        def query(session):
            result = session.transaction().execute(
                """
                SELECT id, author, message, timestamp
                FROM messages
                ORDER BY timestamp DESC
                    LIMIT 50;
                """,
                commit_tx=True,
            )
            return result[0].rows

        rows = pool.retry_operation_sync(query)
        return [
            {
                "id": r.id,
                "author": r.author,
                "message": r.message,
                "timestamp": r.timestamp
            }
            for r in rows
        ]

    except Exception as e:
        print(f'Error retrieving messages: {e}')
        return []


@app.post("/messages")
def add_message(msg: MessageIn):
    """Добавить новое сообщение - ТОЧНО КАК В FLASK"""
    if not driver:
        return {"status": "error", "message": "Database not ready"}

    try:
        msg_id = str(int(time.time() * 1000)) + ''.join(
            [chr(random.randint(97, 122)) for _ in range(7)]
        )
        timestamp = datetime.now().isoformat()

        query = """
            DECLARE $id AS Utf8;
            DECLARE $author AS Utf8;
            DECLARE $message AS Utf8;
            DECLARE $timestamp AS Utf8;

            INSERT INTO messages (id, author, message, timestamp)
            VALUES ($id, $author, $message, $timestamp);
        """

        session = driver.table_client.session().create()
        prepared_query = session.prepare(query)
        session.transaction().execute(
            prepared_query,
            {
                '$id': msg_id,
                '$author': msg.author,
                '$message': msg.message,
                '$timestamp': timestamp,
            },
            commit_tx=True,
        )

        return {
            'id': msg_id,
            'author': msg.author,
            'message': msg.message,
            'timestamp': timestamp
        }

    except Exception as error:
        print(f'Failed to add message: {error}')
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(error)}


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info",
        lifespan="on"
    )
