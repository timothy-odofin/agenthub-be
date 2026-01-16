# Redis Setup for Hugging Face Deployment

## ✅ Current Status

You already have:
- ✅ **MongoDB Atlas** - External, cloud-based (READY TO USE)
- ✅ **PostgreSQL** - External, cloud-based (READY TO USE)
- ❌ **Redis** - Currently running locally (NEEDS CLOUD SETUP)

## 🎯 What You Need To Do

**ONLY SET UP REDIS** - Everything else is ready!

---

## 🚀 Redis Cloud Setup (Choose One Option)

### Option 1: Upstash Redis (Recommended for Hugging Face) ⭐

**Why Upstash?**
- ✅ **FREE tier**: 10,000 commands/day
- ✅ Designed for serverless/edge (perfect for Hugging Face)
- ✅ Global low-latency
- ✅ No credit card for free tier
- ✅ REST API + Redis protocol

**Setup Steps (5 minutes):**

1. **Sign up**: https://console.upstash.com/login
   - Use GitHub, Google, or email

2. **Create Redis Database**:
   - Click "Create Database"
   - **Name**: `agenthub-cache`
   - **Type**: Choose "Regional" (cheaper) or "Global" (faster)
   - **Region**: Select closest to your users
     - US East (N. Virginia) - for US users
     - Europe (Frankfurt) - for EU users
   - Click "Create"

3. **Get Connection Details**:
   - After creation, you'll see the dashboard
   - Copy these values:
     ```
     UPSTASH_REDIS_REST_URL=https://xxx.upstash.io
     UPSTASH_REDIS_REST_TOKEN=AxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxQ==
     ```
   - Also available: **Redis URL**
     ```
     redis://default:password@endpoint.upstash.io:6379
     ```

4. **For Your Hugging Face Secrets**:
   ```bash
   # Format 1: Using Redis URL (easier)
   REDIS_HOST=your-endpoint.upstash.io
   REDIS_PORT=6379
   REDIS_PASSWORD=your-upstash-password
   REDIS_DB=0
   
   # OR Format 2: Using REST API
   UPSTASH_REDIS_REST_URL=https://xxx.upstash.io
   UPSTASH_REDIS_REST_TOKEN=AxxxxxxxxxxxxQ==
   ```

---

### Option 2: Redis Cloud (Traditional Redis)

**Why Redis Cloud?**
- ✅ **FREE tier**: 30 MB storage
- ✅ Traditional Redis hosting
- ✅ 30 connections max on free tier
- ✅ Standard Redis protocol

**Setup Steps (10 minutes):**

1. **Sign up**: https://redis.com/try-free/
   - Click "Get Started"
   - Create account

2. **Create Subscription**:
   - Select **"Fixed"** subscription
   - Choose **"Free 30MB"** plan
   - Select cloud provider and region
   - Click "Create"

3. **Create Database**:
   - In subscription, click "New Database"
   - **Name**: `agenthub`
   - Click "Activate"

4. **Get Connection Details**:
   - Click on your database
   - Copy:
     ```
     Endpoint: redis-xxxxx.c1.us-east-1-1.ec2.cloud.redislabs.com:12345
     Password: your-password
     ```

5. **For Your Hugging Face Secrets**:
   ```bash
   REDIS_HOST=redis-xxxxx.c1.us-east-1-1.ec2.cloud.redislabs.com
   REDIS_PORT=12345
   REDIS_PASSWORD=your-redis-password
   REDIS_DB=0
   ```

---

### Option 3: Aiven Redis (Good Alternative)

**Why Aiven?**
- ✅ **FREE tier**: Available with credit
- ✅ Multiple cloud providers
- ✅ Good management UI

**Setup**: https://console.aiven.io/signup

---

## 🔧 Add Redis to Hugging Face Secrets

Once you have your Redis credentials:

1. **Go to your Space settings**:
   https://huggingface.co/spaces/oyejidet/agenthub-backend/settings

2. **Click "Variables and secrets"**

3. **Add these secrets** (click "New secret" for each):

   ```bash
   # Redis credentials from Upstash or Redis Cloud
   REDIS_HOST=your-redis-endpoint
   REDIS_PORT=6379
   REDIS_PASSWORD=your-redis-password
   REDIS_DB=0
   CACHE_PROVIDER=redis
   ```

