import json
from openai import AsyncOpenAI
from app.config import settings
from app.ai.prompts import PRIORITY_SCORING_PROMPT


class PriorityScorer:
    """Score email priority using OpenAI GPT"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def score(
        self,
        from_email: str,
        subject: str,
        body: str,
        important_contacts: list[str] = None,
        working_hours: str = "9 AM - 5 PM"
    ) -> dict:
        """
        Score email priority from 1-100
        
        Returns:
            {
                "priority_score": int,
                "factors": dict,
                "reasoning": str
            }
        """
        # Truncate body if too long
        max_body_length = 2000
        truncated_body = body[:max_body_length] + "..." if len(body) > max_body_length else body
        
        # Format important contacts
        contacts_str = ", ".join(important_contacts) if important_contacts else "None specified"
        
        prompt = PRIORITY_SCORING_PROMPT.format(
            from_email=from_email,
            subject=subject,
            body=truncated_body,
            important_contacts=contacts_str,
            working_hours=working_hours
        )
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a priority scoring assistant. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Ensure score is within bounds
            priority_score = max(1, min(100, result.get("priority_score", 50)))
            
            return {
                "priority_score": priority_score,
                "factors": result.get("factors", {}),
                "reasoning": result.get("reasoning", "")
            }
            
        except Exception as e:
            # Fallback to medium priority on error
            print(f"Priority scoring error: {e}")
            return {
                "priority_score": 50,
                "factors": {},
                "reasoning": "Error during priority scoring"
            }
