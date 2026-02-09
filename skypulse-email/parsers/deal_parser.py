"""
SkyPulse 2.0 - Deal Parser
Extracts flight deal information from promotional emails.
"""

import logging
from typing import Optional, Dict
from datetime import datetime
from bs4 import BeautifulSoup
import re

from llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class DealParser:
    """Parses flight deals from promotional emails"""
    
    def __init__(self):
        self.llm_client = OllamaClient()
    
    def parse_email(self, email_data: Dict) -> Optional[Dict]:
        """
        Parse a flight deal from an email.
        
        Args:
            email_data: Dictionary with 'subject', 'sender', 'body', 'id'
        
        Returns:
            Dictionary with parsed deal information or None if no deal found
        """
        try:
            subject = email_data.get("subject", "")
            body = email_data.get("body", "")
            sender = email_data.get("sender", "")
            email_id = email_data.get("id", "")
            
            logger.info(f"Parsing email: {subject[:50]}...")
            
            # Clean HTML from body
            clean_body = self._clean_html(body)
            
            # Use LLM to extract deal information
            deal_info = self.llm_client.parse_deal_email(subject, clean_body)
            
            if not deal_info:
                logger.warning(f"No deal information extracted from email: {subject}")
                return None
            
            # Enrich with metadata
            deal_info["source"] = self._identify_source(sender)
            deal_info["source_email_id"] = email_id
            deal_info["raw_content"] = body[:5000]  # Store first 5000 chars
            deal_info["parsed_at"] = datetime.utcnow().isoformat()
            
            # Validate required fields
            if not self._validate_deal(deal_info):
                logger.warning(f"Deal validation failed for: {subject}")
                return None
            
            logger.info(f"✅ Parsed deal: {deal_info.get('route', 'Unknown')} - ${deal_info.get('price', 'N/A')}")
            return deal_info
            
        except Exception as e:
            logger.error(f"Error parsing email: {e}")
            return None
    
    def _clean_html(self, html_content: str) -> str:
        """Remove HTML tags and extract plain text"""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
        except:
            # If HTML parsing fails, return original content
            return html_content
    
    def _identify_source(self, sender_email: str) -> str:
        """Identify the source of the email"""
        sender_lower = sender_email.lower()
        
        if "scottscheapflights" in sender_lower or "going.com" in sender_lower:
            return "scott_cheap_flights"
        elif "secretflying" in sender_lower:
            return "secret_flying"
        elif "theflightdeal" in sender_lower:
            return "the_flight_deal"
        elif "google" in sender_lower:
            return "google_flights"
        else:
            return "unknown"
    
    def _validate_deal(self, deal_info: Dict) -> bool:
        """Validate that deal has required fields"""
        required_fields = ["price", "departure_city", "arrival_city"]
        
        for field in required_fields:
            if not deal_info.get(field):
                logger.debug(f"Missing required field: {field}")
                return False
        
        # Validate price is a number
        try:
            price = float(deal_info["price"])
            if price <= 0 or price > 50000:  # Sanity check
                logger.debug(f"Invalid price: {price}")
                return False
        except (ValueError, TypeError):
            logger.debug(f"Invalid price format: {deal_info.get('price')}")
            return False
        
        return True
    
    def extract_urls(self, text: str) -> list:
        """Extract URLs from text"""
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, text)
        return urls


if __name__ == "__main__":
    # Test deal parser
    parser = DealParser()
    
    test_email = {
        "id": "test123",
        "subject": "Flash Sale: NYC to Tokyo $649",
        "sender": "deals@scottscheapflights.com",
        "body": """
        <html>
        <body>
            <h1>Amazing Deal Alert!</h1>
            <p>Fly from New York to Tokyo for just $649 roundtrip on Japan Airlines.</p>
            <p>Travel dates: April 15-22, 2026</p>
            <p>Book now at https://example.com/book</p>
        </body>
        </html>
        """
    }
    
    deal = parser.parse_email(test_email)
    if deal:
        print(f"✅ Parsed deal: {deal}")
    else:
        print("❌ Failed to parse deal")
