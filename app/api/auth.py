"""User authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets
import os
import uuid

from ..storage.tenant_db import TenantDatabase

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Password hashing - use bcrypt directly to avoid passlib compatibility issues
try:
    import bcrypt
    USE_BCRYPT_DIRECT = True
except ImportError:
    USE_BCRYPT_DIRECT = False
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY", "dev-secret-key-change-in-production"))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30  # 30 days

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# Pydantic models
class UserRegistration(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    tenant_id: str
    user_id: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    email_verified: bool
    tenant_id: Optional[str]


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    new_password: str

    @validator("new_password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    if USE_BCRYPT_DIRECT:
        import bcrypt
        # Handle both bytes and string
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        if isinstance(plain_password, str):
            plain_password = plain_password.encode('utf-8')
        return bcrypt.checkpw(plain_password, hashed_password)
    else:
        return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    if USE_BCRYPT_DIRECT:
        import bcrypt
        # Ensure password is bytes
        if isinstance(password, str):
            password = password.encode('utf-8')
        # Generate salt and hash
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password, salt)
        # Return as string
        return hashed.decode('utf-8')
    else:
        return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[dict]:
    """Get current user from JWT token."""
    if not token:
        return None
    
    payload = verify_token(token)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    
    if not user_id:
        return None
    
    return {"user_id": user_id, "tenant_id": tenant_id}


# Routes
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegistration):
    """
    Register a new user.
    Creates a user account and automatically creates a tenant for them.
    """
    # Import here to avoid circular dependency
    from ..storage.tenant_db import TenantDatabase
    db = TenantDatabase(tenant_id=None)  # No tenant context for admin operations
    
    # Check if user already exists
    with db._conn() as conn:
        if db.use_postgres:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = %s", [user_data.email])
        else:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", [user_data.email])
        
        existing = cursor.fetchone()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Generate user ID and verification token
    user_id = str(uuid.uuid4())
    verification_token = secrets.token_urlsafe(32)
    verification_expires = datetime.now(timezone.utc) + timedelta(days=7)
    
    # Hash password
    password_hash = get_password_hash(user_data.password)
    
    # Create tenant for the user
    tenant_id = str(uuid.uuid4())
    tenant_email = user_data.email
    
    # Set trial expiration to 7 days from now
    trial_ends_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    # Insert tenant first (to satisfy FK) then user
    with db._conn() as conn:
        if db.use_postgres:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO tenants (id, email, subscription_status, subscription_tier, trial_ends_at, owner_user_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [tenant_id, tenant_email, "trial", "free", trial_ends_at, user_id],
            )

            cursor.execute(
                """
                INSERT INTO users (id, email, password_hash, full_name, email_verification_token, email_verification_expires, tenant_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    user_id,
                    user_data.email,
                    password_hash,
                    user_data.full_name,
                    verification_token,
                    verification_expires,
                    tenant_id,
                ],
            )
        else:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO tenants (id, email, subscription_status, subscription_tier, trial_ends_at, owner_user_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [tenant_id, tenant_email, "trial", "free", trial_ends_at.isoformat(), user_id],
            )

            cursor.execute(
                """
                INSERT INTO users (id, email, password_hash, full_name, email_verification_token, email_verification_expires, tenant_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    user_id,
                    user_data.email,
                    password_hash,
                    user_data.full_name,
                    verification_token,
                    verification_expires.isoformat(),
                    tenant_id,
                ],
            )
    
    # TODO: Send verification email
    # For now, we'll return the verification token in the response (remove in production)
    
    return UserResponse(
        id=user_id,
        email=user_data.email,
        full_name=user_data.full_name,
        email_verified=False,
        tenant_id=tenant_id,
    )


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login user and return JWT token.
    Uses email as username.
    """
    db = TenantDatabase(tenant_id=None)
    
    # Get user by email
    with db._conn() as conn:
        if db.use_postgres:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, password_hash, tenant_id, email_verified FROM users WHERE email = %s",
                [form_data.username],  # OAuth2PasswordRequestForm uses username field
            )
        else:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, password_hash, tenant_id, email_verified FROM users WHERE email = ?",
                [form_data.username],
            )
        
        row = cursor.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if db.use_postgres:
        user_id, password_hash, tenant_id, email_verified = row
    else:
        user_id = row["id"]
        password_hash = row["password_hash"]
        tenant_id = row["tenant_id"]
        email_verified = bool(row["email_verified"])
    
    # Verify password
    if not verify_password(form_data.password, password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if email is verified (optional enforcement)
    # if not email_verified:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Email not verified"
    #     )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user_id, "tenant_id": tenant_id or ""}
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        tenant_id=tenant_id or "",
        user_id=user_id,
    )


