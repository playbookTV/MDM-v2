"""
Supabase client configuration and initialization
"""

import logging
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Supabase client instance
supabase: Client = None

async def init_supabase():
    """Initialize Supabase client"""
    global supabase
    
    try:
        supabase = create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_SECRET_KEY  # Use service role key for backend
        )
        
        # Test connection with a simple query
        result = supabase.table("datasets").select("count").execute()
        logger.info("✅ Supabase connection established successfully")
        return supabase
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to Supabase: {e}")
        raise

def get_supabase() -> Client:
    """Get Supabase client instance"""
    if supabase is None:
        raise RuntimeError("Supabase client not initialized. Call init_supabase() first.")
    return supabase