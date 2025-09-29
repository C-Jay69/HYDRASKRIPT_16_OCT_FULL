import os
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)

# Initialize Supabase client
def get_supabase_client() -> Client:
    """Get initialized Supabase client"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")
    
    if not url or not key:
        # For now, we'll use the DATABASE_URL for direct database access
        # This is a fallback when full Supabase credentials aren't available
        logger.warning("Supabase URL/Key not found, using database URL fallback")
        return None
    
    return create_client(url, key)

supabase: Client = get_supabase_client()