#!/usr/bin/env bash
set -euo pipefail

IMAGE="${SMOKE_IMAGE:-warmth-api-smoke}"
PORT="${SMOKE_PORT:-8000}"

docker build -t "$IMAGE" .

cid=""
cleanup() {
  if [[ -n "$cid" ]]; then
    docker rm -f "$cid" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

cid="$(docker run -d --rm -p "${PORT}:8000" \
  -e DISABLE_SECRET_MANAGER=true \
  -e REQUIRE_FIREBASE_AUTH=false \
  -e USE_FIRESTORE_STORE=false \
  "$IMAGE")"

for _ in $(seq 1 30); do
  if curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null; then
    echo "Smoke test passed: GET /health -> 200"
    exit 0
  fi
  sleep 1
done

echo "Smoke test failed: /health did not return 200 within 30s" >&2
exit 1
