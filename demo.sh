#!/usr/bin/env bash
set -euo pipefail

# Demo script: register two capsules, start multi matches from registry,
# poll until completion, evaluate, then trigger evolution and save artifacts.
#
# Usage:
#   ./demo.sh
#   BASE=http://localhost:8000 NUM_MATCHES=2 ROUNDS=5 ./demo.sh
# Optional env:
#   ORCH_CONTAINER - name of the orchestrator container (default: tessera-orchestrator)
#   INJECT_BREACHES - "true" to enable post-run injection (default: true)
#   INJECT_PROB - probability per-round to mark breach when injecting (default: 0.30)

: "${BASE:=http://localhost:8000}"
: "${OUT_DIR:=demo/output}"
: "${NUM_MATCHES:=2}"
: "${ROUNDS:=5}"
: "${INTERVAL_SECONDS:=0.2}"
: "${CONCURRENCY:=2}"
: "${POLL_TIMEOUT:=120}"   # seconds per-run poll timeout
: "${POLL_SLEEP:=1}"
: "${ORCH_CONTAINER:=tessera-orchestrator}"
: "${INJECT_BREACHES:=true}"
: "${INJECT_PROB:=0.30}"

# Tools required
command -v curl >/dev/null 2>&1 || { echo "curl required. install and retry."; exit 2; }
command -v jq >/dev/null 2>&1 || { echo "jq required. install and retry."; exit 2; }
command -v docker >/dev/null 2>&1 || { echo "docker required. install and retry."; exit 2; }

mkdir -p "$OUT_DIR"
TMP_RESP="$(mktemp)"
trap 'rm -f "$TMP_RESP"' EXIT

echo "BASE=$BASE  NUM_MATCHES=$NUM_MATCHES  ROUNDS=$ROUNDS  CONCURRENCY=$CONCURRENCY"
echo "Output dir: $OUT_DIR"
echo "Orchestrator container: $ORCH_CONTAINER"
echo "Inject breaches: $INJECT_BREACHES (prob=$INJECT_PROB)"
echo

# ---------- helpers ----------
post_json() {
  local url=$1
  local data=$2
  http_code=$(curl -sS -o "$TMP_RESP" -w "%{http_code}" -X POST "$url" \
    -H "Content-Type: application/json" --data-binary "$data" || echo "000")
  echo "$http_code"
}

get_json() {
  local url=$1
  http_code=$(curl -sS -o "$TMP_RESP" -w "%{http_code}" "$url" || echo "000")
  echo "$http_code"
}

create_capsule() {
  local payload=$1
  local url="$BASE/capsules"
  code=$(post_json "$url" "$payload")
  body=$(cat "$TMP_RESP")
  if [[ "$code" =~ ^2 ]]; then
    echo "$body"
  else
    echo "ERROR creating capsule (HTTP $code):"
    echo "$body"
    exit 3
  fi
}

start_multi() {
  local payload=$1
  local url="$BASE/battle/start_multi"
  code=$(post_json "$url" "$payload")
  body=$(cat "$TMP_RESP")
  if [[ "$code" =~ ^2 ]]; then
    echo "$body"
  else
    echo "ERROR starting multi battles (HTTP $code):"
    echo "$body"
    exit 4
  fi
}

poll_status() {
  local run=$1
  local timeout_seconds=$2
  local elapsed=0
  local last=""
  while true; do
    status_code=$(get_json "$BASE/battle/status/$run" || echo "000")
    body=$(cat "$TMP_RESP")
    if [[ "$status_code" =~ ^2 ]]; then
      stat=$(echo "$body" | jq -r '.status // empty')
      active=$(echo "$body" | jq -r '.task_active // false')
      echo -n "."
      if [[ "$stat" == "completed" || "$stat" == "stopped" ]]; then
        echo
        echo "Run $run finished -> status=$stat task_active=$active"
        return 0
      fi
    else
      echo "status HTTP $status_code for $run"
    fi

    sleep "$POLL_SLEEP"
    elapsed=$((elapsed + POLL_SLEEP))
    if [ "$elapsed" -ge "$timeout_seconds" ]; then
      echo
      echo "Timeout waiting for run $run after ${timeout_seconds}s. Last response:"
      echo "$body" | jq . || echo "$body"
      return 2
    fi
  done
}

