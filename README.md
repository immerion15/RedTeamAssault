# Save the script
nano redteam_assault.py
# Paste the code above
# Save: Ctrl+O, Enter
# Exit: Ctrl+X

# Make executable
chmod +x redteam_assault.py

# Install required tools
sudo apt update
sudo apt install nmap metasploit-framework -y

# Start PostgreSQL (required for Metasploit)
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Initialize Metasploit database
sudo msfdb init

sudo python3 redteam_assault.py
