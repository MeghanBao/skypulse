"""
SkyPulse External API Integrations
Kayak, Google Flights, Amadeus API connectors
"""
import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from dataclasses import dataclass
import requests

logger = logging.getLogger(__name__)

# Configuration
KAYAK_API_KEY = os.getenv('KAYAK_API_KEY', '')
AMADEUS_API_KEY = os.getenv('AMADEUS_API_KEY', '')
AMADEUS_API_SECRET = os.getenv('AMADEUS_API_SECRET', '')

@dataclass
class FlightOffer:
    origin: str
    destination: str
    departure: str
    return_date: Optional[str]
    price: float
    currency: str
    airline: str
    source: str
    booking_link: str

class KayakConnector:
    """Kayak API connector for flight search"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or KAYAK_API_KEY
        self.base_url = "https://api.kayak.com"
    
    def search_flights(self, origin: str, destination: str, departure: str, 
                      return_date: str = None, passengers: int = 1) -> List[FlightOffer]:
        """
        Search flights via Kayak API
        Note: In production, use official Kayak API or partner network
        """
        logger.info(f"Kayak search: {origin} -> {destination}")
        
        offers = []
        
        # Sample response (in production, parse real API response)
        # Kayak doesn't have public API, using sample data
        sample_offer = FlightOffer(
            origin=origin,
            destination=destination,
            departure=departure,
            return_date=return_date,
            price=149.99,
            currency="EUR",
            airline="Multiple",
            source="Kayak",
            booking_link=f"https://www.kayak.com/flights/{origin}-{destination}"
        )
        offers.append(sample_offer)
        
        return offers
    
    def get_price_alerts(self, origin: str, destination: str) -> Dict:
        """Get price alert data"""
        return {
            "current_price": 149.99,
            "lowest_price": 89.00,
            "highest_price": 450.00,
            "average_price": 180.00,
            "trend": "stable",
            "best_time_to_buy": "now"
        }

class GoogleFlightsConnector:
    """Google Flights integration"""
    
    def __init__(self):
        self.base_url = "https://www.googleapis.com/qpxExpress/v1"
        # Note: Google Flights API was deprecated, using scraping/alternatives
    
    def search_flights(self, origin: str, destination: str, 
                      departure: str, return_date: str = None) -> List[FlightOffer]:
        """
        Search flights (using alternative approach)
        Note: Google Flights API is no longer publicly available
        """
        logger.info(f"Google Flights search: {origin} -> {destination}")
        
        offers = []
        
        # Sample for demonstration
        offer = FlightOffer(
            origin=origin,
            destination=destination,
            departure=departure,
            return_date=return_date,
            price=159.00,
            currency="EUR",
            airline="Various",
            source="Google Flights",
            booking_link=f"https://www.google.com/flights?hl=en#flt={origin}.{destination}"
        )
        offers.append(offer)
        
        return offers

class AmadeusConnector:
    """Amadeus API - Official travel API"""
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key or AMADEUS_API_KEY
        self.api_secret = api_secret or AMADEUS_API_SECRET
        self.base_url = "https://api.amadeus.com"
        self.access_token = None
    
    def authenticate(self) -> bool:
        """Get OAuth access token"""
        if not self.api_key or not self.api_secret:
            logger.warning("Amadeus API credentials not configured")
            return False
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/security/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.api_key,
                    "client_secret": self.api_secret
                }
            )
            data = response.json()
            self.access_token = data.get("access_token")
            return self.access_token is not None
        except Exception as e:
            logger.error(f"Amadeus auth failed: {e}")
            return False
    
    def search_flights(self, origin: str, destination: str,
                     departure_date: str, return_date: str = None,
                     adults: int = 1) -> List[FlightOffer]:
        """Search flights via Amadeus"""
        if not self.access_token and not self.authenticate():
            return []
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            params = {
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDate": departure_date,
                "adults": adults,
                "currencyCode": "EUR",
                "max": 10
            }
            
            response = requests.get(
                f"{self.base_url}/v2/shopping/flight-offers",
                headers=headers,
                params=params
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            offers = []
            
            for offer in data.get("data", [])[:5]:
                first_segment = offer["itineraries"][0]["segments"][0]
                price = float(offer["price"]["total"])
                
                flight_offer = FlightOffer(
                    origin=first_segment["departure"]["iataCode"],
                    destination=first_segment["arrival"]["iataCode"],
                    departure=first_segment["departure"]["at"][:10],
                    return_date=offer["itineraries"][1]["segments"][0]["departure"]["at"][:10] if len(offer["itineraries"]) > 1 else None,
                    price=price,
                    currency=offer["price"]["currency"],
                    airline=first_segment["carrierCode"],
                    source="Amadeus",
                    booking_link=""  # Would need booking API
                )
                offers.append(flight_offer)
            
            return offers
            
        except Exception as e:
            logger.error(f"Amadeus search failed: {e}")
            return []
    
    def get_airport_info(self, iata_code: str) -> Optional[Dict]:
        """Get airport information"""
        if not self.access_token and not self.authenticate():
            return None
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{self.base_url}/v1/reference-data/locations/{iata_code}",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Amadeus airport info failed: {e}")
            return None

class SkyscannerConnector:
    """Skyscanner API connector"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('SKYSCANNER_API_KEY', '')
        self.base_url = "https://partners.api.skyscanner.net"
    
    def search_flights(self, origin: str, destination: str,
                      departure: str, return_date: str = None) -> List[FlightOffer]:
        """Search flights via Skyscanner"""
        logger.info(f"Skyscanner search: {origin} -> {destination}")
        
        # Sample response
        offers = [
            FlightOffer(
                origin=origin,
                destination=destination,
                departure=departure,
                return_date=return_date,
                price=129.00,
                currency="EUR",
                airline="Various",
                source="Skyscanner",
                booking_link=f"https://www.skyscanner.com/transport/flights/{origin}/{destination}"
            )
        ]
        
        return offers

# Factory function
def get_all_connectors() -> Dict:
    """Get all available API connectors"""
    return {
        "kayak": KayakConnector(),
        "google_flights": GoogleFlightsConnector(),
        "amadeus": AmadeusConnector(),
        "skyscanner": SkyscannerConnector()
    }

# Example usage
if __name__ == "__main__":
    connectors = get_all_connectors()
    
    for name, conn in connectors.items():
        print(f"\n{name.upper()} Results:")
        deals = conn.search_flights("BER", "CDG", "2026-03-15", "2026-03-22")
        for deal in deals:
            print(f"  €{deal.price} - {deal.origin} -> {deal.destination} ({deal.airline})")
