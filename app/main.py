import asyncio
import json
import logging
import os
import time

import psycopg
from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from psycopg.rows import dict_row
from pydantic import BaseModel, Field

app = FastAPI(title="DevOps Lab v2")
logging.basicConfig(level=logging.INFO, format="%(message)s")
requests_total = Counter("lab_http_requests_total", "HTTP requests", ["method", "route", "status"])
latency = Histogram("lab_http_request_duration_seconds", "HTTP latency", ["route"])
database_up = Gauge("lab_database_up", "Database reachable from this API process")

def connection():
    return psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=3, row_factory=dict_row)

@app.middleware("http")
async def observe(request: Request, call_next):
    started = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        elapsed = time.perf_counter() - started
        route = getattr(request.scope.get("route"), "path", "unmatched")
        if route not in {"/metrics", "/health", "/ready"}:
            requests_total.labels(request.method, route, str(status)).inc()
            latency.labels(route).observe(elapsed)
            logging.info(json.dumps({"method": request.method, "route": route,
                                     "status": status, "duration_ms": round(elapsed * 1000, 2)}))

@app.get("/health")
def health():
    return {"status": "ok", "version": os.getenv("APP_VERSION", "v1")}

@app.get("/ready")
def ready():
    try:
        with connection() as conn:
            conn.execute("SELECT 1")
        database_up.set(1)
        return {"status": "ready"}
    except psycopg.Error:
        database_up.set(0)
        raise HTTPException(status_code=503, detail="database unavailable")

@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), headers={"Content-Type": CONTENT_TYPE_LATEST})

class Item(BaseModel):
    name: str = Field(min_length=1, max_length=120)

@app.post("/items", status_code=201)
def create_item(item: Item):
    with connection() as conn:
        return conn.execute("INSERT INTO items(name) VALUES (%s) RETURNING id, name", (item.name,)).fetchone()

@app.get("/items")
def list_items():
    with connection() as conn:
        return conn.execute("SELECT id, name FROM items ORDER BY id").fetchall()

@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    with connection() as conn:
        row = conn.execute("DELETE FROM items WHERE id=%s RETURNING id", (item_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="item not found")
    return row

@app.get("/fail")
def fail():
    raise HTTPException(status_code=500, detail="intentional lab error")

@app.get("/slow")
async def slow():
    await asyncio.sleep(0.5)
    return {"delay_seconds": 0.5}
