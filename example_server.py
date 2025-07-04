"""
Example server for ECMCalCheck.

This is a simple TCP server that simulates a spectral data source.
It listens for commands from the client and responds with simulated spectral data.
"""

import json
import socket
import threading
import time
import math
import random
import argparse
from typing import Dict, List, Tuple, Optional


class SpectralDataGenerator:
    """Generates simulated spectral data for testing."""

    def __init__(self, wavelength_range: Tuple[float, float] = (400.0, 800.0), num_points: int = 1000):
        """
        Initialize the spectral data generator.

        Args:
            wavelength_range: Tuple of (min_wavelength, max_wavelength) in nm
            num_points: Number of data points to generate
        """
        self.wavelength_range = wavelength_range
        self.num_points = num_points
        self.wavelengths = [
            wavelength_range[0] + i * (wavelength_range[1] - wavelength_range[0]) / (num_points - 1)
            for i in range(num_points)
        ]
        
        # Define emission peaks for reference sources
        self.mercury_peaks = [404.7, 435.8, 546.1, 578.0]
        self.neon_peaks = [540.1, 585.2, 614.3, 640.2, 703.2]

    def generate_dark_reference(self) -> Dict[str, List[float]]:
        """Generate dark reference data (baseline noise)."""
        intensities = [random.uniform(0, 10) for _ in range(self.num_points)]
        return {"wavelengths": self.wavelengths, "intensities": intensities}

    def generate_white_reference(self) -> Dict[str, List[float]]:
        """Generate white reference data (broadband spectrum)."""
        intensities = [
            900 + 100 * math.sin(wavelength / 100) + random.uniform(-20, 20)
            for wavelength in self.wavelengths
        ]
        return {"wavelengths": self.wavelengths, "intensities": intensities}

    def generate_attenuated_white_reference(self) -> Dict[str, List[float]]:
        """Generate attenuated white reference data."""
        white_ref = self.generate_white_reference()
        intensities = [intensity * 0.5 for intensity in white_ref["intensities"]]
        return {"wavelengths": self.wavelengths, "intensities": intensities}

    def generate_mercury_reference(self) -> Dict[str, List[float]]:
        """Generate mercury reference data (specific emission lines)."""
        intensities = [0] * self.num_points
        
        # Add emission peaks
        for peak in self.mercury_peaks:
            peak_idx = self._find_nearest_wavelength_index(peak)
            # Create a peak with some width
            for i in range(max(0, peak_idx - 5), min(self.num_points, peak_idx + 6)):
                distance = abs(i - peak_idx)
                intensities[i] += 1000 * math.exp(-0.5 * (distance / 2) ** 2)
        
        # Add noise
        intensities = [i + random.uniform(0, 10) for i in intensities]
        return {"wavelengths": self.wavelengths, "intensities": intensities}

    def generate_neon_reference(self) -> Dict[str, List[float]]:
        """Generate neon reference data (specific emission lines)."""
        intensities = [0] * self.num_points
        
        # Add emission peaks
        for peak in self.neon_peaks:
            peak_idx = self._find_nearest_wavelength_index(peak)
            # Create a peak with some width
            for i in range(max(0, peak_idx - 5), min(self.num_points, peak_idx + 6)):
                distance = abs(i - peak_idx)
                intensities[i] += 1000 * math.exp(-0.5 * (distance / 2) ** 2)
        
        # Add noise
        intensities = [i + random.uniform(0, 10) for i in intensities]
        return {"wavelengths": self.wavelengths, "intensities": intensities}

    def generate_aiming_beam(self) -> Dict[str, List[float]]:
        """Generate aiming beam data (single laser line)."""
        intensities = [0] * self.num_points
        
        # Add a single sharp peak at 650nm (red laser)
        peak_wavelength = 650.0
        peak_idx = self._find_nearest_wavelength_index(peak_wavelength)
        
        # Create a sharp peak
        for i in range(max(0, peak_idx - 3), min(self.num_points, peak_idx + 4)):
            distance = abs(i - peak_idx)
            intensities[i] += 2000 * math.exp(-0.5 * (distance / 1) ** 2)
        
        # Add noise
        intensities = [i + random.uniform(0, 5) for i in intensities]
        return {"wavelengths": self.wavelengths, "intensities": intensities}

    def _find_nearest_wavelength_index(self, wavelength: float) -> int:
        """Find the index of the nearest wavelength in the wavelengths list."""
        return min(range(len(self.wavelengths)), key=lambda i: abs(self.wavelengths[i] - wavelength))


class SpectroServer:
    """TCP server that simulates a spectral data source."""

    def __init__(self, host: str = "127.0.0.1", port: int = 12345):
        """
        Initialize the server.

        Args:
            host: Host address to bind to
            port: Port to listen on
        """
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []
        self.data_generator = SpectralDataGenerator()
        self.running = False
        self.command_handlers = {
            "Dark Reference": self.data_generator.generate_dark_reference,
            "White Reference": self.data_generator.generate_white_reference,
            "Attenuated White Reference": self.data_generator.generate_attenuated_white_reference,
            "Mercury Reference": self.data_generator.generate_mercury_reference,
            "Neon Reference": self.data_generator.generate_neon_reference,
            "Aiming Beam": self.data_generator.generate_aiming_beam,
        }

    def start(self):
        """Start the server."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        
        print(f"Server started on {self.host}:{self.port}")
        print("Available commands:")
        for cmd in self.command_handlers.keys():
            print(f"  - {cmd}")
        
        try:
            while self.running:
                client_socket, addr = self.server_socket.accept()
                print(f"Client connected: {addr}")
                self.clients.append(client_socket)
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, addr),
                    daemon=True
                )
                client_thread.start()
        except KeyboardInterrupt:
            print("Server shutting down...")
        finally:
            self.stop()

    def stop(self):
        """Stop the server and close all connections."""
        self.running = False
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        if self.server_socket:
            self.server_socket.close()
        print("Server stopped")

    def handle_client(self, client_socket: socket.socket, addr: Tuple[str, int]):
        """
        Handle client connection.

        Args:
            client_socket: Client socket
            addr: Client address
        """
        buffer = ""
        try:
            while self.running:
                data = client_socket.recv(4096)
                if not data:
                    break
                
                buffer += data.decode("utf-8")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    try:
                        message = json.loads(line)
                        self.process_command(client_socket, message)
                    except json.JSONDecodeError:
                        print(f"Invalid JSON received: {line}")
        except Exception as e:
            print(f"Error handling client {addr}: {e}")
        finally:
            print(f"Client disconnected: {addr}")
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            try:
                client_socket.close()
            except:
                pass

    def process_command(self, client_socket: socket.socket, message: Dict):
        """
        Process a command from a client.

        Args:
            client_socket: Client socket
            message: Command message
        """
        command = message.get("command")
        if not command:
            return
        
        print(f"Received command: {command}")
        
        # Get the appropriate data generator function
        data_generator = self.command_handlers.get(command)
        if data_generator:
            # Generate the data
            data = data_generator()
            # Send the data
            response = json.dumps(data).encode("utf-8") + b"\n"
            client_socket.sendall(response)
            print(f"Sent {len(data['wavelengths'])} data points")
        else:
            print(f"Unknown command: {command}")


def main():
    """Main function to start the server."""
    parser = argparse.ArgumentParser(description="Spectral data server for ECMCalCheck")
    parser.add_argument("--host", default="127.0.0.1", help="Host address to bind to")
    parser.add_argument("--port", type=int, default=12345, help="Port to listen on")
    args = parser.parse_args()
    
    server = SpectroServer(args.host, args.port)
    server.start()


if __name__ == "__main__":
    main()