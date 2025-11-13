"""
Shared utilities for Vercel serverless functions
"""
from notion_client import Client
import os

def get_notion_client():
    """Initialize and return Notion client"""
    # Strip quotes if present (Vercel env vars shouldn't have quotes)
    NOTION_API_KEY = os.environ.get("NOTION_API_KEY", "").strip().strip('"').strip("'")
    if not NOTION_API_KEY:
        raise ValueError("NOTION_API_KEY not configured")
    return Client(auth=NOTION_API_KEY)

def safe_prop(props, name, prop_type, subfield=None):
    """
    Safely extract property from Notion page properties
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
        return val[0].get(sub, "") if val else ""

    # dict‑based types (like select, number, checkbox)
    if isinstance(val, dict) and subfield:
        return val.get(subfield, "")

    return ""

