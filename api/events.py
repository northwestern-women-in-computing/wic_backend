"""
Vercel serverless function for events API
"""
from http.server import BaseHTTPRequestHandler
import os
import json
import sys

# Import utils - try relative import first, then absolute
try:
    from .utils import get_notion_client, safe_prop
except ImportError:
    try:
        from api.utils import get_notion_client, safe_prop
    except ImportError:
        # Fallback: define functions inline if import fails
        from notion_client import Client
        
        def get_notion_client():
            NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
            if not NOTION_API_KEY:
                raise ValueError("NOTION_API_KEY not configured")
            return Client(auth=NOTION_API_KEY)
        
        def safe_prop(props, name, prop_type, subfield=None):
            prop = props.get(name, {})
            val = prop.get(prop_type)
            if not val:
                return ""
            if isinstance(val, list):
                sub = subfield or "plain_text"
                return val[0].get(sub, "") if val else ""
            if isinstance(val, dict) and subfield:
                return val.get(subfield, "")
            return ""

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Get environment variables (strip quotes if present)
            NOTION_API_KEY = os.environ.get("NOTION_API_KEY", "").strip().strip('"').strip("'")
            NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "").strip().strip('"').strip("'")
            
            if not NOTION_API_KEY or not NOTION_DATABASE_ID:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Notion API credentials not configured"}).encode('utf-8'))
                return
            
            notion = get_notion_client()
            
            # Query database with pagination
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
                    
                    page_results = results.get("results", [])
                    all_results.extend(page_results)
                    
                    has_more = results.get("has_more", False)
                    start_cursor = results.get("next_cursor")
                    
                    if not has_more or not start_cursor:
                        break
            except Exception as query_error:
                # Fallback to search API
                try:
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
                except Exception as search_error:
                    all_results = []
            
            events = []
            skipped_count = 0
            
            for page in all_results:
                props = page.get("properties", {})
                
                # Title - try common variations
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
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(events).encode('utf-8'))
        except Exception as e:
            import traceback
            error_details = {
                "error": f"Failed to fetch events: {str(e)}",
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
