# SPDX-License-Identifier: BSD-4-Clause
# Copyright (c) 2025, Renesas Electronics America Inc
# This file is part of the project under the BSD 4-Clause License.

from flask import Flask, jsonify, render_template
from flask_httpauth import HTTPBasicAuth
import os
import json
import platform
import subprocess
import signal
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

HAVE_LIB_GPIOD = False
pkg_name = None

try:
    import gpiod
    HAVE_LIB_GPIOD = True
except ImportError:
    logging.error("Please install python3-libgpiod: pip3 install gpiod")
    sys.exit(1)

def get_debian_package():
    current_file = os.path.abspath(__file__)
    try:
        result = subprocess.run(['dpkg-query', '-S', current_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        package_name = result.stdout.split(':')[0].strip()
        return package_name
    except subprocess.CalledProcessError:
        return None

TEMPLATE_DIR = None
CONFIG_PATH = None

def set_config_paths():
    global pkg_name
    pkg_name = get_debian_package()
    if pkg_name:
        logging.info(f"This file is part of the Debian package: {pkg_name}")
    else:
        logging.warning("This file is not part of any Debian package. Defaulting to 'rz-smart-power-controller'")
        pkg_name = "rz-smart-power-controller"
    return os.environ.get("ATPC_TEMPLATES", f"/usr/local/share/{pkg_name}/templates"), os.environ.get("ATPC_CONFIG", f"/usr/local/etc/{pkg_name}/gpio_config.json")

TEMPLATE_DIR, CONFIG_PATH = set_config_paths()

app = Flask(__name__, template_folder=TEMPLATE_DIR)
auth = HTTPBasicAuth()

users = {}
try:
    with open(CONFIG_PATH, 'r') as f:
        data = json.load(f)
        if 'auth' in data:
            users[data['auth'].get('username', 'admin')] = data['auth'].get('password', 'password123')
        else:
            users['admin'] = 'password123'
except Exception as e:
    logging.error(f'Failed to load auth from config: {e}')
    users['admin'] = 'password123'

kernel_version = platform.release()
gpio_interface = "sysfs"
GPIO_CONFIG = None
GPIO_LINE_MAP = None

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Unhandled exception: {e}")
    return jsonify({"error": "Internal Server Error"}), 500

@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username
    return None

def load_gpio_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Config file not found: {CONFIG_PATH}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in config: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error loading config: {e}")
        raise

def load_gpio_line_map():
    global GPIO_CONFIG, pkg_name
    gpio_lines = {}
    try:
        if gpio_interface == "gpiod":
            for relay in GPIO_CONFIG['relays']:
                chip = gpiod.Chip(GPIO_CONFIG['relays'][relay]['chip'])
                line_offset = GPIO_CONFIG['relays'][relay]['line']
                line = chip.get_line(line_offset)
                if line.is_requested():
                    logging.warning(f"Line {line_offset} already requested. Skipping.")
                    continue
                try:
                    line.request(consumer=pkg_name, type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])
                    gpio_lines[line_offset] = line
                    if GPIO_CONFIG['relays'][relay].get('active', 'high') == 'low':
                        print("Setting initial value to inactive (1) for active low")
                        logging.info(f"Setting initial value to inactive (1) for active low on line {line_offset}")
                        line.set_value(1)
                    else:
                        print("Setting initial value to inactive (0) for active high")
                        logging.info(f"Setting initial value to inactive (0) for active high on line {line_offset}")
                        line.set_value(0)
                    logging.info(f"Requested line {line_offset} on chip {GPIO_CONFIG['relays'][relay]['chip']}")
                except OSError as e:
                    logging.error(f"Failed to request line {line_offset}: {e}")
                    continue
        else:
            logging.info("Not a GPIOD system. Should not have called load_gpio_line_map. BUG?")
            raise RuntimeError("Invalid GPIO interface for loading line map.")
        return gpio_lines
    except Exception as e:
        logging.error(f"Error loading GPIO line map: {e}")
        raise

def set_gpio(relay_id, value):
    global GPIO_CONFIG, GPIO_LINE_MAP
    try:
        if gpio_interface == "gpiod":
            line_offset = GPIO_CONFIG['relays'][str(relay_id)]['line']
            if line_offset in GPIO_LINE_MAP:
                # Handle active low configuration support
                if GPIO_CONFIG['relays'][str(relay_id)].get('active', 'high') == 'low':
                    value = 0 if value else 1
                # Normal active high
                GPIO_LINE_MAP[line_offset].set_value(value)
                return True
            else:
                raise ValueError(f"Line {line_offset} not requested.")
        else:
            path = GPIO_CONFIG['relays'][str(relay_id)]['path'] + '/value'
            # Handle active low configuration support
            if GPIO_CONFIG['relays'][str(relay_id)].get('active', 'high') == 'low':
                value = 0 if value else 1
            # Normal active high
            else:
                value = 1 if value else 0
            with open(path, "w") as f:
                f.write(str(value))
            return True
    except Exception as e:
        logging.error(f"Error setting GPIO: {e}")
        return str(e)

def get_gpio_state(relay_id):
    global GPIO_CONFIG, GPIO_LINE_MAP
    try:
        if gpio_interface == "gpiod":
            line_offset = GPIO_CONFIG['relays'][str(relay_id)]['line']
            if line_offset in GPIO_LINE_MAP:
                if GPIO_CONFIG['relays'][str(relay_id)].get('active', 'high') == 'low':
                    return 0 if GPIO_LINE_MAP[line_offset].get_value() else 1
                return GPIO_LINE_MAP[line_offset].get_value()
            else:
                raise ValueError(f"Line {line_offset} not requested.")
        else:
            path = GPIO_CONFIG['relays'][str(relay_id)]['path'] + '/value'
            # Handle active low configuration support
            if GPIO_CONFIG['relays'][str(relay_id)].get('active', 'high') == 'low':
                with open(path, "r") as f:
                    return 0 if int(f.read().strip()) else 1
            # Normal active high
            with open(path, "r") as f:
                return int(f.read().strip())
    except Exception as e:
        logging.error(f"Error getting GPIO state: {e}")
        return str(e)

@app.route('/relay/<int:relay_id>/<int:state>', methods=['GET'])
@auth.login_required
def control_relay(relay_id, state):
    try:
        if str(relay_id) not in GPIO_CONFIG["relays"] or state not in [0, 1]:
            return jsonify({"error": "Invalid relay ID or state"}), 400
        result = set_gpio(relay_id, state)
        if result is True:
            return jsonify({"message": f"Relay {relay_id} set to {state}"}), 200
        return jsonify({"error": result}), 500
    except Exception as e:
        logging.error(f"Error in control_relay: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/relay_state/<int:relay_id>', methods=['GET'])
@auth.login_required
def get_relay_state(relay_id):
    try:
        if str(relay_id) not in GPIO_CONFIG["relays"]:
            return jsonify({"error": "Invalid relay ID"}), 400
        state = get_gpio_state(relay_id)
        if isinstance(state, int):
            return jsonify({"relay_id": relay_id, "state": state}), 200
        return jsonify({"error": state}), 500
    except Exception as e:
        logging.error(f"Error in get_relay_state: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/reload_config', methods=['GET', 'POST'])
@auth.login_required
def reload_config():
    global GPIO_CONFIG, GPIO_LINE_MAP
    try:
        if gpio_interface == "gpiod":
            GPIO_LINE_MAP = load_gpio_line_map()
        else:
            GPIO_CONFIG = load_gpio_config()
        if gpio_interface == 'sysfs':
            init_sysfs_gpios()
        return jsonify({"message": "GPIO config reloaded"}), 200
    except Exception as e:
        logging.error(f"Error reloading config: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
@auth.login_required
def home():
    try:
        # Add live state to each relay before rendering
        for relay_id in GPIO_CONFIG["relays"]:
            state_val = get_gpio_state(int(relay_id))
            # Convert to ON/OFF considering active-low logic
            if GPIO_CONFIG["relays"][relay_id].get('active', 'high') == 'low':
                state_text = "ON" if state_val == 0 else "OFF"
            else:
                state_text = "ON" if state_val == 1 else "OFF"
            GPIO_CONFIG["relays"][relay_id]["state"] = state_text

        return render_template('index.html', relays=GPIO_CONFIG["relays"])
    except Exception as e:
        logging.error(f"Error rendering home page: {e}")
        return jsonify({"error": str(e)}), 500

def init_sysfs_gpios():
    """Export and initialize sysfs GPIOs using the 'pin' from JSON."""
    for rid, relay in GPIO_CONFIG.get('relays', {}).items():
        pin = relay.get('pin')
        if pin is None:
            continue
        path = relay.get('path')
        if path is None:
            raise ValueError(f"Missing 'path' for relay {rid} in GPIO config.")

        gpio_dir = path
        try:
            if not os.path.exists(gpio_dir):
                with open('/sys/class/gpio/export', 'w') as f:
                    f.write(str(pin))
            with open(f'{gpio_dir}/direction', 'w') as f:
                f.write('out')
            active = relay.get('active', 'high')
            with open(f'{gpio_dir}/active_low', 'w') as f:
                f.write('1' if active == 'low' else '0')
            logging.info(f'Initialized GPIO {pin} for relay {rid}')
        except Exception as e:
            logging.error(f'Failed to init GPIO {pin}: {e}')

if __name__ == '__main__':
    try:
        GPIO_CONFIG = load_gpio_config()
        if int(kernel_version[0]) >= 6 and HAVE_LIB_GPIOD:
            logging.info("Kernel version is 6+ and detected python libgpiod. Switching to libgpiod interface")
            gpio_interface = "gpiod"
            GPIO_LINE_MAP = load_gpio_line_map()
        else:
            logging.info("Using sysfs GPIO interface")
            gpio_interface = "sysfs"
        logging.info(f"Initialized GPIO interface: {gpio_interface}")
        if gpio_interface == 'sysfs':
            init_sysfs_gpios()
    except ValueError:
        logging.warning("Failed to get kernel version. Defaulting to sysfs interface.")
    except Exception as e:
        logging.error(f"Initialization error: {e}")
    logging.info(f"Final: gpio_interface = {gpio_interface}")
    app.run(host='0.0.0.0', port=5000, debug=False)