"""
Secure database operations module with parameterized queries
Prevents SQL injection attacks
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import select, insert, update, delete
import bcrypt
import secrets
import hashlib
import hmac

logger = logging.getLogger(__name__)


class SecureDatabase:
    """Secure database operations with SQL injection prevention"""
    
    def __init__(self, database_url: str):
        """Initialize secure database connection"""
        # Use connection pooling with security settings
        self.engine = create_engine(
            database_url,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,   # Recycle connections after 1 hour
            echo=False,          # Never log SQL in production
            future=True          # Use SQLAlchemy 2.0 style
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        self.metadata = MetaData()
        
    @contextmanager
    def get_session(self) -> Session:
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    def execute_safe_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute parameterized query safely
        NEVER use string formatting or concatenation
        """
        with self.get_session() as session:
            try:
                # Always use parameterized queries
                result = session.execute(
                    text(query),
                    params or {}
                )
                
                # Convert to dictionary list for easier handling
                if result.returns_rows:
                    return [dict(row._mapping) for row in result]
                return []
                
            except SQLAlchemyError as e:
                logger.error(f"Query execution failed: {e}")
                raise
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Safely retrieve user by username
        Prevents SQL injection through parameterized query
        """
        query = """
            SELECT id, username, password_hash, email, role, created_at
            FROM users
            WHERE username = :username
            AND active = true
            LIMIT 1
        """
        
        results = self.execute_safe_query(
            query,
            {"username": username}
        )
        
        return results[0] if results else None
    
    def validate_user_login(
        self,
        username: str,
        password: str
    ) -> Optional[Dict[str, Any]]:
        """
        Secure user authentication with bcrypt
        """
        user = self.get_user_by_username(username)
        
        if not user:
            # Perform dummy hash to prevent timing attacks
            bcrypt.checkpw(b"dummy", b"$2b$12$dummy.hash.to.prevent.timing")
            return None
        
        # Verify password with bcrypt (never MD5!)
        if bcrypt.checkpw(
            password.encode('utf-8'),
            user['password_hash'].encode('utf-8')
        ):
            # Remove password hash from return
            user.pop('password_hash', None)
            return user
        
        return None
    
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: str = 'user'
    ) -> Optional[int]:
        """
        Create user with secure password hashing
        """
        # Hash password with bcrypt (cost factor 12)
        password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt(rounds=12)
        ).decode('utf-8')
        
        query = """
            INSERT INTO users (username, email, password_hash, role, created_at, active)
            VALUES (:username, :email, :password_hash, :role, :created_at, true)
            RETURNING id
        """
        
        try:
            results = self.execute_safe_query(
                query,
                {
                    "username": username,
                    "email": email,
                    "password_hash": password_hash,
                    "role": role,
                    "created_at": datetime.utcnow()
                }
            )
            return results[0]['id'] if results else None
            
        except SQLAlchemyError as e:
            logger.error(f"User creation failed: {e}")
            return None
    
    def search_items(
        self,
        search_term: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Safe search with SQL injection prevention
        """
        # Sanitize and validate inputs
        limit = min(max(1, limit), 1000)  # Cap at 1000
        offset = max(0, offset)
        
        # Use parameterized LIKE query
        query = """
            SELECT id, name, description, created_at
            FROM items
            WHERE (
                name ILIKE :search_pattern
                OR description ILIKE :search_pattern
            )
            AND active = true
            ORDER BY created_at DESC
            LIMIT :limit
            OFFSET :offset
        """
        
        # Add wildcards safely
        search_pattern = f"%{search_term}%"
        
        return self.execute_safe_query(
            query,
            {
                "search_pattern": search_pattern,
                "limit": limit,
                "offset": offset
            }
        )
    
    def prevent_mass_assignment(
        self,
        table_name: str,
        data: Dict[str, Any],
        allowed_fields: List[str]
    ) -> Dict[str, Any]:
        """
        Prevent mass assignment attacks by filtering allowed fields
        """
        return {
            key: value
            for key, value in data.items()
            if key in allowed_fields
        }
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure random token"""
        return secrets.token_urlsafe(length)
    
    def hash_token(self, token: str, salt: str) -> str:
        """Create secure hash of token for storage"""
        return hashlib.pbkdf2_hmac(
            'sha256',
            token.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        ).hex()
    
    def verify_token(self, token: str, salt: str, stored_hash: str) -> bool:
        """Verify token against stored hash"""
        computed_hash = self.hash_token(token, salt)
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(computed_hash, stored_hash)


# Example usage with connection pooling
class SecureDatabasePool:
    """Database connection pool for production use"""
    
    _instance = None
    
    def __new__(cls, database_url: str):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.db = SecureDatabase(database_url)
        return cls._instance
    
    @property
    def database(self) -> SecureDatabase:
        return self.db