#!/bin/bash

# Zen MCP Management Script - Uses stdio interface

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ZEN_SCRIPT="python ${ROOT_DIR}/integrations/zen-mcp/main.py"

echo "🧘‍♀️  ZEN MCP MANAGEMENT"
echo "===================="

# Function to call Zen tools
call_zen() {
    local method="$1"
    local params="$2"
    local req_id=$(date +%s)
    
    local json_req="{\"jsonrpc\":\"2.0\",\"id\":$req_id,\"method\":\"$method\""
    if [ ! -z "$params" ]; then
        json_req="$json_req,\"params\":$params"
    fi
    json_req="$json_req}"
    
    echo "$json_req" | $ZEN_SCRIPT | jq .
}

# Low-noise JSON call helper (prints raw JSON only)
zen_call_raw() {
    local tool="$1"
    local args_json="$2"
    local req
    req=$(cat <<EOF
{"jsonrpc":"2.0","id":$(date +%s),"method":"tools/call","params":{"name":"${tool}","arguments":${args_json}}}
EOF
)
    printf "%s" "$req" | tr -d '\n' | $ZEN_SCRIPT
}

# Background watch loop: poll get_context every N seconds and print new items
# Args: session_id interval expected_match provider
watch_loop() {
  local session_id="$1"
  local interval="$2"
  local expected="$3"
  local provider_filter="$4"

  local pid_file="${ROOT_DIR}/zen/.watch-${session_id}.pid"
  local log_file="${ROOT_DIR}/zen/.watch-${session_id}.log"
  trap 'rm -f "${pid_file}" >/dev/null 2>&1' EXIT
  echo $$ >"$pid_file"

  # Determine starting sinceTs as the latest existing ts (so we only show new)
  local latest_ts
  latest_ts=$(zen_call_raw "zen/get_context" "{\"sessionId\":\"${session_id}\",\"limit\":1}" \
    | jq -r '.result.items[-1].ts // 0' 2>/dev/null || echo 0)
  if ! [[ "$latest_ts" =~ ^[0-9]+$ ]]; then latest_ts=0; fi

  echo "[watch ${session_id}] starting at sinceTs=${latest_ts}, interval=${interval}s" | tee -a "$log_file"

  while :; do
    # Fetch items since latest_ts (exclusive)
    local resp
    resp=$(zen_call_raw "zen/get_context" "{\"sessionId\":\"${session_id}\",\"sinceTs\":${latest_ts}}")
    # Extract new items
    local count
    count=$(echo "$resp" | jq -r '.result.items | length // 0' 2>/dev/null || echo 0)
    if [[ "$count" -gt 0 ]]; then
      # Print each item in a readable line and update latest_ts
      echo "$resp" | jq -r \
        '.result.items[] | [.ts, .role, (.provider // ""), (if (.content|type)=="string" then .content else (.content|tostring) end)] | @tsv' \
        | while IFS=$'\t' read -r ts role prov content; do
            echo "[$(date -u +%H:%M:%S)] ts=${ts} role=${role} provider=${prov} :: ${content}" | tee -a "$log_file"
            latest_ts="$ts"
            # Match expected content if provided
            if [[ -n "$expected" ]]; then
              if [[ -n "$provider_filter" ]]; then
                if [[ "$prov" == "$provider_filter" && "$content" == *"$expected"* ]]; then
                  echo "[watch ${session_id}] ✅ matched expected '${expected}' from ${provider_filter}. Exiting." | tee -a "$log_file"
                  exit 0
                fi
              else
                if [[ "$content" == *"$expected"* ]]; then
                  echo "[watch ${session_id}] ✅ matched expected '${expected}'. Exiting." | tee -a "$log_file"
                  exit 0
                fi
              fi
            fi
          done
    fi
    sleep "$interval"
  done
}

