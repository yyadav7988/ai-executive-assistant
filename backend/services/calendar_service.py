from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from datetime import datetime, timedelta
from typing import Optional

from app.config import settings
from app.models import User


class CalendarService:
    """Handle Google Calendar API operations"""
    
    def __init__(self, user: User):
        """Initialize Calendar service with user credentials"""
        creds = Credentials(
            token=user.access_token,
            refresh_token=user.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET
        )
        self.service = build('calendar', 'v3', credentials=creds)
    
    async def get_upcoming_events(self, days: int = 7) -> list[dict]:
        """Get upcoming calendar events"""
        try:
            now = datetime.utcnow().isoformat() + 'Z'
            end = (datetime.utcnow() + timedelta(days=days)).isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now,
                timeMax=end,
                singleEvents=True,
                orderBy='startTime',
                maxResults=50
            ).execute()
            
            return events_result.get('items', [])
            
        except Exception as e:
            print(f"Error fetching calendar events: {e}")
            return []
    
    async def create_event(
        self,
        title: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
        attendees: Optional[list[str]] = None
    ) -> Optional[dict]:
        """Create calendar event"""
        try:
            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                }
            }
            
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all'
            ).execute()
            
            return created_event
            
        except Exception as e:
            print(f"Error creating calendar event: {e}")
            return None
    
    async def find_available_slots(
        self,
        duration_minutes: int = 60,
        days_ahead: int = 7,
        num_slots: int = 3,
        working_hours: tuple[int, int] = (9, 17)
    ) -> list[dict]:
        """Find available time slots"""
        try:
            events = await self.get_upcoming_events(days=days_ahead)
            available_slots = []
            current_time = datetime.utcnow()
            
            for day in range(days_ahead):
                check_date = current_time + timedelta(days=day)
                
                # Skip weekends
                if check_date.weekday() >= 5:
                    continue
                
                # Check working hours
                start_hour, end_hour = working_hours
                for hour in range(start_hour, end_hour):
                    slot_start = check_date.replace(
                        hour=hour,
                        minute=0,
                        second=0,
                        microsecond=0
                    )
                    slot_end = slot_start + timedelta(minutes=duration_minutes)
                    
                    # Skip past slots
                    if slot_start < current_time:
                        continue
                    
                    # Check if slot conflicts with existing events
                    has_conflict = any(
                        self._time_overlaps(slot_start, slot_end, event)
                        for event in events
                    )
                    
                    if not has_conflict:
                        available_slots.append({
                            'start': slot_start.isoformat(),
                            'end': slot_end.isoformat()
                        })
                        
                        if len(available_slots) >= num_slots:
                            return available_slots
            
            return available_slots
            
        except Exception as e:
            print(f"Error finding available slots: {e}")
            return []
    
    def _time_overlaps(self, start1: datetime, end1: datetime, event: dict) -> bool:
        """Check if time range overlaps with event"""
        try:
            event_start_str = event['start'].get('dateTime', event['start'].get('date'))
            event_end_str = event['end'].get('dateTime', event['end'].get('date'))
            
            # Parse datetime strings
            event_start = datetime.fromisoformat(event_start_str.replace('Z', '+00:00'))
            event_end = datetime.fromisoformat(event_end_str.replace('Z', '+00:00'))
            
            # Make timezone-naive for comparison
            if event_start.tzinfo:
                event_start = event_start.replace(tzinfo=None)
            if event_end.tzinfo:
                event_end = event_end.replace(tzinfo=None)
            
            return start1 < event_end and end1 > event_start
            
        except Exception as e:
            print(f"Error checking time overlap: {e}")
            return False
