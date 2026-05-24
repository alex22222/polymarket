#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-data/raw}"
mkdir -p "$OUT_DIR"

fetch() {
  local url="$1"
  local out="$2"
  if curl --connect-timeout 8 --max-time 20 -fsSL "$url" -o "$out"; then
    echo "ok $out"
  else
    echo "failed $out" >&2
    rm -f "$out"
  fi
}

fetch \
  "https://gamma-api.polymarket.com/public-search?q=bitcoin&limit_per_type=100&search_profiles=false&search_tags=false&keep_closed_markets=1" \
  "$OUT_DIR/gamma-search-bitcoin.json"

fetch \
  "https://gamma-api.polymarket.com/public-search?q=ethereum&limit_per_type=100&search_profiles=false&search_tags=false&keep_closed_markets=1" \
  "$OUT_DIR/gamma-search-ethereum.json"

fetch \
  "https://gamma-api.polymarket.com/markets?active=true&closed=false&archived=false&limit=500&offset=0&order=volume&ascending=false" \
  "$OUT_DIR/gamma-markets-open.json"

fetch \
  "https://gamma-api.polymarket.com/markets?closed=true&archived=false&limit=500&offset=0&order=volume&ascending=false" \
  "$OUT_DIR/gamma-markets-closed.json"

echo "wrote real-data bundle to $OUT_DIR"
