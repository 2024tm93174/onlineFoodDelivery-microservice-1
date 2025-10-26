# FoodGo — Submission Document

**Group:** PS2 
**Date:** 2025-10-16

> Replace placeholders (group id, member names/emails, repo URLs) and export this file to PDF.  
> Screenshots checklist is provided below.

---

## 1. Team & Contributions

- Anand Prakash (2024TM93169) — 100% — Services: Customer, Order, Restaurant, Delivery, Notification, Payment, Architecture & DB Modelling


## 2. Application Overview

A microservices-based online food delivery system implementing **database‑per‑service**, **no cross‑DB joins**, with **replicated read models** in the Order service for statements and decoupling.

## 3. Architecture

- **Services:** customer, restaurant, order, payment, delivery (+ notification optional)
- **Inter-service communication:** Synchronous REST (HTTP). Timeouts and idempotency are implemented for write endpoints.
- **Asynchronous (optional):** Outbox pattern stubs for future events (OrderConfirmed, PaymentSucceeded).
- **Observability:** Prometheus metrics (/metrics), JSON logs with correlationId, sample Grafana dashboard.

### 3.1 Context Map

See `docs/context-map.mmd`.

### 3.2 ERDs per service

- Customer DB: customers, addresses  
- Restaurant DB: restaurants, menu_items  
- Order DB: orders, order_items (+ replicated restaurant_name, address_city)  
- Payment DB: payments, idempotency_keys  
- Delivery DB: drivers, deliveries  
- Notification DB (optional): notifications_log

### 3.3 Place‑Order Sequence

See `docs/sequence-place-order.mmd`.

## 4. Business Rules

- Restaurant must be `is_open=true`; all requested items `is_available=true`.
- Delivery city must equal restaurant city.
- Max 20 items per order; each line quantity ≤ 5.
- Order total = Σ(item_price × qty) + tax (5%) + delivery fee; client/server totals must match.
- COD orders: `payment_status=PENDING` until driver collects; non‑COD attempts set `SUCCESS`/`FAILED`.

## 5. Deployments

### 5.1 Docker Compose

- One Postgres per service; one container per service.
- `docker compose up --build -d`

### 5.2 Minikube (Kubernetes)

- `kubectl apply -f deploy/k8s`  
- Deployments include readiness/liveness probes and resource requests/limits.
- ConfigMaps/Secrets store DB credentials and URLs. PVCs for DBs.

## 6. Monitoring

- Prometheus scrapes `/metrics` on all services.
- Grafana dashboard (`docs/grafana-dashboard.json`) shows RPS, errors, latency (p50/p90/p99).
- Business counters: `orders_placed_total`, `payments_failed_total` (extendable in code).
- Logs: structured JSON including `X-Correlation-ID` header.

## 7. Evidence (Screenshots to include)

- `docker ps` showing running containers.
- Health endpoints (`/health`) in browser.
- Postman/`curl` calls: create customer → place order (with `Idempotency-Key`) → payment → driver assignment.
- Minikube: `kubectl get pods,svc`, `kubectl logs` for one service.
- Grafana dashboard showing traffic; Jaeger trace view for one request.

## 8. Repositories

- Customer: <replace with GitHub URL>
- Restaurant: <replace with GitHub URL>
- Order: <replace with GitHub URL>
- Payment: <replace with GitHub URL>
- Delivery: <replace with GitHub URL>
- Notification (optional): <replace with GitHub URL>

---

### Appendix: Runbook (Demo ≤ 15 minutes)

1. Start Compose; open Swagger UIs.  
2. Create a customer and an address.  
3. Seed a restaurant and menu (or use provided seed).  
4. Place order (card/UPI) with header `Idempotency-Key: demo-123`.  
5. Show payment idempotency by re‑issuing the same request.  
6. Show assigned delivery and status transitions.  
7. Show metrics in Prometheus and Grafana.  
8. Optional: Fail a payment to show error handling and logs.


## 9. Dataset & Seeding (from provided CSVs)

- The assignment CSVs are included under `data/` with a filename mapping (see `data/README.md`).
- Use the provided Docker one-off seed services to import data into each service DB (TRUNCATE + INSERT).
- Ids match the dataset; `orders` receive replicated fields (`restaurant_name`, `address_city`) at seed time.
