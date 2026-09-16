import httpx
import json
from bs4 import BeautifulSoup
from typing import Callable, Dict, Any

from playwright.sync_api import sync_playwright

def fetch_page(url: str) -> str:
    """
    Fetches the content of a page using Playwright to render JavaScript.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # wait_until='networkidle' ensures JS has time to fetch the RFPs via API
            page.goto(url, wait_until='networkidle', timeout=60000)
            html = page.content()
            browser.close()
            
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)
            return text[:120000] # return first 30000 chars to avoid missing content after mega menus
    except Exception as e:
        return f"Error fetching page: {str(e)}"

# OpenAI Tool Definition
fetch_page_schema = {
    "type": "function",
    "function": {
        "name": "fetch_page",
        "description": "Fetches the raw text content of a webpage given its URL. Use this to read the full details of an RFP from a link.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The full HTTP/HTTPS URL of the page to fetch."
                }
            },
            "required": ["url"],
            "additionalProperties": False,
        }
    }
}

# Registry for easy execution by name
TOOL_REGISTRY: Dict[str, Callable] = {
    "fetch_page": fetch_page
}

AVAILABLE_TOOLS = [fetch_page_schema]
