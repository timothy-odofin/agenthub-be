"""
Unit tests for /api/v1/chat/capabilities endpoint.

Tests the capabilities API endpoint that serves agent capabilities to clients.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

from app.main import app
from app.core.capabilities import SystemCapabilities


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_capabilities():
    """Clear capabilities before and after each test."""
    SystemCapabilities().clear()
    yield
    SystemCapabilities().clear()


@pytest.fixture
def mock_capabilities():
    """Fixture that populates test capabilities."""
    capabilities = SystemCapabilities()
    
    capabilities.add_capability(
        category="jira",
        name="jira",
        enabled=True,
        display_config={
            "title": "Jira Integration",
            "description": "Manage Jira issues",
            "icon": "jira",
            "example_prompts": ["Create a task", "Search issues"],
            "tags": ["project-management"]
        }
    )
    
    capabilities.add_capability(
        category="confluence",
        name="confluence",
        enabled=True,
        display_config={
            "title": "Confluence Wiki",
            "description": "Search documentation",
            "icon": "confluence",
            "example_prompts": ["Find docs about X"],
            "tags": ["documentation"]
        }
    )
    
    capabilities.add_capability(
        category="github",
        name="github",
        enabled=True,
        display_config={
            "title": "GitHub",
            "description": "Search code and issues",
            "icon": "github",
            "example_prompts": ["Find implementation of X"],
            "tags": ["code"]
        }
    )
    
    return capabilities


class TestGetCapabilitiesEndpoint:
    """Test GET /api/v1/chat/capabilities endpoint."""
    
    def test_get_capabilities_success(self, mock_capabilities):
        """Test successful retrieval of all capabilities."""
        response = client.get("/api/v1/chat/capabilities")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['success'] is True
        assert data['total'] == 3
        assert len(data['capabilities']) == 3
        assert len(data['categories']) == 3
        
        # Verify structure of first capability
        cap = data['capabilities'][0]
        assert 'id' in cap
        assert 'category' in cap
        assert 'title' in cap
        assert 'description' in cap
        assert 'icon' in cap
        assert 'example_prompts' in cap
    
    def test_get_capabilities_empty(self):
        """Test endpoint when no capabilities exist."""
        response = client.get("/api/v1/chat/capabilities")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['success'] is True
        assert data['total'] == 0
        assert len(data['capabilities']) == 0
        assert len(data['categories']) == 0
    
    def test_get_capabilities_filtered_by_category(self, mock_capabilities):
        """Test filtering capabilities by category."""
        response = client.get("/api/v1/chat/capabilities?category=jira")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['success'] is True
        assert data['total'] == 1
        assert len(data['capabilities']) == 1
        assert data['capabilities'][0]['category'] == "jira"
        assert data['capabilities'][0]['title'] == "Jira Integration"
    
    def test_get_capabilities_filter_nonexistent_category(self, mock_capabilities):
        """Test filtering by nonexistent category returns empty."""
        response = client.get("/api/v1/chat/capabilities?category=nonexistent")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['success'] is True
        assert data['total'] == 0
        assert len(data['capabilities']) == 0
    
    def test_get_capabilities_no_authentication_required(self, mock_capabilities):
        """Test that endpoint does not require authentication."""
        # No Authorization header provided
        response = client.get("/api/v1/chat/capabilities")
        
        # Should succeed without authentication
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
    
    def test_get_capabilities_returns_all_fields(self, mock_capabilities):
        """Test that all capability fields are returned."""
        response = client.get("/api/v1/chat/capabilities")
        
        assert response.status_code == 200
        data = response.json()
        
        cap = data['capabilities'][0]
        
        # Required fields
        assert 'id' in cap
        assert 'category' in cap
        assert 'name' in cap
        assert 'title' in cap
        assert 'description' in cap
        assert 'icon' in cap
        assert 'example_prompts' in cap
        assert 'tags' in cap
        
        # Verify types
        assert isinstance(cap['id'], str)
        assert isinstance(cap['title'], str)
        assert isinstance(cap['example_prompts'], list)
        assert isinstance(cap['tags'], list)
    
    def test_get_capabilities_multiple_in_same_category(self):
        """Test multiple capabilities in same category."""
        capabilities = SystemCapabilities()
        
        capabilities.add_capability("test", "tool1", True, {"title": "Tool 1"})
        capabilities.add_capability("test", "tool2", True, {"title": "Tool 2"})
        capabilities.add_capability("other", "tool3", True, {"title": "Tool 3"})
        
        response = client.get("/api/v1/chat/capabilities?category=test")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['total'] == 2
        assert all(c['category'] == "test" for c in data['capabilities'])


class TestCapabilitiesEndpointErrorHandling:
    """Test error handling for capabilities endpoint."""
    
    @patch('app.core.capabilities.system_capabilities.SystemCapabilities.get_capabilities')
    def test_get_capabilities_exception_handling(self, mock_get_cap):
        """Test that exceptions are properly handled."""
        # Mock to raise exception
        mock_get_cap.side_effect = Exception("Database error")
        
        response = client.get("/api/v1/chat/capabilities")
        
        # Should return 500 with error details
        assert response.status_code == 500
        data = response.json()
        # Check for error in standardized format
        assert 'error' in data
        assert data['error']['code'] == 'INTERNAL_ERROR'
        assert 'Failed to retrieve capabilities' in data['error']['message']


class TestCapabilitiesResponseFormat:
    """Test response format compliance."""
    
    def test_response_format_structure(self, mock_capabilities):
        """Test that response has correct structure."""
        response = client.get("/api/v1/chat/capabilities")
        
        assert response.status_code == 200
        data = response.json()
        
        # Top-level keys
        assert 'success' in data
        assert 'total' in data
        assert 'categories' in data
        assert 'capabilities' in data
        
        # Types
        assert isinstance(data['success'], bool)
        assert isinstance(data['total'], int)
        assert isinstance(data['categories'], list)
        assert isinstance(data['capabilities'], list)
        
        # Consistency
        assert data['total'] == len(data['capabilities'])
    
    def test_capability_object_structure(self, mock_capabilities):
        """Test individual capability object structure."""
        response = client.get("/api/v1/chat/capabilities")
        data = response.json()
        
        for cap in data['capabilities']:
            # Required string fields
            assert isinstance(cap['id'], str) and len(cap['id']) > 0
            assert isinstance(cap['category'], str)
            assert isinstance(cap['name'], str)
            assert isinstance(cap['title'], str)
            assert isinstance(cap['description'], str)  # Can be empty
            assert isinstance(cap['icon'], str)
            
            # Required list fields
            assert isinstance(cap['example_prompts'], list)
            assert isinstance(cap['tags'], list)
            
            # ID format validation (category.name)
            assert '.' in cap['id']
            category, name = cap['id'].split('.', 1)
            assert category == cap['category']
            assert name == cap['name']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
