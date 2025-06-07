"""
URL Shortener Tool for creating and managing short URLs.
"""

import hashlib
import random
import string
import json
import os
from datetime import datetime
from typing import Optional, Dict, List
from urllib.parse import urlparse
import requests

from app.tool.base import BaseTool, ToolResult


class UrlShortener(BaseTool):
    """Tool for creating and managing short URLs."""

    name: str = "url_shortener"
    description: str = """Create and manage short URLs.

    Available commands:
    - shorten: Create a short URL
    - expand: Expand a short URL to original
    - list: List all shortened URLs
    - stats: Get statistics for a short URL
    - delete: Delete a short URL
    - validate: Validate if URL is accessible
    """

    parameters: dict = {
        "type": "object",
        "properties": {
            "command": {
                "description": "The command to execute.",
                "enum": ["shorten", "expand", "list", "stats", "delete", "validate"],
                "type": "string",
            },
            "url": {
                "description": "URL to shorten or validate.",
                "type": "string",
            },
            "short_code": {
                "description": "Short code for URL.",
                "type": "string",
            },
            "custom_code": {
                "description": "Custom short code (optional).",
                "type": "string",
            },
            "description": {
                "description": "Description for the shortened URL.",
                "type": "string",
            },
            "expiry_days": {
                "description": "Number of days until expiry (optional).",
                "type": "integer",
            },
        },
        "required": ["command"],
        "additionalProperties": False,
    }

    def __init__(self):
        super().__init__()
        self.storage_file = "url_shortener_data.json"
        self.base_url = "https://short.ly/"  # Example base URL
        self.data = self._load_data()

    async def execute(
        self,
        command: str,
        url: Optional[str] = None,
        short_code: Optional[str] = None,
        custom_code: Optional[str] = None,
        description: Optional[str] = None,
        expiry_days: Optional[int] = None,
        **kwargs
    ) -> ToolResult:
        """Execute URL shortener command."""
        try:
            if command == "shorten":
                return self._shorten_url(url, custom_code, description, expiry_days)
            elif command == "expand":
                return self._expand_url(short_code)
            elif command == "list":
                return self._list_urls()
            elif command == "stats":
                return self._get_stats(short_code)
            elif command == "delete":
                return self._delete_url(short_code)
            elif command == "validate":
                return self._validate_url(url)
            else:
                return ToolResult(error=f"Unknown command: {command}")
        except Exception as e:
            return ToolResult(error=f"Error executing URL shortener command '{command}': {str(e)}")

    def _load_data(self) -> Dict:
        """Load URL data from storage."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"urls": {}, "stats": {}}

    def _save_data(self):
        """Save URL data to storage."""
        with open(self.storage_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def _generate_short_code(self, length: int = 6) -> str:
        """Generate a random short code."""
        chars = string.ascii_letters + string.digits
        while True:
            code = ''.join(random.choices(chars, k=length))
            if code not in self.data["urls"]:
                return code

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def _shorten_url(self, url: Optional[str], custom_code: Optional[str],
                    description: Optional[str], expiry_days: Optional[int]) -> ToolResult:
        """Create a short URL."""
        try:
            if not url:
                return ToolResult(error="URL is required for shortening")

            if not self._is_valid_url(url):
                return ToolResult(error="Invalid URL format")

            # Check if URL already exists
            for code, data in self.data["urls"].items():
                if data["original_url"] == url:
                    short_url = f"{self.base_url}{code}"
                    return ToolResult(output=f"URL already shortened!\n"
                                            f"Original URL: {url}\n"
                                            f"Short URL: {short_url}\n"
                                            f"Short Code: {code}")

            # Generate or use custom code
            if custom_code:
                if custom_code in self.data["urls"]:
                    return ToolResult(error=f"Custom code '{custom_code}' already exists")
                if not custom_code.isalnum():
                    return ToolResult(error="Custom code must contain only letters and numbers")
                short_code = custom_code
            else:
                short_code = self._generate_short_code()

            # Calculate expiry date
            expiry_date = None
            if expiry_days:
                from datetime import timedelta
                expiry_date = (datetime.now() + timedelta(days=expiry_days)).isoformat()

            # Store URL data
            self.data["urls"][short_code] = {
                "original_url": url,
                "created_at": datetime.now().isoformat(),
                "description": description or "",
                "expiry_date": expiry_date,
                "clicks": 0
            }

            # Initialize stats
            self.data["stats"][short_code] = {
                "total_clicks": 0,
                "daily_clicks": {},
                "referrers": {},
                "countries": {}
            }

            self._save_data()

            short_url = f"{self.base_url}{short_code}"

            output = f"URL shortened successfully!\n"
            output += f"Original URL: {url}\n"
            output += f"Short URL: {short_url}\n"
            output += f"Short Code: {short_code}\n"
            if description:
                output += f"Description: {description}\n"
            if expiry_date:
                output += f"Expires: {expiry_date}\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error shortening URL: {str(e)}")

    def _expand_url(self, short_code: Optional[str]) -> ToolResult:
        """Expand a short URL to original."""
        try:
            if not short_code:
                return ToolResult(error="Short code is required for expansion")

            if short_code not in self.data["urls"]:
                return ToolResult(error=f"Short code '{short_code}' not found")

            url_data = self.data["urls"][short_code]

            # Check if expired
            if url_data.get("expiry_date"):
                expiry = datetime.fromisoformat(url_data["expiry_date"])
                if datetime.now() > expiry:
                    return ToolResult(error=f"Short URL has expired on {expiry.strftime('%Y-%m-%d %H:%M:%S')}")

            # Increment click count
            self.data["urls"][short_code]["clicks"] += 1
            self.data["stats"][short_code]["total_clicks"] += 1

            # Update daily stats
            today = datetime.now().strftime('%Y-%m-%d')
            daily_stats = self.data["stats"][short_code]["daily_clicks"]
            daily_stats[today] = daily_stats.get(today, 0) + 1

            self._save_data()

            output = f"URL expanded successfully!\n"
            output += f"Short Code: {short_code}\n"
            output += f"Original URL: {url_data['original_url']}\n"
            output += f"Created: {url_data['created_at']}\n"
            output += f"Total Clicks: {url_data['clicks']}\n"
            if url_data.get("description"):
                output += f"Description: {url_data['description']}\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error expanding URL: {str(e)}")

    def _list_urls(self) -> ToolResult:
        """List all shortened URLs."""
        try:
            if not self.data["urls"]:
                return ToolResult(output="No shortened URLs found.")

            output = f"Shortened URLs ({len(self.data['urls'])} total):\n"
            output += "=" * 60 + "\n"

            for short_code, url_data in self.data["urls"].items():
                short_url = f"{self.base_url}{short_code}"
                created = datetime.fromisoformat(url_data["created_at"]).strftime('%Y-%m-%d %H:%M')

                output += f"Code: {short_code}\n"
                output += f"Short URL: {short_url}\n"
                output += f"Original: {url_data['original_url'][:50]}{'...' if len(url_data['original_url']) > 50 else ''}\n"
                output += f"Created: {created}\n"
                output += f"Clicks: {url_data['clicks']}\n"

                if url_data.get("description"):
                    output += f"Description: {url_data['description']}\n"

                if url_data.get("expiry_date"):
                    expiry = datetime.fromisoformat(url_data["expiry_date"]).strftime('%Y-%m-%d %H:%M')
                    output += f"Expires: {expiry}\n"

                output += "-" * 40 + "\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error listing URLs: {str(e)}")

    def _get_stats(self, short_code: Optional[str]) -> ToolResult:
        """Get statistics for a short URL."""
        try:
            if not short_code:
                return ToolResult(error="Short code is required for stats")

            if short_code not in self.data["urls"]:
                return ToolResult(error=f"Short code '{short_code}' not found")

            url_data = self.data["urls"][short_code]
            stats_data = self.data["stats"][short_code]

            output = f"Statistics for {short_code}:\n"
            output += "=" * 40 + "\n"
            output += f"Original URL: {url_data['original_url']}\n"
            output += f"Short URL: {self.base_url}{short_code}\n"
            output += f"Created: {url_data['created_at']}\n"
            output += f"Total Clicks: {stats_data['total_clicks']}\n"

            if url_data.get("description"):
                output += f"Description: {url_data['description']}\n"

            # Daily clicks (last 7 days)
            if stats_data["daily_clicks"]:
                output += "\nDaily Clicks (last 7 days):\n"
                sorted_days = sorted(stats_data["daily_clicks"].items())[-7:]
                for day, clicks in sorted_days:
                    output += f"  {day}: {clicks} clicks\n"

            # Top referrers
            if stats_data["referrers"]:
                output += "\nTop Referrers:\n"
                sorted_referrers = sorted(stats_data["referrers"].items(),
                                        key=lambda x: x[1], reverse=True)[:5]
                for referrer, count in sorted_referrers:
                    output += f"  {referrer}: {count} clicks\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error getting stats: {str(e)}")

    def _delete_url(self, short_code: Optional[str]) -> ToolResult:
        """Delete a short URL."""
        try:
            if not short_code:
                return ToolResult(error="Short code is required for deletion")

            if short_code not in self.data["urls"]:
                return ToolResult(error=f"Short code '{short_code}' not found")

            url_data = self.data["urls"][short_code]
            original_url = url_data["original_url"]

            # Remove from data
            del self.data["urls"][short_code]
            if short_code in self.data["stats"]:
                del self.data["stats"][short_code]

            self._save_data()

            output = f"Short URL deleted successfully!\n"
            output += f"Short Code: {short_code}\n"
            output += f"Original URL: {original_url}\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error deleting URL: {str(e)}")

    def _validate_url(self, url: Optional[str]) -> ToolResult:
        """Validate if URL is accessible."""
        try:
            if not url:
                return ToolResult(error="URL is required for validation")

            if not self._is_valid_url(url):
                return ToolResult(error="Invalid URL format")

            # Try to access the URL
            try:
                response = requests.head(url, timeout=10, allow_redirects=True)
                status_code = response.status_code

                if 200 <= status_code < 300:
                    status = "✓ Accessible"
                elif 300 <= status_code < 400:
                    status = "↻ Redirects"
                elif 400 <= status_code < 500:
                    status = "✗ Client Error"
                elif 500 <= status_code < 600:
                    status = "✗ Server Error"
                else:
                    status = "? Unknown"

                # Get additional info
                content_type = response.headers.get('content-type', 'Unknown')
                content_length = response.headers.get('content-length', 'Unknown')
                server = response.headers.get('server', 'Unknown')

                output = f"URL Validation Results:\n"
                output += "=" * 30 + "\n"
                output += f"URL: {url}\n"
                output += f"Status: {status} ({status_code})\n"
                output += f"Content Type: {content_type}\n"
                output += f"Content Length: {content_length}\n"
                output += f"Server: {server}\n"

                if response.url != url:
                    output += f"Final URL: {response.url}\n"

            except requests.RequestException as e:
                output = f"URL Validation Results:\n"
                output += "=" * 30 + "\n"
                output += f"URL: {url}\n"
                output += f"Status: ✗ Not Accessible\n"
                output += f"Error: {str(e)}\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error validating URL: {str(e)}")
