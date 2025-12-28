#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dell G15 System Tray Module
Provides system tray icon with quick access to thermal profiles.
"""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QPixmap, QAction
from PyQt6.QtCore import QByteArray, pyqtSignal, QObject

from typing import Optional, Callable


class SystemTrayIcon(QObject):
    """
    System tray icon for Dell G15 Fan Control.
    
    Provides quick access to thermal profiles and shows
    current temperature in tooltip.
    """
    
    # Signals
    mode_requested = pyqtSignal(str)  # Emitted when user selects a mode
    show_window_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._tray_icon: Optional[QSystemTrayIcon] = None
        self._menu: Optional[QMenu] = None
        self._current_mode: str = "balanced"
        self._current_temp: float = 0.0
        
        self._setup_tray()
    
    def _create_fan_icon(self, color: str = "#3498db") -> QIcon:
        """Create a fan icon as SVG."""
        svg_data = f"""
        <svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
          <g transform="translate(32,32)">
            <path d="M0-28 A28 28 0 0 1 24.24 14 L12.12 7 A14 14 0 0 0 0 -14Z" fill="{color}"/>
            <path d="M24.24 14 A28 28 0 0 1 -24.24 14 L-12.12 7 A14 14 0 0 0 12.12 7Z" fill="{color}"/>
            <path d="M-24.24 14 A28 28 0 0 1 0 -28 L0 -14 A14 14 0 0 0 -12.12 7Z" fill="{color}"/>
            <circle cx="0" cy="0" r="6" fill="white"/>
          </g>
        </svg>
        """
        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray(svg_data.encode('utf-8')))
        return QIcon(pixmap)
    
    def _setup_tray(self) -> None:
        """Setup the system tray icon and menu."""
        # Create tray icon
        self._tray_icon = QSystemTrayIcon(self._create_fan_icon(), self.parent())
        
        # Create context menu
        self._menu = QMenu()
        self._menu.setStyleSheet("""
            QMenu {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #3498db;
            }
            QMenu::separator {
                height: 1px;
                background: #34495e;
                margin: 5px 10px;
            }
        """)
        
        # Show/Hide action
        show_action = QAction("📊 Mostrar/Ocultar", self._menu)
        show_action.triggered.connect(self.show_window_requested.emit)
        self._menu.addAction(show_action)
        
        self._menu.addSeparator()
        
        # Mode actions
        self._mode_actions = {}
        
        modes = [
            ("balanced", "⚖️ Equilibrado", "Modo equilibrado - Curva conservadora"),
            ("performance", "🚀 Rendimiento", "Modo rendimiento - Curva agresiva"),
            ("quiet", "🔇 Silencioso", "Modo silencioso - RPM limitadas"),
            ("gmode", "🎮 G-Mode", "Game Shift - Ventiladores al 100%"),
        ]
        
        for mode_id, label, tooltip in modes:
            action = QAction(label, self._menu)
            action.setToolTip(tooltip)
            action.setCheckable(True)
            action.triggered.connect(lambda checked, m=mode_id: self._on_mode_clicked(m))
            self._menu.addAction(action)
            self._mode_actions[mode_id] = action
        
        # Set initial mode
        if "balanced" in self._mode_actions:
            self._mode_actions["balanced"].setChecked(True)
        
        self._menu.addSeparator()
        
        # Quit action
        quit_action = QAction("❌ Salir", self._menu)
        quit_action.triggered.connect(self.quit_requested.emit)
        self._menu.addAction(quit_action)
        
        # Set menu
        self._tray_icon.setContextMenu(self._menu)
        
        # Connect double-click to show window
        self._tray_icon.activated.connect(self._on_activated)
        
        # Set initial tooltip
        self._update_tooltip()
    
    def _on_mode_clicked(self, mode: str) -> None:
        """Handle mode selection from menu."""
        self.mode_requested.emit(mode)
    
    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window_requested.emit()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Single click - could show tooltip or quick menu
            pass
    
    def _update_tooltip(self) -> None:
        """Update the tray icon tooltip."""
        mode_names = {
            "balanced": "Equilibrado",
            "performance": "Rendimiento",
            "quiet": "Silencioso",
            "gmode": "G-Mode"
        }
        
        mode_name = mode_names.get(self._current_mode, self._current_mode)
        tooltip = f"Dell G15 Fan Control\n"
        tooltip += f"Modo: {mode_name}\n"
        
        if self._current_temp > 0:
            tooltip += f"CPU: {self._current_temp:.1f}°C"
        
        self._tray_icon.setToolTip(tooltip)
    
    def set_mode(self, mode: str) -> None:
        """
        Update the displayed current mode.
        
        Args:
            mode: The current thermal mode
        """
        self._current_mode = mode
        
        # Update checkmarks
        for mode_id, action in self._mode_actions.items():
            action.setChecked(mode_id == mode)
        
        # Update icon color based on mode
        colors = {
            "balanced": "#3498db",    # Blue
            "performance": "#e67e22", # Orange
            "quiet": "#27ae60",       # Green
            "gmode": "#e74c3c"        # Red
        }
        color = colors.get(mode, "#3498db")
        self._tray_icon.setIcon(self._create_fan_icon(color))
        
        self._update_tooltip()
    
    def set_temperature(self, temp: float) -> None:
        """
        Update the displayed temperature.
        
        Args:
            temp: Current CPU temperature in Celsius
        """
        self._current_temp = temp
        self._update_tooltip()
    
    def show(self) -> None:
        """Show the tray icon."""
        if self._tray_icon:
            self._tray_icon.show()
    
    def hide(self) -> None:
        """Hide the tray icon."""
        if self._tray_icon:
            self._tray_icon.hide()
    
    def show_message(self, title: str, message: str, 
                     icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
                     ms_timeout: int = 3000) -> None:
        """
        Show a notification message.
        
        Args:
            title: Notification title
            message: Notification message
            icon: Icon type
            ms_timeout: How long to show the notification
        """
        if self._tray_icon:
            self._tray_icon.showMessage(title, message, icon, ms_timeout)
    
    def is_visible(self) -> bool:
        """Check if tray icon is visible."""
        return self._tray_icon.isVisible() if self._tray_icon else False


def main():
    """Test the system tray icon."""
    import sys
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    tray = SystemTrayIcon()
    tray.show()
    
    # Connect signals for testing
    tray.mode_requested.connect(lambda m: print(f"Mode requested: {m}"))
    tray.show_window_requested.connect(lambda: print("Show window requested"))
    tray.quit_requested.connect(app.quit)
    
    # Test mode changes
    from PyQt6.QtCore import QTimer
    
    modes = ["balanced", "performance", "quiet", "gmode"]
    mode_index = [0]
    
    def cycle_mode():
        mode_index[0] = (mode_index[0] + 1) % len(modes)
        tray.set_mode(modes[mode_index[0]])
        tray.set_temperature(45.0 + mode_index[0] * 10)
        tray.show_message("Modo cambiado", f"Ahora: {modes[mode_index[0]]}")
    
    timer = QTimer()
    timer.timeout.connect(cycle_mode)
    timer.start(5000)
    
    print("Sistema tray activo. Haz clic derecho en el icono para ver el menú.")
    print("El modo cambiará cada 5 segundos para demostrar la funcionalidad.")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
