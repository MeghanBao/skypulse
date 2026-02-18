"""
SkyPulse WhatsApp Notification Service
Send flight deals via WhatsApp Business API
"""
import os
import json
import logging
from datetime import datetime
from typing import Optional, List
import requests

# Configuration
WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN', 'YOUR_WHATSAPP_TOKEN')
WHATSAPP_PHONE_ID = os.getenv('WHATSAPP_PHONE_ID', 'YOUR_PHONE_ID')
WHATSAPP_BUSINESS_ID = os.getenv('WHATSAPP_BUSINESS_ID', 'YOUR_BUSINESS_ID')

logger = logging.getLogger(__name__)

class WhatsAppNotifier:
    def __init__(self, token: str = None, phone_id: str = None):
        self.token = token or WHATSAPP_TOKEN
        self.phone_id = phone_id or WHATSAPP_PHONE_ID
        self.business_id = WHATSAPP_BUSINESS_ID
        self.api_url = f"https://graph.facebook.com/v18.0/{self.phone_id}/messages"
    
    def send_message(self, to: str, message: str) -> dict:
        \"\"\"Send a text message via WhatsApp\"\"\"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Message sent to {to}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send message: {e}")
            return {"error": str(e)}
    
    def send_flight_deal(self, to: str, deal: dict) -> dict:
        \"\"\"Send a formatted flight deal message\"\"\"
        message = self.format_deal_message(deal)
        return self.send_message(to, message)
    
    def format_deal_message(self, deal: dict) -> str:
        \"\"\"Format a flight deal as a WhatsApp message\"\"\"
        template = f\"\"\"
✈️ Flight Deal Alert!

📍 {deal.get('origin', '???')} → {deal.get('destination', '???')}
💰 Price: {deal.get('price', 'N/A')}
📅 Dates: {deal.get('departure', 'TBC')} - {deal.get('return', 'TBC')}
✈️ Airline: {deal.get('airline', 'N/A')}

🔗 {deal.get('booking_link', '#')}

Sent via SkyPulse
\"\"\"
        return template.strip()
    
    def send_interactive_deal(self, to: str, deal: dict) -> dict:
        \"\"\"Send deal with interactive buttons\"\"\"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "flow",
                "header": {
                    "type": "text",
                    "text": f\"✈️ {deal.get('origin', '???')} → {deal.get('destination', '???')}\"
                },
                "body": {
                    "text": f\"💰 {deal.get('price', 'N/A')}\n📅 {deal.get('departure', 'TBC')}\"
                },
                "footer": {
                    "text": "SkyPulse - Smart Flight Deals"
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": "book_deal_1",
                                "title": "Book Now"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "save_deal_1",
                                "title": "Save for Later"
                            }
                        }
                    ]
                }
            }
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send interactive message: {e}")
            return {"error": str(e)}

# Example usage
if __name__ == "__main__":
    notifier = WhatsAppNotifier()
    
    # Test deal
    test_deal = {
        "origin": "Berlin",
        "destination": "Paris",
        "price": "€89",
        "departure": "2026-03-15",
        "return": "2026-03-22",
        "airline": "EasyJet",
        "booking_link": "https://example.com/booking"
    }
    
    # Send test (would need real phone number)
    # result = notifier.send_flight_deal("+1234567890", test_deal)
    print("WhatsApp notification service ready!")
