#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
uv run xbrl-financial-compare sample
uv run xbrl-financial-compare compare data/processed/*.json --out outputs
