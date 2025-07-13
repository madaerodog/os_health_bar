# Health Bar

This project provides a simple utility to monitor system warnings on a Linux machine and store them in a persistent log file.

## How It Works

The core of the project is the `health_monitor.sh` script, which is managed by a systemd service (`health_bar.service`).

1.  **Monitoring**: The service runs continuously in the background, monitoring the system's `journalctl` for any messages with a priority level of "warning" (level 4) or higher.
2.  **Normalization**: To group similar errors, any numerical digits (`0-9`) in a captured warning message are replaced with the placeholder `[NUMBER]`.
3.  **Logging**: The normalized warnings are logged to a CSV file located at `~/.health_bar/health_log.csv`.
4.  **Aggregation**: If an identical normalized warning is logged more than once, instead of creating a new row, the script simply increments a `count` in the existing row.
5.  **Log Management**: The log file is automatically cleared and re-initialized with a header row every time the service starts, which typically occurs at system boot.

## Installation

To install and start the service, run the installer script:

```bash
./install.sh
```

The script will perform the following actions:
- Create the `~/.health_bar` directory for logs.
- Copy the `health_monitor.sh` script to `/usr/local/bin/`.
- Copy the `health_bar.service` file to `/etc/systemd/system/`.
- Reload the systemd daemon.
- Enable and restart the `health_bar` service.

## Log File

- **Location**: `~/.health_bar/health_log.csv`
- **Format**: A CSV file with the following columns: `count,warning,category,level,solution,ignore`.

## A Note on System Notifications

This utility **logs** system warnings; it does **not** generate the notification pop-ups you might see on your desktop. These notifications are a feature of your desktop environment (e.g., GNOME, KDE, XFCE), which is configured to display alerts for high-priority system messages.

To disable these pop-ups, you will need to adjust the notification settings within your specific desktop environment.
