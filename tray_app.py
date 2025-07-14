#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, AppIndicator3, GLib
import os
import signal
import subprocess
import csv
import tempfile

APPINDICATOR_ID = 'health-bar-app'
MAX_HEALTH = 100
menu_is_open = False

def generate_health_bar_svg(health_value, unique_errors):
    """Generate an SVG health bar with current health value and number"""
    # Calculate percentage (each unique error reduces health by 1)
    percentage = max(0, min(100, health_value)) / 100.0
    
    # Create SVG with health bar and text
    svg_content = f'''<svg width="64" height="64" version="1.1" viewBox="0 0 16.933 16.933" xmlns="http://www.w3.org/2000/svg">
    <!-- Background (gray) -->
    <rect width="15.875" height="4.2333" x=".52917" y="6.35" fill="#e0e0e0" stroke="#333" stroke-width=".1"/>
    
    <!-- Health bar (green, proportional to health) -->
    <rect width="{15.875 * percentage}" height="4.2333" x=".52917" y="6.35" fill="#4caf50" stroke-width=".26458"/>
    
    <!-- Health value text -->
    <text x="8.4665" y="4.5" text-anchor="middle" font-family="sans-serif" font-size="3.5" fill="#333">{health_value}</text>
    
    <!-- Unique errors text (small, below bar) -->
    <text x="8.4665" y="13" text-anchor="middle" font-family="sans-serif" font-size="2.5" fill="#666">{unique_errors} errors</text>
</svg>'''
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
        f.write(svg_content)
        return f.name

def main():
    # Define the path to the log file
    log_file_path = os.path.expanduser('~/.health_bar/health_log.csv')
    
    # Check if log file exists
    if not os.path.exists(log_file_path):
        print(f"Warning: Log file not found at {log_file_path}")
        # Create the directory and file if they don't exist
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        with open(log_file_path, 'w') as f:
            f.write("count,warning,category,level,solution,ignore\n")

    # Get initial error counts
    unique_errors = get_error_count(log_file_path)
    total_errors = get_total_error_count(log_file_path)
    health_value = MAX_HEALTH - unique_errors
    
    # Generate initial icon
    icon_path = generate_health_bar_svg(health_value, unique_errors)
    
    # Create the indicator
    indicator = AppIndicator3.Indicator.new(APPINDICATOR_ID, icon_path, AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
    indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
    
    # Store the current icon path for cleanup
    indicator.current_icon_path = icon_path
    
    # Set initial label with error count
    update_indicator_label(indicator, total_errors)
    
    # Set initial menu
    indicator.set_menu(build_menu(log_file_path))

    print(f"Health Bar tray application started")
    
    # Set up periodic updates (every 5 seconds)
    GLib.timeout_add_seconds(5, update_indicator, indicator, log_file_path)
    
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

def get_total_error_count(log_file_path):
    """Get the total count of all errors from the CSV file"""
    try:
        if not os.path.exists(log_file_path):
            return 0
        
        total_count = 0
        with open(log_file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'count' in row:
                    try:
                        total_count += int(row['count'])
                    except ValueError:
                        pass
        
        return total_count
    except Exception as e:
        print(f"Error reading log file: {e}")
        return 0

def update_indicator_label(indicator, error_count):
    """Update the indicator label with the error count"""
    if error_count > 0:
        indicator.set_label(f"{error_count}", "")
    else:
        indicator.set_label("", "")

def update_indicator(indicator, log_file_path):
    """Periodic callback to update the indicator"""
    global menu_is_open
    
    # Get current error counts
    unique_errors = get_error_count(log_file_path)
    total_errors = get_total_error_count(log_file_path)
    health_value = MAX_HEALTH - unique_errors
    
    # Generate new icon
    new_icon_path = generate_health_bar_svg(health_value, unique_errors)
    
    # Update icon using set_icon_full to avoid deprecation warning
    indicator.set_icon_full(new_icon_path, "Health Bar Status")
    
    # Clean up old icon file
    if hasattr(indicator, 'current_icon_path') and os.path.exists(indicator.current_icon_path):
        try:
            os.unlink(indicator.current_icon_path)
        except:
            pass
    
    # Store new icon path
    indicator.current_icon_path = new_icon_path
    
    # Update label
    update_indicator_label(indicator, total_errors)
    
    # Only update menu if it's not currently open
    if not menu_is_open:
        indicator.set_menu(build_menu(log_file_path))
    
    # Return True to continue the timeout
    return True

def build_menu(log_file_path):
    global menu_is_open
    menu = Gtk.Menu()
    
    # Connect menu show/hide events
    menu.connect('show', on_menu_show)
    menu.connect('hide', on_menu_hide)

    # Menu Item: View Logs with error count
    unique_errors = get_error_count(log_file_path)
    total_errors = get_total_error_count(log_file_path)
    item_view_logs = Gtk.MenuItem(label=f'View Logs ({total_errors} total, {unique_errors} unique)')
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

def on_menu_show(menu):
    """Called when menu is shown"""
    global menu_is_open
    menu_is_open = True

def on_menu_hide(menu):
    """Called when menu is hidden"""
    global menu_is_open
    menu_is_open = False

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
