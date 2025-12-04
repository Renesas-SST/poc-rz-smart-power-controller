# Systemd unit (packaging)

- Canonical unit installed by the package: `rz-smart-power-controller.service`.
- The unit template lives at `src/rz-smart-power-controller.service` and is processed by CMake during the build.
- When installed the package places the unit under `/usr/local/lib/systemd/system/rz-smart-power-controller.service` (respecting the configured install prefix). The package `postinst` enables and attempts to start the unit automatically; `prerm` will stop/disable and remove it on uninstall.

If you previously used a wrapper-based unit that invoked `gpio_terminal.sh`, that legacy unit has been removed from the source tree — use the packaged `rz-smart-power-controller.service` for deployments.
