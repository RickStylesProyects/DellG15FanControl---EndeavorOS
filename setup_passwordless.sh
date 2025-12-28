#!/bin/bash
# Script para habilitar ejecución sin contraseña
# Ejecutar una sola vez: sudo ./setup_passwordless.sh

echo "Configurando ejecución sin contraseña para Dell G15 Fan Control..."

cat > /etc/sudoers.d/dell-g15-fan-control << 'SUDOERSEOF'
# Dell G15 Fan Control - Allow passwordless execution
rick ALL=(root) NOPASSWD: /usr/bin/python3 "/home/rick/Programacion/DellG15FanControl - EndeavorOS/g15_fan_control.py"
rick ALL=(root) NOPASSWD: /usr/bin/python3 "/home/rick/Programacion/DellG15FanControl - EndeavorOS/g15_fan_control.py" *
SUDOERSEOF

chmod 440 /etc/sudoers.d/dell-g15-fan-control

if visudo -c -f /etc/sudoers.d/dell-g15-fan-control 2>/dev/null; then
    echo "✓ Configuración exitosa!"
    echo "  Ahora puedes ejecutar la app sin contraseña."
else
    echo "✗ Error en configuración, intentando formato alternativo..."
    
    # Try alternative format without quotes
    cat > /etc/sudoers.d/dell-g15-fan-control << 'SUDOERSEOF2'
# Dell G15 Fan Control - Allow passwordless execution
rick ALL=(root) NOPASSWD: /usr/bin/python3 /home/rick/Programacion/DellG15FanControl\ -\ EndeavorOS/g15_fan_control.py
rick ALL=(root) NOPASSWD: /usr/bin/python3 /home/rick/Programacion/DellG15FanControl\ -\ EndeavorOS/g15_fan_control.py *
SUDOERSEOF2
    
    chmod 440 /etc/sudoers.d/dell-g15-fan-control
    
    if visudo -c -f /etc/sudoers.d/dell-g15-fan-control 2>/dev/null; then
        echo "✓ Configuración exitosa con formato alternativo!"
    else
        echo "✗ Error persistente"
        rm -f /etc/sudoers.d/dell-g15-fan-control
    fi
fi

# Update desktop shortcut to use sudo launcher
DESKTOP_FILE="/home/rick/.local/share/applications/dell-g15-fan-control.desktop"
cat > "$DESKTOP_FILE" << 'DESKTOPEOF'
[Desktop Entry]
Type=Application
Version=1.0
Name=Dell G15 Fan Control
GenericName=Fan Control
Comment=Control de perfiles térmicos para Dell G15 5511
Exec=/home/rick/.local/bin/g15-fan-control-gui
Icon=utilities-system-monitor
Terminal=false
Categories=System;Settings;HardwareSettings;
Keywords=fan;ventilador;dell;g15;thermal;termal;cooling;
StartupNotify=true
DESKTOPEOF

chown rick:rick "$DESKTOP_FILE"
chmod +x "$DESKTOP_FILE"
echo "✓ Acceso directo actualizado"
