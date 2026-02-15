import json
from openai import AsyncOpenAI
from app.config import settings
from app.ai.prompts import SUMMARIZATION_PROMPT


class ThreadSummarizer:
    """Summarize email threads using OpenAI GPT"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def summarize(self, from_email: str, subject: str, body: str) -> dict:
        """
        Generate executive summary of email
        
        Returns:
            {
                "summary": str,
                "next_action": str
            }
        """
        # Truncate body if too long
        max_body_length = 3000
        truncated_body = body[:max_body_length] + "..." if len(body) > max_body_length else body
        
        prompt = SUMMARIZATION_PROMPT.format(
            from_email=from_email,
            subject=subject,
            body=truncated_body
        )
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an executive assistant creating concise email summaries. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=250,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return {
                "summary": result.get("summary", "Email summary unavailable"),
                "next_action": result.get("next_action", "none")
            }
            
        except Exception as e:
            print(f"Summarization error: {e}")
            return {
                "summary": f"Email from {from_email} regarding: {subject}",
                "next_action": "Review email for details"
            }
