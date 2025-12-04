# SPDX-License-Identifier: BSD-4-Clause
# Copyright (c) 2025, Renesas Electronics America Inc
# This file is part of the project under the BSD 4-Clause License.

cmake_minimum_required(VERSION 3.10)

# No compilers needed
project(RZ-Smart-Power-Controller VERSION 2.1 LANGUAGES NONE)

# Use standard install dir variables (bin, etc, share, ...)
include(GNUInstallDirs)

# Our subdirectories (under etc and share)
set(RZSPC_CONF_DIR "${CMAKE_INSTALL_SYSCONFDIR}/rz-smart-power-controller")
set(RZSPC_SHARE_DIR "${CMAKE_INSTALL_DATADIR}/rz-smart-power-controller")

# Option for systemd service installation
option(INSTALL_SYSTEMD_SERVICE "Install systemd service file" OFF)

# --- Files to install ---
# Executables -> /usr/local/bin
install(PROGRAMS
  gpio_api_c.py
  gpio_setup.sh
  gpio_terminal.sh
  gpio_config_tool.py
  DESTINATION ${CMAKE_INSTALL_BINDIR}
)

# Config files -> /usr/local/etc/rz-smart-power-controller
install(FILES
  gpio_config.json
  requirements.txt
  DESTINATION ${RZSPC_CONF_DIR}
)

# Templates -> /usr/local/share/rz-smart-power-controller/templates
install(DIRECTORY
  templates/
  DESTINATION ${RZSPC_SHARE_DIR}/templates
)

# Optional docs -> /usr/local/share/doc/rz-smart-power-controller
if(EXISTS "${CMAKE_SOURCE_DIR}/README.md")
  install(FILES README.md DESTINATION ${CMAKE_INSTALL_DATADIR}/doc/rz-smart-power-controller)
endif()

# Optional systemd service file installation
if(INSTALL_SYSTEMD_SERVICE)
  # Configure service file with install paths
  configure_file(
    rz-smart-power-controller.service
    ${CMAKE_CURRENT_BINARY_DIR}/rz-smart-power-controller.service
    @ONLY
  )
  install(FILES
    ${CMAKE_CURRENT_BINARY_DIR}/rz-smart-power-controller.service
    DESTINATION ${CMAKE_INSTALL_PREFIX}/lib/systemd/system
  )
endif()

# --- CPack: build a .deb that installs under /usr/local ---
set(CPACK_SET_DESTDIR TRUE)
set(CPACK_PACKAGING_INSTALL_PREFIX "/usr/local")

set(CPACK_GENERATOR "DEB")
set(CPACK_PACKAGE_NAME "RZ-Smart-Power-Controller")
set(CPACK_PACKAGE_VERSION "2.0.1")
set(CPACK_DEBIAN_PACKAGE_SECTION "utils")
set(CPACK_DEBIAN_PACKAGE_PRIORITY "optional")
if(NOT DEFINED CPACK_DEBIAN_PACKAGE_ARCHITECTURE)
  # default to architecture-independent package. Override on the cmake command line
  # to mark the package for a specific architecture (e.g. -DCPACK_DEBIAN_PACKAGE_ARCHITECTURE=arm64).
  # Default 'all' To be used when there are no compiled binaries.
  # Once binaries are added, this should be altered by passing the architecture from command line using -DCPACK_DEBIAN_PACKAGE_ARCHITECTURE variable.
  set(CPACK_DEBIAN_PACKAGE_ARCHITECTURE "all")
endif()
set(CPACK_DEBIAN_PACKAGE_MAINTAINER "Preetam S Reddy <preetam.reddy.cp@renesas.com>")
set(CPACK_DEBIAN_PACKAGE_DEPENDS "python3, python3-flask, python3-flask-httpauth, python3-libgpiod")

# Debian control scripts (postinst, prerm)
set(CPACK_DEBIAN_PACKAGE_CONTROL_EXTRA "${CMAKE_SOURCE_DIR}/debian/postinst;${CMAKE_SOURCE_DIR}/debian/prerm")

# Add systemd dependency if service installation is enabled
if(INSTALL_SYSTEMD_SERVICE)
  set(CPACK_DEBIAN_PACKAGE_DEPENDS "${CPACK_DEBIAN_PACKAGE_DEPENDS}, systemd")
endif()

include(CPack)
