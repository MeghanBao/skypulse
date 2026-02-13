"""
SkyPulse 2.0 - Main Email Service with Monitoring
Enhanced with health checks, metrics, and retry logic
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

# Import monitoring modules
from monitoring.health import HealthChecker, health_check
from monitoring.metrics import get_metrics, record_email_processed, record_deal_found, record_notification_sent
from monitoring.retry import get_retry_manager, RetryableError

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SkyPulseEmailService:
    """Enhanced email service with monitoring"""
    
    def __init__(self):
        self.email_reader = EmailReader()
        self.email_sender = EmailSender()
        self.deal_parser = DealParser()
        self.scheduler = BlockingScheduler()
        self.health_checker = HealthChecker()
        self.metrics = get_metrics()
        self.retry_manager = get_retry_manager()
        
        logger.info("SkyPulse Email Service initialized with monitoring")
    
    def process_emails(self):
        """
        Main workflow with enhanced error handling and metrics.
        """
        start_time = time.time()
        success = False
        
        logger.info("=" * 60)
        logger.info("Starting email processing cycle")
        logger.info("=" * 60)
        
        try:
            # 1. Fetch recent emails
            logger.info("Step 1: Fetching emails from IMAP...")
            
            retry_manager = self.retry_manager
            
            def fetch_with_retry():
                return self.email_reader.fetch_recent_emails(
                    days=1,
                    sender_filter=FLIGHT_DEAL_SOURCES
                )
            
            try:
                emails = retry_manager.connect_imap(self.email_reader)
                if not self.email_reader.is_connected:
                    raise RetryableError("Failed to connect to IMAP")
                
                emails = self.email_reader.fetch_recent_emails(
                    days=1,
                    sender_filter=FLIGHT_DEAL_SOURCES
                )
                retry_manager.record_imap_success()
                
            except (ConnectionError, TimeoutError, IOError) as e:
                logger.error(f"IMAP connection failed: {e}")
                retry_manager.record_imap_failure()
                raise RetryableError(f"IMAP error: {e}")
            
            logger.info(f"Fetched {len(emails)} emails")
            
            if not emails:
                logger.info("No new emails found")
                record_email_processed(success=True, duration_seconds=time.time() - start_time)
                return
            
            # 2. Parse deals from emails
            logger.info("Step 2: Parsing deals from emails...")
            parsed_deals = []
            parse_errors = 0
            
            for email_data in emails:
                try:
                    deal_info = self.deal_parser.parse_email(email_data)
                    if deal_info:
                        parsed_deals.append(deal_info)
                        record_deal_found()
                except Exception as e:
                    logger.error(f"Error parsing email: {e}")
                    parse_errors += 1
                    self.metrics.error("parse_error")
            
            logger.info(f"Parsed {len(parsed_deals)} deals from {len(emails)} emails")
            logger.info(f"Parse errors: {parse_errors}")
            
            if not parsed_deals:
                logger.info("No valid deals found in emails")
                record_email_processed(success=True, duration_seconds=time.time() - start_time)
                return
            
            # 3. Save deals and match to subscriptions
            logger.info("Step 3: Saving deals and matching to subscriptions...")
            
            with get_db() as db:
                for deal_info in parsed_deals:
                    try:
                        # Check if deal already exists
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
                        db.flush()
                        
                        logger.info(f"Saved new deal: {deal.route} - ${deal.price}")
                        
                        # Match deal to subscriptions
                        matcher = DealMatcher(db)
                        matches = matcher.match_deal_to_subscriptions(deal)
                        
                        # 4. Send notifications
                        if matches:
                            logger.info(f"Step 4: Sending notifications for {len(matches)} matches...")
                            for match in matches:
                                self._send_notification(db, match)
                        
                    except Exception as e:
                        logger.error(f"Error processing deal: {e}")
                        self.metrics.error("deal_processing_error")
            
            success = True
            logger.info("✅ Email processing cycle completed successfully")
            
        except Exception as e:
            logger.error(f"Error in email processing cycle: {e}", exc_info=True)
            self.health_checker.record_error(str(e))
            self.metrics.error("email_cycle_error")
        
        finally:
            # Record metrics
            duration = time.time() - start_time
            record_email_processed(success=success, duration_seconds=duration)
            
            # Update health check stats
            self.health_checker.record_email_check(success)
            if success:
                self.health_checker.email_successes += 1
            else:
                self.health_checker.record_error("Email processing failed")
            
            self.email_reader.disconnect()
    
    def _send_notification(self, db, match):
        """Send notification with retry"""
        try:
            user = db.query(User).filter(
                User.id == match.subscription.user_id
            ).first()
            
            if not user or not user.email:
                logger.warning(f"No email found for user {match.subscription.user_id}")
                return
            
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
            
            # Send with retry
            def send_with_retry():
                return self.email_sender.send_deal_notification(
                    to_email=user.email,
                    deal_info=deal_info,
                    ai_summary=match.ai_summary
                )
            
            retry_manager = self.retry_manager
            
            success = False
            for attempt in range(3):
                try:
                    if send_with_retry():
                        success = True
                        match.notified_at = datetime.utcnow()
                        match.email_sent = True
                        db.commit()
                        record_notification_sent()
                        retry_manager.record_smtp_success()
                        logger.info(f"✅ Notification sent to {user.email}")
                        break
                except Exception as e:
                    logger.error(f"SMTP attempt {attempt + 1} failed: {e}")
                    if attempt < 2:
                        time.sleep(2 ** attempt)  # Exponential backoff
            
            if not success:
                retry_manager.record_smtp_failure()
                logger.error(f"Failed to send notification to {user.email}")
                
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            self.metrics.error("notification_error")
    
    def get_health_status(self) -> dict:
        """Get health status"""
        return health_check()
    
    def get_metrics_summary(self) -> dict:
        """Get metrics summary"""
        return self.metrics.get_summary()
    
    def start(self):
        """Start the service with monitoring"""
        logger.info("=" * 60)
        logger.info("SkyPulse Email Service Starting (Enhanced)")
        logger.info("=" * 60)
        
        # Initialize database
        logger.info("Initializing database...")
        init_db()
        
        # Test connections
        logger.info("Testing email connections...")
        try:
            if self.email_reader.connect():
                logger.info("✅ IMAP connection successful")
                self.email_reader.disconnect()
            else:
                logger.warning("⚠️ IMAP connection failed - check credentials")
        except Exception as e:
            logger.warning(f"⚠️ IMAP connection error: {e}")
        
        # Run initial email processing
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
