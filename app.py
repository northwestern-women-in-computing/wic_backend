from flask import Flask, jsonify
from flask_cors import CORS, cross_origin
from dotenv import load_dotenv
import os
import csv
import urllib.request
import json

load_dotenv()

app = Flask(__name__)
# Allow CORS for your Vercel frontend
CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.after_request
def ensure_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response

# Environment Variables
SHEET_ID = os.environ.get("SHEET_ID", "").strip().strip('"').strip("'")

# --- HELPER FUNCTION ---
def fetch_csv_data(sheet_name):
    """Fetch a specific tab from Google Sheets as CSV"""
    # Use gviz API to target specific sheet names
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
    response = urllib.request.urlopen(url)
    lines = [line.decode('utf-8') for line in response.readlines()]
    return csv.DictReader(lines)

# --- ROUTES ---

@app.route('/api/leaderboard')
@cross_origin()
def get_leaderboard():
    try:
        # Assuming your tab is named 'Form Responses 1'
        reader = fetch_csv_data('Form Responses 1')
        users = []
        for row in reader:
            users.append({
                "id": row.get("Email Address", ""), # Match your CSV header
                "name": row.get("Name", "Anonymous"),
                "points": int(row.get("Score", 0) or 0)
            })
        
        users.sort(key=lambda u: u["points"], reverse=True)
        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/events')
@cross_origin()
def get_events():
    try:
        # Assuming your tab is named 'Events'
        reader = fetch_csv_data('Sheet1')
        events = []
        for row in reader:
            status = row.get("Status", "confirmed").lower()
            events.append({
                "id": row.get("Event", ""), 
                "title": row.get("Event", "Untitled Event"),
                "status": status,
                "location": row.get("Location", "TBD"),
                "date": row.get("Event date", ""),
                "time": row.get("Event time", ""),
                "points": int(row.get("Points", 0) or 0),
                "description": row.get("Description", ""),
                "attendanceForm": row.get("RSVP Link", ""),
                "category": row.get("Category", "General"),
                "categoryColor": "blue", # You can map this in frontend
                "statusColor": "green" if status == "confirmed" else "gray"
            })
        return jsonify(events)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)