"""
SkyPulse Price Intelligence - Enhanced Version
Advanced price prediction with seasonal patterns and alerts
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
import statistics

logger = logging.getLogger(__name__)

class Recommendation(Enum):
    BUY_NOW = "buy_now"
    WAIT = "wait"
    NEUTRAL = "neutral"

class Season(Enum):
    WINTER = "winter"
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    HOLIDAY = "holiday"
    OFF_PEAK = "off_peak"

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

@dataclass
class SeasonalPattern:
    season: Season
    average_price: float
    min_price: float
    max_price: float
    price_volatility: float
    sample_count: int

@dataclass
class PriceAlert:
    route: str
    target_price: float
    created_at: datetime
    triggered: bool = False

class PriceIntelligence:
    """Enhanced price intelligence with seasonal analysis"""
    
    def __init__(self):
        self.price_history: Dict[str, List[PricePoint]] = {}
        self.alerts: Dict[str, List[PriceAlert]] = {}
        self.min_history_for_prediction = 5
        
        # Seasonal patterns cache
        self.seasonal_patterns: Dict[str, Dict[Season, SeasonalPattern]] = {}
    
    # ============ PRICE HISTORY ============
    
    def add_price(self, route: str, price: float, date: datetime = None):
        """Add a price point to history"""
        if route not in self.price_history:
            self.price_history[route] = []
        
        point = PricePoint(date=date or datetime.now(), price=price)
        self.price_history[route].append(point)
        
        # Keep only last 365 days
        cutoff = datetime.now() - timedelta(days=365)
        self.price_history[route] = [p for p in self.price_history[route] if p.date > cutoff]
        
        # Check alerts
        self._check_alerts(route, price)
    
    def get_price_history(self, route: str, days: int = 30) -> List[PricePoint]:
        """Get price history for a route"""
        if route not in self.price_history:
            return []
        
        cutoff = datetime.now() - timedelta(days=days)
        return [p for p in self.price_history[route] if p.date > cutoff]
    
    # ============ SEASONAL PATTERNS ============
    
    def _get_season(self, date: datetime) -> Season:
        """Determine season from date"""
        month = date.month
        
        # Holiday seasons
        if month in [12, 1]:  # Christmas/New Year
            return Season.HOLIDAY
        if month in [7, 8]:   # Summer vacation
            return Season.SUMMER
        
        # Regular seasons
        if month in [3, 4, 5]:
            return Season.SPRING
        elif month in [9, 10, 11]:
            return Season.AUTUMN
        elif month in [12]:
            return Season.WINTER
        elif month in [1, 2]:
            return Season.WINTER
        
        return Season.OFF_PEAK
    
    def analyze_seasonal_patterns(self, route: str) -> Dict[Season, SeasonalPattern]:
        """Analyze seasonal patterns for a route"""
        if route not in self.price_history:
            return {}
        
        history = self.price_history[route]
        if len(history) < 10:
            return {}
        
        # Group by season
        seasonal_data: Dict[Season, List[float]] = {s: [] for s in Season}
        
        for point in history:
            season = self._get_season(point.date)
            seasonal_data[season].append(point.price)
        
        patterns = {}
        for season, prices in seasonal_data.items():
            if len(prices) >= 3:
                patterns[season] = SeasonalPattern(
                    season=season,
                    average_price=statistics.mean(prices),
                    min_price=min(prices),
                    max_price=max(prices),
                    price_volatility=self._calculate_volatility(prices),
                    sample_count=len(prices)
                )
        
        self.seasonal_patterns[route] = patterns
        return patterns
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calculate price volatility (coefficient of variation)"""
        if len(prices) < 2:
            return 0.0
        
        mean = statistics.mean(prices)
        if mean == 0:
            return 0.0
        
        stdev = statistics.stdev(prices) if len(prices) > 1 else 0
        return (stdev / mean) * 100  # Percentage
    
    def get_seasonal_recommendation(self, route: str, travel_date: datetime) -> Dict:
        """Get recommendation based on seasonal patterns"""
        if route not in self.seasonal_patterns:
            self.analyze_seasonal_patterns(route)
        
        patterns = self.seasonal_patterns.get(route, {})
        target_season = self._get_season(travel_date)
        
        if target_season not in patterns:
            return {"recommendation": "neutral", "reason": "Not enough seasonal data"}
        
        pattern = patterns[target_season]
        current_price = self.get_current_price(route)
        
        # Calculate how good the current price is compared to seasonal average
        if current_price < pattern.average_price * 0.8:
            return {
                "recommendation": "buy_now",
                "reason": f"Current price is {((1 - current_price/pattern.average_price)*100):.0f}% below {target_season.value} average",
                "seasonal_avg": pattern.average_price,
                "volatility": pattern.price_volatility
            }
        elif current_price > pattern.average_price * 1.2:
            return {
                "recommendation": "wait",
                "reason": f"Current price is {((current_price/pattern.average_price-1)*100):.0f}% above {target_season.value} average",
                "seasonal_avg": pattern.average_price,
                "volatility": pattern.price_volatility
            }
        
        return {
            "recommendation": "neutral",
            "reason": f"Price is near {target_season.value} average",
            "seasonal_avg": pattern.average_price,
            "volatility": pattern.price_volatility
        }
    
    # ============ TRENDS ============
    
    def get_trend(self, route: str) -> str:
        """Get price trend (rising/falling/stable)"""
        if route not in self.price_history:
            return "unknown"
        
        history = self.price_history[route]
        if len(history) < 2:
            return "unknown"
        
        # Compare recent average to older average
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
        return "stable"
    
    # ============ PREDICTIONS ============
    
    def get_current_price(self, route: str) -> Optional[float]:
        """Get most recent price"""
        if route not in self.price_history or not self.price_history[route]:
            return None
        return self.price_history[route][-1].price
    
    def predict_price(self, route: str) -> Optional[PricePrediction]:
        """Predict best price and recommendation"""
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
        
        # Trend-based prediction
        trend = self.get_trend(route)
        
        if trend == "falling":
            predicted_low = current_price * 0.85
            recommendation = Recommendation.WAIT
            reasoning = "Prices are trending downward. Consider waiting."
            confidence = 0.75
        elif trend == "rising":
            predicted_low = current_price
            recommendation = Recommendation.BUY_NOW
            reasoning = "Prices are rising. Book now to secure current rate."
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
    
    # ============ ALERTS ============
    
    def create_alert(self, route: str, target_price: float) -> PriceAlert:
        """Create a price alert"""
        if route not in self.alerts:
            self.alerts[route] = []
        
        alert = PriceAlert(
            route=route,
            target_price=target_price,
            created_at=datetime.now()
        )
        self.alerts[route].append(alert)
        return alert
    
    def _check_alerts(self, route: str, current_price: float):
        """Check if any alerts should be triggered"""
        if route not in self.alerts:
            return
        
        for alert in self.alerts[route]:
            if not alert.triggered and current_price <= alert.target_price:
                alert.triggered = True
                logger.info(f"Alert triggered: {route} reached €{current_price}")
    
    def get_active_alerts(self, route: str = None) -> List[PriceAlert]:
        """Get active (non-triggered) alerts"""
        if route:
            return [a for a in self.alerts.get(route, []) if not a.triggered]
        
        all_alerts = []
        for route_alerts in self.alerts.values():
            all_alerts.extend([a for a in route_alerts if not a.triggered])
        return all_alerts
    
    def should_buy(self, route: str, target_price: float = None) -> Dict:
        """Determine if should buy now"""
        prediction = self.predict_price(route)
        
        if not prediction:
            return {"should_buy": None, "reason": "Not enough data for prediction"}
        
        # Check user target price first
        if target_price and prediction.current_price <= target_price:
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
    
    # ============ STATISTICS ============
    
    def get_route_statistics(self, route: str) -> Dict:
        """Get comprehensive statistics for a route"""
        if route not in self.price_history:
            return {}
        
        prices = [p.price for p in self.price_history[route]]
        
        return {
            "current_price": prices[-1] if prices else None,
            "average_price": statistics.mean(prices) if prices else None,
            "min_price": min(prices) if prices else None,
            "max_price": max(prices) if prices else None,
            "median_price": statistics.median(prices) if prices else None,
            "volatility": self._calculate_volatility(prices),
            "sample_count": len(prices),
            "trend": self.get_trend(route),
            "last_updated": self.price_history[route][-1].date.isoformat() if self.price_history[route] else None
        }

# Example usage
if __name__ == "__main__":
    engine = PriceIntelligence()
    
    # Add sample data
    route = "Berlin-Paris"
    for i in range(30):
        price = 100 + (i % 10) * 5  # Varied prices
        date = datetime.now() - timedelta(days=30-i)
        engine.add_price(route, price, date)
    
    # Get prediction
    prediction = engine.predict_price(route)
    if prediction:
        print(f"Current: €{prediction.current_price}")
        print(f"Prediction: {prediction.recommendation.value}")
        print(f"Reasoning: {prediction.reasoning}")
    
    # Seasonal analysis
    patterns = engine.analyze_seasonal_patterns(route)
    print(f"\nSeasonal patterns: {len(patterns)} seasons")
    
    # Create alert
    alert = engine.create_alert(route, 95)
    print(f"\nAlert created: €{alert.target_price}")
    
    # Should buy?
    should_buy = engine.should_buy(route, 120)
    print(f"\nShould buy under €120: {should_buy}")
    
    # Statistics
    stats = engine.get_route_statistics(route)
    print(f"\nStatistics: {stats}")
