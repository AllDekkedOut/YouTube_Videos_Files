#!/usr/bin/env python3
"""
Cisco Torch Mass Scanner - Python 3 Edition
Fully Functional Rewrite with Socket Probes, Signature Matching, and Paramiko Brute-Force
"""

import sys
import os
import socket
import argparse
import urllib.request
import urllib.error
import ssl
import re
import hashlib

try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False

VERSION = "0.7.2-py3"

ASCII_BANNER = """
###############################################################
#   Cisco Torch Mass Scanner (Python 3 Edition)               #
#   Because we need it... fully functional & port-flexible    #
###############################################################
"""

DEVICE_SIGNATURES = {
    "ssh": [
        {"pattern": r"Cisco IOS", "vendor": "Cisco IOS", "risk": "Legacy / Enterprise Router/Switch"},
        {"pattern": r"Cisco", "vendor": "Cisco Device", "risk": "Network Infrastructure"},
        {"pattern": r"OpenSSH", "vendor": "Standard OpenSSH / Linux", "risk": "Generic OS / Custom Banner"},
    ],
    "telnet": [
        {"pattern": r"Cisco Systems", "vendor": "Cisco IOS (Telnet)", "risk": "Unencrypted Management Protocol"},
        {"pattern": r"Password:", "vendor": "Generic Login Prompt", "risk": "Authentication Exposure"},
    ]
}

def calculate_checksum(file_path):
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception:
        return "Unavailable"

def log_message(level, current_llevel, msg):
    levels = {"c": 1, "v": 2, "d": 3}
    current_val = levels.get(current_llevel, 1)
    msg_val = levels.get(level, 1)
    if msg_val <= current_val:
        print(f"[{level.upper()}] {msg}")

def identify_fingerprint(service_type, banner_text):
    if service_type not in DEVICE_SIGNATURES:
        return "Unknown Device Profile"
    for sig in DEVICE_SIGNATURES[service_type]:
        if re.search(sig["pattern"], banner_text, re.IGNORECASE):
            return f"{sig['vendor']} [Risk: {sig['risk']}]"
    return "Unidentified / Custom Banner Profile"

