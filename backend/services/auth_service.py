from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt

from app.config import settings
from app.models import User
from app.schemas.user import UserCreate

SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]


class AuthService:
    """Handle Google OAuth authentication and JWT token management"""
    
    def __init__(self):
        self.client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }
    
    def get_authorization_url(self, state: str = None) -> tuple[str, str]:
        """Generate Google OAuth authorization URL"""
        flow = Flow.from_client_config(
            self.client_config,
            scopes=SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )
        
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=state
        )
        
        return auth_url, state
    
    async def handle_callback(self, code: str, state: str, db: Session) -> dict:
        """Handle OAuth callback and create/update user"""
        # Exchange code for tokens
        flow = Flow.from_client_config(
            self.client_config,
            scopes=SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
            state=state
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Get user info from Google
        user_info_service = build('oauth2', 'v2', credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        
        # Create or update user in database
        user = db.query(User).filter(User.google_id == user_info['id']).first()
        
        if user:
            # Update existing user
            user.access_token = credentials.token
            user.refresh_token = credentials.refresh_token or user.refresh_token
            user.token_expiry = credentials.expiry
        else:
            # Create new user
            user = User(
                email=user_info['email'],
                google_id=user_info['id'],
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                token_expiry=credentials.expiry,
                onboarding_completed=False
            )
            db.add(user)
        
        db.commit()
        db.refresh(user)
        
        # Generate JWT token
        jwt_token = self.create_access_token(user.id)
        
        return {
            'access_token': jwt_token,
            'token_type': 'bearer',
            'user': user
        }
    
    def create_access_token(self, user_id: str) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": str(user_id),
            "exp": expire
        }
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> str:
        """Verify JWT token and return user_id"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise ValueError("Invalid token")
            return user_id
        except JWTError:
            raise ValueError("Invalid token")
    
    async def refresh_google_token(self, user: User, db: Session) -> User:
        """Refresh Google OAuth token if expired"""
        if user.token_expiry and user.token_expiry < datetime.utcnow():
            credentials = Credentials(
                token=user.access_token,
                refresh_token=user.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET
            )
            
            credentials.refresh()
            
            user.access_token = credentials.token
            user.token_expiry = credentials.expiry
            db.commit()
            db.refresh(user)
        
        return user
