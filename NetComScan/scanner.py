import socket
import os
import platform
import subprocess
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.table import Table

# Known MAC OUIs for microcontrollers
MICROCONTROLLER_MAPPING = {
    "B8:27:EB": "Raspberry Pi Foundation",
    "DC:A6:32": "Raspberry Pi Foundation",
    "E4:5F:01": "Raspberry Pi Foundation",
    "DC:44:6D": "Shenzhen Xunlong Software (Orange Pi)",
}

def get_local_ip_and_subnet():
    """Get the local IP address and guess the /24 subnet."""
    try:
        # Create a dummy socket to find the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        # Assume /24 for simplicity in discovery
        subnet_prefix = ".".join(local_ip.split(".")[:-1])
        return local_ip, f"{subnet_prefix}.0/24", subnet_prefix
    except Exception:
        return None, None, None

def ping_ip(ip):
    """Ping an IP to populate the ARP cache."""
    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = ["ping", param, "1", "-w", "500", ip]
    try:
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def populate_arp_cache(subnet_prefix):
    """Ping all IPs in a /24 subnet to populate the ARP cache."""
    ips = [f"{subnet_prefix}.{i}" for i in range(1, 255)]
    with ThreadPoolExecutor(max_workers=50) as executor:
        executor.map(ping_ip, ips)

def get_arp_table():
    """Read the system ARP table and return a list of (IP, MAC)."""
    devices = []
    try:
        # Run arp -a
        output = subprocess.check_output(["arp", "-a"]).decode("ascii", errors="ignore")
        
        # Regex to match IP and MAC
        # Windows format: 172.16.0.1            b4-09-31-3b-66-64     dynamic
        # Linux format: ? (172.16.0.1) at b4:09:31:3b:66:64 [ether] on eth0
        
        lines = output.splitlines()
        for line in lines:
            # Match IPv4 addresses
            ip_match = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", line)
            # Match MAC addresses (hyphen or colon separated)
            mac_match = re.search(r"([0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2})", line)
            
            if ip_match and mac_match:
                ip = ip_match.group(1)
                mac = mac_match.group(1).replace("-", ":").upper()
                devices.append({"ip": ip, "mac": mac})
    except Exception as e:
        print(f"Error reading ARP table: {e}")
        
    return devices

def identify_device(mac):
    """Match the MAC OUI against known microcontroller manufacturers."""
    oui = ":".join(mac.split(":")[:3])
    return MICROCONTROLLER_MAPPING.get(oui, "Unknown Device")

def resolve_hostname(ip):
    """Try to resolve the hostname for an IP address."""
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname
    except Exception:
        return "N/A"

def main():
    console = Console()
    console.print("[bold blue]Network Identification Tool[/bold blue]")
    
    local_ip, subnet, subnet_prefix = get_local_ip_and_subnet()
    if not local_ip:
        console.print("[bold red]Could not determine local network configuration.[/bold red]")
        return
    
    console.print(f"Local IP: [green]{local_ip}[/green]")
    console.print(f"Scanning Subnet: [green]{subnet}[/green]...")
    
    # Try scapy first if available
    try:
        from scapy.all import arping
        console.print("Using [bold cyan]Scapy[/bold cyan] for high-accuracy ARP scanning...")
        # Note: arping returns a list of (packet, answer) pairs
        ans, unans = arping(subnet, verbose=False)
        devices = []
        for snd, rcv in ans:
            devices.append({"ip": rcv.psrc, "mac": rcv.hwsrc.upper()})
    except ImportError:
        console.print("Scapy not found. Using system [bold yellow]ARP fallback[/bold yellow]...")
        console.print("Populating ARP cache (pinging all IPs in subnet)...")
        populate_arp_cache(subnet_prefix)
        devices = get_arp_table()
    except Exception as e:
        console.print(f"[bold red]Scapy failed:[/bold red] {e}. Falling back to system ARP...")
        populate_arp_cache(subnet_prefix)
        devices = get_arp_table()

    # Filter out duplicates and the local IP if needed
    seen_ips = set()
    unique_devices = []
    for d in devices:
        if d["ip"] not in seen_ips:
            unique_devices.append(d)
            seen_ips.add(d["ip"])
    
    # Enrich data
    table = Table(title=f"Discovered Devices in {subnet}")
    table.add_column("IP Address", style="cyan")
    table.add_column("MAC Address", style="magenta")
    table.add_column("Hostname", style="green")
    table.add_column("Identified Device Type", style="bold yellow")
    
    def process_device(device):
        device["hostname"] = resolve_hostname(device["ip"])
        device["type"] = identify_device(device["mac"])
        return device

    with console.status("[bold green]Resolving hostnames and identifying devices...") as status:
        with ThreadPoolExecutor(max_workers=20) as executor:
            enriched_devices = list(executor.map(process_device, unique_devices))
            
    for device in enriched_devices:
        table.add_row(
            device["ip"],
            device["mac"],
            device["hostname"],
            device["type"]
        )
            
    console.print(table)
    console.print(f"\n[bold green]Scan complete. Found {len(enriched_devices)} devices.[/bold green]")

if __name__ == "__main__":
    main()
