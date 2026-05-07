from http.server import BaseHTTPRequestHandler
import os
import json
import csv
import urllib.request

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # 1. Get the Sheet ID from Vercel Environment Variables
            LEAD_SHEET_ID = os.environ.get("LEAD_SHEET_ID", "").strip().strip('"').strip("'")
            
            if not LEAD_SHEET_ID:
                raise ValueError("LEAD_SHEET_ID not configured")

            # 2. Construct the CSV Export URL
            csv_url = f"https://docs.google.com/spreadsheets/d/{LEAD_SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Attendance"

            # 3. Fetch and Parse the data
            response = urllib.request.urlopen(csv_url)
            lines = [line.decode('utf-8') for line in response.readlines()]
            reader = csv.DictReader(lines)
            
            students = []
            for row in reader:
                students.append({
                    "id": row.get("Name", ""), # Using event name as ID or a separate ID column
                    "name": row.get("Name"),
                    "points": int(row.get("Points", 0) or 0)
                })

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(students).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,OPTIONS')
        self.end_headers()