# ---------- Inject demo breaches (post-run) ----------
# This edits the persisted /data/battles/<run>.json inside the orchestrator container:
# - randomly marks some rounds as breach=true according to given probability
# - appends a breach token to defender_output if present (so text-based detectors can also pick it up)
# - recalculates breaches, total_rounds, breach_rate
# Requires docker and container access.
inject_demo_breaches() {
  local run=$1
  local prob=${2:-$INJECT_PROB}
  local container=${3:-$ORCH_CONTAINER}

  # only run if injection enabled
  if [[ "${INJECT_BREACHES,,}" != "true" ]]; then
    echo "Injection disabled (INJECT_BREACHES=${INJECT_BREACHES}) — skipping injection for $run"
    return 0
  fi

  echo "Injecting demo breaches into run $run (prob=$prob) in container $container..."

  docker exec -i "$container" sh -lc "python - <<'PY'
import json, random, sys, pathlib
run = sys.argv[1]
prob = float(sys.argv[2])
p = pathlib.Path('/data/battles') / (run + '.json')
if not p.exists():
    print('persisted run file not found:', p)
    sys.exit(1)
data = json.loads(p.read_text())
rounds = data.get('rounds', [])
if not rounds:
    print('no rounds to mark')
else:
    breaches = 0
    for r in rounds:
        # probabilistically mark as breach
        if random.random() < prob:
            r['breach'] = True
            # ensure defender_output contains a visible breach token (optional)
            d = r.get('defender_output')
            if isinstance(d, str):
                if 'breach=true' not in d:
                    r['defender_output'] = d + ' breach=true'
            else:
                r['defender_output'] = 'breach=true'
        else:
            r['breach'] = False
        if r.get('breach'):
            breaches += 1
    total = len(rounds)
    br = float(breaches) / total if total else 0.0
    data['breaches'] = breaches
    data['total_rounds'] = total
    data['breach_rate'] = br
    p.write_text(json.dumps(data, indent=2))
    print('updated', p, 'breaches', breaches, 'breach_rate', br)
PY
" "$run" "$prob"

  # copy the updated persisted file back into local OUT_DIR for demo record
  docker cp "$container:/data/battles/${run}.json" "$OUT_DIR/${run}.json" >/dev/null 2>&1 || true
  echo "Copied updated persisted run -> $OUT_DIR/${run}.json"
}

