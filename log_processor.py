import csv
import os
import re
import sys
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.health_bar/health_log.csv")

def process_log_entry(log_message):
    logs = []
    header = ["count", "timestamp", "warning", "category", "level", "solution", "ignore"]

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            try:
                file_header = next(reader)
                if file_header != header:
                    # If header is different, assume it's a new or corrupted file and re-initialize
                    logs = []
                else:
                    for row in reader:
                        if row: # Ensure row is not empty
                            logs.append(row)
            except StopIteration:
                # File is empty, just use the default header
                pass

    # Normalize the warning
    normalized_message = re.sub(r'\d+', '[NUMBER]', log_message).strip()

    found = False
    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for i, row in enumerate(logs):
        if len(row) > 2 and row[2].strip() == normalized_message:
            try:
                logs[i][0] = str(int(logs[i][0]) + 1) # Increment count
            except ValueError:
                logs[i][0] = "1" # Reset to 1 if count is not a valid number
            logs[i][1] = current_timestamp # Update timestamp
            found = True
            break
    
    if not found:
        # Add new entry
        logs.append(["1", current_timestamp, normalized_message, "0", "0", "no_solution", "0"])

    # Write back to CSV
    with open(LOG_FILE, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header) # Write header
        writer.writerows(logs)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        process_log_entry(sys.argv[1])