4. **Add your existing database credentials**:

   ```bash
   # PostgreSQL (your existing external DB)
   POSTGRES_HOST=your-postgres-host
   POSTGRES_PORT=5432
   POSTGRES_USER=your-user
   POSTGRES_PASSWORD=your-password
   POSTGRES_DB=polyagent
   PGVECTOR_CONNECTION_STRING=postgresql://user:pass@host:5432/polyagent
   
   # MongoDB Atlas (you already have this)
   MONGODB_HOST=chat-session-cluster.kxl3lsm.mongodb.net
   MONGODB_PORT=27017
   MONGODB_USERNAME=aioyejide_db_user
   MONGODB_PASSWORD=o3CGV5hOHQWRWpZh
   MONGODB_DATABASE=polyagent_sessions
   MONGODB_CONNECTION_STRING=mongodb+srv://aioyejide_db_user:o3CGV5hOHQWRWpZh@chat-session-cluster.kxl3lsm.mongodb.net/polyagent_sessions?retryWrites=true&w=majority
   ```

5. **Add your API keys**:

   ```bash
   # LLM APIs
   OPENAI_API_KEY=sk-proj-...
   GROQ_API_KEY=gsk_...
   
   # Vector DB
   QDRANT_API_KEY=your-key
   QDRANT_ENDPOINT=https://your-cluster.aws.cloud.qdrant.io
   QDRANT_CLUSTER_ID=your-cluster-id
   
   # LangChain (optional)
   LANGCHAIN_API_KEY=lsv2_pt_...
   LANGCHAIN_PROJECT=agent-hub-project
   LANGCHAIN_TRACING_V2=true
   
   # Security
   JWT_SECRET_KEY=your-jwt-secret
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   
   # Atlassian
   ATLASSIAN_API_KEY=your-key
   ATLASSIAN_BASE_URL_CONFLUENCE=https://aioyejide.atlassian.net
   ATLASSIAN_BASE_URL_JIRA=https://aioyejide.atlassian.net
   ATLASSIAN_EMAIL=ai.oyejide@gmail.com
   
   # App Config
   APP_ENV=production
   DEBUG=false
   APP_NAME=AgentHub
   ALLOWED_ORIGINS=https://your-frontend.com
   ```

6. **Click "Restart Space"** to apply the changes

---

## 🧪 Test Redis Connection Locally (Optional)

Before adding to Hugging Face, test your Redis connection:

```bash
# Install redis-cli or use Python
pip install redis

# Test with Python
python3 << EOF
import redis
import os

r = redis.Redis(
    host='your-upstash-endpoint.upstash.io',
    port=6379,
    password='your-password',
    ssl=True,  # Upstash requires SSL
    decode_responses=True
)

# Test connection
r.set('test', 'Hello from Upstash!')
print(r.get('test'))
print("✅ Redis connection successful!")
EOF
```

---

## 📊 Quick Comparison

| Feature | Upstash | Redis Cloud | Your Choice |
|---------|---------|-------------|-------------|
| **Free Tier** | 10K cmds/day | 30 MB storage | ⭐ Upstash |
| **Best For** | Serverless | Traditional | Serverless |
| **Setup Time** | 5 min | 10 min | Faster |
| **Global** | Yes | No (free tier) | Better |
| **SSL/TLS** | Auto | Yes | Both good |

**Recommendation**: Use **Upstash** for Hugging Face deployment - it's designed for this!

---

## 🎯 Summary - What You Need To Do

### Step 1: Set Up Redis (5 minutes)
1. Sign up for Upstash: https://console.upstash.com/login
2. Create Redis database (Regional, closest region)
3. Copy connection details

### Step 2: Add All Secrets to Hugging Face (10 minutes)
1. Go to: https://huggingface.co/spaces/oyejidet/agenthub-backend/settings
2. Click "Variables and secrets"
3. Add Redis credentials (new)
4. Add PostgreSQL credentials (existing)
5. Add MongoDB credentials (existing)
6. Add API keys (existing)
7. Click "Restart Space"

### Step 3: Monitor Deployment (5 minutes)
1. Watch build logs: https://huggingface.co/spaces/oyejidet/agenthub-backend
2. Test API: https://oyejidet-agenthub-backend.hf.space/docs
3. Check health: https://oyejidet-agenthub-backend.hf.space/health

---

## 💰 Cost

| Service | Current | Cloud | Cost |
|---------|---------|-------|------|
| PostgreSQL | External | External | $0 (you have it) |
| MongoDB | Atlas | Atlas | $0 (you have it) |
| Redis | Local | **Upstash** | **$0 (free tier)** |
| **Total** | - | - | **$0/month** 🎉 |

---

## 🚀 Ready?

1. **Set up Upstash Redis**: https://console.upstash.com/login (5 min)
2. **Add secrets to Hugging Face**: (10 min)
3. **Done!** Your app will be live!

Need help with any step? Let me know! 🤝
