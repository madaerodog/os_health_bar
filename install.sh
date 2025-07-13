#!/bin/bash

# This script installs the health_bar utility.
# Run with: sudo ./install.sh

# Install required Python dependencies
apt-get update
apt-get install -y python3-gi gir1.2-appindicator3-0.1 gir1.2-gtk-3.0

# Create the .health_bar directory and log file
mkdir -p ~/.health_bar
touch ~/.health_bar/health_log.csv
echo "count,warning,category,level,solution,ignore" > ~/.health_bar/health_log.csv

# Copy the monitoring script to /usr/local/bin
cp health_monitor.sh /usr/local/bin/health_monitor.sh

# Copy the systemd service file to /etc/systemd/system
cp health_bar.service /etc/systemd/system/health_bar.service

# Create directories for user files
mkdir -p ~/.local/share/icons
mkdir -p ~/.local/bin
mkdir -p ~/.config/autostart

# Copy the tray app and icon
cp tray_app.py ~/.local/bin/health_bar_tray.py
chmod +x ~/.local/bin/health_bar_tray.py
cp health_bar_icon.svg ~/.local/share/icons/health_bar_icon.svg

# Create desktop file for autostart
cat > ~/.config/autostart/health-bar-tray.desktop << EOF
[Desktop Entry]
Type=Application
Name=Health Bar Tray
Comment=System health monitoring tray application
Exec=$HOME/.local/bin/health_bar_tray.py
Icon=$HOME/.local/share/icons/health_bar_icon.svg
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

# Reload the systemd daemon
systemctl daemon-reload

# Enable and start the health_bar service
systemctl enable health_bar.service
systemctl restart health_bar.service

echo "Health Bar has been installed and started."
echo "Starting tray application..."

# Start the tray application
~/.local/bin/health_bar_tray.py &

echo "Installation complete. The tray icon should now appear in your system tray."
