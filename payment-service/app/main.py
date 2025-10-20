# payment-service/app/main.py
from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy import text
from app.database import engine
from app.models import Base
import time, uuid

app = FastAPI(title="payment-service", version="1.0.0")

# Routers
from app.routers import payments
app.include_router(payments.router)

# Metrics
REQUEST_COUNT = Counter("payment_service_http_requests_total", "Total HTTP requests", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("payment_service_http_request_latency_seconds", "Request latency", ["method", "path"])

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
    return {"status": "ok", "service": "payment-service"}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

def _repair_pg_sequences():
    """
    After seeding or manual inserts, Postgres sequences can lag.
    Bump payments.payment_id to max(pk)+1. Safe to run every startup.
    """
    with engine.begin() as conn:
        conn.execute(text("""
            SELECT setval(
                pg_get_serial_sequence('payments','payment_id'),
                GREATEST((SELECT COALESCE(MAX(payment_id), 0) FROM payments) + 1, 1),
                false
            ) WHERE pg_get_serial_sequence('payments','payment_id') IS NOT NULL;
        """))

@app.on_event("startup")
def on_startup():
    # Ensure tables exist, then repair sequences
    Base.metadata.create_all(bind=engine)
    _repair_pg_sequences()
