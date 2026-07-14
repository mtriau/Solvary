#!/bin/sh
# One-time: install Solvary language runtimes into a running Piston.
# Usage: ./install-runtimes.sh [piston_url]   (default http://localhost:2000)
set -e
PISTON="${1:-http://localhost:2000}"
echo "Installing python 3.12.0..."
curl -sf -X POST "$PISTON/api/v2/packages" -H "Content-Type: application/json" -d "{\"language\":\"python\",\"version\":\"3.12.0\"}"
echo
echo "Installing node 20.11.1..."
curl -sf -X POST "$PISTON/api/v2/packages" -H "Content-Type: application/json" -d "{\"language\":\"node\",\"version\":\"20.11.1\"}"
echo
echo "Installed runtimes:"
curl -sf "$PISTON/api/v2/runtimes"
echo
