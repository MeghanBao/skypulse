"""
SkyPulse 2.0 - Ollama LLM Client
Local LLM integration for parsing emails and subscriptions.
"""

import requests
import json
import logging
from typing import Dict, Optional

from config import Config

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for Ollama local LLM"""
    
    def __init__(self):
        self.base_url = Config.OLLAMA_BASE_URL
        self.model = Config.OLLAMA_MODEL
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """
        Generate text using Ollama.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
        
        Returns:
            Generated text or None if failed
        """
        try:
            url = f"{self.base_url}/api/generate"
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return None
    
    def parse_subscription(self, user_prompt: str) -> Optional[Dict]:
        """
        Parse user's natural language subscription request.
        
        Args:
            user_prompt: User's travel request (e.g., "Flights to Tokyo in April under $800")
        
        Returns:
            Dictionary with parsed fields or None if failed
        """
        system_prompt = """You are a flight subscription parser. Extract the following fields from the user's request:
- origin: Departure city/airport
- destination: Arrival city/airport
- max_price: Maximum price (number only)
- start_date: Start date or month
- end_date: End date or month

Return ONLY a JSON object with these fields. If a field is not mentioned, use null."""
        
        prompt = f"Parse this flight request: \"{user_prompt}\""
        
        response = self.generate(prompt, system_prompt)
        
        if not response:
            return None
        
        try:
            # Extract JSON from response
            # Sometimes LLM adds extra text, so we try to find JSON
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                parsed = json.loads(json_str)
                logger.info(f"Parsed subscription: {parsed}")
                return parsed
            else:
                logger.error("No JSON found in Ollama response")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Ollama JSON response: {e}")
            logger.debug(f"Response was: {response}")
            return None
    
    def parse_deal_email(self, email_subject: str, email_body: str) -> Optional[Dict]:
        """
        Parse flight deal from promotional email.
        
        Args:
            email_subject: Email subject line
            email_body: Email body content
        
        Returns:
            Dictionary with deal details or None if failed
        """
        system_prompt = """You are a flight deal extractor. Extract the following from promotional emails:
- airline: Airline name
- route: Flight route (e.g., "NYC → Tokyo")
- departure_city: Departure city
- arrival_city: Arrival city
- price: Price (number only, no currency symbol)
- currency: Currency code (USD, EUR, etc.)
- departure_date: Departure date if mentioned
- return_date: Return date if mentioned
- booking_link: URL to book the flight

Return ONLY a JSON object. Use null for missing fields."""
        
        prompt = f"""Subject: {email_subject}

Body:
{email_body[:1000]}

Extract the flight deal information."""
        
        response = self.generate(prompt, system_prompt)
        
        if not response:
            return None
        
        try:
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                parsed = json.loads(json_str)
                logger.info(f"Parsed deal: {parsed.get('route', 'Unknown')} - ${parsed.get('price', 'N/A')}")
                return parsed
            else:
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse deal JSON: {e}")
            return None
    
    def check_connection(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            url = f"{self.base_url}/api/tags"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            logger.info("Ollama connection successful")
            return True
        except Exception as e:
            logger.error(f"Ollama connection failed: {e}")
            return False


if __name__ == "__main__":
    # Test Ollama client
    client = OllamaClient()
    
    if client.check_connection():
        # Test subscription parsing
        test_prompt = "I want to fly to Tokyo in April for under $800"
        result = client.parse_subscription(test_prompt)
        print(f"✅ Parsed subscription: {result}")
        
        # Test deal parsing
        test_subject = "Flash Sale: NYC to Tokyo $649"
        test_body = "Amazing deal! Fly from New York to Tokyo for just $649 roundtrip on Japan Airlines. Travel dates: April 15-22, 2026. Book now at https://example.com/book"
        deal = client.parse_deal_email(test_subject, test_body)
        print(f"✅ Parsed deal: {deal}")
    else:
        print("❌ Ollama not running. Start it with: ollama serve")
