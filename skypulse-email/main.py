"""
SkyPulse 2.0 - Main Email Service
Orchestrates the entire email monitoring and notification workflow.
"""

import logging
import time
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import Config
from models.database import init_db, get_db
from models.schemas import Deal, User
from email_service.imap_reader import EmailReader, FLIGHT_DEAL_SOURCES
from email_service.smtp_sender import EmailSender
from parsers.deal_parser import DealParser
from matching.matcher import DealMatcher

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SkyPulseEmailService:
    """Main email service orchestrator"""
    
    def __init__(self):
        self.email_reader = EmailReader()
        self.email_sender = EmailSender()
        self.deal_parser = DealParser()
        self.scheduler = BlockingScheduler()
        
        logger.info("SkyPulse Email Service initialized")
    
    def process_emails(self):
        """
        Main workflow: fetch emails, parse deals, match to subscriptions, send notifications.
        This is the core function that runs on a schedule.
        """
        logger.info("=" * 60)
        logger.info("Starting email processing cycle")
        logger.info("=" * 60)
        
        try:
            # 1. Fetch recent emails
            logger.info("Step 1: Fetching emails from IMAP...")
            emails = self.email_reader.fetch_recent_emails(
                days=1,
                sender_filter=FLIGHT_DEAL_SOURCES
            )
            logger.info(f"Fetched {len(emails)} emails")
            
            if not emails:
                logger.info("No new emails found")
                return
            
            # 2. Parse deals from emails
            logger.info("Step 2: Parsing deals from emails...")
            parsed_deals = []
            for email_data in emails:
                deal_info = self.deal_parser.parse_email(email_data)
                if deal_info:
                    parsed_deals.append(deal_info)
            
            logger.info(f"Parsed {len(parsed_deals)} deals from {len(emails)} emails")
            
            if not parsed_deals:
                logger.info("No valid deals found in emails")
                return
            
            # 3. Save deals to database and match to subscriptions
            logger.info("Step 3: Saving deals and matching to subscriptions...")
            with get_db() as db:
                for deal_info in parsed_deals:
                    # Check if deal already exists (by source_email_id)
                    existing = db.query(Deal).filter(
                        Deal.source_email_id == deal_info["source_email_id"]
                    ).first()
                    
                    if existing:
                        logger.info(f"Deal already exists: {deal_info['route']}")
                        continue
                    
                    # Create new deal
                    deal = Deal(
                        source=deal_info.get("source"),
                        source_email_id=deal_info.get("source_email_id"),
                        airline=deal_info.get("airline"),
                        flight_number=deal_info.get("flight_number"),
                        route=deal_info.get("route"),
                        departure_city=deal_info.get("departure_city"),
                        arrival_city=deal_info.get("arrival_city"),
                        departure_date=deal_info.get("departure_date"),
                        return_date=deal_info.get("return_date"),
                        price=float(deal_info.get("price", 0)),
                        currency=deal_info.get("currency", "USD"),
                        booking_link=deal_info.get("booking_link", ""),
                        raw_content=deal_info.get("raw_content", "")
                    )
                    
                    db.add(deal)
                    db.flush()  # Get the deal ID
                    
                    logger.info(f"Saved new deal: {deal.route} - ${deal.price}")
                    
                    # Match deal to subscriptions
                    matcher = DealMatcher(db)
                    matches = matcher.match_deal_to_subscriptions(deal)
                    
                    # 4. Send notifications for matches
                    if matches:
                        logger.info(f"Step 4: Sending notifications for {len(matches)} matches...")
                        self._send_notifications(db, matches)
            
            logger.info("✅ Email processing cycle completed successfully")
            
        except Exception as e:
            logger.error(f"Error in email processing cycle: {e}", exc_info=True)
        
        finally:
            self.email_reader.disconnect()
    
    def _send_notifications(self, db, matches):
        """Send email notifications for deal matches"""
        for match in matches:
            try:
                # Get user email
                user = db.query(User).filter(
                    User.id == match.subscription.user_id
                ).first()
                
                if not user or not user.email:
                    logger.warning(f"No email found for user {match.subscription.user_id}")
                    continue
                
                # Prepare deal info
                deal = match.deal
                deal_info = {
                    "route": deal.route,
                    "price": deal.price,
                    "currency": deal.currency,
                    "airline": deal.airline,
                    "departure_date": deal.departure_date,
                    "return_date": deal.return_date,
                    "booking_link": deal.booking_link
                }
                
                # Send notification
                success = self.email_sender.send_deal_notification(
                    to_email=user.email,
                    deal_info=deal_info,
                    ai_summary=match.ai_summary
                )
                
                if success:
                    match.notified_at = datetime.utcnow()
                    match.email_sent = True
                    db.commit()
                    logger.info(f"✅ Notification sent to {user.email}")
                else:
                    logger.error(f"Failed to send notification to {user.email}")
                    
            except Exception as e:
                logger.error(f"Error sending notification: {e}")
    
    def start(self):
        """Start the email service with scheduled tasks"""
        logger.info("=" * 60)
        logger.info("SkyPulse Email Service Starting")
        logger.info("=" * 60)
        
        # Initialize database
        logger.info("Initializing database...")
        init_db()
        
        # Test connections
        logger.info("Testing email connections...")
        if self.email_reader.connect():
            logger.info("✅ IMAP connection successful")
            self.email_reader.disconnect()
        else:
            logger.warning("⚠️  IMAP connection failed - check credentials")
        
        # Run immediately on startup
        logger.info("Running initial email processing...")
        self.process_emails()
        
        # Schedule periodic processing
        interval_minutes = Config.CHECK_EMAIL_INTERVAL_MINUTES
        logger.info(f"Scheduling email checks every {interval_minutes} minutes")
        
        self.scheduler.add_job(
            self.process_emails,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id='process_emails',
            name='Process flight deal emails',
            replace_existing=True
        )
        
        logger.info("✅ Scheduler started")
        logger.info("=" * 60)
        logger.info("Service is running. Press Ctrl+C to stop.")
        logger.info("=" * 60)
        
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Shutting down...")
            self.scheduler.shutdown()
            logger.info("✅ Service stopped")


def main():
    """Main entry point"""
    try:
        service = SkyPulseEmailService()
        service.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
