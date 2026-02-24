from sqlalchemy.orm import Session
from app.models import Email, User, AutomationLevel, EmailClassification


class DecisionEngine:
    """
    Core decision engine that determines what to do with an email.
    Routes emails based on priority, classification, and automation level.
    """
    
    def decide_action(
        self,
        email: Email,
        user: User,
        db: Session
    ) -> dict:
        """
        Decide what action to take with an email.
        
        Returns:
            {
                "action": "auto_handle" | "queue_approval" | "surface_brief" | "archive",
                "reason": str,
                "confidence": float
            }
        """
        priority = email.priority_score or 50
        classification = email.classification
        automation_level = user.automation_level
        
        # Rule 1: Spam always archived
        if classification == EmailClassification.SPAM:
            return {
                "action": "archive",
                "reason": "Classified as spam",
                "confidence": 0.95
            }
        
        # Rule 2: Read-Only mode - never take action
        if automation_level == AutomationLevel.READ_ONLY:
            return {
                "action": "surface_brief",
                "reason": "Read-only mode enabled",
                "confidence": 1.0
            }
        
        # Rule 3: Urgent + High Priority always surfaced
        if classification == EmailClassification.URGENT and priority >= 80:
            return {
                "action": "surface_brief",
                "reason": "High priority urgent email requires attention",
                "confidence": 0.9
            }
        
        # Rule 4: FYI emails with low priority
        if classification == EmailClassification.FYI and priority < 30:
            if automation_level in [AutomationLevel.AUTO_HANDLE, AutomationLevel.FULL_DELEGATE]:
                return {
                    "action": "archive",
                    "reason": "Low priority FYI email",
                    "confidence": 0.85
                }
            else:
                return {
                    "action": "surface_brief",
                    "reason": "FYI email for review",
                    "confidence": 0.7
                }
        
        # Rule 5: Action Required emails
        if classification == EmailClassification.ACTION_REQUIRED:
            if automation_level == AutomationLevel.FULL_DELEGATE and priority < 60:
                return {
                    "action": "auto_handle",
                    "reason": "Routine action in full delegate mode",
                    "confidence": 0.8
                }
            elif automation_level == AutomationLevel.AUTO_HANDLE and priority < 40:
                return {
                    "action": "auto_handle",
                    "reason": "Low complexity action",
                    "confidence": 0.75
                }
            else:
                return {
                    "action": "queue_approval",
                    "reason": "Action requires user approval",
                    "confidence": 0.85
                }
        
        # Rule 6: Meeting requests (detected in summary)
        if email.summary and ("meeting" in email.summary.lower() or "schedule" in email.summary.lower()):
            if automation_level == AutomationLevel.FULL_DELEGATE:
                return {
                    "action": "auto_handle",
                    "reason": "Auto-schedule meeting in full delegate mode",
                    "confidence": 0.8
                }
            else:
                return {
                    "action": "queue_approval",
                    "reason": "Meeting request needs approval",
                    "confidence": 0.9
                }
        
        # Rule 7: Medium priority in Assist Mode
        if automation_level == AutomationLevel.ASSIST_MODE:
            if priority >= 50:
                return {
                    "action": "queue_approval",
                    "reason": "Draft reply for approval",
                    "confidence": 0.75
                }
            else:
                return {
                    "action": "surface_brief",
                    "reason": "Low priority in assist mode",
                    "confidence": 0.7
                }
        
        # Default: Surface to brief
        return {
            "action": "surface_brief",
            "reason": "Default routing for review",
            "confidence": 0.6
        }
    
    def should_auto_send(self, decision: dict, confidence_threshold: float = 0.8) -> bool:
        """Determine if reply should be auto-sent based on decision confidence"""
        return (
            decision["action"] == "auto_handle" and
            decision["confidence"] >= confidence_threshold
        )
