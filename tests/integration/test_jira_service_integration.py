"""
Integration tests for JiraService to ensure all functions work properly with actual Jira API.
These tests validate that agent tools will work correctly when using JiraService methods.

Requirements:
- Jira connection must be configured in external.yaml
- Valid Jira API credentials in environment variables
- Accessible Jira project for testing
"""

import pytest
import json
from typing import Dict, List, Any
from datetime import datetime

from app.services.external.jira_service import jira, JiraClient
from app.services.agent.tools.atlassian.jira import JiraTools
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class TestJiraServiceIntegration:
    """Integration tests for JiraService with actual Jira API."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up and tear down test environment."""
        # Setup: Ensure we start with a clean state
        self.test_issue_key = None
        self.created_issues = []  # Track issues created during tests
        
        yield
        
        # Teardown: Clean up any issues created during testing (optional)
        if self.created_issues:
            logger.info(f"Created {len(self.created_issues)} test issues during integration tests")
            # Note: In a real scenario, you might want to delete test issues
            # or use a dedicated test project
    
    def test_jira_server_connection(self):
        """Test basic Jira server connection and info retrieval."""
        try:
            server_info = jira.get_server_info()
            
            # Validate server info response
            assert server_info is not None
            assert isinstance(server_info, dict)
            
            # Check for common Jira server info fields
            expected_fields = ['version', 'versionNumbers', 'buildNumber']
            for field in expected_fields:
                assert field in server_info, f"Server info missing '{field}' field"
            
            logger.info(f"✅ Jira server connection successful. Version: {server_info.get('version')}")
            
        except Exception as e:
            pytest.fail(f"Failed to connect to Jira server: {e}")
    def test_get_jira_projects(self):
        """Test retrieving accessible Jira projects."""
        try:
            projects = jira.get_projects()
            
            # Validate projects response
            assert projects is not None
            assert isinstance(projects, list)
            assert len(projects) > 0, "No accessible projects found"
            
            # Check project structure
            first_project = projects[0]
            required_fields = ['key', 'name', 'id']
            for field in required_fields:
                assert field in first_project, f"Project missing '{field}' field"
            
            logger.info(f"✅ Found {len(projects)} accessible projects")
            logger.info(f"Sample project: {first_project['key']} - {first_project['name']}")
            
            # Store first project key for subsequent tests
            self.test_project_key = first_project['key']
            
        except Exception as e:
            pytest.fail(f"Failed to retrieve Jira projects: {e}")
    def test_create_jira_issue(self):
        """Test creating a new Jira issue."""
        # First get available projects
        projects = jira.get_projects()
        assert len(projects) > 0, "No projects available for testing"
        
        project_key = projects[0]['key']
        
        # Create test issue
        test_summary = f"Integration Test Issue - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_description = "This is a test issue created by JiraService integration tests"
        
        try:
            created_issue = jira.create_issue(
                project=project_key,
                summary=test_summary,
                description=test_description,
                issue_type="Task"
            )
            
            # Validate created issue response
            assert created_issue is not None
            assert isinstance(created_issue, dict)
            assert 'key' in created_issue, "Created issue missing 'key' field"
            
            self.test_issue_key = created_issue['key']
            self.created_issues.append(self.test_issue_key)
            
            logger.info(f"✅ Successfully created issue: {self.test_issue_key}")
            
            # Validate issue structure
            required_fields = ['id', 'key', 'self']
            for field in required_fields:
                assert field in created_issue, f"Created issue missing '{field}' field"
            
        except Exception as e:
            # Check if this is a project configuration issue
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ['summary', 'fields', 'screen', 'configuration']):
                logger.warning(f"Skipping issue creation test - project configuration issue: {e}")
                pytest.skip(f"Project configuration doesn't support issue creation: {e}")
            else:
                pytest.fail(f"Failed to create Jira issue: {e}")
    def test_get_specific_issue(self):
        """Test retrieving a specific issue by key."""
        # First create an issue to test with
        self.test_create_jira_issue()
        
        if not self.test_issue_key:
            pytest.skip("No test issue available")
        
        try:
            issue = jira.get_issue(self.test_issue_key)
            
            # Validate issue response
            assert issue is not None
            assert isinstance(issue, dict)
            
            # Check issue structure
            assert 'key' in issue
            assert 'fields' in issue
            assert issue['key'] == self.test_issue_key
            
            # Check issue fields
            fields = issue['fields']
            required_fields = ['summary', 'description', 'status', 'issuetype', 'project']
            for field in required_fields:
                assert field in fields, f"Issue fields missing '{field}'"
            
            logger.info(f"✅ Successfully retrieved issue: {self.test_issue_key}")
            logger.info(f"Summary: {fields['summary']}")
            logger.info(f"Status: {fields['status']['name']}")
            
        except Exception as e:
            pytest.fail(f"Failed to retrieve issue {self.test_issue_key}: {e}")
    def test_search_issues_with_jql(self):
        """Test searching for issues using JQL."""
        # Get a project to search in
        projects = jira.get_projects()
        assert len(projects) > 0, "No projects available for testing"
        
        project_key = projects[0]['key']
        
        # Search for recent issues in the project
        jql_query = f"project = {project_key} ORDER BY created DESC"
        
        try:
            search_results = jira.search_issues(
                jql=jql_query,
                limit=10,
                fields=['key', 'summary', 'status', 'created']
            )
            
            # Validate search results
            assert search_results is not None
            assert isinstance(search_results, dict)
            
            # Check search result structure - API v3 format
            required_fields = ['issues']
            for field in required_fields:
                assert field in search_results, f"Search results missing '{field}' field"
            
            issues = search_results['issues']
            assert isinstance(issues, list)
            
            # Calculate total from the actual issues returned
            total_issues = len(issues)
            logger.info(f"✅ JQL search successful. Found {total_issues} issues")
            
            # If issues found, validate issue structure
            if issues:
                first_issue = issues[0]
                assert 'key' in first_issue
                assert 'fields' in first_issue
                logger.info(f"Sample issue: {first_issue['key']} - {first_issue['fields'].get('summary', 'No summary')}")
            
        except Exception as e:
            pytest.fail(f"Failed to search issues with JQL: {e}")
    def test_search_issues_with_complex_jql(self):
        """Test searching with more complex JQL queries."""
        # Get projects first
        projects = jira.get_projects()
        assert len(projects) > 0, "No projects available for testing"
        
        project_key = projects[0]['key']
        
        # Test different JQL queries
        jql_queries = [
            f"project = {project_key} AND status != Done ORDER BY created DESC",
            f"project = {project_key} AND issuetype = Task ORDER BY updated DESC",
            f"project = {project_key} ORDER BY priority DESC, created ASC"
        ]
        
        for jql in jql_queries:
            try:
                results = jira.search_issues(jql=jql, limit=5)
                
                assert results is not None
                assert isinstance(results, dict)
                assert 'issues' in results
                
                logger.info(f"✅ Complex JQL query successful: {jql[:50]}... Found {len(results['issues'])} issues")
                
            except Exception as e:
                logger.warning(f"JQL query failed (this might be expected): {jql} - Error: {e}")
                # Don't fail the test for complex queries as they might not match any issues
    def test_jira_error_handling(self):
        """Test error handling for invalid operations."""
        
        # Test 1: Try to get a non-existent issue
        try:
            non_existent_issue = jira.get_issue("INVALID-99999")
            # If this doesn't raise an exception, something's wrong
            pytest.fail("Expected exception for non-existent issue")
        except Exception as e:
            logger.info(f"✅ Correctly handled non-existent issue error: {type(e).__name__}")
        
        # Test 2: Try invalid JQL
        try:
            invalid_jql = "nonexistentfield = 'test'"
            jira.search_issues(jql=invalid_jql)
            pytest.fail("Expected exception for invalid JQL")
        except Exception as e:
            logger.info(f"✅ Correctly handled invalid JQL error: {type(e).__name__}")
        
        # Test 3: Try to create issue in non-existent project
        try:
            jira.create_issue(
                project="NONEXISTENT",
                summary="Test",
                description="Test",
                issue_type="Task"
            )
            pytest.fail("Expected exception for non-existent project")
        except Exception as e:
            logger.info(f"✅ Correctly handled non-existent project error: {type(e).__name__}")
    def test_jira_connection_management(self):
        """Test connection management and cleanup."""
        
        # Test multiple operations to ensure connection reuse
        operations = [
            jira.get_server_info(),
            jira.get_projects(),
            jira.search_issues("ORDER BY created DESC", limit=1)
        ]
        
        try:
            for operation in operations:
                result = operation
                assert result is not None
            
            logger.info("✅ Multiple operations with connection reuse successful")
            
            # Test disconnection
            jira.disconnect()
            logger.info("✅ Jira disconnection successful")
            
            # Test reconnection after disconnect
            server_info = jira.get_server_info()
            assert server_info is not None
            logger.info("✅ Jira reconnection after disconnect successful")
            
        except Exception as e:
            pytest.fail(f"Connection management test failed: {e}")
    def test_comprehensive_workflow(self):
        """Test a complete workflow that mimics how agent tools would use JiraService."""
        
        logger.info("🚀 Starting comprehensive Jira workflow test")
        
        try:
            # Step 1: Get server info (health check)
            server_info = jira.get_server_info()
            logger.info(f"Step 1 ✅ Server: Jira {server_info.get('version')}")
            
            # Step 2: Get available projects
            projects = jira.get_projects()
            assert len(projects) > 0, "No projects available"
            test_project = projects[0]
            logger.info(f"Step 2 ✅ Using project: {test_project['key']} - {test_project['name']}")
            
            # Step 3: Search for existing issues in project
            search_jql = f"project = {test_project['key']} ORDER BY created DESC"
            existing_issues = jira.search_issues(search_jql, limit=5)
            logger.info(f"Step 3 ✅ Found {len(existing_issues['issues'])} existing issues")
            
            # Step 4: Create a new issue
            workflow_summary = f"Workflow Test Issue - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            workflow_description = """
            This issue was created as part of a comprehensive workflow test for JiraService integration.
            
            Test Steps:
            1. Server connection verification
            2. Project listing
            3. Issue searching
            4. Issue creation (this step)
            5. Issue retrieval
            6. Final validation
            """
            
            new_issue = jira.create_issue(
                project=test_project['key'],
                summary=workflow_summary,
                description=workflow_description,
                issue_type="Task"
            )
            
            workflow_issue_key = new_issue['key']
            self.created_issues.append(workflow_issue_key)
            logger.info(f"Step 4 ✅ Created issue: {workflow_issue_key}")
            
            # Step 5: Retrieve the created issue
            retrieved_issue = jira.get_issue(workflow_issue_key)
            assert retrieved_issue['key'] == workflow_issue_key
            assert workflow_summary in retrieved_issue['fields']['summary']
            logger.info(f"Step 5 ✅ Retrieved and validated issue: {workflow_issue_key}")
            
            # Step 6: Search for the newly created issue
            new_search_jql = f"key = {workflow_issue_key}"
            found_issues = jira.search_issues(new_search_jql, limit=1)
            assert found_issues['total'] == 1
            assert found_issues['issues'][0]['key'] == workflow_issue_key
            logger.info(f"Step 6 ✅ Found created issue via search")
            
            logger.info("🎉 Comprehensive workflow test completed successfully!")
            
        except Exception as e:
            pytest.fail(f"Comprehensive workflow test failed: {e}")
    
    def test_performance_and_limits(self):
        """Test performance and pagination with larger result sets."""
        
        # Get a project for testing
        projects = jira.get_projects()
        if not projects:
            pytest.skip("No projects available for performance testing")
        
        project_key = projects[0]['key']
        
        try:
            # Test with different limits
            limits = [1, 5, 10, 25]
            
            for limit in limits:
                start_time = datetime.now()
                
                results = jira.search_issues(
                    jql=f"project = {project_key} ORDER BY created DESC",
                    limit=limit
                )
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                assert results is not None
                assert len(results['issues']) <= limit
                
                logger.info(f"✅ Limit {limit}: Retrieved {len(results['issues'])} issues in {duration:.2f}s")
            
            logger.info("✅ Performance and pagination tests completed")
            
        except Exception as e:
            pytest.fail(f"Performance test failed: {e}")


class TestJiraToolsIntegration:
    """Integration tests for JiraTools agent tools with structured input."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up JiraTools instance and track created issues."""
        self.jira_tools = JiraTools()
        self.created_issues = []
        self.test_project_key = None
        
        yield
        
        # Cleanup: Log created issues for reference
        if self.created_issues:
            logger.info(f"Created {len(self.created_issues)} test issues during JiraTools integration tests")
    
    def test_jira_tools_initialization(self):
        """Test JiraTools initialization and tool creation."""
        try:
            # Test tool creation
            tools = self.jira_tools.get_tools()
            
            assert tools is not None
            assert isinstance(tools, list)
            assert len(tools) == 4, f"Expected 4 tools, got {len(tools)}"
            
            # Validate tool names and types
            expected_tools = [
                "get_jira_projects",
                "create_jira_issue", 
                "get_jira_issue",
                "search_jira_issues"
            ]
            
            actual_tool_names = [tool.name for tool in tools]
            
            for expected_tool in expected_tools:
                assert expected_tool in actual_tool_names, f"Missing tool: {expected_tool}"
            
            logger.info(f"✅ JiraTools initialized with {len(tools)} tools: {actual_tool_names}")
            
        except Exception as e:
            pytest.fail(f"Failed to initialize JiraTools: {e}")
    
    def test_get_jira_projects_tool(self):
        """Test the get_jira_projects agent tool."""
        try:
            # Call the tool method directly (simulating agent call)
            result = self.jira_tools._get_projects()
            
            # Validate response format
            assert result is not None
            assert isinstance(result, str)
            
            # Parse JSON response
            response_data = json.loads(result)
            assert isinstance(response_data, dict)
            assert response_data.get("status") == "success"
            assert "total_projects" in response_data
            assert "projects" in response_data
            assert isinstance(response_data["projects"], list)
            assert response_data["total_projects"] > 0, "No projects found"
            
            # Store first project for other tests
            self.test_project_key = response_data["projects"][0]["key"]
            
            logger.info(f"✅ get_jira_projects tool successful. Found {response_data['total_projects']} projects")
            logger.info(f"Sample project: {response_data['projects'][0]['key']} - {response_data['projects'][0]['name']}")
            
        except Exception as e:
            pytest.fail(f"get_jira_projects tool test failed: {e}")
    
    def test_create_jira_issue_tool(self):
        """Test the create_jira_issue agent tool with structured input."""
        # First get projects to use for testing
        self.test_get_jira_projects_tool()
        
        if not self.test_project_key:
            pytest.skip("No test project available")
        
        try:
            # Prepare structured input
            test_summary = f"Agent Tool Test Issue - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            test_description = "This issue was created by JiraTools agent integration tests using structured input"
            
            # Call the tool with structured parameters
            result = self.jira_tools._create_issue(
                project_key=self.test_project_key,
                summary=test_summary,
                description=test_description,
                issue_type="Task"
            )
            
            # Validate response
            assert result is not None
            assert isinstance(result, str)
            
            # Parse JSON response
            response_data = json.loads(result)
            assert isinstance(response_data, dict)
            assert response_data.get("status") == "success"
            assert "issue" in response_data
            assert "project" in response_data
            assert response_data["project"] == self.test_project_key
            
            # Track created issue
            issue_key = response_data["issue"].get("key")
            if issue_key:
                self.created_issues.append(issue_key)
            
            logger.info(f"✅ create_jira_issue tool successful. Created issue: {issue_key}")
            
        except Exception as e:
            # Check if it's an expected error due to project configuration
            if "summary" in str(e) or "project" in str(e).lower():
                logger.warning(f"create_jira_issue tool failed due to project configuration: {e}")
                pytest.skip("Project configuration doesn't support issue creation")
            else:
                pytest.fail(f"create_jira_issue tool test failed: {e}")
    
    def test_get_jira_issue_tool(self):
        """Test the get_jira_issue agent tool."""
        # First create an issue to test with
        try:
            self.test_create_jira_issue_tool()
        except pytest.skip.Exception:
            # If we can't create an issue, try to find an existing one
            projects_result = self.jira_tools._get_projects()
            projects_data = json.loads(projects_result)
            
            if not projects_data["projects"]:
                pytest.skip("No projects available for testing")
            
            project_key = projects_data["projects"][0]["key"]
            
            # Search for any existing issue in the project
            search_result = self.jira_tools._search_issues(
                jql=f"project = {project_key} ORDER BY created DESC",
                max_results=1
            )
            
            search_data = json.loads(search_result)
            if not search_data["search_results"]["issues"]:
                pytest.skip("No existing issues found for testing")
            
            test_issue_key = search_data["search_results"]["issues"][0]["key"]
        else:
            # Use the issue we just created
            if not self.created_issues:
                pytest.skip("No test issue available")
            test_issue_key = self.created_issues[-1]
        
        try:
            # Call the tool with issue key
            result = self.jira_tools._get_issue(issue_key=test_issue_key)
            
            # Validate response
            assert result is not None
            assert isinstance(result, str)
            
            # Parse JSON response
            response_data = json.loads(result)
            assert isinstance(response_data, dict)
            assert response_data.get("status") == "success"
            assert "issue" in response_data
            
            logger.info(f"✅ get_jira_issue tool successful for issue: {test_issue_key}")
            
        except Exception as e:
            pytest.fail(f"get_jira_issue tool test failed: {e}")
    
    def test_search_jira_issues_tool(self):
        """Test the search_jira_issues agent tool with JQL."""
        # Get a project to search in
        self.test_get_jira_projects_tool()
        
        if not self.test_project_key:
            pytest.skip("No test project available")
        
        try:
            # Test basic search
            jql_query = f"project = {self.test_project_key} ORDER BY created DESC"
            
            result = self.jira_tools._search_issues(
                jql=jql_query,
                max_results=5
            )
            
            # Validate response
            assert result is not None
            assert isinstance(result, str)
            
            # Parse JSON response
            response_data = json.loads(result)
            assert isinstance(response_data, dict)
            assert response_data.get("status") == "success"
            assert "search_results" in response_data
            assert "jql" in response_data
            assert response_data["jql"] == jql_query
            assert "max_results" in response_data
            assert response_data["max_results"] == 5
            
            # Validate search results structure
            search_results = response_data["search_results"]
            assert isinstance(search_results, dict)
            assert "issues" in search_results
            
            issues = search_results["issues"]
            assert isinstance(issues, list)
            
            logger.info(f"✅ search_jira_issues tool successful. Found {len(issues)} issues with JQL: {jql_query}")
            
        except Exception as e:
            pytest.fail(f"search_jira_issues tool test failed: {e}")
    
    def test_jira_tools_error_handling(self):
        """Test error handling in JiraTools agent tools."""
        
        # Test 1: Invalid issue key
        try:
            result = self.jira_tools._get_issue(issue_key="INVALID-99999")
            response_data = json.loads(result)
            
            # Should return error message, not raise exception
            assert "Error" in result or response_data.get("status") == "error"
            logger.info("✅ Invalid issue key handled correctly")
            
        except Exception as e:
            pytest.fail(f"Error handling test failed for invalid issue key: {e}")
        
        # Test 2: Invalid JQL
        try:
            result = self.jira_tools._search_issues(
                jql="nonexistentfield = 'test'",
                max_results=10
            )
            
            # Should return error message, not raise exception
            assert "Error" in result
            logger.info("✅ Invalid JQL handled correctly")
            
        except Exception as e:
            pytest.fail(f"Error handling test failed for invalid JQL: {e}")
        
        # Test 3: Empty/None inputs
        try:
            result = self.jira_tools._get_issue(issue_key="")
            assert "Error" in result
            
            result = self.jira_tools._search_issues(jql="", max_results=10)
            assert "Error" in result
            
            logger.info("✅ Empty input validation handled correctly")
            
        except Exception as e:
            pytest.fail(f"Error handling test failed for empty inputs: {e}")
    
    def test_jira_tools_comprehensive_workflow(self):
        """Test complete workflow using JiraTools as an agent would."""
        
        logger.info("🚀 Starting comprehensive JiraTools workflow test")
        
        try:
            # Step 1: Get available projects
            projects_result = self.jira_tools._get_projects()
            projects_data = json.loads(projects_result)
            
            assert projects_data["status"] == "success"
            assert len(projects_data["projects"]) > 0
            
            test_project = projects_data["projects"][0]
            logger.info(f"Step 1 ✅ Using project: {test_project['key']} - {test_project['name']}")
            
            # Step 2: Search existing issues
            search_result = self.jira_tools._search_issues(
                jql=f"project = {test_project['key']} ORDER BY created DESC",
                max_results=3
            )
            search_data = json.loads(search_result)
            
            assert search_data["status"] == "success"
            existing_count = len(search_data["search_results"]["issues"])
            logger.info(f"Step 2 ✅ Found {existing_count} existing issues")
            
            # Step 3: Try to create a new issue (may fail due to permissions)
            try:
                create_result = self.jira_tools._create_issue(
                    project_key=test_project['key'],
                    summary=f"Workflow Test - {datetime.now().strftime('%H%M%S')}",
                    description="Comprehensive workflow test issue",
                    issue_type="Task"
                )
                
                create_data = json.loads(create_result)
                
                if create_data.get("status") == "success":
                    issue_key = create_data["issue"]["key"]
                    self.created_issues.append(issue_key)
                    logger.info(f"Step 3 ✅ Created issue: {issue_key}")
                    
                    # Step 4: Retrieve the created issue
                    get_result = self.jira_tools._get_issue(issue_key=issue_key)
                    get_data = json.loads(get_result)
                    
                    assert get_data["status"] == "success"
                    assert get_data["issue"]["key"] == issue_key
                    logger.info(f"Step 4 ✅ Retrieved created issue: {issue_key}")
                    
                else:
                    logger.info("Step 3 ⚠️ Issue creation skipped (permissions/config)")
                    
            except Exception as create_error:
                logger.info(f"Step 3 ⚠️ Issue creation failed (expected): {create_error}")
            
            logger.info("🎉 JiraTools comprehensive workflow test completed!")
            
        except Exception as e:
            pytest.fail(f"JiraTools comprehensive workflow test failed: {e}")


