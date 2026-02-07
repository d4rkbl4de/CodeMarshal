#!/bin/bash
# docker-build.sh - Build CodeMarshal Docker images
# Usage: ./docker-build.sh [dev|prod]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default to production
BUILD_TYPE="${1:-prod}"

echo -e "${GREEN}Building CodeMarshal Docker image (${BUILD_TYPE})...${NC}"

cd "$PROJECT_DIR"

if [ "$BUILD_TYPE" = "dev" ]; then
    echo -e "${YELLOW}Building development image...${NC}"
    docker build -f Dockerfile.dev -t codemarshal:dev .
    echo -e "${GREEN}Development image built: codemarshal:dev${NC}"
elif [ "$BUILD_TYPE" = "prod" ]; then
    echo -e "${YELLOW}Building production image...${NC}"
    docker build -f Dockerfile -t codemarshal:latest .
    echo -e "${GREEN}Production image built: codemarshal:latest${NC}"
else
    echo -e "${RED}Invalid build type: $BUILD_TYPE${NC}"
    echo "Usage: $0 [dev|prod]"
    exit 1
fi

echo -e "${GREEN}Build complete!${NC}"
