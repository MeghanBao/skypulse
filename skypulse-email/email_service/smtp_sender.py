"""
SkyPulse 2.0 - SMTP Email Sender
Sends notification emails to users.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

from config import Config

logger = logging.getLogger(__name__)


class EmailSender:
    """SMTP email sender for notifications"""
    
    def __init__(self):
        self.server = Config.SMTP_SERVER
        self.port = Config.SMTP_PORT
        self.email = Config.SMTP_EMAIL
        self.password = Config.SMTP_PASSWORD
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None
    ) -> bool:
        """
        Send an email notification.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body_text: Plain text body
            body_html: Optional HTML body
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = self.email
            msg["To"] = to_email
            msg["Subject"] = subject
            
            # Attach text version
            msg.attach(MIMEText(body_text, "plain"))
            
            # Attach HTML version if provided
            if body_html:
                msg.attach(MIMEText(body_html, "html"))
            
            # Connect and send
            with smtplib.SMTP(self.server, self.port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_deal_notification(
        self,
        to_email: str,
        deal_info: dict,
        ai_summary: str
    ) -> bool:
        """
        Send a flight deal notification with AI-generated summary.
        
        Args:
            to_email: User email
            deal_info: Dictionary with deal details
            ai_summary: AI-generated summary
        
        Returns:
            True if sent successfully
        """
        subject = f"✈️ Deal Alert: {deal_info.get('route', 'Flight Deal')} - ${deal_info.get('price', 'N/A')}"
        
        # Plain text version
        body_text = f"""
SkyPulse Deal Alert

{deal_info.get('route', 'Flight Deal')}
Price: ${deal_info.get('price', 'N/A')} {deal_info.get('currency', 'USD')}
Airline: {deal_info.get('airline', 'N/A')}
Dates: {deal_info.get('departure_date', 'N/A')} - {deal_info.get('return_date', 'N/A')}

🤖 AI Insight:
{ai_summary}

Book Now: {deal_info.get('booking_link', '#')}

---
To unsubscribe, reply with "UNSUBSCRIBE"
"""
        
        # HTML version
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .deal-card {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .price {{ font-size: 32px; font-weight: bold; color: #10b981; }}
        .ai-insight {{ background: #eff6ff; border-left: 4px solid #3b82f6; padding: 15px; margin: 20px 0; }}
        .cta-button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✈️ SkyPulse Deal Alert</h1>
        </div>
        <div class="content">
            <div class="deal-card">
                <h2>{deal_info.get('route', 'Flight Deal')}</h2>
                <div class="price">${deal_info.get('price', 'N/A')} {deal_info.get('currency', 'USD')}</div>
                <p><strong>Airline:</strong> {deal_info.get('airline', 'N/A')}</p>
                <p><strong>Dates:</strong> {deal_info.get('departure_date', 'N/A')} - {deal_info.get('return_date', 'N/A')}</p>
            </div>
            
            <div class="ai-insight">
                <strong>🤖 AI Insight:</strong><br>
                {ai_summary}
            </div>
            
            <a href="{deal_info.get('booking_link', '#')}" class="cta-button">Book Now →</a>
            
            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                To unsubscribe, reply with "UNSUBSCRIBE"
            </p>
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(to_email, subject, body_text, body_html)
    
    def send_confirmation_email(self, to_email: str, subscription_details: str) -> bool:
        """Send subscription confirmation email"""
        subject = "✅ SkyPulse Subscription Confirmed"
        
        body_text = f"""
Welcome to SkyPulse!

Your subscription has been confirmed:
{subscription_details}

We'll notify you when we find matching flight deals.

Happy travels!
SkyPulse Team
"""
        
        return self.send_email(to_email, subject, body_text)


if __name__ == "__main__":
    # Test email sender
    sender = EmailSender()
    
    # Test deal notification
    test_deal = {
        "route": "NYC → Tokyo",
        "price": 649,
        "currency": "USD",
        "airline": "Japan Airlines",
        "departure_date": "2026-04-15",
        "return_date": "2026-04-22",
        "booking_link": "https://example.com/book"
    }
    
    test_summary = "This is an excellent deal! The price is 46% below the average for this route during this season."
    
    # Uncomment to test (replace with your email)
    # sender.send_deal_notification("your-email@example.com", test_deal, test_summary)
    print("✅ Email sender module ready")
