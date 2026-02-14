#!/usr/bin/env bash
set -euo pipefail

cp -n .env.example .env || true

mkdir -p data/landing

echo "Bootstrap complete. Update .env with your credentials."
