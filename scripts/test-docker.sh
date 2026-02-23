#!/usr/bin/env bash
# Test API and UI Docker images from repo root. Image names match CI (without registry prefix).
# Run: ./scripts/test-docker.sh
set -e
cd "$(dirname "$0")/.."

IMAGE_API="movie-recommendation-api"
IMAGE_UI="movie-recommendation-ui"
TAG="local"

echo "=== Building API image ($IMAGE_API:$TAG) ==="
docker build -t "$IMAGE_API:$TAG" -f Dockerfile .

echo "=== Running API container (port 8000) ==="
docker run -d --name rec-api-test -p 8000:8000 \
  -e TMDB_API_KEY="${TMDB_API_KEY:-}" \
  -v "$(pwd)/models/trained:/app/models/trained:ro" \
  "$IMAGE_API:$TAG"

sleep 3
echo "=== Health check ==="
curl -s http://localhost:8000/health | head -1
docker stop rec-api-test && docker rm rec-api-test
echo "=== API test OK ==="

echo "=== Building UI image ($IMAGE_UI:$TAG) ==="
docker build -t "$IMAGE_UI:$TAG" -f ui/Dockerfile .

echo "=== Running UI container (port 8501) ==="
docker run -d --name rec-ui-test -p 8501:8501 \
  -e TMDB_API_KEY="${TMDB_API_KEY:-}" \
  -v "$(pwd)/models/trained:/app/models/trained:ro" \
  "$IMAGE_UI:$TAG"

sleep 5
echo "=== UI check (curl 8501) ==="
curl -s -o /dev/null -w "%{http_code}" http://localhost:8501 || true
docker stop rec-ui-test && docker rm rec-ui-test
echo "=== UI test OK ==="

echo "=== All Docker tests passed ==="
