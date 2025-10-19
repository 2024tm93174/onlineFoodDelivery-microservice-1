from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time, uuid

app = FastAPI(title="restaurant-service", version="1.0.0")

# Import routers
from app.routers import restaurants
from app.routers import menu


# Metrics
REQUEST_COUNT = Counter("restaurant_service_http_requests_total", "Total HTTP requests", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("restaurant_service_http_request_latency_seconds", "Request latency", ["method", "path"])

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
    return {"status": "ok", "service": "restaurant-service" }

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

app.include_router(restaurants.router, prefix='/v1')
app.include_router(menu.router, prefix='/v1')
