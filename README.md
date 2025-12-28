# Dell G15 Fan Control Ultimate

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Qt-6-green?logo=qt" alt="Qt6">
  <img src="https://img.shields.io/badge/Platform-EndeavourOS-purple" alt="EndeavourOS">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
</p>

Una aplicación completa para controlar los perfiles térmicos del Dell G15 5511 en EndeavourOS (Arch Linux).

## ✨ Características

- 🎮 **Control de Perfiles Térmicos**: Balanced, Performance, Quiet, G-Mode
- 📊 **Monitoreo en Tiempo Real**: CPU, GPU, RAM, ventiladores, batería
- 🖥️ **GUI Moderna**: Interfaz PyQt6 con tema oscuro
- 📌 **Bandeja del Sistema**: Acceso rápido desde el system tray
- 🚀 **Autoarranque**: Opción de iniciar con el sistema
- 💾 **Persistencia**: Guarda configuración y restaura al despertar
- 💻 **CLI**: Control desde terminal para scripts y automatización

## 📸 Capturas de Pantalla

*La aplicación incluye un tema oscuro moderno con indicadores visuales para temperatura y velocidad de ventiladores.*

## 📋 Requisitos

- **Sistema Operativo**: EndeavourOS / Arch Linux
- **Hardware**: Dell G15 5511 con Intel i7-11800H
- **Kernel Module**: `acpi_call` (instalado automáticamente)
- **Python**: 3.10+
- **Dependencias**: PyQt6, psutil

## 🚀 Instalación

### Instalación Automática (Recomendado)

```bash
# Clonar o descargar este repositorio
cd "DellG15FanControl - EndeavorOS"

# Ejecutar el instalador
sudo ./install.sh
```

El instalador:
1. Instala todas las dependencias
2. Configura el módulo `acpi_call`
3. Crea acceso directo en el menú de aplicaciones
4. Configura servicio systemd para resume
5. Crea comando CLI global

### Instalación Manual

```bash
# Instalar dependencias
sudo pacman -S acpi_call-dkms python-pyqt6 python-psutil

# Cargar módulo
sudo modprobe acpi_call

# Configurar carga automática
echo "acpi_call" | sudo tee /etc/modules-load.d/acpi_call.conf

# Ejecutar la aplicación
sudo python3 g15_fan_control.py
```

## 📖 Uso

### Interfaz Gráfica

Busca "Dell G15 Fan Control" en el menú de aplicaciones, o ejecuta:

```bash
sudo python3 g15_fan_control.py
```

### Línea de Comandos

```bash
# Modo Equilibrado
sudo g15-fan-control --cli b

# Modo Rendimiento
sudo g15-fan-control --cli p

# Modo Silencioso
sudo g15-fan-control --cli q

# G-Mode (ventiladores al 100%)
sudo g15-fan-control --cli g

# Ver estadísticas del sistema
sudo g15-fan-control --monitor
```

## 🎮 Perfiles Térmicos

| Modo | Descripción | Uso Recomendado |
|------|-------------|-----------------|
| ⚖️ **Balanced** | Curva conservadora | Uso general, navegación |
| 🚀 **Performance** | Curva agresiva | Juegos, compilación |
| 🔇 **Quiet** | RPM limitadas | Trabajo silencioso, películas |
| 🎮 **G-Mode** | Ventiladores al 100% | Gaming intensivo, benchmarks |

## ⚙️ Configuración

La configuración se guarda en `~/.config/dell-g15-fan-control/config.json`:

- **Modo por defecto**: Perfil a usar al iniciar
- **Modo al despertar**: Perfil tras suspensión
- **Gobernador CPU**: Cambiar automáticamente (powersave/performance)
- **Notificaciones**: Mostrar al cambiar modo
- **Autoarranque**: Iniciar con el sistema

## 🔧 Solución de Problemas

### El módulo acpi_call no carga

```bash
# Verificar si Secure Boot está habilitado
mokutil --sb-state

# Si está habilitado, desactívalo en la BIOS
# O firma el módulo manualmente (avanzado)
```

### Los modos no cambian

El Dell G15 5511 (Intel) usa la ruta ACPI `\_SB.AMWW.WMAX`. Si tienes un modelo AMD, la ruta es `\_SB.AMW3.WMAX`. Puedes cambiar esto en la configuración.

### No se leen los ventiladores

Asegúrate de que el módulo `dell-smm-hwmon` esté cargado:

```bash
lsmod | grep dell_smm
```

## 🏗️ Estructura del Proyecto

```
DellG15FanControl/
├── dell_g15_fan_control/
│   ├── __init__.py
│   ├── acpi_controller.py    # Control ACPI
│   ├── system_monitor.py     # Monitoreo del sistema
│   ├── config_manager.py     # Gestión de configuración
│   ├── main_window.py        # GUI principal
│   ├── system_tray.py        # Icono de bandeja
│   └── styles.qss            # Estilos CSS
├── g15_fan_control.py        # Script principal
├── install.sh                # Instalador
├── uninstall.sh              # Desinstalador
└── README.md
```

## 📝 Licencia

MIT License - Consulta el archivo LICENSE para más detalles.

## 🙏 Créditos

- Basado en [Dell_G15_Fan_Cli](https://github.com/Mohit-Pala/Dell_G15_Fan_Cli)
- Módulo [acpi_call](https://github.com/mkottman/acpi_call)
- Documentación de la comunidad de Arch Linux

## ⚠️ Advertencia

Esta aplicación modifica parámetros del hardware. Aunque utiliza las mismas llamadas ACPI que el software oficial de Dell, úsala bajo tu propia responsabilidad. El uso del G-Mode de forma prolongada puede acelerar el desgaste de los ventiladores.
