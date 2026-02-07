#!/bin/bash
# docker-entrypoint.sh - Entrypoint for CodeMarshal Docker container
# Sets up environment and runs commands

set -e

# Set up data directory permissions
if [ -d "/data" ]; then
    mkdir -p /data/.codemarshal
    mkdir -p /data/storage
    mkdir -p /data/config
    mkdir -p /data/projects
fi

# Check if running as codemarshal user
if [ "$(id -u)" = "0" ] && [ -n "$CODEMARSHAL_USER" ]; then
    # Drop privileges to codemarshal user
    exec su-exec codemarshal "$0" "$@"
fi

# Execute the command
exec "$@"
