import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import HTTPException
from app.auth import get_current_user
from fastapi.security import HTTPAuthorizationCredentials

# Mock Settings
@pytest.fixture
def mock_settings():
    with patch("app.auth.settings") as mock:
        mock.ELITE_API_KEY = "test-secret-key"
        mock.ENV = "production"
        yield mock

# Mock DB
@pytest.fixture
def mock_db():
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    db.add = MagicMock() # .add is synchronous
    return db

@pytest.mark.asyncio
async def test_auth_valid_api_key_bypass(mock_settings, mock_db):
    """Test that valid API KEY bypass works (e.g. for E2E)"""
    # Simulate API Key Header
    user = await get_current_user(credentials=None, api_key="test-secret-key", db=mock_db)
    assert user.role == "admin"
    assert user.uid == "demo_user"

@pytest.mark.asyncio
async def test_auth_missing_creds(mock_settings, mock_db):
    """Test 401 when no creds provided"""
    with pytest.raises(HTTPException) as exc:
        await get_current_user(credentials=None, api_key=None, db=mock_db)
    assert exc.value.status_code == 401

@pytest.mark.asyncio
async def test_auth_firebase_token_success(mock_settings, mock_db):
    """Test valid Firebase Bearer Token"""
    
    # Mock Firebase Admin
    with patch("app.auth.firebase_auth.verify_id_token") as mock_verify:
        mock_verify.return_value = {
            "uid": "test_user_123",
            "email": "test@example.com"
        }
        
        # Mock DB User lookup (return None to trigger auto-create path)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")
        
        user = await get_current_user(credentials=creds, api_key=None, db=mock_db)
        
        assert user.uid == "test_user_123"
        assert user.role == "client" # Default role
        # Verify user was added to DB
        mock_db.add.assert_called()

@pytest.mark.asyncio
async def test_auth_firebase_token_invalid(mock_settings, mock_db):
    """Test invalid Firebase Token"""
    with patch("app.auth.firebase_auth.verify_id_token", side_effect=Exception("Invalid token")):
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad_token")
        with pytest.raises(HTTPException) as exc:
            await get_current_user(credentials=creds, api_key=None, db=mock_db)
        assert exc.value.status_code == 401