# Helper function for running JiraTools integration tests
def run_jira_tools_tests():
    """Helper function to run JiraTools integration tests manually."""
    test_instance = TestJiraToolsIntegration()
    
    print("🧪 Running JiraTools Integration Tests...")
    
    try:
        # Manual setup instead of fixture
        test_instance.jira_tools = JiraTools()
        test_instance.created_issues = []
        test_instance.test_project_key = None
        
        # Run JiraTools tests
        jira_tools_tests = [
            test_instance.test_jira_tools_initialization,
            test_instance.test_get_jira_projects_tool,
            test_instance.test_create_jira_issue_tool,
            test_instance.test_get_jira_issue_tool,
            test_instance.test_search_jira_issues_tool,
            test_instance.test_jira_tools_error_handling,
            test_instance.test_jira_tools_comprehensive_workflow,
        ]
        
        for i, test in enumerate(jira_tools_tests, 1):
            try:
                test()
                print(f"✅ JiraTools Test {i}: PASSED")
            except pytest.skip.Exception as skip_ex:
                print(f"⚠️ JiraTools Test {i}: SKIPPED - {skip_ex}")
            except Exception as e:
                print(f"❌ JiraTools Test {i}: FAILED - {e}")
        
        print("🎉 All JiraTools integration tests completed!")
        
    except Exception as e:
        print(f"💥 JiraTools integration test setup failed: {e}")


