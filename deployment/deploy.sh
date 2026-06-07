#!/bin/bash
# ==============================================================================
# Lunafish Deploy Script — fofofish.app
# ==============================================================================
# Usage:
#   ./deploy.sh setup    — First time setup (generates secrets, gets SSL cert)
#   ./deploy.sh up       — Start all services
#   ./deploy.sh down     — Stop all services
#   ./deploy.sh restart  — Restart all services
#   ./deploy.sh logs     — View logs
#   ./deploy.sh ssl      — Renew/obtain SSL certificate
#   ./deploy.sh status   — Show service status
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

DOMAIN="fofofish.app"
EMAIL="admin@fofofish.app"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

# ==============================================================================
# SETUP — First time
# ==============================================================================
cmd_setup() {
    log "Setting up Lunafish production environment..."

    # Generate .env if not exists
    if [ ! -f .env ]; then
        log "Generating .env from .env.example..."
        cp .env.example .env

        # Generate secrets
        sed -i "s|POSTGRES_PASSWORD=CHANGE_ME.*|POSTGRES_PASSWORD=$(openssl rand -hex 32)|" .env
        sed -i "s|REDIS_PASSWORD=CHANGE_ME.*|REDIS_PASSWORD=$(openssl rand -hex 32)|" .env
        sed -i "s|DJANGO_SECRET_KEY=CHANGE_ME.*|DJANGO_SECRET_KEY=$(openssl rand -hex 64)|" .env
        sed -i "s|CENTRIFUGO_TOKEN_SECRET=CHANGE_ME.*|CENTRIFUGO_TOKEN_SECRET=$(openssl rand -hex 32)|" .env
        sed -i "s|CENTRIFUGO_API_KEY=CHANGE_ME.*|CENTRIFUGO_API_KEY=$(openssl rand -hex 32)|" .env
        sed -i "s|CENTRIFUGO_ADMIN_PASSWORD=CHANGE_ME.*|CENTRIFUGO_ADMIN_PASSWORD=$(openssl rand -hex 16)|" .env
        sed -i "s|CENTRIFUGO_ADMIN_SECRET=CHANGE_ME.*|CENTRIFUGO_ADMIN_SECRET=$(openssl rand -hex 32)|" .env
        sed -i "s|RTC_JWT_SECRET=CHANGE_ME.*|RTC_JWT_SECRET=$(openssl rand -hex 32)|" .env
        sed -i "s|INTERNAL_CALLBACK_SECRET=CHANGE_ME.*|INTERNAL_CALLBACK_SECRET=$(openssl rand -hex 32)|" .env

        # Set public IP
        PUBLIC_IP=$(curl -s ifconfig.me || curl -s icanhazip.com || echo "YOUR_IP")
        sed -i "s|PUBLIC_IP=YOUR_SERVER_PUBLIC_IP|PUBLIC_IP=$PUBLIC_IP|" .env

        log "Generated .env with random secrets. Review it: nano .env"
    else
        warn ".env already exists, skipping generation"
    fi

    # Create SSL directory
    mkdir -p nginx/ssl

    log "Setup complete! Next steps:"
    echo "  1. Review .env: nano .env"
    echo "  2. Get SSL cert: ./deploy.sh ssl"
    echo "  3. Start services: ./deploy.sh up"
}

# ==============================================================================
# SSL — Get/Renew certificate with certbot
# ==============================================================================
cmd_ssl() {
    log "Obtaining SSL certificate for $DOMAIN..."

    mkdir -p /var/www/certbot

    # Temporary nginx for ACME challenge
    docker compose up -d nginx 2>/dev/null || true

    docker run --rm \
        -v "/etc/letsencrypt:/etc/letsencrypt" \
        -v "/var/www/certbot:/var/www/certbot" \
        certbot/certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        -d "$DOMAIN" \
        -d "www.$DOMAIN"

    # Copy certs to nginx/ssl
    cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem nginx/ssl/fullchain.pem
    cp /etc/letsencrypt/live/$DOMAIN/privkey.pem nginx/ssl/privkey.pem

    log "SSL certificate obtained and copied to nginx/ssl/"

    # Restart nginx
    docker compose restart nginx 2>/dev/null || true
}

# ==============================================================================
# UP — Start services
# ==============================================================================
cmd_up() {
    log "Starting Lunafish services..."

    if [ ! -f .env ]; then
        error ".env not found. Run: ./deploy.sh setup"
    fi

    if [ ! -f nginx/ssl/fullchain.pem ]; then
        warn "SSL cert not found. Using self-signed for now..."
        mkdir -p nginx/ssl
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/privkey.pem \
            -out nginx/ssl/fullchain.pem \
            -subj "/CN=$DOMAIN" 2>/dev/null
    fi

    docker compose up -d

    log "Services started!"
    cmd_status
}

# ==============================================================================
# DOWN — Stop services
# ==============================================================================
cmd_down() {
    log "Stopping Lunafish services..."
    docker compose down
    log "All services stopped."
}

# ==============================================================================
# RESTART
# ==============================================================================
cmd_restart() {
    log "Restarting Lunafish services..."
    docker compose restart
    log "Restarted."
    cmd_status
}

# ==============================================================================
# LOGS
# ==============================================================================
cmd_logs() {
    docker compose logs -f "${@:2}"
}

# ==============================================================================
# STATUS
# ==============================================================================
cmd_status() {
    echo ""
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║          Lunafish — fofofish.app                     ║"
    echo "╠══════════════════════════════════════════════════════╣"
    docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null
    echo "╚══════════════════════════════════════════════════════╝"
    echo ""
    echo "Endpoints:"
    echo "  API:        https://$DOMAIN/api/"
    echo "  Centrifugo: wss://$DOMAIN/realtime/connection/websocket"
    echo "  RTC:        wss://$DOMAIN/rtc/ws"
    echo "  Admin:      https://$DOMAIN/admin/"
    echo ""
}

# ==============================================================================
# Main
# ==============================================================================
case "${1:-help}" in
    setup)   cmd_setup ;;
    up)      cmd_up ;;
    down)    cmd_down ;;
    restart) cmd_restart ;;
    logs)    cmd_logs "$@" ;;
    ssl)     cmd_ssl ;;
    status)  cmd_status ;;
    *)
        echo "Usage: $0 {setup|up|down|restart|logs|ssl|status}"
        echo ""
        echo "Commands:"
        echo "  setup    — First time setup (generates secrets)"
        echo "  up       — Start all services"
        echo "  down     — Stop all services"
        echo "  restart  — Restart all services"
        echo "  logs     — View logs (add service name to filter)"
        echo "  ssl      — Obtain/renew SSL certificate"
        echo "  status   — Show service status"
        ;;
esac
