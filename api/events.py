from http.server import BaseHTTPRequestHandler
import os
import json
import csv
import urllib.request

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # 1. Get the Sheet ID from Vercel Environment Variables
            EVENTS_SHEET_ID = os.environ.get("EVENTS_SHEET_ID", "").strip().strip('"').strip("'")
            
            if not EVENTS_SHEET_ID:
                raise ValueError("EVENTS_SHEET_ID not configured")

            # 2. Construct the CSV Export URL
            # Note: Replace 'Events' with the exact name of the tab in your Google Sheet
            csv_url = f"https://docs.google.com/spreadsheets/d/{EVENTS_SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"

            # 3. Fetch and Parse the data
            response = urllib.request.urlopen(csv_url)
            lines = [line.decode('utf-8') for line in response.readlines()]
            reader = csv.DictReader(lines)
            
            events = []
            for row in reader:
                # We normalize the status to lowercase for the frontend logic
                status = row.get("Status", "").lower()
                
                events.append({
                    "id": row.get("Event", ""), # Using event name as ID or a separate ID column
                    "title": row.get("Event", "Untitled Event"),
                    "status": status,
                    "location": row.get("Location", "TBD"),
                    "date": row.get("Event date", ""),
                    "time": row.get("Event time", ""),
                    "points": int(row.get("Points", 0) or 0),
                    # Adding defaults for fields your frontend expects
                    "category": "General", 
                    "categoryColor": "blue",
                    "statusColor": "green" if status == "confirmed" else "gray"
                })

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(events).encode('utf-8'))

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