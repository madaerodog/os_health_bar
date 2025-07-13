#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, AppIndicator3
import os
import signal
import subprocess

APPINDICATOR_ID = 'health-bar-app'

def main():
    # Define the path to the icon and log file
    icon_path = os.path.expanduser('~/.local/share/icons/health_bar_icon.svg')
    log_file_path = os.path.expanduser('~/.health_bar/health_log.csv')
    
    # Check if icon exists, fallback to a standard icon if not
    if not os.path.exists(icon_path):
        print(f"Warning: Icon not found at {icon_path}, using fallback")
        icon_path = "application-default-icon"  # Standard fallback
    
    # Check if log file exists
    if not os.path.exists(log_file_path):
        print(f"Warning: Log file not found at {log_file_path}")
        # Create the directory and file if they don't exist
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        with open(log_file_path, 'w') as f:
            f.write("count,warning,category,level,solution,ignore\n")

    # Create the indicator
    indicator = AppIndicator3.Indicator.new(APPINDICATOR_ID, icon_path, AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
    indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
    indicator.set_menu(build_menu(log_file_path))

    print(f"Health Bar tray application started with icon: {icon_path}")
    
    # Start the GTK main loop
    Gtk.main()

def get_error_count(log_file_path):
    """Count the number of error lines in the log file (excluding header)"""
    try:
        if not os.path.exists(log_file_path):
            return 0
        
        with open(log_file_path, 'r') as f:
            lines = f.readlines()
        
        # Skip header line and count non-empty lines
        error_lines = [line.strip() for line in lines[1:] if line.strip()]
        return len(error_lines)
    except Exception:
        return 0

def build_menu(log_file_path):
    menu = Gtk.Menu()

    # Menu Item: View Logs with error count
    error_count = get_error_count(log_file_path)
    item_view_logs = Gtk.MenuItem(label=f'View Logs ({error_count})')
    item_view_logs.connect('activate', lambda a: view_logs(log_file_path))
    menu.append(item_view_logs)

    # Menu Item: Restart Service
    item_restart = Gtk.MenuItem(label='Restart Monitoring Service')
    item_restart.connect('activate', restart_service)
    menu.append(item_restart)

    # Separator
    menu.append(Gtk.SeparatorMenuItem())

    # Menu Item: Quit
    item_quit = Gtk.MenuItem(label='Quit')
    item_quit.connect('activate', quit_app)
    menu.append(item_quit)

    menu.show_all()
    return menu

def view_logs(log_file_path):
    # Open the log file with gedit specifically
    try:
        subprocess.run(['gedit', log_file_path], check=True)
    except FileNotFoundError:
        # Fallback to other text editors if gedit is not available
        try:
            subprocess.run(['xdg-open', log_file_path], check=True)
        except Exception as e:
            print(f"Error opening log file: {e}")
    except Exception as e:
        print(f"Error opening log file with gedit: {e}")

def restart_service(_):
    # Restart the systemd service
    try:
        subprocess.run(['systemctl', '--user', 'restart', 'health_bar.service'], check=True)
    except Exception as e:
        # Fallback for system-wide service
        try:
            subprocess.run(['sudo', 'systemctl', 'restart', 'health_bar.service'], check=True)
        except Exception as e_sudo:
            print(f"Error restarting service: {e_sudo}")


def quit_app(_):
    Gtk.main_quit()

if __name__ == "__main__":
    # Gracefully handle Ctrl+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
