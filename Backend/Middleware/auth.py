import firebase_admin
from firebase_admin import credentials, auth
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from dotenv import load_dotenv

load_dotenv()

try:
    firebase_admin.get_app()
except ValueError:
    from pathlib import Path
    key_path = Path(__file__).resolve().parent.parent / "serviceAccountKey.json"
    
    cred = credentials.Certificate(str(key_path)) if key_path.exists() else None
    
    if cred:
        firebase_admin.initialize_app(cred)
    else:
        print(f"⚠️ Warning: Service Account Key not found at {key_path}")
        firebase_admin.initialize_app(options={'projectId': 'luma-362fc'})

security = HTTPBearer()

from Database.database import get_db

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']
        email = decoded_token.get('email')
        name = decoded_token.get('name')
        picture = decoded_token.get('picture')
        
        from Services.credit_service import CreditService
        await CreditService.initialize_user(uid, email, name, picture)
        
        return decoded_token
    except Exception as e:
        print(f"❌ Auth Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
