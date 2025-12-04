# SPDX-License-Identifier: BSD-4-Clause
# Copyright (c) 2025, Renesas Electronics America Inc
# This file is part of the project under the BSD 4-Clause License.

from flask import Flask, jsonify, render_template
from flask_httpauth import HTTPBasicAuth
import os
import json

# --- Minimal changes ONLY ---
# Use installed paths by default; allow overrides via env for local dev
TEMPLATE_DIR = os.environ.get("ATPC_TEMPLATES", "/usr/local/share/at-powercycling/templates")
CONFIG_PATH = os.environ.get("ATPC_CONFIG", "/usr/local/etc/at-powercycling/gpio_config.json")
# --- End minimal changes ---

app = Flask(__name__, template_folder=TEMPLATE_DIR)  # (changed) point to installed templates
auth = HTTPBasicAuth()

# Users for Basic Authentication
users = {
    "admin": "password123",  # Change this to a secure password
}

@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username
    return None

# Function to load GPIO config from external file
def load_gpio_config():
    with open(CONFIG_PATH, "r") as f:  # (changed) read from installed config path
        return json.load(f)

# Load initial config
GPIO_CONFIG = load_gpio_config()

# Set GPIO state
def set_gpio(path, value):
    try:
        with open(path, "w") as f:
            f.write(str(value))
        return True
    except Exception as e:
        return str(e)

# Get GPIO state
def get_gpio_state(path):
    try:
        with open(path, "r") as f:
            return int(f.read().strip())
    except Exception as e:
        return str(e)

@app.route('/relay/<int:relay_id>/<int:state>', methods=['GET'])
@auth.login_required
def control_relay(relay_id, state):
    """Set the state of a relay to either 0 or 1."""
    if str(relay_id) not in GPIO_CONFIG["relays"] or state not in [0, 1]:
        return jsonify({"error": "Invalid relay ID or state (use 0/1)"}), 400
    relay_path = GPIO_CONFIG["relays"][str(relay_id)]["path"]
    result = set_gpio(relay_path, state)
    if result is True:
        return jsonify({"message": f"Relay {relay_id} set to {state}"}), 200
    return jsonify({"error": result}), 500

@app.route('/relay_state/<int:relay_id>', methods=['GET'])
@auth.login_required
def get_relay_state(relay_id):
    """Get the state of a relay."""
    if str(relay_id) not in GPIO_CONFIG["relays"]:
        return jsonify({"error": "Invalid relay ID"}), 400
    relay_path = GPIO_CONFIG["relays"][str(relay_id)]["path"]
    state = get_gpio_state(relay_path)
    if isinstance(state, int):
        return jsonify({"relay_id": relay_id, "state": state}), 200
    return jsonify({"error": state}), 500

@app.route('/reload_config', methods=['GET', 'POST'])
@auth.login_required
def reload_config():
    """Reload the GPIO configuration from the JSON file."""
    global GPIO_CONFIG
    try:
        GPIO_CONFIG = load_gpio_config()
        return jsonify({"message": "GPIO config reloaded"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
@auth.login_required
def home():
    """Home page showing a simple UI for controlling the relays."""
    return render_template('index.html', relays=GPIO_CONFIG["relays"])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
