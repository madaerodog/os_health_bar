# OS Health Bar

OS Health Bar is a lightweight system monitoring utility for Linux desktops. It keeps an eye on your system's journal for warnings and displays a persistent "health bar" in your system tray, giving you an at-a-glance overview of your system's stability.

![Health Bar Icon](health_bar_icon.svg)

## Features

*   **Systemd Service:** A background service (`health_monitor.sh`) runs continuously to monitor `journalctl` for warning-level messages.
*   **Log Aggregation:** Similar warnings are grouped together to avoid cluttering the log. The count of each unique warning is tracked.
*   **Tray Application:** A Python-based GTK tray application (`tray_app.py`) provides a visual representation of the system's health.
*   **Dynamic Icon:** The tray icon is a dynamically generated SVG that changes to reflect the number of unique warnings.
*   **Easy Installation:** A simple `install.sh` script handles installation, uninstallation, and service management.
*   **Autostart:** The tray application is automatically started when you log in.

## How It Works

1.  **Monitoring:** The `health_bar.service` runs the `health_monitor.sh` script, which monitors `journalctl` for new warnings.
2.  **Normalization:** To group similar errors, any numerical digits in a warning are replaced with `[NUMBER]`.
3.  **Logging:** Normalized warnings are logged to `~/.health_bar/health_log.csv`.
4.  **Aggregation:** If an identical warning is logged more than once, the script increments a `count` in the existing row.
5.  **Tray Icon:** The `tray_app.py` application reads the log file and displays a health bar icon in the system tray. The health decreases as the number of unique warnings increases.

## Installation

To install and start the service, run the installer script with `sudo`:

```bash
sudo ./install.sh
```

The script will:

*   Install required dependencies (`python3-gi`, `gir1.2-appindicator3-0.1`, etc.).
*   Copy the necessary files to system and user directories.
*   Set up and start the `systemd` service.
*   Create an autostart entry for the tray application.

## Usage

Once installed, the health bar icon will appear in your system tray. You can click on the icon to open a menu with the following options:

*   **View Logs:** Opens the `health_log.csv` file in your default text editor.
*   **Restart Monitoring Service:** Restarts the `health_bar` service.
*   **About Health Bar:** Opens the project's GitHub repository.
*   **Quit:** Closes the tray application.

## Uninstallation

To completely remove Health Bar from your system:

```bash
sudo ./install.sh -remove
```

The uninstall process will:

*   Stop and disable the `systemd` service.
*   Remove all system and user files.
*   Ask before removing the user data directory (`~/.health_bar`).

## Contributing

Contributions are welcome! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request.