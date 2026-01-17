# Hugging Face Deployment - Database & Redis Setup Guide

## 🎯 Recommended Architecture for Hugging Face

Your AgentHub application requires:
- **PostgreSQL** - Primary relational database (with pgvector)
- **MongoDB** - Session and conversation storage
- **Redis** - Caching layer

### ⚠️ Important: Hugging Face Limitations

Hugging Face Spaces are **stateless containers** that can restart at any time. This means:
- ❌ You CANNOT run databases inside the container
- ❌ Data will be lost on container restart
- ✅ You MUST use external managed services

---

## 🚀 Recommended Setup (All Free Tiers Available!)

### 1. PostgreSQL with pgvector - Use Neon (Best Choice)

**Why Neon?**
- ✅ Free tier: 3 GB storage, 1 GB compute
- ✅ **Supports pgvector extension** (critical for your embeddings!)
- ✅ Generous free tier limits
- ✅ No credit card required for free tier
- ✅ Auto-scaling and branching

**Setup Steps:**

1. **Sign up**: https://neon.tech
2. **Create a new project**: 
   - Name: `agenthub-production`
   - Region: Choose closest to your users
3. **Enable pgvector**:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
4. **Get connection string**:
   - Format: `postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/dbname?sslmode=require`
   - Copy this for Hugging Face secrets

**Alternative**: Supabase
- Also supports pgvector
- 500 MB free tier
- Includes additional features (auth, storage)
- https://supabase.com

---

### 2. MongoDB - Use MongoDB Atlas (You Already Have This!)

**Good news**: You already have MongoDB Atlas configured!
- ✅ Current connection: `chat-session-cluster.kxl3lsm.mongodb.net`
- ✅ Already in the cloud
- ✅ Free tier: 512 MB storage

**What to do**:
1. **Keep your existing MongoDB Atlas cluster**
2. **Verify it's accessible from anywhere**:
   - Go to: https://cloud.mongodb.com
   - Network Access → Add IP: `0.0.0.0/0` (allow from anywhere)
   - ⚠️ For production, use specific IP ranges if possible

3. **Your connection string for Hugging Face**:
   ```
   MONGODB_CONNECTION_STRING=mongodb+srv://aioyejide_db_user:o3CGV5hOHQWRWpZh@chat-session-cluster.kxl3lsm.mongodb.net/polyagent_sessions?retryWrites=true&w=majority
   ```

---

### 3. Redis - Use Upstash (Best for Serverless)

**Why Upstash?**
- ✅ Designed for serverless/edge computing
- ✅ Free tier: 10,000 commands/day
- ✅ Redis 6 compatible
- ✅ REST API + Redis protocol
- ✅ Global replication available

**Setup Steps:**

1. **Sign up**: https://console.upstash.com
2. **Create Redis database**:
   - Name: `agenthub-cache`
   - Type: Global or Regional (Global = faster worldwide)
   - Region: Choose closest to your users
3. **Get connection details**:
   - You'll get: `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`
   - Or standard Redis URL: `redis://default:password@endpoint:port`

**Alternative**: Redis Cloud
- Free tier: 30 MB
- https://redis.com/cloud
- More traditional Redis hosting

---

## 🔧 Environment Variables for Hugging Face

After setting up the services above, add these to your Hugging Face Space secrets:

### Go to: https://huggingface.co/spaces/oyejidet/agenthub-backend/settings

Click **"Variables and secrets"** → **"New secret"**

Add each of these:

```bash
# PostgreSQL (from Neon)
POSTGRES_HOST=ep-xxx.us-east-2.aws.neon.tech
POSTGRES_PORT=5432
POSTGRES_USER=your-neon-user
POSTGRES_PASSWORD=your-neon-password
POSTGRES_DB=agenthub
PGVECTOR_CONNECTION_STRING=postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/agenthub?sslmode=require

# MongoDB (your existing Atlas)
MONGODB_HOST=chat-session-cluster.kxl3lsm.mongodb.net
MONGODB_PORT=27017
MONGODB_USERNAME=aioyejide_db_user
MONGODB_PASSWORD=o3CGV5hOHQWRWpZh
MONGODB_DATABASE=polyagent_sessions
MONGODB_CONNECTION_STRING=mongodb+srv://aioyejide_db_user:o3CGV5hOHQWRWpZh@chat-session-cluster.kxl3lsm.mongodb.net/polyagent_sessions?retryWrites=true&w=majority

# Redis (from Upstash)
REDIS_HOST=your-upstash-endpoint.upstash.io
REDIS_PORT=6379
REDIS_PASSWORD=your-upstash-password
REDIS_DB=0
CACHE_PROVIDER=redis

# LLM APIs
OPENAI_API_KEY=sk-proj-...
GROQ_API_KEY=gsk_...

# Vector Database (if using Qdrant)
QDRANT_API_KEY=your-qdrant-key
QDRANT_ENDPOINT=https://your-cluster.aws.cloud.qdrant.io

# LangChain (optional)
LANGCHAIN_API_KEY=lsv2_pt_...
LANGCHAIN_PROJECT=agent-hub-project
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# Security
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# App Config
APP_ENV=production
DEBUG=false
APP_NAME=AgentHub
ALLOWED_ORIGINS=https://your-frontend.com

# Atlassian (if needed)
ATLASSIAN_API_KEY=your-key
ATLASSIAN_BASE_URL_CONFLUENCE=https://aioyejide.atlassian.net
ATLASSIAN_BASE_URL_JIRA=https://aioyejide.atlassian.net
ATLASSIAN_EMAIL=ai.oyejide@gmail.com
```

