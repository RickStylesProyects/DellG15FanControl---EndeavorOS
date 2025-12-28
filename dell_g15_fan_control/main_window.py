#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dell G15 Fan Control - Main Window
Modern PyQt6 GUI for controlling thermal profiles and monitoring system stats.
"""

import sys
import os
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QGridLayout, QCheckBox, QComboBox,
    QGroupBox, QTabWidget, QProgressBar, QMessageBox, QSpacerItem,
    QSizePolicy, QScrollArea
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPalette, QColor

# Local imports
from .acpi_controller import ACPIController, ThermalMode
from .system_monitor import SystemMonitor
from .config_manager import ConfigManager
from .system_tray import SystemTrayIcon


class StatCard(QFrame):
    """A card widget for displaying a single statistic."""
    
    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("statsCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumSize(120, 70)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_text = f"{icon} {title}" if icon else title
        self.title_label = QLabel(title_text)
        self.title_label.setObjectName("statLabel")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setMinimumHeight(20)
        layout.addWidget(self.title_label)
        
        # Value
        self.value_label = QLabel("--")
        self.value_label.setObjectName("statValue")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setMinimumHeight(25)
        layout.addWidget(self.value_label)
    
    def set_value(self, value: str, style_class: str = "") -> None:
        """Set the displayed value."""
        self.value_label.setText(value)
        if style_class:
            self.value_label.setObjectName(style_class)
            self.value_label.style().unpolish(self.value_label)
            self.value_label.style().polish(self.value_label)


class FanSpeedWidget(QFrame):
    """Widget for displaying fan speed with a visual indicator."""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("statsCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumSize(150, 90)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        self.title_label = QLabel(f"🌀 {title}")
        self.title_label.setObjectName("statLabel")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setMinimumHeight(20)
        layout.addWidget(self.title_label)
        
        # RPM Value
        self.rpm_label = QLabel("-- RPM")
        self.rpm_label.setObjectName("statValue")
        self.rpm_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rpm_label.setMinimumHeight(25)
        layout.addWidget(self.rpm_label)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 5500)  # Max RPM for G15
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(8)
        layout.addWidget(self.progress)
    
    def set_rpm(self, rpm: int) -> None:
        """Set the displayed RPM value."""
        self.rpm_label.setText(f"{rpm} RPM")
        self.progress.setValue(min(rpm, 5500))


class MainWindow(QMainWindow):
    """Main window for Dell G15 Fan Control application."""
    
    def __init__(self, start_minimized: bool = False):
        super().__init__()
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.system_monitor = SystemMonitor()
        self.acpi_controller = ACPIController(
            force_intel=self.config_manager.get("use_intel_path", True)
        )
        
        self._current_mode: str = self.config_manager.get("default_mode", "balanced")
        self._is_root: bool = os.geteuid() == 0
        
        # Setup UI
        self._setup_ui()
        self._load_stylesheet()
        self._setup_tray()
        self._setup_timers()
        
        # Check system requirements
        self._check_requirements()
        
        # Load saved configuration
        self._load_config()
        
        # Apply and display saved mode
        self._apply_startup_mode()
        
        # Show or minimize
        if start_minimized and self.config_manager.get("minimize_to_tray", True):
            self.hide()
            self.tray_icon.show()
        else:
            self.show()
    
    def _setup_ui(self) -> None:
        """Setup the main user interface."""
        self.setWindowTitle("Dell G15 Fan Control Ultimate")
        self.setMinimumSize(600, 700)
        self.setWindowIcon(self._create_app_icon())
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Tab widget
        tabs = QTabWidget()
        tabs.addTab(self._create_monitor_tab(), "📊 Monitor")
        tabs.addTab(self._create_control_tab(), "🎮 Control")
        tabs.addTab(self._create_settings_tab(), "⚙️ Configuración")
        main_layout.addWidget(tabs)
        
        # Status bar
        self.statusBar().showMessage("Listo")
    
    def _create_app_icon(self) -> QIcon:
        """Create the application icon."""
        from PyQt6.QtCore import QByteArray
        
        svg_data = """
        <svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
          <rect width="64" height="64" rx="12" fill="#1a1a2e"/>
          <g transform="translate(32,32)">
            <path d="M0-22 A22 22 0 0 1 19.05 11 L9.52 5.5 A11 11 0 0 0 0 -11Z" fill="#e94560"/>
            <path d="M19.05 11 A22 22 0 0 1 -19.05 11 L-9.52 5.5 A11 11 0 0 0 9.52 5.5Z" fill="#e94560"/>
            <path d="M-19.05 11 A22 22 0 0 1 0 -22 L0 -11 A11 11 0 0 0 -9.52 5.5Z" fill="#e94560"/>
            <circle cx="0" cy="0" r="5" fill="#00d9ff"/>
          </g>
        </svg>
        """
        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray(svg_data.encode('utf-8')))
        return QIcon(pixmap)
    
    def _create_header(self) -> QWidget:
        """Create the header section."""
        header = QFrame()
        header.setObjectName("controlCard")
        layout = QHBoxLayout(header)
        
        # Title
        title_layout = QVBoxLayout()
        
        title = QLabel("Dell G15 Fan Control")
        title.setObjectName("titleLabel")
        title_layout.addWidget(title)
        
        subtitle = QLabel("Control de perfiles térmicos para Dell G15 5511")
        subtitle.setObjectName("subtitleLabel")
        title_layout.addWidget(subtitle)
        
        layout.addLayout(title_layout)
        layout.addStretch()
        
        # Current mode indicator
        self.mode_indicator = QLabel("⚖️ Equilibrado")
        self.mode_indicator.setObjectName("statValue")
        self.mode_indicator.setStyleSheet("font-size: 16pt;")
        layout.addWidget(self.mode_indicator)
        
        return header
    
    def _create_monitor_tab(self) -> QWidget:
        """Create the monitoring tab."""
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Create content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(10)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # CPU Section
        cpu_group = QGroupBox("Procesador")
        cpu_layout = QGridLayout(cpu_group)
        cpu_layout.setSpacing(5)
        
        self.cpu_temp_card = StatCard("Temperatura", "🌡️")
        self.cpu_usage_card = StatCard("Uso CPU", "📈")
        self.cpu_freq_card = StatCard("Frecuencia", "⚡")
        
        cpu_layout.addWidget(self.cpu_temp_card, 0, 0)
        cpu_layout.addWidget(self.cpu_usage_card, 0, 1)
        cpu_layout.addWidget(self.cpu_freq_card, 0, 2)
        
        layout.addWidget(cpu_group)
        
        # Fans Section
        fans_group = QGroupBox("Ventiladores")
        fans_layout = QHBoxLayout(fans_group)
        fans_layout.setSpacing(5)
        
        self.fan1_widget = FanSpeedWidget("Fan 1 (CPU)")
        self.fan2_widget = FanSpeedWidget("Fan 2 (GPU)")
        
        fans_layout.addWidget(self.fan1_widget)
        fans_layout.addWidget(self.fan2_widget)
        
        layout.addWidget(fans_group)
        
        # System Section
        sys_group = QGroupBox("Sistema")
        sys_layout = QGridLayout(sys_group)
        sys_layout.setSpacing(5)
        
        self.ram_card = StatCard("RAM", "💾")
        self.battery_card = StatCard("Batería", "🔋")
        self.battery_health_card = StatCard("Salud Batería", "❤️")
        
        sys_layout.addWidget(self.ram_card, 0, 0)
        sys_layout.addWidget(self.battery_card, 0, 1)
        sys_layout.addWidget(self.battery_health_card, 0, 2)
        
        layout.addWidget(sys_group)
        
        # GPU Section
        gpu_group = QGroupBox("GPU NVIDIA")
        gpu_layout = QGridLayout(gpu_group)
        gpu_layout.setSpacing(5)
        
        self.gpu_temp_card = StatCard("Temp GPU", "🎮")
        self.gpu_usage_card = StatCard("Uso GPU", "📊")
        self.gpu_vram_card = StatCard("VRAM", "🎞️")
        
        gpu_layout.addWidget(self.gpu_temp_card, 0, 0)
        gpu_layout.addWidget(self.gpu_usage_card, 0, 1)
        gpu_layout.addWidget(self.gpu_vram_card, 0, 2)
        
        layout.addWidget(gpu_group)
        
        layout.addStretch()
        
        # Set content to scroll area
        scroll.setWidget(content)
        return scroll
    
    def _create_control_tab(self) -> QWidget:
        """Create the control tab."""
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Create content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(10)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Mode buttons
        modes_group = QGroupBox("Perfiles Térmicos")
        modes_layout = QVBoxLayout(modes_group)
        modes_layout.setSpacing(10)
        
        # G-Mode button (large)
        self.btn_gmode = QPushButton("🎮 G-MODE (Game Shift)")
        self.btn_gmode.setObjectName("btnGMode")
        self.btn_gmode.setCheckable(True)
        self.btn_gmode.setMinimumHeight(60)
        self.btn_gmode.setToolTip("Ventiladores al 100% - Máximo rendimiento")
        self.btn_gmode.clicked.connect(lambda: self._set_mode("gmode"))
        modes_layout.addWidget(self.btn_gmode)
        
        # Other mode buttons
        other_modes_layout = QHBoxLayout()
        
        self.btn_performance = QPushButton("🚀 Rendimiento")
        self.btn_performance.setObjectName("btnPerformance")
        self.btn_performance.setCheckable(True)
        self.btn_performance.setToolTip("Curva agresiva - Para juegos y trabajo intensivo")
        self.btn_performance.clicked.connect(lambda: self._set_mode("performance"))
        other_modes_layout.addWidget(self.btn_performance)
        
        self.btn_balanced = QPushButton("⚖️ Equilibrado")
        self.btn_balanced.setObjectName("btnBalanced")
        self.btn_balanced.setCheckable(True)
        self.btn_balanced.setChecked(True)
        self.btn_balanced.setToolTip("Curva conservadora - Uso general")
        self.btn_balanced.clicked.connect(lambda: self._set_mode("balanced"))
        other_modes_layout.addWidget(self.btn_balanced)
        
        self.btn_quiet = QPushButton("🔇 Silencioso")
        self.btn_quiet.setObjectName("btnQuiet")
        self.btn_quiet.setCheckable(True)
        self.btn_quiet.setToolTip("RPM limitadas - Para trabajo silencioso")
        self.btn_quiet.clicked.connect(lambda: self._set_mode("quiet"))
        other_modes_layout.addWidget(self.btn_quiet)
        
        modes_layout.addLayout(other_modes_layout)
        
        layout.addWidget(modes_group)
        
        # Info section
        info_group = QGroupBox("Información de Modos")
        info_layout = QVBoxLayout(info_group)
        
        info_text = """
