#!/usr/bin/env python3
"""
Prospector - Surgical IT, Enterprise, OT & Government Vendor Goldmine Reconnaissance Tool
Version: 4.17.0
Developed by ADO Security
License: Free to use and reuse

WARNING: This tool is intended for authorized penetration testing and OSINT only. 
Use or modification implies consent to abide by this warning.
"""

import sys
import os
import hashlib
import argparse
import urllib.request
import urllib.error

VERSION = "4.17.0"

# ANSI Escape Codes for Gold/Yellow Styling
GOLD = "\033[93m"
RESET = "\033[0m"

ASCII_BANNER = f"""{GOLD}
██████╗ ██████╗  ██████╗ ███████╗██████╗ ███████╗ ██████╗████████╗ ██████╗ ██████╗ 
██╔══██╗██╔══██╗██╔═══██╗██╔════╝██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗
██████╔╝██████╔╝██║   ██║███████╗██████╔╝█████╗  ██║     v{VERSION} ██║   ██║██████╔╝
██╔═══╝ ██╔══██╗██║   ██║╚════██║██╔═══╝ ██╔══╝  ██║       ██║   ██║   ██║██╔══██╗
██║     ██║  ██║╚██████╔╝███████║██║     ███████╗╚██████╗  ██║   ╚██████╔╝██║  ██║
                                                                                
           [ ADO Security | Surgical Multi-Domain Goldmine Recon v{VERSION} ]
{RESET}"""

# Surgical, vendor-specific IT configuration and sensitive file "goldmines"
IT_GOLDMINES = {
    "ASP.NET / IIS": [
        "/elmah.axd",
        "/web.config",
        "/Trace.axd",
        "/aspnet_client/"
    ],
    "Nginx Web Server": [
        "/nginx_status",
        "/.nginx.conf",
        "/nginx.conf.bak",
        "/conf/nginx.conf"
    ],
    "Application & Environment": [
        "/.env",
        "/storage/logs/laravel.log",
        "/config/database.yml",
        "/settings.py",
        "/phpinfo.php",
        "/server-status"
    ],
    "Version Control & Backups": [
        "/.git/HEAD",
        "/.git/config",
        "/.gitignore",
        "/backup.sql",
        "/db_backup.tar.gz",
        "/wwwroot.zip"
    ]
}

# Enterprise Platforms & Middleware Goldmines (Spring, Salesforce, Workday, GIS)
ENTERPRISE_GOLDMINES = {
    "SpringSource / Spring Boot": [
        "/actuator",
        "/actuator/env",
        "/actuator/heapdump",
        "/actuator/configprops",
        "/actuator/mappings",
        "/actuator/beans"
    ],
    "Salesforce Integration": [
        "/services/data/",
        "/services/apexrest/",
        "/apex/VisualforcePage",
        "/.well-known/salesforce-target"
    ],
    "Workday Integrations": [
        "/ccx/service/customreport/",
        "/ccx/oss/",
        "/ccx/financials/",
        "/ccx/hr/"
    ],
    "GIS (Esri ArcGIS / GeoServer)": [
        "/arcgis/rest/services",
        "/arcgis/rest/admin",
        "/geoserver/web/",
        "/geoserver/ows?service=WFS&request=GetCapabilities"
    ]
}

# Surgical, vendor-specific OT / ICS telemetry and management endpoint "goldmines"
OT_GOLDMINES = {
    "Gilbarco Veeder-Root (ATG)": [
        "/ATG_Status.xml",
        "/tank_status.dat",
        "/fuel_inventory.xml",
        "/cfg.bin",
        "/SerialPort.xml"
    ],
    "Rockwell / Allen-Bradley": [
        "/PlcStatus",
        "/enip",
        "/chal.html",
        "/LogixInfo.htm",
        "/index.cgi?page=status"
    ],
    "Siemens SIMATIC": [
        "/Simatic.OPC.XMLDA",
        "/portal/index.html",
        "/diag/index.html",
        "/Awsweb/",
        "/FormLogin"
    ],
    "Schneider Electric": [
        "/magelis",
        "/citect",
        "/webfactory",
        "/StxWeb"
    ]
}

