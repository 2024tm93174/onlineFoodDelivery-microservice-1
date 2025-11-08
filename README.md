# FoodGo: Online Food Delivery — Microservices (FastAPI + Postgres)

This repository contains a **multi-service, database-per-service** implementation for an online food delivery platform designed specifically to meet the assignment requirements.

> **Services provided**
>
> - `customer-service` — customers & addresses (CRUD)
> - `restaurant-service` — restaurants & menu (list/filter, availability, pricing)
> - `order-service` — create/confirm/cancel orders; statement views; total calculation
> - `payment-service` — charge/capture/refund with **idempotency**
> - `delivery-service` — driver assignment and delivery tracking
> - `notification-service` (optional) — logs email/SMS notifications
>
> Each service owns its **own database**. Cross‑DB joins are disallowed; replicated read models are used for decoupling.

## Quick start (Docker Compose)

Prereqs: Docker & Docker Compose.

```bash
cp .env.example .env
docker compose up --build -d
# Tail logs
docker compose logs -f order-service
```

### Services (local ports)

- Customer: http://localhost:8010/health | http://localhost:8010/docs
- Restaurant: http://localhost:8020/health | http://localhost:8020/docs
- Order: http://localhost:8030/health | http://localhost:8030/docs
- Payment: http://localhost:8040/health | http://localhost:8040/docs
- Delivery: http://localhost:8050/health | http://localhost:8050/docs
- Notification: http://localhost:8060/health | http://localhost:8060/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (user: admin / pass: admin)
- Jaeger: http://localhost:16686

## Place‑Order flow (happy path)

1. `POST /v1/orders` with header `Idempotency-Key` → order-service validates menu & availability via restaurant-service.
2. order-service computes totals; calls `payment-service /v1/payments/charge` (idempotent).
3. On success, order-service sets status `CONFIRMED`, calls `delivery-service /v1/deliveries/assign`.
4. notification-service is called to log/send a message.

See `docs/sequence-place-order.mmd` and the Postman collection in `docs/postman_collection.json`.

## Kubernetes (Minikube)

```bash
# Start minikube
minikube start

# Create namespace, secrets, configmaps, PVCs, DBs, apps
kubectl apply -f deploy/k8s/namespace.yaml
kubectl apply -f deploy/k8s

# Port-forward (if not using Ingress)
kubectl -n foodgo port-forward svc/order-service 8030:80
```

See `deploy/k8s/*` for Deployments, Services, ConfigMaps/Secrets, readiness/liveness probes, and PVCs for Postgres.

## Monitoring & Observability

- **/metrics** endpoint exposed by each service (Prometheus format).
- Sample Prometheus config mounted via Compose and k8s.
- Grafana dashboard JSON at `docs/grafana-dashboard.json` (import into Grafana).
- OpenTelemetry (optional): basic headers propagation and trace IDs in logs.

## Submission package

Use the `docs/Submission.md` as a ready-to-export PDF (print to PDF). It contains:
- system architecture & context map
- ERDs per service
- step-by-step run instructions with screenshots checklist
- links placeholders for per-service repositories (replace with your GitHub URLs)
- demo script outline (<= 15 min)

---

**Note:** This starter is intentionally lightweight but complete. You can extend schemas, add validations and tests, or swap FastAPI for another stack as long as service boundaries and the database-per-service rule remain intact.

## Seeding with the provided datasets

The `/data` folder contains your assignment CSVs. Import them into the databases using one-off seed containers.

```bash
# Build images and start infra
docker compose up --build -d customer-db restaurant-db order-db payment-db delivery-db   customer-service restaurant-service order-service payment-service delivery-service

# Run the seeders once (you can re-run; they TRUNCATE then import)
docker compose run --rm customer-seed
docker compose run --rm restaurant-seed
docker compose run --rm order-seed
docker compose run --rm payment-seed
docker compose run --rm delivery-seed
```

**Notes**
- Seed scripts parse dates like `DD/MM/YY HH:MM` and set the same IDs as in CSV.
- Order seeding also populates replicated fields `restaurant_name` and `address_city` from the CSVs.
# onlineFoodDelivery-microservice

# curl cmds
curl -X POST http://foodgo.local:60715/v1/customers \ -H "Content-Type: application/json" \ -d '{ "name": "John Doe", "email": "john@example.com", "address": "123 Main Street", "phone": "9876543210" }'

curl -X POST http://foodgo.local:60715/v1/orders \ -H "Content-Type: application/json" \ -H "Idempotency-Key: 123e4567-e89b-12d3-a456-426614174000" \ -d '{ "customer_id": 2, "restaurant_id": 1, "address_id": 1, "city": "Pune", "lines": [ {"item_id": 1, "quantity": 2}, {"item_id": 3, "quantity": 1} ], "payment_method": "CREDIT_CARD" }

curl -X POST http://foodgo.local:60715/v1/payments/charge \ -H "Content-Type: application/json" \ -H "Idempotency-Key: 1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p" \ -d '{ "order_id": 1, "amount": 969.42, "method": "CARD" }'

curl -X POST http://foodgo.local:60715/v1/deliveries/assign \ -H "Content-Type: application/json" \ -d '{ "order_id": 1, "city": "Pune" }'


