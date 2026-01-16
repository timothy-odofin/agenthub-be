# Hugging Face Authentication Guide

## 🔐 Getting Your Hugging Face Credentials

### Step 1: Create a Hugging Face Account
1. Go to https://huggingface.co/join
2. Sign up with email or GitHub
3. Verify your email

### Step 2: Create an Access Token

1. Go to https://huggingface.co/settings/tokens
2. Click "**New token**"
3. Fill in:
   - **Name**: `agenthub-deployment` (or any name you prefer)
   - **Role**: Select "**Write**" (needed to push code)
4. Click "**Generate token**"
5. **IMPORTANT**: Copy and save this token immediately! You won't be able to see it again.

Your token will look like: `hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Step 3: Authentication Methods

#### Method A: Token in Git Remote URL (Easiest)
```bash
# Add remote with token embedded
git remote add huggingface https://YOUR-USERNAME:hf_YOUR_TOKEN@huggingface.co/spaces/YOUR-USERNAME/SPACE-NAME

# Push code
git push huggingface feature/huggingface-deployment:main
```

**Example:**
```bash
git remote add huggingface https://john-doe:hf_abc123xyz@huggingface.co/spaces/john-doe/agenthub-backend
```

#### Method B: Git Credential Manager (More Secure)
```bash
# Add remote without token
git remote add huggingface https://huggingface.co/spaces/YOUR-USERNAME/SPACE-NAME

# First push will prompt for credentials
git push huggingface feature/huggingface-deployment:main

# When prompted:
# Username: YOUR-USERNAME
# Password: hf_YOUR_TOKEN (paste your token here, not your password!)
```

#### Method C: Hugging Face CLI (Most Secure)
```bash
# Install Hugging Face CLI
pip install huggingface_hub

# Login (stores token securely)
huggingface-cli login

# When prompted, paste your token
# Token will be saved to ~/.cache/huggingface/token

# Now you can push without embedding credentials
git remote add huggingface https://huggingface.co/spaces/YOUR-USERNAME/SPACE-NAME
git push huggingface feature/huggingface-deployment:main
```

#### Method D: SSH Keys (Advanced)
```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to Hugging Face:
# 1. Go to https://huggingface.co/settings/keys
# 2. Click "Add SSH key"
# 3. Paste your public key
# 4. Save

# Add remote with SSH
git remote add huggingface git@hf.co:spaces/YOUR-USERNAME/SPACE-NAME

# Push
git push huggingface feature/huggingface-deployment:main
```

## 🔒 Security Best Practices

### ✅ DO:
- Use access tokens, not your password
- Create tokens with minimal required permissions (Write for deployment)
- Use descriptive token names
- Store tokens securely (password manager)
- Use Hugging Face CLI for local development
- Revoke tokens you're not using
- Use different tokens for different purposes

### ❌ DON'T:
- Share your tokens publicly
- Commit tokens to git
- Use your account password for git operations
- Give tokens more permissions than needed
- Reuse tokens across different projects

## 🔄 Token Management

### View Your Tokens
https://huggingface.co/settings/tokens

### Revoke a Token
1. Go to https://huggingface.co/settings/tokens
2. Find the token
3. Click "**Manage**" → "**Revoke**"

### Rotate Tokens (Recommended Every 90 Days)
1. Create a new token
2. Update your git remote
3. Test the new token
4. Revoke the old token

## 🔐 Storing Credentials Securely

### macOS Keychain (Automatic)
Git on macOS automatically uses Keychain to store credentials securely.

```bash
# Check if credential helper is configured
git config --global credential.helper

# Should show: osxkeychain
```

### Linux
```bash
# Use libsecret
sudo apt-get install libsecret-1-0 libsecret-1-dev
cd /usr/share/doc/git/contrib/credential/libsecret
sudo make
git config --global credential.helper /usr/share/doc/git/contrib/credential/libsecret/git-credential-libsecret
```

### Windows
```bash
# Use Windows Credential Manager (usually default)
git config --global credential.helper wincred
```

## 🚀 Quick Setup Commands

```bash
# 1. Install Hugging Face CLI
pip install huggingface_hub

# 2. Login with your token
huggingface-cli login
# Paste token when prompted: hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 3. Verify login
huggingface-cli whoami

# 4. Add Hugging Face remote (replace with your details)
export HF_USERNAME="your-username"
export HF_SPACE_NAME="agenthub-backend"
git remote add huggingface https://huggingface.co/spaces/$HF_USERNAME/$HF_SPACE_NAME

# 5. Push to deploy
git push huggingface feature/huggingface-deployment:main
```

## 🔍 Troubleshooting

### "Authentication failed"
- Verify your token is correct
- Check token has "Write" permission
- Make sure token hasn't expired or been revoked
- Try logging in again: `huggingface-cli login`

### "Repository not found"
- Verify Space name is correct
- Check you created the Space on Hugging Face
- Ensure Space is in your account (not an organization)

### "Permission denied"
- Token needs "Write" permission
- You must be the owner or collaborator of the Space

### Git asks for password repeatedly
- Token not stored in credential manager
- Run: `git config --global credential.helper store` (stores in plaintext)
- Or use `huggingface-cli login` for secure storage

## 📱 Alternative: Deploy via Web UI

If you prefer not to use git:

1. Create a Space on Hugging Face
2. In the Space, click "**Files**" tab
3. Click "**Add file**" → "**Upload files**"
4. Upload your Dockerfile and code
5. Configure environment variables in Settings

## 🔗 Useful Links

- **Create Token**: https://huggingface.co/settings/tokens
- **Manage SSH Keys**: https://huggingface.co/settings/keys
- **HF CLI Docs**: https://huggingface.co/docs/huggingface_hub/quick-start
- **Spaces Docs**: https://huggingface.co/docs/hub/spaces-overview

## 💡 Recommended Approach

For the smoothest experience, I recommend:

1. **Install Hugging Face CLI**: `pip install huggingface_hub`
2. **Login once**: `huggingface-cli login` (stores token securely)
3. **Add remote**: `git remote add huggingface https://huggingface.co/spaces/USERNAME/SPACE-NAME`
4. **Push**: `git push huggingface main`

This keeps your token secure and works seamlessly!

---

**Need help?** The setup script `deploy_to_huggingface.sh` will guide you through this process! 🚀
