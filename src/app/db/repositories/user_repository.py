"""
User Repository for MongoDB operations.

This module provides CRUD operations for the User model using MongoDB.
Handles user creation, retrieval, and duplicate checking with proper error handling.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, PyMongoError
from bson import ObjectId

from src.app.db.models.user import User, UserInDB
from src.app.core.utils.logger import get_logger

logger = get_logger(__name__)


class UserRepository:
    """
    Repository for User model operations in MongoDB.
    
    Supports both dependency injection and automatic connection management.
    If no database is provided, will automatically get MongoDB connection.
    """
    
    COLLECTION_NAME = "users"
    _instance: Optional['UserRepository'] = None
    
    def __init__(self, db: Optional[Database] = None):
        """
        Initialize the user repository.
        
        Args:
            db: MongoDB database instance (optional - will auto-connect if not provided)
        """
        self._db = db
        self._collection = None
        self._indexes_ensured = False
    
    @property
    def db(self) -> Database:
        """Get database instance, connecting if necessary."""
        if self._db is None:
            from src.app.connections import ConnectionFactory, ConnectionType
            connection_manager = ConnectionFactory.get_connection_manager(ConnectionType.MONGODB)
            connection_manager.connect()
            self._db = connection_manager.get_database()
            logger.info("Auto-connected to MongoDB for UserRepository")
        return self._db
    
    @property
    def collection(self):
        """Get collection, ensuring indexes on first access."""
        if self._collection is None:
            self._collection = self.db[self.COLLECTION_NAME]
            if not self._indexes_ensured:
                self._ensure_indexes()
                self._indexes_ensured = True
        return self._collection
    
    def _ensure_indexes(self):
        """Create unique indexes for email and username if they don't exist."""
        try:
            # Create unique index on email
            self.collection.create_index("email", unique=True, name="email_unique")
            # Create unique index on username
            self.collection.create_index("username", unique=True, name="username_unique")
            logger.info("User collection indexes ensured")
        except PyMongoError as e:
            logger.error(f"Failed to create indexes: {e}", exc_info=True)
            # Don't raise - indexes might already exist
    
    async def create_user(
        self,
        email: str,
        username: str,
        firstname: str,
        lastname: str,
        password_hash: str
    ) -> Optional[UserInDB]:
        """
        Create a new user in the database.
        
        Args:
            email: User's email address
            username: User's username
            firstname: User's first name
            lastname: User's last name
            password_hash: Hashed password
            
        Returns:
            UserInDB object if successful, None if duplicate email/username
            
        Raises:
            PyMongoError: For database errors other than duplicates
        """
        try:
            # Create User model (will validate and normalize fields)
            user = User(
                email=email,
                username=username,
                firstname=firstname,
                lastname=lastname,
                password_hash=password_hash
            )
            
            # Convert to dict for MongoDB insertion
            user_dict = user.to_dict()
            
            # Insert into database
            result = self.collection.insert_one(user_dict)
            
            # Add MongoDB ID as string and return UserInDB
            user_dict["_id"] = str(result.inserted_id)
            return UserInDB(**user_dict)
            
        except DuplicateKeyError as e:
            # Log but don't raise - caller will handle duplicate check
            logger.warning(f"Duplicate user creation attempt: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating user: {e}", exc_info=True)
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """
        Retrieve a user by email address.
        
        Args:
            email: User's email address
            
        Returns:
            UserInDB object if found, None otherwise
        """
        try:
            # Normalize email to lowercase for comparison
            normalized_email = email.lower().strip()
            user_dict = self.collection.find_one({"email": normalized_email})
            
            if user_dict:
                # Convert ObjectId to string for Pydantic
                user_dict["_id"] = str(user_dict["_id"])
                return UserInDB(**user_dict)
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving user by email: {e}", exc_info=True)
            raise
    
    async def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        """
        Retrieve a user by username.
        
        Args:
            username: User's username
            
        Returns:
            UserInDB object if found, None otherwise
        """
        try:
            # Normalize username to lowercase for comparison
            normalized_username = username.lower().strip()
            user_dict = self.collection.find_one({"username": normalized_username})
            
            if user_dict:
                # Convert ObjectId to string for Pydantic
                user_dict["_id"] = str(user_dict["_id"])
                return UserInDB(**user_dict)
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving user by username: {e}", exc_info=True)
            raise
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """
        Retrieve a user by MongoDB ObjectId.
        
        Args:
            user_id: MongoDB ObjectId as string
            
        Returns:
            UserInDB object if found, None otherwise
            
        Raises:
            ValueError: If user_id is not a valid ObjectId
        """
        try:
            # Validate and convert to ObjectId
            if not ObjectId.is_valid(user_id):
                raise ValueError(f"Invalid ObjectId: {user_id}")
            
            user_dict = self.collection.find_one({"_id": ObjectId(user_id)})
            
            if user_dict:
                # Convert ObjectId to string for Pydantic
                user_dict["_id"] = str(user_dict["_id"])
                return UserInDB(**user_dict)
            return None
            
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Error retrieving user by id: {e}", exc_info=True)
            raise
    
    async def user_exists(self, email: Optional[str] = None, username: Optional[str] = None) -> Dict[str, bool]:
        """
        Check if a user exists by email and/or username.
        
        Args:
            email: Email address to check (optional)
            username: Username to check (optional)
            
        Returns:
            Dict with keys 'email_exists' and 'username_exists'
            
        Example:
            >>> await repo.user_exists(email="test@example.com", username="testuser")
            {'email_exists': True, 'username_exists': False}
        """
        result = {
            "email_exists": False,
            "username_exists": False
        }
        
        try:
            if email:
                normalized_email = email.lower().strip()
                email_count = self.collection.count_documents({"email": normalized_email}, limit=1)
                result["email_exists"] = email_count > 0
            
            if username:
                normalized_username = username.lower().strip()
                username_count = self.collection.count_documents({"username": normalized_username}, limit=1)
                result["username_exists"] = username_count > 0
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking user existence: {e}", exc_info=True)
            raise
    
    async def update_user(self, user_id: str, update_fields: Dict[str, Any]) -> Optional[UserInDB]:
        """
        Update user fields.
        
        Args:
            user_id: MongoDB ObjectId as string
            update_fields: Dictionary of fields to update
            
        Returns:
            Updated UserInDB object if successful, None if user not found
            
        Note:
            - Automatically updates 'updated_at' timestamp
            - Does not allow updating 'email', 'username', or 'password_hash' directly
        """
        try:
            if not ObjectId.is_valid(user_id):
                raise ValueError(f"Invalid ObjectId: {user_id}")
            
            # Prevent updating sensitive fields directly
            forbidden_fields = {"email", "username", "password_hash", "_id", "created_at"}
            if any(field in update_fields for field in forbidden_fields):
                raise ValueError(f"Cannot update forbidden fields: {forbidden_fields}")
            
            # Add updated_at timestamp
            update_fields["updated_at"] = datetime.utcnow()
            
            # Update and return updated document
            result = self.collection.find_one_and_update(
                {"_id": ObjectId(user_id)},
                {"$set": update_fields},
                return_document=True  # Return updated document
            )
            
            if result:
                # Convert ObjectId to string for Pydantic
                result["_id"] = str(result["_id"])
                return UserInDB(**result)
            return None
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error updating user: {e}", exc_info=True)
            raise
    
    async def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate a user account (soft delete).
        
        Args:
            user_id: MongoDB ObjectId as string
            
        Returns:
            True if successful, False if user not found
        """
        try:
            result = await self.update_user(user_id, {"is_active": False})
            return result is not None
        except Exception as e:
            logger.error(f"Error deactivating user: {e}", exc_info=True)
            raise


# Singleton instance - auto-connects to MongoDB when needed
# Following the same pattern as password_manager
user_repository = UserRepository()
