#!/bin/bash
# docker-run.sh - Run CodeMarshal Docker container
# Usage: ./docker-run.sh [command] [args...]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default image
IMAGE="codemarshal:latest"

# Check for dev mode
if [ "$1" = "--dev" ]; then
    IMAGE="codemarshal:dev"
    shift
fi

# Ensure data directories exist
mkdir -p "$PROJECT_DIR/.codemarshal"
mkdir -p "$PROJECT_DIR/storage"
mkdir -p "$PROJECT_DIR/projects"

echo -e "${GREEN}Running CodeMarshal container...${NC}"
echo -e "${YELLOW}Image: $IMAGE${NC}"

# Run container with appropriate mounts
docker run --rm -it \
    -v "$PROJECT_DIR/.codemarshal:/data/.codemarshal" \
    -v "$PROJECT_DIR/storage:/data/storage" \
    -v "$PROJECT_DIR/projects:/data/projects:ro" \
    -e "CODEMARSHAL_HOME=/data" \
    "$IMAGE" \
    "$@"
