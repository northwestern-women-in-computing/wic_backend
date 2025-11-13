"""
Vercel serverless function for leaderboard API
"""
from http.server import BaseHTTPRequestHandler
import os
import json
import requests

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Get environment variables (strip quotes if present)
            SHEET_ID = os.environ.get("SHEET_ID", "").strip().strip('"').strip("'")
            GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "").strip().strip('"').strip("'")
            
            if not SHEET_ID or not GOOGLE_API_KEY:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Google Sheets API credentials not configured"}).encode('utf-8'))
                return
            
            # Fetch the sheet values via Sheets API
            range_ = "'Form Responses 1'!A:E"
            url = (
                f"https://sheets.googleapis.com/v4/spreadsheets/"
                f"{SHEET_ID}/values/{range_}?key={GOOGLE_API_KEY}"
            )
            resp = requests.get(url)
            resp.raise_for_status()
            values = resp.json().get("values", [])

            # Skip header and map rows → user objects
            users = [
                {
                    "id": row[3],               # column D: email as unique ID
                    "name": row[2],             # column C: your name
                    "points": int(row[1] or 0)  # column B: score
                }
                for row in values[1:]
                if len(row) >= 4
            ]

            # Sort descending by points
            users.sort(key=lambda u: u["points"], reverse=True)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(users).encode('utf-8'))
        except Exception as e:
            import traceback
            error_details = {
                "error": f"Failed to fetch leaderboard: {str(e)}",
                "type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(error_details).encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.end_headers()
        return