# Local & State Government Platforms / Vendors Goldmines (including Water, Wastewater, and Electricity)
GOV_GOLDMINES = {
    "Tyler Technologies (Munis / EnerGov / Eagle)": [
        "/munis/portal/",
        "/energov/selfservice/",
        "/eagle/web/",
        "/tyler/client/portal",
        "/CitizenAccess/"
    ],
    "Accela Civic Platform": [
        "/CitizenAccess/",
        "/Accela/Civic/Portal/",
        "/ePermitHub/",
        "/OpenCounter/"
    ],
    "Granicus / CivicPlus": [
        "/civiccms/",
        "/agenda/api/",
        "/sire/pub/",
        "/public/agendas/"
    ],
    "Municipal Water & Wastewater (Cityworks / Infor IPS)": [
        "/cityworks/",
        "/client/cityworks/",
        "/ips/",
        "/hansen/",
        "/waterportal/"
    ],
    "Municipal & Public Power / Electricity (NISC SmartHub / AMI)": [
        "/smarthub/",
        "/nisc/",
        "/mdm/",
        "/ami/",
        "/meterportal/"
    ]
}

# Legacy, Debug, Installer, and Diagnostic Files Catalog
LEGACY_GOLDMINES = {
    "Legacy, Debug & Diagnostic Files": [
        "/test.php",
        "/test2.php",
        "/info.php",
        "/phpinfo.php",
        "/i.php",
        "/version.php",
        "/check.php",
        "/env.php",
        "/db.php",
        "/database.php",
        "/db_test.php",
        "/conn.php",
        "/connect.php",
        "/upload.php",
        "/uploader.php",
        "/file-upload.php",
        "/index.php.bak",
        "/test.php.old",
        "/index.php~",
        "/backup.php",
        "/config.php.bak",
        "/install.php",
        "/setup.php",
        "/update.php",
        "/upgrade.php",
        "/install.aspx",
        "/setup.jsp",
        "/health.php",
        "/status.php",
        "/diagnostic.php",
        "/debug.php",
        "/test.aspx",
        "/test.jsp",
        "/test.asp",
        "/error.log",
        "/debug.log",
        "/php_errors.log",
        "/access.log",
        "/trace.txt",
        "/readme.txt",
        "/changelog.txt",
        "/version.txt",
        "/license.txt",
        "/readme.html"
    ]
}

# Web Server & CMS Fingerprints Catalog (WordPress, Drupal, Tomcat, Apache, Robots, and JWKS)
WEB_GOLDMINES = {
    "Robots & Crawling": [
        "/robots.txt",
        "/sitemap.xml",
        "/.well-known/security.txt",
        "/.well-known/jwks.json",
        "/.well-known/jwk.json",
        "/jwks.json"
    ],
    "WordPress Fingerprints & Sensitive Files": [
        "/wp-login.php",
        "/xmlrpc.php",
        "/wp-config.php.bak",
        "/wp-content/debug.log",
        "/wp-json/wp/v2/users"
    ],
    "Drupal Core Fingerprints & Files": [
        "/CHANGELOG.txt",
        "/INSTALL.txt",
        "/update.php?op=info",
        "/sites/default/settings.php",
        "/core/INSTALL.txt"
    ],
    "Apache Tomcat Default Apps & Manager": [
        "/manager/html",
        "/host-manager/html",
        "/docs/",
        "/examples/",
        "/manager/status"
    ],
    "Apache HTTP Server Status & Info": [
        "/server-status",
        "/server-info"
    ]
}

def calculate_checksum(file_path):
    """Calculates the SHA-256 checksum of the current script file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def scan_vendor_category(target_url, category_name, endpoints):
    print(f"\n[*] Probing category: [{category_name}]")
    for endpoint in endpoints:
        url = target_url.rstrip("/") + endpoint
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": f"ADO-Prospector-Recon/{VERSION}"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                print(f"  [GOLDMINE FOUND] [{response.status}] {url}")
        except urllib.error.HTTPError as e:
            if e.code in [401, 403]:
                print(f"  [PROTECTED/EXISTS] [{e.code}] {url}")
        except Exception:
            pass

def print_help_menu():
    """Prints the comprehensive help menu detailing available options and flags."""
    help_text = f"""
Prospector Reconnaissance Tool (v{VERSION}) - ADO Security
==================================================
LICENSE: Free to use and reuse.
WARNING: Intended for authorized penetration testing and OSINT only. 
Use or modification implies consent to abide by this warning.

SYNTAX:
  python prospector.py -u <target_url> [options]

