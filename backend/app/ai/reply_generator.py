import json
from openai import AsyncOpenAI
from app.config import settings
from app.ai.prompts import REPLY_GENERATION_PROMPT


class ReplyGenerator:
    """Generate smart email replies using OpenAI GPT"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def generate_reply(
        self,
        from_email: str,
        subject: str,
        body: str,
        tone: str = "professional",
        writing_style_examples: str = "",
        calendar_context: str = ""
    ) -> dict:
        """
        Generate email reply
        
        Args:
            from_email: Sender's email
            subject: Email subject
            body: Email body
            tone: "professional", "friendly", or "formal"
            writing_style_examples: Examples of user's writing style
            calendar_context: User's calendar availability
        
        Returns:
            {
                "reply_body": str,
                "suggested_subject": str,
                "confidence": float,
                "reasoning": str
            }
        """
        # Truncate body if too long
        max_body_length = 2500
        truncated_body = body[:max_body_length] + "..." if len(body) > max_body_length else body
        
        # Default writing style if none provided
        if not writing_style_examples:
            writing_style_examples = "Professional and concise communication style"
        
        # Default calendar context
        if not calendar_context:
            calendar_context = "No specific calendar constraints"
        
        prompt = REPLY_GENERATION_PROMPT.format(
            from_email=from_email,
            subject=subject,
            body=truncated_body,
            tone=tone,
            writing_style_examples=writing_style_examples,
            calendar_context=calendar_context
        )
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",  # Using GPT-4 for better reply quality
                messages=[
                    {"role": "system", "content": "You are an executive assistant drafting email replies. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return {
                "reply_body": result.get("reply_body", ""),
                "suggested_subject": result.get("suggested_subject", f"Re: {subject}"),
                "confidence": result.get("confidence", 0.7),
                "reasoning": result.get("reasoning", "")
            }
            
        except Exception as e:
            print(f"Reply generation error: {e}")
            return {
                "reply_body": "",
                "suggested_subject": f"Re: {subject}",
                "confidence": 0.0,
                "reasoning": f"Error generating reply: {str(e)}"
            }
