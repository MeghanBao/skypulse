"""
SkyPulse Price Intelligence Engine
AI-powered price prediction and recommendations
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class Recommendation(Enum):
    BUY_NOW = "buy_now"
    WAIT = "wait"
    NEUTRAL = "neutral"

@dataclass
class PricePoint:
    date: datetime
    price: float
    currency: str = "EUR"

@dataclass 
class PricePrediction:
    current_price: float
    predicted_low: float
    predicted_high: float
    recommendation: Recommendation
    confidence: float
    reasoning: str

class PriceIntelligence:
    def __init__(self):
        self.price_history: Dict[str, List[PricePoint]] = {}
        self.min_history_for_prediction = 5
    
    def add_price(self, route: str, price: float, date: datetime = None):
        \"\"\"Add a price point to history\"\"\"
        if route not in self.price_history:
            self.price_history[route] = []
        
        point = PricePoint(
            date=date or datetime.now(),
            price=price
        )
        self.price_history[route].append(point)
        
        # Keep only last 90 days
        cutoff = datetime.now() - timedelta(days=90)
        self.price_history[route] = [
            p for p in self.price_history[route] 
            if p.date > cutoff
        ]
    
    def get_trend(self, route: str) -> str:
        \"\"\"Get price trend (rising/falling/stable)\"\"\"
        if route not in self.price_history:
            return "unknown"
        
        history = self.price_history[route]
        if len(history) < 2:
            return "unknown"
        
        # Simple moving average comparison
        recent = history[-3:]
        older = history[-6:-3] if len(history) >= 6 else history[:-3]
        
        if not older:
            return "unknown"
        
        recent_avg = sum(p.price for p in recent) / len(recent)
        older_avg = sum(p.price for p in older) / len(older)
        
        diff_percent = ((recent_avg - older_avg) / older_avg) * 100
        
        if diff_percent > 5:
            return "rising"
        elif diff_percent < -5:
            return "falling"
        else:
            return "stable"
    
    def predict_price(self, route: str) -> Optional[PricePrediction]:
        \"\"\"Predict best price and recommendation\"\"\"
        if route not in self.price_history:
            return None
        
        history = self.price_history[route]
        if len(history) < self.min_history_for_prediction:
            return None
        
        prices = [p.price for p in history]
        current_price = prices[-1]
        
        # Calculate statistics
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        
        # Simple prediction logic
        trend = self.get_trend(route)
        
        if trend == "falling":
            predicted_low = current_price * 0.9
            recommendation = Recommendation.WAIT
            reasoning = "Prices are trending downward. Consider waiting for a better deal."
            confidence = 0.75
        elif trend == "rising":
            predicted_low = current_price
            recommendation = Recommendation.BUY_NOW
            reasoning = "Prices are rising. Book now to secure the current rate."
            confidence = 0.75
        else:
            # Stable - check if current price is below average
            if current_price < avg_price * 0.9:
                predicted_low = current_price
                recommendation = Recommendation.BUY_NOW
                reasoning = "Current price is below average - good time to buy!"
                confidence = 0.65
            elif current_price > avg_price * 1.1:
                predicted_low = avg_price * 0.9
                recommendation = Recommendation.WAIT
                reasoning = "Price is above average. Consider waiting."
                confidence = 0.65
            else:
                predicted_low = min_price
                recommendation = Recommendation.NEUTRAL
                reasoning = "Price is close to average. No strong signal."
                confidence = 0.5
        
        return PricePrediction(
            current_price=current_price,
            predicted_low=predicted_low,
            predicted_high=max_price,
            recommendation=recommendation,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def should_buy(self, route: str, target_price: float) -> Dict:
        \"\"\"Determine if should buy now based on target price\"\"\"
        prediction = self.predict_price(route)
        
        if not prediction:
            return {
                "should_buy": None,
                "reason": "Not enough data for prediction"
            }
        
        if prediction.current_price <= target_price:
            return {
                "should_buy": True,
                "reason": f"Current price (€{prediction.current_price}) is below your target (€{target_price})"
            }
        
        if prediction.recommendation == Recommendation.BUY_NOW:
            return {
                "should_buy": True,
                "reason": prediction.reasoning
            }
        
        return {
            "should_buy": False,
            "reason": prediction.reasoning
        }

# Example usage
if __name__ == "__main__":
    engine = PriceIntelligence()
    
    # Add sample price history
    route = "Berlin-Paris"
    for i in range(10):
        price = 100 + (i * 5)  # Rising prices
        engine.add_price(route, price)
    
    # Get prediction
    prediction = engine.predict_price(route)
    if prediction:
        print(f"Current: €{prediction.current_price}")
        print(f"Recommendation: {prediction.recommendation.value}")
        print(f"Reasoning: {prediction.reasoning}")
    
    # Check if should buy
    should_buy = engine.should_buy(route, 120)
    print(f"\nShould buy under €120: {should_buy}")
