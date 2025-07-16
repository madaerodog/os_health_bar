#!/bin/bash

# This script installs/uninstalls the health_bar utility.
# Run with: sudo ./install.sh
# Run with: sudo ./install.sh -remove (to uninstall)

# Check for uninstall option
if [ "$1" = "-remove" ]; then
    echo "Uninstalling Health Bar..."
    
    # Get the actual user (not root when using sudo)
    ACTUAL_USER=${SUDO_USER:-$USER}
    ACTUAL_HOME=$(eval echo ~$ACTUAL_USER)
    
    # Stop and disable the systemd service
    echo "Stopping and disabling health_bar service..."
    systemctl stop health_bar.service 2>/dev/null || true
    systemctl disable health_bar.service 2>/dev/null || true
    
    # Stop any running tray applications
    echo "Stopping tray applications..."
    pkill -f "health_bar_tray.py" 2>/dev/null || true
    
    # Remove systemd service file
    echo "Removing systemd service file..."
    rm -f /etc/systemd/system/health_bar.service
    
    # Remove system-wide monitoring script
    echo "Removing monitoring script..."
    rm -f /usr/local/bin/health_monitor.sh
    
    # Remove user files
    echo "Removing user files..."
    rm -f "$ACTUAL_HOME/.local/bin/health_bar_tray.py"
    rm -f "$ACTUAL_HOME/.health_bar/web_server.py"
    rm -f "$ACTUAL_HOME/.health_bar/index.html"
    rm -f "$ACTUAL_HOME/.health_bar/log_processor.py"
    rm -f "$ACTUAL_HOME/.local/share/icons/health_bar_icon.svg"
    rm -f "$ACTUAL_HOME/.local/share/icons/icon_full_health.png"
    rm -f "$ACTUAL_HOME/.local/share/icons/icon_damage.png"
    rm -f "$ACTUAL_HOME/.config/autostart/health-bar-tray.desktop"
    
    # Ask before removing user data directory
    if [ -d "$ACTUAL_HOME/.health_bar" ]; then
        echo "Found user data directory: $ACTUAL_HOME/.health_bar"
        echo "This contains your health logs. Do you want to remove it? (y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            rm -rf "$ACTUAL_HOME/.health_bar"
            echo "Removed user data directory"
        else
            echo "Keeping user data directory"
        fi
    fi
    
    # Clean up empty directories
    rmdir "$ACTUAL_HOME/.local/bin" 2>/dev/null || true
    rmdir "$ACTUAL_HOME/.local/share/icons" 2>/dev/null || true
    rmdir "$ACTUAL_HOME/.config/autostart" 2>/dev/null || true
    
    # Reload systemd daemon
    systemctl daemon-reload
    
    echo "Health Bar has been uninstalled successfully."
    echo "Note: System packages (python3-gi, etc.) were not removed."
    exit 0
fi

# Get the actual user (not root when using sudo)
ACTUAL_USER=${SUDO_USER:-$USER}
ACTUAL_HOME=$(eval echo ~$ACTUAL_USER)

# Install required Python dependencies and SVG conversion tool
apt-get update
apt-get install -y python3-gi gir1.2-appindicator3-0.1 gir1.2-gtk-3.0 librsvg2-bin imagemagick

# Stop any running tray applications first
echo "Stopping any running tray applications..."
pkill -f "health_bar_tray.py" 2>/dev/null || true
sleep 2

# Create the .health_bar directory and log file in the actual user's home
rm -rf "$ACTUAL_HOME/.health_bar"
mkdir -p "$ACTUAL_HOME/.health_bar"
touch "$ACTUAL_HOME/.health_bar/health_log.csv"
echo "count,warning,category,level,solution,ignore" > "$ACTUAL_HOME/.health_bar/health_log.csv"
chown -R $ACTUAL_USER:$ACTUAL_USER "$ACTUAL_HOME/.health_bar"

# Copy the monitoring script to /usr/local/bin
cp health_monitor.sh /usr/local/bin/health_monitor.sh
chmod +x /usr/local/bin/health_monitor.sh