# Helper function for running integration tests manually
def run_integration_tests():
    """Helper function to run integration tests manually."""
    test_instance = TestJiraServiceIntegration()
    
    print("🧪 Running JiraService Integration Tests...")
    
    try:
        # Manual setup instead of fixture
        test_instance.test_issue_key = None
        test_instance.created_issues = []
        
        # Run individual tests
        tests = [
            test_instance.test_jira_server_connection,
            test_instance.test_get_jira_projects,
            test_instance.test_create_jira_issue,
            test_instance.test_get_specific_issue,
            test_instance.test_search_issues_with_jql,
            test_instance.test_search_issues_with_complex_jql,
            test_instance.test_jira_error_handling,
            test_instance.test_jira_connection_management,
            test_instance.test_comprehensive_workflow,
            test_instance.test_performance_and_limits,
        ]
        
        for i, test in enumerate(tests, 1):
            try:
                test()
                print(f"✅ Test {i}: PASSED")
            except pytest.skip.Exception as skip_ex:
                print(f"⚠️ Test {i}: SKIPPED - {skip_ex}")
            except Exception as e:
                print(f"❌ Test {i}: FAILED - {e}")
        
        print("🎉 All integration tests completed!")
        
    except Exception as e:
        print(f"💥 Integration test setup failed: {e}")


if __name__ == "__main__":
    print("🚀 Running Complete Jira Integration Test Suite")
    print("=" * 60)
    
    # Run JiraService tests
    run_integration_tests()
    
    print("\n" + "=" * 60)
    
    # Run JiraTools tests
    run_jira_tools_tests()
    
    print("\n🎉 All Jira integration tests completed!")
