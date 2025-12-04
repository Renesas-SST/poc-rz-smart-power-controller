# SPDX-License-Identifier: BSD-4-Clause
# Copyright (c) 2025, Renesas Electronics America Inc
# This file is part of the project under the BSD 4-Clause License.

#!/bin/bash
set -euo pipefail

# Installed locations; can be overridden via env
CONFIG_FILE="${RZSPC_CONFIG:-/usr/local/etc/rz-smart-power-controller/gpio_config.json}"
FLASK_SCRIPT="${RZSPC_API:-/usr/local/bin/gpio_api_c.py}"
SETUP_SCRIPT="${RZSPC_SETUP:-/usr/local/bin/gpio_setup.sh}"
PARSER="${RZSPC_PARSER:-/usr/local/bin/gpio_config_tool.py}"

VAR_DIR="/var/run/rz-smart-power-controller"
LOG_DIR="/var/log/rz-smart-power-controller"
SERVER_PID_FILE="$VAR_DIR/flask_server.pid"
LOG_FILE="$LOG_DIR/flask_server.log"

mkdir -p "$VAR_DIR" "$LOG_DIR"

start_server() {
	systemctl start rz-smart-power-controller
}

stop_server() {
	systemctl stop rz-smart-power-controller
}

get_config() {
	cat "$CONFIG_FILE"
}

set_config() {
	echo "Enter new JSON (end with Ctrl-D):"
	tmp=$(mktemp)
	cat > "$tmp"
	if command -v python3 >/dev/null 2>&1 && command -v "$PARSER" >/dev/null 2>&1 && python3 "$PARSER" validate "$tmp"; then
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
	cat <<-'EOF'
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

echo "RZ Smart Power Controller Terminal. Type 'help' for commands."
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
