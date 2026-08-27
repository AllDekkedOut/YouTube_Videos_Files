#!/usr/bin/env python3
"""
Tool Name: ADO Open Ports & Services Extractor
Description: Connects to the Metasploit PostgreSQL database to extract, sort,
             and format discovered hosts, open ports, and running services
             into a modern table with varied background row shading.
Version: 2.0.0

Requirements:
    pip3 install psycopg2-binary pyyaml

Basic Run:
    python3 msf_port_extractor.py
"""

import sys
import yaml

try:
    import psycopg2
except ImportError:
    print("[-] Error: Missing required module 'psycopg2'.")
    print("[*] Install it inside your venv via: pip3 install psycopg2-binary")
    sys.exit(1)

# Modern ANSI Escape Codes (TrueColor 24-bit background shading & varied text colors)
HEADER_BG = "\033[48;2;30;41;59m\033[1;38;5;255m"   # Slate dark background with bright white text
ROW_BG_1  = "\033[48;2;15;23;42m"                  # Deep midnight blue-gray background for even rows
ROW_BG_2  = "\033[48;2;30;41;59m"                  # Slate background for odd rows
TEXT_COLOR = "\033[38;5;253m"                      # Soft light gray text for rows
ACCENT_COLOR = "\033[1;38;5;39m"                   # Vivid Blue accent for headers/footers
RESET = "\033[0m"

# Load database credentials automatically from Metasploit's generated config
CONFIG_PATH = "/usr/share/metasploit-framework/config/database.yml"

def load_msf_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f)
        prod_cfg = config.get("production", config)
        return {
            "dbname": prod_cfg.get("database", "msf"),
            "user": prod_cfg.get("username", "msf"),
            "password": str(prod_cfg.get("password", "")),
            "host": prod_cfg.get("host", "127.0.0.1"),
            "port": str(prod_cfg.get("port", "5432"))
        }
    except Exception as e:
        print(f"[-] Could not read Metasploit config at {CONFIG_PATH}: {e}")
        print("[*] Falling back to default connection parameters.")
        return {
            "dbname": "msf",
            "user": "msf",
            "password": "msf",
            "host": "127.0.0.1",
            "port": "5432"
        }

def fetch_services(db_config):
    print(f"{ACCENT_COLOR}[*] Connecting to database ({db_config['dbname']}@{db_config['host']})...{RESET}")
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Query sorting explicitly by IP address and then numeric port ascending
        query = """
            SELECT 
                h.address AS host_ip,
                COALESCE(h.name, 'N/A') AS hostname,
                s.port,
                s.proto,
                COALESCE(s.name, 'unknown') AS service_name,
                COALESCE(s.info, '') AS service_info
            FROM services s
            JOIN hosts h ON s.host_id = h.id
            WHERE s.state = 'open'
            ORDER BY INET(h.address) ASC, s.port ASC;
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return rows

    except Exception as e:
        print(f"{ACCENT_COLOR}[-] Database connection or query failed: {e}{RESET}")
        sys.exit(1)

def display_results(rows):
    if not rows:
        print(f"{ACCENT_COLOR}\n[-] No open services found in the database.{RESET}")
        return

    print(f"\n{ACCENT_COLOR}")
    print("=====================================================================================================")
    print(" [+] DISCOVERED OPEN PORTS & SERVICES")
    print("=====================================================================================================")
    print(f"{RESET}")

    HOST_W = 18
    PORT_W = 8
    PROTO_W = 6
    SERV_W = 15
    INFO_W = 38

    LINE_FMT = "%-" + str(HOST_W) + "s | %-" + str(PORT_W) + "s | %-" + str(PROTO_W) + "s | %-" + str(SERV_W) + "s | %-" + str(INFO_W) + "s"
    
    header_line = LINE_FMT % ("Host IP", "Port", "Proto", "Service", "Info / Banner")
    separator_line = "-----------------------------------------------------------------------------------------------------"

    print(f"{HEADER_BG} {header_line} {RESET}")
    print(f"{ACCENT_COLOR}{separator_line}{RESET}")

    # Render rows with varied background shading
    for idx, (host_ip, hostname, port, proto, service_name, service_info) in enumerate(rows):
        row_content = LINE_FMT % (host_ip, str(port), proto, service_name, service_info[:INFO_W])
        
        if idx % 2 == 0:
            bg_style = ROW_BG_1
        else:
            bg_style = row_bg = ROW_BG_2
            
        print(f"{bg_style}{TEXT_COLOR} {row_content} {RESET}")

    print(f"{ACCENT_COLOR}")
    print("=====================================================================================================")
    print(f"[+] Total Open Ports/Services Extracted: {len(rows)}")
    print("=====================================================================================================")
    print(f"{RESET}")

if __name__ == "__main__":
    db_config = load_msf_config()
    results = fetch_services(db_config)
    display_results(results)

