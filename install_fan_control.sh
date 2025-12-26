#!/bin/bash

# Dell G15 Fan Control Installer for EndeavourOS (Intel i7-11800H)
# Based on the guide provided by the user.

set -e # Exit on error

echo "Starting Dell G15 Fan Control Installation..."

# Check for sudo
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script as root or with sudo."
  exit 1
fi

# Get the actual user (if running with sudo)
if [ $SUDO_USER ]; then
    ACTUAL_USER=$SUDO_USER
    USER_HOME=$(getent passwd $SUDO_USER | cut -d: -f6)
else
    ACTUAL_USER=$(whoami)
    USER_HOME=$HOME
fi

echo "User detected: $ACTUAL_USER"
echo "Home directory: $USER_HOME"

# Step 1: Install Dependencies
echo "----------------------------------------------------------------"
echo "Step 1: Updating system and installing dependencies..."
echo "----------------------------------------------------------------"

# Check for LTS kernel
KERNEL_RELEASE=$(uname -r)
HEADERS_PKG="linux-headers"

if [[ "$KERNEL_RELEASE" == *"lts"* ]]; then
    echo "LTS Kernel detected ($KERNEL_RELEASE). Switching to linux-lts-headers."
    HEADERS_PKG="linux-lts-headers"
else
    echo "Standard Kernel detected ($KERNEL_RELEASE). Using linux-headers."
fi

pacman -Syu --noconfirm
pacman -S --need --noconfirm base-devel git "$HEADERS_PKG" acpi_call-dkms python-pexpect python-pyqt6 python-psutil

# Step 2: Activate Kernel Module
echo "----------------------------------------------------------------"
echo "Step 2: Activating acpi_call module..."
echo "----------------------------------------------------------------"

# Load module
modprobe acpi_call

# Ensure it loads on boot
echo "acpi_call" | tee /etc/modules-load.d/acpi_call.conf
echo "Module acpi_call configured for auto-load."

# Step 3: Download Software
echo "----------------------------------------------------------------"
echo "Step 3: Cloning software repository..."
echo "----------------------------------------------------------------"

INSTALL_DIR="$USER_HOME/Software/DellFan"
mkdir -p "$INSTALL_DIR"
# Ensure the directory is owned by the user (since we are running as root)
chown -R "$ACTUAL_USER:$ACTUAL_USER" "$INSTALL_DIR"

# Run git as the actual user to avoid permission issues in home dir
if [ -d "$INSTALL_DIR/Dell_G15_Fan_Cli" ]; then
    echo "Directory exists. Removing old version..."
    rm -rf "$INSTALL_DIR/Dell_G15_Fan_Cli"
fi

echo "Cloning into $INSTALL_DIR/Dell_G15_Fan_Cli..."
sudo -u "$ACTUAL_USER" git clone https://github.com/Mohit-Pala/Dell_G15_Fan_Cli.git "$INSTALL_DIR/Dell_G15_Fan_Cli"

cd "$INSTALL_DIR/Dell_G15_Fan_Cli"

# Step 4: Apply Patch for Intel i7-11800H
echo "----------------------------------------------------------------"
echo "Step 4: Applying Intel i7-11800H Patch (AMW3 -> AMWW)..."
echo "----------------------------------------------------------------"

sed -i 's/AMW3/AMWW/g' *.py
echo "Patch applied successfully."

# Step 5: Setup permissions
chmod +x g15-gui.py g15-fan-cli.py

# Step 6: Create Desktop Shortcut
echo "----------------------------------------------------------------"
echo "Step 6: Creating Desktop Shortcut..."
echo "----------------------------------------------------------------"

DESKTOP_FILE="$USER_HOME/.local/share/applications/dell-fan-control.desktop"
mkdir -p "$(dirname "$DESKTOP_FILE")"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Dell Fan Control
Comment=Control de ventiladores G15
Exec=/usr/bin/sudo /usr/bin/python $INSTALL_DIR/Dell_G15_Fan_Cli/g15-gui.py
Icon=utilities-terminal
Terminal=true
Categories=System;Settings;
EOF

chown "$ACTUAL_USER:$ACTUAL_USER" "$DESKTOP_FILE"
echo "Desktop shortcut created at $DESKTOP_FILE"

echo "----------------------------------------------------------------"
echo "Installation Complete!"
echo "----------------------------------------------------------------"
echo "You can now launch the application from your application menu (Dell Fan Control)."
echo "Or run it manually with: sudo python $INSTALL_DIR/Dell_G15_Fan_Cli/g15-gui.py"
echo ""
echo "NOTE: If you have Secure Boot enabled, the acpi_call module might fail to load."
echo "Disable Secure Boot in BIOS if you encounter 'Operation not permitted' errors."
