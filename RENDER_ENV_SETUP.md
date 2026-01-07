# Setting Environment Variables in Render

**IMPORTANT**: Your `.env` file contains sensitive information and should NEVER be committed to GitHub. It's already in `.gitignore` to protect your secrets.

## How It Works

1. **Locally**: You use your `.env` file (never commit this!)
2. **On Render**: You manually copy the values from your `.env` to Render's dashboard
3. **render.yaml**: Only contains the variable NAMES (no values) - safe to commit

## Steps to Configure on Render

### After deploying to Render:

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click on your **agenthub-api** service
3. Click **Environment** tab
4. Add these variables by copying values from your local `.env` file:

### Required Variables (copy from your .env):

```bash
# Security
JWT_SECRET_KEY=<copy from your .env>

# MongoDB (your existing cluster)
MONGODB_HOST=chat-session-cluster.kxl3lsm.mongodb.net
MONGODB_USERNAME=aioyejide_db_user
MONGODB_PASSWORD=<copy from your .env>
MONGODB_CONNECTION_STRING=<copy from your .env>

# LLM Providers
OPENAI_API_KEY=<copy from your .env>
GROQ_API_KEY=<copy from your .env>

# Qdrant
QDRANT_API_KEY=<copy from your .env>
QDRANT_ENDPOINT=<copy from your .env>
QDRANT_CLUSTER_ID=<copy from your .env>

# LangChain
LANGCHAIN_API_KEY=<copy from your .env>

# Atlassian
ATLASSIAN_API_KEY=<copy from your .env>
ATLASSIAN_EMAIL=<copy from your .env>

# GitHub (if using GitHub integration)
GITHUB_APP_ID=<copy from your .env>
GITHUB_APP_CLIENT_ID=<copy from your .env>
GITHUB_CLIENT_SECRET=<copy from your .env>
GITHUB_INSTALLATION_ID=<copy from your .env>
GITHUB_PRIVATE_KEY=<copy CONTENT of your .pem file>

# Frontend URL (update this!)
ALLOWED_ORIGINS=https://your-frontend-domain.com,http://localhost:3000
```

### Optional Variables:

```bash
# PostgreSQL (if you're using PgVector)
POSTGRES_USER=<copy from your .env>
POSTGRES_PASSWORD=<copy from your .env>
POSTGRES_HOST=<your postgres host>
PGVECTOR_CONNECTION_STRING=<copy from your .env>

# Datadog (if using)
DATADOG_API_KEY=<copy from your .env>
DATADOG_APP_KEY=<copy from your .env>
```

## Important Notes

### ✅ Safe to Commit to GitHub:
- `render.yaml` - only has variable names, not values
- `.env.production.example` - template with placeholders
- `DEPLOYMENT_QUICKSTART.md`, `docs/DEPLOYMENT.md` - documentation

### ❌ NEVER Commit to GitHub:
- `.env` - contains real secrets (already in .gitignore)
- `.env.production` - if you create one with real values
- Any file with actual API keys or passwords

### Auto-Configured by Render:
These are automatically set by Render, don't add them:
- `REDIS_HOST`
- `REDIS_PORT`
- `REDIS_URL`
- `PORT` (for your web service)

## Quick Copy Helper

You can use this command to see all your current environment variables:

```bash
cat .env | grep -v "^#" | grep -v "^$"
```

Then copy-paste the values (not the entire file!) into Render's dashboard one by one.

## After Setting Variables

1. Click **"Save Changes"** in Render dashboard
2. Render will automatically redeploy your app
3. Wait for deployment to complete (~5-8 minutes)
4. Test your deployment:
   ```bash
   curl https://your-app.onrender.com/health
   ```

## Security Best Practices

1. ✅ Never commit `.env` to git
2. ✅ Use different secrets for production vs development
3. ✅ Rotate API keys regularly
4. ✅ Only give team members access to Render dashboard (not .env file)
5. ✅ Use Render's environment groups for shared configs

## Need Help?

- See full deployment guide: `docs/DEPLOYMENT.md`
- Quick start: `DEPLOYMENT_QUICKSTART.md`
- Environment template: `.env.production.example`