# Decide strategy automatically then call /evolve/<run>.
# If capsule_id & target_role provided, include them in payload so evolution mutates exact capsule.
trigger_evolution_for_run() {
  local run=$1
  local run_file="$OUT_DIR/${run}.json"

  # get evaluation
  if ! get_json "$BASE/evolve/status/$run"; then
    echo "Failed to get eval status for run $run"
    return 1
  fi
  eval_body=$(cat "$TMP_RESP")
  echo "Evaluation for $run:"
  echo "$eval_body" | jq .

  breach_rate=$(echo "$eval_body" | jq -r '.breach_rate // 0' 2>/dev/null || echo 0)
  strategy="attack_explore"
  if awk "BEGIN {exit !($breach_rate > 0)}"; then
    strategy="defense_harden"
  fi

  # prefer to pass explicit capsule id if present in saved run record
  capsule_id=""
  target_role=""
  if [[ -f "$run_file" ]]; then
    # preferred top-level fields
    capsule_id=$(jq -r '.defender_id // .attacker_id // empty' "$run_file")
    # but choose defender if breaches > 0
    if awk "BEGIN {exit !($breach_rate > 0)}"; then
      # defender preferred
      capsule_id=$(jq -r '.defender_id // empty' "$run_file")
      target_role="defense"
    else
      capsule_id=$(jq -r '.attacker_id // empty' "$run_file")
      target_role="attack"
    fi

    # fallback to meta.* entries
    if [ -z "$capsule_id" ] || [ "$capsule_id" == "null" ]; then
      capsule_id=$(jq -r '.meta.defender_id // .meta.attacker_id // empty' "$run_file")
    fi

    # fallback to first round
    if [ -z "$capsule_id" ]; then
      capsule_id=$(jq -r '.rounds[0].defender_id // .rounds[0].attacker_id // empty' "$run_file")
    fi
  fi

  # build payload: always include strategy; include capsule_id & target_role if available
  if [ -n "$capsule_id" ]; then
    echo "Triggering evolution (strategy=$strategy) for run $run targeted at capsule $capsule_id (role=${target_role:-auto})..."
    payload=$(jq -nc --arg s "$strategy" --arg cid "$capsule_id" --arg tr "${target_role:-}" \
      '{
         strategy: $s,
         capsule_id: ($cid // null),
         target_role: (if $tr=="" then null else $tr end)
       }')
  else
    echo "Triggering evolution (strategy=$strategy) for run $run (no capsule id found, letting server pick)..."
    payload=$(jq -nc --arg s "$strategy" '{ strategy: $s }')
  fi

  code=$(post_json "$BASE/evolve/$run" "$payload")
  evolve_body=$(cat "$TMP_RESP")
  if [[ "$code" =~ ^2 ]]; then
    echo "Evolution result:"
    echo "$evolve_body" | jq .
    echo "$evolve_body" | jq . > "$OUT_DIR/${run}_evolve.json"
    has_mutated=$(echo "$evolve_body" | jq -r '.mutated != null')
    if [[ "$has_mutated" == "true" ]]; then
      capsule_id_new=$(echo "$evolve_body" | jq -r '.mutated.id')
      echo "$evolve_body" | jq '.mutated' > "$OUT_DIR/capsule_${capsule_id_new}.json"
      echo "Saved mutated capsule -> $OUT_DIR/capsule_${capsule_id_new}.json"
    fi
    return 0
  else
    echo "ERROR evolving run (HTTP $code):"
    echo "$evolve_body" | jq . || echo "$evolve_body"
    return 1
  fi
}

# ---------- 1) Create attacker ----------
echo "1) Creating attacker capsule..."
ATTACKER_PAY=$(
cat <<'JSON'
{
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
}
JSON
)
ATTACKER_RESP=$(create_capsule "$ATTACKER_PAY")
echo "$ATTACKER_RESP" | jq .
ATTACKER_ID=$(echo "$ATTACKER_RESP" | jq -r '.id // empty')
echo "Attacker id: ${ATTACKER_ID:-<none>}"
echo

# ---------- 2) Create defender ----------
echo "2) Creating defender capsule..."
DEFENDER_PAY=$(
cat <<'JSON'
{
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
}
JSON
)
DEFENDER_RESP=$(create_capsule "$DEFENDER_PAY")
echo "$DEFENDER_RESP" | jq .
DEFENDER_ID=$(echo "$DEFENDER_RESP" | jq -r '.id // empty')
echo "Defender id: ${DEFENDER_ID:-<none>}"
echo

# ---------- 3) Start multi battles (from_registry) ----------
echo "3) Starting multi battles (from_registry mode)..."
START_PAY=$(
cat <<JSON
{
  "mode":"from_registry",
  "attacker_role":"attack",
  "defender_role":"defense",
  "num_matches": $NUM_MATCHES,
  "rounds": $ROUNDS,
  "interval_seconds": $INTERVAL_SECONDS,
  "concurrency": $CONCURRENCY
}
JSON
)
start_out=$(start_multi "$START_PAY")
echo "$start_out" | jq .
STARTED_RUNS=$(echo "$start_out" | jq -r '.started_run_ids[]?')
if [ -z "$STARTED_RUNS" ]; then
  echo "No runs started. Response:"
  echo "$start_out" | jq .
  exit 5
fi
echo "Started runs: $STARTED_RUNS"
echo

# ---------- 4) Poll statuses until completed + save runs ----------
echo "4) Polling statuses (timeout ${POLL_TIMEOUT}s per run)..."
for run in $STARTED_RUNS; do
  echo "Polling run: $run"
  if ! poll_status "$run" "$POLL_TIMEOUT"; then
    echo "Polling failed for $run"
    exit 6
  fi

  # fetch full record and save
  if ! get_json "$BASE/battle/get/$run"; then
    echo "Failed to fetch run $run record"
    exit 7
  fi
  cat "$TMP_RESP" | jq . > "$OUT_DIR/$run.json"
  echo "Saved -> $OUT_DIR/$run.json"

  # === NEW: inject demo breaches into persisted run file inside orchestrator (so UI shows breach_rate)
  inject_demo_breaches "$run" "$INJECT_PROB"

  # print attacker/defender ids discovered in run record
  atk_id=$(jq -r '.attacker_id // .meta.attacker_id // .rounds[0].attacker_id // empty' "$OUT_DIR/$run.json" || echo "")
  def_id=$(jq -r '.defender_id // .meta.defender_id // .rounds[0].defender_id // empty' "$OUT_DIR/$run.json" || echo "")
  echo "Run $run attacker_id: ${atk_id:-<none>} defender_id: ${def_id:-<none>}"

  # ---------- 5) Evaluate & trigger evolution ----------
  if ! trigger_evolution_for_run "$run"; then
    echo "Evolution failed for run $run (continuing to next run)"
  fi

  echo
done

echo
echo "All done. Output files:"
ls -la "$OUT_DIR"
