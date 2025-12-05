from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")

if not MONGODB_URL:
    print("Warning: MONGODB_URL not found in environment variables")

client = AsyncIOMotorClient(MONGODB_URL)
db = client.luma_db

async def get_db():
    return db
