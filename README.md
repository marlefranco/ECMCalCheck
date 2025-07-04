# ECMCalCheck

A TCP client application with a graphical user interface for displaying and analyzing spectral data.

## Overview

ECMCalCheck is a Python application that connects to a spectral data server via TCP, sends commands to request different types of reference measurements, and visualizes the received spectral data using matplotlib. The application features a dark-themed GUI built with PyQt6, loaded from a Qt Designer file.

## Features

- TCP client for connecting to a spectral data server
- Dark-themed GUI built with PyQt6
- Buttons for different reference measurements:
  - Dark Reference
  - White Reference
  - Attenuated White Reference
  - Mercury Reference
  - Neon Reference
  - Aiming Beam
- Real-time plotting of spectral data (wavelength vs. intensity)

## Installation

### Prerequisites

- Python 3.6 or higher
- PyQt6
- matplotlib

### Install Dependencies

```bash
pip install PyQt6 matplotlib
```

## Usage

### Running the Client

Run the client with:

```bash
python spectro_client.py
```

By default, the client connects to `127.0.0.1:12345`. To use a different server, modify the host and port in the `SpectroApp` initialization in `spectro_client.py`.

### Example Server

For testing purposes, an example server is included that simulates a spectral data source. Run the server with:

```bash
python example_server.py
```

The example server:
- Listens on `127.0.0.1:12345` by default
- Accepts the same commands as expected by the client
- Generates simulated spectral data for each command
- Responds with JSON-formatted data

You can customize the server host and port with command-line arguments:

```bash
python example_server.py --host 192.168.1.100 --port 5000
```

Start the server first, then run the client to see the application in action.

## Development

The application consists of:

- `spectro_client.py` - Main Python script implementing the TCP client and GUI
- `spectro_app.ui` - Qt Designer file defining the GUI layout
- `ui_spectro_app.py` - Auto-generated Python code from the UI file
- `example_server.py` - Example TCP server that simulates a spectral data source for testing
- `REQUIREMENTS.md` - Detailed requirements and recommendations for future development

### UI Development

The application uses auto-generated UI code instead of loading the UI file at runtime. If you make changes to the UI file (`spectro_app.ui`) using Qt Designer, you need to regenerate the UI code.

You can do this in one of two ways:

1. Using the provided script:

```bash
python update_ui.py
```

2. Or using the pyuic6 command directly:

```bash
pyuic6 -o ui_spectro_app.py spectro_app.ui
```

Either method will update the `ui_spectro_app.py` file with the new UI code.

## License

This project is open source and available under the [MIT License](https://opensource.org/licenses/MIT).

## Future Development

See [REQUIREMENTS.md](REQUIREMENTS.md) for a detailed list of planned improvements and feature additions.
