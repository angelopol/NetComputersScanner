# NetComScan

A Python-based network identification tool designed to find and identify microcontrollers (Raspberry Pi, Orange Pi) on your local network.

## Features
- **Automatic Subnet Discovery**: Finds your local IP and scans the corresponding /24 subnet.
- **Microcontroller Identification**: Matches MAC OUIs for Raspberry Pi and Orange Pi.
- **Hostname Resolution**: Quick identification of devices via network hostnames.
- **Clean CLI Output**: Uses `rich` to provide a beautiful, readable table of results.
- **High Compatibility**: Uses `scapy` if available, with a robust fallback to system `arp` and `ping` commands.

## Installation

### From GitHub
You can install the package directly from GitHub:
```bash
pip install git+https://github.com/angelopol/NetComputersScanner.git
```

### From Source
1. Clone the repository:
   ```bash
   git clone https://github.com/angelopol/NetComputersScanner.git
   cd NetComputersScanner
   ```
2. Install the package:
   ```bash
   pip install .
   ```
   *For development, use `pip install -e .`.*

### Dependencies
The main dependency is `rich`. For better accuracy, you can optionally install `scapy`:
```bash
pip install scapy
```

## Usage

Once installed, you can run the scanner in two ways:

### 1. Using the Command Line Entry Point
```bash
netcomscan
```

### 2. Using the Python Module
```bash
python -m NetComScan
```

## How it Works
1. **Network Mapping**: The script identifies your local IP and calculates the target subnet.
2. **Device Discovery**:
   - If `scapy` is installed, it sends ARP requests to all IPs.
   - If not, it pings all IPs in the range to populate your system's ARP cache and then reads it.
3. **Identification**: It checks the first 3 bytes (OUI) of each discovered MAC address against a database of known microcontroller manufacturers.
4. **Resolution**: It resolves hostnames for all discovered IPs in parallel for maximum speed.
