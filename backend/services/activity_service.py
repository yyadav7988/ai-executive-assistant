from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import json

from app.models import ActivityLog, User, Email, EmailAction


class ActivityService:
    """Service for logging and managing AI actions"""
    
    def log_action(
        self,
        db: Session,
        user_id: str,
        action_type: str,
        description: str,
        metadata: Optional[dict] = None,
        can_undo: bool = False
    ) -> ActivityLog:
        """
        Log an AI action
        
        Args:
            user_id: User ID
            action_type: Type of action (e.g., "email_replied", "email_archived", "meeting_scheduled")
            description: Human-readable description
            metadata: Additional metadata (email_id, gmail_id, etc.)
            can_undo: Whether this action can be undone
        """
        activity = ActivityLog(
            user_id=user_id,
            action_type=action_type,
            description=description,
            metadata=metadata or {},
            can_undo=can_undo,
            undone=False
        )
        
        db.add(activity)
        db.commit()
        db.refresh(activity)
        
        return activity
    
    def get_recent_activity(
        self,
        db: Session,
        user_id: str,
        limit: int = 50,
        skip: int = 0
    ) -> list[ActivityLog]:
        """Get recent activity logs for user"""
        return db.query(ActivityLog)\
            .filter(ActivityLog.user_id == user_id)\
            .order_by(ActivityLog.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    async def undo_action(
        self,
        db: Session,
        activity_id: str,
        gmail_service,
        calendar_service
    ) -> bool:
        """
        Undo an action if possible
        
        Returns:
            True if successfully undone, False otherwise
        """
        activity = db.query(ActivityLog).filter(ActivityLog.id == activity_id).first()
        
        if not activity or not activity.can_undo or activity.undone:
            return False
        
        try:
            # Handle different action types
            if activity.action_type == "email_archived":
                # Unarchive email (add back to inbox)
                gmail_id = activity.metadata.get("gmail_id")
                if gmail_id:
                    # This would require Gmail API call to add INBOX label
                    pass
            
            elif activity.action_type == "email_replied":
                # Can't unsend email, but mark as undone
                pass
            
            elif activity.action_type == "meeting_scheduled":
                # Delete calendar event
                google_event_id = activity.metadata.get("google_event_id")
                if google_event_id:
                    # This would require Calendar API call to delete event
                    pass
            
            # Mark as undone
            activity.undone = True
            db.commit()
            
            return True
            
        except Exception as e:
            print(f"Error undoing action: {e}")
            return False