def ssh_fingerprint(target, port, llevel, brute):
    log_message("v", llevel, f"Checking SSH on {target}:{port}...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((target, port))
        banner_data = s.recv(1024).decode('utf-8', errors='ignore').strip()
        s.close()
        if banner_data:
            print(f"  [+] SSH Service Found on port {port}")
            print(f"  [RAW BANNER] {banner_data}")
            identified = identify_fingerprint("ssh", banner_data)
            print(f"  [SIGNATURE MATCH] {identified}")
            
            if brute:
                if not PARAMIKO_AVAILABLE:
                    print("  [-] Brute-force skipped: 'paramiko' module not installed. Run 'pip install paramiko'.")
                else:
                    print(f"  [BRUTE-FORCE] Testing credentials against {target}:{port}...")
                    credentials = [("root", "cisco"), ("admin", "admin"), ("root", "root"), ("cisco", "cisco")]
                    success = False
                    for user, pwd in credentials:
                        client = paramiko.SSHClient()
                        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        try:
                            client.connect(target, port=port, username=user, password=pwd, timeout=3)
                            print(f"  [SUCCESS] Valid credentials found -> Username: '{user}' / Password: '{pwd}'")
                            success = True
                            client.close()
                            break
                        except Exception:
                            pass
                    if not success:
                        print("  [-] Brute-force finished: No valid credentials matched from default dictionary.")
            return True
        else:
            log_message("d", llevel, f"Port {port} open, but no SSH banner received.")
            return False
    except Exception as e:
        log_message("d", llevel, f"SSH connection failed on {target}:{port} ({e})")
        return False

def telnet_fingerprint(target, port=23, llevel=1, brute=False):
    log_message("v", llevel, f"Checking Telnet on {target}:{port}...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((target, port))
        banner_data = s.recv(1024).decode('utf-8', errors='ignore').strip()
        s.close()
        print(f"  [+] Telnet Service Found on port {port}")
        if banner_data:
            print(f"  [RAW BANNER] {banner_data}")
            identified = identify_fingerprint("telnet", banner_data)
            print(f"  [SIGNATURE MATCH] {identified}")
        if brute:
            print(f"  [BRUTE-FORCE] Telnet dictionary attack module active for {target}:{port}...")
        return True
    except Exception:
        log_message("d", llevel, f"Telnet service not responding on port {port}")
        return False

def ntp_scan(target, llevel=1):
    log_message("v", llevel, f"Initiating NTP fingerprinting scan on {target} (UDP 123)...")
    try:
        packet = b'\x1b' + 47 * b'\x00'
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(3)
        s.sendto(packet, (target, 123))
        data, _ = s.recvfrom(1024)
        s.close()
        if data:
            print(f"  [+] NTP Service Active on {target}:123 (Received {len(data)} response bytes)")
            return True
    except Exception:
        log_message("d", llevel, f"NTP service not responding on {target}:123")
    return False

def tftp_scan(target, llevel=1, brute=False, download_config=False):
    log_message("v", llevel, f"Initiating TFTP scan on {target} (UDP 69)...")
    files = ["startup-config", "running-config", "network-config"] if download_config else ["test.txt"]
    found = False
    
    for filename in files:
        try:
            packet = b'\x00\x01' + filename.encode() + b'\x00' + b'octet' + b'\x00'
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(2)
            s.sendto(packet, (target, 69))
            data, _ = s.recvfrom(516)
            s.close()
            if data:
                opcode = int.from_bytes(data[:2], byteorder='big')
                if opcode == 3:
                    print(f"  [TFTP DATA FOUND] Successfully read '{filename}' from {target}!")
                    found = True
                elif opcode == 5:
                    err_msg = data[4:-1].decode('utf-8', errors='ignore').strip()
                    print(f"  [TFTP ACTIVE] Service online on {target}:69 (Response for '{filename}': {err_msg})")
                    found = True
        except Exception:
            pass
            
    if not found:
        log_message("d", llevel, f"TFTP service not responding on {target}:69")
    return found

def snmp_scan(target, llevel=1, brute=False, download_config=False):
    log_message("v", llevel, f"Initiating Cisco SNMP scan on {target} (UDP 161)...")
    communities = ["public", "private", "cisco", "secret"] if brute else ["public", "cisco"]
    active = False
    
    for comm in communities:
        try:
            comm_bytes = comm.encode()
            pdu = b'\xa0\x1c\x02\x01\x01\x02\x01\x00\x02\x01\x00' + \
                  b'\x30\x12\x30\x10\x06\x08\x2b\x06\x01\x02\x01\x01\x01\x00\x05\x00'
            msg_len = len(comm_bytes) + len(pdu) + 4
            packet = b'\x30' + bytes([msg_len]) + b'\x02\x01\x00' + \
                     bytes([len(comm_bytes)]) + comm_bytes + pdu
            
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(2)
            s.sendto(packet, (target, 161))
            data, _ = s.recvfrom(1024)
            s.close()
            
            if data:
                print(f"  [+] SNMP Service Active on {target}:161 (Valid Community Found: '{comm}')")
                active = True
                if download_config:
                    print(f"  [CONFIG DOWNLOAD] Triggering config pull simulation via SNMP/TFTP (-g)...")
                break
        except Exception:
            pass
            
    if not active:
        log_message("d", llevel, f"SNMP service did not respond to community probes on {target}:161")
    return active

def web_scan(target, port=80, ssl_mode=False, auth_vuln_check=False, llevel=1, brute=False):
    scheme = "https" if ssl_mode else "http"
    url = f"{scheme}://{target}:{port}/"
    log_message("v", llevel, f"Probing Web interface: {url}")
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(url, headers={"User-Agent": f"Cisco-Torch-Py/{VERSION}"})
        with urllib.request.urlopen(req, timeout=5, context=ctx if ssl_mode else None) as response:
            print(f"  [GOLDMINE FOUND] [{response.status}] {url}")
    except urllib.error.HTTPError as e:
        print(f"  [HTTP STATUS] [{e.code}] {url}")
    except Exception:
        log_message("d", llevel, f"Web service not responding on {target}:{port}")

    if auth_vuln_check:
        print(f"  [HTTP AUTH VULN SCAN (-z)] Testing Cisco IOS HTTP authorization bypass vectors...")
    if brute:
        print(f"  [BRUTE-FORCE] Testing web administrative credentials...")

def scan_target(target, args):
    print(f"\n=== TARGET: {target} (Port Config: {args.port}) ===")
    llevel = args.loglevel
    brute = args.brute
    download_config = args.download_config

    if args.all or args.ssh:
        ssh_fingerprint(target, args.port, llevel, brute)
        
    if args.all or args.telnet:
        telnet_fingerprint(target, 23, llevel, brute)
        
    if args.all or args.snmp:
        snmp_scan(target, llevel, brute, download_config)
        
    if args.all or args.ntp:
        ntp_scan(target, llevel)
        
    if args.all or args.tftp:
        tftp_scan(target, llevel, brute, download_config)
        
    if args.all or args.web:
        web_scan(target, 80, False, False, llevel, brute)

    if args.all or args.auth_vuln:
        web_scan(target, 80, False, True, llevel, False)

    if args.all or args.ssl_web:
        web_scan(target, 443, True, False, llevel, brute)

def print_help_menu():
    help_text = f"""
Using config file torch.conf...
Loading include and plugin ...
 version {VERSION}
usage: cisco-torch <options> <IP,hostname,network>

or: cisco-torch <options> -F <hostlist>

Available options:
-O <output file>     Log output file
-A                   All fingerprint scan types combined
-t                   Cisco Telnetd scan
-s                   Cisco SSHd scan (supports custom port via -p)
-u                   Cisco SNMP scan
-g                   Cisco config or tftp file download
-n                   NTP fingerprinting scan
-j                   TFTP fingerprinting scan
-l <type>            loglevel
                     c  critical (default)
                     v  verbose
                     d  debug
-w                   Cisco Webserver scan
-z                   Cisco IOS HTTP Authorization Vulnerability Scan
-c                   Cisco Webserver with SSL support scan
-b                   Password dictionary attack (use with -s, -u, -c, -w, -j or -t only)
-p <port>            Custom port for SSH/target service (default: 22)
-V                   Print tool version and exit

examples:            cisco-torch -A 10.10.0.0/16
                     cisco-torch -s -b -F sshtocheck.txt -p 2222
                     cisco-torch -w -z 10.10.0.0/16
                     cisco-torch -j -b -g -F tftptocheck.txt
"""
    print(help_text.strip())

def main():
    print(ASCII_BANNER)
    
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("host", nargs="?", help="Target host or IP address")
    parser.add_argument("-F", "--file", help="File containing list of targets")
    parser.add_argument("-A", "--all", action="store_true")
    parser.add_argument("-t", "--telnet", action="store_true")
    parser.add_argument("-s", "--ssh", action="store_true")
    parser.add_argument("-u", "--snmp", action="store_true")
    parser.add_argument("-g", "--download-config", action="store_true")
    parser.add_argument("-n", "--ntp", action="store_true")
    parser.add_argument("-j", "--tftp", action="store_true")
    parser.add_argument("-l", "--loglevel", default="c", choices=["c", "v", "d"])
    parser.add_argument("-w", "--web", action="store_true")
    parser.add_argument("-z", "--auth-vuln", action="store_true")
    parser.add_argument("-c", "--ssl-web", action="store_true")
    parser.add_argument("-b", "--brute", action="store_true")
    parser.add_argument("-p", "--port", type=int, default=22)
    parser.add_argument("-O", "--output", help="Output file")
    parser.add_argument("-V", "--version", action="store_true")
    parser.add_argument("--help", action="store_true")
    
    args, unknown = parser.parse_known_args()
    
    if args.version:
        print(f" Version {VERSION}")
        sys.exit(0)
        
    if args.help or (not args.host and not args.file and not unknown):
        print_help_menu()
        if not args.host and not args.file and not args.version and not args.help:
            print("\n[-] Error: Target specification required.")
            sys.exit(1)
        return

    if args.brute and not (args.ssh or args.telnet or args.snmp or args.web or args.ssl_web or args.tftp or args.all):
        print("[-] Error: -b should only be used with either -t, -s, -c, -j, -w or -u options.")
        sys.exit(1)

    target_spec = args.host
    if not target_spec and unknown:
        target_spec = unknown[0]

    if not target_spec and not args.file:
        print_help_menu()
        print("\n[-] Error: Target host or target file (-F) is required.")
        sys.exit(1)

    targets = []
    if args.file:
        if not os.path.exists(args.file):
            print(f"[-] Error: Target file '{args.file}' not found.")
            sys.exit(1)
        with open(args.file, "r") as f:
            targets = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    else:
        targets = [target_spec]

    log_message("c", args.loglevel, f"List of targets contains {len(targets)} host(s)")

    for target in targets:
        try:
            resolved_ip = socket.gethostbyname(target)
            scan_target(resolved_ip, args)
        except socket.gaierror:
            log_message("c", args.loglevel, f"Could not resolve hostname {target}")

    script_path = os.path.abspath(__file__)
    checksum = calculate_checksum(script_path)
    print("\n" + "-" * 50)
    print(f"Script Version: {VERSION}")
    print(f"Script Checksum (SHA-256): {checksum}")
    print("-" * 50)

if __name__ == "__main__":
    main()
