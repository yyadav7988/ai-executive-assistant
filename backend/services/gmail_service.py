from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.config import settings
from app.models import User


class GmailService:
    """Handle Gmail API operations"""
    
    def __init__(self, user: User):
        """Initialize Gmail service with user credentials"""
        creds = Credentials(
            token=user.access_token,
            refresh_token=user.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET
        )
        self.service = build('gmail', 'v1', credentials=creds)
        self.user_email = user.email
    
    async def fetch_unread_emails(self, max_results: int = 50) -> list[dict]:
        """Fetch unread emails from inbox"""
        try:
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread in:inbox',
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                email_data = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()
                
                parsed_email = self._parse_email(email_data)
                if parsed_email:
                    emails.append(parsed_email)
            
            return emails
            
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []
    
    def _parse_email(self, email_data: dict) -> Optional[dict]:
        """Parse Gmail API response into structured format"""
        try:
            headers = {h['name']: h['value'] for h in email_data['payload']['headers']}
            
            # Extract body
            body = self._extract_body(email_data['payload'])
            
            # Parse timestamp (milliseconds to datetime)
            from datetime import datetime
            received_at = datetime.fromtimestamp(int(email_data['internalDate']) / 1000)
            
            return {
                'gmail_id': email_data['id'],
                'thread_id': email_data['threadId'],
                'subject': headers.get('Subject', '(No Subject)'),
                'from_email': self._extract_email(headers.get('From', '')),
                'from_name': self._extract_name(headers.get('From', '')),
                'body': body,
                'received_at': received_at
            }
        except Exception as e:
            print(f"Error parsing email: {e}")
            return None
    
    def _extract_body(self, payload: dict) -> str:
        """Extract email body from payload"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                        break
                elif part['mimeType'] == 'text/html' and not body:
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
        else:
            if 'data' in payload['body']:
                body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
        
        return body
    
    def _extract_email(self, from_field: str) -> str:
        """Extract email address from 'From' field"""
        import re
        match = re.search(r'[\w\.-]+@[\w\.-]+', from_field)
        return match.group(0) if match else from_field
    
    def _extract_name(self, from_field: str) -> str:
        """Extract name from 'From' field"""
        import re
        match = re.match(r'^([^<]+)<', from_field)
        if match:
            return match.group(1).strip().strip('"')
        return ""
    
    async def send_reply(
        self,
        to: str,
        subject: str,
        body: str,
        thread_id: Optional[str] = None
    ) -> dict:
        """Send email reply"""
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            message['from'] = self.user_email
            
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            send_params = {
                'userId': 'me',
                'body': {'raw': raw}
            }
            
            if thread_id:
                send_params['body']['threadId'] = thread_id
            
            result = self.service.users().messages().send(**send_params).execute()
            return result
            
        except Exception as e:
            print(f"Error sending email: {e}")
            raise
    
    async def archive_email(self, gmail_id: str) -> bool:
        """Archive email (remove from inbox)"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=gmail_id,
                body={'removeLabelIds': ['INBOX']}
            ).execute()
            return True
        except Exception as e:
            print(f"Error archiving email: {e}")
            return False
    
    async def mark_as_read(self, gmail_id: str) -> bool:
        """Mark email as read"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=gmail_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except Exception as e:
            print(f"Error marking as read: {e}")
            return False
