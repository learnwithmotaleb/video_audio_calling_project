# Communication Platform Backend

Self-hosted control plane for audio and video calling. FastAPI handles application logic, and LiveKit handles media. Flutter clients and the authentication service are separate projects.

**Current status:** project setup, configuration, PostgreSQL and Redis connections, health checks, and a self-hosted LiveKit server, and the call token API with a temporary development identity. The rooms module and chat are added in later phases.

## Requirements

- Python 3.12 or newer
- Docker with Compose v2 (for the containerised setup), or your own PostgreSQL and Redis

## Run with Docker

Replace every `change-me` value in `.env` after copying it.

```bash
cp .env.example .env
docker compose up --build
```

## Run locally

Start PostgreSQL and Redis first, and point the `POSTGRES_*` and `REDIS_*` values in `.env` at them.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
cp .env.example .env
.venv/bin/uvicorn app.main:app --reload
```

Interactive API docs are at `http://localhost:8000/docs`. They are turned off when `ENVIRONMENT=production`.

## Health endpoints

| Endpoint | Purpose | Responses |
| --- | --- | --- |
| `GET /api/v1/health` | Liveness: the process is serving requests | `200` |
| `GET /api/v1/health/ready` | Readiness: PostgreSQL and Redis are reachable | `200`, or `503` if either is down |

## Errors

Every error uses the same shape. `details` appears only on validation errors.

```json
{ "error": { "code": "http_error", "message": "Not Found" } }
```

## Tests

The first command runs unit tests and needs no services. The second also tests real PostgreSQL and Redis using `.env`.

```bash
.venv/bin/pytest
RUN_INTEGRATION=1 .venv/bin/pytest
.venv/bin/ruff check .
```

## Configuration

All settings come from environment variables or `.env`; see [.env.example](.env.example). With `ENVIRONMENT=production` the app refuses to start if a password is empty or still `change-me`, or if `CORS_ORIGINS` contains `*`.

## Ports

Compose publishes these on `127.0.0.1` only:

| Service | Default host port | Variable |
| --- | --- | --- |
| API | 8000 | `API_PORT` |
| PostgreSQL | 5433 | `POSTGRES_HOST_PORT` |
| Redis | 6379 | `REDIS_HOST_PORT` |

## Calls

`POST /api/v1/calls/token` takes `{"room_id": "demo"}` and returns the LiveKit `url` and a 15-minute `token` limited to that room, creating the room if needed.

Until the authentication service exists, the caller is named by the `X-Dev-User-Id` header. Anyone who can reach the API can claim any name and join any room, so keep it on a trusted network. With `ENVIRONMENT=production` every call to this endpoint returns `401`.

## LiveKit

LiveKit runs as a Compose service using [docker/livekit/livekit.yaml](docker/livekit/livekit.yaml). Its keys and node IP come from `.env`. Rooms are not created automatically, so a token is rejected unless the room already exists.

Set `LIVEKIT_NODE_IP` to the address clients use to reach the media ports: the machine's LAN IP in development, or the public IP on a VPS. If that IP changes, update `.env` and run `docker compose up -d livekit`.

| Port | Protocol | Purpose |
| --- | --- | --- |
| 7880 | TCP | API and WebSocket signalling |
| 7881 | TCP | Media fallback when UDP is blocked |
| 7882 | UDP | Media (preferred) |

After changing network, run `scripts/set-node-ip.sh`. It updates `.env` with the Mac's current IP, restarts LiveKit and the API, and prints the command for running the app.

On a Mac using Colima, set `portForwarder: grpc` in `~/.colima/default/colima.yaml`. The `ssh` forwarder does not carry UDP.

## Production

`docker-compose.prod.yml` adds Caddy for automatic TLS and enables LiveKit's TURN server. It keeps PostgreSQL, Redis, the API and LiveKit's port 7880 off the public internet.

1. Point `API_DOMAIN`, `LIVEKIT_DOMAIN` and `TURN_DOMAIN` at the VPS.
2. Run `sudo scripts/setup-vps.sh` once to set UDP buffers and the firewall.
3. In `.env`, set `ENVIRONMENT=production`, real secrets, and `LIVEKIT_PUBLIC_URL=wss://<LIVEKIT_DOMAIN>`.
4. Start it:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

LiveKit restarts a few times on first boot until Caddy has obtained the TURN certificate. After Caddy renews that certificate, restart the `livekit` service.

| Port | Protocol | Purpose |
| --- | --- | --- |
| 80, 443 | TCP | HTTPS, and certificate issuing |
| 443 | UDP | HTTP/3 |
| 3478 | UDP | TURN |
| 5349 | TCP | TURN over TLS |
| 7881 | TCP | Media fallback |
| 7882 | UDP | Media |
| 30000-30100 | UDP | TURN relay |

`POST /api/v1/calls/token` returns `401` in production until the authentication service is connected, so calls cannot start there yet.
