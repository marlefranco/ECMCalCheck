import json
import socket
import threading

from PyQt6 import QtCore, QtGui, QtWidgets, uic

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg


def apply_dark_palette(app: QtWidgets.QApplication) -> None:
    """Apply a basic dark theme to the Qt application."""
    app.setStyle("Fusion")
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(18, 18, 18))
    palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(240, 240, 240))
    palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(30, 30, 30))
    palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor(18, 18, 18))
    palette.setColor(QtGui.QPalette.ColorRole.ToolTipBase, QtGui.QColor(240, 240, 240))
    palette.setColor(QtGui.QPalette.ColorRole.ToolTipText, QtGui.QColor(240, 240, 240))
    palette.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor(240, 240, 240))
    palette.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(30, 30, 30))
    palette.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor(240, 240, 240))
    palette.setColor(QtGui.QPalette.ColorRole.BrightText, QtGui.QColor(255, 0, 0))
    palette.setColor(QtGui.QPalette.ColorRole.Link, QtGui.QColor(42, 130, 218))
    palette.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor(42, 130, 218))
    palette.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor(240, 240, 240))
    app.setPalette(palette)


class TCPClient:
    """Simple TCP client sending JSON commands."""

    def __init__(self, host: str = "127.0.0.1", port: int = 12345):
        self.host = host
        self.port = port
        self.sock = None
        self.lock = threading.Lock()

    def connect(self):
        """Connect to the server."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

    def send_command(self, command: str):
        """Send a JSON command string."""
        if not self.sock:
            return
        payload = json.dumps({"command": command}).encode("utf-8") + b"\n"
        with self.lock:
            self.sock.sendall(payload)

    def start_listener(self, handler):
        """Start background thread to listen for messages."""
        thread = threading.Thread(
            target=self._listen,
            args=(handler,),
            daemon=True,
        )
        thread.start()

    def _listen(self, handler):
        buffer = ""
        while True:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break
                buffer += data.decode("utf-8")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    try:
                        message = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    handler(message)
            except OSError:
                break


class SpectroApp(QtWidgets.QMainWindow):
    """Main window using PyQt6 loaded from a .ui file."""

    plot_signal = QtCore.pyqtSignal(list, list)

    def __init__(self, host: str = "127.0.0.1", port: int = 12345):
        super().__init__()
        self.setWindowTitle("Spectral Client")
        self.client = TCPClient(host, port)
        try:
            self.client.connect()
            self.client.start_listener(self.handle_message)
        except OSError as exc:
            print(f"Connection error: {exc}")

        self._build_ui()
        self.plot_signal.connect(self.plot_spectrum)

    def _build_ui(self):
        """Load the UI from the Qt Designer file and wire up widgets."""
        uic.loadUi("spectro_app.ui", self)

        buttons = [
            self.btnDarkRef,
            self.btnWhiteRef,
            self.btnAttWhiteRef,
            self.btnMercuryRef,
            self.btnNeonRef,
            self.btnAimingBeam,
        ]
        for btn in buttons:
            btn.clicked.connect(lambda _=False, n=btn.text(): self.client.send_command(n))

        matplotlib.rcParams.update({
            "axes.facecolor": "#121212",
            "figure.facecolor": "#121212",
            "text.color": "white",
            "axes.labelcolor": "white",
            "xtick.color": "white",
            "ytick.color": "white",
        })
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel("Wavelength (nm)")
        self.ax.set_ylabel("Intensity")
        self.ax.grid(True, color="#444444")
        self.canvas = FigureCanvasQTAgg(self.figure)
        plot_layout = QtWidgets.QVBoxLayout(self.plotArea)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.addWidget(self.canvas)

    def handle_message(self, message):
        """Handle JSON messages from the server."""
        wavelengths = message.get("wavelengths")
        intensities = message.get("intensities")
        if wavelengths and intensities:
            self.plot_signal.emit(wavelengths, intensities)

    def plot_spectrum(self, wavelengths, intensities):
        self.ax.cla()
        self.ax.set_xlabel("Wavelength (nm)")
        self.ax.set_ylabel("Intensity")
        self.ax.grid(True, color="#444444")
        self.ax.plot(wavelengths, intensities, color="cyan")
        self.canvas.draw()


def main():
    qt_app = QtWidgets.QApplication([])
    apply_dark_palette(qt_app)
    window = SpectroApp()
    window.show()
    qt_app.exec()


if __name__ == "__main__":
    main()
