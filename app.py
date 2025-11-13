from flask import Flask, jsonify, make_response
from flask_cors import CORS, cross_origin
from dotenv import load_dotenv
import os
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.after_request
def ensure_cors_headers(response):
    # always set CORS headers, even on errors
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response

NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
SHEET_ID        = os.environ["SHEET_ID"]
GOOGLE_API_KEY  = os.environ["GOOGLE_API_KEY"]

# Notion API integration
from notion_client import Client
notion = Client(auth=NOTION_API_KEY)

import requests
from urllib.parse import quote

@app.route('/api/leaderboard')
@cross_origin()
def get_leaderboard():
    # 1) Fetch the sheet values via Sheets API
    range_ = "'Form Responses 1'!A:E"

    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/"
        f"{SHEET_ID}/values/{range_}?key={GOOGLE_API_KEY}"
    )
    resp = requests.get(url)
    resp.raise_for_status()
    values = resp.json().get("values", [])

    # 2) Skip header and map rows → user objects
    users = [
        {
          "id":    row[3],               # column D: email as unique ID
          "name":  row[2],               # column C: your name
          "points": int(row[1] or 0)     # column B: score
        }
        for row in values[1:]
        if len(row) >= 4
    ]

    # 3) Sort descending by points
    users.sort(key=lambda u: u["points"], reverse=True)

    return jsonify(users)

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

