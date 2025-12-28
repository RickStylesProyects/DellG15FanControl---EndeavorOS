#!/bin/bash

# Dell G15 Fan Control Ultimate - Uninstallation Script
# For EndeavourOS (Arch Linux based)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║       Dell G15 Fan Control Ultimate - Desinstalador           ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check for root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: Este script debe ejecutarse como root o con sudo.${NC}"
    echo "Uso: sudo ./uninstall.sh"
    exit 1
fi

# Get the actual user (if running with sudo)
if [ -n "$SUDO_USER" ]; then
    ACTUAL_USER=$SUDO_USER
    USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
else
    ACTUAL_USER=$(whoami)
    USER_HOME=$HOME
fi

echo -e "${YELLOW}¿Estás seguro de que quieres desinstalar Dell G15 Fan Control?${NC}"
read -p "Escribe 'si' para confirmar: " confirm

if [ "$confirm" != "si" ]; then
    echo "Desinstalación cancelada."
    exit 0
fi

echo ""
echo -e "${YELLOW}Desinstalando...${NC}"
echo ""

# Remove desktop entry
DESKTOP_FILE="$USER_HOME/.local/share/applications/dell-g15-fan-control.desktop"
if [ -f "$DESKTOP_FILE" ]; then
    rm -f "$DESKTOP_FILE"
    echo -e "${GREEN}✓ Acceso directo eliminado${NC}"
fi

# Remove autostart entry
AUTOSTART_FILE="$USER_HOME/.config/autostart/dell-g15-fan-control.desktop"
if [ -f "$AUTOSTART_FILE" ]; then
    rm -f "$AUTOSTART_FILE"
    echo -e "${GREEN}✓ Autoarranque eliminado${NC}"
fi

# Remove polkit rule
POLKIT_FILE="/usr/share/polkit-1/actions/org.dell.g15.fancontrol.policy"
if [ -f "$POLKIT_FILE" ]; then
    rm -f "$POLKIT_FILE"
    echo -e "${GREEN}✓ Regla polkit eliminada${NC}"
fi

# Remove systemd service
SERVICE_FILE="/etc/systemd/system/dell-g15-fan-resume.service"
if [ -f "$SERVICE_FILE" ]; then
    systemctl disable dell-g15-fan-resume.service 2>/dev/null || true
    rm -f "$SERVICE_FILE"
    systemctl daemon-reload
    echo -e "${GREEN}✓ Servicio systemd eliminado${NC}"
fi

# Remove CLI symlink
if [ -L "/usr/local/bin/g15-fan-control" ]; then
    rm -f "/usr/local/bin/g15-fan-control"
    echo -e "${GREEN}✓ Enlace CLI eliminado${NC}"
fi

# Remove GUI launcher
if [ -f "/usr/local/bin/dell-g15-fan-control-gui" ]; then
    rm -f "/usr/local/bin/dell-g15-fan-control-gui"
    echo -e "${GREEN}✓ Launcher GUI eliminado${NC}"
fi

# Remove sudoers rule
if [ -f "/etc/sudoers.d/dell-g15-fan-control" ]; then
    rm -f "/etc/sudoers.d/dell-g15-fan-control"
    echo -e "${GREEN}✓ Regla sudoers eliminada${NC}"
fi

# Remove user symlink if exists
if [ -L "$USER_HOME/.local/bin/g15-fan-control-gui" ]; then
    rm -f "$USER_HOME/.local/bin/g15-fan-control-gui"
    echo -e "${GREEN}✓ Symlink usuario eliminado${NC}"
fi

# Remove config directory
CONFIG_DIR="$USER_HOME/.config/dell-g15-fan-control"
if [ -d "$CONFIG_DIR" ]; then
    rm -rf "$CONFIG_DIR"
    echo -e "${GREEN}✓ Configuración eliminada${NC}"
fi

echo ""
echo -e "${GREEN}¡Desinstalación completada!${NC}"
echo ""
echo -e "${YELLOW}Nota:${NC} Los paquetes del sistema (acpi_call-dkms, python-pyqt6, etc.)"
echo "      no han sido eliminados. Puedes removerlos manualmente si lo deseas:"
echo ""
echo "      sudo pacman -R acpi_call-dkms python-pyqt6 python-psutil"
echo ""
echo -e "${YELLOW}Nota:${NC} El archivo de módulos acpi_call no ha sido eliminado."
echo "      Si deseas dejar de cargar el módulo en el boot:"
echo ""
echo "      sudo rm /etc/modules-load.d/acpi_call.conf"
echo ""
