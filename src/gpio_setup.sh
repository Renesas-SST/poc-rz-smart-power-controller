# SPDX-License-Identifier: BSD-4-Clause
# Copyright (c) 2025, Renesas Electronics America Inc
# This file is part of the project under the BSD 4-Clause License.

#!/bin/bash
set -euo pipefail

CONFIG_FILE="${ATPC_CONFIG:-/usr/local/etc/at-powercycling/gpio_config.json}"
GPIO_SYS="/sys/class/gpio"

if [[ ! -d "$GPIO_SYS" ]]; then
  echo "GPIO sysfs not found at $GPIO_SYS"
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required; please install it"
  exit 1
fi

# Iterate relays (pin + path) from config
jq -r '.relays[] | "\(.pin) \(.path)"' "$CONFIG_FILE" | while read -r pin rawpath; do
  # Export if needed
  [[ -d "$GPIO_SYS/gpio$pin" ]] || echo "$pin" > "$GPIO_SYS/export"

  # Prefer canonical gpioN directory; fall back to label if present
  dir="$GPIO_SYS/gpio$pin"
  lbl="$(basename "$(dirname "$rawpath")")"  # e.g. P23_0 from /sys/class/gpio/P23_0/value
  [[ -n "$lbl" && -d "$GPIO_SYS/$lbl" ]] && dir="$GPIO_SYS/$lbl"

  # Set direction/value (best effort)
  echo out > "$dir/direction" 2>/dev/null || echo "warn: cannot set direction for $dir"
  echo 0   > "$dir/value"     2>/dev/null || echo "warn: cannot set value for $dir"

  echo "Configured GPIO $pin at $(basename "$dir")"
done
