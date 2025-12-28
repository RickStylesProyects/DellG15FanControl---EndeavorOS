#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dell G15 Fan Control Ultimate
Main entry point for the application.

Usage:
    sudo python3 g15_fan_control.py           # Start GUI
    sudo python3 g15_fan_control.py --minimized  # Start minimized to tray
    sudo python3 g15_fan_control.py --cli b   # CLI: Set balanced mode
    sudo python3 g15_fan_control.py --cli p   # CLI: Set performance mode
    sudo python3 g15_fan_control.py --cli q   # CLI: Set quiet mode
    sudo python3 g15_fan_control.py --cli g   # CLI: Toggle G-Mode
    sudo python3 g15_fan_control.py --monitor # Show system stats
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_banner():
    """Print the application banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║       Dell G15 Fan Control Ultimate v1.0.0                    ║
║       Control de perfiles térmicos para Dell G15 5511         ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def cli_mode(args):
    """Handle CLI mode."""
    from dell_g15_fan_control.acpi_controller import ACPIController, ThermalMode
    
    controller = ACPIController(force_intel=True)
    
    # Run checks
    all_passed, checks = controller.run_checks()
    
    if not all_passed:
        print("❌ Verificaciones del sistema fallaron:")
        for name, passed, msg in checks:
            if not passed:
                print(f"   • {name}: {msg}")
        sys.exit(1)
    
    if len(args) < 1:
        print("Uso: g15_fan_control.py --cli [modo]")
        print("Modos: b (balanced), p (performance), q (quiet), g (gmode)")
        sys.exit(1)
    
    mode = args[0].lower()
    
    if mode.startswith('b'):
        success, msg = controller.set_thermal_mode(ThermalMode.BALANCED)
    elif mode.startswith('p'):
        success, msg = controller.set_thermal_mode(ThermalMode.PERFORMANCE)
    elif mode.startswith('q'):
        success, msg = controller.set_thermal_mode(ThermalMode.QUIET)
    elif mode.startswith('g'):
        success, msg = controller.toggle_gmode()
    elif mode.startswith('h'):
        print("Modos disponibles:")
        print("  b - Balanced (Equilibrado)")
        print("  p - Performance (Rendimiento)")
        print("  q - Quiet (Silencioso)")
        print("  g - G-Mode (Game Shift - ventiladores al 100%)")
        sys.exit(0)
    else:
        print(f"Modo desconocido: {mode}")
        sys.exit(1)
    
    if success:
        print(f"✓ {msg}")
    else:
        print(f"✗ {msg}")
        sys.exit(1)


def monitor_mode():
    """Show system statistics."""
    from dell_g15_fan_control.system_monitor import SystemMonitor
    
    monitor = SystemMonitor()
    
    print_banner()
    print("Estadísticas del sistema:\n")
    
    # CPU
    cpu = monitor.get_cpu_stats()
    if cpu:
        print(f"CPU:")
        print(f"  Temperatura: {cpu.average_temp}°C (máx: {cpu.max_temp}°C)")
        print(f"  Uso: {cpu.usage_percent}%")
        print(f"  Frecuencia: {cpu.frequency_mhz} MHz")
    
    # Fans
    fans = monitor.get_fan_stats()
    if fans:
        print(f"\nVentiladores ({fans.source}):")
        print(f"  Fan 1 (CPU): {fans.fan1_rpm} RPM")
        print(f"  Fan 2 (GPU): {fans.fan2_rpm} RPM")
    
    # RAM
    ram = monitor.get_ram_stats()
    if ram:
        print(f"\nRAM:")
        print(f"  Uso: {ram.used_gb}/{ram.total_gb} GB ({ram.percent}%)")
    
    # Battery
    battery = monitor.get_battery_stats()
    if battery:
        print(f"\nBatería:")
        print(f"  Carga: {battery.percent}%")
        print(f"  Salud: {battery.health_percent}%")
        print(f"  Conectado: {'Sí' if battery.power_plugged else 'No'}")
    
    # GPU
    gpu = monitor.get_gpu_stats()
    if gpu:
        print(f"\nGPU ({gpu.name}):")
        print(f"  Temperatura: {gpu.temp}°C")
        print(f"  Uso: {gpu.usage_percent}%")
        print(f"  VRAM: {gpu.memory_used_mb}/{gpu.memory_total_mb} MB")


def gui_mode(minimized=False):
    """Start GUI mode."""
    from dell_g15_fan_control.main_window import main as gui_main
    
    # Pass minimized flag via sys.argv
    if minimized and "--minimized" not in sys.argv:
        sys.argv.append("--minimized")
    
    gui_main()


def main():
    """Main entry point."""
    # Check for CLI mode
    if "--cli" in sys.argv:
        idx = sys.argv.index("--cli")
        cli_args = sys.argv[idx + 1:] if idx + 1 < len(sys.argv) else []
        print_banner()
        cli_mode(cli_args)
        return
    
    # Check for monitor mode
    if "--monitor" in sys.argv or "-m" in sys.argv:
        monitor_mode()
        return
    
    # Check for apply-saved-mode (used by systemd service)
    if "--apply-saved-mode" in sys.argv:
        from dell_g15_fan_control.main_window import main as gui_main
        gui_main()
        return
    
    # Check for help
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return
    
    # Default: GUI mode
    minimized = "--minimized" in sys.argv
    gui_mode(minimized)


if __name__ == "__main__":
    main()
