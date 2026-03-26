from fastapi import APIRouter, HTTPException, status
from app.schemas.db_schemas import UserSignup, UserLogin, TokenResponse, ForgotPassword, ResetPassword
from app.core.auth import hash_password, verify_password, create_access_token, create_reset_token, decode_reset_token
from app.db.client import supabase_client
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/signup", response_model=TokenResponse)
def signup(user: UserSignup):
    """
    Register a new student. Returns a JWT token on success.
    """
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not configured")

    # Check if email already exists
    try:
        existing = supabase_client.table("users").select("id").eq("email", user.email).execute()
        if existing.data and len(existing.data) > 0:
            raise HTTPException(status_code=400, detail="Email already registered")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking existing user: {e}")
        raise HTTPException(status_code=500, detail="Database error")

    # Determine role
    from app.core.config import settings
    role = "student"
    if user.admin_code and user.admin_code == settings.ADMIN_SECRET_KEY:
        role = "admin"

    # Create user with hashed password
    hashed_pw = hash_password(user.password)

    try:
        response = supabase_client.table("users").insert({
            "username": user.username,
            "email": user.email,
            "password_hash": hashed_pw,
            "role": role
        }).execute()

        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create user")

        new_user = response.data[0]
        token = create_access_token(
            user_id=new_user["id"],
            email=new_user["email"],
            username=new_user["username"],
            role=new_user.get("role", "student")
        )

        return TokenResponse(
            access_token=token,
            user={
                "id": new_user["id"],
                "username": new_user["username"],
                "email": new_user["email"],
                "role": new_user.get("role", "student")
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin):
    """
    Login with email and password. Returns a JWT token on success.
    """
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        response = supabase_client.table("users").select("*").eq("email", credentials.email).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        user = response.data[0]

        if not verify_password(credentials.password, user.get("password_hash", "")):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = create_access_token(
            user_id=user["id"],
            email=user["email"],
            username=user["username"],
            role=user.get("role", "student")
        )

        return TokenResponse(
            access_token=token,
            user={
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "role": user.get("role", "student")
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/forgot-password")
def forgot_password(request: ForgotPassword):
    """
    Generate a password reset token and "simulate" sending it via email.
    """
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not configured")

    # Verify if user exists
    try:
        response = supabase_client.table("users").select("id").eq("email", request.email).execute()
        if not response.data or len(response.data) == 0:
            # Return 200 anyway to prevent email enumeration attacks
            return {"message": "If that email is registered, a reset link has been sent."}
    except Exception as e:
        logger.error(f"Error checking user email: {e}")
        raise HTTPException(status_code=500, detail="Database error")

    # Generate token
    reset_token = create_reset_token(request.email)
    
    # -----------------------------------------------------
    # SIMULATING EMAIL SEND IN CONSOLE
    # -----------------------------------------------------
    reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
    print("\n" + "="*50)
    print("📧 MOCK EMAIL SENT 📧")
    print(f"To: {request.email}")
    print(f"Subject: Password Reset Request")
    print(f"Click the link below to reset your password:")
    print(f"{reset_link}")
    print("="*50 + "\n")
    # -----------------------------------------------------

    return {"message": "If that email is registered, a reset link has been sent.", "dev_token": reset_token}


@router.post("/reset-password")
def reset_password(request: ResetPassword):
    """
    Reset a user's password using a valid reset token.
    """
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not configured")

    email = decode_reset_token(request.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    hashed_pw = hash_password(request.new_password)

    try:
        # Update user's password in Supabase
        response = supabase_client.table("users").update({
            "password_hash": hashed_pw
        }).eq("email", email).execute()

        if not response.data:
            raise HTTPException(status_code=400, detail="Could not update password. User may not exist.")

        return {"message": "Password successfully reset. You can now login with the new password."}

    except Exception as e:
        logger.error(f"Reset password error: {e}")
        raise HTTPException(status_code=500, detail="Reset password failed")
