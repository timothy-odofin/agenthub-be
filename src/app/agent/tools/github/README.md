# GitHub Tools Integration

Professional GitHub integration for agenthub with multi-repository support through GitHub App authentication.

## 🏗️ Architecture

- **GitHubConnectionManager**: GitHub App authentication with repository discovery
- **GitHubToolFactory**: Dynamic tool creation using LangChain GitHubToolkit  
- **GitHubToolsProvider**: Main provider class with multi-repository support
- **Configuration-driven**: Clean separation of tool definitions from connection credentials

## 📋 Configuration

### Environment Variables

```bash
# GitHub App Credentials (Recommended)
export GITHUB_APP_ID="your_app_id"
export GITHUB_PRIVATE_KEY_PATH="/path/to/your/private-key.pem"
export GITHUB_INSTALLATION_ID="your_installation_id"

# Alternative: Personal Access Token
export GITHUB_API_KEY="your_personal_access_token"
```

### GitHub App Setup

1. **Create GitHub App**:
   - Go to GitHub Settings → Developer settings → GitHub Apps
   - Create a new GitHub App
   - Note down the **App ID** (you'll see this immediately)
   - Generate and download the **private key** (.pem file)
   - Save the .pem file securely on your system

2. **Install GitHub App**:
   - In your GitHub App settings, click "Install App"
   - Choose the account/organization to install on
   - Select repositories (specific repos or all repos)
   - Complete installation

3. **Get Installation ID**:
   - **Method 1**: After installation, check the URL - it contains the installation ID
   - **Method 2**: Go to repository Settings → Integrations → GitHub Apps
   - **Method 3**: Use GitHub API to list installations
   - **Note**: Installation ID is optional - the system can auto-detect it

4. **Configure Environment Variables**:
   ```bash
   export GITHUB_APP_ID="123456"                                    # From step 1
   export GITHUB_PRIVATE_KEY_PATH="/path/to/your-app.private-key.pem"  # From step 1  
   export GITHUB_INSTALLATION_ID="87654321"                        # From step 3 (optional)
   ```
   - Update `resources/application-external.yaml`:
   ```yaml
   github:
     app:
       app_id: "${GITHUB_APP_ID}"
       private_key_path: "${GITHUB_PRIVATE_KEY_PATH}"
       installation_id: "${GITHUB_INSTALLATION_ID}"
     repositories:
       allowed_repositories:
         - "owner/repo-name"           # Specific repository
         - "owner/*"                   # All repositories from owner
         - "organization/project-*"    # Pattern matching
   ```

### Tool Configuration

Configure available tools in `resources/application-tools.yaml`:

```yaml
github:
  enabled: true
  description: "GitHub repository management and interaction tools"
  tools:
    create_file:
      enabled: true
      langchain_name: "create_file"
      description: "Create a new file in the repository"
      category: "file_management"
    get_issue:
      enabled: true
      langchain_name: "get_issue" 
      description: "Retrieve information about a specific issue"
      category: "issue_management"
```

## 🚀 Usage

The GitHub tools are automatically discovered and registered with the tool registry:

```python
from app.agent.tools.base.registry import ToolRegistry

# Get all GitHub tools for accessible repositories
github_tools = ToolRegistry.get_instantiated_tools(category="github")

# Tools are automatically scoped by repository
# Example tool names: "create_file_owner_repo", "get_issue_owner_repo"
```

## 🔒 Security Features

- **File-based private keys**: Private keys are read from files (not environment variables)
- **Repository access control**: Fine-grained control over repository access
- **Graceful fallback**: Falls back to personal access token if GitHub App unavailable
- **Permission validation**: Tools only created for accessible repositories

## 🛠️ Tool Factory

The tool factory creates repository-scoped tools to prevent conflicts:

- **Dynamic naming**: `{tool_name}_{repository_safe_name}`
- **Repository context**: Tools include repository information in descriptions
- **Configuration filtering**: Only enabled tools are created
- **Error isolation**: Repository-specific failures don't affect other repositories

## 🎯 Open Source Standards

- ✅ **No inner imports**: All imports at module level
- ✅ **File-based configuration**: Private keys read from files
- ✅ **Clean separation**: Tools/connections/configuration separated  
- ✅ **Error handling**: Comprehensive error handling and logging
- ✅ **Pattern consistency**: Follows existing Atlassian tools pattern
- ✅ **Documentation**: Comprehensive documentation and examples