case "$1" in
    "register")
        name="${2:-test-agent}"
        shift 2
        caps="$*"
        
        if [ -z "$caps" ]; then
            caps='["chat","analyze"]'
        else
            # Convert args to JSON array
            caps=$(echo "$caps" | sed 's/[^ ]*/"&"/g' | sed 's/ /, /g' | sed 's/^/[/; s/$/]/')
        fi
        
        echo "📝 Registering agent: $name with capabilities: $caps"
        call_zen "tools/call" "{\"name\":\"zen/register_agent\",\"arguments\":{\"name\":\"$name\",\"capabilities\":$caps}}"
        ;;
        
    "list")
        echo "📋 Listing all agents:"
        call_zen "tools/call" "{\"name\":\"zen/list_agents\",\"arguments\":{}}"
        ;;
        
    "create-session")
        echo "🔧 Creating new session..."
        call_zen "tools/call" "{\"name\":\"zen/create_session\",\"arguments\":{\"agentIds\":[],\"tags\":[\"test\"],\"ttlMs\":3600000}}"
        ;;
        
    "tools")
        echo "🛠️  Available tools:"
        call_zen "tools/list" ""
        ;;

    "handoff")
        # Usage: handoff <target-agent> <title and instructions...>
        # Creates a session, posts a structured handoff message, publishes a redis event,
        # and starts a background watcher that exits on 'DONE' from the target provider.
        target_agent="${2:-claude-code-agent}"
        shift 2 || true
        handoff_text="$*"
        if [ -z "$handoff_text" ]; then
          handoff_text="Implement the requested change. Provide:
