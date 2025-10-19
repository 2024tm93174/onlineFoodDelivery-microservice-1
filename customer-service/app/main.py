from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time, uuid

app = FastAPI(title="customer-service", version="1.0.0")

# Import routers
from app.routers import customers
from app.routers import addresses


# Metrics
REQUEST_COUNT = Counter("customer_service_http_requests_total", "Total HTTP requests", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("customer_service_http_request_latency_seconds", "Request latency", ["method", "path"])

# Correlation ID middleware
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
    return {"status": "ok", "service": "customer-service" }

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

app.include_router(customers.router, prefix='/v1')
app.include_router(addresses.router, prefix='/v1')