---

## 📋 Step-by-Step Setup Checklist

### ✅ PostgreSQL Setup (15 minutes)
- [ ] Sign up for Neon: https://neon.tech
- [ ] Create new project
- [ ] Enable pgvector extension
- [ ] Copy connection string
- [ ] Test connection locally
- [ ] Add to Hugging Face secrets

### ✅ MongoDB Setup (Already Done!)
- [x] You already have MongoDB Atlas
- [ ] Verify network access allows `0.0.0.0/0`
- [ ] Update connection string format for Hugging Face
- [ ] Add to Hugging Face secrets

### ✅ Redis Setup (10 minutes)
- [ ] Sign up for Upstash: https://console.upstash.com
- [ ] Create Redis database
- [ ] Copy connection details
- [ ] Test connection locally (optional)
- [ ] Add to Hugging Face secrets

### ✅ Configure Hugging Face (5 minutes)
- [ ] Go to Space settings
- [ ] Add all environment variables
- [ ] Restart Space to apply changes

---

## 💰 Cost Analysis

### Free Tier (Perfect for Starting)

| Service | Free Tier | Upgrade Cost |
|---------|-----------|--------------|
| **Neon PostgreSQL** | 3 GB storage | $19/month for 10 GB |
| **MongoDB Atlas** | 512 MB | $9/month for 2 GB |
| **Upstash Redis** | 10K cmds/day | $10/month for 1M cmds/day |
| **Hugging Face Space** | CPU basic | $0.60/hour for upgrade |
| **Total** | **$0/month** | ~$40-50/month for production |

### When to Upgrade?

**Stay on Free Tier if:**
- ✅ Testing and development
- ✅ Low traffic (<1000 users/day)
- ✅ Small data (<500 MB)

**Upgrade When:**
- 📈 Traffic increases
- 📊 Data grows beyond free limits
- 🚀 Need better performance
- 💼 Production/commercial use

---

## 🔄 Migration Strategy

### Phase 1: Set Up Services (Do This First)
1. Create Neon PostgreSQL database
2. Keep existing MongoDB Atlas
3. Create Upstash Redis

### Phase 2: Test Locally
```bash
# Update your .env file with new credentials
POSTGRES_HOST=your-neon-endpoint.neon.tech
REDIS_HOST=your-upstash-endpoint.upstash.io
# Keep MongoDB as is

# Test locally
cd src && uvicorn app.main:app --reload
```

### Phase 3: Deploy to Hugging Face
1. Add all secrets to Hugging Face Space
2. Restart Space
3. Monitor logs for any connection issues
4. Test API endpoints

### Phase 4: Migrate Data (if needed)
- Export from local databases
- Import to cloud services
- Verify data integrity

---

## 🧪 Testing Connections

Create a test script to verify all services:

```python
# test_connections.py
import psycopg2
from pymongo import MongoClient
import redis
import os

# Test PostgreSQL
try:
    conn = psycopg2.connect(os.getenv('PGVECTOR_CONNECTION_STRING'))
    print("✅ PostgreSQL connected")
    conn.close()
except Exception as e:
    print(f"❌ PostgreSQL failed: {e}")

# Test MongoDB
try:
    client = MongoClient(os.getenv('MONGODB_CONNECTION_STRING'))
    client.server_info()
    print("✅ MongoDB connected")
    client.close()
except Exception as e:
    print(f"❌ MongoDB failed: {e}")

# Test Redis
try:
    r = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        password=os.getenv('REDIS_PASSWORD'),
        db=int(os.getenv('REDIS_DB', 0))
    )
    r.ping()
    print("✅ Redis connected")
except Exception as e:
    print(f"❌ Redis failed: {e}")
```

---

## 🆘 Troubleshooting

### "Connection refused" or "Connection timeout"

**For PostgreSQL/Neon:**
- Check connection string format
- Ensure SSL mode is enabled: `?sslmode=require`
- Verify IP allowlist (Neon allows all by default)

**For MongoDB Atlas:**
- Check Network Access settings
- Ensure `0.0.0.0/0` is whitelisted
- Verify username/password are correct

**For Upstash Redis:**
- Check host and port are correct
- Ensure password is correct
- Try both TLS and non-TLS ports

### "Authentication failed"
- Double-check credentials
- Ensure no extra spaces in environment variables
- Verify password doesn't contain special characters that need escaping

### "Database not found"
- Create database first
- Check database name matches exactly

---

## 🎯 Quick Start Commands

```bash
# 1. Set up your services (links above)

# 2. Update local .env for testing
cp .env .env.backup
# Edit .env with new cloud credentials

# 3. Test locally
python test_connections.py

# 4. Add secrets to Hugging Face
# Go to: https://huggingface.co/spaces/oyejidet/agenthub-backend/settings

# 5. Push any changes
git add .
git commit -m "Update for cloud database configuration"
git push huggingface feature/huggingface-deployment:main

# 6. Monitor deployment
# Visit: https://huggingface.co/spaces/oyejidet/agenthub-backend
```

---

## 📚 Additional Resources

- **Neon Docs**: https://neon.tech/docs
- **MongoDB Atlas Docs**: https://www.mongodb.com/docs/atlas
- **Upstash Docs**: https://docs.upstash.com/redis
- **Hugging Face Spaces**: https://huggingface.co/docs/hub/spaces

---

**Ready to start?** Let's set up Neon PostgreSQL and Upstash Redis! 🚀
