import json
import socket
import threading
import tkinter as tk
from tkinter import ttk

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


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
        thread = threading.Thread(target=self._listen, args=(handler,), daemon=True)
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


class SpectroApp(tk.Tk):
    def __init__(self, host: str = "127.0.0.1", port: int = 12345):
        super().__init__()
        self.title("Spectral Client")
        self.configure(bg="#2b2b2b")
        self.client = TCPClient(host, port)
        try:
            self.client.connect()
            self.client.start_listener(self.handle_message)
        except OSError as exc:
            print(f"Connection error: {exc}")

        self._build_ui()

    def _build_ui(self):
        left_frame = tk.Frame(self, bg="#2b2b2b")
        left_frame.pack(side=tk.LEFT, fill=tk.Y)

        button_names = [
            "Dark Reference",
            "White Reference",
            "Attenuated White Reference",
            "Mercury Reference",
            "Neon Reference",
            "Aiming Beam",
        ]
        for name in button_names:
            btn = tk.Button(
                left_frame,
                text=name,
                command=lambda n=name: self.client.send_command(n),
                bg="#444444",
                fg="white",
                activebackground="#555555",
                relief=tk.FLAT,
                width=20,
                pady=5,
            )
            btn.pack(fill=tk.X, padx=5, pady=5)

        plot_frame = tk.Frame(self, bg="#121212")
        plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

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
        self.canvas = FigureCanvasTkAgg(self.figure, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def handle_message(self, message):
        """Handle JSON messages from the server."""
        wavelengths = message.get("wavelengths")
        intensities = message.get("intensities")
        if wavelengths and intensities:
            self.after(0, self.plot_spectrum, wavelengths, intensities)

    def plot_spectrum(self, wavelengths, intensities):
        self.ax.cla()
        self.ax.set_xlabel("Wavelength (nm)")
        self.ax.set_ylabel("Intensity")
        self.ax.grid(True, color="#444444")
        self.ax.plot(wavelengths, intensities, color="cyan")
        self.canvas.draw()


def main():
    app = SpectroApp()
    app.mainloop()


if __name__ == "__main__":
    main()