1) Summary, 2) Minimal diff, 3) Tests green, 4) Risk/rollback."
        fi

        echo "🧾 Creating handoff for: $target_agent"
        create_req='{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"zen/create_session","arguments":{"agentIds":["'"$target_agent"'"],"tags":["handoff","impl"],"ttlMs":7200000}}}'
        session_json=$(echo "$create_req" | $ZEN_SCRIPT)
        session_id=$(echo "$session_json" | jq -r '.result.session.id // empty')
        if [ -z "$session_id" ] || [ "$session_id" = "null" ]; then
            echo "❌ Failed to create session" >&2
            echo "$session_json" | jq . >&2
            exit 1
        fi
        echo "🆔 Session: $session_id"
        mkdir -p "${ROOT_DIR}/zen" 2>/dev/null || true
        echo "$session_id" > "${ROOT_DIR}/zen/.last_session"

        # Post structured handoff message to context
        now_iso=$(date -u +%Y-%m-%dT%H:%M:%SZ)
        esc_text=$(printf '%s' "$handoff_text" | sed 's/"/\\"/g')
        handoff_body="Handoff @ ${now_iso}\n\nTask:\n${handoff_text}\n\nAcceptance:\n- Diff <300 LOC, ≤3 modules\n- Run: npm run check, pyright, pytest/vitest\n- Include test notes\n- PR against develop\n\nPlan template:\n- Step 1\n- Step 2\n- Step 3\n\nReport DONE when PR is opened and checks are green."
        esc_body=$(printf '%s' "$handoff_body" | sed 's/"/\\"/g')
        add_req='{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"zen/add_context","arguments":{"sessionId":"'"$session_id"'","role":"user","provider":"codex-cli","content":"'"$esc_body"'"}}}'
        echo "$add_req" | $ZEN_SCRIPT | jq .

        # Publish redis event to notify implementer
        if command -v redis-cli >/dev/null 2>&1; then
          ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
          evt=$(printf '{"type":"handoff","target":"%s","sessionId":"%s","ts":"%s","title":"%s"}' \
                "$target_agent" "$session_id" "$ts" "$esc_text")
          redis-cli -h 127.0.0.1 -p 6379 PUBLISH "zen:events" "$evt" >/dev/null || true
          echo "📣 Published handoff event on zen:events"
        fi

        # Start background watcher looking for DONE from the implementer
        ( watch_loop "$session_id" 10 'DONE' "$target_agent" ) &
        echo "🔭 Auto-watch started (PID $!). It will stop when it sees: 'DONE' from ${target_agent}."
        ;;

    "watch")
        # Usage: watch <session-id> [--interval 10] [--until "ACK OK"] [--provider "claude-code-agent"]
        if [ -z "$2" ]; then
          echo "❌ Usage: $0 watch <session-id> [--interval 10] [--until \"ACK OK\"] [--provider <name>]" >&2
          exit 1
        fi
        session_id="$2"; shift 2
        interval=10
        until_text=""
        provider=""
        while [[ $# -gt 0 ]]; do
          case "$1" in
            --interval) interval="${2:-10}"; shift 2 ;;
            --until) until_text="${2:-}"; shift 2 ;;
            --provider) provider="${2:-}"; shift 2 ;;
            *) echo "Unknown option: $1" >&2; exit 2 ;;
          esac
        done
        echo "👂 Starting background watch for session ${session_id} (interval=${interval}s, until='${until_text}', provider='${provider}')"
        ( watch_loop "$session_id" "$interval" "$until_text" "$provider" ) & disown
        echo "PID: $!  (stored in zen/.watch-${session_id}.pid)"
        ;;

    "stop-watch")
        # Usage: stop-watch <session-id>
        if [ -z "$2" ]; then
          echo "❌ Usage: $0 stop-watch <session-id>" >&2
          exit 1
        fi
        session_id="$2"
        pid_file="${ROOT_DIR}/zen/.watch-${session_id}.pid"
        if [ -f "$pid_file" ]; then
          pid=$(cat "$pid_file")
          if kill "$pid" >/dev/null 2>&1; then
            echo "🛑 Stopped watch (pid $pid) for session ${session_id}"
            rm -f "$pid_file"
          else
            echo "⚠️  Could not stop pid $pid; removing stale pid file"
            rm -f "$pid_file"
          fi
        else
          echo "No pid file found at $pid_file"
        fi
        ;;

    "send-test")
        # Usage: send-test [agent-id] [message...]
        # Creates a session and appends a user message so an external agent can respond.
        target_agent="${2:-claude-code-agent}"
        shift 2 || true
        test_msg="$*"
        if [ -z "$test_msg" ]; then
            test_msg="Ping from codex-cli. Please reply with: ACK OK"
        fi

        echo "📨 Creating probe session for agent: $target_agent"
        create_req='{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"zen/create_session","arguments":{"agentIds":["'"$target_agent"'"],"tags":["probe"],"ttlMs":3600000}}}'
        session_json=$(echo "$create_req" | $ZEN_SCRIPT)
        session_id=$(echo "$session_json" | jq -r '.result.session.id // empty')
        if [ -z "$session_id" ] || [ "$session_id" = "null" ]; then
            echo "❌ Failed to create session" >&2
            echo "$session_json" | jq . >&2
            exit 1
        fi
        echo "🆔 Session: $session_id"
        mkdir -p "${ROOT_DIR}/zen" 2>/dev/null || true
        echo "$session_id" > "${ROOT_DIR}/zen/.last_session"

        echo "✏️  Adding context message: $test_msg"
        add_req='{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"zen/add_context","arguments":{"sessionId":"'"$session_id"'","role":"user","provider":"codex-cli","content":"'"$(printf '%s' "$test_msg" | sed 's/"/\\"/g')"'"}}}'
        echo "$add_req" | $ZEN_SCRIPT | jq .

        # Optional: publish a Redis event to nudge listeners, if redis-cli exists
        if command -v redis-cli >/dev/null 2>&1; then
            ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
            evt=$(printf '{"type":"command","target":"%s","sessionId":"%s","ts":"%s","message":"%s"}' \
                  "$target_agent" "$session_id" "$ts" "$test_msg")
            redis-cli -h 127.0.0.1 -p 6379 PUBLISH "zen:events" "$evt" >/dev/null || true
            echo "📣 Published command event on redis channel zen:events"
        fi

        echo "👀 Watch for responses:"
        echo "  tail -f \"${ROOT_DIR}/zen/context/$session_id.jsonl\"   # live file view"
        echo "  scripts/zen-mcp-cli.sh getctx $session_id 10  # last 10 entries"
        echo "  $0 watch $session_id --interval 10 --until 'ACK OK' --provider 'claude-code-agent'  # background watch"

        # Auto-start background watcher that exits when expected text appears
        ( watch_loop "$session_id" 10 'ACK OK' 'claude-code-agent' ) &
        echo "🔭 Auto-watch started (PID $!). It will stop when it sees: 'ACK OK' from claude-code-agent."
        ;;
        
    "help")
        echo "Usage: $0 {register|list|create-session|tools} [args]"
        echo ""
        echo "Examples:"
        echo "  $0 register my-agent chat analyze refactor"
        echo "  $0 list"
        echo "  $0 create-session"
        echo "  $0 tools"
        ;;
        
    *)
        echo "Unknown command: $1"
        echo "Use '$0 help' for usage"
        exit 1
        ;;
esac
