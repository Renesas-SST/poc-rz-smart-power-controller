#!/bin/sh
# SPDX-License-Identifier: BSD-4-Clause
set -e

# This script sets up GPIO pins based on the kernel version.
# For kernel >= 6.x, it uses a Python API with libgpiod.
# For kernel < 6.x, it uses legacy sysfs GPIO logic.
# It reads configuration from a JSON file including authentication credentials.

# Configuration
CONFIG_FILE="${RZSPC_CONFIG:-/usr/local/etc/rz-smart-power-controller/gpio_config.json}"
PARSER="${RZSPC_PARSER:-/usr/local/bin/gpio_config_tool.py}"
API_SCRIPT="${RZSPC_API:-/usr/local/bin/gpio_api_c.py}"
API_PORT="${RZSPC_PORT:-5000}"
API_URL="http://localhost:$API_PORT"

# Extract auth credentials from JSON using Python
AUTH_USER=$(python3 -c "import json; d=json.load(open('$CONFIG_FILE')); print(d.get('auth', {}).get('username', ''))")
AUTH_PASS=$(python3 -c "import json; d=json.load(open('$CONFIG_FILE')); print(d.get('auth', {}).get('password', ''))")


if [ -z "$AUTH_USER" ] || [ -z "$AUTH_PASS" ]; then
	echo "Authentication details missing in config" >&2
	exit 1
fi

# Validate config
python3 "$PARSER" validate "$CONFIG_FILE" || {
	echo "Invalid GPIO config" >&2
	exit 1
}

# Detect kernel version
KERNEL_MAJOR=$(uname -r | cut -d. -f1)
echo "Detected kernel version: $(uname -r)"

if [ "$KERNEL_MAJOR" -ge 6 ]; then
	echo "Kernel >= 6.x: Using Python API with libgpiod"

	check_api() {
		curl -s -u "$AUTH_USER:$AUTH_PASS" "$API_URL/reload_config" >/dev/null
	}

	if ! pgrep -f "$API_SCRIPT" >/dev/null || ! check_api; then
		echo "Starting GPIO API service..."
		nohup python3 "$API_SCRIPT" >/var/log/gpio_api.log 2>&1 &
		for i in $(seq 1 10); do
			sleep 1
			if check_api; then
				echo "GPIO API is up and running."
				break
			fi
			echo "Waiting for API to start..."
		done
	fi
	# Reload config to request GPIO lines
	echo "Reloading GPIO config in API..."
	curl -s -u "$AUTH_USER:$AUTH_PASS" "$API_URL/reload_config" >/dev/null

	# Initialize relays using relay IDs (keys from JSON)
	for relay_id in $(python3 -c "import json; d=json.load(open('$CONFIG_FILE')); print(' '.join(d.get('relays', {}).keys()))"); do
		echo "Initializing relay $relay_id..."
		curl -s -u "$AUTH_USER:$AUTH_PASS" "$API_URL/relay/$relay_id/0" >/dev/null
	done
	echo "GPIO setup complete using libgpiod API."

else
	echo "Kernel < 6.x: Using legacy sysfs GPIO logic"
	GPIO_SYS="/sys/class/gpio"
	if [ ! -d "$GPIO_SYS" ]; then
		echo "GPIO sysfs not found at $GPIO_SYS" >&2
		exit 1
	fi

	python3 "$PARSER" list "$CONFIG_FILE" | while read -r kvpairs; do
		pin="" path="" active=""
		for kv in $kvpairs; do
			key="${kv%%=*}"
			val="${kv#*=}"
			case "$key" in
				pin) pin="$val" ;;
				path) path="$val" ;;
				active) active="$val" ;;
			esac
		done

		if [ -n "$pin" ] && [ -n "$path" ]; then
			if [ ! -d "$GPIO_SYS/gpio$pin" ]; then
				echo "$pin" > "$GPIO_SYS/export"
			fi
			dir="$GPIO_SYS/gpio$pin"
			echo out > "$dir/direction" 2>/dev/null || echo "warn: cannot set direction for $dir"
			if [ "$active" = "low" ]; then
				echo 1 > "$dir/value" 2>/dev/null || echo "warn: cannot set value for $dir"
			else
				echo 0 > "$dir/value" 2>/dev/null || echo "warn: cannot set value for $dir"
			fi
			echo "Configured GPIO pin=$pin active=$active"
		fi
	done

	echo "GPIO setup complete using sysfs."
fi
exit 0
