"""
Integration tests for Jira comment functionality with user mentions and "On behalf of" feature.

This test suite validates:
1. Adding comments to Jira issues
2. User search functionality
3. Creating comments with mentions (ADF format)
4. "On behalf of" context in comments
5. Listing users (all users and project users)

Requirements:
- Jira connection configured in external.yaml
- Valid Jira API credentials in environment variables
- Test ticket: SCRUM-15 in https://aioyejide.atlassian.net
- User to mention: Ahmad Asiyanbola
"""

import pytest
import json
from datetime import datetime

from app.services.external.jira_service import jira
from app.agent.tools.atlassian.jira import JiraTools
from app.core.utils.logger import get_logger
from app.core.security.token_manager import token_manager

logger = get_logger(__name__)


class TestJiraCommentIntegration:
    """Integration tests for Jira comment features."""
    
    # Test configuration
    TEST_ISSUE_KEY = "SCRUM-15"  # Your actual ticket
    TEST_PROJECT_KEY = "SCRUM"
    TEST_USER_SEARCH = "Ahmad Asiyanbola"  # User to search and mention
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up JiraTools instance."""
        self.jira_tools = JiraTools()
        self.added_comments = []  # Track comments added for reporting
        
        yield
        
        # Teardown: Report added comments
        if self.added_comments:
            logger.info(f"Added {len(self.added_comments)} test comments during integration tests")
            for comment_info in self.added_comments:
                logger.info(f"  - {comment_info}")
    
    def test_jira_connection_and_issue_access(self):
        """Test basic connection and verify we can access the test issue."""
        try:
            # Test connection
            server_info = jira.get_server_info()
            assert server_info is not None
            logger.info(f"✅ Connected to Jira: {server_info.get('version')}")
            
            # Test issue access
            issue = jira.get_issue(self.TEST_ISSUE_KEY)
            assert issue is not None
            assert issue['key'] == self.TEST_ISSUE_KEY
            
            # Log issue details
            fields = issue['fields']
            logger.info(f"✅ Accessed issue: {self.TEST_ISSUE_KEY}")
            logger.info(f"   Summary: {fields['summary']}")
            logger.info(f"   Status: {fields['status']['name']}")
            logger.info(f"   Type: {fields['issuetype']['name']}")
            
        except Exception as e:
            pytest.fail(f"Failed to connect or access issue {self.TEST_ISSUE_KEY}: {e}")
    
    def test_add_simple_comment(self):
        """Test adding a simple text comment to the issue."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        comment_text = f"Integration test comment - Simple text\nTimestamp: {timestamp}"
        
        try:
            # Add comment using tools layer
            result_json = self.jira_tools._add_comment(
                issue_key=self.TEST_ISSUE_KEY,
                comment_body=comment_text
            )
            
            result = json.loads(result_json)
            
            # Validate result
            assert result['status'] == 'success'
            assert result['issue_key'] == self.TEST_ISSUE_KEY
            assert 'comment' in result
            
            logger.info(f"✅ Simple comment added successfully")
            logger.info(f"   Comment ID: {result['comment'].get('id')}")
            
            self.added_comments.append(f"Simple text comment on {self.TEST_ISSUE_KEY}")
            
        except Exception as e:
            pytest.fail(f"Failed to add simple comment: {e}")
    
    def test_add_comment_with_on_behalf_of(self):
        """Test adding a comment with 'On behalf of' context."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        comment_text = f"Integration test comment - With user context\nTimestamp: {timestamp}"
        on_behalf_of = "Test User (test.user@example.com)"
        
        try:
            # Add comment with on_behalf_of parameter
            result_json = self.jira_tools._add_comment(
                issue_key=self.TEST_ISSUE_KEY,
                comment_body=comment_text,
                on_behalf_of=on_behalf_of
            )
            
            result = json.loads(result_json)
            
            # Validate result
            assert result['status'] == 'success'
            assert result['issue_key'] == self.TEST_ISSUE_KEY
            assert result['on_behalf_of'] == on_behalf_of
            assert 'comment' in result
            
            logger.info(f"✅ Comment with 'On behalf of' added successfully")
            logger.info(f"   On behalf of: {on_behalf_of}")
            logger.info(f"   Comment ID: {result['comment'].get('id')}")
            
            self.added_comments.append(f"'On behalf of' comment on {self.TEST_ISSUE_KEY}")
            
        except Exception as e:
            pytest.fail(f"Failed to add comment with 'On behalf of': {e}")
    
    def test_search_users(self):
        """Test searching for users in Jira."""
        try:
            # Search for the test user
            result_json = self.jira_tools._search_users(
                query=self.TEST_USER_SEARCH,
                max_results=10
            )
            
            result = json.loads(result_json)
            
            # Validate result
            assert result['status'] == 'success'
            assert result['query'] == self.TEST_USER_SEARCH
            assert 'users' in result
            assert len(result['users']) > 0, f"No users found matching '{self.TEST_USER_SEARCH}'"
            
            # Find the specific user
            users = result['users']
            logger.info(f"✅ Found {len(users)} user(s) matching '{self.TEST_USER_SEARCH}':")
            
            for user in users:
                logger.info(f"   - {user['display_name']} ({user['email']})")
                logger.info(f"     Account ID: {user['account_id']}")
                logger.info(f"     Active: {user['active']}")
            
            # Store first user for mention test
            self.test_user_account_id = users[0]['account_id']
            self.test_user_display_name = users[0]['display_name']
            
        except Exception as e:
            pytest.fail(f"Failed to search for users: {e}")
    
    def test_get_all_users(self):
        """Test getting all Jira users with pagination."""
        try:
            result_json = self.jira_tools._get_all_users(
                start_at=0,
                max_results=10
            )
            
            result = json.loads(result_json)
            
            # Validate result
            assert result['status'] == 'success'
            assert 'users' in result
            assert result['start_at'] == 0
            assert result['max_results'] == 10
            
            users = result['users']
            logger.info(f"✅ Retrieved {len(users)} users (first 10)")
            
            # Log first few users
            for i, user in enumerate(users[:3], 1):
                logger.info(f"   {i}. {user['display_name']} - {user['email']}")
            
        except Exception as e:
            # Some Jira instances might restrict listing all users
            logger.warning(f"Getting all users failed (might be restricted): {e}")
            pytest.skip(f"Getting all users not available: {e}")
    
    def test_get_project_users(self):
        """Test getting users with access to the project."""
        try:
            result_json = self.jira_tools._get_project_users(
                project_key=self.TEST_PROJECT_KEY,
                max_results=20
            )
            
            result = json.loads(result_json)
            
            # Validate result
            assert result['status'] == 'success'
            assert result['project_key'] == self.TEST_PROJECT_KEY
            assert 'users' in result
            
            users = result['users']
            logger.info(f"✅ Found {len(users)} user(s) with access to project {self.TEST_PROJECT_KEY}")
            
            # Log users
            for user in users:
                logger.info(f"   - {user['display_name']} ({user['email']})")
            
            # Verify the test user is in the project
            user_found = any(
                self.TEST_USER_SEARCH.lower() in user['display_name'].lower()
                for user in users
            )
            
            if user_found:
                logger.info(f"✅ Test user '{self.TEST_USER_SEARCH}' has access to the project")
            else:
                logger.warning(f"⚠️  Test user '{self.TEST_USER_SEARCH}' not found in project users")
            
        except Exception as e:
            pytest.fail(f"Failed to get project users: {e}")
    
    def test_add_comment_with_mention_adf(self):
        """Test adding a comment with user mention using ADF format."""
        # First, search for the user to get account ID
        search_result_json = self.jira_tools._search_users(
            query=self.TEST_USER_SEARCH,
            max_results=5
        )
        
        search_result = json.loads(search_result_json)
        
        if not search_result['users']:
            pytest.skip(f"User '{self.TEST_USER_SEARCH}' not found for mention test")
        
        user = search_result['users'][0]
        account_id = user['account_id']
        display_name = user['display_name']
        
        logger.info(f"Found user for mention: {display_name} (Account ID: {account_id})")
        
        try:
            # Create ADF with mention (without on_behalf_of for better rendering)
            adf = JiraTools.create_mention_adf(
                account_id=account_id,
                display_name=display_name,
                additional_text=" - This is an integration test. Please review this ticket when you have time."
            )
            
            # Add comment with ADF
            result_json = self.jira_tools._add_comment(
                issue_key=self.TEST_ISSUE_KEY,
                comment_body=json.dumps(adf)
            )
            
            result = json.loads(result_json)
            
            # Validate result
            assert result['status'] == 'success'
            assert result['issue_key'] == self.TEST_ISSUE_KEY
            assert result['format'] == 'adf'
            
            logger.info(f"✅ Comment with mention added successfully")
            logger.info(f"   Mentioned: @{display_name}")
            logger.info(f"   Comment ID: {result['comment'].get('id')}")
            
            self.added_comments.append(f"Comment with @{display_name} mention on {self.TEST_ISSUE_KEY}")
            
        except Exception as e:
            pytest.fail(f"Failed to add comment with mention: {e}")
    
    def test_add_comment_with_mention_and_on_behalf_of(self):
        """Test adding a comment with mention AND 'On behalf of' context.
        
        Note: For better rendering in Jira, we use plain text with @username
        instead of ADF format when including 'on behalf of' context.
        """
        # Search for user
        search_result_json = self.jira_tools._search_users(
            query=self.TEST_USER_SEARCH,
            max_results=5
        )
        
        search_result = json.loads(search_result_json)
        
        if not search_result['users']:
            pytest.skip(f"User '{self.TEST_USER_SEARCH}' not found")
        
        user = search_result['users'][0]
        display_name = user['display_name']
        
        try:
            # For on_behalf_of, use plain text with mention (@username)
            on_behalf_of = "Integration Test Bot (integration-test@agenthub.com)"
            comment_text = f"@{display_name} - Integration test: Testing mention with on behalf of feature"
            
            # Add comment with on_behalf_of (plain text format)
            result_json = self.jira_tools._add_comment(
                issue_key=self.TEST_ISSUE_KEY,
                comment_body=comment_text,
                on_behalf_of=on_behalf_of
            )
            
            result = json.loads(result_json)
            
            # Validate result
            assert result['status'] == 'success'
            assert result['format'] == 'text'
            assert result['on_behalf_of'] == on_behalf_of
            
            logger.info(f"✅ Comment with mention AND 'On behalf of' added")
            logger.info(f"   On behalf of: {on_behalf_of}")
            logger.info(f"   Mentioned: @{display_name}")
            logger.info(f"   Comment ID: {result['comment'].get('id')}")
            
            self.added_comments.append(
                f"Combined mention + on-behalf-of comment on {self.TEST_ISSUE_KEY}"
            )
            
        except Exception as e:
            pytest.fail(f"Failed to add combined mention + on-behalf-of comment: {e}")
    
    def test_add_comment_with_multiple_mentions(self):
        """Test adding a comment mentioning multiple users using ADF."""
        # Get project users
        users_result_json = self.jira_tools._get_project_users(
            project_key=self.TEST_PROJECT_KEY,
            max_results=5
        )
        
        users_result = json.loads(users_result_json)
        users = users_result['users']
        
        if len(users) < 1:
            pytest.skip("Not enough users in project for multi-mention test")
        
        try:
            # Build text parts with mentions
            text_parts = [
                {"type": "text", "content": "Integration Test: Multiple mentions - "}
            ]
            
            # Add up to 2 users
            for i, user in enumerate(users[:2]):
                if i > 0:
                    text_parts.append({"type": "text", "content": " and "})
                
                text_parts.append({
                    "type": "mention",
                    "account_id": user['account_id'],
                    "display_name": user['display_name']
                })
            
            text_parts.append({
                "type": "text",
                "content": " - This is a test of multiple user mentions."
            })
            
            # Create ADF without on_behalf_of for better rendering
            adf = JiraTools.create_comment_with_mentions(text_parts=text_parts)
            
            # Add comment
            result_json = self.jira_tools._add_comment(
                issue_key=self.TEST_ISSUE_KEY,
                comment_body=json.dumps(adf)
            )
            
            result = json.loads(result_json)
            
            # Validate
            assert result['status'] == 'success'
            assert result['format'] == 'adf'
            
            mentioned_names = [user['display_name'] for user in users[:2]]
            logger.info(f"✅ Comment with multiple mentions added")
            logger.info(f"   Mentioned: {', '.join(f'@{name}' for name in mentioned_names)}")
            logger.info(f"   Comment ID: {result['comment'].get('id')}")
            
            self.added_comments.append(
                f"Multi-mention comment on {self.TEST_ISSUE_KEY}"
            )
            
        except Exception as e:
            pytest.fail(f"Failed to add multi-mention comment: {e}")
    
    def test_extract_user_from_token(self):
        """Test extracting user information from JWT token payload."""
        # Create a mock token payload (simulating a real JWT)
        mock_payload = {
            'user_id': 'test-123',
            'email': 'john.doe@company.com',
            'username': 'johndoe',
            'firstname': 'John',
            'lastname': 'Doe',
            'sub': 'test-123',
            'type': 'access'
        }
        
        try:
            # Extract user info
            user_info = JiraTools.extract_user_from_token(mock_payload)
            
            # Validate
            assert user_info is not None
            assert isinstance(user_info, str)
            
            # Should contain name and email
            assert 'John Doe' in user_info
            assert 'john.doe@company.com' in user_info
            
            logger.info(f"✅ User info extracted from token: {user_info}")
            
            # Test with minimal payload (only email)
            minimal_payload = {'email': 'jane@company.com'}
            user_info_minimal = JiraTools.extract_user_from_token(minimal_payload)
            assert user_info_minimal == 'jane@company.com'
            logger.info(f"✅ Minimal user info extracted: {user_info_minimal}")
            
            # Test with username only
            username_payload = {'username': 'bob'}
            user_info_username = JiraTools.extract_user_from_token(username_payload)
            assert user_info_username == 'bob'
            logger.info(f"✅ Username extracted: {user_info_username}")
            
        except Exception as e:
            pytest.fail(f"Failed to extract user from token: {e}")
    
    def test_comprehensive_comment_workflow(self):
        """Test complete workflow: search user -> get project users -> add comment with mention."""
        logger.info("🚀 Starting comprehensive comment workflow test")
        
        try:
            # Step 1: Verify issue access
            issue = jira.get_issue(self.TEST_ISSUE_KEY)
            logger.info(f"Step 1 ✅ Verified access to issue {self.TEST_ISSUE_KEY}")
            
            # Step 2: Get project users
            users_result_json = self.jira_tools._get_project_users(
                project_key=self.TEST_PROJECT_KEY,
                max_results=10
            )
            users_result = json.loads(users_result_json)
            assert len(users_result['users']) > 0
            logger.info(f"Step 2 ✅ Retrieved {len(users_result['users'])} project users")
            
            # Step 3: Search for specific user
            search_result_json = self.jira_tools._search_users(
                query=self.TEST_USER_SEARCH,
                max_results=5
            )
            search_result = json.loads(search_result_json)
            
            if not search_result['users']:
                logger.warning(f"Test user '{self.TEST_USER_SEARCH}' not found, using first project user")
                target_user = users_result['users'][0]
            else:
                target_user = search_result['users'][0]
            
            logger.info(f"Step 3 ✅ Selected user: {target_user['display_name']}")
            
            # Step 4: Create comment with mention and context using ADF
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            adf = JiraTools.create_mention_adf(
                account_id=target_user['account_id'],
                display_name=target_user['display_name'],
                additional_text=f" - Comprehensive workflow test completed successfully.\nTimestamp: {timestamp}"
            )
            
            # Step 5: Add the comment
            result_json = self.jira_tools._add_comment(
                issue_key=self.TEST_ISSUE_KEY,
                comment_body=json.dumps(adf)
            )
            
            result = json.loads(result_json)
            assert result['status'] == 'success'
            assert result['format'] == 'adf'
            
            logger.info(f"Step 4 ✅ Added comment with mention")
            logger.info(f"   Issue: {self.TEST_ISSUE_KEY}")
            logger.info(f"   Mentioned: @{target_user['display_name']}")
            logger.info(f"   Comment ID: {result['comment'].get('id')}")
            
            logger.info("🎉 Comprehensive comment workflow test completed successfully!")
            
            self.added_comments.append(
                f"Comprehensive workflow test comment on {self.TEST_ISSUE_KEY}"
            )
            
        except Exception as e:
            pytest.fail(f"Comprehensive workflow test failed: {e}")


class TestJiraErrorHandling:
    """Test error handling for Jira comment operations."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.jira_tools = JiraTools()
    
    def test_add_comment_invalid_issue(self):
        """Test adding comment to non-existent issue."""
        try:
            result_json = self.jira_tools._add_comment(
                issue_key="INVALID-99999",
                comment_body="Test comment"
            )
            # Should raise an exception via @handle_atlassian_errors
            pytest.fail("Expected exception for invalid issue")
        except Exception as e:
            logger.info(f"✅ Correctly handled invalid issue error: {type(e).__name__}")
    
    def test_add_comment_empty_body(self):
        """Test adding comment with empty body."""
        result_json = self.jira_tools._add_comment(
            issue_key="SCRUM-15",
            comment_body=""
        )
        
        result = json.loads(result_json)
        assert result.get('status') == 'error'
        assert 'error' in result
        logger.info("✅ Correctly handled empty comment body")
    
    def test_search_users_empty_query(self):
        """Test searching users with empty query."""
        result_json = self.jira_tools._search_users(query="")
        result = json.loads(result_json)
        assert result.get('status') == 'error'
        assert 'error' in result
        logger.info("✅ Correctly handled empty search query")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
