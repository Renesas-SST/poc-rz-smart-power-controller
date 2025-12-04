# SPDX-License-Identifier: BSD-4-Clause
# Copyright (c) 2025, Renesas Electronics America Inc
# This file is part of the project under the BSD 4-Clause License.

# GPIO Relay Control System

This project is a Flask-based web and terminal interface for controlling GPIO relays on Linux-based systems (like Renesas RZ or Raspberry Pi with exported GPIO pins).

---

## 📁 Components

### 1. `gpio_api_c.py` – Flask Web API
Provides a secure HTTP interface to control GPIO relays with Basic Authentication.

**Endpoints:**

| Endpoint                    | Method   | Description              |
| --------------------------- | -------- | ------------------------ |
| `/`                         | GET      | Home page with UI        |
| `/relay/<relay_id>/<state>` | GET      | Set relay state (0 or 1) |
| `/relay_state/<relay_id>`   | GET      | Get current relay state  |
| `/reload_config`            | GET/POST | Reload config from JSON  |

### 2. `gpio_config.json` – Configuration
Defines the GPIO pins and paths for each relay.

```json
{
  "relays": {
    "1": { "pin": 304, "path": "/sys/class/gpio/P23_0/value" },
    ...
  }
}
```

### 3. `gpio_setup.sh` – GPIO Initialization
Exports and sets direction for each pin defined in the config.

Usage:
```bash
chmod +x gpio_setup.sh
sudo ./gpio_setup.sh
```

### 4. `gpio_terminal.sh` – Terminal CLI
Interactive script to manage the Flask server and config.

**Commands:**
- `start server` – Starts the Flask server
- `stop server` – Stops it
- `getconfig` – Shows current config
- `setconfig` – Allows editing config
- `run config setup` – Executes GPIO setup

### 5. `index.html` – Web UI
Simple and responsive web page to control relays visually.

- Uses JavaScript to fetch and toggle relay state
- Colored indicators show ON/OFF status
- Uses the Flask backend API

---

## 🔄 Workflow

1. Run `gpio_terminal.sh` and start the server
2. Execute `run config setup` to export GPIO pins
3. Open the browser to the server's IP: `http://<your-ip>:5000`
4. Use UI or API to control relays

---

## 🔒 Security

- Basic Authentication (change default password!)
- Make sure to secure the server on deployment (use HTTPS, firewall, etc.)

---

## 🧰 Requirements

- Python 3
- Flask, flask_httpauth
- A Linux system with `/sys/class/gpio` interface

Install dependencies:
```bash
pip install flask flask_httpauth
```

---

## 🚀 Running

```bash
# Run from terminal:
./gpio_terminal.sh
```

Or manually:
```bash
python3 gpio_api_c.py
```

Then visit `http://localhost:5000` or `<your-device-ip>:5000`

---
# Systemd unit (packaging)

- Canonical unit installed by the package: `rz-smart-power-controller.service`.
- The unit template lives at `src/rz-smart-power-controller.service` and is processed by CMake during the build.
- When installed the package places the unit under `/usr/local/lib/systemd/system/rz-smart-power-controller.service` (respecting the configured install prefix). The package `postinst` enables and attempts to start the unit automatically; `prerm` will stop/disable and remove it on uninstall.

If you previously used a wrapper-based unit that invoked `gpio_terminal.sh`, that legacy unit has been removed from the source tree — use the packaged `rz-smart-power-controller.service` for deployments.