@app.route('/api/events/debug')
def get_events_debug():
    """Debug endpoint to see raw Notion response and count"""
    try:
        if NOTION_API_KEY is None or NOTION_DATABASE_ID is None:
            return jsonify({"error": "Notion API credentials not configured"}), 500
        
        all_results = []
        start_cursor = None
        
        try:
            while True:
                query_body = {"page_size": 100}
                if start_cursor:
                    query_body["start_cursor"] = start_cursor
                
                results = notion.request(
                    path=f"databases/{NOTION_DATABASE_ID}/query",
                    method="POST",
                    body=query_body
                )
                
                all_results.extend(results.get("results", []))
                
                has_more = results.get("has_more", False)
                start_cursor = results.get("next_cursor")
                
                if not has_more or not start_cursor:
                    break
        except Exception as e:
            return jsonify({"error": f"Query failed: {str(e)}"}), 500
        
        # Analyze all pages
        pages_info = []
        for page in all_results:
            props = page.get("properties", {})
            # Try to get title
            title = None
            for prop_name, prop_value in props.items():
                if isinstance(prop_value, dict) and prop_value.get("type") == "title":
                    title = safe_prop(props, prop_name, "title")
                    if title:
                        break
            
            status = safe_prop(props, "Status", "status", "name") or safe_prop(props, "Event Status", "status", "name")
            pages_info.append({
                "id": page.get("id", ""),
                "has_title": bool(title),
                "title": title or "NO TITLE",
                "status": status or "NO STATUS",
                "property_names": list(props.keys())
            })
        
        return jsonify({
            "total_pages_from_notion": len(all_results),
            "pages_info": pages_info,
            "sample_page_properties": list(all_results[0].get("properties", {}).keys()) if all_results else []
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/events/summary')
def get_events_summary():
    """Get summary of events query - for debugging"""
    try:
        if NOTION_API_KEY is None or NOTION_DATABASE_ID is None:
            return jsonify({"error": "Notion API credentials not configured"}), 500
        
        all_results = []
        start_cursor = None
        page_count = 0
        
        try:
            while True:
                query_body = {"page_size": 100}
                if start_cursor:
                    query_body["start_cursor"] = start_cursor
                
                results = notion.request(
                    path=f"databases/{NOTION_DATABASE_ID}/query",
                    method="POST",
                    body=query_body
                )
                
                all_results.extend(results.get("results", []))
                page_count += 1
                
                has_more = results.get("has_more", False)
                start_cursor = results.get("next_cursor")
                
                if not has_more or not start_cursor:
                    break
        except Exception as e:
            return jsonify({"error": f"Query failed: {str(e)}"}), 500
        
        # Count events with titles
        events_with_titles = 0
        events_without_titles = 0
        statuses = {}
        
        for page in all_results:
            props = page.get("properties", {})
            title = None
            for prop_name, prop_value in props.items():
                if isinstance(prop_value, dict) and prop_value.get("type") == "title":
                    title = safe_prop(props, prop_name, "title")
                    if title:
                        break
            
            if title:
                events_with_titles += 1
                status = safe_prop(props, "Status", "status", "name") or safe_prop(props, "Event Status", "status", "name") or "No Status"
                statuses[status] = statuses.get(status, 0) + 1
            else:
                events_without_titles += 1
        
        return jsonify({
            "total_pages_from_notion": len(all_results),
            "api_pages_fetched": page_count,
            "events_with_titles": events_with_titles,
            "events_without_titles": events_without_titles,
            "status_breakdown": statuses,
            "sample_property_names": list(all_results[0].get("properties", {}).keys()) if all_results else []
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/events')
def get_events():
    try:
        # Use the correct Notion API method
        if NOTION_API_KEY is None or NOTION_DATABASE_ID is None:
            return jsonify({"error": "Notion API credentials not configured"}), 500
        
        # Query database - try using pages endpoint with database filter
        # First, let's try the direct database query endpoint with pagination
        all_results = []
        start_cursor = None
        
        try:
            while True:
                # Query without any filters - Notion API will return all accessible pages
                query_body = {
                    "page_size": 100
                }
                if start_cursor:
                    query_body["start_cursor"] = start_cursor
                
                print(f"Querying Notion with: page_size={query_body.get('page_size')}, start_cursor={'Yes' if start_cursor else 'No'}")
                
                results = notion.request(
                    path=f"databases/{NOTION_DATABASE_ID}/query",
                    method="POST",
                    body=query_body
                )
                
                page_results = results.get("results", [])
                all_results.extend(page_results)
                print(f"Fetched {len(page_results)} pages in this batch, total so far: {len(all_results)}")
                
                # Check if there are more pages
                has_more = results.get("has_more", False)
                start_cursor = results.get("next_cursor")
                
                print(f"Has more: {has_more}, Next cursor: {start_cursor[:20] if start_cursor else 'None'}...")
                
                if not has_more or not start_cursor:
                    break
        except Exception as query_error:
            print(f"Database query failed: {str(query_error)}")
            print("Trying search API as fallback...")
            # If direct query fails, try using search endpoint to find all pages in the database
            try:
                # Search for pages that are children of this database
                search_results = notion.request(
                    path="search",
                    method="POST",
                    body={
                        "filter": {
                            "property": "object",
                            "value": "page"
                        },
                        "sort": {
                            "direction": "descending",
                            "timestamp": "last_edited_time"
                        },
                        "page_size": 100
                    }
                )
                all_results = search_results.get("results", [])
                print(f"Search API returned {len(all_results)} pages")
            except Exception as search_error:
                print(f"Search API also failed: {str(search_error)}")
                all_results = []
        
        events = []
        skipped_count = 0
        print(f"Total pages from Notion: {len(all_results)}")
        
        for page in all_results:
            props = page.get("properties", {})
            
            # Debug: Print available property names (only for first event)
            if len(events) == 0:
                print("Available properties:", list(props.keys()))
                print("Sample properties:", {k: list(v.keys()) if isinstance(v, dict) else type(v).__name__ for k, v in list(props.items())[:3]})
                # Check for URL properties
                url_props = [k for k, v in props.items() if isinstance(v, dict) and v.get("type") == "url"]
                if url_props:
                    print("URL properties found:", url_props)
            
            # Try to find properties with common name variations
            # Title - try common variations, or get first title-type property
            title = (safe_prop(props, "Event name", "title") or 
                    safe_prop(props, "Name", "title") or
                    safe_prop(props, "Title", "title") or
                    safe_prop(props, "Event", "title"))
            
            # If title not found, try to get the first property that is a title type
            if not title:
                for prop_name, prop_value in props.items():
                    if isinstance(prop_value, dict) and prop_value.get("type") == "title":
                        title = safe_prop(props, prop_name, "title")
                        if title:
                            break
            
            # Skip events without titles
            if not title:
                skipped_count += 1
                print(f"Skipping page {page.get('id', 'unknown')[:20]}... - no title found. Available props: {list(props.keys())[:5]}")
                continue
            
            # Date - try common variations
            date_val = (safe_prop(props, "Event date", "date", "start") or
                       safe_prop(props, "Date", "date", "start") or
                       safe_prop(props, "Event Date", "date", "start") or
                       safe_prop(props, "When", "date", "start"))
            
            # Category - try common variations
            category = (safe_prop(props, "Category", "select", "name") or
                        safe_prop(props, "Type", "select", "name") or
                        safe_prop(props, "Event Type", "select", "name"))
            categoryColor = (safe_prop(props, "Category", "select", "color") or
                            safe_prop(props, "Type", "select", "color") or
                            safe_prop(props, "Event Type", "select", "color"))
            
            # Location/Venue - try common variations
            location = (safe_prop(props, "Venue", "select", "name") or
                       safe_prop(props, "Location", "select", "name") or
                       safe_prop(props, "Where", "select", "name") or
                       safe_prop(props, "Venue", "rich_text") or
                       safe_prop(props, "Location", "rich_text"))
            
            # Capacity - try common variations
            maxAttendees = (props.get("Capacity", {}).get("number") or
                           props.get("Max Attendees", {}).get("number") or
                           props.get("Max Capacity", {}).get("number") or 0)
            
            # Current attendees count - not available in Notion, default to 0
            attendees = 0
            
            # Format - try common variations
            format_val = (safe_prop(props, "Format", "select", "name") or
                          safe_prop(props, "Event Format", "select", "name") or
                          safe_prop(props, "Type", "select", "name"))
            
            # Status - try common variations
            status = (safe_prop(props, "Status", "status", "name") or
                     safe_prop(props, "Event Status", "status", "name"))
            statusColor = (safe_prop(props, "Status", "status", "color") or
                          safe_prop(props, "Event Status", "status", "color"))
            
            # Description - try common variations (rich_text type)
            description = (safe_prop(props, "Description", "rich_text") or
                          safe_prop(props, "Event Description", "rich_text") or
                          safe_prop(props, "Details", "rich_text") or
                          safe_prop(props, "About", "rich_text"))
            
            # Points - try common variations (number type)
            points = (props.get("Points", {}).get("number") or
                     props.get("Event Points", {}).get("number") or
                     props.get("Reward Points", {}).get("number") or
                     props.get("Point Value", {}).get("number") or 0)
            
            # Attendance Form URL - try common variations (url type)
            # URL types in Notion are just strings, not lists
            attendanceForm = None
            # First, try exact property names
            for prop_name in ["Attendance Form", "RSVP Form", "RSVP Link", "Registration Form", 
                            "Registration Link", "Form", "Link", "RSVP", "Attendance", "RSVP URL"]:
                prop = props.get(prop_name, {})
                if isinstance(prop, dict) and prop.get("type") == "url":
                    url_val = prop.get("url")
                    if url_val:
                        attendanceForm = url_val
                        break
            
            # If not found, search all URL-type properties
            if not attendanceForm:
                for prop_name, prop_value in props.items():
                    if isinstance(prop_value, dict) and prop_value.get("type") == "url":
                        url_val = prop_value.get("url")
                        if url_val and any(keyword in prop_name.lower() for keyword in ["form", "rsvp", "link", "attendance", "register"]):
                            attendanceForm = url_val
                            break
            
            event = {
                "id": page.get("id", ""),
                "title": title,
                "date": date_val,
                "category": category,
                "categoryColor": categoryColor,
                "location": location,
                "maxAttendees": maxAttendees if maxAttendees else 0,
                "attendees": attendees if attendees else 0,
                "format": format_val,
                "status": status,
                "statusColor": statusColor,
                "description": description,
                "points": points if points else 0,
                "attendanceForm": attendanceForm,
            }
            events.append(event)
        
        print(f"Processed {len(events)} events, skipped {skipped_count} pages without titles")
        return jsonify(events)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch events: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True) 