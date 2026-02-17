from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database import get_db
from app.api.auth import get_current_user
from app.models import User, Email, CalendarEvent, EmailStatus, EmailClassification

router = APIRouter()


@router.get("/today")
async def get_todays_brief(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get Today's Brief - the main view of the application
    
    Returns:
        {
            "handled_automatically": [...],
            "needs_attention": [...],
            "upcoming": [...]
        }
    """
    # Get emails from last 24 hours
    yesterday = datetime.utcnow() - timedelta(days=1)
    
    # Handled Automatically
    handled = db.query(Email).filter(
        Email.user_id == current_user.id,
        Email.status.in_([EmailStatus.ARCHIVED, EmailStatus.REPLIED]),
        Email.processed_at >= yesterday
    ).order_by(Email.processed_at.desc()).limit(20).all()
    
    # Needs Attention
    needs_attention = db.query(Email).filter(
        Email.user_id == current_user.id,
        Email.status == EmailStatus.PENDING_APPROVAL
    ).order_by(Email.priority_score.desc()).limit(20).all()
    
    # Also include high-priority unprocessed emails
    urgent_emails = db.query(Email).filter(
        Email.user_id == current_user.id,
        Email.status == EmailStatus.PROCESSED,
        Email.classification.in_([EmailClassification.URGENT, EmailClassification.ACTION_REQUIRED]),
        Email.priority_score >= 70
    ).order_by(Email.priority_score.desc()).limit(10).all()
    
    needs_attention.extend(urgent_emails)
    
    # Upcoming - Calendar events for next 7 days
    now = datetime.utcnow()
    next_week = now + timedelta(days=7)
    
    upcoming_events = db.query(CalendarEvent).filter(
        CalendarEvent.user_id == current_user.id,
        CalendarEvent.start_time >= now,
        CalendarEvent.start_time <= next_week
    ).order_by(CalendarEvent.start_time).limit(20).all()
    
    return {
        "handled_automatically": [
            {
                "id": str(e.id),
                "subject": e.subject,
                "from_email": e.from_email,
                "from_name": e.from_name,
                "summary": e.summary,
                "status": e.status.value,
                "processed_at": e.processed_at.isoformat() if e.processed_at else None
            }
            for e in handled
        ],
        "needs_attention": [
            {
                "id": str(e.id),
                "subject": e.subject,
                "from_email": e.from_email,
                "from_name": e.from_name,
                "summary": e.summary,
                "priority_score": e.priority_score,
                "classification": e.classification.value if e.classification else None,
                "received_at": e.received_at.isoformat()
            }
            for e in needs_attention
        ],
        "upcoming": [
            {
                "id": str(evt.id),
                "title": evt.title,
                "start_time": evt.start_time.isoformat(),
                "end_time": evt.end_time.isoformat(),
                "auto_scheduled": evt.auto_scheduled
            }
            for evt in upcoming_events
        ]
    }


@router.get("/summary")
async def get_executive_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get executive summary for today"""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Count emails by status
    total_emails = db.query(Email).filter(
        Email.user_id == current_user.id,
        Email.received_at >= today
    ).count()
    
    handled = db.query(Email).filter(
        Email.user_id == current_user.id,
        Email.status.in_([EmailStatus.ARCHIVED, EmailStatus.REPLIED]),
        Email.processed_at >= today
    ).count()
    
    needs_attention = db.query(Email).filter(
        Email.user_id == current_user.id,
        Email.status.in_([EmailStatus.PENDING_APPROVAL, EmailStatus.PROCESSED]),
        Email.priority_score >= 70
    ).count()
    
    # Upcoming meetings today
    tomorrow = today + timedelta(days=1)
    meetings_today = db.query(CalendarEvent).filter(
        CalendarEvent.user_id == current_user.id,
        CalendarEvent.start_time >= today,
        CalendarEvent.start_time < tomorrow
    ).count()
    
    return {
        "total_emails_today": total_emails,
        "handled_automatically": handled,
        "needs_attention": needs_attention,
        "meetings_today": meetings_today,
        "automation_level": current_user.automation_level.value
    }
