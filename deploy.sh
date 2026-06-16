#!/usr/bin/env bash
set -euo pipefail

# Production deployment script for travis-ops-center
# Usage: bash deploy.sh [domain] [email]

echo "========================================="
echo "Travis Ops Center — Production Deploy"
echo "========================================="

DOMAIN="${1:-ops-center.local}"
EMAIL="${2:-admin@example.com}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$REPO_DIR"

# Step 1: Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "✓ Creating .env from template..."
    cp .env.example .env
    echo "  ⚠ EDIT .env and set AUTH_USER and AUTH_PASS before continuing!"
    echo "  Then run: bash deploy.sh $DOMAIN $EMAIL"
    exit 0
fi

# Step 2: Check for Docker
if ! command -v docker >/dev/null 2>&1; then
    echo "✗ Docker not found. Install Docker and try again."
    exit 1
fi

if ! command -v docker-compose >/dev/null 2>&1; then
    echo "✗ docker-compose not found. Install Docker Compose and try again."
    exit 1
fi

echo "✓ Docker and docker-compose found"

# Step 3: Load .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Step 4: Build and start
echo "✓ Building Docker image..."
docker-compose build

echo "✓ Starting container..."
docker-compose up -d

# Step 5: Wait for service
echo "⏳ Waiting for service to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:${SERVER_PORT:-8080} >/dev/null 2>&1; then
        echo "✓ Service is running"
        break
    fi
    sleep 1
done

# Step 6: Output deployment info
echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Web UI: http://localhost:${SERVER_PORT:-8080}"
echo ""
echo "Authentication:"
echo "  Username: ${AUTH_USER:-admin}"
echo "  Password: (from .env AUTH_PASS)"
echo ""
echo "Next steps:"
echo ""
echo "1. Test locally:"
echo "   curl -u ${AUTH_USER:-admin}:PASSWORD http://localhost:${SERVER_PORT:-8080}"
echo ""
echo "2. If using a domain + HTTPS:"
echo "   - Point DNS to this server"
echo "   - Run: certbot certonly -d $DOMAIN"
echo "   - Add nginx config with SSL (see README.md)"
echo ""
echo "3. Monitor logs:"
echo "   docker-compose logs -f"
echo ""
echo "4. To stop:"
echo "   docker-compose down"
echo ""
echo "5. To ingest evidence from Termux:"
echo "   git clone $REPO_DIR"
echo "   python3 scripts/evidence_ingest.py /path/to/file --notes 'description'"
echo "   ./scripts/sync_vault.sh 'Added evidence'"
echo ""
