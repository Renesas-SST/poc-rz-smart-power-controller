SPDX-License-Identifier: BSD-4-Clause

Copyright (c) 2025, Renesas Electronics America Inc

This file is part of the project under the BSD 4-Clause License.

# Renesas Smart Power Controller - GPIO Relay Control System

This project is a Flask-based web and terminal interface for controlling GPIO relays on Linux-based systems (like Renesas RZ or Raspberry Pi with exported GPIO pins).


---

## 📁 Hierarchy

The following describes the hierarchy of this release directory.

```
.
├── bin
│   └── RZ-Smart-Power-Controller-2.0.1-Linux.deb              <------- ARM64 prebuilt debian installer package for RZ boards running yocto / ubuntu builds.
├── LICENSE.md                                                 <------- BSD 4 clause license file.
├── r12uz0207eu0210-renesas-smart-power-controller.pdf         <------- Comprehensive user manual.
├── README.md                                                  <------- This file. Start here alwyas.
└── source                                                     <------- Source code released under BSD-4-Clause License.
    ├── build_deb.sh                                           <------- Primary build and package script.
    └── src                                                    
        ├── CMakeLists.txt                                     
        ├── debian                                             <------- structure that helps create an installer.
        │   ├── control                                        <------- debian installer control file. Used to control installation in the final deb package.
        │   ├── postinst
        │   └── prerm
        ├── gpio_api_c.py                                      
        ├── gpio_config.json                                   
        ├── gpio_config_tool.py                                
        ├── gpio_setup.sh
        ├── gpio_terminal.sh
        ├── LICENSE.md                                         <------- BSD-4-Clause License file for the source code.
        ├── README.md                                          <------- Readme file about the source code.
        ├── requirements.txt                                   <------- Python packages needed to be installed automatically in installer.
        ├── rz-smart-power-controller.service    
        ├── SYSTEMD.md    
        └── templates    
            └── index.html    

6 directories, 20 files
```
> [!NOTE]
> The src directory has its own README.md providing the details for the webserver application.
> This application is a PoC that has only been verified on the Renesas RZ/G2L-SBC board.

## Quick Start

Dependency: Debian image with dpkg package manager. Also requires a working internet on the parget board with pythnon 3 installed.
Image load: Just use standard linux commands to copy the debian .deb binary to the target RZ board through USB/SSH/SDMMC/etc to any known location like /home or /root or /tmp on target board.
Installation:
Run the following commands on the debian file.

```
# apt-get update
# ls /usr/local/etc/rz-smart-power-controller/gpio_config.json
```
Refer the user manual for full details.

---

## GPIO Backend Configuration (libgpiod vs sysfs)

The server supports two GPIO access backends:

- `libgpiod` (preferred): uses the modern character device GPIO interface via the Python `gpiod` bindings.
- `sysfs` (fallback / legacy): uses paths under `/sys/class/gpio/...`.

Backend selection is controlled by the environment variable `RZSPC_GPIO_BACKEND`:

- `auto` (default): prefer `libgpiod` when available and a relay entry provides `chip`/`line`; fall back to `sysfs` when not available.
- `libgpiod`: force libgpiod-only operation (requires Python `gpiod` and per-relay `chip`/`line` fields).
- `sysfs`: force sysfs-only operation (requires `path` fields in the relay config).

Config format notes (in `src/gpio_config.json`): each relay may include either or both of the following:

```
"1": {
    "pin": 304,
    "path": "/sys/class/gpio/P23_0/value",    # sysfs path (legacy)
    "chip": "gpiochip0",                      # libgpiod chip (optional)
    "line": 0                                  # libgpiod line offset (optional)
}
```

Examples:

Set `libgpiod` preferred (auto) and start the server:
```bash
export RZSPC_GPIO_BACKEND=auto
export RZSPC_TEMPLATES=$(pwd)/src/templates
export RZSPC_CONFIG=$(pwd)/src/gpio_config.json
python3 src/gpio_api_c.py
```

Force sysfs-only mode:
```bash
export RZSPC_GPIO_BACKEND=sysfs
python3 src/gpio_api_c.py
```

Status endpoint (authenticated):
```bash
curl -u admin:password123 "http://localhost:5000/gpio_backend_status"
```

Adjust the `chip` and `line` values to match your platform's gpiochip device and line offsets when using libgpiod.

