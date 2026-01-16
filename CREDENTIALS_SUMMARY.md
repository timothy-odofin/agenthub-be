# 🔑 Quick Credential Guide for Hugging Face

## Step-by-Step: Getting Your Credentials

### 1️⃣ Create Hugging Face Account
```
🌐 Visit: https://huggingface.co/join
�� Sign up with email or GitHub
✅ Verify your email
```

### 2️⃣ Get Your Access Token
```
🌐 Visit: https://huggingface.co/settings/tokens
➕ Click "New token"
📝 Name: "agenthub-deployment"
🔐 Role: "Write"
📋 Copy token (looks like: hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx)
```

**⚠️ IMPORTANT**: Save this token immediately! You won't see it again.

### 3️⃣ Create a Space
```
🌐 Visit: https://huggingface.co/new-space
📝 Space name: "agenthub-backend" (or your choice)
🐳 SDK: "Docker" (MUST SELECT THIS!)
💻 Hardware: "CPU basic" (free) or upgrade
✅ Click "Create Space"
```

## 🚀 Three Ways to Authenticate

### Option A: Hugging Face CLI (Recommended ⭐)
```bash
# Install CLI
pip install huggingface_hub

# Login once (stores token securely)
huggingface-cli login
# Paste your token when prompted

# Verify
huggingface-cli whoami

# Add remote and push
git remote add huggingface https://huggingface.co/spaces/YOUR-USERNAME/YOUR-SPACE
git push huggingface main
```

### Option B: Token in Git URL (Quick & Easy)
```bash
# Replace with your actual values:
# - YOUR-USERNAME: Your Hugging Face username
# - YOUR-TOKEN: Your access token (starts with hf_)
# - YOUR-SPACE: Your Space name

git remote add huggingface https://YOUR-USERNAME:YOUR-TOKEN@huggingface.co/spaces/YOUR-USERNAME/YOUR-SPACE

git push huggingface main
```

**Example:**
```bash
git remote add huggingface https://john-doe:hf_abc123xyz456@huggingface.co/spaces/john-doe/agenthub-backend
```

### Option C: Git Credential Prompt (Interactive)
```bash
# Add remote
git remote add huggingface https://huggingface.co/spaces/YOUR-USERNAME/YOUR-SPACE

# Push (will prompt for credentials)
git push huggingface main

# When prompted:
Username: YOUR-USERNAME
Password: YOUR-TOKEN (paste your hf_ token, NOT your account password!)
```

## 🎯 Quick Test

After authentication, test it:
```bash
# Check if you're logged in
huggingface-cli whoami

# Check your remotes
git remote -v
```

## 🔒 Security Tips

✅ **DO:**
- Keep your token private
- Use token, not password for git
- Store in password manager
- Revoke unused tokens

❌ **DON'T:**
- Share tokens publicly
- Commit tokens to git
- Reuse tokens across projects
- Use "Read" permission (use "Write")

## 🆘 Troubleshooting

**"Authentication failed"**
- Check token is correct
- Verify token has "Write" permission
- Try logging in again: `huggingface-cli login`

**"Repository not found"**
- Verify Space name matches exactly
- Check you created the Space first
- Ensure Space is in your account

**Git keeps asking for password**
- Use `huggingface-cli login` method
- Or embed token in URL (Option B)

## 📋 Complete Flow

```bash
# 1. Install and login
pip install huggingface_hub
huggingface-cli login  # Paste token: hf_xxx...

# 2. Add remote (replace with your values)
git remote add huggingface https://huggingface.co/spaces/YOUR-USERNAME/YOUR-SPACE

# 3. Commit and push
git add .
git commit -m "Deploy to Hugging Face"
git push huggingface main

# 4. Visit your Space
# https://huggingface.co/spaces/YOUR-USERNAME/YOUR-SPACE
```

## 🤝 Or Use the Helper Script!

```bash
./deploy_to_huggingface.sh
```

This script will:
- ✅ Check prerequisites
- ✅ Install Hugging Face CLI
- ✅ Help you login
- ✅ Set up git remote
- ✅ Show you next steps

---

**Ready?** Get your token at: https://huggingface.co/settings/tokens ��
