#!/bin/bash

# This script installs the health_bar utility.

# Create the .health_bar directory and log file
mkdir -p /home/constantin/.health_bar
touch /home/constantin/.health_bar/health_log.csv
echo "count,warning,category,level,solution,ignore" > /home/constantin/.health_bar/health_log.csv

# Copy the monitoring script to /usr/local/bin
sudo cp health_monitor.sh /usr/local/bin/health_monitor.sh

# Copy the systemd service file to /etc/systemd/system
sudo cp health_bar.service /etc/systemd/system/health_bar.service

# Reload the systemd daemon
sudo systemctl daemon-reload

# Enable and start the health_bar service
sudo systemctl enable health_bar.service
sudo systemctl restart health_bar.service

echo "Health Bar has been installed and started."
