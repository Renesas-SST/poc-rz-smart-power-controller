# SPDX-License-Identifier: BSD-4-Clause
# Copyright (c) 2025, Renesas Electronics America Inc
# This file is part of the project under the BSD 4-Clause License.

# Renesas Smart Power Controller - GPIO Relay Control System

This project is a Flask-based web and terminal interface for controlling GPIO relays on Linux-based systems (like Renesas RZ or Raspberry Pi with exported GPIO pins).


---

## 📁 Hierarchy

The following describes the hierarchy of this release directory.

```
.
├── bin
│   └── at-powercycling-2.0.1-Linux.deb                     <------- ARM64 prebuilt debian installer package for RZ boards running yocto / ubuntu builds.
├── LICENSE.md                                              <------- BSD 4 clause license file.
├── r12uz0207eu0100-renesas-smart-power-controller.pdf      <------- Comprehensive user manual.
├── README.md                                               <------- This file. Start here alwyas.
└── src                                                     <------- Source code released under BSD-4-Clause License.
    ├── CMakeLists.txt
    ├── debian                                              <------- structure that helps create an installer.
    │   └── control                                         <------- debian installer control file. Used to control installation in the final deb package.
    ├── gpio_api_c.py
    ├── gpio_config.json
    ├── gpio_setup.sh
    ├── gpio_terminal.sh
    ├── LICENSE.md                                          <------- BSD-4-Clause License file for the source code.
    ├── README.md                                           <------- Readme file about the source code.
    ├── requirements.txt                                    <------- Python packages needed to be installed automatically in installer.
    └── templates
        └── index.html

5 directories, 14 files
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
# apt-get updat
# ls /usr/local/etc/at-powercycling/gpio_config.jso
```
Refer the user manual for full details.

---
