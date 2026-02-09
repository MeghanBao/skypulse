"""
SkyPulse 2.0 - Deal Matcher
Matches flight deals to user subscriptions with AI-powered scoring.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from models.schemas import Subscription, Deal, DealMatch, User
from llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class DealMatcher:
    """Matches deals to subscriptions and generates AI summaries"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.llm_client = OllamaClient()
    
    def match_deal_to_subscriptions(self, deal: Deal) -> List[DealMatch]:
        """
        Find matching subscriptions for a deal and create DealMatch records.
        
        Args:
            deal: Deal object from database
        
        Returns:
            List of created DealMatch objects
        """
        # Get all active subscriptions
        active_subscriptions = self.db.query(Subscription).filter(
            Subscription.is_active == True
        ).all()
        
        logger.info(f"Matching deal {deal.route} against {len(active_subscriptions)} subscriptions")
        
        matches = []
        for subscription in active_subscriptions:
            score = self._calculate_match_score(deal, subscription)
            
            if score >= 50:  # Threshold for creating a match
                # Generate AI summary
                ai_summary = self._generate_ai_summary(deal, subscription)
                
                # Create DealMatch
                deal_match = DealMatch(
                    subscription_id=subscription.id,
                    deal_id=deal.id,
                    match_score=score,
                    ai_summary=ai_summary,
                    created_at=datetime.utcnow()
                )
                
                self.db.add(deal_match)
                matches.append(deal_match)
                
                logger.info(f"✅ Match created: {subscription.prompt[:50]}... (score: {score})")
        
        if matches:
            self.db.commit()
            logger.info(f"Created {len(matches)} matches for deal: {deal.route}")
        else:
            logger.info(f"No matches found for deal: {deal.route}")
        
        return matches
    
    def _calculate_match_score(self, deal: Deal, subscription: Subscription) -> float:
        """
        Calculate match score between a deal and subscription.
        
        Score components:
        - Destination match: 40 points
        - Price match: 30 points
        - Date match: 20 points
        - Origin match: 10 points
        
        Returns:
            Score from 0-100
        """
        score = 0.0
        
        # 1. Destination matching (40 points)
        if subscription.destination:
            dest_score = self._match_location(
                deal.arrival_city,
                subscription.destination
            )
            score += dest_score * 40
        else:
            score += 20  # Partial score if no destination specified
        
        # 2. Price matching (30 points)
        if subscription.max_price:
            if deal.price <= subscription.max_price:
                # Better deals get higher scores
                price_ratio = deal.price / subscription.max_price
                score += (1 - price_ratio * 0.5) * 30  # Max 30 points for very cheap
            else:
                # Slightly over budget still gets some points
                overage = (deal.price - subscription.max_price) / subscription.max_price
                if overage < 0.2:  # Within 20% over budget
                    score += 15 * (1 - overage / 0.2)
        else:
            score += 15  # Partial score if no price specified
        
        # 3. Date matching (20 points)
        if subscription.start_date or subscription.end_date:
            date_score = self._match_dates(
                deal.departure_date,
                subscription.start_date,
                subscription.end_date
            )
            score += date_score * 20
        else:
            score += 10  # Partial score if no dates specified
        
        # 4. Origin matching (10 points)
        if subscription.origin:
            origin_score = self._match_location(
                deal.departure_city,
                subscription.origin
            )
            score += origin_score * 10
        else:
            score += 5  # Partial score if no origin specified
        
        return min(score, 100)  # Cap at 100
    
    def _match_location(self, location1: str, location2: str) -> float:
        """
        Match two location strings (city names, airport codes, etc.)
        
        Returns:
            Score from 0.0 to 1.0
        """
        if not location1 or not location2:
            return 0.0
        
        loc1 = location1.lower().strip()
        loc2 = location2.lower().strip()
        
        # Exact match
        if loc1 == loc2:
            return 1.0
        
        # Substring match (e.g., "Paris" in "Paris CDG")
        if loc1 in loc2 or loc2 in loc1:
            return 0.9
        
        # Common abbreviations/variations
        # This could be expanded with a proper city/airport database
        variations = {
            "nyc": ["new york", "new york city"],
            "la": ["los angeles"],
            "sf": ["san francisco"],
            "paris": ["cdg", "orly"],
            "london": ["lhr", "lgw", "ltn"],
            "tokyo": ["nrt", "hnd"],
        }
        
        for key, values in variations.items():
            if (loc1 == key and loc2 in values) or (loc2 == key and loc1 in values):
                return 0.95
        
        # No match
        return 0.0
    
    def _match_dates(
        self,
        deal_date: Optional[str],
        sub_start: Optional[str],
        sub_end: Optional[str]
    ) -> float:
        """
        Match deal dates against subscription date preferences.
        
        Returns:
            Score from 0.0 to 1.0
        """
        if not deal_date:
            return 0.5  # Unknown date gets neutral score
        
        if not sub_start and not sub_end:
            return 0.5  # No preference specified
        
        # For MVP, we do simple string matching
        # In production, this should parse dates properly
        deal_date_lower = deal_date.lower()
        
        if sub_start:
            start_lower = sub_start.lower()
            # Check if month/year mentioned in both
            if any(month in deal_date_lower and month in start_lower 
                   for month in ["jan", "feb", "mar", "apr", "may", "jun", 
                                 "jul", "aug", "sep", "oct", "nov", "dec"]):
                return 1.0
        
        if sub_end:
            end_lower = sub_end.lower()
            if any(month in deal_date_lower and month in end_lower 
                   for month in ["jan", "feb", "mar", "apr", "may", "jun", 
                                 "jul", "aug", "sep", "oct", "nov", "dec"]):
                return 1.0
        
        return 0.3  # Some credit for having a date
    
    def _generate_ai_summary(self, deal: Deal, subscription: Subscription) -> str:
        """
        Generate AI-powered summary explaining why this deal matches.
        
        Args:
            deal: Deal object
            subscription: Subscription object
        
        Returns:
            AI-generated summary text
        """
        prompt = f"""
You are a travel advisor. Explain why this flight deal is good for the user.

User's request: "{subscription.prompt}"

Deal details:
- Route: {deal.route}
- Price: ${deal.price} {deal.currency}
- Airline: {deal.airline}
- Dates: {deal.departure_date} to {deal.return_date}

Write a brief, enthusiastic 2-3 sentence summary explaining why this is a great match.
Focus on value, convenience, and how it meets their needs.
"""
        
        system_prompt = "You are a helpful travel advisor. Be concise, enthusiastic, and focus on value."
        
        summary = self.llm_client.generate(prompt, system_prompt)
        
        if not summary:
            # Fallback summary if LLM fails
            summary = f"Great deal on {deal.route} for ${deal.price}! This matches your search for {subscription.destination or 'travel deals'}."
        
        return summary.strip()


if __name__ == "__main__":
    # Test matcher (requires database setup)
    from models.database import get_db_session
    
    session = get_db_session()
    matcher = DealMatcher(session)
    
    # Create test subscription
    test_sub = Subscription(
        user_id=1,
        prompt="Flights to Paris under $500 in April",
        destination="Paris",
        max_price=500,
        start_date="April 2026",
        is_active=True
    )
    session.add(test_sub)
    session.commit()
    
    # Create test deal
    test_deal = Deal(
        source="test",
        source_email_id="test123",
        airline="Air France",
        route="NYC → Paris",
        departure_city="New York",
        arrival_city="Paris",
        departure_date="2026-04-15",
        return_date="2026-04-22",
        price=449,
        currency="USD",
        booking_link="https://example.com"
    )
    session.add(test_deal)
    session.commit()
    
    # Test matching
    matches = matcher.match_deal_to_subscriptions(test_deal)
    print(f"✅ Created {len(matches)} matches")
    for match in matches:
        print(f"  Score: {match.match_score}")
        print(f"  Summary: {match.ai_summary}")
