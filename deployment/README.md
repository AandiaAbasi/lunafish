# Lunafish Production Deployment — fofofish.app

## Architecture

```
                          Internet
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Single Server (VPS)                        │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                NGINX (port 80/443)                    │    │
│  │   SSL termination + reverse proxy                     │    │
│  │                                                       │    │
│  │   /api/      → django:8000                           │    │
│  │   /realtime/ → centrifugo:8000  (WebSocket + HTTP)   │    │
│  │   /rtc/      → mediasoup:3001   (WebSocket)          │    │
│  └──────────┬──────────────┬─────────────────┬──────────┘    │
│             │              │                  │               │
│  ┌──────────▼──┐ ┌────────▼────────┐ ┌──────▼──────────┐   │
│  │   Django    │ │   Centrifugo    │ │   Mediasoup     │   │
│  │   :8000     │ │   :8000         │ │   :3001         │   │
│  │             │ │                  │ │   UDP 40000-    │   │
│  │  REST API   │ │  Realtime hub   │ │   40100         │   │
│  └──────┬──────┘ └────────┬────────┘ └─────────────────┘   │
│         │                  │                                  │
│  ┌──────▼──────┐ ┌────────▼────────┐                        │
│  │ PostgreSQL  │ │     Redis       │                        │
│  │   :5432     │ │     :6379       │                        │
│  └─────────────┘ └─────────────────┘                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘

Public ports:
  80/tcp    — HTTP (redirects to HTTPS)
  443/tcp   — HTTPS (Nginx)
  40000-40100/udp — WebRTC media (Mediasoup)
```

## Requirements

- Linux server (Ubuntu 22.04+ recommended)
- Docker + Docker Compose v2
- Domain `fofofish.app` pointing to server IP
- Firewall allowing: 80, 443, 40000-40100/udp

## Quick Start

```bash
# 1. Clone to server
git clone <repo-url> /opt/lunafish
cd /opt/lunafish/deployment/production

# 2. First time setup (generates secrets, .env)
./deploy.sh setup

# 3. Review and edit .env
nano .env

# 4. Get SSL certificate
./deploy.sh ssl

# 5. Start everything
./deploy.sh up

# 6. Check status
./deploy.sh status
```

## Services

| Service | Internal Port | Purpose |
|---------|--------------|---------|
| **nginx** | 80, 443 | Reverse proxy, SSL, routing |
| **centrifugo** | 8000 | Realtime events (chat, whiteboard, hands) |
| **mediasoup** | 3001 + UDP 40000-40100 | WebRTC SFU (audio/video/screen) |
| **django** | 8000 | Application API (placeholder) |
| **postgres** | 5432 | Database |
| **redis** | 6379 | Centrifugo engine, Django cache |

## Endpoints (public)

| URL | Purpose |
|-----|---------|
| `https://fofofish.app/api/` | Django REST API |
| `wss://fofofish.app/realtime/connection/websocket` | Centrifugo WebSocket |
| `https://fofofish.app/realtime/connection/http_stream` | Centrifugo HTTP streaming (fallback) |
| `wss://fofofish.app/rtc/ws` | Mediasoup WebSocket (signaling) |
| `https://fofofish.app/admin/` | Django admin |

## Adding Django

When your Django project is ready:

1. Copy your Django project into `deployment/production/django/`
2. Update the Dockerfile if needed
3. Uncomment the `django` service in `docker-compose.yml`
4. Uncomment `depends_on: django` in the `nginx` service
5. Run `docker compose up -d --build django`

## SSL Certificate

```bash
# First time
./deploy.sh ssl

# Renewal (add to crontab: 0 3 * * 1 /opt/lunafish/deployment/production/deploy.sh ssl)
./deploy.sh ssl
```

## Monitoring

```bash
# All logs
./deploy.sh logs

# Specific service
./deploy.sh logs centrifugo
./deploy.sh logs mediasoup

# Service status
./deploy.sh status
```

## Firewall (UFW)

```bash
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 40000:40100/udp
ufw enable
```

## Scaling Notes

This setup is for a single server handling:
- ~100 concurrent classroom participants
- ~10 concurrent video streams
- ~1000 realtime connections (Centrifugo)

For more capacity:
- Add more Mediasoup workers (1 per CPU core) via env var
- Scale Centrifugo horizontally (Redis pub/sub handles coordination)
- Move PostgreSQL to managed database
- Add CDN for static assets