OPTIONS:
  -u, --url         Target base URL (e.g., http://target.local) (Required)
  --it              Scan surgical IT application, Nginx & config goldmine files only
  --enterprise      Scan enterprise platforms (Spring, Salesforce, Workday, GIS) only
  --ot              Scan OT vendor telemetry and interface goldmines only
  --gov             Scan state/local government vendors, water, wastewater & electricity only
  --legacy          Scan legacy, debug, installer, diagnostic & log files only
  --web             Scan web server fingerprints, CMS, Tomcat, robots.txt, and JWKS endpoints only
  -a, --all         Scan all IT, Enterprise, OT, Government, Legacy, and Web catalogs
  --help            Show this help menu and exit

CONCRETE EXAMPLES:
  1. Basic Run (Scan default IT & Nginx endpoints):
     python prospector.py -u http://target.local --it

  2. Standard Run (Scan legacy diagnostic, installers, and log files):
     python prospector.py -u http://target.local --legacy

  3. Web Run (Scan WordPress, Drupal, Tomcat, robots.txt, and JWKS):
     python prospector.py -u http://target.local --web

  4. Advanced Run (Scan all available catalogs):
     python prospector.py -u http://target.local --all
"""
    print(help_text.strip())

def main():
    print(ASCII_BANNER)
    
    parser = argparse.ArgumentParser(description="Prospector Surgical IT, OT, Enterprise & Government Goldmine Tool by ADO Security", add_help=False)
    parser.add_argument("-u", "--url", help="Target base URL (e.g., http://target.local)")
    parser.add_argument("--it", action="store_true", help="Scan surgical IT application, Nginx & config goldmine files")
    parser.add_argument("--enterprise", action="store_true", help="Scan enterprise platforms (Spring, Salesforce, Workday, GIS)")
    parser.add_argument("--ot", action="store_true", help="Scan surgical OT vendor telemetry and interface goldmines")
    parser.add_argument("--gov", "--government", action="store_true", help="Scan government platforms and water/power utilities")
    parser.add_argument("--legacy", action="store_true", help="Scan legacy, debug, installer, diagnostic & log files")
    parser.add_argument("--web", action="store_true", help="Scan web server fingerprints, CMS, Tomcat, robots.txt, and JWKS")
    parser.add_argument("-a", "--all", action="store_true", help="Scan all IT, Enterprise, OT, Government, Legacy, and Web catalogs")
    parser.add_argument("--help", action="store_true", help="Show help menu")
    
    args = parser.parse_args()
    
    if args.help or not args.url:
        print_help_menu()
        if not args.url and not args.help:
            print("\n[-] Error: Target URL (-u / --url) is required.")
            sys.exit(1)
        return

    active_scopes = []
    if args.it:
        active_scopes.append(("IT", IT_GOLDMINES))
    if args.enterprise:
        active_scopes.append(("ENTERPRISE PLATFORMS", ENTERPRISE_GOLDMINES))
    if args.ot:
        active_scopes.append(("OT", OT_GOLDMINES))
    if args.gov:
        active_scopes.append(("GOVERNMENT & UTILITIES", GOV_GOLDMINES))
    if args.legacy:
        active_scopes.append(("LEGACY & DIAGNOSTIC FILES", LEGACY_GOLDMINES))
    if args.web:
        active_scopes.append(("WEB & CMS FINGERPRINTS", WEB_GOLDMINES))
        
    if args.all:
        active_scopes = [
            ("IT", IT_GOLDMINES),
            ("ENTERPRISE PLATFORMS", ENTERPRISE_GOLDMINES),
            ("OT", OT_GOLDMINES),
            ("GOVERNMENT & UTILITIES", GOV_GOLDMINES),
            ("LEGACY & DIAGNOSTIC FILES", LEGACY_GOLDMINES),
            ("WEB & CMS FINGERPRINTS", WEB_GOLDMINES)
        ]

    if not active_scopes:
        active_scopes.append(("IT", IT_GOLDMINES))
        print("[*] No specific scope flags provided. Defaulting to surgical IT goldmines.")

    for scope_type, categories in active_scopes:
        print(f"\n=== STARTING {scope_type} SURGICAL RECONNAISSANCE ===")
        for vendor, endpoints in categories.items():
            scan_vendor_category(args.url, vendor, endpoints)

    # Script checksum validation footer required at the end of every release
    script_path = os.path.abspath(__file__)
    checksum = calculate_checksum(script_path)
    print("\n" + "-" * 50)
    print(f"Tool Vendor: ADO Security (Free to use/reuse)")
    print(f"Script Version: {VERSION}")
    print(f"Script Checksum (SHA-256): {checksum}")
    print("-" * 50)

if __name__ == "__main__":
    main()
