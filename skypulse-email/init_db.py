"""
SkyPulse 2.0 - Database Initialization Script
Creates database and optionally seeds test data.
"""

import logging
from datetime import datetime

from models.database import init_db, get_db_session
from models.schemas import User, Subscription, Deal, DealMatch

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def seed_test_data():
    """Seed database with test data for development"""
    logger.info("Seeding test data...")
    
    db = get_db_session()
    
    try:
        # Create test user
        test_user = User(
            email="test@skypulse.com",
            language="en",
            verified=True
        )
        db.add(test_user)
        db.commit()
        logger.info(f"Created test user: {test_user.email}")
        
        # Create test subscriptions
        subscriptions = [
            Subscription(
                user_id=test_user.id,
                prompt="Flights to Paris under $500 in April",
                destination="Paris",
                max_price=500,
                start_date="April 2026",
                is_active=True
            ),
            Subscription(
                user_id=test_user.id,
                prompt="Weekend trip to Tokyo under $800",
                destination="Tokyo",
                max_price=800,
                is_active=True
            ),
            Subscription(
                user_id=test_user.id,
                prompt="Business trip to London next month",
                destination="London",
                max_price=1000,
                start_date="March 2026",
                is_active=True
            ),
        ]
        
        for sub in subscriptions:
            db.add(sub)
        db.commit()
        logger.info(f"Created {len(subscriptions)} test subscriptions")
        
        # Create test deals
        deals = [
            Deal(
                source="scott_cheap_flights",
                source_email_id="test001",
                airline="Air France",
                route="NYC → Paris",
                departure_city="New York",
                arrival_city="Paris",
                departure_date="2026-04-15",
                return_date="2026-04-22",
                price=449,
                currency="USD",
                booking_link="https://example.com/paris",
                raw_content="Test deal content"
            ),
            Deal(
                source="secret_flying",
                source_email_id="test002",
                airline="Japan Airlines",
                route="LAX → Tokyo",
                departure_city="Los Angeles",
                arrival_city="Tokyo",
                departure_date="2026-05-10",
                return_date="2026-05-17",
                price=649,
                currency="USD",
                booking_link="https://example.com/tokyo",
                raw_content="Test deal content"
            ),
        ]
        
        for deal in deals:
            db.add(deal)
        db.commit()
        logger.info(f"Created {len(deals)} test deals")
        
        logger.info("✅ Test data seeded successfully")
        
    except Exception as e:
        logger.error(f"Error seeding test data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    # Initialize database
    logger.info("Initializing SkyPulse database...")
    init_db()
    logger.info("✅ Database tables created")
    
    # Check if --seed flag is provided
    if "--seed" in sys.argv:
        seed_test_data()
    else:
        logger.info("Tip: Run with --seed flag to add test data")
    
    logger.info("✅ Database initialization complete")
