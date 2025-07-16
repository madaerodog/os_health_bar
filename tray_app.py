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
import base64

APPINDICATOR_ID = 'health-bar-app'
MAX_HEALTH = 100
menu_is_open = False
VERSION = "1.1.3"  # Version for debugging

ICON_FULL_HEALTH = os.path.expanduser('~/.local/share/icons/icon_full_health.png')
ICON_DAMAGE = os.path.expanduser('~/.local/share/icons/icon_damage.png')

def generate_health_bar_overlay_svg(health_value):
    """Generate an SVG for only the health bar overlay."""
    percentage = max(0, min(100, health_value)) / 100.0
    
    # Dimensions for the health bar within the 64x64 icon
    # Based on visual inspection, the bar is roughly at x=7, y=50, width=50, height=8
    # SVG units are 16.933 / 64 = 0.264578125 mm/px
    # So, for a 64x64 icon, 1px = 0.26458mm
    # x=7px -> 1.852mm
    # y=50px -> 13.229mm
    # width=50px -> 13.229mm
    # height=8px -> 2.116mm

    # Using a viewBox that matches the 64x64 pixel dimensions directly for simplicity
    # and then scaling the internal elements.
    # The health bar itself is 50px wide and 8px high, positioned at (7, 50) on a 64x64 canvas.
    bar_width_px = 50 * percentage
    bar_height_px = 8
    bar_x_px = 7
    bar_y_px = 50

    svg_content = f'''<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
    <rect x="{bar_x_px}" y="{bar_y_px}" width="{bar_width_px}" height="{bar_height_px}" fill="#4caf50"/>
</svg>'''
    
    svg_file = tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False)
    svg_file.write(svg_content)
    svg_file.close()
    return svg_file.name

def compose_icon(base_icon_path, health_value):
    """Composes the health bar onto the base icon and returns the path to the composite PNG."""
    health_bar_svg_path = generate_health_bar_overlay_svg(health_value)
    
    # Convert health bar SVG to PNG
    health_bar_png_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    health_bar_png_file.close()
    
    try:
        subprocess.run([
            'rsvg-convert', 
            '-w', '64', 
            '-h', '64', 
            '-b', 'rgba(0,0,0,0)', 
            '-f', 'png', 
            '-o', health_bar_png_file.name, 
            health_bar_svg_path
        ], check=True, capture_output=True)
    except Exception as e:
        print(f"Error converting health bar SVG to PNG: {e}")
        return base_icon_path # Fallback
    finally:
        os.unlink(health_bar_svg_path)

    # Composite the health bar PNG onto the base icon PNG
    composite_png_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    composite_png_file.close()

    # The health bar is positioned at (7, 50) on the 64x64 base image
    geometry_offset = "+7+50"

    try:
        subprocess.run([
            'convert',
            base_icon_path,
            health_bar_png_file.name,
            '-geometry', geometry_offset,
            '-composite',
            composite_png_file.name
        ], check=True, capture_output=True)
        return composite_png_file.name
    except Exception as e:
        print(f"Error compositing icons: {e}")
        return base_icon_path # Fallback
    finally:
        os.unlink(health_bar_png_file.name)

def cleanup_old_icon(icon_path):
    """Cleanup old icon files with proper error handling"""
    try:
        if os.path.exists(icon_path):
            os.unlink(icon_path)
    except:
        pass
    return False  # Don't repeat the timer

def main():
    print(f"Health Bar Tray v{VERSION} starting...")
    
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
    
    # Determine base icon
    base_icon = ICON_FULL_HEALTH if unique_errors == 0 else ICON_DAMAGE
    
    # Generate initial composite icon
    icon_path = compose_icon(base_icon, health_value)
    
    # Create the indicator
    indicator = AppIndicator3.Indicator.new(APPINDICATOR_ID, icon_path, AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
    indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
    
    # Store the current icon path for cleanup
    indicator.current_icon_path = icon_path
    
    # Set initial label with health value
    update_indicator_label(indicator, health_value)
    
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

def update_indicator_label(indicator, health_value):
    """Update the indicator label with the current health value"""
    indicator.set_label(f"{health_value} HP", "")

def update_indicator(indicator, log_file_path):
    """Periodic callback to update the indicator"""
    global menu_is_open
    
    # Get current error counts
    unique_errors = get_error_count(log_file_path)
    total_errors = get_total_error_count(log_file_path)
    health_value = MAX_HEALTH - unique_errors
    
    # Determine base icon
    base_icon = ICON_FULL_HEALTH if unique_errors == 0 else ICON_DAMAGE

    # Generate new composite icon
    new_icon_path = compose_icon(base_icon, health_value)
    
    # Update icon using set_icon_full to avoid deprecation warning
    indicator.set_icon_full(new_icon_path, "Health Bar Status")
    
    # Clean up old icon file (but wait a bit to ensure it's not still being used)
    if hasattr(indicator, 'current_icon_path') and os.path.exists(indicator.current_icon_path):
        try:
            # Don't immediately delete, let the system process it first
            old_path = indicator.current_icon_path
            # Schedule deletion after a delay
            GLib.timeout_add_seconds(10, lambda: cleanup_old_icon(old_path))
        except:
            pass
    
    # Store new icon path
    indicator.current_icon_path = new_icon_path
    
    # Update label
    update_indicator_label(indicator, health_value)
    
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
    item_view_logs.connect('activate', view_logs_in_browser)
    menu.append(item_view_logs)

    # Separator
    menu.append(Gtk.SeparatorMenuItem())

    # Menu Item: About Health Bar
    item_about = Gtk.MenuItem(label='About Health Bar')
    item_about.connect('activate', open_about)
    menu.append(item_about)

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


def open_about(widget):
    # Open the GitHub repository in the default browser
    url = 'https://github.com/madaerodog/os_health_bar'
    
    try:
        # Try using subprocess.Popen to detach the process
        subprocess.Popen(['xdg-open', url])
    except FileNotFoundError:
        try:
            # Fallback to firefox
            subprocess.Popen(['firefox', url])
        except FileNotFoundError:
            try:
                # Fallback to chrome
                subprocess.Popen(['google-chrome', url])
            except FileNotFoundError:
                pass

def view_logs_in_browser(widget):
    # Open the browser to the web server address
    url = 'http://localhost:8088'
    try:
        subprocess.Popen(['xdg-open', url])
    except Exception as e:
        print(f"Failed to open browser: {e}")

def quit_app(_):
    Gtk.main_quit()

if __name__ == "__main__":
    # Gracefully handle Ctrl+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()