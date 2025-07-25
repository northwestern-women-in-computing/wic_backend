from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
load_dotenv()

app = Flask(__name__)
CORS(app)

NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

# Notion API integration
from notion_client import Client
notion = Client(auth=NOTION_API_KEY)

# Mock events data (same as frontend for now)
# events = [
#     {
#         "id": 1,
#         "title": "Tech Talk: Women Leaders in AI",
#         "description": "Join us for an inspiring talk with women leaders from top AI companies discussing their career journeys and the future of artificial intelligence.",
#         "date": "2024-02-15",
#         "time": "18:00",
#         "location": "Tech Building Room 101",
#         "points": 10,
#         "attendees": 45,
#         "maxAttendees": 60,
#         "category": "Tech Talk",
#     },
#     {
#         "id": 2,
#         "title": "Coding Workshop: Web Development",
#         "description": "Hands-on workshop covering HTML, CSS, and JavaScript fundamentals. Perfect for beginners!",
#         "date": "2024-02-22",
#         "time": "19:00",
#         "location": "Computer Lab A",
#         "points": 15,
#         "attendees": 25,
#         "maxAttendees": 30,
#         "category": "Workshop",
#     },
#     {
#         "id": 3,
#         "title": "Networking Night with Industry Professionals",
#         "description": "Connect with alumni and industry professionals over dinner and meaningful conversations about career paths in tech.",
#         "date": "2024-03-01",
#         "time": "18:30",
#         "location": "University Center",
#         "points": 20,
#         "attendees": 35,
#         "maxAttendees": 50,
#         "category": "Networking",
#     },
#     {
#         "id": 4,
#         "title": "Hackathon: Women in Tech Challenge",
#         "description": "24-hour hackathon focused on creating solutions that empower women in technology. Prizes and mentorship included!",
#         "date": "2024-03-15",
#         "time": "09:00",
#         "location": "Innovation Hub",
#         "points": 50,
#         "attendees": 20,
#         "maxAttendees": 40,
#         "category": "Hackathon",
#     },
#     {
#         "id": 5,
#         "title": "Resume Review and Interview Prep",
#         "description": "Get your resume reviewed by industry professionals and practice technical interviews in a supportive environment.",
#         "date": "2024-03-22",
#         "time": "17:00",
#         "location": "Career Services Center",
#         "points": 10,
#         "attendees": 15,
#         "maxAttendees": 25,
#         "category": "Career",
#     },
#     {
#         "id": 6,
#         "title": "Panel: Entrepreneurship in Tech",
#         "description": "Hear from successful women entrepreneurs about starting tech companies, securing funding, and building diverse teams.",
#         "date": "2024-04-05",
#         "time": "18:00",
#         "location": "Auditorium B",
#         "points": 15,
#         "attendees": 30,
#         "maxAttendees": 100,
#         "category": "Panel",
#     },
# ]

def safe_prop(props, name, prop_type, subfield=None):
    """
    - For 'title' and 'rich_text', returns the first item's subfield (default 'plain_text').
    - For 'select', returns the dict's subfield (e.g. 'name').
    - Falls back to "" if missing.
    """
    prop = props.get(name, {})
    val = prop.get(prop_type)

    if not val:
        return ""

    # list‑based types
    if isinstance(val, list):
        sub = subfield or "plain_text"
        return val[0].get(sub, "")

    # dict‑based types (like select, number, checkbox)
    if isinstance(val, dict) and subfield:
        return val.get(subfield, "")

    return ""

@app.route('/api/events')
def get_events():
    results = notion.databases.query(database_id=NOTION_DATABASE_ID)
    events = []
    for page in results["results"]:
        props = page["properties"]
        event = {
            "id": page["id"],
            "title": safe_prop(props, "Event name", "title"),
            "date": safe_prop(props, "Event date", "date", "start"),
            "category": safe_prop(props, "Category", "select", "name"),
            "categoryColor": safe_prop(props, "Category", "select", "color"),
            "location": safe_prop(props, "Venue", "select", "name"),
            "maxAttendees": props.get("Capacity", {}).get("number", 0),
            "format": safe_prop(props, "Format", "select", "name"),
            "status": safe_prop(props, "Status", "status", "name"),
            "statusColor": safe_prop(props, "Status", "status", "color"),
        }
        events.append(event)
    return jsonify(events)

if __name__ == '__main__':
    app.run(debug=True) 