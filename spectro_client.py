import json
import socket
import threading

from PyQt6 import QtCore, QtWidgets

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg


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
    """Main window using PyQt6."""

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
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QHBoxLayout(central_widget)

        button_layout = QtWidgets.QVBoxLayout()
        layout.addLayout(button_layout)

        button_names = [
            "Dark Reference",
            "White Reference",
            "Attenuated White Reference",
            "Mercury Reference",
            "Neon Reference",
            "Aiming Beam",
        ]
        for name in button_names:
            btn = QtWidgets.QPushButton(name)
            btn.clicked.connect(lambda _=False, n=name: self.client.send_command(n))
            button_layout.addWidget(btn)

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
        layout.addWidget(self.canvas, 1)

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
    window = SpectroApp()
    window.show()
    qt_app.exec()


if __name__ == "__main__":
    main()
