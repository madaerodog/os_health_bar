#!/usr/bin/env python3
import http.server
import socketserver
import json
import csv
import os
import re

PORT = 8088
LOG_FILE = os.path.expanduser("~/.health_bar/health_log.csv")

class HealthBarHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        return super().end_headers()

    def do_GET(self):
        if self.path == '/':
            self.path = 'index.html'
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        if self.path == '/api/logs':
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(self._get_logs_as_json().encode('utf-8'))
        else:
            super().do_GET()

    def _get_logs_as_json(self):
        logs = []
        try:
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'r', newline='') as csvfile:
                    reader = csv.reader(csvfile)
                    next(reader)  # Skip header row
                    for row in reader:
                        if not row: continue
                        # Use regex to remove [NUMBER] from the message
                        message = re.sub(r'\[NUMBER\]', '', row[2]).strip()
                        
                        logs.append({
                            "count": row[0],
                            "timestamp": row[1],
                            "message": message
                        })
        except Exception as e:
            print(f"Error reading log file: {e}")
            return json.dumps({"error": str(e)})
        
        # Sort by count descending
        logs.sort(key=lambda x: int(x['count']), reverse=True)
        return json.dumps(logs)

if __name__ == "__main__":
    # Set the working directory to the script's location
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    # Allow reusing addresses to avoid "Address already in use" errors
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), HealthBarHTTPRequestHandler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()