@router.post("/verify-email")
async def verify_email(token: str):
    """Verify user email address."""
    db = TenantDatabase(tenant_id=None)
    
    # Find user by verification token
    with db._conn() as conn:
        if db.use_postgres:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, email_verification_expires FROM users 
                WHERE email_verification_token = %s
                """,
                [token],
            )
        else:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, email_verification_expires FROM users 
                WHERE email_verification_token = ?
                """,
                [token],
            )
        
        row = cursor.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )
    
    if db.use_postgres:
        user_id, expires = row
        expires_dt = expires
    else:
        user_id = row["id"]
        expires_str = row["email_verification_expires"]
        expires_dt = datetime.fromisoformat(expires_str.replace("Z", "+00:00")) if expires_str else None
    
    # Check if token expired
    if expires_dt and datetime.now(timezone.utc) > expires_dt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token expired"
        )
    
    # Mark email as verified
    with db._conn() as conn:
        if db.use_postgres:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE users 
                SET email_verified = TRUE, 
                    email_verification_token = NULL,
                    email_verification_expires = NULL
                WHERE id = %s
                """,
                [user_id],
            )
        else:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE users 
                SET email_verified = 1, 
                    email_verification_token = NULL,
                    email_verification_expires = NULL
                WHERE id = ?
                """,
                [user_id],
            )
    
    return {"message": "Email verified successfully"}


@router.post("/forgot-password")
async def forgot_password(request: PasswordResetRequest):
    """Send password reset email."""
    db = TenantDatabase(tenant_id=None)
    
    # Find user by email
    with db._conn() as conn:
        if db.use_postgres:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = %s", [request.email])
        else:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", [request.email])
        
        row = cursor.fetchone()
    
    # Don't reveal if email exists (security best practice)
    if not row:
        return {"message": "If the email exists, a password reset link has been sent"}
    
    user_id = row[0] if db.use_postgres else row["id"]
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Store reset token
    with db._conn() as conn:
        if db.use_postgres:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE users 
                SET password_reset_token = %s, password_reset_expires = %s
                WHERE id = %s
                """,
                [reset_token, reset_expires, user_id],
            )
        else:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE users 
                SET password_reset_token = ?, password_reset_expires = ?
                WHERE id = ?
                """,
                [reset_token, reset_expires.isoformat(), user_id],
            )
    
    # TODO: Send password reset email
    # For now, we'll return the token (remove in production)
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    reset_url = f"{frontend_url}/reset-password?token={reset_token}"
    
    return {"message": "If the email exists, a password reset link has been sent", "reset_url": reset_url}


@router.post("/reset-password")
async def reset_password(request: PasswordReset):
    """Reset password with token."""
    db = TenantDatabase(tenant_id=None)
    
    # Find user by reset token
    with db._conn() as conn:
        if db.use_postgres:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, password_reset_expires FROM users 
                WHERE password_reset_token = %s
                """,
                [request.token],
            )
        else:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, password_reset_expires FROM users 
                WHERE password_reset_token = ?
                """,
                [request.token],
            )
        
        row = cursor.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
    
    if db.use_postgres:
        user_id, expires = row
        expires_dt = expires
    else:
        user_id = row["id"]
        expires_str = row["password_reset_expires"]
        expires_dt = datetime.fromisoformat(expires_str.replace("Z", "+00:00")) if expires_str else None
    
    # Check if token expired
    if expires_dt and datetime.now(timezone.utc) > expires_dt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token expired"
        )
    
    # Update password
    password_hash = get_password_hash(request.new_password)
    
    with db._conn() as conn:
        if db.use_postgres:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE users 
                SET password_hash = %s,
                    password_reset_token = NULL,
                    password_reset_expires = NULL
                WHERE id = %s
                """,
                [password_hash, user_id],
            )
        else:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE users 
                SET password_hash = ?,
                    password_reset_token = NULL,
                    password_reset_expires = NULL
                WHERE id = ?
                """,
                [password_hash, user_id],
            )
    
    return {"message": "Password reset successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user_id = current_user["user_id"]
    db = TenantDatabase(tenant_id=None)
    
    with db._conn() as conn:
        if db.use_postgres:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, email, full_name, email_verified, tenant_id FROM users WHERE id = %s",
                [user_id],
            )
        else:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, email, full_name, email_verified, tenant_id FROM users WHERE id = ?",
                [user_id],
            )
        
        row = cursor.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if db.use_postgres:
        user_id, email, full_name, email_verified, tenant_id = row
    else:
        user_id = row["id"]
        email = row["email"]
        full_name = row["full_name"]
        email_verified = bool(row["email_verified"])
        tenant_id = row["tenant_id"]
    
    return UserResponse(
        id=user_id,
        email=email,
        full_name=full_name,
        email_verified=email_verified,
        tenant_id=tenant_id,
    )

