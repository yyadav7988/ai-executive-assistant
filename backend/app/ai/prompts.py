"""AI Prompt templates for various intelligence tasks"""

CLASSIFICATION_PROMPT = """You are an email classification system for an executive assistant.

Analyze this email and classify it into ONE of these categories:
- urgent: Requires immediate attention (deadlines, time-sensitive matters)
- action_required: Needs a response or action from the user
- fyi: Informational only, no action needed
- spam: Unwanted, promotional, or irrelevant content

Email:
From: {from_email}
Subject: {subject}
Body: {body}

Respond ONLY with valid JSON in this exact format:
{{
  "classification": "urgent|action_required|fyi|spam",
  "reasoning": "brief explanation in one sentence"
}}"""


PRIORITY_SCORING_PROMPT = """You are a priority scoring system for an executive assistant.

Score this email from 1-100 based on these factors:
- Sender importance (30 points): Is this from a VIP contact or important person?
- Urgency (30 points): Contains urgent keywords, deadlines, or time-sensitive content?
- Action required (20 points): Does it need a response or action?
- Time sensitivity (20 points): Is there a specific deadline or time constraint?

Important contacts: {important_contacts}
User's working hours: {working_hours}

Email:
From: {from_email}
Subject: {subject}
Body: {body}

Respond ONLY with valid JSON in this exact format:
{{
  "priority_score": 75,
  "factors": {{
    "sender_importance": 30,
    "urgency": 20,
    "action_required": 15,
    "time_sensitivity": 10
  }},
  "reasoning": "brief explanation in one sentence"
}}"""


SUMMARIZATION_PROMPT = """You are an executive assistant summarizing email threads.

Create a concise 2-3 sentence summary that answers:
1. What is this email about?
2. What's needed from the user (if anything)?
3. What's the next action?

Email:
From: {from_email}
Subject: {subject}
Body: {body}

Respond ONLY with valid JSON in this exact format:
{{
  "summary": "concise 2-3 sentence summary",
  "next_action": "specific next step or 'none' if no action needed"
}}"""


REPLY_GENERATION_PROMPT = """You are an executive assistant drafting email replies.

User's writing style examples:
{writing_style_examples}

Tone requested: {tone}

Email to reply to:
From: {from_email}
Subject: {subject}
Body: {body}

Context from user's calendar:
{calendar_context}

Draft a {tone} reply that:
- Addresses the sender's request or question
- Matches the user's writing style
- Is concise and professional
- Includes next steps if applicable
- Keeps it brief (2-4 paragraphs maximum)

Respond ONLY with valid JSON in this exact format:
{{
  "reply_body": "the complete email reply text",
  "suggested_subject": "Re: {subject}",
  "confidence": 0.85,
  "reasoning": "why this reply is appropriate in one sentence"
}}"""


CALENDAR_INTELLIGENCE_PROMPT = """You are a calendar management assistant.

Analyze this email for meeting intent and scheduling needs.

Email:
From: {from_email}
Subject: {subject}
Body: {body}

User's calendar for next 7 days:
{calendar_availability}

User's working hours: {working_hours}

Tasks:
1. Determine if this is a meeting request
2. If yes, extract meeting details and suggest 3 available time slots
3. Draft a meeting invite description

Respond ONLY with valid JSON in this exact format:
{{
  "is_meeting_request": true,
  "meeting_topic": "topic or null",
  "duration_minutes": 60,
  "suggested_slots": [
    {{"start": "2026-02-15T10:00:00", "end": "2026-02-15T11:00:00"}},
    {{"start": "2026-02-15T14:00:00", "end": "2026-02-15T15:00:00"}},
    {{"start": "2026-02-16T09:00:00", "end": "2026-02-16T10:00:00"}}
  ],
  "draft_invite": "meeting description text"
}}"""


WRITING_STYLE_ANALYSIS_PROMPT = """You are analyzing a user's writing style from their sent emails.

Analyze these email examples and extract the user's writing patterns:

{email_examples}

Identify:
- Typical greeting style
- Sentence structure (short/long, formal/casual)
- Common phrases or expressions
- Sign-off style
- Overall tone

Respond ONLY with valid JSON in this exact format:
{{
  "greeting_style": "description",
  "sentence_structure": "description",
  "common_phrases": ["phrase1", "phrase2"],
  "sign_off_style": "description",
  "overall_tone": "professional|friendly|formal|casual",
  "style_summary": "one sentence summary of writing style"
}}"""
