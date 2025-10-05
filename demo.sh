#!/usr/bin/env bash
set -euo pipefail

# Requires: curl, jq
BASE=http://localhost:8000
OUT_DIR=demo/output
mkdir -p "$OUT_DIR"

echo "1) Create attacker capsule..."
ATTACKER_RESPONSE=$(curl -s -X POST "$BASE/capsules" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "capsule-demo-attacker",
    "version": "v1",
    "role": "attack",
    "image": "ghcr.io/tessera/llama:attacker-v1",
    "entrypoint": "python run.py --mode attack",
    "env": {"LLM_MODEL":"meta-llama/Meta-Llama-3-8B-Instruct"},
    "config": {"service_url":"http://capsule-demo:9000"},
    "tags": ["demo","attack"],
    "owner":"demo",
    "description":"Demo attacker capsule"
  }')

echo "$ATTACKER_RESPONSE" | jq .
ATTACKER_ID=$(echo "$ATTACKER_RESPONSE" | jq -r '.id')
echo "Attacker id: $ATTACKER_ID"

echo
echo "2) Create defender capsule..."
DEFENDER_RESPONSE=$(curl -s -X POST "$BASE/capsules" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "capsule-demo-defender",
    "version": "v1",
    "role": "defense",
    "image": "ghcr.io/tessera/guardian:defender-v1",
    "entrypoint": "python run.py --mode defense",
    "env": {"LLM_MODEL":"meta-llama/Meta-Llama-3-8B-Instruct"},
    "config": {"service_url":"http://capsule-demo:9000"},
    "tags": ["demo","defense"],
    "owner":"demo",
    "description":"Demo defender capsule"
  }')

echo "$DEFENDER_RESPONSE" | jq .
DEFENDER_ID=$(echo "$DEFENDER_RESPONSE" | jq -r '.id')
echo "Defender id: $DEFENDER_ID"

echo
echo "3) Start multi battles (from_registry mode) — 2 matches, rounds=5"
START_RESP=$(curl -s -X POST "$BASE/battle/start_multi" \
  -H "Content-Type: application/json" \
  -d '{
    "mode":"from_registry",
    "attacker_role":"attack",
    "defender_role":"defense",
    "num_matches":2,
    "rounds":5,
    "interval_seconds":0.2,
    "concurrency":2
  }')

echo "$START_RESP" | jq .
RUN_IDS=$(echo "$START_RESP" | jq -r '.started_run_ids[]')
echo "Started runs: $RUN_IDS"

echo
echo "4) Poll statuses (will wait until all runs are completed)."
for id in $RUN_IDS; do
  echo "Polling $id ..."
  while true; do
    ST=$(curl -s "$BASE/battle/status/$id" | jq -r '.status + " | active:" + (.task_active|tostring)')
    echo -n "."
    if echo "$ST" | grep -E "completed|stopped" >/dev/null; then
      echo
      echo "$id finished -> $ST"
      echo "Fetching full record..."
      curl -s "$BASE/battle/get/$id" | jq . > "$OUT_DIR/$id.json"
      echo "Saved -> $OUT_DIR/$id.json"
      break
    fi
    sleep 1
  done
done

echo
echo "Done. Output directory: $OUT_DIR"
ls -la "$OUT_DIR"
