import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load the keys from your .env file
load_dotenv()

def get_supabase_client() -> Client:
    """Connects to your remote Supabase Postgres database."""
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    return create_client(url, key)

# --- OTP AUTHENTICATION FUNCTIONS ---

def send_magic_code(email: str):
    """Triggers Supabase to send a 6-digit OTP to the user's email."""
    supabase = get_supabase_client()
    try:
        supabase.auth.sign_in_with_otp({"email": email})
        return True
    except Exception as e:
        print(f"Error sending OTP: {e}")
        return False

def verify_magic_code(email: str, code: str):
    """Verifies the 6-digit code with the Supabase Auth server."""
    supabase = get_supabase_client()
    try:
        response = supabase.auth.verify_otp({"email": email, "token": code, "type": "email"})
        return response.user 
    except Exception as e:
        print(f"Error verifying OTP: {e}")
        return None

# --- DATABASE READ/WRITE FUNCTIONS ---

def get_user(email: str):
    """Fetches a user profile by email."""
    supabase = get_supabase_client()
    response = supabase.table("users").select("*").eq("email", email).execute()
    
    if len(response.data) > 0:
        return response.data[0]
    return None

def create_user(username: str, email: str):
    """Inserts a brand new user into the database."""
    supabase = get_supabase_client()
    response = supabase.table("users").insert(
        {"username": username, "email": email, "query_count": 0}
    ).execute()
    return response.data[0]

def increment_query_count(email: str, current_count: int):
    """Updates the cloud database to permanently save their usage."""
    supabase = get_supabase_client()
    new_count = current_count + 1
    
    supabase.table("users").update({"query_count": new_count}).eq("email", email).execute()
    return new_count