"""
SkyPulse 2.0 - IMAP Email Reader
Fetches promotional emails from configured inbox.
"""

import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta

from config import Config

logger = logging.getLogger(__name__)


class EmailReader:
    """IMAP email reader for promotional flight deals"""
    
    def __init__(self):
        self.server = Config.IMAP_SERVER
        self.port = Config.IMAP_PORT
        self.email = Config.IMAP_EMAIL
        self.password = Config.IMAP_PASSWORD
        self.connection = None
    
    def connect(self):
        """Connect to IMAP server"""
        try:
            logger.info(f"Connecting to IMAP server: {self.server}:{self.port}")
            self.connection = imaplib.IMAP4_SSL(self.server, self.port)
            self.connection.login(self.email, self.password)
            logger.info("IMAP connection established")
            return True
        except Exception as e:
            logger.error(f"IMAP connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from IMAP server"""
        if self.connection:
            try:
                self.connection.logout()
                logger.info("IMAP connection closed")
            except:
                pass
    
    def fetch_recent_emails(self, folder="INBOX", days=1, sender_filter=None) -> List[Dict]:
        """
        Fetch recent emails from specified folder.
        
        Args:
            folder: IMAP folder name (default: INBOX)
            days: Number of days to look back
            sender_filter: Optional list of sender emails to filter
        
        Returns:
            List of email dictionaries with parsed content
        """
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            # Select folder
            self.connection.select(folder)
            
            # Calculate date filter
            since_date = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
            
            # Build search criteria
            search_criteria = f'(SINCE {since_date})'
            if sender_filter:
                sender_queries = ' OR '.join([f'FROM "{sender}"' for sender in sender_filter])
                search_criteria = f'({sender_queries}) {search_criteria}'
            
            # Search emails
            status, messages = self.connection.search(None, search_criteria)
            
            if status != "OK":
                logger.error("Failed to search emails")
                return []
            
            email_ids = messages[0].split()
            logger.info(f"Found {len(email_ids)} emails matching criteria")
            
            emails = []
            for email_id in email_ids[-50:]:  # Limit to last 50 emails
                email_data = self._fetch_email(email_id)
                if email_data:
                    emails.append(email_data)
            
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []
    
    def _fetch_email(self, email_id) -> Optional[Dict]:
        """Fetch and parse a single email"""
        try:
            status, msg_data = self.connection.fetch(email_id, "(RFC822)")
            
            if status != "OK":
                return None
            
            # Parse email
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Decode subject
            subject = self._decode_header(msg["Subject"])
            sender = msg.get("From", "")
            date = msg.get("Date", "")
            
            # Extract body
            body = self._get_email_body(msg)
            
            return {
                "id": email_id.decode(),
                "subject": subject,
                "sender": sender,
                "date": date,
                "body": body,
                "raw": raw_email,
            }
            
        except Exception as e:
            logger.error(f"Error parsing email {email_id}: {e}")
            return None
    
    def _decode_header(self, header_value):
        """Decode email header"""
        if not header_value:
            return ""
        
        decoded_parts = decode_header(header_value)
        header = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                header += part.decode(encoding or "utf-8", errors="ignore")
            else:
                header += part
        return header
    
    def _get_email_body(self, msg) -> str:
        """Extract email body (prefer plain text, fallback to HTML)"""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        break
                    except:
                        pass
                elif content_type == "text/html" and not body:
                    try:
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
            except:
                body = str(msg.get_payload())
        
        return body


# Predefined email sources for flight deals
FLIGHT_DEAL_SOURCES = [
    "deals@scottscheapflights.com",
    "alerts@secretflying.com",
    "deals@theflightdeal.com",
    "noreply@google.com",  # Google Flights alerts
]


if __name__ == "__main__":
    # Test email reader
    reader = EmailReader()
    if reader.connect():
        emails = reader.fetch_recent_emails(days=7, sender_filter=FLIGHT_DEAL_SOURCES)
        print(f"✅ Fetched {len(emails)} emails")
        for email_data in emails[:3]:
            print(f"\nSubject: {email_data['subject']}")
            print(f"From: {email_data['sender']}")
            print(f"Body preview: {email_data['body'][:200]}...")
        reader.disconnect()
