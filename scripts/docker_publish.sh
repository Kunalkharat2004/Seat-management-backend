#!/bin/bash
# ═══════════════════════════════════════════════════════════
# SF Portal — Build & Push script (Podman)
# Usage (run from backend/ directory):
#   ./scripts/docker_publish.sh v3       # tags as v3 + latest
#   ./scripts/docker_publish.sh v3 beta  # tags as v3 + beta
# ═══════════════════════════════════════════════════════════
set -e

IMAGE="docker.io/kunalkharat2004/sf-portal"
VERSION=${1:-"latest"}    # First arg  = version tag  (e.g. v3)
EXTRA_TAG=${2:-"latest"}  # Second arg = extra tag    (default: latest)

# Always run from backend/ directory regardless of where the script is called from
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."   # cd into backend/

echo "══════════════════════════════════════════════"
echo "  Building $IMAGE:$VERSION"
echo "══════════════════════════════════════════════"

# ── 1. Build image ─────────────────────────────────────────
#   --format docker  → enables HEALTHCHECK support
#   --platform linux/amd64  → targets remote Linux server
podman build \
  --format docker \
  --platform linux/amd64 \
  -f docker/prod/Dockerfile \
  -t "$IMAGE:$VERSION" \
  .

# ── 2. Also tag as extra tag (default: latest) ─────────────
if [ "$VERSION" != "$EXTRA_TAG" ]; then
  echo "▶ Tagging $IMAGE:$VERSION → $IMAGE:$EXTRA_TAG"
  podman tag "$IMAGE:$VERSION" "$IMAGE:$EXTRA_TAG"
fi

# ── 3. Push both tags ──────────────────────────────────────
echo "▶ Pushing $IMAGE:$VERSION ..."
podman push "$IMAGE:$VERSION"

if [ "$VERSION" != "$EXTRA_TAG" ]; then
  echo "▶ Pushing $IMAGE:$EXTRA_TAG ..."
  podman push "$IMAGE:$EXTRA_TAG"
fi

echo ""
echo "✅ Pushed:  $IMAGE:$VERSION"
[ "$VERSION" != "$EXTRA_TAG" ] && echo "✅ Pushed:  $IMAGE:$EXTRA_TAG"
echo ""
echo "══ To deploy on your remote server ═══════════"
echo "  podman-compose -f podman-compose.prod.yml pull"
echo "  podman-compose -f podman-compose.prod.yml up -d sf-portal-backend"