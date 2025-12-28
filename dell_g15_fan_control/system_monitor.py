#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dell G15 System Monitor Module
Monitors CPU temperature, fan speeds, RAM usage, battery, and GPU stats.
"""

import os
import subprocess
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
from pathlib import Path

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


@dataclass
class CPUStats:
    """CPU statistics container."""
    average_temp: float
    max_temp: float
    core_temps: List[float]
    usage_percent: float
    frequency_mhz: float


@dataclass
class FanStats:
    """Fan statistics container."""
    fan1_rpm: int  # CPU fan
    fan2_rpm: int  # GPU fan
    source: str    # Where we got the data from (dell_smm, hwmon, etc.)


@dataclass
class RAMStats:
    """RAM statistics container."""
    used_gb: float
    total_gb: float
    percent: float
    available_gb: float


@dataclass
class BatteryStats:
    """Battery statistics container."""
    percent: float
    health_percent: float
    is_charging: bool
    time_remaining: Optional[str]
    power_plugged: bool


@dataclass
class GPUStats:
    """GPU statistics container."""
    name: str
    temp: float
    usage_percent: float
    memory_used_mb: int
    memory_total_mb: int
    fan_speed_percent: int


class SystemMonitor:
    """
    Monitor system statistics for Dell G15.
    
    Provides real-time data about CPU temperature, fan speeds,
    RAM usage, battery health, and GPU stats.
    """
    
    # Battery sysfs paths
    BATTERY_BASE = "/sys/class/power_supply/BAT0"
    
    def __init__(self):
        """Initialize the system monitor."""
        if not PSUTIL_AVAILABLE:
            raise ImportError("psutil is required. Install with: pip install psutil")
        
        self._nvidia_available = self._check_nvidia_smi()
    
    def _check_nvidia_smi(self) -> bool:
        """Check if nvidia-smi is available."""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--version"],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def get_cpu_stats(self) -> Optional[CPUStats]:
        """
        Get CPU statistics including temperature and usage.
        
        Returns:
            CPUStats object or None if unavailable
        """
        try:
            # Get temperatures
            temps = psutil.sensors_temperatures()
            core_temps = []
            
            # Try different temperature sources
            for source in ['coretemp', 'k10temp', 'acpitz']:
                if source in temps:
                    core_temps = [t.current for t in temps[source]]
                    break
            
            if not core_temps:
                # Fallback: try any available temperature
                for source, readings in temps.items():
                    if readings:
                        core_temps = [t.current for t in readings]
                        break
            
            avg_temp = sum(core_temps) / len(core_temps) if core_temps else 0.0
            max_temp = max(core_temps) if core_temps else 0.0
            
            # Get CPU usage
            usage = psutil.cpu_percent(interval=0.1)
            
            # Get CPU frequency
            freq = psutil.cpu_freq()
            frequency = freq.current if freq else 0.0
            
            return CPUStats(
                average_temp=round(avg_temp, 1),
                max_temp=round(max_temp, 1),
                core_temps=[round(t, 1) for t in core_temps],
                usage_percent=round(usage, 1),
                frequency_mhz=round(frequency, 0)
            )
            
        except Exception as e:
            print(f"Error getting CPU stats: {e}")
            return None
    
    def get_fan_stats(self) -> Optional[FanStats]:
        """
        Get fan speed statistics.
        
        Returns:
            FanStats object or None if unavailable
        """
        try:
            fans = psutil.sensors_fans()
            
            # Try Dell SMM first (most likely for G15)
            if 'dell_smm' in fans and len(fans['dell_smm']) >= 2:
                return FanStats(
                    fan1_rpm=fans['dell_smm'][0].current,
                    fan2_rpm=fans['dell_smm'][1].current,
                    source='dell_smm'
                )
            
            # Try thinkpad (just in case)
            if 'thinkpad' in fans:
                readings = fans['thinkpad']
                return FanStats(
                    fan1_rpm=readings[0].current if len(readings) > 0 else 0,
                    fan2_rpm=readings[1].current if len(readings) > 1 else 0,
                    source='thinkpad'
                )
            
            # Try any available fan source
            for source, readings in fans.items():
                if readings:
                    return FanStats(
                        fan1_rpm=readings[0].current if len(readings) > 0 else 0,
                        fan2_rpm=readings[1].current if len(readings) > 1 else 0,
                        source=source
                    )
            
            # Try reading from hwmon directly
            fan_rpm = self._read_hwmon_fans()
            if fan_rpm:
                return FanStats(
                    fan1_rpm=fan_rpm[0],
                    fan2_rpm=fan_rpm[1] if len(fan_rpm) > 1 else 0,
                    source='hwmon'
                )
            
            return None
            
        except Exception as e:
            print(f"Error getting fan stats: {e}")
            return None
    
    def _read_hwmon_fans(self) -> List[int]:
        """Try to read fan speeds from hwmon sysfs."""
        fans = []
        hwmon_base = Path("/sys/class/hwmon")
        
        if not hwmon_base.exists():
            return fans
        
        for hwmon_dir in hwmon_base.iterdir():
            # Look for fan files
            for i in range(1, 5):
                fan_input = hwmon_dir / f"fan{i}_input"
                if fan_input.exists():
                    try:
                        with open(fan_input) as f:
                            rpm = int(f.read().strip())
                            fans.append(rpm)
                    except (ValueError, PermissionError):
                        pass
        
        return fans
    
    def get_ram_stats(self) -> Optional[RAMStats]:
        """
        Get RAM usage statistics.
        
        Returns:
            RAMStats object or None if unavailable
        """
        try:
            mem = psutil.virtual_memory()
            
            return RAMStats(
                used_gb=round(mem.used / (1024**3), 2),
                total_gb=round(mem.total / (1024**3), 2),
                percent=round(mem.percent, 1),
                available_gb=round(mem.available / (1024**3), 2)
            )
            
        except Exception as e:
            print(f"Error getting RAM stats: {e}")
            return None
    
    def get_battery_stats(self) -> Optional[BatteryStats]:
        """
        Get battery statistics including health.
        
        Returns:
            BatteryStats object or None if unavailable
        """
        try:
            battery = psutil.sensors_battery()
            
            if battery is None:
                return None
            
            # Calculate battery health
            health = self._calculate_battery_health()
            
            # Format time remaining
            time_remaining = None
            if battery.secsleft > 0 and battery.secsleft != psutil.POWER_TIME_UNLIMITED:
                hours = battery.secsleft // 3600
                minutes = (battery.secsleft % 3600) // 60
                time_remaining = f"{hours}h {minutes}m"
            
            return BatteryStats(
                percent=round(battery.percent, 1),
                health_percent=round(health, 1) if health else 0.0,
                is_charging=battery.power_plugged and battery.percent < 100,
                time_remaining=time_remaining,
                power_plugged=battery.power_plugged
            )
            
        except Exception as e:
            print(f"Error getting battery stats: {e}")
            return None
    
    def _calculate_battery_health(self) -> Optional[float]:
        """Calculate battery health percentage from sysfs."""
        try:
            # Try energy-based calculation first
            design_path = Path(self.BATTERY_BASE) / "energy_full_design"
            full_path = Path(self.BATTERY_BASE) / "energy_full"
            
            # Fallback to charge-based
            if not design_path.exists():
                design_path = Path(self.BATTERY_BASE) / "charge_full_design"
                full_path = Path(self.BATTERY_BASE) / "charge_full"
            
            if design_path.exists() and full_path.exists():
                with open(design_path) as f:
                    design = int(f.read().strip())
                with open(full_path) as f:
                    full = int(f.read().strip())
                
                if design > 0:
                    return (full / design) * 100
            
            return None
            
        except (ValueError, PermissionError, FileNotFoundError):
            return None
    
    def get_gpu_stats(self) -> Optional[GPUStats]:
        """
        Get NVIDIA GPU statistics.
        
        Returns:
            GPUStats object or None if unavailable (no NVIDIA GPU or nvidia-smi)
        """
        if not self._nvidia_available:
            return None
        
        try:
            # Query nvidia-smi for GPU info
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total,fan.speed",
                    "--format=csv,noheader,nounits"
                ],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return None
            
            parts = [p.strip() for p in result.stdout.strip().split(',')]
            
            if len(parts) >= 6:
                return GPUStats(
                    name=parts[0],
                    temp=float(parts[1]) if parts[1] != '[N/A]' else 0.0,
                    usage_percent=float(parts[2]) if parts[2] != '[N/A]' else 0.0,
                    memory_used_mb=int(parts[3]) if parts[3] != '[N/A]' else 0,
                    memory_total_mb=int(parts[4]) if parts[4] != '[N/A]' else 0,
                    fan_speed_percent=int(parts[5]) if parts[5] != '[N/A]' else 0
                )
            
            return None
            
        except (subprocess.TimeoutExpired, ValueError, IndexError) as e:
            print(f"Error getting GPU stats: {e}")
            return None
    
    def get_all_stats(self) -> Dict:
        """
        Get all system statistics.
        
        Returns:
            Dictionary with all available stats
        """
        return {
            'cpu': self.get_cpu_stats(),
            'fans': self.get_fan_stats(),
            'ram': self.get_ram_stats(),
            'battery': self.get_battery_stats(),
            'gpu': self.get_gpu_stats()
        }


def main():
    """Test the system monitor."""
    monitor = SystemMonitor()
    
    print("=== Dell G15 System Monitor ===\n")
    
    # CPU
    cpu = monitor.get_cpu_stats()
    if cpu:
        print(f"CPU:")
        print(f"  Temperatura promedio: {cpu.average_temp}°C")
        print(f"  Temperatura máxima:   {cpu.max_temp}°C")
        print(f"  Uso:                  {cpu.usage_percent}%")
        print(f"  Frecuencia:           {cpu.frequency_mhz} MHz")
    else:
        print("CPU: No disponible")
    
    # Fans
    fans = monitor.get_fan_stats()
    if fans:
        print(f"\nVentiladores ({fans.source}):")
        print(f"  Fan 1 (CPU):  {fans.fan1_rpm} RPM")
        print(f"  Fan 2 (GPU):  {fans.fan2_rpm} RPM")
    else:
        print("\nVentiladores: No disponible")
    
    # RAM
    ram = monitor.get_ram_stats()
    if ram:
        print(f"\nRAM:")
        print(f"  Uso:        {ram.used_gb}/{ram.total_gb} GB ({ram.percent}%)")
        print(f"  Disponible: {ram.available_gb} GB")
    else:
        print("\nRAM: No disponible")
    
    # Battery
    battery = monitor.get_battery_stats()
    if battery:
        print(f"\nBatería:")
        print(f"  Carga:      {battery.percent}%")
        print(f"  Salud:      {battery.health_percent}%")
        print(f"  Cargando:   {'Sí' if battery.is_charging else 'No'}")
        print(f"  Conectado:  {'Sí' if battery.power_plugged else 'No'}")
        if battery.time_remaining:
            print(f"  Restante:   {battery.time_remaining}")
    else:
        print("\nBatería: No disponible")
    
    # GPU
    gpu = monitor.get_gpu_stats()
    if gpu:
        print(f"\nGPU ({gpu.name}):")
        print(f"  Temperatura: {gpu.temp}°C")
        print(f"  Uso:         {gpu.usage_percent}%")
        print(f"  VRAM:        {gpu.memory_used_mb}/{gpu.memory_total_mb} MB")
        print(f"  Ventilador:  {gpu.fan_speed_percent}%")
    else:
        print("\nGPU NVIDIA: No disponible o nvidia-smi no encontrado")


if __name__ == "__main__":
    main()
