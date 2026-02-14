import json
from openai import AsyncOpenAI
from app.config import settings
from app.ai.prompts import CLASSIFICATION_PROMPT
from app.models.email import EmailClassification


class EmailClassifier:
    """Classify emails using OpenAI GPT"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def classify(self, from_email: str, subject: str, body: str) -> dict:
        """
        Classify an email into one of: urgent, action_required, fyi, spam
        
        Returns:
            {
                "classification": EmailClassification,
                "reasoning": str
            }
        """
        # Truncate body if too long (to save tokens)
        max_body_length = 2000
        truncated_body = body[:max_body_length] + "..." if len(body) > max_body_length else body
        
        prompt = CLASSIFICATION_PROMPT.format(
            from_email=from_email,
            subject=subject,
            body=truncated_body
        )
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
              messages=[
                    {"role": "system", "content": "You are an email classification assistant. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Map classification to enum
            classification_map = {
                "urgent": EmailClassification.URGENT,
                "action_required": EmailClassification.ACTION_REQUIRED,
                "fyi": EmailClassification.FYI,
                "spam": EmailClassification.SPAM
            }
            
            classification = classification_map.get(
                result.get("classification", "fyi"),
                EmailClassification.FYI
            )
            
            return {
                "classification": classification,
                "reasoning": result.get("reasoning", "")
            }
                
        except Exception as e:
            # Fallback classification on error
            print(f"Classification error: {e}")
            return {
                "classification": EmailClassification.FYI,
                "reasoning": "Error during classification"
            }

                messages=[