# Copy the systemd service file to /etc/systemd/system
cp health_bar.service /etc/systemd/system/health_bar.service

# Create directories for user files in the actual user's home
mkdir -p "$ACTUAL_HOME/.local/share/icons"
mkdir -p "$ACTUAL_HOME/.local/bin"
mkdir -p "$ACTUAL_HOME/.config/autostart"

# Remove old files first to ensure clean replacement
rm -f "$ACTUAL_HOME/.local/bin/health_bar_tray.py"
rm -f "$ACTUAL_HOME/.health_bar/web_server.py"
rm -f "$ACTUAL_HOME/.health_bar/index.html"
rm -f "$ACTUAL_HOME/.health_bar/log_processor.py"
rm -f "$ACTUAL_HOME/.local/share/icons/health_bar_icon.svg"
rm -f "$ACTUAL_HOME/.local/share/icons/icon_full_health.png"
rm -f "$ACTUAL_HOME/.local/share/icons/icon_damage.png"

# Copy the tray app and icon to the actual user's home
cp tray_app.py "$ACTUAL_HOME/.local/bin/health_bar_tray.py"
chmod +x "$ACTUAL_HOME/.local/bin/health_bar_tray.py"
cp web_server.py "$ACTUAL_HOME/.health_bar/web_server.py"
chmod +x "$ACTUAL_HOME/.health_bar/web_server.py"
cp index.html "$ACTUAL_HOME/.health_bar/index.html"
cp log_processor.py "$ACTUAL_HOME/.health_bar/log_processor.py"
chmod +x "$ACTUAL_HOME/.health_bar/log_processor.py"
cp health_bar_icon.svg "$ACTUAL_HOME/.local/share/icons/health_bar_icon.svg"
cp icon_full_health.png "$ACTUAL_HOME/.local/share/icons/icon_full_health.png"
cp icon_damage.png "$ACTUAL_HOME/.local/share/icons/icon_damage.png"

# Set proper ownership
chown $ACTUAL_USER:$ACTUAL_USER "$ACTUAL_HOME/.local/share/icons/health_bar_icon.svg"
chown $ACTUAL_USER:$ACTUAL_USER "$ACTUAL_HOME/.local/share/icons/icon_full_health.png"
chown $ACTUAL_USER:$ACTUAL_USER "$ACTUAL_HOME/.local/share/icons/icon_damage.png"
chown $ACTUAL_USER:$ACTUAL_USER "$ACTUAL_HOME/.local/bin/health_bar_tray.py"
chown $ACTUAL_USER:$ACTUAL_USER "$ACTUAL_HOME/.health_bar/web_server.py"
chown $ACTUAL_USER:$ACTUAL_USER "$ACTUAL_HOME/.health_bar/index.html"
chown $ACTUAL_USER:$ACTUAL_USER "$ACTUAL_HOME/.health_bar/log_processor.py"

# Clean up any temporary icon files that might be cached
rm -f /tmp/tmp*.svg /tmp/tmp*.png 2>/dev/null || true

# Create desktop file for autostart in the actual user's home
cat > "$ACTUAL_HOME/.config/autostart/health-bar-tray.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Health Bar Tray
Comment=System health monitoring tray application
Exec=$ACTUAL_HOME/.local/bin/health_bar_tray.py
Icon=$ACTUAL_HOME/.local/share/icons/health_bar_icon.svg
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

# Set proper ownership for the desktop file
chown $ACTUAL_USER:$ACTUAL_USER "$ACTUAL_HOME/.config/autostart/health-bar-tray.desktop"

# Reload the systemd daemon
systemctl daemon-reload

# Enable and start the health_bar service
systemctl enable health_bar.service
systemctl restart health_bar.service

echo "Health Bar has been installed and started."
echo "Starting tray application for the current session..."

# Start the tray application as the actual user with the correct environment
sudo -u $ACTUAL_USER DISPLAY=:0 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u $ACTUAL_USER)/bus "$ACTUAL_HOME/.local/bin/health_bar_tray.py" &

echo "Installation complete. The tray icon should now appear in your system tray."
echo "If the icon does not appear, please log out and log back in."
