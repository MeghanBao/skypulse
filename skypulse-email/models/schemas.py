"""
SkyPulse 2.0 - Database Models
Defines User, Subscription, and Deal schemas using SQLAlchemy.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User model - represents email subscribers"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    language = Column(String(5), default="en")  # en, zh
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(email='{self.email}')>"


class Subscription(Base):
    """Subscription model - user's flight preferences"""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Original user input
    prompt = Column(Text, nullable=False)
    
    # Parsed fields (extracted by LLM)
    origin = Column(String(100))
    destination = Column(String(100))
    max_price = Column(Float)
    start_date = Column(String(50))  # Can be "April 2026" or "2026-04-01"
    end_date = Column(String(50))
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    matched_deals = relationship("DealMatch", back_populates="subscription")
    
    def __repr__(self):
        return f"<Subscription(user={self.user_id}, route={self.origin}→{self.destination})>"


class Deal(Base):
    """Deal model - parsed flight deals from emails"""
    __tablename__ = "deals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Source information
    source = Column(String(100))  # "scott_cheap_flights", "secret_flying", etc.
    source_email_id = Column(String(255))  # Original email ID
    
    # Flight details
    airline = Column(String(100))
    flight_number = Column(String(20))
    route = Column(String(200))  # "NYC → Tokyo"
    departure_city = Column(String(100))
    arrival_city = Column(String(100))
    departure_date = Column(String(50))
    return_date = Column(String(50))
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    
    # Links
    booking_link = Column(Text)
    
    # Raw data
    raw_content = Column(Text)  # Original email content
    
    # Metadata
    parsed_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # When the deal expires
    
    # Relationships
    matches = relationship("DealMatch", back_populates="deal")
    
    def __repr__(self):
        return f"<Deal(route={self.route}, price=${self.price})>"


class DealMatch(Base):
    """DealMatch model - links deals to subscriptions"""
    __tablename__ = "deal_matches"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    
    # AI-generated summary
    ai_summary = Column(Text)  # "Why this is a good deal for you"
    match_score = Column(Float)  # 0-100 confidence score
    
    # Notification tracking
    notified_at = Column(DateTime)
    email_sent = Column(Boolean, default=False)
    email_opened = Column(Boolean, default=False)
    link_clicked = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subscription = relationship("Subscription", back_populates="matched_deals")
    deal = relationship("Deal", back_populates="matches")
    
    def __repr__(self):
        return f"<DealMatch(sub={self.subscription_id}, deal={self.deal_id}, score={self.match_score})>"
