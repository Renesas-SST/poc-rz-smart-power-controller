# SPDX-License-Identifier: BSD-4-Clause
# Copyright (c) 2025, Renesas Electronics America Inc
# This file is part of the project under the BSD 4-Clause License.

#!/bin/bash
set -euo pipefail

# Installed locations; can be overridden via env
CONFIG_FILE="${ATPC_CONFIG:-/usr/local/etc/at-powercycling/gpio_config.json}"
FLASK_SCRIPT="${ATPC_API:-/usr/local/bin/gpio_api_c.py}"
SETUP_SCRIPT="${ATPC_SETUP:-/usr/local/bin/gpio_setup.sh}"

VAR_DIR="/var/run/at-powercycling"
LOG_DIR="/var/log/at-powercycling"
SERVER_PID_FILE="$VAR_DIR/flask_server.pid"
LOG_FILE="$LOG_DIR/flask_server.log"

mkdir -p "$VAR_DIR" "$LOG_DIR"

start_server() {
  if [[ -f "$SERVER_PID_FILE" ]] && kill -0 "$(cat "$SERVER_PID_FILE")" 2>/dev/null; then
    echo "Server already running (PID: $(cat "$SERVER_PID_FILE"))"
    return 0
  fi
  nohup python3 "$FLASK_SCRIPT" >> "$LOG_FILE" 2>&1 &
  echo $! > "$SERVER_PID_FILE"
  echo "Server started (PID: $(cat "$SERVER_PID_FILE"))"
}

stop_server() {
  if [[ -f "$SERVER_PID_FILE" ]]; then
    kill "$(cat "$SERVER_PID_FILE")" 2>/dev/null || true
    rm -f "$SERVER_PID_FILE"
    echo "Server stopped"
  else
    echo "No running server found"
  fi
}

get_config() {
  cat "$CONFIG_FILE"
}

set_config() {
  echo "Enter new JSON (end with Ctrl-D):"
  tmp=$(mktemp)
  cat > "$tmp"
  if jq empty "$tmp" 2>/dev/null; then
    install -m 0644 "$tmp" "$CONFIG_FILE"
    echo "Config updated at $CONFIG_FILE"
  else
    echo "Invalid JSON; not updated"
  fi
  rm -f "$tmp"
}

run_setup() {
  "$SETUP_SCRIPT"
}

show_help() {
  cat <<'EOF'
Commands:
  start server        - start Flask server
  stop server         - stop Flask server
  getconfig           - print current JSON config
  setconfig           - replace JSON config (reads from stdin)
  run config setup    - apply config to GPIO via sysfs
  help                - show this help
  exit | quit         - leave
EOF
}

echo "AT-PowerCycling Terminal. Type 'help' for commands."
while true; do
  echo -n "> "
  read -r input || break
  case "$input" in
    "start server") start_server ;;
    "stop server")  stop_server ;;
    "getconfig")    get_config ;;
    "setconfig")    set_config ;;
    "run config setup") run_setup ;;
    "help")         show_help ;;
    "exit"|"quit")  echo "Goodbye."; break ;;
    *) echo "Unknown command. Type 'help'." ;;
  esac
done
