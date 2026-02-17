from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.api.auth import get_current_user
from app.models import User, Email, EmailAction, EmailStatus
from app.schemas.email import EmailResponse, EmailWithActions
from app.services.gmail_service import GmailService
from app.services.activity_service import ActivityService
from app.ai.classifier import EmailClassifier
from app.ai.priority_scorer import PriorityScorer
from app.ai.summarizer import ThreadSummarizer
from app.ai.reply_generator import ReplyGenerator
from app.services.decision_engine import DecisionEngine

router = APIRouter()


@router.post("/sync")
async def sync_emails(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync emails from Gmail and process them"""
    try:
        # Initialize services
        gmail_service = GmailService(current_user)
        classifier = EmailClassifier()
        scorer = PriorityScorer()
        summarizer = ThreadSummarizer()
        decision_engine = DecisionEngine()
        activity_service = ActivityService()
        
        # Fetch unread emails
        raw_emails = await gmail_service.fetch_unread_emails(max_results=20)
        
        processed_count = 0
        
        for raw_email in raw_emails:
            # Check if email already exists
            existing = db.query(Email).filter(
                Email.gmail_id == raw_email['gmail_id']
            ).first()
            
            if existing:
                continue
            
            # Create email record
            email = Email(
                user_id=current_user.id,
                **raw_email,
                status=EmailStatus.UNPROCESSED
            )
            db.add(email)
            db.flush()
            
            # AI Processing
            # 1. Classify
            classification_result = await classifier.classify(
                email.from_email,
                email.subject,
                email.body
            )
            email.classification = classification_result['classification']
            
            # 2. Score priority
            score_result = await scorer.score(
                email.from_email,
                email.subject,
                email.body
            )
            email.priority_score = score_result['priority_score']
            
            # 3. Summarize
            summary_result = await summarizer.summarize(
                email.from_email,
                email.subject,
                email.body
            )
            email.summary = summary_result['summary']
            
            email.processed_at = datetime.utcnow()
            email.status = EmailStatus.PROCESSED
            
            # 4. Decide action
            decision = decision_engine.decide_action(email, current_user, db)
            
            # Log activity
            activity_service.log_action(
                db=db,
                user_id=current_user.id,
                action_type="email_processed",
                description=f"Processed email: {email.subject}",
                metadata={
                    "email_id": str(email.id),
                    "classification": email.classification.value,
                    "priority": email.priority_score,
                    "decision": decision['action']
                }
            )
            
            processed_count += 1
        
        db.commit()
        
        # Update last sync
        current_user.last_sync = datetime.utcnow()
        db.commit()
        
        return {
            "status": "success",
            "processed": processed_count,
            "message": f"Processed {processed_count} new emails"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email sync failed: {str(e)}")


@router.get("/", response_model=list[EmailResponse])
async def list_emails(
    status: Optional[EmailStatus] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List emails with optional filtering"""
    query = db.query(Email).filter(Email.user_id == current_user.id)
    
    if status:
        query = query.filter(Email.status == status)
    
    emails = query.order_by(Email.received_at.desc()).offset(skip).limit(limit).all()
    return emails


@router.get("/{email_id}", response_model=EmailWithActions)
async def get_email(
    email_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get email details with actions"""
    email = db.query(Email).filter(
        Email.id == email_id,
        Email.user_id == current_user.id
    ).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    return email


@router.post("/{email_id}/approve")
async def approve_reply(
    email_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve and send draft reply"""
    email = db.query(Email).filter(
        Email.id == email_id,
        Email.user_id == current_user.id
    ).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # Get pending action
    action = db.query(EmailAction).filter(
        EmailAction.email_id == email_id,
        EmailAction.approved == False
    ).first()
    
    if not action or not action.draft_reply:
        raise HTTPException(status_code=400, detail="No draft reply found")
    
    # Send reply
    gmail_service = GmailService(current_user)
    await gmail_service.send_reply(
        to=email.from_email,
        subject=f"Re: {email.subject}",
        body=action.draft_reply,
        thread_id=email.thread_id
    )
    
    # Update action
    action.approved = True
    action.sent_at = datetime.utcnow()
    email.status = EmailStatus.REPLIED
    
    # Log activity
    activity_service = ActivityService()
    activity_service.log_action(
        db=db,
        user_id=current_user.id,
        action_type="email_replied",
        description=f"Sent reply to: {email.from_email}",
        metadata={"email_id": str(email.id), "gmail_id": email.gmail_id}
    )
    
    db.commit()
    
    return {"status": "success", "message": "Reply sent"}


@router.post("/{email_id}/archive")
async def archive_email(
    email_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Archive email"""
    email = db.query(Email).filter(
        Email.id == email_id,
        Email.user_id == current_user.id
    ).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # Archive in Gmail
    gmail_service = GmailService(current_user)
    success = await gmail_service.archive_email(email.gmail_id)
    
    if success:
        email.status = EmailStatus.ARCHIVED
        
        # Log activity
        activity_service = ActivityService()
        activity_service.log_action(
            db=db,
            user_id=current_user.id,
            action_type="email_archived",
            description=f"Archived email: {email.subject}",
            metadata={"email_id": str(email.id), "gmail_id": email.gmail_id},
            can_undo=True
        )
        
        db.commit()
        return {"status": "success", "message": "Email archived"}
    else:
        raise HTTPException(status_code=500, detail="Failed to archive email")
