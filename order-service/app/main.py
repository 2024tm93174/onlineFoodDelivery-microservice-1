# order-service/app/main.py
from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy import text
from app.database import engine
from app.models import Base
import time, uuid
import logging
import os

log = logging.getLogger("order-service")

app = FastAPI(title="order-service", version="1.0.0")

# Routers
from app.routers import orders  # noqa: E402
app.include_router(orders.router)

# Metrics
REQUEST_COUNT = Counter(
    "order_service_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "order_service_http_request_latency_seconds",
    "Request latency",
    ["method", "path"],
)

# Correlation ID + metrics middleware
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    corr = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    start = time.time()
    response: Response = await call_next(request)
    duration = time.time() - start
    path = request.url.path
    REQUEST_COUNT.labels(request.method, path, str(response.status_code)).inc()
    REQUEST_LATENCY.labels(request.method, path).observe(duration)
    response.headers["X-Correlation-ID"] = corr
    return response

@app.get("/health")
async def health():
    return {"status": "ok", "service": "order-service"}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def _repair_pg_sequences():
    """
    After seeding with explicit ids, Postgres sequences can lag.
    Bump only the sequences this service owns. Keep this defensive.
    """
    # allow disabling via env if desired
    if os.getenv("DISABLE_SEQUENCE_REPAIR", "").lower() in {"1", "true", "yes"}:
        log.info("Sequence repair disabled by env")
        return

    try:
        with engine.begin() as conn:
            # orders.order_id — safe if it's an identity/serial; no-op otherwise
            conn.execute(text("""
                SELECT setval(
                    pg_get_serial_sequence('orders','order_id'),
                    GREATEST((SELECT COALESCE(MAX(order_id), 0) FROM orders) + 1, 1),
                    false
                )
                WHERE pg_get_serial_sequence('orders','order_id') IS NOT NULL;
            """))
        log.info("Sequence repair completed")
    except Exception as exc:
        # Don't block startup if DB is empty or schema differs
        log.warning("Sequence repair skipped: %s", exc)


@app.on_event("startup")
def on_startup():
    # Create tables and (best-effort) repair the orders sequence.
    Base.metadata.create_all(bind=engine)
    _repair_pg_sequences()
