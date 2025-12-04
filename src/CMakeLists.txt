# SPDX-License-Identifier: BSD-4-Clause
# Copyright (c) 2025, Renesas Electronics America Inc
# This file is part of the project under the BSD 4-Clause License.

cmake_minimum_required(VERSION 3.10)

# No compilers needed
project(AT-PowerCycling LANGUAGES NONE)

# Use standard install dir variables (bin, etc, share, ...)
include(GNUInstallDirs)

# Our subdirectories (under etc and share)
set(ATPC_CONF_DIR "${CMAKE_INSTALL_SYSCONFDIR}/at-powercycling")
set(ATPC_SHARE_DIR "${CMAKE_INSTALL_DATADIR}/at-powercycling")

# --- Files to install ---
# Executables -> /usr/local/bin
install(PROGRAMS
  gpio_api_c.py
  gpio_setup.sh
  gpio_terminal.sh
  DESTINATION ${CMAKE_INSTALL_BINDIR}
)

# Config files -> /usr/local/etc/at-powercycling
install(FILES
  gpio_config.json
  requirements.txt
  DESTINATION ${ATPC_CONF_DIR}
)

# Templates -> /usr/local/share/at-powercycling/templates
install(DIRECTORY
  templates/
  DESTINATION ${ATPC_SHARE_DIR}/templates
)

# Optional docs -> /usr/local/share/doc/at-powercycling
if(EXISTS "${CMAKE_SOURCE_DIR}/README.md")
  install(FILES README.md DESTINATION ${CMAKE_INSTALL_DATADIR}/doc/at-powercycling)
endif()

# --- CPack: build a .deb that installs under /usr/local ---
set(CPACK_SET_DESTDIR TRUE)
set(CPACK_PACKAGING_INSTALL_PREFIX "/usr/local")

set(CPACK_GENERATOR "DEB")
set(CPACK_PACKAGE_NAME "at-powercycling")
set(CPACK_PACKAGE_VERSION "2.0.1")
set(CPACK_DEBIAN_PACKAGE_SECTION "utils")
set(CPACK_DEBIAN_PACKAGE_PRIORITY "optional")
set(CPACK_DEBIAN_PACKAGE_ARCHITECTURE "all")
set(CPACK_DEBIAN_PACKAGE_MAINTAINER "Chandra Sekhar <you@example.com>")
set(CPACK_DEBIAN_PACKAGE_DEPENDS "python3, python3-flask, python3-flask-httpauth, jq")
include(CPack)