<style>
    .mode-title { color: #e94560; font-weight: bold; }
    .mode-desc { color: #a8a8a8; }
</style>
<p><span class="mode-title">🎮 G-Mode (Game Shift):</span><br/>
<span class="mode-desc">Fuerza los ventiladores al 100%. Ideal para gaming intensivo o benchmarks.</span></p>

<p><span class="mode-title">🚀 Rendimiento:</span><br/>
<span class="mode-desc">Curva agresiva. Los ventiladores responden más rápido a aumentos de temperatura.</span></p>

<p><span class="mode-title">⚖️ Equilibrado:</span><br/>
<span class="mode-desc">Modo por defecto. Balance entre ruido y temperatura.</span></p>

<p><span class="mode-title">🔇 Silencioso:</span><br/>
<span class="mode-desc">Limita las RPM máximas. Para trabajo de oficina o multimedia.</span></p>
        """
        
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setOpenExternalLinks(True)
        info_layout.addWidget(info_label)
        
        layout.addWidget(info_group)
        
        # Status
        status_group = QGroupBox("Estado del Sistema")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("✅ Sistema listo")
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(status_group)
        
        layout.addStretch()
        
        # Set content to scroll area
        scroll.setWidget(content)
        return scroll
    
    def _create_settings_tab(self) -> QWidget:
        """Create the settings tab."""
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Create content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(10)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Startup settings
        startup_group = QGroupBox("Inicio")
        startup_layout = QVBoxLayout(startup_group)
        
        self.chk_autostart = QCheckBox("Iniciar con el sistema")
        self.chk_autostart.setToolTip("Ejecutar la aplicación automáticamente al iniciar sesión")
        self.chk_autostart.stateChanged.connect(self._on_autostart_changed)
        startup_layout.addWidget(self.chk_autostart)
        
        self.chk_minimized = QCheckBox("Iniciar minimizado en bandeja")
        self.chk_minimized.stateChanged.connect(self._on_setting_changed)
        startup_layout.addWidget(self.chk_minimized)
        
        layout.addWidget(startup_group)
        
        # Behavior settings
        behavior_group = QGroupBox("Comportamiento")
        behavior_layout = QVBoxLayout(behavior_group)
        
        self.chk_tray = QCheckBox("Minimizar a bandeja en lugar de cerrar")
        self.chk_tray.setChecked(True)
        self.chk_tray.stateChanged.connect(self._on_setting_changed)
        behavior_layout.addWidget(self.chk_tray)
        
        self.chk_notifications = QCheckBox("Mostrar notificaciones al cambiar modo")
        self.chk_notifications.setChecked(True)
        self.chk_notifications.stateChanged.connect(self._on_setting_changed)
        behavior_layout.addWidget(self.chk_notifications)
        
        # Mode on resume
        resume_layout = QHBoxLayout()
        resume_label = QLabel("Modo al despertar de suspensión:")
        resume_layout.addWidget(resume_label)
        
        self.combo_resume_mode = QComboBox()
        self.combo_resume_mode.addItems(["Equilibrado", "Rendimiento", "Silencioso", "G-Mode", "Último usado"])
        self.combo_resume_mode.currentIndexChanged.connect(self._on_setting_changed)
        resume_layout.addWidget(self.combo_resume_mode)
        resume_layout.addStretch()
        
        behavior_layout.addLayout(resume_layout)
        
        layout.addWidget(behavior_group)
        
        # CPU Governor settings
        governor_group = QGroupBox("Gobernador CPU")
        governor_layout = QVBoxLayout(governor_group)
        
        self.chk_governor = QCheckBox("Cambiar gobernador CPU automáticamente")
        self.chk_governor.setToolTip("Cambiar a 'performance' en G-Mode y 'powersave' en otros modos")
        self.chk_governor.setChecked(True)
        self.chk_governor.stateChanged.connect(self._on_setting_changed)
        governor_layout.addWidget(self.chk_governor)
        
        layout.addWidget(governor_group)
        
        # Advanced settings
        advanced_group = QGroupBox("Avanzado")
        advanced_layout = QVBoxLayout(advanced_group)
        
        # Update interval
        interval_layout = QHBoxLayout()
        interval_label = QLabel("Intervalo de actualización:")
        interval_layout.addWidget(interval_label)
        
        self.combo_interval = QComboBox()
        self.combo_interval.addItems(["1 segundo", "2 segundos", "5 segundos"])
        self.combo_interval.setCurrentIndex(1)
        self.combo_interval.currentIndexChanged.connect(self._on_interval_changed)
        interval_layout.addWidget(self.combo_interval)
        interval_layout.addStretch()
        
        advanced_layout.addLayout(interval_layout)
        
        # Install resume service button
        self.btn_install_service = QPushButton("📦 Instalar servicio de resume (requiere sudo)")
        self.btn_install_service.setToolTip("Crea un servicio systemd para restaurar el perfil térmico al despertar")
        self.btn_install_service.clicked.connect(self._install_resume_service)
        advanced_layout.addWidget(self.btn_install_service)
        
        layout.addWidget(advanced_group)
        
        # About
        about_group = QGroupBox("Acerca de")
        about_layout = QVBoxLayout(about_group)
        
        about_text = QLabel("""
<p><b>Dell G15 Fan Control Ultimate</b> v1.0.0</p>
<p>Control de perfiles térmicos para Dell G15 5511 en EndeavourOS</p>
<p style="color: #a8a8a8;">Basado en Dell_G15_Fan_Cli con mejoras significativas.</p>
<p style="color: #e94560;">⚠️ Requiere el módulo acpi_call y privilegios de root.</p>
        """)
        about_text.setWordWrap(True)
        about_layout.addWidget(about_text)
        
        layout.addWidget(about_group)
        
        layout.addStretch()
        
        # Set content to scroll area
        scroll.setWidget(content)
        return scroll
    
    def _load_stylesheet(self) -> None:
        """Load the QSS stylesheet."""
        style_path = Path(__file__).parent / "styles.qss"
        
        if style_path.exists():
            with open(style_path, 'r') as f:
                self.setStyleSheet(f.read())
    
    def _setup_tray(self) -> None:
        """Setup the system tray icon."""
        self.tray_icon = SystemTrayIcon(self)
        self.tray_icon.mode_requested.connect(self._set_mode)
        self.tray_icon.show_window_requested.connect(self._toggle_window)
        self.tray_icon.quit_requested.connect(self._quit_app)
        self.tray_icon.show()
    
    def _setup_timers(self) -> None:
        """Setup update timers."""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_stats)
        self.update_timer.start(2000)  # 2 seconds default
        
        # Initial update
        self._update_stats()
    
    def _check_requirements(self) -> None:
        """Check system requirements."""
        messages = []
        
        # Check root
        if not self._is_root:
            messages.append("⚠️ No se está ejecutando como root. Algunas funciones estarán limitadas.")
        
        # Check ACPI
        all_passed, checks = self.acpi_controller.run_checks()
        
        for name, passed, msg in checks:
            if not passed:
                messages.append(f"❌ {name}: {msg}")
        
        if messages:
            self.status_label.setText("\n".join(messages))
            self.status_label.setStyleSheet("color: #e74c3c;")
        else:
            self.status_label.setText("✅ Sistema listo - Todos los requisitos cumplidos")
            self.status_label.setStyleSheet("color: #27ae60;")
    
    def _load_config(self) -> None:
        """Load configuration into UI."""
        config = self.config_manager.config
        
        self.chk_autostart.setChecked(self.config_manager.is_autostart_enabled())
        self.chk_minimized.setChecked(config.start_minimized)
        self.chk_tray.setChecked(config.minimize_to_tray)
        self.chk_notifications.setChecked(config.show_notifications)
        self.chk_governor.setChecked(config.set_cpu_governor)
        
        # Resume mode
        mode_map = {"balanced": 0, "performance": 1, "quiet": 2, "gmode": 3}
        self.combo_resume_mode.setCurrentIndex(mode_map.get(config.mode_on_resume, 0))
        
        # Update interval
        interval_map = {1000: 0, 2000: 1, 5000: 2}
        self.combo_interval.setCurrentIndex(interval_map.get(config.update_interval_ms, 1))
    
    def _apply_startup_mode(self) -> None:
        """Apply and display the saved mode on startup."""
        # Update UI to show saved mode
        mode_labels = {
            "balanced": "⚖️ Equilibrado",
            "performance": "🚀 Rendimiento",
            "quiet": "🔇 Silencioso",
            "gmode": "🎮 G-Mode"
        }
        
        # Update mode indicator in header
        self.mode_indicator.setText(mode_labels.get(self._current_mode, "⚖️ Equilibrado"))
        
        # Update button states
        self.btn_balanced.setChecked(self._current_mode == "balanced")
        self.btn_performance.setChecked(self._current_mode == "performance")
        self.btn_quiet.setChecked(self._current_mode == "quiet")
        self.btn_gmode.setChecked(self._current_mode == "gmode")
        
        # Update tray icon
        self.tray_icon.set_mode(self._current_mode)
    
    def _save_config(self) -> None:
        """Save configuration from UI."""
        config = self.config_manager.config
        
        config.start_minimized = self.chk_minimized.isChecked()
        config.minimize_to_tray = self.chk_tray.isChecked()
        config.show_notifications = self.chk_notifications.isChecked()
        config.set_cpu_governor = self.chk_governor.isChecked()
        
        # Resume mode
        mode_map = {0: "balanced", 1: "performance", 2: "quiet", 3: "gmode", 4: "last"}
        config.mode_on_resume = mode_map.get(self.combo_resume_mode.currentIndex(), "balanced")
        
        # Update interval
        interval_map = {0: 1000, 1: 2000, 2: 5000}
        config.update_interval_ms = interval_map.get(self.combo_interval.currentIndex(), 2000)
        
        self.config_manager.save()
    
    def _update_stats(self) -> None:
        """Update system statistics display."""
        # CPU
        cpu = self.system_monitor.get_cpu_stats()
        if cpu:
            temp_style = "statValue"
            if cpu.average_temp > 85:
                temp_style = "tempHot"
            elif cpu.average_temp > 70:
                temp_style = "tempWarm"
            else:
                temp_style = "tempCool"
            
            self.cpu_temp_card.set_value(f"{cpu.average_temp}°C", temp_style)
            self.cpu_usage_card.set_value(f"{cpu.usage_percent}%")
            self.cpu_freq_card.set_value(f"{int(cpu.frequency_mhz)} MHz")
            
            # Update tray tooltip
            self.tray_icon.set_temperature(cpu.average_temp)
        
        # Fans
        fans = self.system_monitor.get_fan_stats()
        if fans:
            self.fan1_widget.set_rpm(fans.fan1_rpm)
            self.fan2_widget.set_rpm(fans.fan2_rpm)
        
        # RAM
        ram = self.system_monitor.get_ram_stats()
        if ram:
            self.ram_card.set_value(f"{ram.used_gb:.1f}/{ram.total_gb:.1f} GB")
        
        # Battery
        battery = self.system_monitor.get_battery_stats()
        if battery:
            status = "⚡" if battery.is_charging else "🔌" if battery.power_plugged else ""
            self.battery_card.set_value(f"{status} {battery.percent:.0f}%")
            self.battery_health_card.set_value(f"{battery.health_percent:.1f}%")
        
        # GPU
        gpu = self.system_monitor.get_gpu_stats()
        if gpu:
            self.gpu_temp_card.set_value(f"{gpu.temp}°C")
            self.gpu_usage_card.set_value(f"{gpu.usage_percent:.0f}%")
            self.gpu_vram_card.set_value(f"{gpu.memory_used_mb}/{gpu.memory_total_mb} MB")
        else:
            self.gpu_temp_card.set_value("N/A")
            self.gpu_usage_card.set_value("N/A")
            self.gpu_vram_card.set_value("N/A")
    
    def _set_mode(self, mode: str) -> None:
        """Set the thermal mode."""
        mode_map = {
            "balanced": ThermalMode.BALANCED,
            "performance": ThermalMode.PERFORMANCE,
            "quiet": ThermalMode.QUIET,
            "gmode": ThermalMode.GMODE
        }
        
        if mode not in mode_map:
            return
        
        # Update button states
        self.btn_balanced.setChecked(mode == "balanced")
        self.btn_performance.setChecked(mode == "performance")
        self.btn_quiet.setChecked(mode == "quiet")
        self.btn_gmode.setChecked(mode == "gmode")
        
        # Update mode indicator
        mode_labels = {
            "balanced": "⚖️ Equilibrado",
            "performance": "🚀 Rendimiento",
            "quiet": "🔇 Silencioso",
            "gmode": "🎮 G-Mode"
        }
        self.mode_indicator.setText(mode_labels.get(mode, mode))
        
        # Apply mode
        if self._is_root:
            if mode == "gmode":
                success, msg = self.acpi_controller.toggle_gmode()
                # Check actual state
                if self.acpi_controller.is_gmode_active:
                    self._current_mode = "gmode"
                else:
                    self._current_mode = "balanced"
                    mode = "balanced"
            else:
                success, msg = self.acpi_controller.set_thermal_mode(mode_map[mode])
                if success:
                    self._current_mode = mode
            
            # Apply CPU governor if enabled
            if self.chk_governor.isChecked() and success:
                if mode in ["gmode", "performance"]:
                    self.acpi_controller.set_cpu_governor("performance")
                else:
                    self.acpi_controller.set_cpu_governor("powersave")
            
            # Show notification
            if self.config_manager.get("show_notifications", True):
                if success:
                    self.tray_icon.show_message("Modo cambiado", msg)
                else:
                    self.tray_icon.show_message("Error", msg, 
                        QSystemTrayIcon.MessageIcon.Warning)
            
            self.statusBar().showMessage(msg)
        else:
            self.statusBar().showMessage("Se requieren privilegios de root para cambiar el modo")
        
        # Update tray icon
        self.tray_icon.set_mode(mode)
        
        # Save last mode
        self.config_manager.set("default_mode", mode)
        self.config_manager.save()
    
    def _on_autostart_changed(self, state: int) -> None:
        """Handle autostart checkbox change."""
        script_path = str(Path(__file__).parent.parent / "g15_fan_control.py")
        self.config_manager.setup_autostart(state == Qt.CheckState.Checked.value, script_path)
    
    def _on_setting_changed(self) -> None:
        """Handle settings change."""
        self._save_config()
    
    def _on_interval_changed(self, index: int) -> None:
        """Handle update interval change."""
        intervals = {0: 1000, 1: 2000, 2: 5000}
        self.update_timer.setInterval(intervals.get(index, 2000))
        self._save_config()
    
    def _install_resume_service(self) -> None:
        """Show instructions for installing the resume service."""
        script_path = str(Path(__file__).parent.parent / "g15_fan_control.py")
        success, data = self.config_manager.create_systemd_resume_service(script_path)
        
        if success:
            commands = "\n".join(data['install_commands'])
            
            QMessageBox.information(
                self,
                "Instalar servicio de resume",
                f"Para instalar el servicio de resume, ejecuta los siguientes comandos en una terminal:\n\n{commands}\n\nEsto restaurará el perfil térmico al despertar de suspensión."
            )
    
    def _toggle_window(self) -> None:
        """Toggle window visibility."""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()
            self.raise_()
    
    def _quit_app(self) -> None:
        """Quit the application."""
        # Reset to balanced mode before quitting
        if self._is_root and self._current_mode != "balanced":
            self.acpi_controller.set_thermal_mode(ThermalMode.BALANCED)
        
        self.tray_icon.hide()
        QApplication.quit()
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        if self.config_manager.get("minimize_to_tray", True):
            event.ignore()
            self.hide()
            self.tray_icon.show_message(
                "Dell G15 Fan Control",
                "La aplicación sigue ejecutándose en la bandeja del sistema."
            )
        else:
            self._quit_app()


def main():
    """Main entry point for the GUI application."""
    import sys
    
    # Check for --minimized flag
    start_minimized = "--minimized" in sys.argv
    
    # Check for --apply-saved-mode flag (for resume service)
    if "--apply-saved-mode" in sys.argv:
        config = ConfigManager()
        controller = ACPIController(force_intel=config.get("use_intel_path", True))
        
        mode = config.get("mode_on_resume", "balanced")
        if mode == "last":
            mode = config.get("default_mode", "balanced")
        
        if mode == "gmode":
            controller.activate_gmode()
        else:
            mode_map = {
                "balanced": ThermalMode.BALANCED,
                "performance": ThermalMode.PERFORMANCE,
                "quiet": ThermalMode.QUIET
            }
            if mode in mode_map:
                controller.set_thermal_mode(mode_map[mode])
        
        sys.exit(0)
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Dell G15 Fan Control")
    app.setOrganizationName("DellG15Control")
    
    window = MainWindow(start_minimized=start_minimized)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
