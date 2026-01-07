"""
Unit tests for UserRepository.

Tests all CRUD operations with mocked MongoDB database.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from bson import ObjectId
from pymongo.errors import DuplicateKeyError, PyMongoError

from src.app.db.repositories.user_repository import UserRepository
from src.app.db.models.user import UserInDB


class TestUserRepository:
    """Test suite for UserRepository."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock MongoDB database."""
        db = Mock()
        collection = Mock()
        db.__getitem__ = Mock(return_value=collection)
        return db
    
    @pytest.fixture
    def mock_collection(self, mock_db):
        """Get the mock collection from mock database."""
        return mock_db[UserRepository.COLLECTION_NAME]
    
    @pytest.fixture
    def repository(self, mock_db):
        """Create UserRepository instance with mocked database."""
        with patch.object(UserRepository, '_ensure_indexes'):
            return UserRepository(mock_db)
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing."""
        return {
            "email": "test@example.com",
            "username": "testuser",
            "firstname": "John",
            "lastname": "Doe",
            "password_hash": "hashed_password_123"
        }
    
    @pytest.fixture
    def sample_user_dict(self, sample_user_data):
        """Sample user dictionary as stored in MongoDB."""
        return {
            "_id": ObjectId(),
            "email": "test@example.com",
            "username": "testuser",
            "firstname": "John",
            "lastname": "Doe",
            "password_hash": "hashed_password_123",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
    
    # ==================== Create User Tests ====================
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, repository, mock_collection, sample_user_data):
        """Test successful user creation."""
        # Mock insert_one to return inserted_id
        mock_result = Mock()
        mock_result.inserted_id = ObjectId()
        mock_collection.insert_one.return_value = mock_result
        
        # Create user
        result = await repository.create_user(**sample_user_data)
        
        # Verify result
        assert result is not None
        assert isinstance(result, UserInDB)
        assert result.email == "test@example.com"
        assert result.username == "testuser"
        assert result.firstname == "John"
        assert result.lastname == "Doe"
        
        # Verify insert_one was called
        assert mock_collection.insert_one.called
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, repository, mock_collection, sample_user_data):
        """Test user creation with duplicate email."""
        # Mock DuplicateKeyError
        mock_collection.insert_one.side_effect = DuplicateKeyError("E11000 duplicate key error")
        
        # Attempt to create user
        result = await repository.create_user(**sample_user_data)
        
        # Should return None for duplicates
        assert result is None
    
    @pytest.mark.asyncio
    async def test_create_user_database_error(self, repository, mock_collection, sample_user_data):
        """Test user creation with database error."""
        # Mock PyMongoError
        mock_collection.insert_one.side_effect = PyMongoError("Database connection failed")
        
        # Should raise the error
        with pytest.raises(PyMongoError):
            await repository.create_user(**sample_user_data)
    
    @pytest.mark.asyncio
    async def test_create_user_normalizes_fields(self, repository, mock_collection):
        """Test that user creation normalizes email and username."""
        mock_result = Mock()
        mock_result.inserted_id = ObjectId()
        mock_collection.insert_one.return_value = mock_result
        
        # Create user with uppercase email and username
        result = await repository.create_user(
            email="TEST@EXAMPLE.COM",
            username="TESTUSER",
            firstname="john",
            lastname="doe",
            password_hash="hash123"
        )
        
        # Verify normalization
        assert result.email == "test@example.com"
        assert result.username == "testuser"
        assert result.firstname == "John"  # Capitalized
        assert result.lastname == "Doe"    # Capitalized
    
    # ==================== Get User by Email Tests ====================
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_found(self, repository, mock_collection, sample_user_dict):
        """Test retrieving user by email when user exists."""
        mock_collection.find_one.return_value = sample_user_dict
        
        result = await repository.get_user_by_email("test@example.com")
        
        assert result is not None
        assert isinstance(result, UserInDB)
        assert result.email == "test@example.com"
        
        # Verify find_one was called with normalized email
        mock_collection.find_one.assert_called_once_with({"email": "test@example.com"})
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, repository, mock_collection):
        """Test retrieving user by email when user doesn't exist."""
        mock_collection.find_one.return_value = None
        
        result = await repository.get_user_by_email("notfound@example.com")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_normalizes_input(self, repository, mock_collection, sample_user_dict):
        """Test that email is normalized before query."""
        mock_collection.find_one.return_value = sample_user_dict
        
        await repository.get_user_by_email("  TEST@EXAMPLE.COM  ")
        
        # Should query with lowercase, trimmed email
        mock_collection.find_one.assert_called_once_with({"email": "test@example.com"})
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_database_error(self, repository, mock_collection):
        """Test get_user_by_email with database error."""
        mock_collection.find_one.side_effect = PyMongoError("Connection lost")
        
        with pytest.raises(PyMongoError):
            await repository.get_user_by_email("test@example.com")
    
    # ==================== Get User by Username Tests ====================
    
    @pytest.mark.asyncio
    async def test_get_user_by_username_found(self, repository, mock_collection, sample_user_dict):
        """Test retrieving user by username when user exists."""
        mock_collection.find_one.return_value = sample_user_dict
        
        result = await repository.get_user_by_username("testuser")
        
        assert result is not None
        assert isinstance(result, UserInDB)
        assert result.username == "testuser"
        
        mock_collection.find_one.assert_called_once_with({"username": "testuser"})
    
    @pytest.mark.asyncio
    async def test_get_user_by_username_not_found(self, repository, mock_collection):
        """Test retrieving user by username when user doesn't exist."""
        mock_collection.find_one.return_value = None
        
        result = await repository.get_user_by_username("notfound")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_username_normalizes_input(self, repository, mock_collection, sample_user_dict):
        """Test that username is normalized before query."""
        mock_collection.find_one.return_value = sample_user_dict
        
        await repository.get_user_by_username("  TESTUSER  ")
        
        # Should query with lowercase, trimmed username
        mock_collection.find_one.assert_called_once_with({"username": "testuser"})
    
    # ==================== Get User by ID Tests ====================
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_found(self, repository, mock_collection, sample_user_dict):
        """Test retrieving user by ID when user exists."""
        user_id = str(sample_user_dict["_id"])
        mock_collection.find_one.return_value = sample_user_dict
        
        result = await repository.get_user_by_id(user_id)
        
        assert result is not None
        assert isinstance(result, UserInDB)
        assert str(result.id) == user_id
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, repository, mock_collection):
        """Test retrieving user by ID when user doesn't exist."""
        user_id = str(ObjectId())
        mock_collection.find_one.return_value = None
        
        result = await repository.get_user_by_id(user_id)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_invalid_objectid(self, repository, mock_collection):
        """Test retrieving user with invalid ObjectId."""
        with pytest.raises(ValueError, match="Invalid ObjectId"):
            await repository.get_user_by_id("invalid_id")
    
    # ==================== User Exists Tests ====================
    
    @pytest.mark.asyncio
    async def test_user_exists_email_only(self, repository, mock_collection):
        """Test checking if email exists."""
        mock_collection.count_documents.return_value = 1
        
        result = await repository.user_exists(email="test@example.com")
        
        assert result["email_exists"] is True
        assert result["username_exists"] is False
    
    @pytest.mark.asyncio
    async def test_user_exists_username_only(self, repository, mock_collection):
        """Test checking if username exists."""
        mock_collection.count_documents.return_value = 1
        
        result = await repository.user_exists(username="testuser")
        
        assert result["email_exists"] is False
        assert result["username_exists"] is True
    
    @pytest.mark.asyncio
    async def test_user_exists_both(self, repository, mock_collection):
        """Test checking both email and username."""
        # Return 1 for both queries
        mock_collection.count_documents.return_value = 1
        
        result = await repository.user_exists(email="test@example.com", username="testuser")
        
        assert result["email_exists"] is True
        assert result["username_exists"] is True
        
        # Should be called twice (once for email, once for username)
        assert mock_collection.count_documents.call_count == 2
    
    @pytest.mark.asyncio
    async def test_user_exists_neither(self, repository, mock_collection):
        """Test checking when neither email nor username exists."""
        mock_collection.count_documents.return_value = 0
        
        result = await repository.user_exists(email="new@example.com", username="newuser")
        
        assert result["email_exists"] is False
        assert result["username_exists"] is False
    
    @pytest.mark.asyncio
    async def test_user_exists_normalizes_inputs(self, repository, mock_collection):
        """Test that user_exists normalizes email and username."""
        mock_collection.count_documents.return_value = 0
        
        await repository.user_exists(email="  TEST@EXAMPLE.COM  ", username="  TESTUSER  ")
        
        # Check both calls had normalized values
        calls = mock_collection.count_documents.call_args_list
        assert calls[0][0][0] == {"email": "test@example.com"}
        assert calls[1][0][0] == {"username": "testuser"}
    
    # ==================== Update User Tests ====================
    
    @pytest.mark.asyncio
    async def test_update_user_success(self, repository, mock_collection, sample_user_dict):
        """Test successful user update."""
        user_id = str(sample_user_dict["_id"])
        updated_dict = sample_user_dict.copy()
        updated_dict["firstname"] = "Jane"
        
        mock_collection.find_one_and_update.return_value = updated_dict
        
        result = await repository.update_user(user_id, {"firstname": "Jane"})
        
        assert result is not None
        assert result.firstname == "Jane"
        
        # Verify find_one_and_update was called correctly
        assert mock_collection.find_one_and_update.called
    
    @pytest.mark.asyncio
    async def test_update_user_not_found(self, repository, mock_collection):
        """Test updating non-existent user."""
        user_id = str(ObjectId())
        mock_collection.find_one_and_update.return_value = None
        
        result = await repository.update_user(user_id, {"firstname": "Jane"})
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_user_forbidden_fields(self, repository, mock_collection):
        """Test that forbidden fields cannot be updated."""
        user_id = str(ObjectId())
        
        # Test each forbidden field
        forbidden_updates = [
            {"email": "new@example.com"},
            {"username": "newusername"},
            {"password_hash": "newhash"},
            {"_id": ObjectId()},
            {"created_at": datetime.utcnow()}
        ]
        
        for update in forbidden_updates:
            with pytest.raises(ValueError, match="Cannot update forbidden fields"):
                await repository.update_user(user_id, update)
    
    @pytest.mark.asyncio
    async def test_update_user_adds_updated_at(self, repository, mock_collection, sample_user_dict):
        """Test that update_user automatically adds updated_at timestamp."""
        user_id = str(sample_user_dict["_id"])
        mock_collection.find_one_and_update.return_value = sample_user_dict
        
        await repository.update_user(user_id, {"firstname": "Jane"})
        
        # Check that updated_at was added to the update
        call_args = mock_collection.find_one_and_update.call_args
        update_dict = call_args[0][1]["$set"]
        assert "updated_at" in update_dict
        assert isinstance(update_dict["updated_at"], datetime)
    
    @pytest.mark.asyncio
    async def test_update_user_invalid_objectid(self, repository, mock_collection):
        """Test updating user with invalid ObjectId."""
        with pytest.raises(ValueError, match="Invalid ObjectId"):
            await repository.update_user("invalid_id", {"firstname": "Jane"})
    
    # ==================== Deactivate User Tests ====================
    
    @pytest.mark.asyncio
    async def test_deactivate_user_success(self, repository, mock_collection, sample_user_dict):
        """Test successful user deactivation."""
        user_id = str(sample_user_dict["_id"])
        deactivated_dict = sample_user_dict.copy()
        deactivated_dict["is_active"] = False
        
        mock_collection.find_one_and_update.return_value = deactivated_dict
        
        result = await repository.deactivate_user(user_id)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_deactivate_user_not_found(self, repository, mock_collection):
        """Test deactivating non-existent user."""
        user_id = str(ObjectId())
        mock_collection.find_one_and_update.return_value = None
        
        result = await repository.deactivate_user(user_id)
        
        assert result is False
    
    # ==================== Index Creation Tests ====================
    
    def test_ensure_indexes_called_on_init(self, mock_db):
        """Test that indexes are created on repository initialization."""
        mock_collection = mock_db[UserRepository.COLLECTION_NAME]
        
        # Create repository (should call _ensure_indexes)
        repo = UserRepository(mock_db)
        
        # Access collection property to trigger lazy initialization of indexes
        _ = repo.collection
        
        # Verify create_index was called for both email and username
        assert mock_collection.create_index.call_count == 2
        
        # Check the calls
        calls = mock_collection.create_index.call_args_list
        
        # First call: email index
        assert calls[0][0][0] == "email"
        assert calls[0][1]["unique"] is True
        assert calls[0][1]["name"] == "email_unique"
        
        # Second call: username index
        assert calls[1][0][0] == "username"
        assert calls[1][1]["unique"] is True
        assert calls[1][1]["name"] == "username_unique"
    
    def test_ensure_indexes_handles_errors(self, mock_db):
        """Test that index creation errors don't crash initialization."""
        mock_collection = mock_db[UserRepository.COLLECTION_NAME]
        mock_collection.create_index.side_effect = PyMongoError("Index already exists")
        
        # Should not raise exception
        repo = UserRepository(mock_db)
        
        # Access collection property to trigger lazy initialization
        _ = repo.collection
        
        # Repository should still be created
        assert repo is not None
